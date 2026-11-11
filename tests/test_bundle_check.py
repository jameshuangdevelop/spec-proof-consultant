import importlib.util
import json
import stat
import subprocess
import sys
import zipfile
from contextlib import nullcontext
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("check_bundle", Path(__file__).parents[1] / "packaging/check_bundle.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
LAUNCHER = "proof-readiness/scripts/spec-consultant"
ENGINE = "proof-readiness/runtime/spec-consultant-macos-arm64"


def archive(build, members):
    with zipfile.ZipFile(build / "proof-readiness-macos-arm64.zip", "w") as bundle:
        for name, mode, data in members:
            member = zipfile.ZipInfo(name)
            member.create_system = 3
            member.external_attr = mode << 16
            bundle.writestr(member, data)


@pytest.fixture
def layout(tmp_path, monkeypatch):
    build = tmp_path / "build"
    build.mkdir()
    root = tmp_path / "read-only target"
    root.mkdir()
    output = tmp_path / "new private output"
    monkeypatch.setattr(
        sys, "argv", ["check_bundle.py", "--build", str(build), "--root", str(root), "--output", str(output)]
    )
    return build, root, output


@pytest.mark.parametrize("damage", ["missing", "corrupt", "missing-engine", "non-executable-engine"])
def test_bad_zip_rejected_despite_healthy_staging(layout, monkeypatch, damage):
    build, root, output = layout
    for name in (LAUNCHER, ENGINE, "dist/spec-consultant-macos-arm64"):
        staged = build / name
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_bytes(b"healthy staging must never run")
        staged.chmod(0o755)
    if damage == "corrupt":
        (build / "proof-readiness-macos-arm64.zip").write_bytes(b"not a ZIP archive")
    elif damage != "missing":
        members = [(LAUNCHER, stat.S_IFREG | 0o755, b"launcher")]
        if damage == "non-executable-engine":
            members.append((ENGINE, stat.S_IFREG | 0o644, b"engine"))
        archive(build, members)

    def forbidden(*args, **kwargs):
        pytest.fail("No runtime may execute before ZIP validation succeeds")

    monkeypatch.setattr(checker.subprocess, "run", forbidden)
    with pytest.raises((FileNotFoundError, zipfile.BadZipFile, ValueError)):
        checker.main()
    assert list(root.iterdir()) == []
    assert not (output / "commands.json").exists()


@pytest.mark.parametrize("stage", ["absent", "broken"])
def test_valid_zip_drives_both_execution_paths_without_staging(layout, monkeypatch, stage):
    build, root, output = layout
    if stage == "broken":
        (build / "proof-readiness").write_bytes(b"not even a directory")
        (build / "dist").write_bytes(b"not even a directory")
    archive(
        build,
        [
            (LAUNCHER, stat.S_IFREG | 0o755, b"archive launcher"),
            (ENGINE, stat.S_IFREG | 0o751, b"archive engine"),
            ("proof-readiness/LICENSE", stat.S_IFREG | 0o644, b"archive notice"),
        ],
    )
    installed = output / "installed ZIP"
    calls = []

    class DirectEngineReached(Exception):
        pass

    def run(command, **kwargs):
        calls.append(command)
        if len(calls) == 4:
            assert command == [str(installed / ENGINE), "runtime-info"]
            raise DirectEngineReached
        assert command[0] == str(installed / LAUNCHER)
        response = (
            json.dumps(
                {
                    "mode": "frozen",
                    "build": {"release_qualified": False},
                    "notices": True,
                    "data_sha256": {"catalog.json": "x"},
                }
            )
            if len(calls) == 3
            else ""
        )
        return subprocess.CompletedProcess(command, 2 if len(calls) == 1 else 0, response, "")

    monkeypatch.setattr(checker.subprocess, "run", run)
    # Boundary test only; the full frozen smoke is a separately recorded check.
    with pytest.raises(DirectEngineReached):
        checker.main()
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    assert stat.S_IMODE(installed.stat().st_mode) == 0o700
    assert (installed / LAUNCHER).read_bytes() == b"archive launcher"
    assert (installed / ENGINE).read_bytes() == b"archive engine"
    assert (installed / LAUNCHER).stat().st_mode & 0o111 == 0o111
    assert (installed / ENGINE).stat().st_mode & 0o111 == 0o111
    assert not (installed / "proof-readiness/LICENSE").stat().st_mode & 0o111
    assert list(root.iterdir()) == []


@pytest.mark.parametrize(
    "name,mode",
    [
        ("../escape", stat.S_IFREG | 0o755),
        ("/proof-readiness/escape", stat.S_IFREG | 0o755),
        ("proof-readiness/../escape", stat.S_IFREG | 0o755),
        ("proof-readiness\\escape", stat.S_IFREG | 0o755),
        ("proof-readiness/link", stat.S_IFLNK | 0o777),
        ("proof-readiness/fifo", stat.S_IFIFO | 0o600),
        (LAUNCHER, stat.S_IFREG | 0o755),
    ],
)
def test_unsafe_zip_members_rejected_before_extraction(layout, name, mode):
    build, _, output = layout
    # The last case duplicates the launcher name.
    with pytest.warns(UserWarning) if name == LAUNCHER else nullcontext():
        archive(build, [(LAUNCHER, stat.S_IFREG | 0o755, b"launcher"), (name, mode, b"unsafe")])
    with pytest.raises(ValueError, match="unsafe or duplicate ZIP member"):
        checker.main()
    assert not (output / "installed ZIP").exists()
