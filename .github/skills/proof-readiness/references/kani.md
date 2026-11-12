# Kani — finite Rust harnesses

Provenance: [catalog snapshot and shared rules](index.md). Each entry below:
version `1.0.0`, status `documented`, sources checked `2026-11-05`;
method `bounded-model-checking`, language Rust.
All three hard-exclude **FFI, concurrency, async, assembly, dynamic dispatch**.
Inspect actual callees and conditional configurations, not only the target body.

## kani-rust-arithmetic

Pattern: production function + arithmetic. Goals: arithmetic/functional
correctness—overflow, panics, approved integer postconditions in a small kernel.
Requires an isolatable sequential function and explicit domain/unwind completeness.
Resolve intended overflow semantics, call graph and pinned-release feature support;
obtain explicit approval for inferred contracts before implementation.

Assurance: Checks enabled safety properties and assertions for all inputs represented by a harness, subject to complete unwinding, models, assumptions, and tool soundness.

Does not establish: unbounded sizes beyond harness bounds, unstated intent, or
concurrency correctness. Compatibility unknown: pin Kani and matching Rust after
feature inspection. Later work checks approved postconditions and enabled
panic/overflow failures; retain harness, commands, full output and successful
unwinding assertions, reporting bounds and failures.
Alternatives: Verus for unbounded mathematical intent with source adaptation;
property-based tests give executable samples, not exhaustive verification.
Sources: [Kani](https://model-checking.github.io/kani/),
[loop unwinding](https://model-checking.github.io/kani/tutorial-loop-unwinding.html).

## kani-rust-slices

Pattern: production function + indexing. Goals: memory safety/functional
correctness—out-of-bounds and small-buffer assertions. Requires finite buffer/input
domain; cost grows with modeled size. Resolve legitimate lengths, preconditions,
indexing intent, dependencies and loop completeness. Inspect tests for off-by-one
requirements without treating their behavior as approved intent.

Assurance: Enabled checks and assertions over the stated finite harness domain with complete unwinding.

Does not establish: correctness at larger sizes or coverage of excluded
dependencies/models. Compatibility unknown: pin Kani/Rust and inspect allocation
and library support. Later checks require approved slice safety/postconditions,
exact bounds, preserved counterexamples, successful unwinding assertions and full
output. Alternative: Verus sequence specifications for arbitrary lengths after
proof adaptation.
Source: [loop unwinding](https://model-checking.github.io/kani/tutorial-loop-unwinding.html).

## kani-rust-unsafe-memory

Pattern: production function + unsafe. Goal: memory safety for isolated sequential
unsafe operations. Requires explicit allocation, pointer validity and aliasing
assumptions; inspect tool UB coverage, not a claim of all UB checking.
Inventory allocations, lifetimes, aliases and caller obligations; ensure the
harness models real callers without assuming away bugs. List unsupported checks.

Assurance: Supported enabled UB checks over the modeled harness domain; coverage depends on the pinned Kani release.

Does not establish: absence of every Rust UB class or soundness of arbitrary unsafe
abstractions/FFI. Compatibility unknown: inspect pinned-release UB/feature support.
Later work retains harness, assumptions, versions, exact commands and full output;
partial UB coverage is not a complete memory-safety proof.
Alternative: Miri dynamically detects UB on executed paths, not exhaustive proof.
Sources: [Kani](https://model-checking.github.io/kani/),
[limitations](https://model-checking.github.io/kani/limitations.html).

Catalog example for arithmetic/slices:
[official bounded harness/slice tutorial](https://github.com/model-checking/kani/blob/main/docs/src/tutorial/loops-unwinding/src/lib.rs).
It is not reproduction evidence; no local execution is implied.
