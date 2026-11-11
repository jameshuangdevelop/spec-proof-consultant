"""Bundle identity and durable handoff invocation; no provisioning/network here."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shlex
import sys
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path


def runtime_info() -> dict:
    data = files("spec_consultant").joinpath("data")
    identity = data.joinpath("runtime-build.json")
    build = json.loads(identity.read_text()) if identity.is_file() else None
    return {
        "mode": "frozen" if getattr(sys, "frozen", False) else "source",
        "version": version("spec-consultant"),
        "python": platform.python_version(),
        "platform": f"{sys.platform}-{platform.machine()}",
        "build": build,
        "data_sha256": {
            entry.name: hashlib.sha256(entry.read_bytes()).hexdigest()
            for entry in data.iterdir()
            if entry.name.endswith(".json") and entry.name != "runtime-build.json"
        },
        "notices": data.joinpath("THIRD-PARTY-NOTICES.txt").read_text()
        if data.joinpath("THIRD-PARTY-NOTICES.txt").is_file()
        else None,
    }


def check_declared_roots(args: object) -> None:
    """Prevent accidentally assessing undeclared roots through a prepared launcher."""
    declared = os.environ.get("SPEC_CONSULTANT_ROOTS")
    if not declared:
        return
    actual = getattr(args, "roots", None)
    input_file = getattr(args, "profile_file", None) or getattr(args, "assessment", None)
    if input_file:
        value = json.loads(Path(input_file).read_text())
        profiled = value.get("profile", value)
        actual = [root["path"] for root in profiled.get("roots", [])]
    if actual and {str(Path(root).resolve()) for root in actual} != set(declared.splitlines()):
        raise ValueError("assessment roots differ from explicit launcher --root boundaries")


def handoff_invocation(assessment: dict) -> str:
    launcher = os.environ.get("SPEC_CONSULTANT_LAUNCHER")
    if not launcher:
        if getattr(sys, "frozen", False):
            raise ValueError("frozen handoffs require the trusted skill launcher; no temporary _MEI invocation")
        return "spec-consultant"
    info = runtime_info()
    expected = (info["build"] or {}).get("launcher_sha256")
    path = Path(launcher)
    cache = Path(os.environ.get("SPEC_CONSULTANT_CACHE", ""))
    roots = [Path(root["path"]).resolve() for root in assessment["profile"]["roots"]]
    for candidate in (path, cache):
        if not candidate.is_absolute() or candidate.resolve() != candidate:
            raise ValueError("runtime handoff requires absolute nonsymlink installation paths")
        if any(candidate == root or root in candidate.parents for root in roots):
            raise ValueError("runtime installation overlaps assessed roots")
    if not path.is_file() or not cache.is_dir() or not expected:
        raise ValueError("runtime handoff identity unavailable; do not trust an environment override")
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("runtime launcher identity mismatch")
    args = [str(path), "--cache", str(cache)]
    for root in roots:
        args += ["--root", str(root)]
    args += ["run"]
    return shlex.join(args)
