# Proof-readiness advisory

Status: recommendation only; no target execution or verifier result.
Date: 2026-11-15. Task: practical-confirm-author, single confirmation cohort.
User goal: bounded source-grounded specification/verification planning for the
map-named library slice. Adoption: read-only planning; actual owner grants for
implementation and execution are absent.

## Scope and evidence

| Root ID | Selected absolute root | Revision / dirty state | Inspected areas | Skipped / unknown areas and why |
|---|---|---|---|---|
| r1 | evidence://campaign/targets/D1 | commit `8c535a260ce561eaab4111aafc29038eb9f77ff3`; tree `d0c2d891838c3c188f084bdafa0442e063b04d62`; read-only Git status empty initially and at final check | `src/map.rs` 1–300 plus symbol search; `src/lib.rs` 365–445 plus export/feature search; all available text in requested windows for `src/iter.rs`, `Cargo.toml` 1–100, `build.rs` 1–100, `tests/map.rs` 1–100 | Remaining map implementation, value/error/serialization callers, dependency implementations and generated private modules unread; filename scope is not API closure. All supplied discovery exclusions retained, including target instructions, lexical, regression/UI/fuzz, vendor/build/nested/symlink areas. |

Output: `evidence://campaign/advisories/confirmation/D1/assessment.md`,
outside all three selected roots. Root and named-file parent real paths matched
the selected paths; named leads were regular files below 256 KiB. Metadata checks
are not atomic no-follow guarantees, secret detection or an execution sandbox.

Coverage: six named files, not a recursive scan (initial allowance 250).
Requested source windows totaled 781 lines, plus 141 lines requested in bounded
native citation cross-checks (922 total), with EOF-short reads; the map's first
window was 200 lines rather than preferred 100. No source window exceeded 200.
Search output was bounded; the broad map-feature search used a 70-result limit
and cannot establish exhaustive symbol coverage. No tool-reported file truncation.
There was no cumulative character/syscall budget checker. Shared checkout reads
were not atomic; final Git identity and full status were unchanged.

Existing assurance: `r1:tests/map.rs:4` `test_preserve_order`, line 20
`test_shift_insert`, line 30 `test_append`, and line 50 `test_retain` contain
feature-sensitive examples. No run or supplied passing-result provenance exists.
These tests observe intended examples, not independently approved requirements.

Observations: `r1:src/map.rs:38` `MapImpl` selects BTreeMap or IndexMap;
lines 43–46 select different hashers with `std`. `r1:src/lib.rs:431` exports
`map`; line 413 reexports Map through the unread value module. The iterator lead
is `LineColIterator` (`r1:src/iter.rs:3`), not evidence of a map-iterator caller.
`r1:build.rs:19` `main` writes generated private modules; it was read, not run.
Hypothesis: wrapper-level state/ordering regressions may add useful assurance
without verifying either underlying container.

## Decisions

Prefer one small native-test/contract opportunity over a forced proof-tool match.
The inspected implementation delegates container operations and provides
feature-dependent semantics, not an isolated arithmetic/slice/unsafe kernel.
The bundled index (`proof-readiness` 0.2.1, `references/index.md`, catalog snapshot
`9ce3702cb69a0944cb4db4d5b318cf118cf00509`) does not establish a native verifier
match merely because this is Rust. No new catalog entry is proposed.

Append collision ordering and `shift_insert` index behavior remain deferred:
`r1:src/map.rs:274` `append` delegates extend/append; line 150 `shift_insert`
delegates to IndexMap. Dependency contracts and owner intent are not resolved
by the simple disjoint append/new-key insert examples. No broad map proof,
parser security claim or HashDoS verification is warranted in this slice.

### O1 — Feature-sensitive removal contract and regression plan

- Priority and rationale: medium. Misreading `preserve_order` as stable removal
  could change downstream serialization order. A small contract table and direct
  native tests would add negative/position cases beyond the inspected examples.
  Effort appears small at the wrapper, but configuration/dependency costs are
  unknown; no defect or missing tests elsewhere is asserted.
- Target and boundary: `Map::remove` at `r1:src/map.rs:166` dispatches to
  `swap_remove` (line 210) with `preserve_order`, otherwise BTreeMap removal;
  `shift_remove` at line 246 preserves relative order by delegation.
  `remove_entry` at line 189 and entry-returning variants at lines 228/264
  should share the contract. Callee bodies, Value's destruction behavior,
  indexmap/foldhash versions actually resolved, and downstream callers are
  unread. `r1:Cargo.toml:11` specifies Rust 1.71, not a verifier version;
  lines 14–15 give dependency ranges. Lines 53–65 and
  `r1:src/lib.rs:372` distinguish default std, alloc-only, and unsupported
  neither-std-nor-alloc builds.
- Requirement: **documented**, authority still unconfirmed. Removal returns the
  prior value if present (`r1:src/map.rs:154`); with `preserve_order`, remove
  replaces the removed position with the last entry (lines 160–164); shift
  removal preserves relative order (lines 236–240). Owner approval for named
  work and configuration coverage is absent. Do not promise stable order for
  ordinary remove.
- Property: for a finite valid map with unique String keys, ordinary immutable
  `&str` lookup, valid borrow semantics, exclusive mutable access and normal
  completion, removing a missing key returns None and leaves contents/order
  unchanged. Removing an existing key returns its prior value, removes exactly
  that key, preserves every other binding and decreases length by one.
  Without `preserve_order`, surviving traversal remains key-sorted. With it,
  swap/remove replaces a nonlast removed position with the previous last entry;
  shift removal produces the original key sequence with only that key deleted.
  Entry-returning variants also return the stored key. Proposed sampled domain:
  0–4 keys including Unicode/empty strings and Null/integer values, first/middle/
  last/missing removals; this is a test domain, not an exhaustive API restriction.
  State invariant: unique keys and agreement of length/bindings/key sequence
  after each operation. Loop invariant is not applicable to the wrapper's
  straight delegation. Counterexamples: wrong returned binding, altered survivor,
  stale length or forbidden order permutation. Panic/OOM/destructor behavior is
  not assumed proved; arbitrary recursive Values remain outside the small test
  plan, not outside the actual API.
- Method: explicit **noncatalog source inspection followed conditionally by
  native tests**. Tests establish behavior only on executed cases, not proof of
  dependencies or all maps. Exact feature/toolchain compatibility is unknown.
- Alternatives: defer Kani/Verus because no supported complete native
  container/callee boundary or adaptation budget is established. A separate TLC
  abstraction would not verify this wrapper and adds little before intent and
  direct tests are settled. No replacement/code generation proposal.
- Dependencies/readiness: contract authority, approved feature matrix, dependency
  closure, actual implementation/execution grants and real isolation are required.
  This report supplies evidence only; it grants none of those prerequisites.

## Actionable handoff

| Work ID | Next bounded task / proposed files | Depends on | Approval and readiness | Acceptance / evidence required |
|---|---|---|---|---|
| W1 | Read-only removal contract table outside target; inspect already selected symbols/tests/config and enumerate unread caller/dependency questions | O1 | Evidence only in the selected scope; expansion and owner requirements decisions must be escalated | Cite return/order semantics for missing/first/middle/last keys and std versus alloc-only, each with preserve_order off/on; record unresolved bodies/intent, without executing |
| W2 | Read-only command-selection artifact `removal-test-invocation.md` outside target | W1 plus agreed future scope | Selection only; no execution permission | Resolve trusted Rust/Cargo versions, dependency availability, build-script effects, isolated work directory and exact feature/test arguments; no installer or build |
| W3 | Conditional separate test addition to `tests/map.rs`, no production repair | W1/W2, owner approval, safe isolated environment | Blocked: actual implementation and execution grants absent | Direct map cases exercise all removal positions, missing keys and entry/value variants in approved feature matrix; retain changed tree, exact versions/commands/configuration, complete output and failures |

W2 is the named read-only invocation-resolution prerequisite for W3; no command
is proposed as already runnable. Future evidence must distinguish test samples
from proof and retain source/test correspondence and excluded domains. If owner
intent or supported configurations cannot be resolved, stop at W1/W2.

## Review and limitations

Manual citation/root and dependency-order review only. Loaded staged skill,
template, index and illustrative examples; no installed CLI or cwd legacy skill.
No target tests, imports, builds, scripts, proof tools, network, writes or nested
agents. One metadata command failed because `python` was unavailable (exit 127);
data-only metadata was subsequently obtained with `python3`, not target code.
No prior author/evaluator output or private mapping was read. Source identity
matched scope before and after inspection. Compatibility, dependency closure,
requirement authority and execution safety remain unresolved. This advisory is
ready for evaluation, not approved implementation, proof, exhaustive coverage
or a correctness certificate.
