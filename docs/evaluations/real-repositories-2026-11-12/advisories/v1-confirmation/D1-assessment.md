# Proof-readiness advisory — D1 / dev-confirm-ee8d0e6

Status: completed advisory, recommendation only; no target execution or verifier result.
2026-11-12. Task: real-baseline/dev-confirm. Goal: useful contracts for existing
Chain/Take production code, without replacement or production changes.
Audience: bytes maintainers/downstream owners. Campaign authority is read-only,
not upstream intent approval or implementation authorization.

## Scope and evidence

| Root | Selected absolute root | Identity | Inspected | Skipped/unknown |
|---|---|---|---|---|
| r1 | <SOURCE-D1> | tokio-rs/bytes; commit f2cf483f13c9956a0f24ce2b7527f2318b0c8a2c; tree 8a832951605a44373017ac9abb8c125b8f02f2c6; clean read-only Git status | Entire chain.rs/take.rs; bounded Buf/BufMut interfaces and slice implementation; exports, manifest, README, test_chain/test_take, relevant test_buf macro/callers, CI 1–180 | Bytes/BytesMut allocation/refcount internals, iterators, UninitSlice internals, other storage types, external Rust/std bodies, CI scripts and last CI section; no whole-library claim |

Output: this file, outside all three selected roots. Before reading, the supplied
regular-file inventories were checked for symlink components/types and hashes;
metadata discovery found no symlinks or nested .git entries outside each root's
own .git. This is a point-in-time check, not atomic no-follow access, secret
detection or an OS sandbox. Before/after identity and the precise read ledger
are in COMMANDS.md / RESULT.json. No historical test result was supplied.
Existing tests and CI definitions are inspected evidence of intended coverage,
not evidence of a passing run.

## Decisions

Prefer two small evidence tasks over adding a verification framework immediately.
There is already substantial composition coverage: the test macro checks empty,
advance, rejection and vectored behavior
(`r1:tests/test_buf.rs:25-115`, `buf_tests!`), instantiated for split slices
and nested Chain/Take (`r1:tests/test_buf.rs:388-418`, `make_input`).
Tests also exercise cross-buffer copying and mutable capacity saturation
(`r1:tests/test_chain.rs:132-178`, `chain_growing_buffer`,
`chain_overflow_remaining_mut`, `chain_get_bytes`). None ran here.
Incremental value is concentrated at the vectored scratch-array/lifetime boundary
and a reusable state-transition contract, not duplicating the examples.

### O1 — Vectored prefix and lifetime boundary (priority 1)

- **Impact/cost:** a wrong prefix or invalid borrowed slice affects consumers of
  scatter/gather I/O. A boundary matrix and unsafe-source review are a modest
  task; tool support/lifetime analysis cost is uncertain.
- **Target/call boundary:** `r1:src/buf/take.rs:162-194`,
  `Take::chunks_vectored`, caps its temporary IoSlice array at 16, calls
  `inner.chunks_vectored`, truncates the last slice and uses two transmutes.
  `r1:src/buf/chain.rs:168-173`, `Chain::chunks_vectored`, delegates twice,
  using the first result as the second destination offset. The default Buf
  implementation and obligations are at
  `r1:src/buf/buf_impl.rs:184-225`, `Buf::chunks_vectored`.
  This is enabled only with `std` (default per `r1:Cargo.toml:23-25`).
  Standard-library IoSlice bodies/representation are not inspected; calling a
  std type alone is not evidence of FFI. Generic concrete callees must obey the
  Buf contract, including counts within destination capacity. Arbitrary
  `dyn Buf` callees are outside a supported Kani pilot.
- **Requirement:** documented: output slice lengths sum to at most remaining,
  underlying data is unchanged, end-of-buffer returns zero without changing
  destination, and empty destinations must be handled (Buf citation above).
  The natural byte-prefix/order interpretation comes from “starting at self's
  current position” and Chain's consume-first contract
  (`r1:src/buf/buf_impl.rs:2407-2427`, `Buf::chain`).
  Exact trailing-slot preservation for nonempty output and returning *all*
  available bytes are not asserted as universal requirements. Maintainer approval
  of the proposed test oracle is unresolved; tests do not supply that approval.
- **Property:** for lawful sequential Buf implementations, any limit L and
  destination capacity d, n is in 0..=d; concatenating dst[..n] yields a prefix
  of the current logical stream of length <= min(L, inner.remaining()); no data
  mutation, cursor change, panic or out-of-lifetime references. For nonempty
  remaining and d>0, at least one returned slice is nonempty; when d=0, n=0.
  If remaining=0, destination is unchanged. The loop invariant is that the
  emitted prefix equals the consumed prefix of the temporary slice sequence,
  emitted length <= initial L, and local residual limit equals L minus emitted
  length until the truncating return. Lifetime obligation: every returned view
  refers to inner storage borrowed for `'a`, not the local descriptor array.
  Counterexamples: n>d, wrong seam byte, total length>L, expired storage,
  mutation at EOF, or panic for a legal empty destination.
  Include d=0,1,15,16,17; zero/empty inner fragments; L=0, seam−1/seam/seam+1,
  larger-than-stream and usize::MAX. No invented 16-slice public maximum:
  the implementation may return a partial prefix for larger d.
- **Method:** first noncatalog source audit and proposed native regression cases.
  `r1:tests/test_take.rs:33-87`, `take_chunks_vectored`, already covers
  limits 0,1,3,4,6,7 on two chunks; the inspected test does not span the 16-slot
  scratch threshold. These are sample tests, not proofs of lifetime safety.
  `kani-rust-slices` / `kani-rust-unsafe-memory` 1.0.0, bundled
  `references/kani.md`, are conditional possibilities only: the former gives
  enabled checks/assertions over the stated finite harness domain with complete
  unwinding; the latter only supported enabled UB checks in the modeled domain,
  dependent on pinned release. They do not prove all Rust UB classes, arbitrary
  sizes, or excluded dependencies. FFI, concurrency, async, assembly and dynamic
  dispatch are hard exclusions. Exact std/IoSlice/transmute support is unknown;
  no supported/ready native pilot is claimed. Do not stub away those operations
  and call the result verification of this path.
- **Alternatives/readiness:** native tests plus manual lifetime argument best fit
  current no-change constraints. Miri would observe UB only on executed paths,
  after separate approval and isolation. No tool or test implementation is
  approved. Requirement confirmation and std-body/support investigation precede
  any harness proposal.

### O2 — Compositional cursor/limit contract (priority 2)

- **Impact/cost:** small concrete slice-based state sequences can expose seam,
  reset and nested-adapter errors beyond single examples; low evidence cost,
  bounded-check integration cost unknown. Less urgent than unsafe vectored work.
- **Target/boundary:** `r1:src/buf/chain.rs:132-191`, `Buf for Chain`;
  `r1:src/buf/take.rs:103-159`, `limit`, `set_limit`, `Buf for Take`;
  constructors at `r1:src/buf/buf_impl.rs:2379-2427`, `Buf::take/chain`;
  concrete slice remaining/chunk/advance at
  `r1:src/buf/buf_impl.rs:2895-2916`, `Buf for &[u8]`.
  Methods are generic/static when concretized to slices/adapters, not inherently
  dynamic dispatch. copy_to_bytes is **not** within the small native pilot:
  both overrides/default path reach Bytes/BytesMut storage/allocation or a
  concrete inner override (`r1:src/buf/buf_impl.rs:2346-2377`); those bodies
  remain outside the inspected boundary, so its native compatibility is unknown.
- **Requirement:** documented read-at-most limit, consume a then b, remaining
  bounds and advance semantics, at the citations above and
  `r1:src/buf/buf_impl.rs:124-182,227-256`, `Buf`.
  Inferred candidate saturation rule follows actual `saturating_add` in Chain;
  tests establish an example of mutable saturation, not universal authority.
  Maintainers must approve how that rule is documented for synthetic large
  remaining counts. No requirement of panic-state atomicity is invented.
- **Property:** model each lawful inner as a byte stream with cursor p and
  remaining R. Chain exposes A suffix followed by B suffix; its reported
  remaining is min(usize::MAX, Ra+Rb), not unchecked addition. Take reports
  min(R,L), and its chunk is the inner chunk truncated to L. For
  0<=c<=min(R,L), Take::advance advances inner exactly c and sets L'=L−c;
  Chain advances a by min(c,Ra), then b by c−min(c,Ra), for legal c.
  set_limit(k) changes no inner cursor and resets L to k; direct get_mut access
  may change inner independently, so L is not assumed to be the original limit
  minus all underlying consumption. Invariant across legal operation sequences:
  exposed bytes are the designated stream suffix restricted by current L,
  nonempty chunk iff remaining>0. c=0 is a no-op. For c>remaining, Buf allows
  panic or end-clamping, not arbitrary behavior; concrete Take additionally
  asserts c<=L. Rejected calls need not leave state unchanged. Include zero,
  seam, exhausted first buffer, L>R, usize::MAX, limit reset after exhaustion,
  nested adapters and direct inner advancement. Counterexamples are incorrect
  suffix/cursor/limit or overflow wraparound; panic on a legal c is also a failure.
- **Method:** investigate a non-std, concrete slice Chain/Take pilot without
  replacing production. `kani-rust-arithmetic` and `kani-rust-slices` 1.0.0
  (`references/kani.md`) fit the observed arithmetic/indexing pattern only
  conditionally. Arithmetic assurance is enabled safety checks/assertions for
  all represented inputs subject to complete unwinding, models, assumptions and
  tool soundness; slice assurance as in O1. A proposed domain of two slices of
  0..=8 bytes and up to four operations is useful but would not discharge
  unbounded nesting, huge capacities, allocation, mutable unsafe paths or
  vectored lifetimes. Separate arithmetic obligations at machine maxima must
  remain, not be “proved” by tiny allocations. Kani/Rust/usize width,
  panic behavior, library and configuration compatibility remain unknown.
  No exclusion may be assumed away by success stubs.
- **Alternatives/readiness:** a native property-test matrix is cheaper and can
  reuse existing macro callers; sampled observations only. Verus adaptation
  is deferred: no source adaptation approval, and no need to change production
  merely to add an exploratory contract. New framework adoption requires a
  demonstrated gap after inspecting/running existing tests in a separate task.

## Actionable handoff

| Work | Next bounded task / proposed files | Dependencies / approval | Acceptance evidence |
|---|---|---|---|
| W1 | Read-only: confirm O1 oracle, concrete caller types and IoSlice lifetime argument; compare tests/test_take.rs and test_buf.rs with d=0/15/16/17 matrix | Present campaign grant permits bounded source evidence only; owner intent and external-source scope unresolved | Cited contract table, lifetime provenance for both transmutes, existing-vs-missing cases; retain unknowns, no “safe” verdict from tests |
| W2 | Read-only: define O2 transition oracle and feature/callee inventory for concrete slices | Separate maintainer/downstream acceptance of intent required before implementation | Domains, reset/get_mut/rejection semantics, saturation rule and config/support questions documented without dropping large-domain obligations |
| W3 | Separately proposed tests/test_take.rs/test_chain.rs additions, or external bounded harness only if justified | Blocked: named owner approval, W1/W2, execution isolation, pinned tools/config and explicit write/execution authority | Original source identity, exact commands/tool versions, harness/test hash, inputs/bounds, assumptions, enabled checks, full output including failures; complete unwinding for bounded checking; source correspondence and unsupported checks stated |

No commands in W3 ran. No production edits or replacement are recommended.
Defer the broader mutable BufMut proof: its initialization/aliasing obligations
(`r1:src/buf/buf_mut.rs:30-107`, `BufMut::advance_mut`;
`r1:src/buf/chain.rs:193-226`, `BufMut for Chain`) and UninitSlice/allocation
dependencies are not discharged by the read-only slice pilot. Existing
overflow tests reduce the immediate benefit of another isolated arithmetic test,
but do not establish unsafe soundness. A separate TLC state abstraction or
Dafny replacement would add correspondence/replacement costs with no present
approval or incremental need.

## Review and limitations

Root IDs, cited symbols and loaded Kani guidance were manually reviewed; no proof,
recommendation validation, exact target compatibility or exhaustive coverage is
established. CI 1–180 declares feature/platform/Miri work but scripts and results
were not inspected/reproduced. One beyond-EOF read of test_chain.rs failed
(201–360; actual 178 lines); no source was lost from its already complete read.
Search head limits and skipped ranges are recorded in the ledger. Approval,
external bodies, large-domain behavior and unsafe implementation obligations
remain explicit blockers to implementation, not conclusions of incorrectness.
