import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from spec_consultant.cli import main
from spec_consultant.runtime import handoff_invocation

LAUNCHER = Path(__file__).parents[1] / ".github/skills/proof-readiness/scripts/spec-consultant"


def test_source_runtime_info_and_reject_unanchored_override(capsys, monkeypatch, tmp_path):
    assert main(["runtime-info"]) == 0
    info = json.loads(capsys.readouterr().out)
    assert info["mode"] == "source"
    assert "catalog.json" in info["data_sha256"]
    monkeypatch.setenv("SPEC_CONSULTANT_LAUNCHER", str(LAUNCHER))
    monkeypatch.setenv("SPEC_CONSULTANT_CACHE", str(tmp_path))
    with pytest.raises(ValueError, match="identity unavailable"):
        handoff_invocation({"profile": {"roots": []}})


@pytest.fixture
def install(tmp_path):
    if (platform.system(), platform.machine()) != ("Darwin", "arm64"):
        pytest.skip("Only macOS ARM64 currently supported")
    # Trusted product fixture, not an assessed target script.
    skill = tmp_path / "trusted skill"
    (skill / "scripts").mkdir(parents=True)
    launcher = skill / "scripts/spec-consultant"
    launcher.write_bytes(LAUNCHER.read_bytes())
    engine = tmp_path / "trusted engine"
    engine.write_text('#!/bin/sh\nprintf "%s\\n" "$TMPDIR" "$HOME" "$PATH"\n')
    engine.chmod(0o700)
    digest = hashlib.sha256(engine.read_bytes()).hexdigest()
    manifest = skill / "runtime-manifest"
    manifest.write_text(f"spec-runtime-v1\nmacos-arm64|{digest}|engine|-\n")
    root = tmp_path / "selected root"
    root.mkdir()
    cache = tmp_path / "private cache"
    base = ["/bin/sh", str(launcher), "--root", str(root), "--cache", str(cache)]

    def invoke(*args, **env):
        return subprocess.run(
            [*base, *args],
            text=True,
            capture_output=True,
            env={**os.environ, "HOME": str(root), "TMPDIR": str(root), "PATH": str(root), **env},
        )

    return invoke, root, cache, engine, digest, manifest, launcher


def test_prepare_offline_and_verify_every_execution(install):
    invoke, root, cache, engine, digest, _, _ = install
    assert invoke("run", "runtime-info").returncode == 2
    assert not cache.exists()
    assert invoke("prepare").returncode == 2
    assert not cache.exists()  # No consent, no mkdir/temp/download.
    assert invoke("--allow-download", "prepare").returncode == 2  # No invented URL.
    assert not cache.exists()
    assert invoke("--from", str(engine), "prepare").returncode == 0
    assert invoke("status").returncode == 0
    run = invoke("run")
    assert run.returncode == 0, run.stderr
    assert str(root) not in run.stdout
    assert "/usr/bin:/bin" in run.stdout
    assert not list(cache.glob(".runtime.*"))
    (cache / digest).write_text("corrupt")
    assert "digest mismatch" in invoke("run").stderr
    assert list(root.iterdir()) == []


def test_boundary_alias_manifest_and_wrong_digest_fail_closed(install):
    invoke, root, cache, engine, _, manifest, launcher = install
    # The reviewed digest is verified before any provisioning write.
    engine.write_text("wrong")
    assert "digest mismatch" in invoke("--from", str(engine), "prepare").stderr
    assert not cache.exists()
    alias = cache
    alias.symlink_to(root, target_is_directory=True)
    assert invoke("--from", str(engine), "prepare").returncode == 2
    assert list(root.iterdir()) == []
    alias.unlink()
    manifest.write_text("spec-runtime-v1\nmacos-arm64|$(touch nope)|engine|-\n")
    assert "invalid digest" in invoke("status").stderr
    overlap = subprocess.run(
        ["/bin/sh", str(launcher), "--root", str(launcher.parents[2]), "--cache", str(cache), "status"],
        text=True,
        capture_output=True,
    )
    assert "overlaps" in overlap.stderr


@pytest.mark.parametrize("name", ["[a]", "*", "?"])
@pytest.mark.parametrize("multiple_roots", [False, True])
@pytest.mark.parametrize("existing_cache", [False, True])
def test_literal_glob_roots_reject_inside_cache_and_allow_outside(
    install, tmp_path, name, multiple_roots, existing_cache
):
    _, ordinary_root, cache, engine, digest, _, launcher = install
    root = tmp_path / name
    root.mkdir()
    (tmp_path / "a").mkdir()  # A sibling matching each literal root's glob.
    (root / "source.txt").write_text("read-only target data\n")
    inside = root / "cache"
    if existing_cache:
        inside.mkdir(mode=0o700)
    bundled = launcher.parents[1] / "runtime"
    bundled.mkdir()
    (bundled / "engine").write_bytes(engine.read_bytes())
    roots = [ordinary_root, root] if multiple_roots else [root]
    root_args = [arg for selected in roots for arg in ("--root", str(selected))]
    before = sorted(
        (p.relative_to(root), p.stat().st_mode, p.read_bytes() if p.is_file() else None) for p in root.rglob("*")
    )

    def invoke(storage, operation):
        return subprocess.run(
            ["/bin/sh", str(launcher), *root_args, "--cache", str(storage), operation],
            cwd=tmp_path,
            env={"PATH": str(root), "HOME": str(root), "TMPDIR": str(root)},
            capture_output=True,
            text=True,
        )

    rejected = invoke(inside, "prepare")
    assert rejected.returncode == 2, rejected
    assert "overlaps selected root" in rejected.stderr
    assert inside.exists() == existing_cache
    prepared = invoke(cache, "prepare")
    assert prepared.returncode == 0, prepared.stderr
    assert (cache / digest).read_bytes() == engine.read_bytes()
    assert invoke(cache, "status").returncode == 0
    run = invoke(cache, "run")  # Only the trusted external fixture engine executes.
    assert run.returncode == 0, run.stderr
    assert str(root) not in run.stdout
    assert not list(cache.glob(".runtime.*"))
    after = sorted(
        (p.relative_to(root), p.stat().st_mode, p.read_bytes() if p.is_file() else None) for p in root.rglob("*")
    )
    assert after == before
    assert list(ordinary_root.iterdir()) == []


@pytest.mark.parametrize("boundary", ["installation", "manifest", "local-runtime"])
def test_literal_glob_root_protects_other_storage_boundaries(install, tmp_path, boundary):
    _, _, cache, engine, _, manifest, launcher = install
    root = tmp_path / "[a]"
    root.mkdir()
    (tmp_path / "a").mkdir()
    options = []
    if boundary == "installation":
        skill = root / "skill"
        shutil.copytree(launcher.parents[1], skill)
        launcher = skill / "scripts/spec-consultant"
    elif boundary == "manifest":
        copied = root / "runtime-manifest"
        copied.write_bytes(manifest.read_bytes())
        options = ["--manifest", str(copied)]
    else:
        copied = root / "engine"
        copied.write_bytes(engine.read_bytes())
        options = ["--from", str(copied)]
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    result = subprocess.run(
        ["/bin/sh", str(launcher), "--root", str(root), "--cache", str(cache), *options, "prepare"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2, result
    assert "overlaps selected root" in result.stderr
    assert not cache.exists()
    assert {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()} == before


def test_unpublished_and_noconsent_leave_no_storage(install):
    invoke, _, cache, _, digest, manifest, _ = install
    manifest.write_text("spec-runtime-v1\n# No approved releases\n")
    assert "release not published/prepared" in invoke("prepare").stderr
    assert not cache.exists()
    manifest.write_text(f"spec-runtime-v1\nmacos-arm64|{digest}|engine|https://example.invalid/v1/engine\n")
    assert "explicit --allow-download consent" in invoke("prepare").stderr
    assert not cache.exists()


@pytest.mark.parametrize("download_result", ["valid", "wrong-digest", "curl-failure"])
def test_download_boundary_contract(install, tmp_path, download_result):
    invoke, _, cache, engine, digest, manifest, launcher = install
    url = "https://example.invalid/releases/download/v1/engine"
    manifest.write_text(f"spec-runtime-v1\nmacos-arm64|{digest}|engine|{url}\n")
    record = tmp_path / "curl invocation.json"
    stub = tmp_path / "trusted curl stub"
    # Instrument only the fixed curl executable boundary in the installed copy.
    # No real curl/network/TLS runs here; this checks argv, environment, and the
    # launcher's treatment of returned bytes/failures, not curl's redirect logic.
    stub.write_text(
        f"#!{sys.executable}\n"
        "import json, os, pathlib, sys\n"
        f"pathlib.Path({str(record)!r}).write_text(json.dumps("
        "{'args': sys.argv[1:], 'env': dict(os.environ)}))\n"
        f"payload = {engine.read_bytes() if download_result == 'valid' else b'wrong'!r}\n"
        "pathlib.Path(sys.argv[sys.argv.index('--output') + 1]).write_bytes(payload)\n"
        f"sys.exit({22 if download_result == 'curl-failure' else 0})\n"
    )
    stub.chmod(0o700)
    source = launcher.read_text()
    assert source.count("/usr/bin/curl") == 1
    launcher.write_text(source.replace("/usr/bin/curl", f"'{stub}'"))
    assert "explicit --allow-download consent" in invoke("prepare").stderr
    assert not record.exists()
    assert not cache.exists()
    result = invoke(
        "--allow-download",
        "prepare",
        HTTPS_PROXY="http://untrusted.invalid",
        CURL_HOME=str(tmp_path),
        CURL_CA_BUNDLE="/untrusted/ca",
    )
    call = json.loads(record.read_text())
    args = call["args"]
    assert args == [
        "--disable",
        "--fail",
        "--silent",
        "--show-error",
        "--proto",
        "=https",
        "--tlsv1.2",
        "--max-time",
        "300",
        "--location",
        "--max-redirs",
        "5",
        "--proto-redir",
        "=https",
        "--output",
        args[-2],
        url,
    ]
    output = Path(args[-2])
    assert output.name == "runtime"
    assert output.parent.parent == cache
    assert call["env"]["HOME"] == str(output.parent)
    assert call["env"]["PATH"] == "/usr/bin:/bin"
    assert not {"HTTPS_PROXY", "CURL_HOME", "CURL_CA_BUNDLE"} & call["env"].keys()
    assert not list(cache.glob(".runtime.*"))
    if download_result == "valid":
        assert result.returncode == 0, result.stderr
        assert (cache / digest).read_bytes() == engine.read_bytes()
        assert invoke("status").returncode == 0
    else:
        assert result.returncode == 2
        expected = "download failed" if download_result == "curl-failure" else "digest mismatch"
        assert expected in result.stderr
        assert not (cache / digest).exists()


def test_download_rejects_http_manifest_before_storage(install):
    invoke, _, cache, _, digest, manifest, _ = install
    manifest.write_text(f"spec-runtime-v1\nmacos-arm64|{digest}|engine|http://example.invalid/v1/engine\n")
    result = invoke("--allow-download", "prepare")
    assert result.returncode == 2
    assert "HTTPS required" in result.stderr
    assert not cache.exists()


def test_missing_data_and_invalid_schema_are_errors(monkeypatch, tmp_path):
    import spec_consultant.validation as validation

    monkeypatch.setattr(validation, "files", lambda _: tmp_path)
    assert main(["schema", "assessment"]) == 2
    (tmp_path / "data").mkdir()
    (tmp_path / "data/assessment.schema.json").write_text('{"type": "not-a-json-schema-type"}')
    from jsonschema.exceptions import SchemaError

    with pytest.raises(SchemaError):
        validation.schema_check({}, validation.resource("assessment.schema.json"))


def test_launcher_declared_roots_are_not_ignored(monkeypatch, tmp_path):
    monkeypatch.setenv("SPEC_CONSULTANT_ROOTS", str(tmp_path / "other"))
    assert main(["profile", str(tmp_path), "-o", str(tmp_path / "unused")]) == 2
    assert not (tmp_path / "unused").exists()
