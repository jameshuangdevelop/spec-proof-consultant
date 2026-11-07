# Agent organization

Humans work in one Copilot CLI session with the **orchestrator**. It delegates
bounded work to specialists in separate contexts and returns decisions, evidence,
and PRs to the human. No extra terminals or manually coordinated specialist
sessions are required.

```text
Human: goals, clarification, permissions, and PR approval
                         |
                   Orchestrator
              /          |          \
       Implementor    Evaluator    Researcher
         changes      independent   candidate
        and checks      findings    knowledge
              \          |          /
              Results return to orchestrator
```

| Role | Responsibility | Must not do |
|---|---|---|
| Orchestrator | Scope, task graph, delegation, human decisions, integration, branch/PR publication | Substitute agent agreement for evidence or human approval |
| Implementor | Bounded changes, focused regressions, trusted product checks | Self-approve, change independent reports, promote knowledge |
| Evaluator | Independent source/behavior checks, reproductions, held-out cases | Repair production work or grade against a desired verdict |
| Researcher | Primary-source research, scenario proposals, examples and exclusions | Treat claims as reproduced evidence or update accepted knowledge |

All four profiles opt into repository instructions. Only the orchestrator has
the `agent` tool. Specialists use `user-invocable: false` to keep them out of
normal manual selection; programmatic access can still exist. These settings and
instructions are not an access-control boundary, filesystem sandbox, branch
protection, or guarantee that models obey every instruction.

## Start one session

Use a checkout containing this contribution:

```sh
cd /path/to/proof-readiness
copilot --agent orchestrator
```

Alternatively start `copilot`, select `/agent orchestrator`, and give it an
objective. Restart an existing CLI session after adding/changing agent profiles.
CLI support and local profile overrides can affect loading; check `/agent` and
`/env` rather than assuming the intended profiles loaded.

Example initial prompt:

```text
Act as this project's orchestrator. Read docs/AGENT-ORGANIZATION.md and
repository instructions. Inspect current branches, PRs, dirty work, and
retained evaluation artifacts before deciding what remains to be done.

Coordinate the implementor, evaluator, and researcher as subagents in
this session. I will communicate only with you. Preserve concurrent work;
use a fresh branch and isolated worktree for each new contribution.

First independently evaluate the latest relevant implementation. Repair
reproducible failures and obtain reevaluation of the fixed revision.
Research new scenarios only after the handoff is reliable, or when a
specific missing fact blocks that work. Use existing contribution schemas
if present; leave research candidates unaccepted pending review.

Open a PR with scoped evidence and limitations. Do not merge or promote
material catalog changes without approval. Return only decisions needing
my input, meaningful progress, blockers, and the final PR handoff.
```

Custom agents are definitions, not persistent employees. The orchestrator invokes
them on demand; this contribution does not start services, schedule research,
add a workflow runtime, or implement an automated approval system. Delegation can
consume additional credits. Use configured models and agreed execution budgets.
If custom delegation is unavailable, report it instead of spawning nested CLI
processes or making the human coordinate hidden substitutes.

## Task and result contracts

The orchestrator gives each specialist:

- Task ID, bounded goal, acceptance criteria, dependencies, and stop conditions.
- Checkout/worktree, branch/base revision, and dirty-content identity if relevant.
- Exact source, reproduction, schema, and retained-evidence locations.
- Allowed writable paths, authorized commands, environment/network constraints,
  and any explicit target-execution authorization.
- Expected result/evidence destination and required output.

Specialists return:

- Task ID and status: completed, blocked, or failed.
- Observations versus hypotheses; changed files or proposed changes.
- Exact commands and results, assessed tree identity, and evidence paths.
- Findings, counterexamples, unresolved intent/compatibility, and limitations.
- Recommended next action and any decision the orchestrator must escalate.

Keep operational task state in the session's task system and retain substantial
evidence outside assessed roots. Record locations so a new session can resume.
Do not include secrets or raw private code in external research prompts or PRs.
An immutable evaluator report must not be overwritten by an implementation fix.

## Working loop and review gates

1. **Intake:** inspect actual repository state and scope the next contribution.
2. **Implement/research:** delegate only what is needed. Materialize research
   candidates through the implementor if the contribution format is available.
3. **Evaluate:** pin an unchanging tree and use a separate evaluator context.
   Parallel work requires independent writable scopes; a worktree is not
   isolation for executing untrusted code.
4. **Repair:** return reproductions, not a request for a positive verdict. Bound
   retries; preserve findings and escalate unresolved decisions.
5. **Publish:** orchestrator stages only this contribution, records checks and
   evaluation identity, pushes a new branch, and opens a PR. Use draft status
   for incomplete/blocked work. Human approval remains required before merge.

An existing PR is not permission to include unrelated dirty changes. New work
starts from an approved base, unless a dependent/stacked branch is explicitly
agreed and described in its PR. Specialists never merge or act as human reviewers.
Research acceptance additionally requires the project's evidence and promotion
rules; a positive evaluator report alone does not promote knowledge.

## Offline assessment versus authorized research

The product's repository assessment remains offline and read-only. A separately
authorized research task may fetch public sources. Verifier/tool reproduction
against untrusted targets needs explicit authorization and real isolation, not
merely shell permissions, a temporary directory, or a Python virtual environment.
Unavailable isolation means documented/unexecuted evidence, not a fabricated run.

## Configuration references

- [Custom agents](https://docs.github.com/en/copilot/concepts/customizations/custom-agents)
- [CLI custom agents](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli)
- [Configuration and tool aliases](https://docs.github.com/en/copilot/reference/custom-agents-configuration)

These instructions target Copilot CLI. Invocation flags and tool behavior can
differ in other Copilot environments; unsupported configuration must not be
presented as enforced isolation.
