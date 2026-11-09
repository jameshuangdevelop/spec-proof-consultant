# Spec Consultant

An agent-neutral, offline-first assessment CLI and Agent Skill for existing
repositories. It identifies **provisional** specification/proof opportunities,
creates a dependency-aware backlog, and generates a repository-specific execution
prompt. Curated verification knowledge ships with the package; normal assessments
do not research tools, call a model, or require model credentials.

This is an initial working version, not a universal proof-readiness detector.
Static rules do not understand intent. Use the skill with your existing agent to
inspect source, propose precise contracts, and resolve requirements.

## One-session agent team

Use `copilot --agent orchestrator` in this checkout. The orchestrator is the
human-facing lead and delegates to the implementor, independent evaluator, and
researcher without requiring extra terminals. See the
[org chart, role boundaries, and startup prompt](docs/AGENT-ORGANIZATION.md).
Contributions still require a new branch, pull request, and approval.

## Install

Requires **Python 3.11+**, pip, and a POSIX platform (tested on macOS; uses
descriptor-relative, no-follow file access available on macOS/Linux).
Git is optional. From this checkout:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
spec-consultant --help
```

For runtime-only installation, use `python -m pip install .` instead of the
editable/dev install. The only direct runtime dependency is `jsonschema`.
Install the package from a trusted checkout, not from code being assessed.
After dependencies are installed, assessment needs no network. Nothing is
published, pushed, or scheduled by this package.

## Assess repositories

Choose an output directory **outside every assessed root**:

```sh
spec-consultant assess /absolute/path/to/repo \
  --out /absolute/path/to/assessment-output

spec-consultant assess /absolute/path/to/rust-repo /absolute/path/to/c-library \
  --goal memory-safety --adoption no-production-changes \
  --max-candidates 3 --out /absolute/path/to/assessment-output
```

Outputs:

| File | Purpose |
|---|---|
| `assessment.json` | Canonical structured assessment; edit this for semantic enrichment |
| `report.md` | Evidence, scenario decisions/exclusions, sources, gaps, and limitations |
| `backlog.md` | Priorities, readiness, dependencies, acceptance criteria, required evidence |
| `orchestrator.md` | Self-contained agent handoff including the canonical assessment |

The CLI never modifies assessed roots. It rejects outputs inside roots, including
through symlink aliases. It only reads target files and invokes read-only Git
metadata commands; it never runs target builds/tests, installs target dependencies,
or runs proof tools. Proposed paths/commands are not execution evidence.

All initial recommendations are `static-provisional`, all outcomes `not-run`.
Ready tasks gather evidence. Implementation tasks remain blocked on inspection,
requirement approval, compatibility, and prerequisites. Owner approval is not
inferred from repository instructions or the presence of a test.

### Separate discovery, semantic enrichment, and rendering

```sh
spec-consultant profile /absolute/path/to/repo -o /outside/roots/profile.json
spec-consultant catalog --profile /outside/roots/profile.json
spec-consultant catalog --scenario kani-rust-slices
spec-consultant assess --profile /outside/roots/profile.json --out /outside/roots/assessment
spec-consultant schema assessment
```

An agent can then inspect the referenced source and requirements and edit
`assessment.json` (see the skill). Add project-specific properties, requirement
references, actual adoption constraints, trusted boundaries, uncertainty, and
priority rationale. Preserve deterministic matching evidence and exact catalog
assurance wording. Change `analysis` to `agent-reviewed` only after real inspection.
New assessments use canonical/profile format **v2**. A reviewed v2 assessment
records semantic `conclusions` with an explicit `represented`, `deferred`, or
`rejected` disposition and reason. Preserve property-level provenance, domains,
assumptions, exclusions, unknowns, relationships, and linked `work_item_ids`.
Every root and retained task needs a disposition. Represented `no-new-work`
conclusions have no tasks; `evidence-only` conclusions link only read-only work.
Remove replaced static pilots from executable work, recording why they were
discarded instead of silently losing them or their replacement.

`matches` remains immutable discovery evidence. Reviewed read-only investigation
can coexist with an excluded scenario; source and language checks still apply.
Blocked implementation against an excluded/unestablished scenario additionally
needs `review`: rationale, source references, included/excluded
`root-id:relative-path` files, configuration, and `compatibility: unknown`.
Included files cannot retain scenario hard exclusions. File isolation is a
reviewed claim, not a call graph or compatibility certificate; it never unblocks
implementation. Approval, requirement and dependency checks remain mandatory.

Honest noncatalog work uses null `scenario` and `scenario_version`, with
`tool: native-tests` / `method: testing` (harness scope), or
`tool: source-inspection` / `method: source-inspection` (evidence gathering only).
Use the validator's fixed non-proof assurance wording. These are not new curated
verifier scenarios. Consult `schema assessment` for the full structures.

If goals/adoption change, regenerate static matches with the corresponding options
and reconcile semantic work instead of manually changing the deterministic decisions.
Re-profile to include additional source/requirement files before citing them.

```sh
spec-consultant validate /outside/roots/assessment/assessment.json
spec-consultant freshness /outside/roots/assessment/assessment.json
spec-consultant render /outside/roots/assessment/assessment.json --out /outside/roots/assessment
```

Validation rejects malformed structures, missing/cyclic dependencies, invalid
source references, stale referenced hashes, inappropriate scopes, unsupported
catalog assurance claims, and unapproved ready implementation work. It retains
all deterministic scenario decisions, including exclusions. **Schema validity
does not validate recommendation correctness**, requirement legitimacy, or whether
a proposed tool will work. Recorded grants must be confirmed with the actual owner.
The execution agent records completed prerequisites/results separately; this
assessment format does not claim that any task has executed.

`freshness` re-scans using the original limits and compares content, Git identity
and dirty status, configurations, discovered dependencies, and exclusions. A commit
SHA alone is insufficient for dirty content. Newly added files can make an old
profile stale. Saved profiles are freshness-checked before assessment. Scans are
not atomic; stop/re-scan if content changes concurrently.
Legacy v1 assessments remain readable without rewriting their discovery evidence.
Freshness reports the profiling-policy change and requires re-profiling for a new
handoff; this alone does not mean the old source changed.

Exit codes: `0` success/unchanged, `1` freshness drift, `2` invalid input or
unavailable source. `validate --no-source-check` is an explicitly labeled archival
check, not permission to skip execution freshness checks.

### Discovery controls

Default limits are **250 inspected files/root, 256 KiB/file, 5,000 directory
entries/root, depth 20**, with at most three detailed candidate scenarios.
The canonical assessment records all limits and uninspected areas. To request
broader discovery explicitly:

```sh
spec-consultant assess /absolute/path/to/repo \
  --max-files 1000 --max-bytes 524288 --max-entries 20000 --max-depth 30 \
  --max-candidates 8 --out /outside/roots/broader-assessment
```

Limits bound discovery, not semantic coverage. Oversized, non-UTF-8, binary,
special, and symlink files are not inspected. A directory that cannot fit within
the entry budget is left entirely uninspected rather than selecting a
filesystem-order-dependent subset. Dependency/build/private directories and
secret-like filenames are skipped. This is path-based secret avoidance, **not
a guarantee of detecting secrets embedded in otherwise ordinary source files**.
No raw source excerpts are serialized. Nested Git repositories/submodules are
skipped unless selected as explicit roots. Git submodule contents, ignored/excluded
areas, code generation, conditional compilation, and target configurations may
remain uninspected. `.h` defaults to C; a C++ header's true context needs inspection.

`--goal` is repeatable: `memory-safety`, `arithmetic`, `functional-correctness`,
`state-invariants`, `progress`, `verified-source`. Multiple goals select their
union; omitted goals remain unresolved. `--adoption` is `unknown` (default),
`no-production-changes`, or `source-adaptation`. Adoption eligibility is never
approval to implement. Catalog retrieval accepts the same filters.

## Curated knowledge and assurance boundaries

Ten narrowly scoped scenarios cover Rust integer kernels, slices, and isolated
unsafe memory; Verus integer/sequence contracts; C/C++ buffers and bit operations;
TLA+ state safety/concurrency progress; and Dafny verified-source/code generation.
Entries contain versioned IDs, explicit signals/goals/exclusions, inspection
questions, alternatives, constraints, templates, primary-source URLs and check
dates, and exact assurance limits. Compatibility is explicitly unknown until the
target features and pinned release are inspected.

Rules require an applicable language **and all required heuristic patterns in
one source file**, plus goal/adoption compatibility. For Rust/C/C++ kernels,
required signals are grouped by lexically identified production function, not
combined across unrelated symbols. Comments, documentation examples and literals
are masked while preserving source lines. Benchmark/example paths and test/harness
functions do not seed production pilots. C/C++ `extern "C"` is recorded as linkage,
not an unavailable foreign implementation. Actual external calls, compilation
language and preprocessor configurations remain inspection obligations.
Root-wide FFI, concurrency,
assembly, or other scenario-specific blockers conservatively exclude a native
scenario until isolation is established. This is deliberately not a call graph.
Dependencies/configurations are evidence and inspection obligations, not assumed
compatible. No suitable entry / more information required are normal outcomes.
Scenario selection order favors small native harness pilots, then models, adapted
proof source, and opt-in replacement; it is a planning policy, **not an assurance
ranking**. Backlog priority is separate from readiness/confidence and must be
refined using actual project impact.

| Method | What the initial catalog proposes, not what assessment proves |
|---|---|
| Kani / CBMC | Harness-scoped bounded checks with explicit domains, models, enabled checks, and complete unwinding |
| Verus | Deductive contracts for adapted supported Rust, with trusted boundaries |
| TLC | Finite abstract model checks; implementation correspondence is separate |
| Dafny | Verification of Dafny source and possible generated-code integration; not arbitrary-language verification |

Tests, executable checks, workflow tools, model checking, deductive verification,
and proof assistants are distinct. All shipped scenarios are **documented**:
primary documentation was reviewed on **2026-11-05**. No proof tool was run to
reproduce them, and no recommendation accuracy was measured.

See [catalog contribution and evaluation](docs/CATALOG.md). There is no autonomous
research system, hosted service, frontend, vector database, or proprietary SDK.

## Install the Agent Skill

After installing the trusted package, copy the complete skill directory into the
skill location supported by your agent. For an agent discovering `.github/skills`:

```sh
mkdir -p /path/to/agent-workspace/.github/skills
cp -R .github/skills/proof-readiness /path/to/agent-workspace/.github/skills/
```

Do this **before** assessing that workspace, not as a modification during assessment.
The [skill](.github/skills/proof-readiness/SKILL.md) uses official Agent Skills YAML
frontmatter and an agent-neutral workflow: profile, retrieve local scenarios,
inspect source/tests/specs, propose contracts, validate, and render. Ask your agent:

> Use proof-readiness to assess `/absolute/repo`. Keep discovery bounded, detail at
> most three scenarios, and write outputs to `/outside/roots/assessment`. Do not
> execute or modify the target.

## Reproducible provisional example

From the package checkout after installation:

```sh
spec-consultant assess examples/rust-buffer \
  --goal memory-safety --adoption no-production-changes \
  --out assessment-output/example
spec-consultant validate assessment-output/example/assessment.json
spec-consultant freshness assessment-output/example/assessment.json
```

The Rust fixture has `prefix_sum`, indexed buffer access, and an existing test.
The slice-harness scenario is a provisional candidate. Source inspection should
resolve whether callers must guarantee `length <= buffer.len()` or whether the
API should reject longer inputs; the existing test does not decide that intent.
No Rust test, build, Kani harness, or proof is executed by these commands.
The tiny fixture is not a measured recommendation benchmark.
See [example interpretation](examples/README.md).

## Development

```sh
python -m pytest -q
ruff check .
ruff format --check .
python -m pip wheel --no-deps . --wheel-dir /tmp/spec-consultant-wheels
```

Fixtures cover matching and nonmatching cases, unsupported features, mixed-language
FFI, verification artifacts, dirty/non-Git roots, scan limits, unsafe paths,
out-of-root symlinks, freshness, invalid dependency graphs, and unsupported
assurance claims. Tests exercise the assessor, **not** the verification tools or
target examples. Generated local outputs and development environments are ignored.

The [repair evaluation](docs/REPAIR-EVALUATION.md) documents retained evaluator
failures, semantic dispositions, regression evidence and independent reproduction.

## License

Licensed under the [MIT License](LICENSE).
