import pytest

from spec_consultant.matcher import assess
from spec_consultant.profiler import profile
from spec_consultant.validation import catalog, validate_assessment

from .conftest import FIXTURES


def statuses(value):
    return {match["scenario"]: match["status"] for match in value["matches"]}


def test_correct_rust_candidates_and_incorrect_c_matches(assessment):
    matches = statuses(assessment)
    assert matches["kani-rust-slices"] == "candidate"
    assert matches["verus-rust-integer-contract"] == "candidate"
    assert matches["cbmc-c-buffer"] == "excluded"
    assert matches["tla-concurrency-liveness"] != "candidate"
    validate_assessment(assessment)
    assert all(item["result"] == "not-run" for item in assessment["work_items"])
    assert all(item["readiness"] == "blocked" for item in assessment["work_items"] if item["kind"] == "implementation")


def test_native_buffer_and_bitvectors():
    result = assess(profile([str(FIXTURES / "native")]))
    matches = statuses(result)
    assert matches["cbmc-c-buffer"] == "candidate"
    assert matches["cbmc-c-bitvector"] == "candidate"
    assert matches["kani-rust-slices"] == "excluded"


def test_mixed_language_ffi_conservatively_blocks_native_proofs():
    result = assess(profile([str(FIXTURES / "boundaries")]))
    matches = statuses(result)
    assert matches["kani-rust-unsafe-memory"] == "excluded"
    assert matches["verus-rust-sequence-invariant"] == "excluded"
    assert matches["cbmc-c-buffer"] == "excluded"
    reason = " ".join(text for match in result["matches"] for text in match["reasons"])
    assert "ffi" in reason
    assert not result["work_items"]


@pytest.mark.parametrize(
    ("feature", "source"),
    [
        ("async", "async fn f(x: u8) -> u8 { x + 1 }"),
        ("assembly", 'fn f(x: u8) -> u8 { asm!("nop"); x + 1 }'),
        ("dynamic_dispatch", "fn f(x: &dyn Trait) -> u8 { 1 + 1 }"),
    ],
)
def test_unsupported_features_not_language_only_matches(tmp_path, feature, source):
    (tmp_path / "lib.rs").write_text(source)
    result = assess(profile([str(tmp_path)]))
    match = next(m for m in result["matches"] if m["scenario"] == "kani-rust-arithmetic")
    assert match["status"] == "excluded"
    assert feature in " ".join(match["reasons"])


def test_language_only_and_unknown_language_are_not_matches(tmp_path):
    (tmp_path / "empty.rs").write_text("// No function or desired property provided.\n")
    result = assess(profile([str(tmp_path)]))
    assert statuses(result)["kani-rust-arithmetic"] == "more-information-required"
    assert result["work_items"] == []
    assert result["coverage_gaps"]
    (tmp_path / "empty.rs").unlink()
    (tmp_path / "unknown.xyz").write_text("unknown source")
    result = assess(profile([str(tmp_path)]))
    assert not result["work_items"]
    assert any("no suitable catalog entry" in gap for gap in result["coverage_gaps"])


def test_separate_concurrency_model_not_native_proof(tmp_path):
    (tmp_path / "lib.rs").write_text("fn work(x: u8) -> u8 { std::thread::spawn(|| {}); x + 1 }\n")
    result = assess(profile([str(tmp_path)]))
    assert statuses(result)["kani-rust-arithmetic"] == "excluded"
    assert statuses(result)["tla-concurrency-liveness"] == "candidate"
    assert all(item["scope"] == "separate-model" for item in result["work_items"])
    validate_assessment(result)


def test_existing_artifacts_and_separate_model():
    result = assess(profile([str(FIXTURES / "existing")]))
    assert statuses(result)["tla-state-machine-safety"] == "candidate"
    assert any("kernel.rs" in item["existing_assurance"] for item in result["work_items"])
    assert all("Contents/results not validated" in item["existing_assurance"] for item in result["work_items"])


def test_dafny_is_opt_in_codegen_not_foreign_source_verification(tmp_path):
    (tmp_path / "kernel.py").write_text("def add(x, y):\n    return x + y\n")
    result = assess(profile([str(tmp_path)]))
    assert statuses(result)["dafny-verified-kernel-codegen"] == "candidate"
    for item in result["work_items"]:
        assert item["tool"] == "Dafny"
        assert item["method"] == "verified-source-codegen"
        assert item["scope"] == "production"
        assert "arbitrary existing" in " ".join(item["does_not_establish"])
    assert any("no native-source" in gap for gap in result["coverage_gaps"])


def test_catalog_is_documented_not_reproduced():
    entries = catalog()["scenarios"]
    assert 8 <= len(entries) <= 12
    assert all(entry["evidence_status"] == "documented" for entry in entries)
    assert all(entry["sources"] and entry["tool_version"] for entry in entries)


def test_desired_goals_and_adoption_constraints(assessment):
    result = assess(assessment["profile"], goals=["memory-safety"], adoption="no-production-changes")
    matches = statuses(result)
    assert matches["kani-rust-slices"] == "candidate"
    assert matches["kani-rust-arithmetic"] == "excluded"
    assert matches["verus-rust-sequence-invariant"] == "excluded"
    assert matches["dafny-verified-kernel-codegen"] == "excluded"
    assert len(result["work_items"]) == 2
    validate_assessment(result)


def test_cpp_language_is_not_treated_as_rust(tmp_path):
    (tmp_path / "bits.cpp").write_text("unsigned shift(unsigned x) { return (x << 1) & 255; }\n")
    value = assess(profile([str(tmp_path)]))
    assert statuses(value)["cbmc-c-bitvector"] == "candidate"
    assert statuses(value)["kani-rust-arithmetic"] == "excluded"
