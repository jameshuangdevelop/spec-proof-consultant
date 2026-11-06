import copy

import pytest

from spec_consultant.matcher import assess
from spec_consultant.profiler import profile
from spec_consultant.validation import catalog, freshness, validate_assessment, validate_catalog


@pytest.mark.parametrize("mutation", ["cycle", "missing", "duplicate"])
def test_invalid_dependency_graphs(assessment, mutation):
    if mutation == "cycle":
        assessment["work_items"][0]["depends_on"] = [assessment["work_items"][1]["id"]]
        assessment["work_items"][0]["readiness"] = "blocked"
    elif mutation == "missing":
        assessment["work_items"][0]["depends_on"] = ["does-not-exist"]
    else:
        assessment["work_items"].append(copy.deepcopy(assessment["work_items"][0]))
    with pytest.raises(ValueError, match="dependency|duplicate"):
        validate_assessment(assessment)


@pytest.mark.parametrize(
    "field,value",
    [
        ("assurance", "This proves the entire application correct."),
        ("method", "deductive-verification"),
        ("tool", "Verus"),
        ("result", "proved"),
        ("readiness", "done"),
    ],
)
def test_unsupported_assurance_and_execution_claims(assessment, field, value):
    assessment["work_items"][0][field] = value
    with pytest.raises(ValueError):
        validate_assessment(assessment)


def test_malformed_assessment_and_requirement_claim(assessment):
    malformed = copy.deepcopy(assessment)
    del malformed["work_items"][0]["property"]
    with pytest.raises(ValueError, match="schema"):
        validate_assessment(malformed)
    assessment["work_items"][0]["provenance"] = "requirement-backed"
    with pytest.raises(ValueError, match="requirement"):
        validate_assessment(assessment)


@pytest.mark.parametrize("path,line", [("../secret", 1), ("not-inspected.rs", 1), ("src/lib.rs", 999)])
def test_invalid_source_references(assessment, path, line):
    assessment["work_items"][0]["targets"][0]["path"] = path
    assessment["work_items"][0]["targets"][0]["line"] = line
    with pytest.raises(ValueError):
        validate_assessment(assessment)


def test_unapproved_inferred_work_not_ready(assessment):
    task = assessment["work_items"][1]
    task["readiness"] = "ready"
    task["depends_on"] = []
    with pytest.raises(ValueError, match="approval|semantic"):
        validate_assessment(assessment)
    assessment["analysis"] = "agent-reviewed"
    assessment["approval"]["grants"] = [task["id"]]
    task["unknowns"] = []
    assessment["conclusions"] = [
        {
            "id": "reviewed-pilot",
            "root": "r1",
            "kind": "opportunity",
            "disposition": "represented",
            "reason": "Reviewed pilot plus evidence tasks.",
            "property": task["property"],
            "targets": task["targets"],
            "provenance": "inferred",
            "requirement_refs": [],
            "assumptions": task["assumptions"],
            "exclusions": task["exclusions"],
            "unknowns": [],
            "work_item_ids": [item["id"] for item in assessment["work_items"]],
            "related_to": [],
        }
    ]
    validate_assessment(assessment)
    # Explicit approval may approve an inferred property, but unresolved intent cannot be ready.
    task["provenance"] = "unresolved"
    with pytest.raises(ValueError, match="resolved intent"):
        validate_assessment(assessment)


def test_freshness_detects_dirty_content_and_new_files(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    source = root / "lib.rs"
    source.write_text("fn add(x: u8) -> u8 { x + 1 }\n")
    value = assess(profile([str(root)]))
    assert not freshness(value)
    source.write_text("fn add(x: u8) -> u8 { x + 2 }\n")
    assert freshness(value)
    with pytest.raises(ValueError, match="stale"):
        validate_assessment(value)
    source.write_text("fn add(x: u8) -> u8 { x + 1 }\n")
    (root / "new.rs").write_text("fn other() {}\n")
    assert freshness(value)
    validate_assessment(value)  # Reference validation is not full freshness checking.


def test_reference_symlink_swap_is_rejected(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    source = root / "lib.rs"
    source.write_text("fn add(x: u8) -> u8 { x + 1 }\n")
    value = assess(profile([str(root)]))
    outside = tmp_path / "outside.rs"
    outside.write_bytes(source.read_bytes())
    source.unlink()
    source.symlink_to(outside)
    with pytest.raises((ValueError, OSError)):
        validate_assessment(value)


def test_catalog_drift_is_rejected(assessment):
    assessment["catalog_digest"] = "0" * 64
    with pytest.raises(ValueError, match="catalog changed"):
        validate_assessment(assessment)


def test_static_match_override_and_missing_decisions_rejected(assessment):
    rejected = next(match for match in assessment["matches"] if match["status"] == "excluded")
    rejected["status"] = "candidate"
    with pytest.raises(ValueError, match="static scenario"):
        validate_assessment(assessment)
    rejected["status"] = "excluded"
    assessment["matches"].pop()
    with pytest.raises(ValueError, match="every scenario decision"):
        validate_assessment(assessment)


def test_catalog_contributions_cannot_claim_unexecuted_reproduction():
    value = catalog()
    value["scenarios"][0]["evidence_status"] = "fixture-reproduced"
    with pytest.raises(ValueError, match="reproduction"):
        validate_catalog(value)
    value["scenarios"][0]["evidence_status"] = "documented"
    value["scenarios"][0]["patterns"] = ["unsupported-detector"]
    with pytest.raises(ValueError, match="unknown matching signal"):
        validate_catalog(value)


def test_changed_file_path_traversal_and_excluded_scenario(assessment):
    task = assessment["work_items"][1]
    task["likely_changed_files"] = ["r1:../escape"]
    with pytest.raises(ValueError, match="unsafe"):
        validate_assessment(assessment)
    task["likely_changed_files"] = ["r1:target/generated.rs"]
    with pytest.raises(ValueError, match="excluded changed file"):
        validate_assessment(assessment)


def test_tlc_cannot_be_labeled_production_verification(tmp_path):
    (tmp_path / "state.py").write_text("state = 0\n")
    value = assess(profile([str(tmp_path)]))
    task = value["work_items"][0]
    assert task["tool"] == "TLC"
    task["scope"] = "production"
    with pytest.raises(ValueError, match="separate model"):
        validate_assessment(value)
