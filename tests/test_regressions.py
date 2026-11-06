"""Focused regressions for retained evaluator R1-R10; no target execution."""

import copy
import json

import pytest

from spec_consultant.cli import main
from spec_consultant.matcher import assess
from spec_consultant.profiler import profile
from spec_consultant.render import artifacts
from spec_consultant.validation import validate_assessment

from .review_helpers import conclusion, ref, reviewed, scoped, work


def source(tmp_path, files):
    root = tmp_path / "target"
    root.mkdir()
    for path, content in files.items():
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)
    return assess(profile([str(root)]), adoption="no-production-changes")


def test_r1_reviewed_isolation_preserves_exclusion_and_blocks_real_ffi(tmp_path):
    value = source(
        tmp_path,
        {
            "kernel.rs": "pub fn add_small(a: u32, b: u32) -> u32 { a + b }\n",
            "ffi.rs": 'unsafe extern "C" { fn foreign() -> u32; }\n',
            "REQUIREMENTS.md": "For both inputs 0..=100 return mathematical addition; FFI remains unresolved.\n",
        },
    )
    original = copy.deepcopy(value["matches"])
    assert next(m for m in original if m["scenario"] == "kani-rust-arithmetic")["status"] == "excluded"
    targets = [ref("kernel.rs", symbol="add_small")]
    evidence = work("inspect-isolated", targets)
    evidence.update(
        property="For a,b in 0..=100, return mathematical a+b.",
        provenance="requirement-backed",
        requirement_refs=[ref("REQUIREMENTS.md")],
    )
    pilot = work("isolated-pilot", targets, kind="implementation")
    pilot["depends_on"] = [evidence["id"]]
    pilot["review"] = scoped(targets, ["r1:kernel.rs"], ["r1:ffi.rs"])
    record = conclusion("isolated-addition", targets, [evidence, pilot])
    record["assumptions"] = ["0<=a,b<=100; no foreign calls in this source."]
    record["exclusions"] = ["foreign, ffi.rs and cross-language behavior are not verified."]
    record["unknowns"] = ["Pinned Kani support remains unknown."]
    reviewed(value, [evidence, pilot], [record])
    validate_assessment(value)
    assert value["matches"] == original
    assert pilot["readiness"] == "blocked" and not value["approval"]["grants"]
    del pilot["review"]
    with pytest.raises(ValueError, match="scoped review"):
        validate_assessment(value)
    pilot["review"] = scoped(targets, ["r1:kernel.rs", "r1:ffi.rs"])
    with pytest.raises(ValueError, match="hard exclusion"):
        validate_assessment(value)


def test_r2_c_linkage_is_not_ffi_but_external_declarations_are(tmp_path):
    value = source(
        tmp_path,
        {
            "kernel.h": '#ifdef __cplusplus\nextern "C" {\n#endif\n'
            "unsigned first(const unsigned *data) { return data[0] + 1; }\n"
            "#ifdef __cplusplus\n}\n#endif\n",
        },
    )
    assert next(m for m in value["matches"] if m["scenario"] == "cbmc-c-buffer")["status"] == "candidate"
    file = value["profile"]["roots"][0]["files"][0]
    assert any(s["kind"] == "linkage" for s in file["signals"])
    assert not any(s["kind"] == "ffi" for s in file["signals"])
    assert any("compilation language" in unknown for m in value["matches"] for unknown in m["unknowns"])
    root = value["profile"]["roots"][0]["path"]
    from pathlib import Path

    (Path(root) / "external.c").write_text(
        "extern unsigned unavailable(const unsigned *data);\n"
        "unsigned call(const unsigned *data) { return unavailable(data) + data[0]; }\n"
    )
    blocked = assess(profile([root]))
    assert next(m for m in blocked["matches"] if m["scenario"] == "cbmc-c-buffer")["status"] == "excluded"


def test_r3_comments_doctests_literals_and_benchmarks_are_not_primary_targets(tmp_path):
    value = source(
        tmp_path,
        {
            "lib.rs": "//! fn ghost(x:u8)->u8 { unsafe { buffer[0] + x } }\n"
            "/* nested /* fn ghost2(){ buffer[0]; } */ comment */\n"
            'const EXAMPLE: &str = r###"fn ghost3(){ unsafe { buffer[0] + 1 } }"###;\n'
            'const NORMAL: &str = "fn ghost4() { buffer[0] + 1 }";\n'
            "fn real(buffer: &[u8]) -> u8 { buffer[0] + 1 }\n",
            "benches/bench.rs": "fn do_bench(buffer: &[u8]) -> u8 { buffer[0] + 1 }\n",
        },
    )
    targets = [target for item in value["work_items"] for target in item["targets"]]
    assert targets and all(target["symbol"] == "real" for target in targets)
    assert all(target["path"] == "lib.rs" and target["line"] == 5 for target in targets)
    validate_assessment(value)
    value["work_items"][0]["targets"] = [ref("lib.rs", 1, "ghost")]
    with pytest.raises(ValueError, match="comment|symbol"):
        validate_assessment(value)


def test_r3_documentation_only_constant_has_no_executable_tasks(tmp_path):
    value = source(
        tmp_path,
        {
            "lib.rs": "//! fn ghost(x:u32)->u32 { x+1 }\n//! buffer[0]; unsafe\n"
            'const DOCUMENTATION: &str = "fn ghost(){unsafe {buffer[0]+1}}";\n',
        },
    )
    assert not value["work_items"]
    assert all(m["status"] != "candidate" for m in value["matches"] if m["scenario"].startswith("kani"))


def test_r4_invalid_input_contract_survives_handoff_not_semantically_validated(tmp_path):
    value = source(
        tmp_path,
        {
            "lib.rs": "fn prefix_total(bytes: &[u8], length: usize) -> Option<u64> {\n"
            "let mut sum=0; for i in 0..length { sum += bytes[i] as u64; } Some(sum) }\n",
            "REQUIREMENTS.md": "Invalid requested lengths return None without panic; buffers up to 1024.\n",
        },
    )
    targets = [ref("lib.rs", symbol="prefix_total")]
    item = work("prefix-contract", targets, scenario="kani-rust-slices")
    record = conclusion("invalid-length", targets, [item])
    record.update(
        property="If length>bytes.len(), return None without panic; otherwise return the exact sum.",
        provenance="requirement-backed",
        requirement_refs=[ref("REQUIREMENTS.md")],
        input_domain="bytes.len()<=1024; arbitrary usize length, including usize::MAX.",
        assumptions=["Never assume requested length<=bytes.len()."],
        postconditions=["Valid sum<=261120; no independent overflow pilot."],
        counterexample_conditions=["Source trace: [], length=1 reaches bytes[0]; not executed."],
    )
    reviewed(value, [item], [record])
    validate_assessment(value)
    for text in artifacts(value, "/outside/assessment.json").values():
        assert "return None without panic" in text and "usize::MAX" in text
        assert "261120" in text and "not executed" in text
    # R4 is a non-goal control: the validator cannot adjudicate requirement meaning.
    record["property"] = "Assume length<=bytes.len(); only valid prefixes matter."
    validate_assessment(value)


def test_r5_existing_harness_status_only_no_duplicate_pilot(tmp_path):
    value = source(
        tmp_path,
        {
            "lib.rs": "fn add_sat(a:u8,b:u8)->u8 { a.saturating_add(b) }\n"
            "#[kani::proof]\nfn add_sat_spec(){ let a:u8=kani::any(); let b:u8=kani::any();\n"
            "assert_eq!(add_sat(a,b), ((a as u16+b as u16).min(255)) as u8); }\n",
            "PROOF-STATUS.md": "Existing full-u8 pair harness; logs absent, result unconfirmed; no rerun.\n",
        },
    )
    targets = [ref("lib.rs", 3, "add_sat_spec")]
    item = work("audit-existing-proof", targets)
    item["existing_assurance"] = "Full-u8 pair harness present; result unconfirmed; no duplicate or rerun."
    record = conclusion("existing-evidence", targets, [item], kind="evidence-only")
    record["existing_assurance"] = item["existing_assurance"]
    record["existing_assurance_refs"] = [ref("PROOF-STATUS.md")]
    reviewed(value, [item], [record])
    validate_assessment(value)
    assert all(task["kind"] == "evidence-gathering" for task in value["work_items"])
    for text in artifacts(value, "/outside/assessment.json").values():
        assert "result unconfirmed" in text and "no duplicate" in text


def test_r6_device_boundaries_remain_blocked_after_scoped_review(tmp_path):
    value = source(
        tmp_path,
        {
            "lib.rs": "async unsafe fn device(offset:u64, cb:&dyn Adjust)->u64 {\n"
            'asm!("mrs {}, cntvct_el0"); cb.adjust(value + offset) }\n',
        },
    )
    assert next(m for m in value["matches"] if m["scenario"] == "kani-rust-arithmetic")["status"] == "excluded"
    targets = [ref("lib.rs", symbol="device")]
    item = work("device-pilot", targets, kind="implementation")
    item["review"] = scoped(targets, ["r1:lib.rs"])
    record = conclusion("device-boundaries", targets, [item])
    reviewed(value, [item], [record])
    with pytest.raises(ValueError, match="hard exclusion"):
        validate_assessment(value)
    record.update(
        disposition="deferred",
        reason="Assembly, callback and async behavior unresolved.",
        work_item_ids=[],
        exclusions=["No no-op asm, identity callback, or executor surrogate."],
    )
    value["work_items"] = []
    validate_assessment(value)
    for text in artifacts(value, "/outside/assessment.json").values():
        assert "deferred" in text and "No no-op asm" in text


def test_r7_archive_no_work_has_explicit_reason_not_discovery_loop(tmp_path):
    value = source(tmp_path, {"README.md": "Archived documentation only; no continuing verification obligation.\n"})
    record = conclusion("archive", [ref("README.md")], kind="no-new-work")
    record["reason"] = "Permanently archived; no executable obligation or verification budget."
    reviewed(value, [], [record])
    validate_assessment(value)
    for text in artifacts(value, "/outside/assessment.json").values():
        assert "no-new-work" in text and "Permanently archived" in text
    assert "Gather more information" not in artifacts(value, "/outside/assessment.json")["backlog.md"]


def test_r8_native_testing_gap_survives_cli_canonical_to_all_projections(tmp_path):
    value = source(
        tmp_path,
        {
            "ledger.py": "class Ledger:\n def debit(self, amount):\n  self.balance -= amount\n",
            "REQUIREMENTS.md": "Overdraft must reject and leave state unchanged; rejection API unresolved.\n",
        },
    )
    targets = [ref("ledger.py", 2)]
    evidence = work("ledger-intent", targets, scenario=None)
    pilot = work("ledger-tests", targets, scenario=None, kind="implementation")
    pilot["depends_on"] = [evidence["id"]]
    record = conclusion("ledger-atomicity", targets, [evidence, pilot])
    record.update(
        property="Overdraft rejection preserves balance; do not assume amount<=balance.",
        provenance="requirement-backed",
        requirement_refs=[ref("REQUIREMENTS.md")],
        assumptions=["Nonnegative initial balance is inferred, not an approved constructor policy."],
        unknowns=["Exception versus return rejection protocol remains unresolved."],
        exclusions=["Sampled testing is not a proof over unbounded Python integers."],
        counterexample_conditions=["Source trace: balance=5,debit=6 leaves -1; not executed."],
        property_components=[
            {
                "property": "Constructor nonnegative-start policy",
                "provenance": "inferred",
                "requirement_refs": [],
                "disposition": "deferred",
                "reason": "Constructor requirements absent.",
            }
        ],
    )
    reviewed(value, [evidence, pilot], [record])
    canonical = tmp_path / "canonical.json"
    canonical.write_text(json.dumps(value))
    out = tmp_path / "rendered"
    assert main(["validate", str(canonical)]) == 0
    assert main(["render", str(canonical), "--out", str(out)]) == 0
    validate_assessment(json.loads(canonical.read_text()))
    for name in ("report.md", "backlog.md", "orchestrator.md"):
        text = (out / name).read_text()
        for expected in (
            "ledger-atomicity",
            "Overdraft rejection",
            "balance=5,debit=6",
            "inferred",
            "deferred",
            "Constructor requirements absent",
            "ledger-tests",
            "blocked",
            "ledger-intent",
            "unbounded Python integers",
        ):
            assert expected in text
    pilot["assurance"] = "This proves Python correct."
    with pytest.raises(ValueError, match="honest assurance"):
        validate_assessment(value)


@pytest.mark.parametrize("label", ["aes", "parser"])
def test_r9_r10_inferred_refinements_are_not_approved_model_proofs(tmp_path, label):
    value = source(
        tmp_path,
        {
            "kernel.c": "unsigned first(unsigned *buffer) { return buffer[0] + 1; }\n",
            "API.md": "Caller obligations and configuration remain separate from inferred refinements.\n",
        },
    )
    targets = [ref("kernel.c", symbol="first")]
    item = work("inspect-" + label, targets, scenario="cbmc-c-buffer")
    record = conclusion(label + "-contract", targets, [item])
    if label == "aes":
        record.update(
            assumptions=["CBC lengths are multiples of 16; no invalid-length rejection promised."],
            exclusions=[
                "NIST-vector tests are not security or constant-time proofs.",
                "Arbitrary partial-call CTR equivalence is not promised.",
            ],
            unknowns=["Zero-length memcpy definedness and AES128/192/256 flags unconfirmed."],
        )
    else:
        record.update(
            assumptions=["Strict/relaxed x parent-links; initialized reachable state; input/token bounds 0..32."],
            exclusions=[
                "No full RFC grammar or count-only/error parity assumption.",
                "A TLC model is not a C parser proof.",
            ],
            unknowns=["C integer widths and non-strict incremental scope require confirmation."],
            counterexample_conditions=[
                "Source trace: [12], lengths 2 then 4 may split primitives; "
                "compare final initialized token fields/count, not executed."
            ],
        )
    record["property_components"] = [
        {
            "property": "Detailed poststate/equivalence refinement",
            "provenance": "inferred",
            "requirement_refs": [ref("API.md")],
            "disposition": "represented",
            "reason": "Proposed for inspection, not approved implementation.",
        }
    ]
    reviewed(value, [item], [record])
    validate_assessment(value)
    for text in artifacts(value, "/outside/assessment.json").values():
        assert "inferred" in text and "not approved implementation" in text
        assert all(boundary in text for boundary in record["exclusions"] + record["unknowns"])


def test_conclusion_links_dependencies_approvals_and_language_checks_are_not_relaxed(tmp_path):
    value = source(tmp_path, {"lib.rs": "fn real(x:u8)->u8 { x + 1 }\n"})
    targets = [ref("lib.rs", symbol="real")]
    item = work("pilot", targets, kind="implementation")
    record = conclusion("review", targets, [item])
    reviewed(value, [item], [record])
    item["readiness"] = "ready"
    with pytest.raises(ValueError, match="approval"):
        validate_assessment(value)
    item["readiness"] = "blocked"
    item["depends_on"] = ["missing"]
    with pytest.raises(ValueError, match="dependency"):
        validate_assessment(value)
    item["depends_on"] = []
    record["work_item_ids"] = ["missing"]
    with pytest.raises(ValueError, match="unknown work"):
        validate_assessment(value)
    record["work_item_ids"] = [item["id"]]
    wrong_language = work("wrong-language", targets, scenario="cbmc-c-buffer")
    value["work_items"] = [wrong_language]
    record["work_item_ids"] = [wrong_language["id"]]
    with pytest.raises(ValueError, match="language"):
        validate_assessment(value)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing-root", "disposition for every root"),
        ("unlinked-task", "every retained work item"),
        ("no-work-task", "no-new-work conclusions cannot authorize tasks"),
        ("omitted-target", "scoped review omits a target file"),
        ("ready-unknown", "scoped compatibility is unknown"),
    ],
)
def test_reviewed_completeness_and_scope_cannot_authorize_silent_or_unsupported_work(tmp_path, mutation, message):
    value = source(
        tmp_path,
        {
            "kernel.rs": "fn real(x:u8)->u8 { x + 1 }\n",
            "ffi.rs": 'unsafe extern "C" { fn foreign() -> u32; }\n',
        },
    )
    targets = [ref("kernel.rs", symbol="real")]
    evidence = work("inspect", targets)
    pilot = work("pilot", targets, kind="implementation")
    pilot["depends_on"] = [evidence["id"]]
    pilot["review"] = scoped(targets, ["r1:kernel.rs"], ["r1:ffi.rs"])
    record = conclusion("review", targets, [evidence, pilot])
    reviewed(value, [evidence, pilot], [record])
    validate_assessment(value)
    if mutation == "missing-root":
        value["conclusions"] = []
    elif mutation == "unlinked-task":
        record["work_item_ids"] = [evidence["id"]]
    elif mutation == "no-work-task":
        record["kind"] = "no-new-work"
    elif mutation == "omitted-target":
        pilot["review"]["included_files"] = ["r1:ffi.rs"]
        pilot["review"]["excluded_files"] = []
    else:
        pilot["readiness"] = "ready"
        value["approval"]["grants"] = [pilot["id"]]
    with pytest.raises(ValueError, match=message):
        validate_assessment(value)
