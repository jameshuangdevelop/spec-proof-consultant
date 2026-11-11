"""Portable fixtures: no Homebrew, native code loading, network, or target execution."""

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

HELPER = Path(__file__).parents[1] / "packaging/native_provenance.py"
SPEC = importlib.util.spec_from_file_location("native_provenance", HELPER)
native = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(native)


def keg(tmp_path, formula, version, member, texts):
    root = tmp_path / "arbitrary-prefix" / "Cellar" / formula / version
    source = root / member
    source.parent.mkdir(parents=True)
    source.write_bytes(b"fixture native source")
    (root / ".brew").mkdir()
    (root / ".brew" / f"{formula}.rb").write_text("formula data; never executed")
    (root / "INSTALL_RECEIPT.json").write_text(
        json.dumps(
            {
                "source": {"versions": {"stable": version}},
                # This unrelated dependency must never become part of the collected inventory.
                "runtime_dependencies": [{"full_name": "not-shipped"}],
            }
        )
    )
    for name, text in texts.items():
        (root / name).write_text(text)
    return root, source


def test_known_local_native_texts_and_retained_identity(tmp_path):
    for formula, version, member, texts, component in [
        ("mpdecimal", "4.0.1", "lib/libmpdec.4.dylib", {"COPYRIGHT.txt": "BSD two clause full fixture"}, "mpdecimal"),
        ("xz", "5.8.4", "lib/liblzma.5.dylib", {"COPYING": "package split", "COPYING.0BSD": "0BSD full"}, "liblzma"),
    ]:
        _, source = keg(tmp_path, formula, version, member, texts)
        origin = native.inspect_origin(source)
        assert origin["component"] == component
        assert origin["version"] == origin["receipt_version"] == version
        assert origin["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
        assert origin["status"] == "local-texts-collected-review-required"
        assert len(origin["notice_texts"]) == len(texts)
        assert len(origin["provenance_files"]) == 2
        retained = tmp_path / f"retained-{formula}"
        records = native.retain_evidence([origin], retained)
        assert all(native.digest(retained / name) == record["sha256"] for name, record in records.items())
        assert "not-shipped" not in {record.get("component") for record in records.values()}


@pytest.mark.parametrize("text", [None, ""])
def test_missing_or_empty_text_is_unresolved(tmp_path, text):
    _, source = keg(
        tmp_path,
        "mpdecimal",
        "4.0.1",
        "lib/libmpdec.4.dylib",
        {} if text is None else {"COPYRIGHT.txt": text},
    )
    origin = native.inspect_origin(source)
    assert origin["status"] == "unresolved"
    assert not origin["notice_texts"]
    assert any("missing/empty native notice" in gap for gap in origin["release_gates"])


def test_ssl_crypto_share_attribution_not_filename_guessing(tmp_path):
    root, ssl = keg(tmp_path, "openssl@3", "3.5.9", "lib/libssl.3.dylib", {"LICENSE.txt": "Apache 2 text"})
    crypto = ssl.with_name("libcrypto.3.dylib")
    crypto.write_bytes(b"crypto fixture")
    first, second = native.inspect_origin(ssl), native.inspect_origin(crypto)
    assert first["component"] == second["component"] == "OpenSSL"
    assert first["notice_texts"] == second["notice_texts"]
    assert first["source_sha256"] != second["source_sha256"]
    assert any("NOTICE presence/absence" in gap for gap in first["release_gates"])
    unknown = tmp_path / "libssl.3.dylib"
    unknown.write_bytes(ssl.read_bytes())
    assert native.inspect_origin(unknown)["component"] == "unknown"
    crypto.unlink()
    crypto.symlink_to(unknown)
    swapped = native.inspect_origin(crypto)
    assert swapped["source_realpath"] == str(unknown)
    assert swapped["component"] == "unknown" and swapped["status"] == "unresolved"
    assert root.name == first["version"]


def test_missing_swapped_receipt_and_cpython_partial_coverage(tmp_path):
    root, source = keg(
        tmp_path,
        "python@3.11",
        "3.11.18",
        "Frameworks/Python.framework/Versions/3.11/Python",
        {"LICENSE": "PSF top level only"},
    )
    origin = native.inspect_origin(source)
    assert origin["component"] == "CPython"
    assert any("Mersenne Twister" in gap for gap in origin["release_gates"])
    receipt = root / "INSTALL_RECEIPT.json"
    receipt.write_text('{"source":{"versions":{"stable":"0.0"}}}')
    assert any("differs" in gap for gap in native.inspect_origin(source)["release_gates"])
    receipt.unlink()
    assert any("missing/invalid origin" in gap for gap in native.inspect_origin(source)["release_gates"])
    receipt.write_text("[]")
    assert any("missing/invalid origin" in gap for gap in native.inspect_origin(source)["release_gates"])
    source.unlink()
    assert native.inspect_origin(source)["source_sha256"] is None


def test_analysis_literal_and_artifact_member_binding(tmp_path):
    _, source = keg(tmp_path, "mpdecimal", "4.0.1", "lib/libmpdec.4.dylib", {"COPYRIGHT.txt": "full text"})
    toc, binary = tmp_path / "Analysis-00.toc", tmp_path / "binary"
    binary.write_bytes(b"fixture final artifact")
    toc.write_text(repr(([], [(source.name, str(source), "BINARY")], [("ignore", "data", "DATA")])))
    candidate = native.inspect_origin(source)
    candidates = {str(source.resolve()): candidate}
    reader = SimpleNamespace(
        toc={source.name: (0, 0, 0, 0, "b")}, extract=lambda destination: b"relocated member bytes"
    )
    inventory = native.native_inventory(toc, binary, candidates, {}, reader)
    assert inventory["binary_sha256"] == native.digest(binary)
    assert inventory["analysis_sha256"] == native.digest(toc)
    assert not inventory["release_qualified"]
    assert len(inventory["entries"]) == 1
    item = inventory["entries"][0]
    assert item["type"] == "BINARY" and item["destination"] == source.name
    assert item["source_sha256"] != item["final_member_sha256"]
    source.write_bytes(b"swapped after discovery")
    changed = native.native_inventory(toc, binary, candidates, {}, reader)["entries"][0]
    assert any("absent/changed" in gap for gap in changed["release_gates"])
    missing = native.native_inventory(toc, binary, {}, {})["entries"][0]
    assert missing["final_member_sha256"] is None and missing["status"] == "unresolved"
    reader.toc[source.name] = (0, 0, 0, 0, "n")
    symlink = native.native_inventory(toc, binary, candidates, {}, reader)["entries"][0]
    assert symlink["final_member_sha256"] is None
    toc.write_text(repr([("same", str(source), "BINARY"), ("same", str(source), "EXTENSION")]))
    with pytest.raises(ValueError, match="duplicate"):
        native.analysis_entries(toc)
    marker = tmp_path / "must-not-exist"
    toc.write_text(f"__import__('pathlib').Path({str(marker)!r}).touch()")
    with pytest.raises(ValueError):
        native.analysis_entries(toc)
    assert not marker.exists()


def test_wheel_sbom_is_retained_not_transitive_coverage(tmp_path):
    files = [
        Path("rpds/rpds.so"),
        Path("rpds_py-1.dist-info/licenses/LICENSE"),
        Path("rpds_py-1.dist-info/sboms/rpds-py.cyclonedx.json"),
    ]
    for path in files:
        full = tmp_path / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text('{"all_targets":true}' if path.suffix == ".json" else "fixture bytes")
    dist = SimpleNamespace(files=files, version="2026.9.1", locate_file=lambda path: tmp_path / path)
    wheels = native.wheel_origins(dist)
    origin = native.inspect_origin(tmp_path / files[0], wheels)
    assert origin["component"] == "rpds-py" and origin["version"] == "2026.9.1"
    assert len(origin["notice_texts"]) == len(origin["provenance_files"]) == 1
    assert origin["status"] == "unresolved"
    assert any("all_targets=true" in gap and "Unicode-3.0" in gap for gap in origin["release_gates"])
    assert native.digest(tmp_path / files[-1]) == origin["provenance_files"][0]["sha256"]
    other = tmp_path / "rpds/adjacent.so"
    other.write_bytes(b"not in wheel RECORD")
    assert native.inspect_origin(other, wheels)["component"] == "unknown"
