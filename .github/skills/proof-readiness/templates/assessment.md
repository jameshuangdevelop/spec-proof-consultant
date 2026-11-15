# Proof-readiness advisory

Status: recommendation only; no target execution or verifier result.
Date / user goal / adoption constraints:

## Scope and evidence

| Root ID | Selected absolute root | Revision / dirty state (or unavailable) | Inspected areas | Skipped / unknown areas and why |
|---|---|---|---|---|
| r1 | | | | |

Output path (outside all selected roots); path/read safety limitations:
Discovery budget used / truncation / overruns / concurrency or freshness limitations:
Existing assurance: cite artifacts and any separately supplied result provenance;
presence alone is not a pass. Do not claim independently reproduced results.

Use `r1:relative/path:line` + symbol for citations throughout. Mark missing line
information explicitly. Separate observations from hypotheses.

## Decisions

Summarize represented opportunities, deferred/rejected alternatives and reasons,
or no-new-work. Include catalog gaps and incremental benefit over existing
assurance. At most three detailed opportunities; zero is valid.

### O1 — title (omit if none)

- Priority and rationale: impact, cost/effort uncertainty, incremental assurance.
- Target and call/configuration boundary: source citations, callees/callers,
  conditions, FFI/concurrency/unsupported or unread dependencies.
- Requirement: statement, `documented` / `inferred` / `unresolved`, citations,
  authority and actual approval status. Tests are observed behavior, not intent.
- Property: precise input domain; preconditions; postconditions; loop/state
  invariants (or not applicable with reason); counterexample conditions.
- Method: scenario ID/version + bundled guide, or explicit noncatalog source
  inspection/native tests. Compatibility: supported with evidence / unknown /
  excluded. State the scenario's exact conditional assurance, non-coverage,
  assumptions and exclusions; do not turn a recommendation into a proof.
- Alternatives: rejected/deferred methods and reasons.
- Dependencies and readiness: evidence work versus implementation, requirement
  decisions, compatibility checks, adoption and execution approval. Unknowns block
  implementation; no approval is granted by this report.

## Actionable handoff

| Work ID | Next bounded task / proposed files | Depends on | Approval and readiness | Acceptance / evidence required |
|---|---|---|---|---|
| W1 | Read-only investigation, if warranted | | State actual grants or missing approval; no invented grant | Source-backed answers or explicit unknowns |

Implementation, if proposed, is a separate blocked task until named prerequisites
and actual approvals are satisfied. For each task requiring future execution,
provide a clearly unexecuted conditional invocation specification (tool, arguments,
working directory, version/configuration prerequisites), or name a read-only
command-selection task/artifact that resolves the tool version, configuration and
invocation before execution. Keep unresolved support explicit; do not invent
versions or treat command selection as execution approval. Pure source-only tasks
need no shell commands.
Separately describe future execution evidence (exact versions/commands,
source/harness/model, bounds, assumptions, complete output, failures,
correspondence) without claiming any execution here.
If no work is warranted, say so and omit task rows.

## Review and limitations

Check citations/root IDs, loaded guide provenance, approval states and dependency
order. Record source identity changes/unavailability, unresolved intent,
compatibility, coverage and safety limitations. This advisory has not established
proof, target compatibility, exhaustive coverage or recommendation correctness.
