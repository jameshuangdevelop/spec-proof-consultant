# Dafny — opt-in verified-source replacement

Provenance: [catalog snapshot and shared rules](index.md).
`dafny-verified-kernel-codegen`, version `1.0.0`, status `documented`,
method `verified-source-codegen`, any original language.
Sources checked `2026-11-05`: [Dafny](https://dafny.org/),
[Dafny reference](https://dafny.org/latest/DafnyRef/DafnyRef).

Pattern: production function + arithmetic. Goals: arithmetic/functional
correctness/verified source—small replacement kernel written in Dafny.
Hard exclusions: **FFI, concurrency, assembly, async**.
Requires explicit opt-in to replacement/code generation and review of
generated-language integration/compiler trust. Determine whether rewriting is
acceptable and which supported compilation target/integration boundary is needed.
Before implementation establish rewrite approval, contract, target backend,
equivalence obligations, API/runtime/build/trust boundaries.

Assurance: Dafny verifies stated contracts of Dafny source; approved compilation can produce target-language code with separate integration and compiler trust obligations.

Does not establish: verification of arbitrary existing Rust/C/C++/other source,
equivalence to existing code without a separate argument, or correctness of
unverified extern implementations. Compatibility unknown: pin Dafny and supported
backend, runtime and integration toolchain.
Later work retains Dafny source, proof output, compiler/backend versions, commands
and separate correspondence/integration evidence. Never label the original code
verified. Alternative: a supported native-language scenario avoids rewriting.
