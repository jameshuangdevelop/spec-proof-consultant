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
texts and Python's top-level license text are collected; missing distribution
texts stop the builder, and unavailable interpreter texts remain explicit
release gates. PyInstaller's GPL exception permits
generated applications subject to its terms, not a waiver of Python/native
dependency obligations.

### Native notices and provenance (partial, not release certification)

Before freezing, the builder discovers this interpreter's extension/framework
files and their Mach-O load paths, plus recorded rpds wheel members. It reads
only local data, never runs Homebrew/formula code, fetches licenses, or assumes
that all formula runtime dependencies are shipped. Resolved keg ancestors,
`INSTALL_RECEIPT.json` and matching `.brew/*.rb` identify local versions; full
local Python, mpdecimal, OpenSSL and liblzma texts are collected when available.
liblzma uses the local `COPYING` package explanation and `COPYING.0BSD`, not a
blanket GPL label inferred from xz's separately licensed scripts. The combined
`THIRD-PARTY-NOTICES.txt` is embedded in the frozen runtime and copied into the
installed skill ZIP. The rpds wheel SBOM is retained/hashed and embedded as data.

`native-notice-discovery.json` is embedded **candidate** evidence, not a claim
that every discovered file was collected. After freezing, `native-analysis.toc`
is parsed as literal data (not executed). `native-inventory.json` records **every**
actual BINARY/EXTENSION destination, source realpath/source SHA-256, component,
version, notice hashes, receipt/formula hashes and explicit status/gates. It is
bound to the final executable and Analysis hashes. When CArchive extraction
succeeds, a separate `final_member_sha256` hashes the actual collected bytes:
PyInstaller relocation/ad-hoc signing can change them from source bytes.
Unavailable final correspondence is explicitly unresolved, never silently
represented by the source hash.

The final inventory is an **external sidecar**, at the build output and in the
full installed skill ZIP, not inside the frozen executable. Match its
`binary_sha256` before use. `native-provenance-evidence/` retains content-hashed
local notice/receipt/formula/SBOM bytes in the output and ZIP for offline review.
Paths describe this build environment, not portable identities; use hashes.
Embedded `runtime-info` identifies pre-freeze discovery and explicitly points
to the external final inventory; it does not assert complete coverage.

Unknown origins (including other hosted-Python distributions), missing/empty
texts, missing origin records and post-discovery changes remain explicit
unresolved release gates, not CI failures for development artifacts merely
because a prefix/distribution differs. CPython's top PSF license is **not**
complete incorporated-code coverage: Mersenne Twister, select/kqueue, SipHash24,
dtoa, cfuhash, asyncio and other incorporated/static notices still need review.
OpenSSL upstream NOTICE presence/absence is not proven by a keg lacking NOTICE.
rpds's top MIT text and wheel SBOM do **not** close Rust transitive obligations:
archery, rpds, libc, pyo3, unicode-ident including Unicode-3.0, and
Cargo.lock/portable-atomic reconciliation remain unresolved. The SBOM's
`all_targets=true` is not proof of compiled inclusion. No static/transitive
completeness or legal certification is claimed.

Independent review must complete native/transitive coverage and
interpreter/library provenance before publication. Wheel and executable hashes are **not**
reproducible-build, legal-compliance or complete native-provenance certificates.
The builder records those unresolved release gates and defaults to refusing
release qualification even from a clean tree. `--development` makes working
evaluation artifacts only. macOS signing is PyInstaller **ad-hoc**, not Developer
ID signing or notarization; Gatekeeper/quarantine must never be disabled.
Distribution/version URLs, signatures, full platform qualification and owner
approval remain orchestrator release responsibilities.

The workflow retains manual `workflow_dispatch` and also runs on ordinary
`pull_request` events for relevant source, packaging, skill, workflow, example,
project metadata and license changes. It checks out the exact PR head, builds
unqualified macOS ARM64 evaluation artifacts, then runs `packaging/check_bundle.py`
against that build and trusted read-only `examples/rust-buffer`, with check output
under `RUNNER_TEMP`. Available build/check evidence is uploaded even on failure;
it is qualification evidence, not a public release. The workflow never tags,
releases, publishes packages or receives write permissions/secrets, and checkout
does not persist credentials. No installed automatic hooks, services or updater
are added.
