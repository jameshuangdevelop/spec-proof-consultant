"""Schema, dependency, source-snapshot, and catalog-consistency validation."""

from __future__ import annotations

import hashlib
import json
import re
from importlib.resources import files
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .profiler import PATTERNS, SKIP_DIRS, is_secret, read_safe, safe_relative
from .source import code_view, definitions, inspect_source

METHODS = {
    "Kani": "bounded-model-checking",
    "CBMC": "bounded-model-checking",
    "Verus": "deductive-verification",
    "TLC": "explicit-state-model-checking",
    "Dafny": "verified-source-codegen",
}
NONCATALOG = {
    "native-tests": (
        "testing",
        "Executable tests cover only the examples or generated traces actually run; no proof is established.",
        ["Exhaustive correctness over unbounded inputs", "A deductive proof or native-verifier compatibility"],
    ),
    "source-inspection": (
        "source-inspection",
        "Read-only source and evidence inspection adds no executed test, model-checking result, or proof.",
        ["A successful verification run", "Tool compatibility established by execution"],
    ),
}


def resource(name: str) -> dict:
    return json.loads(files("spec_consultant").joinpath("data", name).read_text(encoding="utf-8"))


def schema_check(value: dict, schema: dict) -> None:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(value), key=lambda error: str(list(error.path)))
    if errors:
        error = errors[0]
        raise ValueError(f"schema {'.'.join(map(str, error.path)) or '<root>'}: {error.message}")


def check_graph(items: list[dict], key: str = "id", dependencies: str = "depends_on") -> None:
    by_id = {item[key]: item for item in items}
    if len(by_id) != len(items):
        raise ValueError("duplicate work item IDs")
    pending = set(by_id)
    finished = set()
    while pending:
        ready = {name for name in pending if set(by_id[name][dependencies]) <= finished}
        if not ready:
            raise ValueError("invalid dependency graph: missing dependency or cycle")
        finished.update(ready)
        pending -= ready


def validate_catalog(value: dict) -> None:
    schema_check(value, resource("catalog.schema.json"))
    ids = set()
    for entry in value["scenarios"]:
        if entry["id"] in ids:
            raise ValueError("duplicate scenario ID")
        ids.add(entry["id"])
        if METHODS[entry["tool"]] != entry["method"]:
            raise ValueError("tool/method mismatch")
        if not set(entry["patterns"] + entry["hard_exclusions"]) <= PATTERNS.keys():
            raise ValueError("catalog contains an unknown matching signal")
        check_graph(entry["work_items"], "key", "prerequisites")
        if entry["evidence_status"] != "documented":
            raise ValueError("reproduction claims require a future evidence-record schema")


def catalog() -> dict:
    value = resource("catalog.json")
    validate_catalog(value)
    return value


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def validate_profile(value: dict) -> None:
    schema = resource("assessment.schema.json")
    schema_check(value, {"$ref": "#/$defs/profile", "$defs": schema["$defs"]})
    roots = value["roots"]
    if len({root["id"] for root in roots}) != len(roots):
        raise ValueError("duplicate root IDs")
    if len({root["path"] for root in roots}) != len(roots):
        raise ValueError("duplicate root paths")
    for root in roots:
        if not Path(root["path"]).is_absolute():
            raise ValueError("root paths must be absolute")
        paths = set()
        for file in root["files"]:
            parts = safe_relative(file["path"]).parts
            if is_secret(file["path"]) or file["path"] in paths or set(parts) & SKIP_DIRS:
                raise ValueError("excluded or duplicate file path")
            paths.add(file["path"])
            if any(signal["line"] > file["lines"] for signal in file["signals"]):
                raise ValueError("signal outside source file")
            if value["version"] == "2" and "symbols" not in file:
                raise ValueError("v2 profiles require lexical symbol records")
            if any(
                symbol["line"] > symbol["end_line"] or symbol["end_line"] > file["lines"] + 1
                for symbol in file.get("symbols", [])
            ):
                raise ValueError("symbol outside source file")
        snapshot = hashlib.sha256("\n".join(f"{f['path']}:{f['sha256']}" for f in root["files"]).encode()).hexdigest()
        if snapshot != root["snapshot"]:
            raise ValueError("inconsistent profile snapshot")


def validate_assessment(value: dict, *, check_sources: bool = True) -> None:
    schema_check(value, resource("assessment.schema.json"))
    validate_profile(value["profile"])
    knowledge = catalog()
    if value["catalog_digest"] != digest(knowledge):
        raise ValueError("catalog changed; reassess against the installed catalog")
    scenarios = {entry["id"]: entry for entry in knowledge["scenarios"]}
    roots = {root["id"]: root for root in value["profile"]["roots"]}
    indexed = {(root["id"], file["path"]): file for root in roots.values() for file in root["files"]}
    checked = set()
    contents = {}

    def reference(ref: dict, *, executable: bool = False, check_symbol: bool = True) -> None:
        safe_relative(ref["path"])
        key = (ref["root"], ref["path"])
        file = indexed.get(key)
        if not file or ref["line"] > file["lines"]:
            raise ValueError(f"source reference not in inspected snapshot: {key}")
        if check_sources and key not in checked:
            root = roots[ref["root"]]
            data = read_safe(Path(root["path"]), ref["path"], root["limits"]["max_bytes"])
            if hashlib.sha256(data).hexdigest() != file["sha256"]:
                raise ValueError(f"stale source reference: {key}")
            contents[key] = data.decode("utf-8")
            checked.add(key)
        symbols = file.get("symbols")
        if check_sources and file["language"] in {"rust", "c", "cpp"}:
            code = code_view(contents[key], file["language"])
            symbols = definitions(code, file["language"])
            if executable and not code.splitlines()[ref["line"] - 1].strip():
                raise ValueError("executable target is in a comment, literal, or blank line")
        if ref["symbol"] and check_symbol:
            observed = (
                any(
                    symbol["name"] == ref["symbol"] and symbol["line"] <= ref["line"] <= symbol["end_line"]
                    for symbol in symbols
                )
                if symbols is not None
                else any(signal["symbol"] == ref["symbol"] for signal in file["signals"])
            )
            if not observed:
                declaration = (
                    not executable
                    and check_sources
                    and file["language"] == "rust"
                    and re.search(r"\bfn\s+" + re.escape(ref["symbol"]) + r"\b", code.splitlines()[ref["line"] - 1])
                )
                if not declaration:
                    raise ValueError(
                        "unobserved executable symbol at source reference; use null for non-symbol evidence"
                    )
        if executable and file["kind"] not in {"source", "specification", "test"}:
            raise ValueError("executable target must not be documentation, an example, or a benchmark")

    from .matcher import match_scenarios

    expected_matches = {
        (match["root"], match["scenario"]): match
        for match in match_scenarios(value["profile"], knowledge, value["context"])
    }
    pairs = set()
    for match in value["matches"]:
        entry = scenarios.get(match["scenario"])
        if not entry or match["scenario_version"] != entry["version"] or match["root"] not in roots:
            raise ValueError("unknown scenario version or repository root")
        pair = (match["root"], match["scenario"])
        if pair in pairs:
            raise ValueError("duplicate scenario match")
        pairs.add(pair)
        expected = expected_matches[pair]
        if match != expected:
            raise ValueError("static scenario decision/evidence differs from inspectable rules")
        if match["status"] == "candidate" and not match["targets"]:
            raise ValueError("candidate must cite source evidence")
        for ref in match["targets"]:
            if ref["root"] != match["root"]:
                raise ValueError("match target belongs to another root")
            reference(ref, check_symbol=value["profile"]["version"] != "1")
    if pairs != expected_matches.keys():
        raise ValueError("assessment must retain every scenario decision, including exclusions")
    check_graph(value["work_items"])
    by_id = {item["id"]: item for item in value["work_items"]}
    if not set(value["approval"]["grants"]) <= by_id.keys():
        raise ValueError("approval references unknown work")
    for item in value["work_items"]:
        entry = scenarios.get(item["scenario"])
        if item["tool"] in NONCATALOG:
            method, assurance, limits = NONCATALOG[item["tool"]]
            if (
                value["analysis"] != "agent-reviewed"
                or item["scenario"] is not None
                or item["scenario_version"] is not None
                or (item["method"], item["assurance"], item["does_not_establish"]) != (method, assurance, limits)
            ):
                raise ValueError("noncatalog testing/inspection needs reviewed work and honest assurance labels")
            if item["tool"] == "source-inspection" and item["kind"] != "evidence-gathering":
                raise ValueError("source inspection must be read-only evidence gathering")
            if item["tool"] == "native-tests" and item["scope"] != "harness":
                raise ValueError("native tests concern a harness, not a production or abstract-model proof")
        else:
            if not entry or item["scenario_version"] != entry["version"]:
                raise ValueError("unknown work scenario or version")
            for field in ("tool", "method", "assurance", "does_not_establish"):
                if item[field] != entry[field]:
                    raise ValueError(f"unsupported assurance claim or catalog drift: {field}")
        if item["readiness"] == "done":
            raise ValueError("assessment cannot claim executed work; result is not-run")
        if item["effort"]["min_hours"] > item["effort"]["max_hours"]:
            raise ValueError("invalid effort range")
        if item["provenance"] == "requirement-backed" and not item["requirement_refs"]:
            raise ValueError("requirement-backed work needs requirement source references")
        for ref in item["requirement_refs"]:
            reference(ref)
        for ref in item["targets"]:
            executable = item["tool"] in {"Kani", "CBMC", "Verus", "native-tests"}
            reference(ref, executable=executable)
            file = indexed[(ref["root"], ref["path"])]
            if entry:
                if "*" not in entry["languages"] and file["language"] not in entry["languages"]:
                    raise ValueError("work target language is not applicable to the selected scenario")
                match = expected_matches[(ref["root"], entry["id"])]
                if match["status"] != "candidate":
                    if value["analysis"] != "agent-reviewed":
                        raise ValueError("work item selects an excluded or unestablished scenario")
                    if item["kind"] == "implementation" and not item.get("review"):
                        raise ValueError("excluded/unestablished implementation needs an explicit scoped review")
        review = item.get("review")
        if review:
            if value["analysis"] != "agent-reviewed":
                raise ValueError("scoped eligibility requires agent review")
            included, excluded = set(review["included_files"]), set(review["excluded_files"])
            if included & excluded:
                raise ValueError("review includes and excludes the same file")
            target_files = {f"{ref['root']}:{ref['path']}" for ref in item["targets"]}
            if not target_files <= included:
                raise ValueError("scoped review omits a target file")
            for ref in review["source_refs"]:
                reference(ref)
            scoped_signals = set()
            for path in included | excluded:
                root_id, _, relative = path.partition(":")
                safe_relative(relative)
                file = indexed.get((root_id, relative))
                if not file:
                    raise ValueError("review boundary file must be in the inspected snapshot")
                if path in included:
                    signals = file["signals"]
                    if check_sources:
                        reference({"root": root_id, "path": relative, "line": 1, "symbol": None})
                        signals, _ = inspect_source(contents[(root_id, relative)], file["language"], PATTERNS)
                    scoped_signals.update(signal["kind"] for signal in signals)
            if entry and item["kind"] == "implementation" and set(entry["hard_exclusions"]) & scoped_signals:
                raise ValueError("reviewed implementation still contains a hard exclusion in its included files")
            if item["kind"] == "implementation" and item["readiness"] == "ready":
                raise ValueError("scoped compatibility is unknown; implementation cannot be ready")
        for path in item["likely_changed_files"]:
            root_id, separator, relative = path.partition(":")
            if not separator or root_id not in roots:
                raise ValueError("changed file must be root-id:relative-path")
            safe_relative(relative)
            if is_secret(relative) or set(safe_relative(relative).parts) & SKIP_DIRS:
                raise ValueError("excluded changed file")
        if item["readiness"] == "ready" and item["depends_on"]:
            raise ValueError("dependent work cannot be ready before prerequisites are executed")
        if item["readiness"] == "ready" and item["kind"] == "implementation":
            if (
                value["analysis"] != "agent-reviewed"
                or item["id"] not in value["approval"]["grants"]
                or item["provenance"] == "unresolved"
                or item["unknowns"]
            ):
                raise ValueError("implementation needs semantic review, explicit approval, resolved intent")
        if item["tool"] == "TLC" and item["scope"] != "separate-model":
            raise ValueError("TLC work must concern a separate model, not an implementation proof")
        if item["tool"] == "Dafny" and item["scope"] != "production":
            raise ValueError("Dafny option concerns verified-source production replacement")
        if value["context"]["adoption"] == "no-production-changes" and item["kind"] == "implementation":
            if item["scope"] == "production" or item["tool"] in {"Verus", "Dafny"}:
                raise ValueError("implementation conflicts with the no-production-changes adoption constraint")

    conclusions = value.get("conclusions", [])
    conclusion_ids = {conclusion["id"] for conclusion in conclusions}
    if len(conclusion_ids) != len(conclusions):
        raise ValueError("duplicate semantic conclusion IDs")
    linked = set()
    reviewed_roots = set()
    for conclusion in conclusions:
        if value["analysis"] != "agent-reviewed" or conclusion["root"] not in roots:
            raise ValueError("semantic conclusions require a reviewed, known repository root")
        reviewed_roots.add(conclusion["root"])
        if not set(conclusion["related_to"]) <= conclusion_ids or conclusion["id"] in conclusion["related_to"]:
            raise ValueError("unknown or self-related semantic conclusion")
        work_ids = set(conclusion["work_item_ids"])
        if not work_ids <= by_id.keys():
            raise ValueError("semantic conclusion references unknown work")
        if conclusion["disposition"] != "represented" or conclusion["kind"] == "no-new-work":
            if work_ids:
                raise ValueError("deferred, rejected, or no-new-work conclusions cannot authorize tasks")
        elif not work_ids:
            raise ValueError("represented opportunity/evidence conclusion must link its work")
        for work_id in work_ids:
            task = by_id[work_id]
            if any(ref["root"] != conclusion["root"] for ref in task["targets"]):
                raise ValueError("conclusion links work for another root")
            if conclusion["kind"] == "evidence-only" and task["kind"] != "evidence-gathering":
                raise ValueError("evidence-only conclusion must not introduce implementation work")
            if (
                conclusion.get("compatibility", {}).get("status") == "unknown"
                and task["kind"] == "implementation"
                and task["readiness"] == "ready"
            ):
                raise ValueError("conclusion compatibility is unknown; implementation cannot be ready")
        linked.update(work_ids)
        for ref in (
            conclusion["targets"] + conclusion["requirement_refs"] + conclusion.get("existing_assurance_refs", [])
        ):
            reference(ref)
            if ref["root"] != conclusion["root"]:
                raise ValueError("conclusion evidence belongs to another root")
        if conclusion["provenance"] == "requirement-backed" and not conclusion["requirement_refs"]:
            raise ValueError("requirement-backed conclusion needs requirement evidence")
        for component in conclusion.get("property_components", []):
            for ref in component["requirement_refs"]:
                reference(ref)
                if ref["root"] != conclusion["root"]:
                    raise ValueError("conclusion evidence belongs to another root")
            if component["provenance"] == "requirement-backed" and not component["requirement_refs"]:
                raise ValueError("requirement-backed component needs evidence")
    if value["version"] == "2" and value["analysis"] == "agent-reviewed":
        if reviewed_roots != roots.keys() or linked != by_id.keys():
            raise ValueError("reviewed handoff needs a disposition for every root and every retained work item")


def freshness(value: dict) -> list[str]:
    from .profiler import profile_root

    changes = []
    if value["profile"]["version"] == "1":
        return ["Profiling policy changed from v1 to v2; re-profile, retaining archived discovery as evidence."]
    for old in value["profile"]["roots"]:
        new = profile_root(Path(old["path"]), old["id"], **old["limits"])
        if new != old or new["changed_during_scan"]:
            changes.append(f"{old['id']}: snapshot, Git identity/status, coverage, or signals changed")
    return changes
