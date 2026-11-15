# Real-repository advisory evidence — 2026-11-12

**V1 and V2: NOT ACCEPTED. Report data, not accepted catalog knowledge.**
This is documentation-only publication of retained evidence, not a new experiment,
benchmark repair, approval, or permission to expose another cohort.

## What was observed

| Phase | Three numerical outcomes (repository order) | Procedural interpretation |
|---|---|---|
| V1 initial development | D1/D2/D3: 9.625 / 9.625 / 9.625 | Numerical observations retained |
| V1 development confirmation | D1/D2/D3: 10 / 10 / 10 | Not clean final campaign assurance |
| V1 holdout replica 1 | H1/H2/H3: null / null / null | BLOCKED_UNSCORABLE grade records |
| V1 holdout replica 2 | H1/H2/H3: null / 10 / null | Partial numerical observation only |
| V2 initial development | D1/D2/D3: null / null / null | UNSCORED; no individual evaluator grades issued |
| V2 repaired development | D1/D2/D3: 10 / 10 / 10 | Fresh independent grades; subsequently procedurally BLOCKED |

All **18 canonical author advisories**, including unsuccessful/ungraded phases,
are retained below. They cover **six unique assessed public repositories**, not
every acquired or research-only root. Null is not zero, a low grade, or a pass.
The [machine-readable results](results.json) retain raw/final values, factors,
weights, caps, findings where available, source/candidate identity, advisory
hashes, and the distinction between absent grades and blocked grade records.
Every numeric observation was checked against retained parent arithmetic audits;
this publication does not independently regrade semantic quality.

V1 failed read/time resource requirements. Its individual development scores
remain observations, not compliant campaign assurance. V2 initial mapping stopped
after an inclusive 201-line read against a 200-line maximum, before reports were
read or graded. Explicit development repair round 1 introduced conservative
100-line/inclusive reading and conditional execution **or a named read-only
command-selection artifact**, with metadata 0.2.1.

Fresh development advice for the repaired candidate received 10/10/10. After
scoring, the same evaluator separately applied the unchanged joint frozen rules:
**BLOCKED BEFORE LOCK / CONFIRMATION / HOLDOUTS**. Explicit repair is permitted,
but “overall” resource compliance does not clearly forgive prior overruns.
The ambiguity rule forbids choosing the favorable interpretation. No rules,
original scores, or original reports were rewritten. No V2 confirmation or new
holdouts began; unexposed holds remain preserved and undisclosed here.
No third campaign is authorized without human steering.

## Inventory

Each row links all three normalized canonical reports.

| Phase | Reports |
|---|---|
| V1 initial development | [D1](advisories/v1-dev0/D1-assessment.md), [D2](advisories/v1-dev0/D2-assessment.md), [D3](advisories/v1-dev0/D3-assessment.md) |
| V1 confirmation | [D1](advisories/v1-confirmation/D1-assessment.md), [D2](advisories/v1-confirmation/D2-assessment.md), [D3](advisories/v1-confirmation/D3-assessment.md) |
| V1 holdout 1 | [H1](advisories/v1-holdout1/H1-assessment.md), [H2](advisories/v1-holdout1/H2-assessment.md), [H3](advisories/v1-holdout1/H3-assessment.md) |
| V1 holdout 2 | [H1](advisories/v1-holdout2/H1-assessment.md), [H2](advisories/v1-holdout2/H2-assessment.md), [H3](advisories/v1-holdout2/H3-assessment.md) |
| V2 initial development | [D1](advisories/v2-dev0/D1-assessment.md), [D2](advisories/v2-dev0/D2-assessment.md), [D3](advisories/v2-dev0/D3-assessment.md) |
| V2 repaired development | [D1](advisories/v2-dev1/D1-assessment.md), [D2](advisories/v2-dev1/D2-assessment.md), [D3](advisories/v2-dev1/D3-assessment.md) |

## Scope, pins and attribution

These were **rubric-informed, scoped advisory tasks**, not normal whole-repository
usage or a blind general-product benchmark. Scope and exact commit/tree pins,
production-file links and actual upstream license paths appear in
[sources.json](sources.json). Links are commit-pinned; no source bulk is copied.

| ID | Upstream | Scoped component | Upstream license paths |
|---|---|---|---|
| D1 | tokio-rs/bytes | Chain / Take adapters | MIT: LICENSE |
| D2 | littlefs-project/littlefs | caching block-device operations | BSD-3-Clause: LICENSE.md |
| D3 | pallets/itsdangerous | timed signing, signing, encoding | BSD-3-Clause: LICENSE.txt |
| H1 | google/double-conversion | string-to-double parsing | BSD-3-Clause: LICENSE, COPYING |
| H2 | google/btree | generic B-tree | Apache-2.0: LICENSE |
| H3 | rust-random/rand | SmallRng / xoshiro implementations | MIT OR Apache-2.0: COPYRIGHT, LICENSE-MIT, LICENSE-APACHE |

Approved assessment base: `ee8d0e655a2ac51ce032ea1e8de1388b69dce930`,
tree `b357629ecfde57d434bee1d3f86acc7f7aa1fc95`.
Repaired candidate: `706868e2d18810687180bb79ea7b9d7826197633`,
tree `30ea8295baea2f94da8ee62d1838493f9f002389`.
The existing contribution changed only SKILL, assessment template and plugin
metadata; this publication changes none of them.

## Frozen rules and provenance

The [RUBRIC](rubric/RUBRIC.md) and [RULES](rubric/RULES.json) are jointly normative.
Their common freeze preceded initial selection. Original SHA-256 values:

- RUBRIC.md: `7420a0ff0741e29351fa3f030d3366543ce11ea7c3734cba14c44597db0b59de`
- RULES.json: `c1c019802f9876e122fa2d71d6c6089eae01df5004b2b3103beb140be18008f9`
- Original SHA256SUMS: `8d10bc6088a51a7ecc7f46a3938f4397bdc72ec4502a064a87ca88b311e6e32d`

[manifest.json](manifest.json) records original and published SHA-256 values,
the original freeze metadata, retained input digests and all ten unchanged skill
asset hashes. Copies use **only mechanical, longest-first literal prefix
replacement** of private source/evidence roots with explicit placeholders.
Reverse equality against original bytes was checked for every copy. Published
hashes must not be mistaken for original hashes. RUBRIC is byte-identical where
no private prefix occurs; RULES baseline path metadata is normalized, with no
normative rule, threshold, constraint or score edited.

`<SOURCE-D1>` through `<SOURCE-H3>` denote the six pinned source roots.
`<E1>` and `<E2>` denote retained campaign evidence; `<PROJECT>` the publication
checkout; `<RUBRIC-BASELINE>` the older rubric-baseline checkout;
`<SESSION-EVIDENCE>` the common evidence parent. Private absolute prefixes are
deliberately not published. Artifact mentions in advisories refer to retained
evidence or proposed future work, not necessarily public files or executed work.

## Findings and limitations

[protocol.json](protocol.json) records procedural reasons and the three original
medium H01 dispositions. Each was corrected **in a new advisory**, by naming
D1/D2/D3 command-selection tasks with configuration, version, invocation and
approval prerequisites. Original reports/scores remain unchanged. This is not a
skill-only causal improvement claim: visible task configuration also specified
100-line windows.

- Scores are subjective advisory-quality grades, **not formal proof**, passing
  target tests, verified compatibility, or approved upstream intent.
- No target execution is claimed. Suggested tests, bounded checking, models,
  implementation proofs and source observations remain distinct.
- Exact model/settings/metering are unknown. Budget control was manual and
  instruction-based, not sandboxed or mechanically enforced. Hash/source
  identity evidence does not establish complete process telemetry.
- No normal whole-repo usability, causal improvement, cost or efficiency claim.
- Retained product evidence records **12 focused asset/distribution tests**
  passing on the repaired candidate, not 20. A preceding plugin-only mismatch
  test failed before metadata alignment; that failure was retained. No target
  tests were thereby run. This documentation-only packaging did not rerun
  product tests because all ten skill assets and existing tracked bytes remain
  unchanged.
- No applicable hosted CI in the committed candidate tree; an older runtime
  workflow is unrelated. No native-client update requalification was performed.
- Links were checked locally for structure/existence, not fetched over network.
  Private source maps, raw task/tool transcripts, internal model instructions,
  withheld future holdout identities/scopes/keys and reserve identities are not
  publication inputs.

**Next:** the parent alone commits/pushes/updates the existing draft PR, then an
independent evaluator reviews that committed fixed publication revision.
This implementor's packaging checks are not merge approval or a correctness
certificate. No catalog promotion.
