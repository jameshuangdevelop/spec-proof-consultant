# Catalog contributions and future evaluation

The catalog is pre-researched expertise, not a prompt that asks every assessment
to discover tools again. Normal assessment is offline. Knowledge gaps are explicit
outputs; they are not permission to fabricate support or perform background research.

## Contribution format

Submit a JSON catalog envelope matching
`src/spec_consultant/data/catalog.schema.json`:

```json
{
  "version": "1",
  "scenarios": [
    {
      "id": "stable-language-pattern-goal-id",
      "version": "1.0.0",
      "title": "A narrow scenario",
      "languages": ["rust"],
      "patterns": ["function", "arithmetic"],
      "goals": ["A specific property family"],
      "goal_tags": ["arithmetic"],
      "constraints": ["An explicit adoption or modeling constraint"],
      "hard_exclusions": ["ffi"],
      "questions": ["Which call dependencies are supported by the pinned release?"],
      "tool": "Kani",
      "method": "bounded-model-checking",
      "alternatives": [{"tool": "Verus", "reason": "Different source adaptation and proof obligations"}],
      "assurance": "Exact conditional assurance; never an unrestricted correctness claim.",
      "does_not_establish": ["What remains outside that assurance"],
      "tool_version": "Unknown compatibility unless a precise supported range is substantiated.",
      "sources": [{"url": "https://model-checking.github.io/kani/", "checked": "2026-11-05"}],
      "examples": [],
      "evidence_status": "documented",
      "work_items": [
        {
          "key": "inspect",
          "kind": "evidence-gathering",
          "property": "Resolve project intent and feature compatibility",
          "prerequisites": [],
          "acceptance": ["Record source-backed intent and unsupported features"]
        },
        {
          "key": "verify",
          "kind": "implementation",
          "property": "Check the approved property in the declared domain",
          "prerequisites": ["inspect"],
          "acceptance": ["Retain exact commands, versions, bounds, assumptions, and complete output"]
        }
      ]
    }
  ]
}
```

This is a **format example**, not an additional researched scenario. Contributions
are reviewed before merging into the packaged catalog; they are not automatically
loaded from untrusted target repositories.

```sh
spec-consultant schema catalog
spec-consultant validate-catalog /path/to/proposed-catalog.json
```

`patterns` and `hard_exclusions` must name signals actually implemented in the
profiler. New detection rules require focused positive/negative fixtures. Bump an
entry's semantic version for rule, assurance, source-applicability, or template
changes. The assessment stores a digest of the installed catalog; changed catalog
knowledge requires reassessment rather than silently re-rendering different advice.

Public examples must have a verified URL and an honest scope label. An official
tutorial is not evidence that an industrial codebase adopted the method.
Omit examples when unsubstantiated. The initial catalog only cites the official
Kani tutorial source and TLA+ Examples corpus; no local reproduction is implied.
Each primary source has its own check date. A mutable `latest` documentation URL
does not pin a tool release or establish target compatibility.

## Evaluation gate

1. **Grounding:** read primary tool documentation and any claimed example; record
   dates and check that each substantive assurance claim follows from the sources.
   Reject invented links, implied support based only on language, marketing-tier
   assurance rankings, or arbitrary-language Dafny verification claims.
2. **Scope:** make the scenario narrow enough to give a concrete property,
   target-pattern family, required assumptions, exclusions, and useful alternatives.
   State the trusted computing/modeling boundary, platform/feature/version limits,
   and what failure, timeout, or incomplete exploration means.
3. **Matching:** add positive and negative assessor fixtures, unknown-feature and
   boundary cases. Distinguish deterministic observations from heuristics and
   semantic judgments. Assess effects on false-positive leads and missed leads;
   do not invent accuracy percentages from synthetic fixtures.
4. **Actionability:** provide a small dependency-aware template with inspection
   prerequisites, source references, approval gates, acceptance criteria, and
   required execution evidence. Avoid specifying implementation contracts from
   syntax alone.
5. **Evidence review:** documented entries need primary sources. Reproduction
   promotion needs actual retained execution evidence, reviewed separately.
   Multi-case support requires distinct real cases and limitations; repeated
   synthetic examples do not establish general applicability.
6. **Integration:** review licensing and security of any contributed fixtures,
   run pytest, Ruff lint/format, schema and graph checks, and a packaged CLI
   example. Do not execute contributed target code during ordinary assessment.

## Future execution-evidence record

No autonomous researcher or scheduled updater exists in this version. A future
research contribution may propose a **separate** evidence record containing:

| Field | Required information |
|---|---|
| Identity | Scenario ID/version, case repository URL, revision, dirty status/content hashes |
| Tool environment | Exact tool/compiler/solver/OS versions and platform model |
| Inputs | Fixture/harness/model paths and hashes, approved contract, configuration, assumptions |
| Execution | Exact commands, start/end timestamps, exit status, complete retained stdout/stderr with hashes |
| Scope | Input/unwind/state bounds, completeness checks, trusted bodies/axioms/stubs, omitted behavior |
| Outcome | Failure/counterexample, timeout, unknown, bounded result, or scoped proof; no coerced pass |
| Correspondence | Separate argument connecting model/adapted/generated source to the original implementation |
| Review | Reviewer decision, reproducibility steps, negative cases, and known limitations |

That future record requires a versioned schema and explicit review before entries
may be promoted. Although the catalog schema names `fixture-reproduced` and
`multi-case-supported` as statuses, the v1 contribution validator accepts
**documented only**: it cannot substantiate the stronger statuses and deliberately
rejects them. Current pytest fixtures test the assessor's behavior, not a Kani,
CBMC, Verus, TLC, or Dafny result.
