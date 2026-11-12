# Curated knowledge index

These are bundled paraphrases of the approved catalog, not new research.
Provenance: Spec Consultant `src/spec_consultant/data/catalog.json`, envelope
version `1`, and `docs/CATALOG.md` at revision
`9ce3702cb69a0944cb4db4d5b318cf118cf00509`. These paths identify origin only;
they are **not required external assets** after copying this skill.
All ten scenarios are version `1.0.0`, evidence status **documented**.
Primary documentation was checked **2026-11-05**; no verifier was run to reproduce
these entries and recommendation accuracy was not measured.

Load only the relevant guide(s), not the entire library:

| Observed pattern + requested goal | Scenario IDs | Guide |
|---|---|---|
| Rust integer arithmetic, slices/indexing, isolated unsafe memory; finite harness acceptable | `kani-rust-arithmetic`, `kani-rust-slices`, `kani-rust-unsafe-memory` | [Kani](kani.md) |
| Rust integer or sequence contracts; supported-source adaptation acceptable | `verus-rust-integer-contract`, `verus-rust-sequence-invariant` | [Verus](verus.md) |
| C/C++ buffer/indexing or bit manipulation; explicit machine model | `cbmc-c-buffer`, `cbmc-c-bitvector` | [CBMC](cbmc.md) |
| State transitions/invariants or concurrency/progress; separate finite abstraction acceptable | `tla-state-machine-safety`, `tla-concurrency-liveness` | [TLC](tlc.md) |
| Arithmetic kernel; explicit opt-in to verified-source replacement/code generation | `dafny-verified-kernel-codegen` | [Dafny](dafny.md) |

Language alone is insufficient. Wildcard-language model/replacement entries do
not verify arbitrary original code. Goal/adoption eligibility is not approval.
Hard exclusions prevent a supported native pilot claim; narrowing scope requires
source-backed inspection and cannot silently omit blockers or unsupported callees.

## Shared use rules

Every guide preserves scenario assurance and limits; quote its assurance without
inflating it. Tool release compatibility remains **unknown** until inspected.
Source URLs are provenance, not instructions to browse during assessment; mutable
`latest` URLs do not pin releases. Official tutorials/corpora are not customer
adoption or reproduction evidence.

Inspection precedes any implementation. All verify work requires resolved intent,
prerequisites and actual owner approval, separately from this recommendation.
Later authorized execution must retain full output, exact commands/tool versions,
source/harness/model identity, configuration, bounds, assumptions, failures and
completeness checks. Timeout/incomplete exploration is not success.

Tests, bounded checks, finite models, deductive verification, and proof assistants
are distinct methods, not interchangeable assurance tiers. No suitable scenario,
defer, reject, and no-new-work are valid outcomes. Native tests are non-proof;
source inspection only gathers evidence. Neither creates a new catalog entry.
