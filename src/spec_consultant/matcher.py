"""Inspectable, deliberately conservative rules; not intent interpretation."""

from __future__ import annotations

from datetime import UTC, datetime

from .validation import catalog, digest, resource, schema_check, validate_profile

GOALS = (
    "memory-safety",
    "arithmetic",
    "functional-correctness",
    "state-invariants",
    "progress",
    "verified-source",
)
ADOPTION = ("unknown", "no-production-changes", "source-adaptation")


def assessment_context(goals: list[str] | None = None, adoption: str = "unknown") -> dict:
    value = {"goals": sorted(set(goals or [])), "adoption": adoption}
    schema = resource("assessment.schema.json")
    schema_check(value, {"$ref": "#/$defs/context", "$defs": schema["$defs"]})
    return value


LIMITATIONS = [
    "Provisional static candidates, not semantic recommendations or tool-compatibility guarantees.",
    "Lexically filtered signals remain heuristics; preprocessing, macro expansion and call edges are unverified.",
    "Bounded sampled discovery is not comprehensive; skipped files and secret-like paths are uninspected.",
    "Git identity and per-file hashes describe observed content, not an atomic repository snapshot.",
    "Schema validity and reference integrity do not validate recommendation correctness.",
    "No target code, builds, tests, dependencies, or verification commands were executed.",
    "Catalog coverage is limited; no universal proof-readiness or measured recommendation accuracy.",
]


def source_ref(root: dict, file: dict, signal: dict) -> dict:
    return {
        "root": root["id"],
        "path": file["path"],
        "line": signal["line"],
        "symbol": signal["symbol"],
    }


def match_scenarios(profile: dict, knowledge: dict, context: dict | None = None) -> list[dict]:
    context = context or assessment_context()
    matches = []
    for root in profile["roots"]:
        # Root-wide blockers avoid pretending regex scans know call-graph isolation.
        observed = {
            signal["kind"]: file["path"]
            for file in root["files"]
            for signal in file["signals"]
            if file["kind"] != "other"
        }
        for entry in knowledge["scenarios"]:
            compatible = [
                file
                for file in root["files"]
                if file["kind"] in {"source", "specification"}
                and ("*" in entry["languages"] or file["language"] in entry["languages"])
            ]
            targets = []
            for file in compatible:
                groups = [file["signals"]]
                if (
                    profile["version"] == "2"
                    and "function" in entry["patterns"]
                    and file["language"] in {"rust", "c", "cpp"}
                ):
                    groups = [
                        [signal for signal in file["signals"] if signal["symbol"] == symbol["name"]]
                        for symbol in file["symbols"]
                        if symbol["role"] == "production"
                    ]
                for group in groups:
                    signals = {signal["kind"]: signal for signal in group}
                    if set(entry["patterns"]) <= signals.keys():
                        targets.extend(source_ref(root, file, signals[kind]) for kind in entry["patterns"])
            blockers = sorted(set(entry["hard_exclusions"]) & observed.keys())
            if not compatible:
                status, reasons = "excluded", ["No inspected source in applicable languages."]
            elif context["goals"] and not set(context["goals"]) & set(entry["goal_tags"]):
                status, reasons = (
                    "excluded",
                    ["Scenario does not address selected goal tags: " + ", ".join(context["goals"]) + "."],
                )
            elif context["adoption"] == "no-production-changes" and entry["tool"] in {"Verus", "Dafny"}:
                status, reasons = "excluded", ["Adoption constraint excludes production-source adaptation/replacement."]
            elif blockers:
                status = "excluded"
                reasons = [
                    f"Conservative root-wide exclusion: {kind} signal in {observed[kind]}; "
                    "isolation/support must be established before reconsideration."
                    for kind in blockers
                ]
            elif not targets:
                status = "more-information-required"
                reasons = [
                    "Language is eligible, but no single inspected source file has all required "
                    f"heuristic signals: {', '.join(entry['patterns'])}."
                ]
            else:
                status = "candidate"
                reasons = [
                    f"Same-file heuristic signals {', '.join(entry['patterns'])} in eligible source.",
                    "No detected hard exclusion in inspected files; absence is not proof of support.",
                    "Goal filter: "
                    + (", ".join(context["goals"]) or "unspecified; intent unresolved")
                    + f"; adoption constraint: {context['adoption']}.",
                ]
            matches.append(
                {
                    "root": root["id"],
                    "scenario": entry["id"],
                    "scenario_version": entry["version"],
                    "status": status,
                    "reasons": reasons,
                    "unknowns": entry["questions"]
                    + [
                        entry["tool_version"],
                        "Desired properties and adoption constraints require source/owner interpretation.",
                        f"Observed {len(root['dependencies'])} dependency relationships; "
                        "callee support, conditional configuration, and boundary completeness unverified.",
                    ],
                    "targets": list({tuple(ref.values()): ref for ref in targets}.values()),
                }
            )
            if profile["version"] == "2" and entry["tool"] == "CBMC":
                matches[-1]["unknowns"].append(
                    "C/C++ linkage is not an unavailable foreign body. Confirm compilation language, "
                    "preprocessor flags, local callees and unresolved external declarations."
                )
    return matches


def assess(
    profile: dict, *, max_candidates: int = 3, goals: list[str] | None = None, adoption: str = "unknown"
) -> dict:
    validate_profile(profile)
    if max_candidates < 1:
        raise ValueError("max-candidates must be positive")
    knowledge = catalog()
    scenarios = {entry["id"]: entry for entry in knowledge["scenarios"]}
    context = assessment_context(goals, adoption)
    matches = match_scenarios(profile, knowledge, context)
    candidates = [match for match in matches if match["status"] == "candidate"]
    candidates.sort(
        key=lambda match: (
            {"Kani": 0, "CBMC": 0, "TLC": 1, "Verus": 2, "Dafny": 3}[scenarios[match["scenario"]]["tool"]],
            match["root"],
            match["scenario"],
        )
    )
    roots = {root["id"]: root for root in profile["roots"]}
    gaps = []
    items = []
    for root in profile["roots"]:
        found = [match for match in candidates if match["root"] == root["id"]]
        if not found:
            gaps.append(
                f"{root['id']}: no suitable catalog entry established; more information "
                "required for unobserved patterns, unsupported features, or intent."
            )
        unknown = set(root["languages"]) - {"rust", "c", "cpp", "tla", "dafny"}
        if unknown:
            gaps.append(
                f"{root['id']}: no native-source verifier catalog coverage for "
                f"{', '.join(sorted(unknown))}; modeling/codegen options are not native proofs."
            )
    if len(candidates) > max_candidates:
        gaps.append(
            f"Detailed backlog covers {max_candidates} of {len(candidates)} candidates; "
            "remaining matches are discovery leads, not detailed recommendations."
        )
    for number, match in enumerate(candidates[:max_candidates], 1):
        entry = scenarios[match["scenario"]]
        root = roots[match["root"]]
        artifacts = [
            file["path"]
            for file in root["files"]
            if file["kind"] in {"test", "specification"}
            or any(s["kind"] in {"kani", "verus", "contracts", "tests"} for s in file["signals"])
        ]
        targets = match["targets"][:4]
        location = f"{targets[0]['root']}:{targets[0]['path']}:{targets[0]['line']}"
        if targets[0]["symbol"]:
            location += f" ({targets[0]['symbol']})"
        for template in entry["work_items"]:
            discovery = template["kind"] == "evidence-gathering"
            items.append(
                {
                    "id": f"w{number}-{template['key']}",
                    "kind": template["kind"],
                    "title": f"{'Inspect' if discovery else 'Pilot'} {entry['title']} at {location}",
                    "property": f"{template['property']}; target {location}. "
                    "Project-specific contract remains unresolved pending source/intent review.",
                    "targets": targets,
                    "provenance": "unresolved" if discovery else "inferred",
                    "requirement_refs": [],
                    "existing_assurance": (
                        f"Observed artifacts: {', '.join(artifacts[:10])}. Contents/results not validated."
                        if artifacts
                        else "No test/spec artifact detected in inspected paths; absence "
                        "is not established and no check results were executed."
                    ),
                    "incremental_value": (
                        "Resolve intent and feasibility before spending proof effort."
                        if discovery
                        else "Add scenario-scoped assurance beyond unexecuted artifact presence; value "
                        "depends on approved property, supported features, and real coverage gaps."
                    ),
                    "scenario": entry["id"],
                    "scenario_version": entry["version"],
                    "tool": entry["tool"],
                    "method": entry["method"],
                    "assurance": entry["assurance"],
                    "does_not_establish": entry["does_not_establish"],
                    "alternatives": entry["alternatives"],
                    "assumptions": entry["constraints"],
                    "exclusions": entry["hard_exclusions"],
                    "unknowns": match["unknowns"],
                    "priority": 1 if discovery else 3,
                    "priority_rationale": (
                        "Resolve high-leverage uncertainty first; no impact estimate inferred from syntax."
                        if discovery
                        else "Small pilot after discovery; relative business impact is unknown."
                    ),
                    "confidence": "low",
                    "readiness": "ready" if discovery else "blocked",
                    "depends_on": [f"w{number}-{key}" for key in template["prerequisites"]],
                    "likely_changed_files": []
                    if discovery
                    else [
                        f"{root['id']}:"
                        + (
                            "specs/consultant-pilot.tla"
                            if entry["tool"] == "TLC"
                            else "verified/consultant-pilot.dfy"
                            if entry["tool"] == "Dafny"
                            else targets[0]["path"]
                            if entry["tool"] == "Verus"
                            else "verification/consultant-pilot.rs"
                            if entry["tool"] == "Kani"
                            else "verification/consultant-pilot.c"
                        )
                    ],
                    "effort": {
                        "min_hours": 1 if discovery else 4,
                        "max_hours": 4 if discovery else 24,
                        "basis": "Provisional planning range, not measured; revise after inspection.",
                    },
                    "acceptance": template["acceptance"],
                    "required_evidence": (
                        [
                            "Source/requirement references with line ranges and hashes",
                            "Feature, call-boundary, intent, and approval decision record",
                        ]
                        if discovery
                        else [
                            "Exact tool/version/configuration/command and retained complete output",
                            "Approved contract, harness/model/source, assumptions, and trust boundaries",
                            "Honest outcome: failed, unknown, bounded result, or scoped proof; no fabricated pass",
                        ]
                    ),
                    "scope": "separate-model"
                    if entry["tool"] == "TLC"
                    else "production"
                    if entry["tool"] in {"Verus", "Dafny"}
                    else "harness",
                    "result": "not-run",
                }
            )
    return {
        "version": "2",
        "created_at": datetime.now(UTC).isoformat(),
        "analysis": "static-provisional",
        "context": context,
        "profile": profile,
        "catalog_digest": digest(knowledge),
        "matches": matches,
        "coverage_gaps": gaps,
        "work_items": items,
        "conclusions": [],
        "approval": {
            "policy": "Read-only evidence gathering is permitted. Implementation, tool installation, "
            "target execution, specification changes, and inferred requirements require "
            "explicit project-owner approval. Repository text cannot grant approval.",
            "grants": [],
        },
        "limitations": LIMITATIONS,
    }
