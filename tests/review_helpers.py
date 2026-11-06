"""Construct reviewed assessment data; never import or execute target code."""

import copy

from spec_consultant.validation import catalog

TEST_ASSURANCE = "Executable tests cover only the examples or generated traces actually run; no proof is established."
TEST_LIMITS = ["Exhaustive correctness over unbounded inputs", "A deductive proof or native-verifier compatibility"]
INSPECTION_ASSURANCE = (
    "Read-only source and evidence inspection adds no executed test, model-checking result, or proof."
)
INSPECTION_LIMITS = ["A successful verification run", "Tool compatibility established by execution"]


def ref(path, line=1, symbol=None, root="r1"):
    return {"root": root, "path": path, "line": line, "symbol": symbol}


def work(identifier, targets, *, scenario="kani-rust-arithmetic", kind="evidence-gathering"):
    entry = next((entry for entry in catalog()["scenarios"] if entry["id"] == scenario), None)
    tool = entry["tool"] if entry else "native-tests" if kind == "implementation" else "source-inspection"
    return {
        "id": identifier,
        "kind": kind,
        "title": identifier,
        "property": "Source-backed proposal",
        "targets": targets,
        "provenance": "inferred",
        "requirement_refs": [],
        "existing_assurance": "Artifact status unconfirmed; no target execution.",
        "incremental_value": "Resolve the scoped requirement and evidence gap.",
        "scenario": scenario,
        "scenario_version": entry["version"] if entry else None,
        "tool": tool,
        "method": entry["method"] if entry else "testing" if tool == "native-tests" else "source-inspection",
        "assurance": entry["assurance"]
        if entry
        else TEST_ASSURANCE
        if tool == "native-tests"
        else INSPECTION_ASSURANCE,
        "does_not_establish": entry["does_not_establish"]
        if entry
        else TEST_LIMITS
        if tool == "native-tests"
        else INSPECTION_LIMITS,
        "alternatives": [],
        "assumptions": ["No approval to execute targets."],
        "exclusions": entry["hard_exclusions"] if entry else ["No formal proof or invented native verifier."],
        "unknowns": ["Pinned compatibility remains unknown."],
        "priority": 3,
        "priority_rationale": "Provisional marginal value; review before investment.",
        "confidence": "low",
        "readiness": "blocked" if kind == "implementation" else "ready",
        "depends_on": [],
        "likely_changed_files": [],
        "effort": {"min_hours": 1, "max_hours": 4, "basis": "Provisional, not measured."},
        "acceptance": ["Preserve requirements and record exact source/evidence boundaries."],
        "required_evidence": ["Exact source hashes, requirements, and approval; no invented execution."],
        "scope": "harness",
        "result": "not-run",
    }


def scoped(targets, included, excluded=()):
    return {
        "rationale": "Inspect the exact included source and its callees; unrelated boundaries remain excluded.",
        "source_refs": targets,
        "included_files": included,
        "excluded_files": list(excluded),
        "configuration": ["External harness only; source unchanged; compiler/platform flags remain unresolved."],
        "compatibility": "unknown",
    }


def conclusion(identifier, targets, items=(), *, kind="opportunity", disposition="represented"):
    return {
        "id": identifier,
        "root": targets[0]["root"],
        "kind": kind,
        "disposition": disposition,
        "reason": "Source review recorded explicitly; execution remains unapproved.",
        "property": "Reviewed source/requirement conclusion",
        "targets": targets,
        "provenance": "inferred",
        "requirement_refs": [],
        "assumptions": [],
        "exclusions": [],
        "unknowns": [],
        "work_item_ids": [item["id"] for item in items],
        "related_to": [],
    }


def reviewed(value, items, conclusions):
    value["analysis"] = "agent-reviewed"
    value["work_items"] = items
    value["conclusions"] = conclusions
    return value


def retained_review(value, row):
    """Preserve the retained agent's semantics, adding structural dispositions, not tool evidence."""
    targets = copy.deepcopy(row["target_refs"])
    kind = (
        "no-new-work"
        if row["disposition"] == "no-new-work"
        else ("evidence-only" if row["method"]["type"] == "evidence-gathering" else "opportunity")
    )
    items = []
    if kind != "no-new-work":
        evidence = work(row["id"] + "-evidence", targets, scenario=row["catalog_scenario"])
        items.append(evidence)
        if kind == "opportunity":
            pilot = work(row["id"] + "-pilot", targets, scenario=row["catalog_scenario"], kind="implementation")
            pilot["depends_on"] = [evidence["id"]]
            items.append(pilot)
        for item in items:
            item.update(
                {
                    "title": row["property"],
                    "property": row["property"],
                    "provenance": row["requirement_status"],
                    "requirement_refs": row["requirement_refs"],
                    "existing_assurance": row["existing_assurance"],
                    "incremental_value": row["marginal_addition"],
                    "assumptions": row["preconditions"] + row["adoption_constraints"],
                    "exclusions": list(dict.fromkeys(item["exclusions"] + row["assurance_limits"])),
                    "unknowns": [row["compatibility_status"]["details"]],
                    "priority_rationale": row["rationale"],
                }
            )
            if row["catalog_scenario"]:
                included = {target["path"] for target in targets}
                if row["case"] == "tiny-aes":
                    included.add("aes.h")
                excluded = [
                    "r1:" + file["path"]
                    for file in value["profile"]["roots"][0]["files"]
                    if file["kind"] in {"source", "benchmark", "example"} and file["path"] not in included
                ]
                item["review"] = scoped(targets, ["r1:" + path for path in sorted(included)], excluded)
                item["review"]["rationale"] = row["compatibility_status"]["details"]
                item["review"]["configuration"] = [row["method"]["plan"]]
    record = conclusion(row["id"], targets, items, kind=kind)
    record.update(
        {
            "property": row["property"],
            "reason": row["rationale"],
            "provenance": row["requirement_status"],
            "requirement_refs": row["requirement_refs"],
            "assumptions": row["preconditions"] + row["adoption_constraints"],
            "exclusions": row["assurance_limits"],
            "unknowns": [row["compatibility_status"]["details"]],
            "input_domain": row["input_domain"],
            "postconditions": row["postconditions"],
            "counterexample_conditions": row["counterexample_conditions"],
            "existing_assurance": row["existing_assurance"],
            "existing_assurance_refs": row["existing_assurance_refs"],
            "compatibility": row["compatibility_status"],
            "incremental_value": row["marginal_addition"],
            "method_plan": f"{row['method']['tool']} / {row['method']['type']}: {row['method']['plan']}",
            "observations": row["observations"],
            "alternatives": [
                {"tool": alternative["method"], "reason": alternative["reason"]} for alternative in row["alternatives"]
            ],
            "property_components": [
                {
                    "property": component["property"],
                    "provenance": component["requirement_status"],
                    "requirement_refs": component["requirement_refs"],
                    "disposition": "deferred" if component["requirement_status"] == "unresolved" else "represented",
                    "reason": "Unresolved intent is outside the executable contract pending clarification."
                    if component["requirement_status"] == "unresolved"
                    else "Retain this provenance; inference is not approval.",
                }
                for component in row["property_components"]
            ],
        }
    )
    return reviewed(value, items, [record])
