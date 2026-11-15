# D1 — Chain / Take proof-readiness advisory

Task: real-baseline/dev0, D1. Status: completed advisory, recommendation only.
2026-11-12; no target execution, verifier result, upstream approval or self-score.
Audience: bytes maintainers or downstream adapter owners. Goal: useful contracts
on existing production code; no replacement or production changes authorized.

## Scope and evidence

| Root | Selected absolute path | Frozen identity | Inspected | Skipped / unknown |
|---|---|---|---|---|
| r1 | `<SOURCE-D1>` | tokio-rs/bytes `f2cf483f13c9956a0f24ce2b7527f2318b0c8a2c`, tree `8a832951605a44373017ac9abb8c125b8f02f2c6`; supplied clean | Complete Chain/Take, Buf adapter/interface and slice implementation ranges, BufMut interface/chain constructor, adapter tests, Cargo, README, exports, CI first 160 lines | Bytes/BytesMut allocation/refcount internals, iterator internals, other storage types, forwarding macro bodies, optional dependency bodies, remaining CI; not whole-library assurance |

Canonical output: this file, outside **all three** selected roots. Ancestor
metadata and resolved paths checked before target reads; chosen files regular,
no known symlink ancestors. No atomic snapshot/no-follow sandbox or secret scanner
is supplied by these tools. No target instruction was adopted as authority.
Read bounds, timestamps, exact ranges and identity checks: `tool-ledger.json`,
`COMMANDS.md`, `RESULT.json` alongside this file (provenance, not another backlog).
Initial actual source digest snapshot followed initial source reads, not an
atomic pre-assessment capture; frozen selection identity supplies the before
baseline. Final digest reconciliation is recorded in RESULT.

Source observations: the generic APIs compose arbitrary trait implementations,
not only contiguous slices (r1:src/buf/chain.rs:131-189, `impl Buf`;
r1:src/buf/take.rs:135-190, `impl Buf`). The `std` feature gates vectored code;
default is std, MSRV 1.57, serde and extra-platforms optional
(r1:Cargo.toml:7-39). CI defines stable/nightly, cross and no-std checks, but
its presence is not a pass and no CI logs were supplied
(r1:.github/workflows/ci.yml:45-150). Existing adapter tests provide observed
examples and negative copy coverage, not independently reproduced results
(r1:tests/test_chain.rs:7-181; r1:tests/test_take.rs:7-81).

## Decisions

Recommend two bounded investigations, ranked below. Begin with native contract
tests/review, not an asserted whole-adapter proof. Existing tests already cover
normal concatenation, some vectored limits and mutable remaining saturation;
incremental work should target composition, destination edges and failure states.
No evidence here establishes a defect or mandates a production patch.

### O1 — Vectored prefix, destination bounds, and borrowed-slice validity

- **Priority / value:** first: std-only `Take::chunks_vectored` combines a
  16-entry temporary array, early truncation, and unsafe lifetime transmutation.
  Small additional test matrix and manual lifetime review appear lower cost than
  whole-library verification; arbitrary implementation coverage remains costly.
  Current tests use two-entry destinations and limits 0,1,3,4,6,7, not the
  16-entry boundary (r1:tests/test_take.rs:34-81).
- **Boundary:** r1:src/buf/take.rs:160-190, `chunks_vectored`, delegates to
  `inner.chunks_vectored`, then borrows only `dst[..cnt]`; Chain concatenates
  delegated descriptors (r1:src/buf/chain.rs:166-172). Buf's contract limits
  total byte length, requires zero return/no dst mutation at exhaustion and
  safe handling of empty dst (r1:src/buf/buf_impl.rs:184-225). The default
  callee uses `chunk`; generic override bodies are not all known. No explicit
  FFI/async/concurrency in these bodies; a generic Buf could hide these.
- **Requirement / authority:** documented prefix and nonmutation semantics in
  that Buf interface, plus documented Take limit (r1:src/buf/take.rs:84-132).
  Interpreting a nonempty-buffer promise as requiring a descriptor with *empty*
  dst is inconsistent with the default implementation; resolve this as an
  explicit empty-dst exception with maintainers, not by manufacturing a failure.
  Requirement authority remains upstream; campaign owner grants discovery only.
- **Property proposed:** for a contract-conforming immutable inner Buf, any
  representable limit L including 0 and usize::MAX, any dst length including
  0,1,15,16,17+, returned n is at most min(dst.len,16); descriptors `dst[..n]`
  concatenate to a prefix of inner remaining data of length at most
  min(inner.remaining,L). No cursor/limit or underlying bytes change.
  At L=0 or exhausted inner, n=0 and dst is unchanged. For nonempty dst and
  available bytes, at least one returned slice is nonempty. Do **not** demand
  maximum possible fill: the 16-descriptor cap and shorter prefixes are allowed.
  Unwritten-tail preservation is a candidate stronger property, not general
  documented Buf intent; confirm before requiring it.
  Returned references must remain valid for the self-borrow lifetime despite
  dropping the temporary IoSlice array; review provenance from inner `'a`
  references, not from temporary descriptors. Loop invariant: running remainder
  equals L minus lengths of fully emitted slices; earlier output is the same
  prefix and subtraction happens only when slice.len < remainder.
  Counterexamples: dst-bound panic for a legal inner, emitted suffix beyond L,
  reordered/skipped bytes, mutation on exhausted input, or reference derived
  from temporary-owned byte storage. This is a proposed review/test oracle,
  not a reported runtime counterexample.
- **Method:** explicit noncatalog native tests plus source lifetime review
  preferred. Loaded guide `references/kani.md`, scenarios
  `kani-rust-slices` and `kani-rust-unsafe-memory` v1.0.0 (documented, not
  reproduced). The former offers “Enabled checks and assertions over the stated
  finite harness domain with complete unwinding”; the latter offers “Supported
  enabled UB checks over the modeled harness domain; coverage depends on the
  pinned Kani release.” Neither certifies every lifetime/UB class.
  All guide entries hard-exclude FFI, concurrency, async, assembly and dynamic
  dispatch. Arbitrary Buf coverage cannot be declared eligible; concrete slice /
  nested Chain monomorphizations could be investigated, but IoSlice, transmute,
  library support and pinned Kani/Rust compatibility remain unknown. No native
  pilot is ready. Allocation/refcount paths remain outside that proposed subset.
- **Alternatives / readiness:** ordinary tests observe samples, not proof;
  Miri could inspect executed lifetime paths only under separate execution
  approval, not exhaust arbitrary implementations. Verus requires adaptation;
  replacement conflicts with current adoption preference. No tool is necessary
  for the first useful source-contract review. Implementation/execution blocked
  pending resolved intent, selected implementations/configuration and owner
  permission.

### O2 — Cursor/limit conservation across adapter compositions and errors

- **Priority / value:** second: protect users composing `chain().take()` or
  `take().chain()` from ordering and limit regressions. Existing
  `chain_get_bytes` spans the seam, `long_take` covers limit above inner size,
  and a Take copy panic is observed in test source
  (r1:tests/test_chain.rs:163-181; r1:tests/test_take.rs:7-31). A stateful
  composition matrix adds more value than duplicating those examples.
- **Boundary:** Chain uses saturating addition and split advance
  (r1:src/buf/chain.rs:136-164); Take reports min, calls inner advance and only
  then decrements limit (r1:src/buf/take.rs:135-157). Constructor/caller contracts:
  r1:src/buf/buf_impl.rs:2379-2427, `take`, `chain`; concrete slice callee
  advance checks size and slices (r1:src/buf/buf_impl.rs:2895-2916).
  Cross-seam copy allocates BytesMut, calls put/take/freeze
  (r1:src/buf/chain.rs:174-189); these internals are unread and block a complete
  copy-to-Bytes proof. Mutable Chain is separate unsafe BufMut coverage,
  r1:src/buf/chain.rs:191-227; initialized-prefix caller obligations are explicit
  at r1:src/buf/buf_mut.rs:66-107.
- **Requirement:** documented concatenation order and “at most limit” reading;
  cursor conservation is inferred formalization requiring approval. Buf advance
  permits panic on overrun, or clamping if it does not panic; zero is a no-op
  (r1:src/buf/buf_impl.rs:227-256). Copy *must* panic above remaining
  (r1:src/buf/buf_impl.rs:2346-2377). No documented general rollback guarantee
  was found. Do not equate every panic with a bug.
- **Property proposed:** over all usize limits/counts and contract-conforming
  inner buffers, legal advance c <= exposed remaining consumes exactly prefix c
  and leaves its suffix. For Chain with mathematical counts A,B, split consumption
  is min(c,A) and c-min(c,A), and remaining is min(usize::MAX,A'+B'), **not**
  necessarily old saturated remaining minus c. For Take with inner count N and
  stored L, new L=L-c and inner N'=N-c; remaining=min(N',L-c). Include empty
  first/last buffers, c=0, seam ±1, L=0, L>N, and abstract count overflow without
  allocating usize::MAX bytes. `set_limit` replaces L rather than resetting
  the inner cursor; `get_mut` or Chain mutable access can independently change
  inner state, so recompute the relation after these operations
  (r1:src/buf/take.rs:63-132; r1:src/buf/chain.rs:57-112).
  State invariant between operations: exposed sequence is current concatenation
  / bounded prefix, not a snapshot at adapter creation. Successful copy length
  c returns exactly that prefix and advances equally; copy beyond remaining
  panics. For advance overrun inspect panic vs allowed clamp separately, including
  cnt > inner.remaining but <= Take limit. Chain can consume first buffer before
  second rejects; do not assume unchanged state after panic. Whether stronger
  failure atomicity is wanted is unresolved. Counterexamples include wrong seam
  consumption, limit underflow on a successful legal call, successful overlong
  copy, or an overrun return that violates the permitted clamp semantics.
- **Method / limits:** native stateful tests with a sequence/count oracle,
  noncatalog and non-proof, are the preferred proposal. Optional Kani arithmetic/
  slices investigation (`kani-rust-arithmetic`, `kani-rust-slices`, v1.0.0,
  same loaded guide) could cover finite sequential concrete cases; arithmetic
  assurance is “Checks enabled safety properties and assertions for all inputs
  represented by a harness, subject to complete unwinding, models, assumptions,
  and tool soundness.” Full generic storage, unsafe mutable adapters, panic
  runtime/library internals and allocation are not thereby verified. Pinned
  compatibility and unwind sufficiency unknown; overflow needs a separate
  count abstraction with explicit correspondence, not tiny slices alone.
  No need for TLC abstraction or source replacement at this stage.
- **Dependencies:** upstream decision on desired post-error guarantees and
  selected Buf implementations; enumerate configurations before tests or
  bounded harness work. No implementation permission is granted here.

## Actionable handoff

| Work | Next bounded task / proposed files | Dependencies / actual approval | Acceptance / retained evidence |
|---|---|---|---|
| W1 | Read-only O1 oracle/lifetime review of `take.rs`, `chain.rs`, Buf interface and the two adapter tests | Discovery in selected scope allowed; maintainer answers unavailable | Resolve empty-dst wording, trace `'a` origins and delegated cnt obligation; enumerate dst/limit/fragment matrix and existing-case overlap with citations; preserve remaining unknowns |
| W2 | Read-only O2 transition/error table, including concrete slice and hypothetical legal clamping Buf | Discovery allowed; no authority to impose stronger rollback contract | Table for successful/overrun/zero transitions, saturation and direct inner mutation; identify any mismatch as hypothesis with source trace, not an executed defect |
| W3 | Separately proposed native regression additions in `tests/test_take.rs`, `tests/test_chain.rs`; optional finite harness only after support audit | Blocked: W1/W2 requirement decisions, owner implementation approval, separately authorized isolated execution, tool/version/config selection | Approved oracles, negative cases not suppressed; exact future commands/versions/source/test or harness hashes/features/word size/panic strategy, full stdout/stderr and failures. For Kani additionally domains, assumptions, enabled checks, unwind completeness and excluded callees; samples and bounded checks reported separately |

## Review and limitations

Skill loaded AS IS: `SKILL.md`, index, template, Kani guide. Skill approval
revision `ee8d0e655a2ac51ce032ea1e8de1388b69dce930`; ten asset hashes matched
adjacent identity. Shared instructions/rubric were read, not evaluator private
material. No new catalog entry, research reproduction, code change or proof.
All root IDs here mean D1 only. Manual citation/property review; skipped storage
internals, arbitrary Buf implementations, platform dependencies and unexecuted
tests could change the proposed scope. Unknown compatibility stays unknown.
This advisory is ready for independent evaluation, not self-approved for merge.
