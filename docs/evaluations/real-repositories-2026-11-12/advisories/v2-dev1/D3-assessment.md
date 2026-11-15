# D3 — timestamped signer advisory

Status: authored advice only, 2026-11-12. No execution, verifier result, grading,
approval or repair. Goal: useful contracts for existing TimestampSigner and its
signer/encoding/caller boundary. Audience: Pallets maintainers/downstream owners.
Campaign authority permits offline discovery, not upstream intent or implementation.

## Scope and evidence

| Root | Selected absolute root | Identity |
|---|---|---|
| r1 | <SOURCE-D3> | HEAD 672971d66a2ef9f85151e53283113f33d642dabd; tree ef4287f82d8234404b58c7b29d38197e1f38e207; tracked status empty before inspection |

Read timed.py, signer.py, encoding.py, exception interfaces, bounded serializer
and URL-safe caller context, timed/signer/encoding tests, timed/signer docs,
concepts search hits, pyproject and CI. README hashed, not interpreted.
Skipped: arbitrary custom algorithms/digests/signers, full serialization internals,
JSON/zlib, Python stdlib/OS datetime/HMAC implementations, application policy and
key storage. No deployed keys were sought or read. Public fixture strings are not
deployment key evidence. No whole-system cryptographic or authentication claim.

Existing artifacts: r1:tests/test_itsdangerous/test_timed.py:34-94 observes expiry,
future time, missing/malformed timestamps and signature-error metadata;
r1:tests/test_itsdangerous/test_encoding.py:31-39 samples 0/192/uint64 max;
r1:tests/test_itsdangerous/test_signer.py:93-102 exercises key rotation.
CI advertises Python 3.10-3.13/PyPy, Mac/Windows/Linux
(r1:.github/workflows/tests.yaml:9-32). None was executed or reproduced.
Test presence is not approved intent or a passing result.

Output is outside all three selected roots. Scoped ancestors/files were checked
with lstat and regular-file hashes; no known symlink was followed. This is not
atomic snapshotting, sandboxing or a guarantee of detecting secrets.
All views were explicit <=100-line windows; searches <=20 matches. Provenance
records UTC, budget accounting limits, identities and before/after hashes.

## Decisions

Two opportunities: native contract/regression planning on existing Python code,
not forcing a formal tool onto a noncatalog surface. The curated index has no
native Python verification scenario. Rust/C guide entries do not apply by
analogy. A separate finite model would check its abstraction, not Python exception
behavior or HMAC. Verified-source replacement/code generation is contrary to this
adoption preference; not recommended. No production edit proposed.

### O1 — Exact age gate and caller fallback semantics

- **Priority:** first; high downstream policy relevance with low-cost source/owner
  clarification and native boundary cases. Incremental benefit over existing
  tests: equality, max_age=0/None/negative, and no-expiration bypass of clock checks.
- **Target/call boundary:** r1:src/itsdangerous/timed.py:29-51 (`get_timestamp`,
  datetime conversion, sign) and :72-168 (`unsign`/`validate`).
  Sign authenticates the payload plus timestamp using inherited get_signature
  (r1:src/itsdangerous/signer.py:215-239). Integer clock truncates time.time;
  subclasses may override it. Base64/int encoding is at
  r1:src/itsdangerous/encoding.py:20-55. TimedSerializer calls unsign with
  return_timestamp=True and forwards max_age (:201-220); URLSafeTimedSerializer
  inherits that behavior (r1:src/itsdangerous/url_safe.py:75-80).
- **Requirement — documented:** expiry optional and timestamp not older than a
  given age, r1:docs/timed.rst:6-9; aware UTC result,
  r1:src/itsdangerous/timed.py:35-43 and :78-86.
  **Inferred from implementation:** acceptance includes age==max_age, rejects
  negative age only when max_age is supplied. **Unresolved:** intended behavior
  for negative max_age, rollback clocks without max_age, custom clocks and
  timedelta-like/non-int values. Keep API annotation int|None; do not broaden it
  by accidental Python duck typing. Owner approval is absent.
- **Property/domain:** fixed supported signer config with a nonempty key list,
  normal nonempty separator (initial pilot b"."), deterministic clock N and
  successfully authenticated, syntactically valid timestamp T; datetime
  conversion must succeed whenever that branch needs it. For integer M>=0,
  unsign accepts exactly 0<=N-T<=M with max_age=M; otherwise SignatureExpired
  with original payload and aware UTC date_signed. Equality and zero are included.
  With max_age=None the function does not consult the current clock or enforce
  age. Return_timestamp=False returns bytes; True returns (bytes, aware datetime).
  Sign/unsign roundtrip preserves want_bytes(value), including UTF-8 str and
  payloads containing the separator. Negative timestamps and uint64 overflow
  are not automatically signable: O2 distinguishes the domains.
  No loop invariant in the age gate; it is a branch decision.
- **Caller invariant:** TimedSerializer loads tries another signer after
  BadSignature, but not after SignatureExpired (r1:src/itsdangerous/timed.py:202-220).
  iter_unsigners uses configured signer then fallback configurations, and keys
  (r1:src/itsdangerous/serializer.py:287-307). Test plan should assert an expired
  successfully verified token does not become accepted via a later fallback;
  do not infer whole application policy from this local control flow.
- **Counterexamples/test boundaries:** ages -1/0/M/M+1, M=0/None/negative,
  timestamps around an integer-second rollover, and payload separator occurrences.
  Example: signed at T=100, checked at N=110,M=10 is an inferred accepted equality
  case; N=111 is expired. N=99 with M=10 is expired, whereas with None it bypasses
  the age gate. These are source-derived examples, not run results.
  Negative M has no age satisfying 0<=age<=M; preserve that edge for owner decision,
  not silently constrain the published API to positive M.
- **Method/limits:** explicit noncatalog source analysis and proposed native pytest
  regression matrix. Execution would observe samples, not prove arbitrary tokens,
  clock implementations or cryptographic security. No catalog compatibility
  claim. Python/platform/dependency versions still need pinning.
- **Alternatives/prerequisites:** extend existing freezegun-based tests rather than
  reimplement signing. A finite TLC model would require separate opt-in and
  correspondence evidence and would not check Python datetime exceptions.
  Resolve intent, platform conversion domain and owner/execution approval first.

### O2 — Timestamp representation and failure taxonomy at the trust boundary

- **Priority:** second; important robustness and client error handling, moderate
  matrix cost across platform date ranges and authenticated malformed envelopes.
  This is not a request to weaken rejection or claim a confirmed vulnerability.
- **Target/callees/config:** r1:src/itsdangerous/timed.py:88-159,
  r1:src/itsdangerous/encoding.py:28-55, inherited Signer.unsign
  r1:src/itsdangerous/signer.py:244-277. Encoding delegates base64/struct;
  timestamp_to_datetime delegates datetime.fromtimestamp. Their bodies/support
  are unread. r1:src/itsdangerous/exc.py:23-64 establishes
  SignatureExpired < BadTimeSignature < BadSignature.
  validate catches only BadSignature (:160-168), not arbitrary conversion errors.
- **Requirement:** integer clock and aware UTC conversion are **documented**
  at r1:src/itsdangerous/timed.py:29-43. Broad “only validates” bool wording at
  :160-162 is documented, but exception totality over all strings/platforms is
  **unresolved**, not an approved no-throw promise.
  **Inferred proposal:** specify a decision table for missing timestamp,
  failed signature, invalid encoding/width, valid uint64 but unrepresentable
  calendar time, expiry and return_timestamp.
- **Property/domain:** distinguish (a) signable unsigned 64-bit integer T
  (0..2^64-1 from struct >Q), (b) any decoded byte length 0..8 accepted by padded
  unpack, and (c) platform-convertible UTC datetime T. These are not identical.
  Zero encodes as empty bytes and decodes as zero; >8 decoded bytes fail unpack.
  Include original signed bytes and str (UTF-8 conversion), wrong/missing
  separators, empty timestamp and noncanonical base64. Base64 decoder adds
  padding; do not invent strict-canonical rejection absent evidence.
  For each cell record exact result/exception class, payload and date_signed;
  no universal “malformed implies BadTimeSignature” property is assumed.
- **Source-observed branches:** missing timestamp rethrows earlier signature error,
  else BadTimeSignature (:102-106). Decode/unpack failure is caught (:112-115).
  Bad signature with convertible timestamp carries date_signed; conversion
  ValueError/OSError/OverflowError is wrapped in BadTimeSignature (:119-130).
  For a *valid* signature, conversion on expiry/future or return_timestamp
  (:139-156) has no corresponding local conversion-error catch.
  Successful max_age=None,return_timestamp=False does not convert T at all.
  These are control-flow observations, not runtime reproductions.
- **Concrete challenge:** construct using public base Signer with the same
  nonproduction fixture config a valid signature over `payload.sep.timestamp`
  where timestamp is uint64 max (eight 0xff bytes before base64 encoding).
  Parsing can yield 2^64-1; no-age/no-return can return payload without conversion,
  while return_timestamp=True or an age-error branch attempts datetime conversion.
  Actual platform error type/range is unknown and must be retained, not asserted
  universally. validate may propagate a non-BadSignature conversion exception.
  The existing underscore-malformed test covers a different decode/width path,
  not this valid-MAC/calendar-range distinction.
- **Trust/key boundary:** payload/date_signed on failed signatures are diagnostic
  untrusted metadata, never authenticated application data
  (r1:src/itsdangerous/exc.py:29-33; timed.py:119-130).
  Verification iterates keys newest-first, signing uses newest key
  (r1:src/itsdangerous/signer.py:138-144, :197-199, :244-250);
  include rotation/salt agreement in the test config. Do not assert “tampering
  always fails” for arbitrary configured algorithms: NoneAlgorithm intentionally
  emits empty signatures (:31-37), custom algorithms are open, and HMAC/hashlib
  security is outside inspected source. No app authentication claim.
- **Method:** noncatalog source decision-table work and proposed native tests on
  unchanged production code. Native samples do not prove all bytes/platforms or
  cryptographic unforgeability. No Kani/CBMC/Verus support claim for Python.
  Tests should preserve unexpected exceptions as findings, not suppress them or
  update expectations to force acceptance. Any error-normalization repair would
  be a separate blocked production change, requiring an owner-approved contract.
- **Prerequisites/alternatives:** owner decides error taxonomy, supported platforms,
  separator/config domain and whether a raw conversion exception is contractual.
  Existing regression extension is preferable to a surrogate parser or signing
  rewrite. Compatibility remains unknown until Python/stdlib dependencies and
  platform ranges are documented.

## Actionable handoff

| Work | Next bounded task / proposed artifact | Dependency / authority | Acceptance |
|---|---|---|---|
| D3-W1 | Read-only `D3-time-contract.md`: owner questions and age/exception decision table | Advice authorized only; no owner implementation grant | Explicit documented/inferred/unresolved labels, equality/negative/None cases, signable vs calendar domain, failed-signature trust and fallback behavior |
| D3-W2 | Read-only `D3-command-plan.md`: select native regression invocation and dependency/platform pins | W1; no test execution authority | Exact pytest/Python/freezegun versions, cwd r1, arguments/selectors for proposed test files, OS/timezone/clock control, no live keys/network, isolated run plan; label unexecuted |
| D3-W3 | Separately proposed extensions to test_timed.py/test_encoding.py/test_signer.py only | W1/W2 plus named maintainer/downstream owner approval and execution/isolation authorization | Boundary table covered without skipping failures; retain raw complete output, source/test hashes, exact versions/commands/platforms, fixture clock/config, failure/counterexample artifacts |

No commands in W2 have been selected or run. W3 is blocked, not authorized.
Production remains unchanged; no verified-source replacement is proposed.

## Review and limitations

Actual supplied skill/index/template used; index gap is preserved, not filled by
inventing a Python scenario. Source/intent/proposal/result distinctions are above.
Identity recheck and budget are in provenance. No exhaustive coverage, standard
library compatibility, recommendation validation, proof or approval is established.
