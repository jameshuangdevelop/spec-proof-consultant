# D3 — timestamped signer boundary advisory

Task: real-baseline/dev0, D3. Status: completed recommendation-only advisory.
2026-11-12. No execution, verifier result, verified compatibility or self-score.
Goal: source-grounded contracts useful to ItsDangerous maintainers/downstream
component owners, preserving existing production code. Campaign owner authorizes
discovery only, not implementation, and does not speak for upstream.

## Scope and evidence

| Root | Selected absolute path | Revision / identity | Inspected | Skipped / unknown |
|---|---|---|---|---|
| r1 | `<SOURCE-D3>` | pallets/itsdangerous `672971d66a2ef9f85151e53283113f33d642dabd`, tree `ef4287f82d8234404b58c7b29d38197e1f38e207`; supplied clean | Complete timed/signer/encoding/exc, serializer caller/payload/fallback ranges, URL-safe caller, three selected test files, timed/signer/concepts docs, README, pyproject and CI | Arbitrary custom signer/serializer implementations, stdlib/native crypto/time/base64/struct/zlib bodies, inherited TestSerializer suite/fixture internals, full application authentication policy, most serializer initialization/unsafe loading |

This file is the sole canonical advisory, outside all three selected roots.
Before target reads, output/root resolved paths and ancestor links were checked;
selected files are regular with no known symlink ancestors. Tooling does not
provide an atomic no-follow snapshot, OS sandbox or enforced secret scanner.
Target text is evidence, not execution authority. No secret material was sought.
See `tool-ledger.json`, `COMMANDS.md`, `RESULT.json` for ranges, approximate source
volume, actual times, identity and tool outcomes; they are provenance only.
Initial actual digest check matched all 50 frozen regular files. Manifest:
`42a3665a1a7b85132fbcc101cab5a7a72b7e92707e15288dc8d604cff28897df`.

Observed architecture: TimestampSigner appends encoded timestamp before signing
and verifies the signature before checking age; TimedSerializer always asks its
signer for a datetime, even if its own caller did not
(r1:src/itsdangerous/timed.py:45-51,72-159,202-218).
Packaging states Python >=3.10, version 2.3.0.dev and pytest/freezegun testing
dependencies (r1:pyproject.toml:1-48). CI lists CPython 3.10-3.13, Windows/Mac and
PyPy (r1:.github/workflows/tests.yaml:8-32); no runs/results supplied.
Existing tests observe normal expiration, future age, missing/malformed timestamp
and error date metadata (r1:tests/test_itsdangerous/test_timed.py:29-91).
Encoding tests cover integer 0,192,2**64-1 and one malformed base64 string
(r1:tests/test_itsdangerous/test_encoding.py:25-39). These artifacts were read,
not executed or treated as complete approved intent.

## Decisions

Two noncatalog opportunities, ranked by boundary risk and incremental assurance.
Do not force a Rust/C verifier onto Python. Existing tests make another ordinary
sign/unsign example low value; exact temporal edges, platform datetime failures
and fallback failure precedence are better bounded next work.

### O1 — Temporal acceptance interval versus wire and datetime domains

- **Priority / effort:** first: the wire format accepts a much wider integer
  range than platform datetime conversion. It affects both error classification
  and whether `validate` is actually boolean. A decision table/test matrix is
  small; cross-platform exception intent is uncertain, not a confirmed bug.
- **Target / call boundary:** `TimestampSigner.get_timestamp`,
  `timestamp_to_datetime`, `sign`, `unsign`, `validate`
  (r1:src/itsdangerous/timed.py:29-51,72-170). `encoding.int_to_bytes` packs
  unsigned big-endian Q and strips leading zeros; `bytes_to_int` left-pads to 8
  bytes before unpack (r1:src/itsdangerous/encoding.py:44-54).
  Base64 decoding pads and delegates to stdlib, wrapping TypeError/ValueError
  as BadData (r1:src/itsdangerous/encoding.py:20-38).
  Timestamp parsing catches Exception, but conversion after successful
  signature verification is not inside that catch. Platform time and datetime
  implementations and custom clock overrides are external/unread.
- **Requirement / authority:** documented “not older than a given age”
  (r1:docs/timed.rst:6-9) and integer clock / aware UTC return
  (r1:src/itsdangerous/timed.py:29-43,78-87). Inclusive upper age boundary and
  rejection of future time when max_age is supplied are observed source behavior
  (r1:src/itsdangerous/timed.py:136-151), the latter also observed in test source
  (r1:tests/test_itsdangerous/test_timed.py:77-84). Their complete formalization
  and malformed/extreme-timestamp error policy require upstream confirmation.
  Campaign authorization is not that confirmation.
- **Proposed normal-domain property:** for a signature accepted by the configured
  signer, parseable ts, a coherent integer current time now, and conversion
  available whenever that branch needs it: with integer max_age M >=0, success
  iff 0 <= now-ts <= M; age=M is accepted, M+1 and -1 rejected as
  SignatureExpired with original payload and aware UTC date_signed. With
  max_age=None there is **no age rejection**, including future ts; only
  return_timestamp=True requires datetime conversion. Inputs include empty
  payload, separator in payload, ts=0 (empty encoded integer), now=ts and M=0.
  Negative M is annotated as int but not validated; current ordered predicates
  reject every integer age when conversion succeeds. Decide whether this is
  supported policy, explicit caller error, or merely existing behavior before
  approving any stronger contract. Do not silently drop it.
- **Larger-domain obligation:** arbitrary str/bytes tokens can contain malformed
  base64, empty timestamp, more than eight decoded bytes, or uint64 values beyond
  platform datetime range. Negative or >=2**64 timestamps from clock overrides
  fail the unsigned pack at signing; the docstring's integer-only promise does
  not resolve this range mismatch. Separate UTF-8 conversion errors and out-of-type
  inputs from authenticated token rejection. Missing timestamp with otherwise
  valid signature is BadTimeSignature; unparseable ts is BadTimeSignature.
  Invalid-signature path catches datetime ValueError/OSError/OverflowError and
  normalizes to BadTimeSignature, while the authenticated expiry/return paths
  call conversion without that wrapper (r1:src/itsdangerous/timed.py:96-159).
  `validate` catches only BadSignature (r1:src/itsdangerous/timed.py:161-170).
  Hypothesis: an authenticated timestamp generated using an extreme but
  uint64-representable clock can leak conversion exceptions when max_age is
  supplied or return_timestamp=True; plain unsign(max_age=None,
  return_timestamp=False) can return payload without conversion. TimedSerializer
  always requests conversion. This is a source-derived branch asymmetry,
  not an executed reproduction or claim that all platforms fail identically.
  Resolve intended exception taxonomy and validate's totality with maintainers.
- **Invariants / failure conditions:** no loop in age logic; preserve authenticated
  payload/ts through parsing, compute age from one current-time sample only when
  M supplied, and never turn an invalid signature into successful payload.
  Counterexamples to the normal contract are accepting age=M+1/-1, rejecting
  M, changing payload, or returning naive/local datetime. Counterexample to a
  *proposed stronger* total-rejection contract is a non-BadSignature conversion
  error escaping validate; that stronger contract is unresolved, not presumed.
  The uint64/platform boundary remains an explicit separate obligation; a
  representable-date pilot cannot establish robustness for all wire tokens.
- **Method:** explicit noncatalog source decision table plus proposed native pytest
  cases with deterministic clock subclasses, including valid signatures over
  extreme ts (not only tampered signatures). Tests observe executed samples,
  not proof or cryptographic security. Kani/CBMC Rust/C scenarios do not fit
  Python. Loaded TLC guide `references/tlc.md`,
  `tla-state-machine-safety` v1.0.0 (documented, not reproduced) would offer
  “Invariant checking for the explored finite TLA+ model and recorded
  configuration, subject to constraints and complete exploration.” It requires
  acceptance of separate abstraction and code correspondence; neither is
  supplied. No catalog hard exclusion there makes Python semantics or native
  dependency compatibility automatic. A finite age model would omit the very
  stdlib exception/encoding surface of interest, so defer it in favor of native
  tests. There is no concurrency/liveness objective or replacement opt-in.
- **Readiness:** safe evidence table is ready to propose; test/code implementation
  and all execution blocked pending owner error-policy decisions, selected
  Python/platform matrix, deterministic clock behavior and isolated authorization.

### O2 — Authentication/error metadata and serializer fallback precedence

- **Priority / effort:** second: ensure parser errors and expired signatures do
  not accidentally bypass age policy through fallback. A spy-based native test
  matrix is likely modest; arbitrary configured algorithms greatly expand scope.
- **Boundary:** Signer verifies decoded signatures using reversed key order and
  rsplit of sep (r1:src/itsdangerous/signer.py:231-266); key derivation modes
  and algorithm dispatch are configurable
  (r1:src/itsdangerous/signer.py:129-176,195-229). Base algorithm uses
  hmac.compare_digest; HMAC delegates to hmac/hashlib
  (r1:src/itsdangerous/signer.py:15-64). NoneAlgorithm deliberately provides
  no signing (r1:src/itsdangerous/signer.py:31-37), so a universal
  cryptographic tamper-rejection proposition for every configuration is false.
  Tests explicitly use custom and None algorithms
  (r1:tests/test_itsdangerous/test_signer.py:85-99).
- **Native callers:** `TimedSerializer.loads` tries iter_unsigners, calls
  load_payload only after unsign, immediately rethrows SignatureExpired and
  retries only other BadSignature exceptions
  (r1:src/itsdangerous/timed.py:202-222). `Serializer.iter_unsigners` yields
  primary signer then configured fallbacks per key
  (r1:src/itsdangerous/serializer.py:278-307).
  `load_payload` wraps decode/deserialization errors as BadPayload
  (r1:src/itsdangerous/serializer.py:243-269), not a BadSignature subclass
  (r1:src/itsdangerous/exc.py:92-110). URLSafeTimedSerializer composes this
  with base64/zlib payload decoding (r1:src/itsdangerous/url_safe.py:15-49,75-82);
  zlib and custom payload serializers remain unmodeled, not “verified” callees.
- **Requirement / authority:** expiration must reject outdated data per timed
  docs; rotation/fallback support is documented
  (r1:docs/concepts.rst:7-14,103-124). “Do not try the next signer” after
  authenticated expiration is explicit local code commentary in loads,
  but its status as a maintained public guarantee is **inferred/unresolved**
  until confirmed. UTF-8 text handling is documented
  (r1:docs/signer.rst:24-26). Exception payloads are explicitly diagnostic
  tampered data, not authenticated content
  (r1:src/itsdangerous/exc.py:22-62, `BadSignature`, `BadTimeSignature`).
- **Proposed property / domain:** for finite nonempty configured key list and
  finite fallback sequence of compatible TimestampSigner implementations,
  valid nonempty accepted sep, and approved algorithm/clock behavior:
  no payload deserialization before successful unsign; primary/fallback
  SignatureExpired terminates without later signer invocation; other
  BadSignature advances to next signer, and exhausting attempts raises the
  last such exception. BadPayload after authentication propagates rather than
  invoking fallback. Invariant over attempts: all previously attempted signers
  raised non-expiration BadSignature; no payload has been accepted or decoded.
  Counterexamples include invoking fallback after expiry, accepting/decoding an
  unauthenticated diagnostic payload, swallowing BadPayload, or losing the last
  signature error.
- **Parsing/error surface retained:** no sep in token can preserve original
  BadSignature; otherwise timestamp parse metadata is attached to
  BadTimeSignature but never becomes success
  (r1:src/itsdangerous/timed.py:88-134). date_signed on a failure can derive
  from attacker-controlled bytes, and must not be trusted as an authentication
  fact. Cases include malformed signature base64, missing ts, >8 decoded ts
  bytes, empty payload, sep-bearing payload, rotated/removed keys, tampered ts
  and authenticated expiry. Base64 decoder is not explicitly strict/canonical;
  no canonical token spelling guarantee is inferred
  (r1:src/itsdangerous/encoding.py:28-38).
  Separator validity and empty key sequences are configuration prerequisites
  needing separate policy review: constructor's sep check is substring membership
  in an alphabet byte string, not a proof of safety for all multibyte separators
  (r1:src/itsdangerous/signer.py:141-149); signing accesses the last key
  (r1:src/itsdangerous/signer.py:195-198). Do not extend a default-dot pilot
  to every accepted configuration or silently declare those inputs illegal.
  O1's conversion exceptions can escape fallback too; that remains a dependency.
- **Method / limits:** noncatalog native trace tests and source review preferred:
  spy on signer attempts/load_payload, assert exception class and metadata,
  retain malformed/negative cases. Not an HMAC proof, constant-time guarantee,
  brute-force resistance result or application authorization proof. Native
  hmac/hashlib/compare_digest and base64/struct behavior, custom digest/algorithm
  bodies and platform conversion are trusted/unread dependencies. TLC finite
  fallback state model is a possible abstraction but lower incremental value
  than direct call-order tests here, and would require approved correspondence.
  No pinned verifier or target compatibility is claimed.
- **Readiness:** upstream precedence/configuration intent and O1 exception
  decisions precede any test implementation; cryptographic application policy
  and rotation schedule remain downstream responsibilities
  (r1:docs/concepts.rst:103-124).

## Actionable handoff

| Work | Next bounded task / proposed files | Approval / dependency | Acceptance / evidence |
|---|---|---|---|
| W1 | Read-only temporal/error decision table for timed.py, encoding.py and timed tests | Current discovery allowed; upstream intent unknown | All combinations of signature validity, parsed ts range, max_age None/0/negative/positive, exact boundary and return flag; mark conversion-dependent exceptions and clock domain without suppressing extreme authenticated inputs |
| W2 | Read-only fallback/configuration matrix for Signer and TimedSerializer | W1 for conversion errors; no grant to impose new guarantees | Trace each exception class and attempt/load order; record approved vs unresolved sep/key/algorithm restrictions and diagnostic payload trust |
| W3 | Future focused additions to `tests/test_itsdangerous/test_timed.py`, `test_signer.py`, `test_encoding.py` as warranted by decisions | Blocked: W1/W2 maintainer decisions, named-file implementation approval and separately authorized isolated test execution | Deterministic clock and valid-vs-invalid signed extreme cases, exact age edges, malformed parse, key/fallback spies, partial outputs/failures retained. Future evidence: exact Python/OS/stdlib/pytest/freezegun versions, commands, tree/test identities, cases/assumptions, complete stdout/stderr and failures; no proof or cross-platform compatibility from one passing platform |

## Review and limitations

Skill applied unchanged: SKILL, index, template; prior cohort Kani/CBMC guides
remain in context and TLC guide loaded for alternatives. Only relevant TLC safety
scenario is discussed; no Python catalog support is invented or promoted.
Skill hashes, frozen brief digest and source reconciliation are retained in
provenance. All citations use r1=D3; manual review does not certify advice.
Inherited serializer tests and stdlib/native bodies were not inspected, no
application secrets or private/evaluator material read, and no proposed commands
executed. Source observations, inferred properties and proposed stronger policies
are intentionally distinct. Ready for independent evaluation only.
