# D1 — Chain / Take advisory

Status: authored recommendation only, 2026-11-12. No execution, grading, proof,
implementation approval, or production change. Goal: useful contracts on existing
production adapters, addressed to bytes maintainers/downstream component owners.
The campaign owner authorized offline advice only; upstream intent is not granted.

## Scope and evidence

| Root | Selected absolute root | Identity |
|---|---|---|
| r1 | <SOURCE-D1> | HEAD f2cf483f13c9956a0f24ce2b7527f2318b0c8a2c; tree 8a832951605a44373017ac9abb8c125b8f02f2c6; tracked status empty before inspection |

Inspected production Chain and Take, bounded Buf/BufMut interfaces and slice
implementation, adapter constructors/exports, focused tests and Cargo/CI metadata.
Uninspected: storage internals (Bytes/BytesMut), IntoIter implementation, broader
trait methods, CI scripts, external libraries and standard-library implementation.
No whole-library memory-safety or generic-implementor compatibility claim.
README was hashed but not interpreted. Existing tests and CI are artifacts, not
reproduced passing results. The viewed tests cover concatenation, copy boundaries,
mutable saturation, and a two-fragment vectored Take.

Output is outside all three selected roots. Ancestor and scoped-file lstat checks
found no symlinks before inspection; regular-file hashes were collected. This is
not atomic no-follow access, sandboxing, or secret detection. Source views used
explicit inclusive windows of at most 100 lines; one beyond-EOF request returned
an error, not source. Budget/UTC and before/after hashes are in COMMANDS.md.

## Decisions

Two opportunities, not a quota of three. Prefer the existing implementations.
First investigate a small static-dispatch adapter harness; second improve the
source-backed vectored contract and test plan. Defer allocation/copy proofs and
mutable unsafe proofs: they require storage and initialization evidence beyond
this bounded scope. Existing pointer-preservation tests
(r1:tests/test_chain.rs:159, `chain_get_bytes`; r1:tests/test_take.rs:16,
`take_copy_to_bytes`) are useful but do not prove allocation behavior.

### O1 — Sequential adapter cursor and limit conservation

- **Priority:** first; broad downstream relevance and inexpensive contract
  clarification before a potentially modest bounded harness. Incremental benefit:
  arbitrary represented bytes/limits and composed transitions beyond examples.
- **Target/boundary:** r1:src/buf/chain.rs:130 (`Buf for Chain`, remaining,
  chunk, advance), r1:src/buf/take.rs:135 (`Buf for Take`), constructors
  r1:src/buf/buf_impl.rs:2400 and :2422. Slice callee:
  r1:src/buf/buf_impl.rs:2895; `&mut T` forwarding at :2887.
  Statically monomorphize `&[u8]`, Chain of slices, and Take of that Chain.
  No trait objects, FFI, async or concurrent calls in this proposed scope.
  General T/U implementations remain unverified; this is not arbitrary Buf support.
- **Requirement — documented:** Buf cursor movement and empty-chunk equivalence
  at r1:src/buf/buf_impl.rs:124-182 and :226-256; first-then-next ordering
  at :2407-2422; Take's maximum at :2378-2405 and
  r1:src/buf/take.rs:106-132. These are repository documentation, not owner approval.
  **Inferred proposal:** finite transition oracle below; owner must approve it.
- **Property/domain:** initial slices A/B of lengths 0..8, arbitrary byte values,
  arbitrary usize limit L (including 0 and usize::MAX), and bounded sequences of
  advance/set_limit observations. Let S be the current concatenated suffix.
  `remaining(Take)=min(|S|,L)`; chunk is the first underlying chunk truncated to L,
  not necessarily the entire visible sequence. For successful valid
  `0 <= n <= min(|S|,L)`, S becomes S[n..], L becomes L-n, and the next visible
  sequence is S[n..][..min(|S|-n,L-n)]. Chain distributes consumption as
  min(n,|A|) to A and the residual to B. Zero advance is a no-op.
  `set_limit(k)` replaces L, does not rewind the inner cursor.
  Re-snapshot S after permitted `get_mut`/first_mut/last_mut changes; do not assume
  those escape hatches leave the inner state unchanged.
- **Negative/counterexample conditions:** wrong boundary selection when A empty,
  consuming B early, limit underflow, byte reorder, wrong empty/chunk relation.
  Include invalid n>L and n>|S| as negative cases, not assumptions of universal
  success. Take asserts n<=L before delegating, but Buf permits panic OR clamp for
  excessive advance (:247-254); do not impose generic panic atomicity.
  Chain `remaining` uses saturating_add (:135-137): the finite slice pilot has no
  sum overflow, so it cannot establish the abstract >usize capacity case.
  A separate source-only arithmetic review should retain that case explicitly.
- **Method:** candidate `kani-rust-slices` and `kani-rust-arithmetic`, version
  1.0.0, bundled `references/kani.md` and index. Compatibility **unknown**.
  Conditional assurance: enabled checks and assertions over the stated finite
  harness domain with complete unwinding; arithmetic checks cover represented
  inputs subject to models, assumptions and tool soundness. No unbounded sizes,
  generic trait correctness or concurrency proof. Resolve Kani/Rust compatibility
  and library/panic modeling before calling this a supported pilot.
  Cargo edition 2021/MSRV 1.57/default std are observed at r1:Cargo.toml:7-24;
  neither MSRV nor CI nightly is a Kani compatibility pin.
- **Alternatives/readiness:** native property tests could exercise this same
  oracle without exhaustive assurance, at lower setup risk. Verus requires
  source adaptation; replacement/adaptation is not the selected adoption path.
  No production edit is recommended. Approval and compatibility block a harness.

### O2 — Vectored prefix, cap, and lifetime evidence

- **Priority:** second; sensitive unsafe lifetime boundary but higher setup cost.
  r1:src/buf/take.rs:160-187 (`chunks_vectored`) uses a 16-slot local array and two
  transmutes. r1:src/buf/chain.rs:165-169 composes callees via a destination suffix.
  Relevant contract: r1:src/buf/buf_impl.rs:184-223. Std-only; IoSlice internals
  and transmute validity were not inspected. No native verifier compatibility
  claim follows from the small function size.
- **Requirement — documented:** no payload modification, emitted total <= remaining,
  correct count, no panic, EOF returns 0 without destination mutation, empty
  destinations handled. **Inferred:** outputs form an ordered prefix of visible
  bytes; confirm empty component handling and permitted partial enumeration
  with maintainers. Do not require all bytes or all destination slots to be used.
- **Property/domain:** valid stable inner Buf, fragmented backing storage remaining
  live for the borrow, destination length 0..18, fragmentation 0..17 nonempty
  fragments (plus EOF), arbitrary L with 0/boundary/usize::MAX cases.
  Return k<=min(dst.len(),16) for Take; concatenation of emitted slices is a prefix
  of inner bytes of length <=min(inner.remaining(),L); no cursor/limit movement.
  At L=0 or EOF return 0 and preserve dst; at empty dst return 0.
  Loop invariant: copied slices form the already-emitted prefix, remaining local
  limit equals L minus emitted length until early return; index stays within cnt.
  Returned references must refer to the live inner storage, not local array data.
  Counterexamples: escape past L, wrong count/suffix indexing, changed cursor,
  panic with zero slots, or reference outliving backing bytes.
- **Existing assurance:** r1:tests/test_take.rs:34-84 checks limits 0/1/3/4/6/7 on two
  chunks, not >16 fragments or backing lifetime validity; Chain vectored test
  r1:tests/test_chain.rs:45-133 observes transitions. These were read, not run.
- **Method:** noncatalog source lifetime/callee review and proposed native regression
  tests first. Kani slices/unsafe-memory 1.0.0 are conditional candidates only:
  pin supported IoSlice/transmute/UB checks before any pilot; the unsafe guide
  covers only supported enabled UB checks in a modeled domain, not all Rust UB.
  Miri could inspect executed paths later, not prove arbitrary lifetimes.
  A separate finite model would not validate these production transmutes.
- **Dependencies:** resolve callee contract, allocation lifetime/alias obligations,
  empty fragments, and pinned tool support; retain unknown standard-library bodies.
  Approval required for any tests/harness. No source replacement proposed.

## Actionable handoff

| Work | Next bounded task / proposed files | Dependencies / approval | Acceptance evidence |
|---|---|---|---|
| D1-W1 | Read-only owner contract decision on O1 and saturation/invalid advance; produce `D1-contract-decisions.md` outside roots | Advice authorized; no upstream intent grant | Document owner decision or unresolved status, precise supported inner types, saturation and invalid-input semantics |
| D1-W2 | Read-only compatibility/command selection artifact `D1-command-plan.md` for O1 Kani and optional native tests; no execution | W1; selected pinned Kani/Rust and Cargo configuration still unknown | Exact tool version, cwd r1, arguments/harness location, feature/target/panic settings, finite sequence and unwind bounds, dependency inspection, exclusions; explicitly unexecuted |
| D1-W3 | Read-only O2 lifetime and fragment-boundary plan, `D1-vectored-plan.md` | Owner clarification and IoSlice/tool support unknown | Trace both transmutes to backing allocation; enumerate 0/16/17-slot boundaries and negative cases, or retain blockers |

Future implementation is a **separate blocked** work item: new harness/test files
only after named owner/execution authorization and isolation review; production
files unchanged. Any later run must retain exact versions/commands, source/harness
hashes, full output including failures, bounds/assumptions, successful unwind
completeness checks where applicable, and model-to-production correspondence.
No invocation has been selected or executed here.

## Review and limitations

Uses the supplied immutable skill, index/template and Kani guide, not the engine.
Candidate is unapproved. Source observations, inferred properties and proposed
work are distinct above. Source identity recheck is recorded in provenance.
No claim of complete caller coverage, verifier compatibility, recommendation
correctness, proof, or approval. No third opportunity warranted within scope.
