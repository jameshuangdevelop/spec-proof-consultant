# TLC — separate finite TLA+ models

Provenance: [catalog snapshot and shared rules](index.md). Both entries:
version `1.0.0`, status `documented`, method `explicit-state-model-checking`,
any implementation language. Neither has a catalog hard exclusion; this does not
make abstraction, correspondence or feature compatibility automatic.
Sources checked `2026-11-05`:
[TLA+ tools](https://lamport.azurewebsites.net/tla/tools.html),
[official Examples corpus](https://github.com/tlaplus/Examples).
The corpus distinguishes TLC models and TLAPS proofs; it is not local execution
or reproduction evidence.

## tla-state-machine-safety

Pattern: state machine. Goal: state invariants in explicit finite models.
Requires acceptance of a separate abstraction, finite constants and implementation
correspondence review. Extract variables, transitions, approved invariants,
source/requirement links, omitted behaviors and abstraction boundary.

Assurance: Invariant checking for the explored finite TLA+ model and recorded configuration, subject to constraints and complete exploration.

Does not establish: implementation correctness without correspondence evidence,
an unbounded theorem, or liveness from safety checks. Compatibility unknown: pin
TLC/TLA+ tools and Java; retain configuration.
Later work retains model/configuration, exact TLC commands, state counts and full
output, reviews correspondence and labels finite-model results, not implementation
proofs. Alternatives: TLAPS mechanically checked deductive proofs are separate
work; stateful tests check implementation traces, not exhaustive abstract spaces.

## tla-concurrency-liveness

Pattern: concurrency. Goals: progress/state invariants—deadlock, starvation and
approved temporal properties. Requires scheduling/fairness model, manageable
finite state space and separate correspondence review. Resolve promised progress,
weak/strong fairness and scheduling abstraction; link to approved requirements and
justify assumptions or leave unresolved.

Assurance: Safety/liveness checks explicitly configured over a finite TLA+ model under recorded fairness assumptions and completed exploration.

Does not establish: real scheduler fairness, unbounded process-count correctness,
or implementation race freedom. Compatibility unknown: pin TLC and inspect temporal
property/symmetry settings. Later work retains fairness, configuration, exact
commands and complete output, distinguishing deadlock, safety, liveness and
implementation correspondence. Alternatives: TLAPS for separate unbounded temporal
proof effort; concurrency testing explores implementation schedules without
automatic model correspondence.
