import hashlib
import json
import os
import subprocess

import pytest

from spec_consultant.profiler import profile, read_safe, safe_relative
from spec_consultant.validation import validate_profile

from .conftest import EXAMPLE, FIXTURES


def test_multiple_roots_dependencies_and_artifacts():
    value = profile([str(EXAMPLE), str(FIXTURES / "native"), str(FIXTURES / "existing")])
    validate_profile(value)
    assert value["roots"][0]["languages"]["rust"] == 1
    assert value["roots"][1]["languages"]["c"] == 1
    assert value["roots"][1]["dependencies"][0]["relationship"] == "target_link_libraries"
    artifacts = value["roots"][2]["files"]
    assert any(file["kind"] == "specification" for file in artifacts)
    assert {"kani", "verus", "contracts"} <= {signal["kind"] for file in artifacts for signal in file["signals"]}


def test_cargo_dependency_relationships_without_resolving_or_execution(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "Cargo.toml").write_text(
        '[dependencies]\nlocal = {path = "../other"}\nserde = "1"\n'
        "[target.'cfg(unix)'.dependencies]\nlibc = \"0.2\"\n"
        '[workspace.dependencies]\nshared = {path = "shared"}\n'
    )
    (root / "build.rs").write_text('compile_error!("MUST NOT RUN");')
    deps = profile([str(root)])["roots"][0]["dependencies"]
    assert {(d["name"], d["target"]) for d in deps} >= {("local", "../other"), ("serde", None)}
    assert any(d["relationship"].startswith("target.") for d in deps)
    assert any(d["relationship"] == "workspace.dependencies" for d in deps)


def test_dirty_and_non_git(tmp_path):
    nongit = tmp_path / "plain"
    nongit.mkdir()
    assert profile([str(nongit)])["roots"][0]["git"]["available"] is False
    root = tmp_path / "git"
    root.mkdir()

    def git(*args):
        return subprocess.run(
            ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
        ).stdout.strip()

    git("init")
    (root / "lib.rs").write_text("fn double(x: u8) -> u8 { x + x }\n")
    git("add", "lib.rs")
    git(
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-m",
        "fixture",
    )
    clean = profile([str(root)])["roots"][0]
    assert clean["git"]["dirty"] is False
    (root / "lib.rs").write_text("fn triple(x: u8) -> u8 { x * 3 }\n")
    dirty = profile([str(root)])["roots"][0]
    assert dirty["git"]["dirty"] is True
    assert dirty["git"]["revision"] == clean["git"]["revision"]
    assert dirty["snapshot"] != clean["snapshot"]
    assert dirty["files"][0]["sha256"] == hashlib.sha256((root / "lib.rs").read_bytes()).hexdigest()


def test_symlinks_secrets_special_files_and_limits(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside.rs"
    outside.write_text("fn outside() { unsafe { foreign(); } }\n")
    (root / "escape.rs").symlink_to(outside)
    (root / "escape-dir").symlink_to(tmp_path, target_is_directory=True)
    (root / ".env").write_text("PASSWORD=NEVER_SERIALIZE")
    (root / "credentials.json").write_text('{"token": "NEVER_SERIALIZE"}')
    (root / "target").mkdir()
    (root / "target" / "generated.rs").write_text("fn generated() {}")
    (root / "binary.rs").write_bytes(b"\x00binary")
    (root / "large.rs").write_text("x" * 50)
    os.mkfifo(root / "pipe")
    result = profile([str(root)], max_bytes=32)["roots"][0]
    assert not result["files"]
    serialized = json.dumps(result)
    assert "NEVER_SERIALIZE" not in serialized
    assert ".env" not in serialized
    assert {area["reason"] for area in result["uninspected"]} >= {
        "symlink; never followed",
        "secret-like path",
        "binary content",
        "dependency/build/private directory",
    }
    for relative in ("escape.rs", "escape-dir/outside.rs", "pipe", ".env"):
        with pytest.raises((OSError, ValueError)):
            read_safe(root, relative, 1000)


@pytest.mark.parametrize("path", ["../x", "/tmp/x", "a/../../x", "a\\x", "r1:x", ".", "a//b"])
def test_unsafe_references(path):
    with pytest.raises(ValueError):
        safe_relative(path)


def test_unknown_language_and_scan_limits(tmp_path):
    (tmp_path / "unknown.xyz").write_text("a language the profiler does not know")
    (tmp_path / "a.rs").write_text("fn a() {}")
    (tmp_path / "b.rs").write_text("fn b() {}")
    value = profile([str(tmp_path)], max_files=1)["roots"][0]
    assert len(value["files"]) == 1
    assert any("file limit" in area["reason"] for area in value["uninspected"])
    limited = profile([str(tmp_path)], max_entries=1)["roots"][0]
    assert any("entry limit" in area["reason"] for area in limited["uninspected"])
    full = profile([str(tmp_path)])["roots"][0]
    assert full["languages"]["unknown"] == 1


def test_depth_and_duplicate_roots(tmp_path):
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "lib.rs").write_text("fn f() {}")
    result = profile([str(tmp_path)], max_depth=1)["roots"][0]
    assert any(area["reason"] == "depth limit" for area in result["uninspected"])
    with pytest.raises(ValueError, match="duplicate"):
        profile([str(tmp_path), str(tmp_path)])


def test_ancestor_symlink_and_missing_git(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "lib.rs").write_text("fn outside() {}")
    (root / "nested").symlink_to(outside, target_is_directory=True)
    with pytest.raises(OSError):
        read_safe(root, "nested/lib.rs", 1000)

    def missing_git(*args, **kwargs):
        raise FileNotFoundError("Git unavailable")

    monkeypatch.setattr(subprocess, "run", missing_git)
    result = profile([str(root)])["roots"][0]
    assert result["git"]["available"] is False
    assert not result["files"]


def test_entry_limit_is_deterministic_without_sampling_arbitrary_directory_order(tmp_path):
    for name in ("z.rs", "b.rs", "a.rs"):
        (tmp_path / name).write_text("fn f() {}")
    first = profile([str(tmp_path)], max_entries=2)
    second = profile([str(tmp_path)], max_entries=2)
    assert first == second
    assert not first["roots"][0]["files"]


def test_nested_repository_is_a_separate_explicit_scope(tmp_path):
    child = tmp_path / "nested"
    child.mkdir()
    (child / ".git").write_text("gitdir: ../unavailable-metadata\n")
    (child / "lib.rs").write_text("fn nested() {}")
    result = profile([str(tmp_path)])["roots"][0]
    assert not result["files"]
    assert any("nested repository" in area["reason"] for area in result["uninspected"])
    explicit = profile([str(child)])["roots"][0]
    assert any(file["path"] == "lib.rs" for file in explicit["files"])
