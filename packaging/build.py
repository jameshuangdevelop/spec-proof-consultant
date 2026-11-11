#!/usr/bin/env python3
"""Trusted macOS ARM64 builder. Output/scratch must be outside the source checkout."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import sysconfig
import zipfile
from pathlib import Path

from native_provenance import (
    inspect_origin,
    native_inventory,
    retain_evidence,
    wheel_origins,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new external build directory")
    parser.add_argument("--development", action="store_true", help="explicit dirty/unqualified local artifact")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if output == root or root in output.parents or output.exists():
        parser.error("output must be new and outside source checkout")
    if (sys.platform, platform.machine()) != ("darwin", "arm64"):
        parser.error("only macOS ARM64 currently has a resolved build lock; other platforms unqualified")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    output.mkdir(parents=True, mode=0o700)
    records = []

    def run(command: list[str], cwd: Path = root) -> str:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True)
        records.append(
            {
                "command": command,
                "cwd": str(cwd),
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        (output / "commands.json").write_text(json.dumps(records, indent=2))
        if result.returncode:
            raise RuntimeError(f"command failed; see {output / 'commands.json'}: {command}")
        return result.stdout.strip()

    revision = run(["/usr/bin/git", "rev-parse", "HEAD"])
    status = run(["/usr/bin/git", "status", "--porcelain=v1", "--untracked-files=all"])
    if status and not args.development:
        raise ValueError("release build refuses dirty tree; local testing requires --development")
    # Snapshot all relevant trusted inputs, never the source Git directory or assessed repositories.
    snapshot = output / "snapshot"
    snapshot.mkdir()
    for name in ("src", "packaging", ".github/skills/proof-readiness", "pyproject.toml", "LICENSE"):
        source = root / name
        destination = snapshot / name
        if source.is_dir():
            shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(source, destination)
    file_hashes = {str(p.relative_to(snapshot)): sha(p) for p in sorted(snapshot.rglob("*")) if p.is_file()}
    (output / "source-files.json").write_text(json.dumps(file_hashes, indent=2))
    data = snapshot / "src/spec_consultant/data"
    launcher = snapshot / ".github/skills/proof-readiness/scripts/spec-consultant"
    # Include full installed distribution notice texts, including builder notices,
    # without claiming that every builder dependency is collected into the binary.
    notices = [(snapshot / "LICENSE").read_text()]
    notice_inventory = {}
    lock = snapshot / "packaging/requirements-macos-arm64.lock"
    for line in lock.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        name, rest = line.split("==", 1)
        expected = rest.split()[0]
        dist = metadata.distribution(name)
        if dist.version != expected:
            raise ValueError(f"builder dependency differs from lock: {name}")
        texts = [
            f
            for f in dist.files or []
            if any(part.endswith(".dist-info") for part in f.parts)
            and f.name.lower().startswith(("license", "copying", "notice", "authors"))
        ]
        if not texts:
            raise ValueError(f"release gate: missing license inventory for {name}")
        notice_inventory[name] = {str(f): sha(Path(dist.locate_file(f))) for f in texts}
        for item in texts:
            notices.append(f"\n===== {name} {dist.version}: {item} =====\n" + dist.locate_file(item).read_text())
    python_license = Path(sysconfig.get_path("stdlib")) / "LICENSE.txt"
    interpreter_gates = []
    if python_license.is_file() and python_license.stat().st_size:
        notices.append(
            "\n===== Python top-level license (not complete incorporated-code notices) =====\n"
            + python_license.read_text()
        )
    else:
        interpreter_gates.append("interpreter top-level LICENSE.txt missing/empty; coverage unresolved")
    # Data-only discovery from this interpreter's native files and Mach-O load commands.
    # Do not infer collected files from Homebrew formula runtime_dependencies.
    wheels = wheel_origins(metadata.distribution("rpds-py"))
    stdlib = Path(sysconfig.get_path("stdlib"))
    framework = stdlib.parent.parent / "Python"
    pending = list((stdlib / "lib-dynload").glob("*.so")) + [Path(p) for p in wheels]
    if framework.is_file():
        pending.append(framework)
    else:
        libdir, library = sysconfig.get_config_var("LIBDIR"), sysconfig.get_config_var("LDLIBRARY")
        if libdir and library and (Path(libdir) / library).is_file():
            pending.append(Path(libdir) / library)
    candidates = {}
    discovery_gaps = []
    while pending:
        source = pending.pop().resolve()
        if str(source) in candidates:
            continue
        candidates[str(source)] = inspect_origin(source, wheels)
        if not source.is_file():
            discovery_gaps.append(f"missing discovery source: {source}")
            continue
        loads = run(["/usr/bin/otool", "-L", str(source)], output)
        for line in loads.splitlines()[1:]:
            dependency = line.strip().split(" (", 1)[0]
            if dependency.startswith(("/usr/lib/", "/System/Library/")):
                continue
            if dependency.startswith("/"):
                pending.append(Path(dependency))
            else:
                discovery_gaps.append(f"unresolved pre-freeze load path in {source.name}: {dependency}")
    native_evidence = output / "native-provenance-evidence"
    evidence_records = retain_evidence(list(candidates.values()), native_evidence)
    seen_texts = set()
    for origin in candidates.values():
        for text in origin["notice_texts"]:
            if text["sha256"] not in seen_texts:
                seen_texts.add(text["sha256"])
                notices.append(
                    f"\n===== Native local text: {origin['component']} {origin['version']}: "
                    f"{Path(text['path']).name}; sha256={text['sha256']} =====\n" + Path(text["realpath"]).read_text()
                )
    discovery = {
        "format": 1,
        "scope": "pre-freeze candidates, NOT the final collected inventory",
        "sources": list(candidates.values()),
        "discovery_gaps": sorted(set(discovery_gaps)),
        "release_qualified": False,
    }
    discovery_path = data / "native-notice-discovery.json"
    discovery_path.write_text(json.dumps(discovery, indent=2))
    # Keep wheel SBOM bytes both inside the frozen package and in external evidence.
    for name, record in evidence_records.items():
        if "sboms" in Path(record["path"]).parts:
            shutil.copy2(native_evidence / name, data / ("native-" + name))
    (data / "THIRD-PARTY-NOTICES.txt").write_text("\n".join(notices))
    info = {
        "format": 1,
        "source_revision": revision,
        "source_dirty": bool(status),
        "source_status": status,
        "source_files_sha256": hashlib.sha256(json.dumps(file_hashes, sort_keys=True).encode()).hexdigest(),
        "launcher_sha256": sha(launcher),
        "lock_sha256": sha(lock),
        "python": sys.version,
        "interpreter_executable": str(Path(sys.executable).resolve()),
        "interpreter_executable_sha256": sha(Path(sys.executable).resolve()),
        "platform": platform.platform(),
        "target": "macos-arm64",
        "dependencies": {name: metadata.version(name) for name in notice_inventory},
        "notice_inventory": notice_inventory,
        "python_license_sha256": sha(python_license) if not interpreter_gates else None,
        "native_notices": {
            "discovery_sha256": sha(discovery_path),
            "scope": "pre-freeze local texts only; not complete static/transitive coverage",
            "final_inventory": "external native-inventory.json sidecar, NOT embedded; match binary_sha256",
        },
        "release_qualified": False,
        "release_gates": [
            "native-library provenance and notice inventory require independent review",
            "interpreter distribution provenance is recorded, not reproducibly pinned",
            "platform qualification, license review and publication approval pending",
        ]
        + interpreter_gates,
        "signing": "PyInstaller macOS ad-hoc only; not Developer ID signed or notarized",
    }
    (data / "runtime-build.json").write_text(json.dumps(info, indent=2))
    run([sys.executable, "-m", "pip", "install", "--no-deps", "--no-build-isolation", str(snapshot)], output)
    dist = output / "dist"
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--console",
            "--noupx",
            "--clean",
            "--name",
            "spec-consultant-macos-arm64",
            "--distpath",
            str(dist),
            "--workpath",
            str(output / "work"),
            "--specpath",
            str(output),
            "--collect-data",
            "spec_consultant",
            "--collect-data",
            "jsonschema_specifications",
            "--copy-metadata",
            "spec-consultant",
            "--copy-metadata",
            "jsonschema",
            str(snapshot / "packaging/entrypoint.py"),
        ],
        output,
    )
    binary = dist / "spec-consultant-macos-arm64"
    # Preserve the collected native inventory and load commands for later notice/provenance review.
    shutil.copy2(output / "work/spec-consultant-macos-arm64/Analysis-00.toc", output / "native-analysis.toc")
    from PyInstaller.archive.readers import CArchiveReader

    inventory = native_inventory(
        output / "native-analysis.toc", binary, candidates, wheels, CArchiveReader(str(binary))
    )
    inventory["evidence_files"] = retain_evidence(inventory["entries"], native_evidence)
    inventory_path = output / "native-inventory.json"
    inventory_path.write_text(json.dumps(inventory, indent=2))
    run(["/usr/bin/otool", "-L", str(binary)], output)
    run(["/usr/bin/codesign", "-d", "--verbose=4", str(binary)], output)
    skill = output / "proof-readiness"
    shutil.copytree(snapshot / ".github/skills/proof-readiness", skill)
    (skill / "runtime").mkdir()
    shutil.copy2(binary, skill / "runtime" / binary.name)
    (skill / "scripts/spec-consultant").chmod(0o755)
    digest = sha(binary)
    (skill / "runtime-manifest").write_text(f"spec-runtime-v1\nmacos-arm64|{digest}|{binary.name}|-\n")
    shutil.copy2(data / "THIRD-PARTY-NOTICES.txt", skill / "THIRD-PARTY-NOTICES.txt")
    shutil.copy2(data / "runtime-build.json", skill / "runtime-build.json")
    shutil.copy2(inventory_path, skill / "native-inventory.json")
    shutil.copy2(data / "native-notice-discovery.json", skill / "native-notice-discovery.json")
    shutil.copytree(native_evidence, skill / "native-provenance-evidence")
    shutil.copy2(snapshot / "LICENSE", skill / "LICENSE")
    archive = output / "proof-readiness-macos-arm64.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(skill.rglob("*")):
            if path.is_file():
                bundle.write(path, str(path.relative_to(output)))
    external = {
        "build": info,
        "artifacts": {p.name: {"sha256": sha(p), "bytes": p.stat().st_size} for p in (binary, archive)},
        "skill_manifest_sha256": sha(skill / "runtime-manifest"),
        "native_inventory_sha256": sha(inventory_path),
    }
    (output / "artifact-manifest.json").write_text(json.dumps(external, indent=2))
    print(json.dumps(external, indent=2))
    if not args.development:
        raise ValueError("release gates remain unresolved; artifacts retained for evaluation, not publication")


if __name__ == "__main__":
    main()
