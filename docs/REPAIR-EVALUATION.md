# Retained evaluator repair

This is a new repair evaluation, not a replacement for the retained evaluator's
report. The complete report, protocol, reproductions, ledgers, recommendation
payloads, rejected assessments, and ten proposed fixtures were read before
implementation. Original diagnostics were reproduced read-only. No target builds,
tests, dependencies, proof tools or evaluator-writing scripts were executed.
The curated catalog is unchanged.

## Root causes and bounded changes

Original source references below refer to `spec_consultant/` in the preserved
0.1.0 wheel, not the repaired `src/spec_consultant/` checkout.

| Failure | Original cause | Repair and regression evidence |
|---|---|---|
| Legitimate reviewed isolated work rejected | `validation.py:170-174` required every task, including read-only investigation, to select a static candidate for the entire root. The canonical format had no separate scoped review. | `src/spec_consultant/validation.py:239-279` permits reviewed investigation while retaining immutable discovery; excluded/unestablished implementation needs explicit file/configuration/source review and remains blocked with unknown compatibility. R1 accepts the isolated opportunity but rejects included real FFI and missing review. R6 retains device/async/callback exclusions. |
| C++ linkage suppresses C recommendations | `profiler.py:75` treated every `extern "..."` as FFI, regardless of source language. Root-wide matching propagated this classification. | `src/spec_consultant/source.py:110-135` separates C/C++ linkage from Rust FFI and explicit C external declarations. R2 compares guarded linkage with genuine external declarations; pinned jsmn and tiny-aes remain provisional CBMC candidates. This does not establish C/C++ compilation or tool support. |
| Comment/doctest/benchmark symbols become production targets | `profiler.py:336-349` scanned raw lines and retained heuristic signal/symbol state without lexical executable definitions. Unrelated same-file patterns could accumulate into a candidate. | `src/spec_consultant/source.py:12-107` masks native-language comments/literals and records live definitions/roles; `matcher.py:64-78` groups native kernel signals by production symbol. `validation.py:133-172` checks live native references. R3 rejects ghost/doctest/string targets, preserves real symbols, and excludes benchmark/example production leads; pinned itoa no longer targets doctest `main` or `do_bench`. |
| Four of nine semantic conclusions cannot survive handoff | `data/assessment.schema.json:140-152` allowed only catalog formal tools/methods and task-shaped records; `validation.py:158-174` additionally rejected excluded C/mixed-root tasks. There was no explicit semantic disposition model. | The v2 schema adds conclusions, component provenance/dispositions, relationships and scoped review. `validation.py:206-219` fixes honest native-testing/source-inspection labels, and `validation.py:301-357` enforces root/task disposition completeness. `render.py:23-95` projects semantic data through all outputs; reports also include scoped eligibility evidence. R4-R10 and the nine-case CLI handoff verify semantic preservation rather than JSON/snapshot validity alone. |

Static decisions are compared against the full deterministic matching record,
not silently rewritten to endorse semantic conclusions. Existing dependency,
safe-path/hash, language, adoption, approval and assurance checks remain.
Scoped compatibility is deliberately unknown: even an approval grant cannot
make such implementation ready. Reviewed no-work dispositions do not trigger
an endless generic discovery backlog.

## Disposition of all nine retained conclusions

“Represented” means retained semantic information, not approved implementation
or a successful verification result.

| Retained case | Canonical disposition | Executable backlog |
|---|---|---|
| itoa | Represented opportunity: production formatter contract and exact bounds | Ready inspection; dependent implementation blocked |
| jsmn | Represented opportunity: configuration/state/token bounds and separate count-only behavior | Ready inspection; dependent CBMC work blocked; no substituted TLC proof |
| tiny-aes | Represented opportunity: mode-specific caller contracts and buffer/state properties | Ready inspection; dependent CBMC work blocked; inferred refinements not approved |
| prefix-buffer | Represented opportunity: arbitrary requested lengths, invalid-length rejection without panic | Ready inspection; dependent implementation blocked; no redundant overflow pilot |
| mixed-boundary | Represented isolated-kernel opportunity; foreign component explicitly excluded | Ready inspection; dependent implementation blocked; original root-wide exclusion retained |
| unsupported | Represented no-new-work with real device/concurrency/callback blockers | No surrogate/no-op implementation |
| existing-proof | Represented evidence-only existing harness status | One inspection task; no duplicate harness or invented passing result |
| no-work | Represented archive/no-new-work reason | No tasks |
| python-gap | Represented native-testing opportunity; rejection mechanism/initial-state intent remain qualified | Ready inspection; dependent tests blocked; no formal-tool compatibility claim |

Unresolved property components are explicitly deferred with a reason.
Inferred components retain inferred provenance, not approval. Discarded/folded
historical static pilots become rejected conclusions with their original reasons
and relationships to the retained conclusion; they do not become live work.

## Regression scope and results

All ten proposed fixtures were applied where supported:

| Fixtures | Assertions |
|---|---|
| R1-R3 | Reviewed isolation, linkage vs external implementation, live production targets and negative controls |
| R4 | Invalid lengths remain in the contract; input-domain assumptions cannot silently erase rejection behavior. Structural validation still cannot detect an independently wrong semantic contract. |
| R5-R7 | Existing assurance is presence/status only; unsupported real boundaries remain blocked; archive roots stop explicitly. |
| R8 | Python debit state preservation survives canonical CLI validation/rendering as sampled testing, not proof; fabricated proof assurance is rejected. |
| R9 | CBC caller alignment, IV/counter refinements and mode limits retain provenance; no cryptographic/constant-time or arbitrary partial-CTR-equivalence claims. |
| R10 | Parser configuration, reachable state, integer/buffer limits and count-only boundaries survive; non-strict incremental primitive counterexamples are labeled source reasoning, not executed/approved defects. |

The repaired full suite passed **80 tests**, including **23 focused repair and
retained-corpus cases**; Ruff lint/format checks passed. The original wheel fails
the twelve original-baseline selectors. Some baseline failures intentionally
demonstrate rejection of the new semantic structures; they do not mean the old
negative controls were previously wrong. The original wrong-contract diagnostic
remains the documented structural-validation non-goal.

The wheel builds, installs into an isolated output directory, includes the v2
schema and unchanged ten-entry catalog, and performs CLI assessment, source
validation and freshness checks without target execution. The retained evidence
manifest's **451 entries have zero checksum mismatches**.

## Independent reproduction

From this checkout, use Python 3.11+; the existing environment needs no new
dependencies. For a fresh development environment:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

Run from the explicit checkout root. The bundle is read-only input. Do not run
its `run_evaluation.py`, `run_diagnostics.py`, `check_customer_expectations.py`
or `write_review.py` in place: those scripts overwrite retained evidence.

```sh
cd /Users/jameshuang/Repos/proof-readiness
EVAL=/Users/jameshuang/.copilot/session-state/9bb8f3d6-0622-4441-acee-5109bf83c073/files/customer-evaluation
.venv/bin/python -m pytest -q tests --evaluation-dir "$EVAL"
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

Without that bundle, `pytest -q tests` runs portable cases and explicitly skips
the six retained-corpus integrations. To preserve regenerated nine-case outputs,
add `--basetemp /absolute/new/output-directory` to the pytest command. Choose a
new path outside the checkout and evaluated roots: **pytest clears a reused
basetemp**. The semantic-handoff test writes each case's assessment, report,
backlog and prompt, plus `dispositions.json`; originals are never overwritten.

Compare the new portable regressions with the preserved original installation:

```sh
BASELINE=/Users/jameshuang/.copilot/session-state/9f330828-04da-4e01-a780-b33d66268e3e/files/wheel-install
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$BASELINE" .venv/bin/python -m pytest \
  -q tests/test_regressions.py -k 'not reviewed_completeness' --tb=short
```

Expected: twelve failures and five deselections, exit 1. The repaired suite must
pass, not merely reject malformed new inputs. The preserved original wheel is
under the same session's `files/wheels/`; build repaired wheels in a different
directory. Do not overwrite the original wheel.

## Remaining limits

The native lexical filter is not a Rust/C/C++ parser, preprocessor, macro expander
or call graph. Conditional compilation, C headers' actual language, local callees,
implicit/unresolved externals, generated code and pinned tool support still need
inspection. Python and other languages retain heuristic profiling/reference
limitations; the native lexical repair is not universal executable-symbol
validation.

Reviewed scopes conservatively operate at file boundaries, not independently
verified component/callee closures. Legacy v1 output stays readable, but the new
profiling policy requires a fresh scan for execution handoff. Every represented
opportunity remains provisional. Approval legitimacy, semantic correctness,
model correspondence and actual verification outcomes are not established by
schema validation or these assessor tests. No accuracy, cost advantage, universal
compatibility, target proof or benchmark superiority is claimed.
