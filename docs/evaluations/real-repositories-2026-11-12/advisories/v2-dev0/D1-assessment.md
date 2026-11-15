# D1 — Chain / Take proof-readiness advisory

Task real-v2/dev0; freshcontextv2ordinal3. 2026-11-12.
Status: completed read-only recommendation, not implementation approval, evaluation,
proof, or an executed test result. Audience: bytes maintainers/downstream owners.
Goal: useful contracts for existing production adapters, without replacement.
Campaign owner authorizes discovery only and cannot approve upstream intent.

## Scope and evidence

| Root | Absolute selected root | Identity | Inspected | Skipped / unknown |
|---|---|---|---|---|
| r1 (D1) | <SOURCE-D1> | tokio-rs/bytes; commit f2cf483f13c9956a0f24ce2b7527f2318b0c8a2c; tree 8a832951605a44373017ac9abb8c125b8f02f2c6; detached, clean at before check | Entire Chain/Take; Buf interface, constructors, slice body and reference-forwarding boundary; BufMut interface; adapter tests, bounded generic callers/tests, exports, manifest, README, CI excerpt | Storage/allocation/refcount internals, iterator body, downstream Buf implementations, CI scripts and workflow after line 160; not whole-library assurance |

Output is the new `real-repo-refinement-v2/assessments/dev0-ee8d0e6` directory,
outside r1 and both other selected roots. Before reading source, metadata checks
found no known symlinks or nested Git roots in selected snapshots. This is neither
no-follow/atomic access nor an execution sandbox. No target code was run.
Identity hashes, exact read ranges, budget estimates, and final recheck are in
COMMANDS.md and BEFORE-AFTER.json. Discovery used 20 source read/search operations;
conservative returned-source estimate below 60,000 characters, not hard metering.

Observed architecture: Buf's public adapters construct the production Chain and
Take (r1:src/buf/buf_impl.rs:2379-2427, `take`, `chain`);
exports are r1:src/buf/mod.rs:17-39. Default `std` and optional serde/extra-platforms
are configuration, not verified compatibility (r1:Cargo.toml:7-32).
The selected state operations contain no direct FFI or async, but generic T/U
do not establish a sequential, statically dispatched transitive call graph.

Existing evidence, **not run/pass evidence**:
`long_take`, `take_copy_to_bytes`, panic, and vectored examples already cover
important boundaries (r1:tests/test_take.rs:6-87). Chain tests cover ordinary
copy/iteration, write routing, vectored progression, saturation of mutable
remaining and copy optimizations (r1:tests/test_chain.rs:7-187). The generic
suite already checks empty, advance, overshoot, and vectored behavior on nested
limited chains (r1:tests/test_buf.rs:29-120,389-419). CI defines stable/nightly,
cross and no_std jobs (r1:.github/workflows/ci.yml:61-149); scripts were not read,
and no historical or independently reproduced result was supplied.

## Decisions

Two opportunities, ordered by near-term usefulness. Prefer small native
regressions and contract review over new verification infrastructure. Existing
tests make another hello/world example low value. No production change is
recommended. No bug is established by this static assessment.

### O1 — Stateful composition and conservation at the split/limit boundary

- **Priority / value:** first; modest test-design effort, approval-dependent.
  Add sequence coverage across changing limits and both chain halves rather than
  duplicate the existing single-call examples. Benefit is interoperability of
  existing adapters; this is not a request to replace them.
- **Target / boundary:** `Chain::{remaining,chunk,advance}` at
  r1:src/buf/chain.rs:135-162, `Take::{remaining,chunk,advance,set_limit}` at
  r1:src/buf/take.rs:130-149. Chain dispatches to T/U, Take to T.
  The slice implementation used by a small pilot is actually visible at
  r1:src/buf/buf_impl.rs:2895-2916; reference forwarding is at 2887-2893.
  Tests are real callers, including nested composition at
  r1:tests/test_buf.rs:407-419. Arbitrary trait objects remain outside a native
  Kani pilot; a generic API can be instantiated with dynamic dispatch.
- **Requirement / authority:** documented chain order and “at most limit” at
  r1:src/buf/buf_impl.rs:2379-2427, stable remaining/chunk and advance obligations
  at 125-182,225-256. These are upstream documented requirements, not campaign
  approval. Exact post-panic state is **unresolved**, not promised transactional.
  `get_mut` explicitly permits external cursor movement despite advising against
  direct reads (r1:src/buf/take.rs:63-81); limit reset is documented at 106-132.
- **Proposition:** for valid finite Buf states representing sequences A and B,
  C=A concatenated with B, observed remaining is saturating(|A|+|B|).
  For Take(C,L), remaining=min(remaining(C),L), and chunk is the first underlying
  chunk truncated to L. For any successful advance n<=remaining, remove exactly
  n prefix bytes, preserving order; route min(n,|A|) to A and the residual to B;
  Take's limit becomes L-n. Invariant across legal operation sequences: cursor
  consumption equals the model's consumption, never exceeds current availability,
  and underlying content is unchanged. Recompute from current inner state after
  `get_mut`; `set_limit` replaces the limit, not a lifetime consumption budget.
  No loop invariant is needed inside these branch-only functions.
  Domain includes empty halves, zero/exact/overlarge limits, n=0, exact split,
  split+1 and total exhaustion, nested adapters, usize::MAX limits. Saturating
  length behavior for conceptual huge Buf implementations is a separate arithmetic
  obligation; small slice tests cannot represent overflowing actual allocations.
- **Errors / counterexamples:** n>Take.limit asserts; n>underlying remaining may
  panic or clamp according to Buf (r1:src/buf/buf_impl.rs:245-256). Do not require
  universal panic or unchanged chain state: Chain can consume A before B panics.
  `copy_to_bytes` has the stronger documented oversize panic (2359-2364);
  Take checks remaining at r1:src/buf/take.rs:151-157. Storage/allocation paths
  through Chain copy (r1:src/buf/chain.rs:172-188) remain an explicit uninspected
  dependency, not included in an asserted supported proof pilot.
  A wrong split residual, byte duplication, underflow on legal n, or limit
  incorrectly tied to external reads would falsify the proposed contract.
- **Method / limits:** first noncatalog source review plus proposed native
  sequence tests; observed samples, not proof. Optional investigation matches
  `kani-rust-arithmetic` and `kani-rust-slices` v1.0.0, bundled
  references/kani.md: finite sequential slice-backed instantiations with approved
  bounds, no FFI/concurrency/async/assembly/dynamic dispatch. Arithmetic assurance
  is enabled checks/assertions on represented inputs subject to complete
  unwinding, models, assumptions and tool soundness; slice assurance is enabled
  checks/assertions over the finite harness domain with complete unwinding.
  Exact Kani/Rust compatibility is **unknown**. Do not silently include generic
  downstream bodies or allocated copy paths under that claim.
- **Alternatives / readiness:** avoid Verus adaptation or Dafny replacement:
  no adaptation/replacement approval, disproportionate cost for these adapters.
  Mathematical sequence spec can be reviewed without changing production.
  Requirements sign-off, concrete callee inventory and separate execution grant
  precede any test/harness implementation. Current authority covers none of it.

### O2 — Vectored prefix contract, 16-entry cap and lifetime boundary

- **Priority / value:** second; meaningful risk from slicing and unsafe lifetime
  widening, medium/uncertain effort. Existing 2-entry tests leave a useful focused
  dimension: empty destination, 15/16/17 capacity and many underlying fragments.
- **Target / requirement:** `Chain::chunks_vectored` at
  r1:src/buf/chain.rs:166-170 delegates the unused destination tail;
  `Take::chunks_vectored` at r1:src/buf/take.rs:160-190 uses 16 temporary IoSlices,
  bounds the inner request, truncates by limit and transmutes references.
  Documented Buf contract is r1:src/buf/buf_impl.rs:184-223: non-mutating data,
  byte bound, count, no panic, zero remaining leaves dst unchanged, zero-length
  dst must be handled. Positive remaining's “at least one” text needs the
  unavoidable empty-destination exception confirmed by maintainers.
  Exact maximal fragment count is **not** required: the 16 cap is an implementation
  choice, not a promise to expose every fragment.
- **Proposition / domain:** for conforming underlying Buf and std enabled, all
  destination lengths including zero, all limits including zero/usize::MAX:
  return 0<=k<=dst.len(); returned slices concatenate to a prefix of visible
  bytes of total length <=min(inner.remaining(),limit); no cursor/data mutation;
  when visible data exists and dst is nonempty, expose some nonempty data.
  Zero visible remaining must leave dst unchanged. Take returns <=16 entries;
  do not infer a 16-entry Chain limit. Take loop invariant: already exposed
  bytes plus residual limit equals initial limit; written slices refer into
  backing bytes borrowed for `'a`, not into temporary IoSlice descriptors.
  This lifetime claim is a review obligation, **not established** by the comment.
  Caller must preserve backing validity and obey borrowing.
  Counterexamples: returned count out of range; an over-limit byte, non-prefix
  fragment, expired backing reference, panic on dst=[], or empty/exhausted
  operation unexpectedly modifying a sentinel destination.
- **Method / alternatives:** prefer noncatalog contract review and targeted native
  regressions extending r1:tests/test_take.rs:35-87 and
  r1:tests/test_chain.rs:45-139. Kani slices/unsafe-memory v1.0.0 are conditional
  investigation only: std IoSlice bodies were not inspected, lifetime/alias
  modeling and pinned UB checks are unknown. Unsafe-memory assurance is only
  supported enabled UB checks over the modeled domain, not every UB class.
  Neither unit tests nor a possible future Miri run proves lifetime soundness.
  No current supported native verifier recommendation; do not model away IoSlice
  and call it a proof of this unsafe operation.
- **Dependencies:** upstream intent on empty dst, reference lifetime review,
  std/platform support inventory and separate grant; implementation blocked.

## Actionable handoff

| Work | Next bounded task / proposed files | Dependencies / approval | Acceptance evidence |
|---|---|---|---|
| W1 | Read-only contract table for named O1 symbols; propose cases for tests/test_take.rs, tests/test_chain.rs, tests/test_buf.rs without editing | Discovery authorized; maintainer decisions on rejection/post-panic guarantees pending | Sequence model and expected values for zero/split/reset/external movement; separate huge-size saturation obligation; no allocation or generic-callee proof claim |
| W2 | Read-only O2 lifetime and destination-contract review; propose vectored test matrix in tests/test_take.rs | Resolve empty-dst wording and IoSlice/backing lifetimes; upstream approval absent | Trace every borrowed slice through both branches; capacities 0,1,15,16,17 and fragment count >16; sentinel/zero/exact/excess limits; known unsupported boundaries explicit |

Any later editing/execution is separately blocked, not authorized by these rows.
Retain source/harness identities, exact tool/Rust versions, commands/configuration,
enabled checks, finite size/sequence bounds, unwinding assertions, assumptions,
complete stdout/stderr including failures and isolation record if authorized.
Native tests remain samples; bounded checks do not establish all Buf implementations,
arbitrary sizes, concurrent storage correctness or the whole library.

## Review and limitations

Manually cross-checked cited symbols/ranges against loaded source; no automated
validator or target result. Loaded approved SKILL, index, template and Kani guide
unchanged; shared CBMC guide loaded for the next root, not used as a Rust method.
No prior advisories, evaluator keys, feedback or research were consulted.
Uninspected storage, external implementations and platform bodies remain unknown.
Final source freshness record is shared in BEFORE-AFTER.json; no atomic claim.
This assessment grants no approval and has not established recommendation correctness.
