# Self-contained runtime (evaluation artifacts)

The canonical skill is `.github/skills/proof-readiness`. Build output copies it;
there is no second hand-maintained skill. A generated macOS ARM64 skill ZIP
contains the launcher, matching manifest, raw PyInstaller one-file console engine,
MIT license, third-party notices and build identity. Install the entire directory
outside **all** selected roots. No Python/uv prerequisite or PATH edits are needed
to use that artifact. Source CLI installation is still supported.

## Trust and consent

The installed launcher and manifest must come from a separately trusted,
reviewed distribution, never from an assessment target. The manifest grammar is
UTF-8 lines: `spec-runtime-v1`, comments beginning `#`, then
`platform|64-lowercase-hex-sha256|safe-asset-basename|immutable-https-url-or--`.
Currently only `macos-arm64` is implemented, with at most one entry. No shell
evaluation, “latest”, side-downloaded checksum, registry or release discovery.
The source manifest has no approved entries. Generated manifests pin the local
binary and have `-` for the URL; **nothing has been published**.

Invocation grammar:

```text
/absolute/skill/scripts/spec-consultant --root ROOT [--root ROOT ...]
  --cache /absolute/physical/private-cache
  [--from /absolute/approved-raw-file | --allow-download] prepare
/absolute/skill/scripts/spec-consultant --root ROOT --cache CACHE status
/absolute/skill/scripts/spec-consultant --root ROOT --cache CACHE run CLI-ARGS...
```

All options precede the operation. Explicit root declarations must be complete
before the bootloader runs; the engine additionally rejects assessment/profile
roots differing from those declarations. Supply the same complete list for saved
profiles/assessments. `--manifest` is for reviewed external fixtures only, never
target-provided trust. Environment runtime overrides are not trust anchors:
handoffs require a launcher hash embedded by the builder and external physical
installation paths. Move the installation only deliberately; regenerate handoffs
after a move. Frozen direct execution cannot generate durable handoffs; use the
launcher for assessments/rendering.

`prepare` verifies bundled/local bytes before writing. Downloads require the
explicit prior-consent flag and a reviewed immutable HTTPS URL. At most five
HTTPS-only redirects are allowed (for example, GitHub release assets redirecting
to a CDN); HTTP downgrades are forbidden. Curl configuration and inherited
environment are ignored, no credentials are supplied, and the final bytes must
match the reviewed manifest digest.
`status`/`run` have no network path. An absent, partial, symlinked or corrupt cache
fails closed, not a silent repair. Preparation uses private temp directories and
an atomic hard-link installation (concurrent preparation does not replace an
existing entry). Every run rechecks the digest, uses system tools via fixed
`/usr/bin:/bin`, ignores target HOME/TMPDIR and Python environment, and changes cwd
outside targets. The private cache is mode 700 and current-user-owned.
Root aliases are physically resolved; symlink/noncanonical storage paths are
rejected. Storage parents must already exist. Symlinks from a target to storage
are not followed by assessment. Selected root `/` necessarily has no external
storage and is rejected.

These are defensive checks, **not** a same-user tamper/race sandbox or isolation
for target execution. Declare roots honestly; do not invoke the launcher itself
through an untrusted shell/interpreter or inherited dynamic-loader injection.
Private temporary `_MEI` extraction is deleted after execution, not persisted in
handoff commands. Handoffs invoke the same absolute launcher/cache with quoted
roots; existing freshness/approval policy is unchanged.

## Build

Use a new trusted scratch venv outside the source checkout:

```sh
python3.11 -m venv /external/builder
/external/builder/bin/python -m pip install --require-hashes --only-binary=:all: \
  -r packaging/requirements-macos-arm64.lock
/external/builder/bin/python packaging/build.py --development \
  --output /external/new-build-directory
```

The output directory must not exist. The builder copies trusted inputs into an
external snapshot, installs the package there with no build isolation/dependency
resolution, then uses a static entrypoint and narrow data/metadata collection.
It never installs into the assessed/source checkout. The default refuses a dirty
source tree; `--development` explicitly permits it and records dirty status plus
snapshot file hashes. Development artifacts never claim release cleanliness.
The retained commands include stdout/stderr. `runtime-info` emits JSON with
interpreter/application/build identities, catalog/schema hashes and full notices.
Final binary/ZIP hashes are external in `artifact-manifest.json`, avoiding a
circular embedded self-hash.

The lock was resolved using pip for CPython 3.11 macOS ARM64 and pins exact wheel
hashes. `requirements.in` documents inputs; retain the pip resolver report when
updating the lock. Other platforms require their own reviewed lock and tests.
There is deliberately no Linux/Windows support claim or dependency installation
by the end-user launcher.

## Redistribution and qualification gates

MIT licensing is tightly coupled to artifact redistribution (same authorized
copyright/text intended by the unmerged licensing contribution); it does not
incorporate that contribution's other work. Full installed dependency license
texts and Python's license/third-party text are collected; missing distribution
or interpreter texts stop the builder. PyInstaller's GPL exception permits
generated applications subject to its terms, not a waiver of Python/native
dependency obligations.

`native-analysis.toc` preserves collected library paths. Independent review must
complete the native/transitive notice inventory and interpreter/library
provenance before publication. Wheel hashes and executable hashes are **not**
reproducible-build, legal-compliance or complete native-provenance certificates.
The builder records those unresolved release gates and defaults to refusing
release qualification even from a clean tree. `--development` makes working
evaluation artifacts only. macOS signing is PyInstaller **ad-hoc**, not Developer
ID signing or notarization; Gatekeeper/quarantine must never be disabled.
Distribution/version URLs, signatures, full platform qualification and owner
approval remain orchestrator release responsibilities.

The manual `workflow_dispatch` workflow builds unqualified macOS evaluation
artifacts only. It never tags, releases, publishes packages or receives write
permissions/secrets. No automatic hooks, services or updater are installed.
