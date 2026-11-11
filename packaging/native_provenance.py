"""Data-only native attribution. Local observations are not license certification."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

CPYTHON_GAP = (
    "CPython incorporated/static notices unresolved: Mersenne Twister, select/kqueue, "
    "SipHash24, dtoa, cfuhash, asyncio and other incorporated code; top PSF license is not complete coverage"
)
RPDS_GAP = (
    "rpds Rust transitive notices/compiled inclusion unresolved: archery, rpds, libc, pyo3, "
    "unicode-ident (including Unicode-3.0), Cargo.lock/portable-atomic; "
    "wheel SBOM all_targets=true is not compiled inclusion evidence"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_record(path: Path) -> dict:
    real = path.resolve(strict=True)
    return {"path": str(path), "realpath": str(real), "sha256": digest(real), "bytes": real.stat().st_size}


def analysis_entries(path: Path) -> list[tuple[str, str, str]]:
    """Read PyInstaller's literal Analysis data, never import/eval a spec or TOC."""
    entries = []

    def walk(value):
        if not isinstance(value, (tuple, list)):
            return
        if len(value) == 3 and isinstance(value[2], str) and value[2] in {"BINARY", "EXTENSION"}:
            if not all(isinstance(item, str) and item for item in value):
                raise ValueError("invalid native Analysis entry")
            entries.append(tuple(value))
        else:
            for item in value:
                walk(item)

    walk(ast.literal_eval(path.read_text()))
    if not entries or len({entry[0] for entry in entries}) != len(entries):
        raise ValueError("missing or duplicate native Analysis destinations")
    return entries


def wheel_origins(dist) -> dict[str, dict]:
    """Only recorded wheel members count as origins, not arbitrary adjacent .so files."""
    files = [Path(dist.locate_file(item)) for item in dist.files or []]
    notices = [
        p
        for p in files
        if any(part.endswith(".dist-info") for part in p.parts)
        and p.name.lower().startswith(("license", "copying", "notice", "authors"))
    ]
    sboms = [p for p in files if "sboms" in p.parts and p.suffix == ".json"]
    identities = [
        p for p in files if p.parent.name.endswith(".dist-info") and p.name in {"METADATA", "WHEEL", "RECORD"}
    ]
    evidence, gaps = [], [RPDS_GAP]
    for path in notices + sboms + identities:
        if path.is_file() and path.stat().st_size:
            evidence.append(file_record(path))
        else:
            gaps.append(f"missing wheel evidence: {path.name}")
    if not notices:
        gaps.append("missing rpds-py top-level license text")
    if not sboms:
        gaps.append("missing rpds-py SBOM")
    return {
        str(p.resolve()): {
            "component": "rpds-py",
            "version": dist.version,
            "origin_kind": "installed-wheel",
            "notice_texts": [r for r in evidence if r["path"] in {str(n) for n in notices}],
            "provenance_files": [r for r in evidence if r["path"] in {str(s) for s in sboms + identities}],
            "release_gates": gaps,
        }
        for p in files
        if p.suffix == ".so"
    }


def inspect_origin(source: str | Path, wheels: dict[str, dict] | None = None) -> dict:
    source = Path(source)
    result = {
        "source_path": str(source),
        "source_realpath": str(source.resolve()),
        "source_sha256": None,
        "component": "unknown",
        "version": None,
        "origin_kind": "unknown",
        "notice_texts": [],
        "provenance_files": [],
        "release_gates": [],
    }
    gaps = result["release_gates"]
    try:
        result["source_sha256"] = digest(source.resolve(strict=True))
    except OSError:
        gaps.append("native source missing or unreadable")
        result["status"] = "unresolved"
        return result
    real = source.resolve()
    if str(real) in (wheels or {}):
        result.update(wheels[str(real)])
        # Do not let per-entry gates mutate the shared wheel description.
        result["release_gates"] = list(result["release_gates"])
    else:
        keg = next((p for p in real.parents if (p / "INSTALL_RECEIPT.json").exists() or (p / ".brew").is_dir()), None)
        if keg is not None:
            formula = keg.parent.name
            result.update(origin_kind="homebrew-keg", version=keg.name, formula=formula)
            for path in [keg / "INSTALL_RECEIPT.json", keg / ".brew" / f"{formula}.rb"]:
                try:
                    result["provenance_files"].append(file_record(path))
                    if path.suffix == ".json":
                        receipt = json.loads(path.read_text())
                        result["receipt_version"] = receipt.get("source", {}).get("versions", {}).get("stable")
                        if not result["receipt_version"]:
                            gaps.append("receipt source version unavailable")
                        elif result["receipt_version"] != keg.name.split("_", 1)[0]:
                            gaps.append("receipt source version differs from resolved keg version")
                except (OSError, ValueError, AttributeError, TypeError):
                    gaps.append(f"missing/invalid origin evidence: {path.name}")
            relative = real.relative_to(keg)
            texts = []
            if formula.startswith("python@") and (
                (real.name == "Python" and "Python.framework" in relative.parts)
                or (real.suffix == ".so" and "lib-dynload" in relative.parts)
            ):
                result["component"] = "CPython"
                texts = ["LICENSE"]
                gaps.append(CPYTHON_GAP)
            elif formula == "mpdecimal" and real.name.startswith("libmpdec.") and relative.parts[0] == "lib":
                result["component"] = "mpdecimal"
                texts = ["COPYRIGHT.txt"]
            elif formula.startswith("openssl@") and real.name.startswith(("libssl.", "libcrypto.")):
                result["component"] = "OpenSSL"
                texts = ["LICENSE.txt"]
                if (keg / "NOTICE").is_file():
                    texts.append("NOTICE")
                else:
                    gaps.append("OpenSSL upstream NOTICE presence/absence not established by installed keg")
            elif formula == "xz" and real.name.startswith("liblzma.") and relative.parts[0] == "lib":
                result["component"] = "liblzma"
                # COPYING explains the package split; do not assign GPL script licenses to liblzma.
                texts = ["COPYING", "COPYING.0BSD"]
            for name in texts:
                try:
                    record = file_record(keg / name)
                    if not record["bytes"]:
                        raise ValueError("empty notice")
                    result["notice_texts"].append(record)
                except (OSError, ValueError):
                    gaps.append(f"missing/empty native notice: {name}")
        if result["component"] == "unknown":
            gaps.append("unrecognized native component/origin; notice coverage unresolved")
    result["status"] = "unresolved" if result["release_gates"] else "local-texts-collected-review-required"
    return result


def native_inventory(
    analysis: Path, binary: Path, candidates: dict[str, dict], wheels: dict[str, dict], reader=None
) -> dict:
    """Bind every actual native entry to this binary; source and final hashes are separate."""
    entries = []
    for destination, source, kind in analysis_entries(analysis):
        item = inspect_origin(source, wheels)
        item.update(destination=destination, type=kind, final_member_sha256=None)
        prior = candidates.get(item["source_realpath"])
        if prior is None or prior["source_sha256"] != item["source_sha256"]:
            item["release_gates"].append("origin absent/changed since pre-freeze notice discovery")
        elif prior["notice_texts"] != item["notice_texts"]:
            item["release_gates"].append("notice texts changed since pre-freeze discovery")
        elif prior["provenance_files"] != item["provenance_files"]:
            item["release_gates"].append("provenance evidence changed since pre-freeze discovery")
        try:
            if reader is None or reader.toc[destination][-1] != "b":
                # In particular, do not hash a symlink target string as native member bytes.
                raise ValueError("not a binary archive member")
            member = reader.extract(destination) if reader is not None else None
            if not isinstance(member, bytes):
                raise ValueError("member unavailable")
            item["final_member_sha256"] = hashlib.sha256(member).hexdigest()
            item["final_member_status"] = "CArchive extracted bytes (may differ from relocated/signed source)"
        except (KeyError, OSError, ValueError):
            item["final_member_status"] = "unresolved: final member byte correspondence unavailable"
            item["release_gates"].append(item["final_member_status"])
        item["status"] = "unresolved" if item["release_gates"] else "local-texts-collected-review-required"
        entries.append(item)
    return {
        "format": 1,
        "binary_sha256": digest(binary),
        "analysis_sha256": digest(analysis),
        "release_qualified": False,
        "entries": entries,
        "release_gates": sorted(
            {
                "independent native/static/transitive provenance and license review pending",
                *(gate for item in entries for gate in item["release_gates"]),
            }
        ),
        "limitations": [
            "sidecar is not embedded; match binary_sha256 before using it",
            "local file/receipt/formula observations are not portable provenance identities; use hashes",
            "dynamic inventory does not establish static/transitive license coverage or legal approval",
        ],
    }


def retain_evidence(origins: list[dict], destination: Path) -> dict:
    """Retain exact local data bytes for offline review, without running formula code."""
    destination.mkdir(exist_ok=True)
    records = {}
    for origin in origins:
        for record in origin["notice_texts"] + origin["provenance_files"]:
            name = record["sha256"] + "-" + Path(record["path"]).name
            content = Path(record["realpath"]).read_bytes()
            if hashlib.sha256(content).hexdigest() != record["sha256"]:
                raise ValueError("native evidence changed during collection")
            (destination / name).write_bytes(content)
            records[name] = record
    return records
