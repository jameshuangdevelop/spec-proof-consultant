# Install the Agent Skill

Use your existing agent. The core is offline Markdown guidance: **no engine,
Python, Node.js, new model API, or runtime dependency is required**. Client tools
are needed only for the route you choose; online installers need network access
at installation/update time, not during assessment.

Every route must retain the whole `.github/skills/proof-readiness` folder:
`SKILL.md`, six `references/*.md`, `templates/assessment.md`,
`examples/assessments.md`, and `LICENSE` (ten files). Its license is an exact copy
of the root MIT license. Do not copy only `SKILL.md`.

**Availability:** remote examples target `jameshuangdevelop/spec-proof-consultant`
after this installation change is merged. Earlier revisions lack the bundled
license and plugin manifests. No release, official listing, or client activation
is implied. Review the selected revision and installed contents; if the remote
version is older, use a reviewed checkout containing all ten files.

## Claude Code

Requires a Claude Code version supporting plugins and custom skill directories:

```text
/plugin marketplace add jameshuangdevelop/spec-proof-consultant
/plugin install proof-readiness@spec-proof-consultant
/proof-readiness:proof-readiness
```

This adds this repository's own marketplace, not an official catalog entry.
The minimal plugin points to the single canonical `.github/skills/` container;
it adds no hooks, servers, executables, or duplicate skill tree.

Custom marketplace automatic updates are off by default. To update manually:

```sh
claude plugin update proof-readiness@spec-proof-consultant
```

Plugin maintainers must bump the plugin version for changes to reach users
reliably. Local skill edits are not an update strategy. As a plugin-free fallback,
copy the whole folder to `~/.claude/skills/proof-readiness` (personal) or
`.claude/skills/proof-readiness` (project), then invoke `/proof-readiness`
without the plugin namespace. Avoid installing both forms simultaneously.

## GitHub Copilot

Requires GitHub CLI with `gh skill` support (help checked with `gh` 2.102.0) and
a Copilot client supporting Agent Skills:

```sh
gh skill install jameshuangdevelop/spec-proof-consultant proof-readiness --allow-hidden-dirs --agent github-copilot --scope user
```

The hidden-directory flag is needed for discovery under `.github`. Selection by
skill name avoids relying on hidden exact-path selection behavior. User scope
places the copy under `~/.copilot/skills`. In Copilot CLI, use `/skills reload`,
then `/skills info proof-readiness` and `/proof-readiness`. For supported VS Code
Copilot versions, start a fresh chat and check skill discovery; behavior is
version-dependent. Native project placement is `.github/skills/proof-readiness`.

Without a pin, `gh` selects the latest tagged release, falling back to default
branch HEAD. Confirm that selection includes all ten files; it may not be the
latest merged code. For reproducibility, add `--pin` followed by a reviewed tag or
full commit SHA containing this change. Do not treat an unreviewed PR SHA as an
approved release; `main` is not documented as a supported pin value.

Manual update:

```sh
gh skill update proof-readiness
```

Pinned installs are skipped by updates; changing the pin or explicitly unpinning
is a separate trust decision. `gh` adds source-tracking frontmatter, so installed
`SKILL.md` need not be byte-identical to source. Preserve local edits first.
If `gh skill` is unavailable, use whole-folder copying instead.

## Codex

The simplest route needs no installer: copy the whole folder from a reviewed
checkout or repository ZIP to `~/.agents/skills/proof-readiness` (personal) or
`.agents/skills/proof-readiness` (project). Create the parent; the destination
skill folder should not already exist. Check `/skills`, then use
`$proof-readiness`. Local discovery/refresh is not an upstream update.

Optional **third-party** convenience route, only if you choose to run npm code
and already have Node.js **22.20.0+** and `npx`:

```sh
DO_NOT_TRACK=1 npx skills@1.8.1 add jameshuangdevelop/spec-proof-consultant --skill proof-readiness --agent codex --global --copy
```

This pins the installer version, not the skill revision. `--copy` installs all
assets rather than a symlink; `DO_NOT_TRACK=1` disables installer telemetry.
Review the installer as well as the skill before running it. Manual update for
this route (preserve local edits first):

```sh
DO_NOT_TRACK=1 npx skills@1.8.1 update proof-readiness --global
```

Do not install or upgrade Node.js just to use the core skill; whole-folder
copying remains an alternative.

## Gemini CLI

Requires a Gemini CLI version supporting Agent Skills:

```sh
gemini skills install https://github.com/jameshuangdevelop/spec-proof-consultant.git --path .github/skills/proof-readiness --scope user
```

The copy goes under `~/.gemini/skills`; project placement is
`.gemini/skills/proof-readiness`. Use `/skills reload` and `/skills list`, then ask
Gemini to use `proof-readiness`. Review and accept activation only when intended;
do not bypass consent.

Repeat the install command to update. This replaces the installed snapshot:
local edits and destination-only files can be lost. Save them separately first.
Reloading skills does not fetch upstream changes.

## Other / editable

Use a trusted checkout or download the repository ZIP from GitHub. Copy the
**entire** `.github/skills/proof-readiness` folder, including its `LICENSE`, to
your client's supported location. A file manager works on any supported platform;
the [README](../README.md#get-the-skill) also shows an optional POSIX copy command.
Do not copy into an existing destination: that can nest folders or leave stale
assets. Check for the ten files and working references, template, and examples.

For manual updates, review a new source revision, save local edits elsewhere,
and replace the installed folder completely. Pulling a source clone does **not**
update an independent installed copy. Keep editable variants separate.

## Trust and verification limits

Review instructions and source before installing or updating. Install only this
reviewed skill and retain its MIT notice. Installation grants no permission to
execute assessed code, run proof tools, modify targets, browse during assessment,
or transmit private code. Your existing agent's data policies still apply;
offline guidance is not a promise of an offline model or an enforced sandbox.

Repository tests check relocated asset/reference closure, license retention, and
manifest paths without the Python engine. They do not prove external installer
behavior or client activation. The commands above are documentation-grounded;
external client install/update/activation runs were **not executed** for this
implementation. Check discovery in your own supported client before assessment.

Primary references (research checked **2026-11-12 UTC**):

- [Claude plugin manifest and custom skills](https://code.claude.com/docs/en/plugins-reference)
  and [marketplace updates](https://code.claude.com/docs/en/plugins/host-marketplace.md#keep-users-up-to-date).
- [GitHub CLI install](https://cli.github.com/manual/gh_skill_install),
  [update](https://cli.github.com/manual/gh_skill_update), and
  [Copilot Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills).
- [Codex skill locations](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills);
  optional third-party [skills installer source at the researched revision](https://github.com/vercel-labs/skills/tree/e781cb4d07433dfe1d19e924ed45cc61738c55ec).
- [Gemini CLI skills installation, discovery, and consent](https://geminicli.com/docs/cli/skills/).
