# Installation and updates

There are two independent pieces:

1. **Skill/plugin:** instructions for an existing agent. One canonical copy lives
   at `.github/skills/proof-readiness/SKILL.md`. The root's
   `.claude-plugin/plugin.json` points to that directory, and
   `.claude-plugin/marketplace.json` indexes the root plugin as
   `proof-readiness@spec-consultant`. There are no hooks, servers, scripts,
   automatic installers, or bundled orchestration agents in the plugin manifest.
2. **Runtime:** the offline Python `spec-consultant` CLI, installed separately.
   The plugin does not install it or grant permission to execute target code.

Start with [Get the skill](../README.md#get-the-skill) for per-client commands.
Install outside assessments; never copy files into a target during read-only
assessment. Avoid installing both the standalone skill and plugin in the same
client: duplicate discovery can produce conflicting instructions.

## Client routes and update controls

### Claude Code

In Claude Code:

```text
/plugin marketplace add jameshuangdevelop/spec-proof-consultant
/plugin install proof-readiness@spec-consultant
```

For deliberate updates:

```text
/plugin marketplace update spec-consultant
/plugin update proof-readiness@spec-consultant
```

Inspect the marketplace's auto-update control in `/plugin` rather than assuming
it is enabled. This is a third-party repository marketplace, **not membership in
`claude-plugins-official`**; official and third-party marketplace defaults can
differ. Review updates before enabling automatic uptake.

References: [plugin manifest and commands](https://code.claude.com/docs/en/plugins-reference),
[marketplaces and updates](https://code.claude.com/docs/en/plugin-marketplaces),
[marketplace schema](https://code.claude.com/docs/en/plugins/marketplace-reference).

### Codex

The current [Codex plugin documentation](https://developers.openai.com/plugins/build/plugins)
describes:

```sh
codex plugin marketplace add jameshuangdevelop/spec-proof-consultant
codex plugin add proof-readiness@spec-consultant
```

This client is unavailable here; the route is documented, not reproduced. Use
the installed client's plugin management controls and current documentation for
updates; this project configures no Codex auto-update policy.

If plugins are unavailable, a standalone installation via GitHub CLI is:

```sh
gh skill install jameshuangdevelop/spec-proof-consultant \
  .github/skills/proof-readiness/SKILL.md --agent codex --scope user
```

Use the `gh skill update` workflow below for that standalone route, not plugin
update commands. No Codex minimum version or universal plugin compatibility is
asserted.

### GitHub Copilot (CLI and VS Code)

Copilot CLI can install from the repository root without registering a marketplace:

```sh
copilot plugin install jameshuangdevelop/spec-proof-consultant
copilot plugin list
copilot plugin update proof-readiness
```

Or register the marketplace and install/update by its qualified name:

```sh
copilot plugin marketplace add jameshuangdevelop/spec-proof-consultant
copilot plugin install proof-readiness@spec-consultant
copilot plugin update proof-readiness@spec-consultant
```

Choose one route, not both. The explicit update commands fetch new content; this
repository does not configure automatic updates. CLI help does not document a
local filesystem path for `plugin install`; do not treat a local-path install as
tested. `--plugin-dir` is a separate session-local discovery mechanism.

For a standalone skill discoverable by Copilot CLI and VS Code:

```sh
gh skill install jameshuangdevelop/spec-proof-consultant \
  .github/skills/proof-readiness/SKILL.md --agent github-copilot --scope user
```

Reload/restart and check the client's skill list before use. VS Code also has its
own agent plugin UI/marketplace settings; CLI plugin installation does not
configure those. Follow the VS Code documentation if choosing its plugin route
instead of the standalone skill above. No VS Code executable was available for
an end-to-end check here.

References: [Copilot CLI plugins](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating),
[VS Code plugins](https://code.visualstudio.com/docs/agent-customization/agent-plugins).

### Gemini CLI (manual updates)

```sh
gemini skills install https://github.com/jameshuangdevelop/spec-proof-consultant.git \
  --path .github/skills/proof-readiness
```

The [Gemini skill documentation](https://geminicli.com/docs/cli/skills/) describes
this Git URL/subdirectory route; user scope is the default. It was not run here.
No automatic skill update is configured: review changes, then reinstall through
the installed client's removal/overwrite workflow. Do not silently overwrite
local customizations.

### Any other agent or editable files (manual updates)

From a trusted checkout:

```sh
mkdir -p /path/to/agent-workspace/.github/skills
cp -R .github/skills/proof-readiness /path/to/agent-workspace/.github/skills/
```

Replace the destination with your client's documented discovery location.
Do not assume every client searches `.github/skills`. The directory can instead
be opened as editable instructions when a client has no skill support. Keep the
whole directory together; it has no dependency on files outside the skill bundle.
When updating, review the new source, preserve local edits separately, remove the
old copy, and copy the new directory. No update tracking is provided by copying.

An optional external installer documents:

```sh
npx skills@latest add jameshuangdevelop/spec-proof-consultant --skill proof-readiness
```

This downloads/executes third-party tooling; it is **not required**, was not
installed or run here, and discovery against a published release is unverified.
See its [commands and update workflow](https://github.com/vercel-labs/skills/blob/main/docs/commands.md).
Review/trust that tooling independently. If discovery fails, use the exact
[canonical directory](https://github.com/jameshuangdevelop/spec-proof-consultant/tree/main/.github/skills/proof-readiness)
or GitHub CLI's exact `SKILL.md` path rather than assuming conventional directory
discovery.

## GitHub CLI standalone updates and pinning

GitHub CLI supports an exact path even outside conventional skill directories:

```sh
gh skill install jameshuangdevelop/spec-proof-consultant \
  .github/skills/proof-readiness/SKILL.md --agent codex --scope user
gh skill update proof-readiness --dry-run
gh skill update proof-readiness
```

Substitute `--agent github-copilot`, `claude-code`, or `gemini-cli` as appropriate.
See [`gh skill install`](https://cli.github.com/manual/gh_skill_install) and
[`gh skill update`](https://cli.github.com/manual/gh_skill_update), or your
installed CLI's help. `--pin COMMIT_SHA` pins a **remote Git ref**, not a skill
metadata version. Choose an actually reviewed commit containing the desired skill;
no release tag is assumed here. Pinned skills are skipped by updates unless
explicitly unpinned. `gh` injects source-tracking frontmatter; an installed copy
is therefore not byte-identical to source. Updates can replace local edits.
No scheduled updater is installed.

## Runtime requirements: why Python and POSIX?

The Agent Skills format imposes neither requirement. They come from this CLI:

- Python implements bounded offline scanning, catalog matching, JSON Schema
  validation and rendering. Python **3.11+** supplies `tomllib` in the standard
  library for TOML manifests. The only direct runtime dependency is
  `jsonschema`; this contribution does not change the Python minimum.
- The scanner uses descriptor-relative `os.open(..., dir_fd=...)`,
  `O_NOFOLLOW`, and `O_DIRECTORY` to reject symlinks and reduce path replacement
  races. These protections are not relaxed for distribution.
- macOS has been tested. Linux provides the relevant POSIX APIs but is not
  claimed tested by this distribution check. Native Windows is unsupported.
  WSL may supply a POSIX environment, but is an **untested workaround**, not a
  promise of native Windows support. Scans are still not atomic.

Install the runtime into a dedicated environment outside every assessed root:

```sh
python3.11 -m venv "$HOME/.venvs/spec-consultant"
"$HOME/.venvs/spec-consultant/bin/python" -m pip install \
  "git+https://github.com/jameshuangdevelop/spec-proof-consultant.git@9ce3702cb69a0944cb4db4d5b318cf118cf00509"
export PATH="$HOME/.venvs/spec-consultant/bin:$PATH"
spec-consultant --help
```

The immutable ref is an existing approved CLI revision, not a future release tag.
Git is needed by this install command; pip may download build dependencies and
`jsonschema`/its dependencies. Transitive dependencies are not locked, so this is
a source pin, not a fully reproducible environment. A virtual environment is not
an isolation boundary for untrusted code.

Alternatively use the environment's
`python -m pip install /absolute/path/to/trusted/checkout`. Do not use a system-wide
pip by default, or install from the target being assessed. Git is optional during
assessment; the CLI then lacks Git metadata where unavailable. Normal assessments
are offline once dependencies are installed.

If Python, required APIs, dependencies or the CLI are missing, **stop and report
the missing prerequisite**. Do not fabricate assessment output, bypass scanner
protections, or execute a target-provided replacement. Installation is not
automatic permission to execute or modify the target.

Skill/plugin updates and runtime updates are independent. To update the runtime,
review a new trusted revision and explicitly reinstall that ref into the same
dedicated environment. Skill metadata version `0.1.0` alone does not establish
runtime compatibility.

## Validation status and release checklist

This contribution supplies repository-local manifests and docs; remote plugin
commands only work **after these files are merged into the referenced remote**.
There is currently no GitHub release or PyPI/npm publication. The runtime command
above uses an already existing immutable revision; it does not depend on these
unmerged manifests.

Available CLI help was inspected with Copilot CLI **1.0.107** and GitHub CLI
**2.102.0**. With Copilot CLI, `copilot --plugin-dir /path/to/this/checkout plugin
list` discovered `proof-readiness (v0.1.0)` without invoking a model. This checks
local plugin discovery, not skill activation or remote installation.
Automated product tests check manifest consistency, a single canonical skill,
and relocation/local-link closure. Those checks do not certify client
installation, model behavior, or agent compliance. No remote installation or
external installer was run for this contribution. Claude Code, Codex, Gemini CLI
and VS Code were unavailable; their routes are documentation-based. No minimum
agent versions are invented.

Before public release or catalog submission:

- [ ] Independently evaluate this contribution and obtain PR approval/merge.
- [ ] Reproduce the remote install and update paths on each claimed client;
      record client versions, source revisions, settings, and discovered skills.
- [ ] Verify runtime/skill compatibility at the intended immutable release ref.
- [ ] Resolve the project's **license decision** before release/catalog listing.
      No license is selected by this contribution.
- [ ] Only then choose a release/tag and consider third-party catalog submission.
      Listing is deferred; a repository marketplace is not official catalog
      membership, automatic acceptance, or approval to publish.
