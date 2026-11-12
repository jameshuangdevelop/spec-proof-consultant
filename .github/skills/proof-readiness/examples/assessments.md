# Worked decisions (illustrative, not repository results)

All paths, lines, symbols and requirements below are fictional, illustrating the
assessment template. No current checkout was assessed and no tool or target was
run. A real report must replace these with inspected evidence, scope/identity,
coverage, actual approvals and the full handoff. Citations are not reusable facts.

## 1. Positive lead: bounded Rust slices

- Scope: `r1 = /example/buffer`, revision unavailable; inspected `src/buffer.rs`,
  callers and `docs/api.md`; vendor/build trees skipped.
- Evidence: `r1:src/buffer.rs:12` `copy_prefix` indexes `dst` and `src`;
  `r1:docs/api.md:8` documents equal lengths, at most 16 bytes.
  Classification: documented; requirement authority still to be confirmed.
- Proposed property: for equal-length slices of length `0..=16`, output equals
  the initial source and no out-of-bounds access occurs; precondition equal
  lengths, invariant copied prefix equals source prefix, counterexample a
  differing copied byte or invalid access. Do not assume equal lengths if the
  actual API promises rejection of mismatches instead.
- P1: `kani-rust-slices` `1.0.0` ([guide](../references/kani.md)) could give
  finite-domain checks beyond sample tests with modest harness scope.
  Assurance: Enabled checks and assertions over the stated finite harness domain with complete unwinding.
  Not larger lengths or excluded dependencies/models. Compatibility unknown until
  allocation/library/callee and release support are established.
- W1: read-only confirm requirement authority, full call/configuration boundary
  and feasible bounds; accepted when citations and unknowns are recorded.
  W2: proposed harness, blocked on W1, approved domain and explicit execution/
  implementation approval; retain versions, exact harness/commands/output,
  bounds and successful unwinding assertions. No approval or execution exists.
- Defer Verus: adaptation budget not established; no unbounded guarantee promised.

## 2. Blocked: C buffer crosses an unknown external boundary

- Evidence: `r1:src/decode.c:24` `decode` indexes a destination and calls
  `foreign_fill`; `r2:include/bridge.h:9` declares it but body/configuration is
  unavailable. Both roots' revisions unavailable; binary vendor payload skipped.
- `cbmc-c-buffer` `1.0.0` ([guide](../references/cbmc.md)) is not an established
  match: the unavailable body/configuration leaves compatibility unknown.
  An ordinary external C declaration or missing body does not establish FFI;
  if a foreign-language implementation is later established, the FFI hard
  exclusion applies. Do not replace the external body with a success stub to
  claim supported verification.
- Requirement unresolved: test at `r1:tests/decode.c:30` observes truncation but
  does not approve it. Candidate domain (byte input length `0..=32`, capacity
  `0..=32`), precondition (valid storage), postcondition (reject or truncate) need
  owner resolution. Loop invariant and write-bound counterexamples cannot be
  finalized without the real callee contract.
- P1 evidence-only W1: locate body/configuration safely and request intended
  behavior; acceptance is a cited answer or retained unknown, not a proof.
  Harness implementation blocked on intent, boundary support and actual approval.
  Source inspection adds evidence only. Native tests could sample behavior after
  separate authorization, not settle intent or prove safety.

## 3. No new verification work

- Scope: `r1 = /example/docs-site`, revision unavailable; inspected page content,
  package metadata and routing configuration, dependency/build/secret areas skipped.
- `r1:content/start.md:1` is prose; `r1:site.json:4` selects static routing.
  No production arithmetic/indexing kernel or state-machine requirement was found
  in this bounded inspection. User goal is editorial consistency, no replacement.
- No catalog match established; do not force Dafny replacement or invent a TLC
  state model. Existing `r1:tests/links.test.js:7` asserts link behavior; its
  presence does not establish a passing run.
- Outcome: no-new-work for verification in the inspected scope. Editorial review
  is an honest non-proof alternative, not a new scenario. No implementation
  tasks or approval claims. Uninspected plugins remain a coverage limitation.
