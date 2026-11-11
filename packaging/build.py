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
    if not python_license.is_file():
        raise ValueError("release gate: interpreter LICENSE.txt unavailable")
    notices.append("\n===== Python (includes third-party notices) =====\n" + python_license.read_text())
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
        "python_license_sha256": sha(python_license),
        "release_qualified": False,
        "release_gates": [
            "native-library provenance and notice inventory require independent review",
            "interpreter distribution provenance is recorded, not reproducibly pinned",
            "platform qualification, license review and publication approval pending",
        ],
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
    }
    (output / "artifact-manifest.json").write_text(json.dumps(external, indent=2))
    print(json.dumps(external, indent=2))
    if not args.development:
        raise ValueError("release gates remain unresolved; artifacts retained for evaluation, not publication")


if __name__ == "__main__":
    main()
