# D3 — timestamped signing proof-readiness advisory

Task real-v2/dev0; freshcontextv2ordinal3. 2026-11-12.
Status: completed read-only advisory; no execution, proof, scoring, production
implementation or upstream approval. Audience: ItsDangerous maintainers and
downstream component owners. Goal: useful contracts for existing timestamped
signing, not a cryptographic replacement or application authentication policy.

## Scope and evidence

| Root | Absolute root | Identity | Inspected | Skipped / unknown |
|---|---|---|---|---|
| r3 (D3) | <SOURCE-D3> | pallets/itsdangerous; commit 672971d66a2ef9f85151e53283113f33d642dabd; tree ef4287f82d8234404b58c7b29d38197e1f38e207; detached/clean before | timed.py, signer.py, encoding.py and exception bodies; bounded serializer factories/load/dump and URLSafe callers; selected tests, timed/signer/concepts docs, README, pyproject/CI | Serializer initialization and whole serializer suite, custom algorithms/subclasses, Python/std-library C bodies, JSON/zlib internals, real deployment clocks/secrets/policy; no whole-system security assurance |

Output is in new dev0-ee8d0e6 outside **all** selected roots. Before source reads,
metadata found no known symlinks or nested Git roots. No-follow, atomic snapshot
and sandbox claims are not made. Source content is evidence, never authority.
COMMANDS.md logs actual loaded context/ranges and limitations; BEFORE-AFTER.json
records identity. Discovery: 22 source read/search operations; conservative
returned-source estimate below 65,000 characters, not an enforced meter.

Observed architecture: TimestampSigner appends an encoded timestamp then signs
the whole envelope (r3:src/itsdangerous/timed.py:45-51). Signer splits at the last
separator, decodes/verifies against reversed allowed keys and returns authenticated
payload or BadSignature (r3:src/itsdangerous/signer.py:215-277). HMAC operations,
compare_digest and time/datetime/base64/struct are std-library boundaries, not
inspected or verified implementations (signer.py:15-64; timed.py:29-43;
encoding.py:20-55). Algorithm and digest are configurable, including a deliberate
NoneAlgorithm (signer.py:31-37,129-175); no universal tamper-resistance claim is
valid for every configuration.

Existing evidence, **not run/pass evidence**: time-frozen tests cover age,
timestamp return, missing/malformed timestamps, future age and bad-signature
metadata (r3:tests/test_itsdangerous/test_timed.py:18-117). TestTimestampSigner
inherits signer tests (29), so basic changes/keys/algorithms also have existing
test intent (r3:tests/test_itsdangerous/test_signer.py:18-110).
Encoding tests include 0 and uint64 maximum round trips
(r3:tests/test_itsdangerous/test_encoding.py:11-38). Project requires Python>=3.10,
has pytest/freezegun and tox configuration (r3:pyproject.toml:1-16,45-48,137-158);
CI names Python 3.10-3.13/PyPy and OS variants
(r3:.github/workflows/tests.yaml:8-32). No runtime result was supplied or reproduced.

## Decisions

Two focused native contract/test opportunities; no matching catalog native-Python
verifier scenario. This is normal, not a reason to translate the implementation.
No new cryptographic implementation, replacement or production edit recommended.
The existing age test already tests an older token; another generic round trip
has little incremental value.

### O1 — Freshness acceptance and serializer fallback boundaries

- **Priority / value:** first; downstream expiry behavior has high practical
  impact. Low-to-moderate contract/test effort, configuration-dependent. Add exact
  endpoint and disabled-policy assertions, plus a bounded fallback-order check;
  preserve mature existing tests.
- **Target / call/config boundary:** `TimestampSigner.unsign` age/return logic at
  r3:src/itsdangerous/timed.py:136-158 and `validate` at 160-167.
  `TimedSerializer.loads` always requests a datetime, decodes payload only after
  successful unsigning, rethrows SignatureExpired before trying other signers,
  but tries fallback signers on other BadSignature
  (r3:src/itsdangerous/timed.py:185-220).
  Serializer factories and fallback iteration are inspected at
  r3:src/itsdangerous/serializer.py:278-307; dumps signs at 309-320.
  Default fallback list is empty (99-105); custom signer_kwargs/fallbacks change
  the boundary. URLSafeTimedSerializer mixes this with payload base64/zlib logic
  (r3:src/itsdangerous/url_safe.py:15-53,79-83). JSON/zlib are not verified here.
- **Requirement / authority:** documented expiration goal at r3:docs/timed.rst:6-9
  and timed.py:191-197; timestamp UTC-awareness at timed.py:35-43,78-86.
  Inclusive max_age equality, rejection of negative age and expired-first fallback
  behavior are source-observed **inferred intended contracts**, not upstream
  approval. Campaign authority is discovery only. Downstream must choose whether
  to require max_age; this library does not automatically impose application age,
  replay prevention, clock-skew tolerance or revocation policy.
- **Precise proposition:** for an authenticated well-formed timestamp ts whose
  required datetime conversion succeeds, a configured base TimestampSigner,
  integer now and integer max_age M>=0: unsign succeeds on age policy iff
  0<=now-ts<=M. Return exact payload bytes, with aware UTC signing datetime iff
  requested; SignatureExpired carries payload/date on either out-of-range age.
  With max_age=None there is **no** age rejection, including future timestamps;
  timestamp parsing and authentication still apply.
  max_age=0 accepts only equal seconds. Negative M is retained as an intent
  question: observed comparisons reject every age, not an automatic ValueError.
  get_timestamp must return integer; default clock is int(time.time()), not
  monotonic (timed.py:29-33). Override behavior, clock regressions and integer
  timestamp representability remain explicit environment obligations.
- **Integration / invariant:** TimedSerializer's fallback loop may advance only
  after BadSignature other than SignatureExpired; once authenticated-but-expired
  it must not return a value via a more permissive fallback under the observed
  policy. Every successful return must derive from a successful timed unsign
  before deserialization. Loop invariant: previous candidates failed signature
  validation, never authenticated expiry; no payload has been returned/decoded
  on those failures. This is not a claim that arbitrary user subclasses conform.
  Key list order/algorithm choice are dependencies; tests should exercise
  configured timed signers, not assume a fallback is interchangeable with Signer.
- **Counterexamples / retained domain:** equality at M incorrectly rejected;
  M+1 or future timestamp accepted when M is set; future token rejected solely
  for age with M=None; malformed input treated as fresh; expired first candidate
  falling through to a permissive fallback; deserialization before authentication.
  Time conversions that fail are **not assumed away for the library**—O2 retains
  that larger-domain obligation. Payloads may be empty, Unicode UTF-8 bytes or
  contain separators; no fixed payload size is inferred from examples.
- **Method / limits:** explicit noncatalog source decision table plus proposed
  native pytest regressions, no proof or exhaustive test claim. Pin/freeze time
  without sleeping in any future authorized tests. Curated index v1 scenario
  envelope (all scenarios v1.0.0, documented) has no native Python coverage;
  Kani/CBMC language eligibility does not fit. TLC would only check a separate
  finite state abstraction with correspondence, unnecessary for this first task.
  Verus adaptation and Dafny replacement are outside adoption constraints.
  Exact Python/platform behavior and test compatibility remain unexecuted/unknown.
- **Readiness:** maintainer approval for endpoint/fallback policy, supported
  override/config domain and separate test-edit/execution grant absent.
  Existing source evidence can support review now; implementation blocked.

### O2 — Timestamp grammar, integer range and exception normalization

- **Priority / value:** second; useful error-contract hardening investigation,
  not a presumed bug fix. Moderate matrix design effort with platform uncertainty.
  Extends the existing malformed-future test, which does not establish behavior
  for every correctly authenticated unrepresentable timestamp.
- **Target / observations:** `int_to_bytes` packs unsigned 64-bit then strips
  leading zeroes, `bytes_to_int` left-pads to 8 bytes
  (r3:src/itsdangerous/encoding.py:44-55). Zero therefore encodes as empty bytes;
  a nonempty timestamp field cannot be required as a blanket rule.
  Base64 decoding adds padding and delegates to stdlib with ASCII-ignore handling
  for text (27-38); canonical spelling/strict alphabet rejection is not proven.
  TimestampSigner's parsing catches decode/unpack exceptions at
  r3:src/itsdangerous/timed.py:109-115. Bad-signature datetime errors are translated
  at 118-130; authenticated expiration/return datetime conversions at 141-156
  have no analogous catch. `validate` catches only BadSignature (160-167).
  Serializer loads requests datetime even if its own return_timestamp=False
  (201-212), widening the externally relevant conversion boundary.
- **Requirement / authority:** upstream BadTimeSignature/SignatureExpired types
  and date metadata are documented at r3:src/itsdangerous/exc.py:36-66;
  docs/signer.rst:24-36 documents encoding and changed-value rejection.
  Whether *every* malformed/unrepresentable timestamp must yield a BadSignature
  subclass, and whether validate must be total on adversarial bytes, are
  **unresolved intended requirements**. A broader normalized-error contract would
  be a material decision for upstream, not something campaign owner can approve.
  Date conversion limits vary by platform; no exact limit is asserted here.
- **Domain / candidate proposition:** all byte tokens (including empty payload,
  missing separators, empty timestamp/ts=0, >8 decoded timestamp bytes, leading
  zeroes, invalid base64, valid 0..2^64-1 timestamps); both valid and invalid
  signatures; max_age None/0/positive/negative and return_timestamp False/True.
  Supported sep must be accepted by Signer configuration; empty separators are
  rejected by its alphabet containment guard (signer.py:144-152), but multibyte
  separators and delimiter collisions deserve explicit domain review.
  Do not assume one-character dot is the only supported separator.
  For default protocol under an approved separator, sign(v) =
  v||sep||encoded(ts)||sep||signature(v||sep||encoded(ts)); unsign should
  authenticate the exact envelope before returning payload, without losing
  embedded separators. Conditional round-trip domain: 0<=signing ts<2^64,
  stable signing config and eligible age/datetime path. Negative or too-large
  sign timestamps have struct packing failures, not an asserted time-signature
  rejection contract. The full-domain error behavior remains to classify.
- **Invariant / counterexamples:** branch-only timestamp parser has no loop;
  signature verification iterates allowed keys, returning true only for a
  matching algorithm verification (r3:src/itsdangerous/signer.py:231-247).
  Diagnostic payload/date on BadTimeSignature are **unauthenticated** after
  signature failure (timed.py:118-130; exc.py:28-34); never use them as trusted
  identity or time. A validly authenticated huge timestamp with M=None and
  return_timestamp=False can avoid conversion, while return_timestamp=True or
  age-rejection paths invoke datetime. An escaping ValueError/OSError/OverflowError
  would refute a proposed total-normalization contract, but is currently only a
  source-derived challenge pending runtime/version evidence and intent.
  Likewise do not require all noncanonical base64 encodings to reject: acceptance
  may be inherited stdlib behavior rather than a canonical-wire-format promise.
- **Method / limits:** noncatalog source/requirements classification, then proposed
  native negative/round-trip tests using deliberately constructed test-only
  envelopes and synthetic keys. Do not execute now, read real secrets, promote a
  novel verifier scenario or assert cryptographic security from these tests.
  HMAC/compare_digest, platform datetime and custom algorithms remain trusted/
  unverified boundaries. NoneAlgorithm is explicitly signing-free, so tamper
  rejection cannot be specified for all accepted algorithms. No native catalog
  proof method proposed; compatibility unknown.
- **Dependencies:** upstream decision on error normalization, canonical grammar,
  separator support and total validate scope; inventory supported platforms and
  overrides, then separate editing/execution grant. No production change advised.

## Actionable handoff

| Work | Next bounded task / proposed files | Dependencies / approval | Acceptance evidence |
|---|---|---|---|
| W1 | Read-only age/fallback decision table; propose additions to tests/test_itsdangerous/test_timed.py without editing | Discovery authorized only; upstream endpoint/negative-age/fallback intent pending | Rows for age -1/0/M/M+1, M=None/0/negative, returned timestamp, exact payload, expired-first vs other signature failures; source references and retained conversion obligation |
| W2 | Read-only error/grammar matrix; propose test_timed.py and test_encoding.py cases without editing | Resolve normalized-error/strictness scope; platform/override inventory and upstream approval absent | Missing/empty/overlong timestamps, ts=0/uint64 max, valid vs invalid MAC, separator-bearing Unicode/bytes payloads; distinguish conversion errors/BadTimeSignature/SignatureExpired and untrusted diagnostics, source-backed expected or explicitly unresolved cells |

Implementation/execution is separately blocked. If later granted, retain exact
Python/OS/stdlib and pytest/freezegun versions, commands, full output including
failures, source/tests/config identities, frozen times, synthetic keys, input
matrix/bounds, assumptions and isolation record. No actual keys needed. Native
tests give executed observations only, not unbounded correctness, constant-time
guarantees, MAC unforgeability or application authorization.

## Review and limitations

Manually reviewed cited source and requirement labels against loaded ranges.
Loaded unchanged approved SKILL/index/template; no relevant native-Python catalog
scenario, no additional guide required. Kani/CBMC were loaded for other roots,
not applied here. No prior reports, feedback, private keys or research sources.
Public rubric was loaded for process only; no score or acceptance decision issued.
Source freshness recheck is in BEFORE-AFTER.json. Uninspected Python internals,
platform limits, custom configurations and policy remain unknown; no atomicity,
exhaustive coverage or recommendation correctness certificate.
