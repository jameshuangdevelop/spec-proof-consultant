# Practical benchmark — 2026-11-15

**New prospective campaign; documentation evidence ready for independent
fixed-revision review, not self-approved for merge.** All twelve advisories
qualify under the frozen bounded advisory-quality gate. Ratings are subjective
source-grounded advisory evidence, not proof or general product validation.

| Cohort | Reports in slot order | Exact mean | Independent evidence |
|---|---|---|---|
| Development dev0 (D1–D3) | 10, 10, 10 | 10 | [Report](evaluations/dev0/REPORT.md), [grades](evaluations/dev0/RESULT.json) |
| Fresh confirmation (D1–D3) | 10, 10, 10 | 10 | [Report](evaluations/confirmation/REPORT.md), [grades](evaluations/confirmation/RESULT.json) |
| Heldout A (H1–H3) | 10, 77/8, 10 | 79/8 = 9.875 | [Report](evaluations/heldout-a/REPORT.md), [grades](evaluations/heldout-a/RESULT.json) |
| Heldout B (H1–H3) | 19/2, 10, 10 | 59/6 | [Report](evaluations/heldout-b/REPORT.md), [grades](evaluations/heldout-b/RESULT.json) |

All 12 are countable, each ≥9 and each exact cohort mean ≥9; no caps,
hard failures or unresolved high/critical findings. **Noncritical findings are
retained, not repaired:** A H2 underexplains the nested-mute secondary lead
(D=.75) and has pointer slips; B H1 attributes an unread masking helper to the
wrong filename (G=.75). The canonical advisories and single original grades
remain unchanged semantically.

Eight repositories were selected/frozen; only **six primary repositories**
were assessed, twice each. Two reserves were unused and their identities are
not published. Twelve reports do not mean twelve distinct repositories.

## Frozen rules and identity

- Exact prospective [QUALITY.md](protocol/QUALITY.md),
  [SCORING.json](protocol/SCORING.json), [OPERATIONS.md](protocol/OPERATIONS.md);
  [freeze](protocol/FREEZE.json) and independent
  [protocol review](protocol-review/REPORT.md), [result](protocol-review/RESULT.json).
- [Cohort freeze](provenance/COHORT-FREEZE.json):
  all eight pins/scopes/goals frozen before mapping or authoring.
- [First qualifying candidate lock](provenance/LOCK.json): as-is skill **0.2.1**
  locked immediately after dev0, without product repair. All ten locked files
  equal candidate commit `29df86f38291093e90055f30c00361930d5d27cd`
  ([PR 9](https://github.com/jameshuangdevelop/spec-proof-consultant/pull/9)).
  No subsequent candidate search, confirmation retry or heldout repair.
- Gate: weighted factors only 0, .25, .5, .75, 1; weights G/C=2,
  M/A/D/H=1.5; exact sum, lowest triggered cap, no N/A renormalization or
  pre-gate rounding. Each report and exact cohort mean ≥9; unresolved
  high/critical findings or material regression block acceptance.
- Publication base: approved main commit
  `544a37baabf4a08d6fc4c5c6a7ef9d64a5226b89`,
  tree `6b966f9e1a6874e811876e5ce350a01c489545f5`
  ([merged PR 10](https://github.com/jameshuangdevelop/spec-proof-consultant/pull/10)).

## Canonical advisories and author handoffs

Each cohort has three canonical Markdown advisories and **one aggregate**
author RESULT.json, matching the actual retained evidence (not invented
per-root result files).

| Cohort | Canonical reports | Aggregate author result |
|---|---|---|
| dev0 | [D1](advisories/dev0/D1/assessment.md), [D2](advisories/dev0/D2/assessment.md), [D3](advisories/dev0/D3/assessment.md) | [RESULT](advisories/dev0/RESULT.json) |
| confirmation | [D1](advisories/confirmation/D1/assessment.md), [D2](advisories/confirmation/D2/assessment.md), [D3](advisories/confirmation/D3/assessment.md) | [RESULT](advisories/confirmation/RESULT.json) |
| heldout A | [H1](advisories/heldout-a/H1/assessment.md), [H2](advisories/heldout-a/H2/assessment.md), [H3](advisories/heldout-a/H3/assessment.md) | [RESULT](advisories/heldout-a/RESULT.json) |
| heldout B | [H1](advisories/heldout-b/H1/assessment.md), [H2](advisories/heldout-b/H2/assessment.md), [H3](advisories/heldout-b/H3/assessment.md) | [RESULT](advisories/heldout-b/RESULT.json) |

## Sources, provenance and blinding

[SOURCE.json](sources/SOURCE.json) contains only the six primary selection
records. Per-root identity evidence includes original license-file hashes,
commit/tree pins and acquisition-only provenance:
[D1](sources/D1-identity.json), [D2](sources/D2-identity.json),
[D3](sources/D3-identity.json), [H1](sources/H1-identity.json),
[H2](sources/H2-identity.json), [H3](sources/H3-identity.json).
Frozen [development](scopes/development.json) and [heldout](scopes/heldout.json)
scopes preserve filename-based starting boundaries, exclusions, limits and
conditional owner-grant requirements. Actual inspected/skipped coverage,
bounded citation audits and unresolved closure appear in reports/results;
these are not complete target coverage or licensing-closure certificates.

Private maps were made by each fresh evaluator before its author assignment,
with at least two challenges/root; authors received frozen skill/scopes/goals,
not maps, rubric or feedback. Only neutral receipt evidence is public:
[dev0](provenance/receipts/dev0-maps.json),
[confirmation](provenance/receipts/confirmation-maps.json),
[A](provenance/receipts/heldout-a-maps.json),
[B](provenance/receipts/heldout-b-maps.json).
[Dev handover](provenance/author-handover-dev0.json),
[A handover](provenance/author-handover-heldout-a.json),
[B handover](provenance/author-handover-heldout-b.json) record later integrity
handoffs; no confirmation handover was supplied.
[Heldout barrier](provenance/HELDOUT-BARRIER.json) records both authors and
grades complete before release, with no feedback between authors. Receipt
timestamps corroborate packet production/receipt and later handoffs, but alone
are not independently sufficient to prove assignment timing or full context
blinding. Base64 is procedural routing, not encryption or a security boundary.

[Hash manifest and normalization recipe](provenance/MANIFEST.json) distinguish
original-private hashes from normalized-public hashes. Frozen rule bytes are
exact. All embedded evidence hashes still identify **original** artifacts;
use the manifest for public-file hashes. Absolute private prefixes become
logical `evidence://campaign`, `checkout://trusted-product` or
`checkout://agent-startup` locators; runtime UUIDs become stable neutral IDs.
Logical locators to unpublished maps/targets/runtime are provenance, not broken
local-file promises. No raw maps, source bodies, agent logs/prompts, reserve
identities, exclusions or historical allocation input are included. The
manifest deliberately omits itself and authored README/diagnostics; the
publication handoff records their hashes.

## Validation, diagnostics and limitations

[Product validation](provenance/PRODUCT-VALIDATION.json) records **12 trusted
asset/distribution tests passed**, not target verification, recommendation
correctness or native-client compatibility. This docs-only materialization
did not rerun product tests, trials, source audits or target tools.

[Diagnostics and limitations](DIAGNOSTICS.md) retain failed delivery/probes,
parser/accounting issues and historical boundaries. No safety waiver or
changed scoring rule is concealed by publication.

Known limitations: bounded manual source audits; excluded/platform/generated/
callback bodies and downstream behavior unresolved; no complete action,
syscall, injected-input, model-setting or cost certificate. Missing data is
**unknown, not zero**. Profiles, worktrees and shared-host metadata checks are
neither isolation nor atomic snapshots. No claim of target tests/proofs,
exact-tool/native-client compatibility, general usability, performance/cost
improvement, reviewer savings, exhaustive coverage or accepted new catalog
knowledge follows.

Older campaigns remain stopped/unaccepted; this fresh authorization is not a
retrospective waiver or regrade. Orchestrator must pin a new immutable
documentation revision, commission independent review, and handle branch/PR
publication and human approval. No merge authority is inferred.
