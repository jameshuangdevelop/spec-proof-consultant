# CBMC — finite C/C++ harnesses

Provenance: [catalog snapshot and shared rules](index.md). Both entries:
version `1.0.0`, status `documented`, method `bounded-model-checking`, C/C++;
source [CBMC](https://www.cprover.org/cbmc/), checked `2026-11-05`.
Both hard-exclude **assembly, concurrency, FFI**. C++ linkage alone is not an
unavailable foreign implementation; actual external bodies still need inspection.

## cbmc-c-buffer

Pattern: production function + indexing. Goals: memory safety/functional correctness,
array bounds, pointers and approved buffer assertions.
Requires compilation flags, include paths, data model, callee bodies, and explicit
loop/allocation bounds. Resolve compiler extensions, C++ features, sound environment
stubs and complete unwinding. Record architecture, allocation semantics, flags,
includes, stubs, buffer contracts and external-call boundaries; approve intended
behavior and bounds.

Assurance: Enabled memory/UB checks and assertions over the modeled C/C++ harness domain with complete unwinding and specified platform model.

Does not establish: unbounded heap/loops, unmodeled external implementations or
general support for every C++ feature. Compatibility unknown: CBMC 6 documentation
changes standard-check and malloc defaults; pin version and flags.
Later work retains exact commands, flags, enabled check inventory, bounds, complete
output and successful unwinding assertion results.
Alternative: sanitizers/fuzzing find executable bugs, not exhaustive assurance
outside executed inputs.

## cbmc-c-bitvector

Pattern: production function + bitwise operations. Goals: arithmetic/functional
correctness—shifts, overflow policy, approved bit-level assertions.
Requires explicit integer widths, signedness/platform model and isolated kernel
with modeled callees. Resolve signed overflow policy and implementation-defined
behavior; record compiler configuration and requirements, inspect every called
function and unsupported feature.

Assurance: Bit-precise enabled checks and assertions in the modeled harness domain with complete unwinding and explicit platform assumptions.

Does not establish: portability across unspecified data models or correctness
outside harness assumptions. Compatibility unknown: pin CBMC, machine model and
enabled checks. Later work retains exact commands/model/checks/output, bounds,
assumptions, failures and unwinding completeness.
Alternative: executable reference tests expose differential sample mismatches,
not proof over all inputs.
