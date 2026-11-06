"""Opt-in integration with retained, pinned evidence. Never rewrite the bundle."""

import copy
import hashlib
import json

import pytest

from spec_consultant.cli import main
from spec_consultant.matcher import assess
from spec_consultant.profiler import profile
from spec_consultant.validation import freshness, validate_assessment

from .review_helpers import conclusion, retained_review

PUBLIC_PINS = {
    "itoa": "1577ed901354d0d7448ac162328f9dbf5183124c",
    "jsmn": "25647e692c7906b96ffd2b05ca54c097948e879c",
    "tiny-aes": "23856752fbd139da0b8ca6e471a13d5bcc99a08d",
}


def retained_assessment(base, case):
    root = base / "targets" / ("public" if case in PUBLIC_PINS else "synthetic") / case
    value = assess(
        profile([str(root)]),
        goals=["arithmetic", "memory-safety", "functional-correctness", "state-invariants", "progress"],
        adoption="no-production-changes",
    )
    if case in PUBLIC_PINS:
        assert value["profile"]["roots"][0]["git"]["revision"] == PUBLIC_PINS[case]
        assert value["profile"]["roots"][0]["git"]["dirty"] is False
    return value


def test_pinned_itoa_primary_targets_are_live_production(evaluation_dir):
    value = retained_assessment(evaluation_dir, "itoa")
    targets = [ref for item in value["work_items"] for ref in item["targets"]]
    assert targets and all(target["symbol"] not in {"main", "do_bench"} for target in targets)
    assert all(target["path"] not in {"benches/bench.rs", "fuzz/fuzz_targets/fuzz_itoa.rs"} for target in targets)
    assert any(target["symbol"] == "format" for target in targets)
    validate_assessment(value)


@pytest.mark.parametrize("case", ["jsmn", "tiny-aes"])
def test_pinned_c_linkage_does_not_suppress_native_lead(evaluation_dir, case):
    value = retained_assessment(evaluation_dir, case)
    match = next(m for m in value["matches"] if m["scenario"] == "cbmc-c-buffer")
    assert match["status"] == "candidate"
    assert any("Unknown target compatibility" in unknown for unknown in match["unknowns"])
    validate_assessment(value)


def test_all_nine_semantic_conclusions_survive_canonical_handoff(evaluation_dir, tmp_path):
    # Fingerprint original report/results/recommendations and rejected payloads before/after.
    originals = [
        evaluation_dir / name
        for name in (
            "REPORT.md",
            "customer-expectations-results.json",
            "product-arm/recommendations.json",
            "semantic-review-ledger.json",
            "static-review-ledger.json",
            "regression-fixtures.md",
        )
    ] + list((evaluation_dir / "product-arm").glob("*/semantic-assessment-rejected.json"))
    hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in originals}
    rows = json.loads((evaluation_dir / "product-arm/recommendations.json").read_text())["recommendations"]
    discarded = json.loads((evaluation_dir / "product-arm/discarded-static-candidates.json").read_text())
    assert len(rows) == 9
    dispositions = {}
    for row in rows:
        value = retained_review(retained_assessment(evaluation_dir, row["case"]), row)
        main_record = value["conclusions"][0]
        # Discarded historical leads are source evidence, not live targets or resurrected tasks.
        for index, lead in enumerate(lead for lead in discarded if lead["case"] == row["case"]):
            references = [dict(target, symbol=None) for target in lead["static_targets"]]
            record = conclusion(f"{row['id']}-discarded-{index}", references, disposition="rejected")
            record.update(
                property=lead["scenario"] + " provisional pilot", reason=lead["reason"], related_to=[row["id"]]
            )
            value["conclusions"].append(record)
        expected_matches = copy.deepcopy(value["matches"])
        validate_assessment(value)
        assert not freshness(value)
        directory = tmp_path / row["case"]
        directory.mkdir()
        canonical = directory / "assessment.json"
        canonical.write_text(json.dumps(value, indent=2) + "\n")
        assert main(["validate", str(canonical)]) == 0
        assert main(["render", str(canonical), "--out", str(directory)]) == 0
        reloaded = json.loads(canonical.read_text())
        assert reloaded["matches"] == expected_matches
        assert reloaded["conclusions"][0] == main_record
        assert not reloaded["approval"]["grants"]
        assert all(item["result"] == "not-run" for item in reloaded["work_items"])
        assert all(
            item["readiness"] == "blocked" for item in reloaded["work_items"] if item["kind"] == "implementation"
        )
        assert main_record["property"] == row["property"]
        assert main_record["input_domain"] == row["input_domain"]
        assert main_record["postconditions"] == row["postconditions"]
        assert main_record["counterexample_conditions"] == row["counterexample_conditions"]
        assert main_record["requirement_refs"] == row["requirement_refs"]
        assert main_record["existing_assurance_refs"] == row["existing_assurance_refs"]
        for name in ("report.md", "backlog.md", "orchestrator.md"):
            text = (directory / name).read_text()
            # Assert semantic obligations/limits, not a JSON or text snapshot.
            for statement in (
                row["property"],
                row["input_domain"],
                row["rationale"],
                row["existing_assurance"],
                row["marginal_addition"],
                row["method"]["plan"],
                row["compatibility_status"]["details"],
                *row["observations"],
                *row["preconditions"],
                *row["postconditions"],
                *row["counterexample_conditions"],
                *row["assurance_limits"],
                *row["adoption_constraints"],
                *(alternative["reason"] for alternative in row["alternatives"]),
            ):
                assert statement in text, (row["id"], name, statement)
            for component in main_record["property_components"]:
                assert component["property"] in text and component["provenance"] in text
                assert component["disposition"] in text and component["reason"] in text
            for item in reloaded["work_items"]:
                assert item["id"] in text and item["readiness"] in text
                if item.get("review"):
                    assert "Included files: " + ", ".join(item["review"]["included_files"]) in text
                    assert (
                        "Excluded files/boundaries: " + (", ".join(item["review"]["excluded_files"]) or "none recorded")
                        in text
                    )
                    assert item["review"]["rationale"] in text
            for rejection in value["conclusions"][1:]:
                assert rejection["reason"] in text and "rejected" in text
        if row["case"] in {"jsmn", "tiny-aes"}:
            assert all(task["tool"] == "CBMC" for task in value["work_items"])
        if row["case"] == "mixed-boundary":
            assert next(m for m in value["matches"] if m["scenario"] == "kani-rust-arithmetic")["status"] == "excluded"
            assert all(target["path"] == "src/kernel.rs" for task in value["work_items"] for target in task["targets"])
        if row["case"] == "python-gap":
            assert value["work_items"][1]["tool"] == "native-tests"
            assert value["work_items"][1]["scenario"] is None
        if row["case"] in {"unsupported", "no-work"}:
            assert not value["work_items"] and main_record["kind"] == "no-new-work"
        if row["case"] == "existing-proof":
            assert len(value["work_items"]) == 1 and value["work_items"][0]["kind"] == "evidence-gathering"
        dispositions[row["id"]] = main_record["disposition"]
    assert len(dispositions) == 9 and set(dispositions.values()) == {"represented"}
    assert hashes == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in originals}
    (tmp_path / "dispositions.json").write_text(json.dumps(dispositions, indent=2) + "\n")


def test_legacy_static_exclusion_remains_immutable_during_review(evaluation_dir):
    # Keep original discovery evidence; a new scoped record does not rewrite a legacy match.
    base = json.loads((evaluation_dir / "static/mixed-boundary/assessment/assessment.json").read_text())
    original = copy.deepcopy(base["matches"])
    row = next(
        row
        for row in json.loads((evaluation_dir / "product-arm/recommendations.json").read_text())["recommendations"]
        if row["case"] == "mixed-boundary"
    )
    base["version"] = "2"
    value = retained_review(base, row)
    validate_assessment(value)
    assert value["matches"] == original


def test_retained_r6_r7_negatives_have_explicit_dispositions(evaluation_dir):
    rows = json.loads((evaluation_dir / "product-arm/recommendations.json").read_text())["recommendations"]
    for row in rows:
        if row["case"] in {"unsupported", "no-work"}:
            value = retained_review(retained_assessment(evaluation_dir, row["case"]), row)
            validate_assessment(value)
            assert not value["work_items"]
            assert value["conclusions"][0]["reason"] == row["rationale"]
