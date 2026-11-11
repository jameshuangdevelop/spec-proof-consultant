#!/usr/bin/env python3
"""Bounded trusted product smoke checks; targets are read-only source data."""

from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path, action="append")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    build = args.build.resolve()
    roots = [root.resolve() for root in args.root]
    output = args.output.resolve()
    if output.exists() or any(output == r or r in output.parents for r in roots):
        parser.error("output must be new and outside all roots")
    output.mkdir(parents=True, mode=0o700)

    def fingerprint() -> dict:
        return {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for root in roots for p in root.rglob("*")
            if p.is_file() and not p.is_symlink() and ".git" not in p.relative_to(root).parts
        }

    before = fingerprint()
    records = []
    launcher = build / "proof-readiness/scripts/spec-consultant"
    cache = output / "private cache"
    base = [str(launcher), "--cache", str(cache)]
    for root in roots:
        base += ["--root", str(root)]
    # Neither Python nor uv is in the child PATH. HOME/TMPDIR point into a
    # selected root to exercise the launcher's external extraction policy.
    env = {"PATH": "/nonexistent", "HOME": str(roots[0]), "TMPDIR": str(roots[0]), "LC_ALL": "C"}

    def run(command: list[str], expected: int = 0, child_env: dict | None = None) -> str:
        result = subprocess.run(command, env=child_env or env, capture_output=True, text=True, cwd="/")
        records.append({"command": command, "env": child_env or env, "returncode": result.returncode,
                        "stdout": result.stdout, "stderr": result.stderr})
        (output / "commands.json").write_text(json.dumps(records, indent=2))
        assert result.returncode == expected, records[-1]
        return result.stdout

    run([*base, "status"], 2)
    assert not cache.exists()
    run([*base, "prepare"])
    info = json.loads(run([*base, "run", "runtime-info"]))
    assert info["mode"] == "frozen" and info["build"]["release_qualified"] is False
    assert info["notices"] and info["data_sha256"]["catalog.json"]
    # Also demonstrate direct standalone engine startup with no Python/uv.
    extraction = output / "direct extraction"
    extraction.mkdir(mode=0o700)
    direct_env = {**env, "TMPDIR": str(extraction), "HOME": str(extraction)}
    run([str(build / "dist/spec-consultant-macos-arm64"), "runtime-info"], child_env=direct_env)
    assert not list(extraction.iterdir())
    run([*base, "run", "schema", "assessment"])
    run([*base, "run", "catalog"])
    assessment = output / "assessment with spaces"
    run([*base, "run", "assess", *map(str, roots), "--out", str(assessment)])
    canonical = assessment / "assessment.json"
    run([*base, "run", "validate", str(canonical)])
    run([*base, "run", "freshness", str(canonical)])
    run([*base, "run", "render", str(canonical), "--out", str(output / "rendered")])
    prompt = (assessment / "orchestrator.md").read_text()
    proposed = prompt.split("```sh\n", 1)[1].split("\n```", 1)[0].splitlines()
    assert "_MEI" not in "\n".join(proposed)
    for command in proposed:
        parsed = shlex.split(command)
        assert parsed[0] == str(launcher)
        run(parsed)  # Next-session command, no inherited runtime launcher environment.
    # Trusted negative fixture: these target-supplied executables/configs are
    # data only. Even inherited PATH/HOME/TMPDIR must not cause their execution.
    fake_root = output / "untrusted target fixture"
    fake_root.mkdir()
    marker = output / "target-executed"
    for name in ("python", "python3", "uv", "git"):
        tool = fake_root / name
        tool.write_text(f"#!/bin/sh\n/usr/bin/touch {shlex.quote(str(marker))}\nexit 99\n")
        tool.chmod(0o700)
    (fake_root / ".curlrc").write_text("url = https://example.invalid/never-fetch\n")
    (fake_root / "lib.rs").write_text("pub fn f(x: u8) -> u8 { x + 1 }\n")
    fake_env = {**env, "PATH": str(fake_root), "HOME": str(fake_root), "TMPDIR": str(fake_root)}
    run([str(launcher), "--cache", str(cache), "--root", str(fake_root), "run",
         "assess", str(fake_root), "--out", str(output / "fake-target-assessment")], child_env=fake_env)
    assert not marker.exists()
    invalid = output / "invalid.json"
    invalid.write_text("{}")
    run([*base, "run", "validate", str(invalid)], 2)
    digest = next(p for p in cache.iterdir() if not p.name.startswith("."))
    digest.write_bytes(b"not an executable")
    run([*base, "run", "runtime-info"], 2)  # Digest check happens before execution.
    after = fingerprint()
    (output / "source-integrity.json").write_text(json.dumps({"before": before, "after": after}, indent=2))
    assert before == after
    assert not list(cache.glob(".runtime.*"))
    print(f"{len(records)} runtime commands passed; target data unchanged; evidence: {output}")


if __name__ == "__main__":
    main()
