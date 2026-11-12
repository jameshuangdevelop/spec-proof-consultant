# Verus — adapted Rust contracts

Provenance: [catalog snapshot and shared rules](index.md). Both entries:
version `1.0.0`, status `documented`, method `deductive-verification`, Rust;
source [Verus guide](https://verus-lang.github.io/verus/guide/), checked
`2026-11-05`. Both hard-exclude **FFI, unsafe, async, assembly, dynamic dispatch,
concurrency**. Supported-source adaptation is required, not drop-in checking.

## verus-rust-integer-contract

Pattern: production function + arithmetic. Goals: arithmetic/functional correctness,
approved pre/postconditions without enumerating bounded executions.
Requires willingness to adapt supported Rust and explicit machine-integer versus
mathematical-integer semantics. Inspect whether kernel and every callee fit the
subset, source-to-contract mapping, migration scope and trusted boundaries.
Obtain approval for contracts and production adaptation.

Assurance: Deductive verification of stated contracts for translated/adapted Verus code, subject to trusted specifications, external bodies, and the verifier/compiler trust boundary.

Does not establish: drop-in arbitrary Rust verification, correctness of external
bodies, unstated requirements or compiler. Compatibility unknown: pin Verus and
required Rust toolchain; inspect every callee.
Later work retains adapted source, assumptions, exact version/output and inventory
of `external_body`, admits and trusted declarations; do not hide proof gaps.
Alternative: Kani finite harness checks may require less production adaptation.

## verus-rust-sequence-invariant

Pattern: production function + indexing. Goals: memory safety/functional correctness,
length/indexing and approved sequence postconditions using invariants.
Requires adaptation into supported Verus and proof/loop-invariant authoring budget.
Resolve the sequence relation defining success and container support/trust;
map source operations to specification relations and inventory adaptation/API
obligations.

Assurance: Proof of stated sequence invariants and postconditions in adapted Verus code under declared preconditions and trusted APIs.

Does not establish: arbitrary Rust library correctness or automatic proof of the
original unadapted application. Compatibility unknown: inspect release-specific
container/borrowing support. Later work retains proof source, exact tool output,
trusted-boundary inventory and reviews correspondence to original behavior before
integration. Alternative: finite Kani buffers may need less initial proof effort.
