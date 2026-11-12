# Proof-readiness advisory — D3 / dev-confirm-ee8d0e6

Status: completed advisory, not a verifier/target-test result.
2026-11-12. Task real-baseline/dev-confirm. Audience: Pallets maintainers and
downstream component owners. Goal: source-grounded timestamped signer contracts,
using existing production code; no replacement or source changes. The campaign
grant is read-only and does not approve upstream intent, implementation or execution.

## Scope and evidence

| Root | Selected absolute root | Revision / dirty state | Inspected | Skipped/unknown |
|---|---|---|---|---|
| r1 | <SOURCE-D3> | pallets/itsdangerous; 672971d66a2ef9f85151e53283113f33d642dabd; tree ef4287f82d8234404b58c7b29d38197e1f38e207; clean Git status | Entire timed.py, signer.py, encoding.py, exc.py, selected Serializer config/sign/unsign-iterator/unsafe/load_payload boundaries; url_safe.py; supplied timed/signer/encoding tests; timed/signer/concepts docs, README, pyproject 1–200, tests CI | stdlib hmac/hashlib/base64/struct/time/datetime/zlib bodies, custom algorithms/serializer/subclass bodies, full serializer and inherited test_serializer suite, final pyproject ranges, application policy and key management |

Output is outside all three selected roots. Before content reads, supplied
tracked regular-file paths/types/hashes and their symlink components were
checked; metadata search found no symlinks or nested .git outside root .git.
No atomic snapshot, OS isolation or automatic secret-detection guarantee exists.
Only example keys in public source were read; no real environment secrets
were sought. See COMMANDS.md and RESULT.json for actual operations, identity,
context, time and approximate returned-character limits.

## Decisions

Recommend two evidence-first/native-test opportunities, not a formal-verifier
port. The curated index (`references/index.md`, catalog envelope 1, all scenarios
1.0.0, documented snapshot checked 2026-11-05) has no native Python scenario.
Rust/C finite checkers do not cover these Python bodies. A separate TLC model
would prove properties only of a finite abstraction with correspondence still
owed; a Dafny replacement needs explicit replacement/codegen adoption not present
here. No new catalog entry or support claim is created.

Existing tests already cover normal expiration, future age, malformed/missing
timestamp, UTC return and tampering (`r1:tests/test_itsdangerous/test_timed.py:29-94`,
`TestTimestampSigner`), with inherited signer tests. Encoding tests cover zero,
192 and uint64 maximum (`r1:tests/test_itsdangerous/test_encoding.py:32-40`,
`test_int_bytes`); signer tests cover key rotation and selectable algorithms
(`r1:tests/test_itsdangerous/test_signer.py:89-111`,
`test_algorithm/test_secret_keys`). These artifacts are not passing results.
The source-specific gap is the interaction of authentication, conversion,
age policy and fallback exception handling—not a lack of a basic roundtrip test.

### O1 — Timestamp domain and exception contract (priority 1)

- **Value/effort:** callers may rely on validate returning a bool or catching
  BadSignature; conversion errors could cross that boundary. A source truth table
  and focused regression matrix are low/moderate cost. Platform-specific date
  limits require separate evidence and cannot be inferred from this Darwin host.
- **Target/call boundary:** `r1:src/itsdangerous/timed.py:29-51`,
  `TimestampSigner.get_timestamp/timestamp_to_datetime/sign`;
  `r1:src/itsdangerous/timed.py:72-169`, `unsign/validate`.
  Sign authenticates value+separator+encoded timestamp, not value alone.
  `r1:src/itsdangerous/signer.py:215-273`,
  `Signer.get_signature/verify_signature/unsign`, performs signature decoding
  and tries keys; `r1:src/itsdangerous/encoding.py:11-54` contains UTF-8 conversion,
  URL-safe base64, `>Q` packing and zero-left-padding unpack.
  These call Python stdlib implementations, uninspected here; their documented
  conventional semantics inform the proposal, not a proof of those bodies.
  User-overridden clock/date methods, digest/algorithm and serializer are
  open extension points, not established compatible implementations.
- **Requirement/class/authority:** documented expiration and aware UTC return
  in `r1:docs/timed.rst:6-22` and
  `r1:src/itsdangerous/timed.py:22-42,78-87`; documented BadTimeSignature
  hierarchy at `r1:src/itsdangerous/exc.py:23-64`.
  Exact inclusivity/future rejection comes from current code, thus **inferred**
  proposed contract pending maintainer confirmation: with max_age M supplied,
  accept only 0<=now−ts<=M. Negative M therefore accepts no age, rather than
  being silently assumed impossible. With M=None no age policy is applied.
  **Unresolved:** public allowed timestamp range and whether authenticated but
  unrepresentable dates must be normalized to BadTimeSignature. get_timestamp
  says “integer”, while packing uses unsigned 64-bit and datetime may have a
  smaller/platform-dependent domain. No owner approval is supplied.
- **Property/domain:** native str (UTF-8 encodable) or bytes values, including
  empty and embedded separators; nonempty configured key list, accepted separator,
  named supported key derivation/algorithm; integer ts in 0..2**64−1 for successful
  encoding; max_age None or any int; both return_timestamp values.
  The uint64 restriction describes the encoder, **not** approval to discard
  negative/too-large clock values or malformed/untrusted tokens: their error
  behavior must be included in the decision table. Arbitrary token bytes can
  have missing separators, undecodable timestamp, decoded lengths 0..>8,
  invalid MAC and authentic MAC. Empty timestamp encoding decodes to zero
  (`int_to_bytes(0)==b""` is tested), not necessarily “timestamp missing”.
  For successfully signed representable timestamp and matching config,
  unsign returns original bytes iff age policy allows; timestamp=True additionally
  returns the corresponding aware UTC datetime. Missing/malformed/signature-error
  branches should be enumerated separately with exception class, payload and
  date_signed; do not treat diagnostic payload or date as authenticated data.
  Return must never turn failed MAC into successful authenticated output.
  Straight-line parsing needs no loop invariant; key-loop invariant is O2.
- **Counterexamples and unresolved larger domain:** wrong result at age=M,
  future acceptance when M supplied, malformed timestamp accepted as another
  payload, unauthenticated output returned, or an unexpected non-BadSignature
  exception for a domain the owner promises validate handles.
  Source observation: the invalid-MAC branch catches ValueError/OSError/
  OverflowError from datetime conversion (`timed.py:118-131`); the valid-MAC
  expiration and return_timestamp conversions (`timed.py:138-158`) lack that
  normalization. **Unexecuted hypothesis:** an authentically signed uint64
  timestamp beyond datetime's supported range can return payload with
  M=None/return_timestamp=False, yet raise a raw date-conversion exception when
  requesting a timestamp or enforcing age. validate catches only BadSignature.
  This is a contract question, not a demonstrated exploit or a demand to change
  behavior. It remains relevant even if ordinary current clocks never emit it:
  overrides and separately constructed authenticated tokens are possible.
  Clock outputs below zero or beyond uint64 likewise need explicit rejection
  intent; cannot claim roundtrip for every integer from the clock docstring.
- **Method/assurance:** noncatalog source inspection followed, only if approved,
  by native table/property tests extending
  tests/test_itsdangerous/test_timed.py and test_encoding.py.
  Include age −1/0/M/M+1, M=0/negative/None, ts=0/uint64-max, 8/9 decoded bytes,
  invalid and valid MACs, missing timestamp and return_timestamp combinations.
  Controlled clock/subclass fixtures isolate policy; separately retain real
  datetime-platform cases and Python version/OS provenance. Sampled tests are
  observations, not exhaustive verification or cryptographic proof.
  Compatibility and platform exception types have not been executed/confirmed.
- **Alternatives/readiness:** inspection alone can resolve control flow but not
  owner intent or platform behavior. A translated arithmetic model would miss the
  important exception/date boundary; no framework implementation is justified
  before the owner chooses the supported date/error domain. Production repair is
  a separate blocked option, not this recommendation.

### O2 — Rotation and timed fallback control-flow contract (priority 2)

- **Value/cost:** configuration transitions can retain or revoke token acceptance
  unexpectedly; an explicit test matrix adds incremental assurance beyond one
  old-key example. Moderate scope; arbitrary custom signer semantics remain
  unknown and should not be hidden behind a universal claim.
- **Target/call boundary:** `r1:src/itsdangerous/signer.py:67-74,135-177`,
  `_make_keys_list/Signer.__init__`; `signer.py:195-241`,
  `derive_key/get_signature/verify_signature`. Sign uses the last key; verify
  traverses reversed keys. `r1:src/itsdangerous/serializer.py:278-307`,
  `make_signer/iter_unsigners`, yields the primary configured signer first,
  then fallback configurations, each instantiated per key in list order.
  Those are distinct ordering layers—fallback enumeration is not claimed to
  reverse keys merely because Signer.verify_signature does.
  `r1:src/itsdangerous/timed.py:172-221`,
  `TimedSerializer.iter_unsigners/loads`, always requests timestamp=True even
  if loads' caller does not, stops immediately on SignatureExpired, tries next
  signer on other BadSignature, and deserializes only after successful unsign.
  Thus O1's conversion boundary affects serializer calls too.
  `r1:src/itsdangerous/url_safe.py:15-52,78-83`,
  `URLSafeSerializerMixin.load_payload/URLSafeTimedSerializer`, adds
  base64/zlib/serializer behavior, not a stronger authentication contract.
- **Requirement:** documented oldest-to-newest rotation policy and removal
  semantics at `r1:docs/concepts.rst:102-137`; UTF-8/signature-error expectations
  at `r1:docs/signer.rst:24-39`; default/fallback intent from iter_unsigners
  docstring. Immediate expiration stop is an inferred explicit policy backed by
  code/comment in timed.loads, not maintainer approval. Downstream key lifetime,
  salt separation and algorithm choice remain the owner's responsibility.
  Current docs discuss their security context (`r1:docs/concepts.rst:18-29,57-68`);
  this assessment does not approve secrets or algorithms.
- **Property/domain:** finite nonempty list of byte/UTF-8 keys, fixed salt,
  concrete normal HMAC signer and named digest/derivation; bounded ordered
  fallback configurations satisfying TimestampSigner API; O1's age/date domain
  retained. New signatures use newest key; any retained authentic key can
  validate a matching token; removing its only matching key removes that
  acceptance **conditional on the algorithm's MAC behavior**, not a mathematical
  no-collision guarantee. Primary success prevents fallback use; ordinary
  BadSignature continues; expiration terminates immediately; no payload parser
  is invoked by normal loads before some unsigner succeeds.
  Invariant: before each key attempt none of the previously attempted keys
  verified; before each fallback attempt all earlier nonexpired attempts failed
  with BadSignature. Counterexamples: signing with an old key, accepting a
  token with no verifying retained key, bypassing expiry using fallback, or
  parsing untrusted payload on the normal failure path.
  Include reordered/duplicate/single/removed keys, wrong salt, bad MAC,
  empty config list and invalid derivation as explicit config-error cases—not
  assumed valid inputs. Empty key-list behavior/exception intent is unresolved.
  Injected custom algorithms such as NoneAlgorithm (returns empty bytes,
  `r1:src/itsdangerous/signer.py:31-37`) invalidate generic tamper-resistance
  claims; no all-algorithm authenticity guarantee is proposed.
- **Method/assurance:** noncatalog native test/control-flow audit with counting
  test doubles for call order and approved concrete signers for actual
  serialization. Doubles only observe control-flow policy and do not establish
  real crypto/date/serialization equivalence. Existing TestSigner key/algorithm
  tests and inherited timed tests provide starting cases, not completeness.
  hashlib/hmac/compare_digest and real custom extension bodies remain trusted/
  unmodeled, not verified here. No claim about constant time, MAC strength,
  replay prevention, confidentiality, key lifecycle or whole authentication.
- **Alternatives/readiness:** add no new crypto verification framework or digest
  replacement based solely on language/age of SHA1. Owner must confirm allowed
  algorithms, fallback behavior, error domain and adoption; O1 precedes meaningful
  expiration tests. The uninspected inherited serializer test suite may already
  contain fallback cases, so inspect it under separate bounded scope before
  proposing duplicate tests.

## Actionable handoff

| Work | Next bounded task / proposed files | Dependencies / approval | Acceptance / evidence |
|---|---|---|---|
| W1 | Read-only matrix for timed.py, encoding.py, signer.py, exc.py and current supplied tests | Campaign grant permits this evidence only; owner decision on clock/date/max_age/error contract missing | Enumerate MAC-validity × parse/range × age × return mode with exact source path, exception/payload/date provenance, unresolved cells retained; distinguish current behavior from desired intent |
| W2 | Read-only trace/coverage inventory for TimedSerializer plus configured/fallback Signer and proposed test matrix | W1; separate scope for inherited serializer tests/custom configured bodies; owner policy approval missing | Call order, expiration stop, no-deserialization-before-auth table, existing-vs-missing cases; no unsupported extension assumed equivalent |
| W3 | Separately proposed regression tests in supplied test_timed.py/test_signer.py/test_encoding.py, no production replacement | Blocked: W1/W2, owner intent, exact dependency/runtime/platform selection, explicit write/execution authorization and disposable no-secret isolation | Exact commands and Python/dependency versions, source/config/test identities, deterministic clock/timezone domains, platform date limits, complete output including failures; no inference of exhaustive proof from pass |

No task in W3 ran. The normal-load authentication ordering does not apply to
the explicitly unsafe diagnostic path:
`r1:src/itsdangerous/serializer.py:349-406`, `loads_unsafe/_loads_unsafe_impl`,
can deserialize a BadSignature payload and warns about unsafe serializers.
`r1:src/itsdangerous/timed.py:223-230`, `loads_unsafe`, forwards max_age there.
That path must not be used as evidence of authenticated data; application-specific
safe use is outside this assessment.

## Review and limitations

Index/scenario provenance, root citations, documented/inferred/unresolved labels
and approval dependencies were manually reviewed. No source changes, test results,
proof, exact-tool support, vulnerability reproduction or exhaustive call graph
were established. pyproject declares Python>=3.10, test dependencies and tox
environments (`r1:pyproject.toml:16,45-48,137-160`); CI declares
CPython 3.10–3.13/PyPy and OS variants (`r1:.github/workflows/tests.yaml:8-32`).
These definitions do not prove matrix completion or present target compatibility.
No runtime version was queried by importing/executing target code. Before/after
regular-file/Git identity is retained separately; static snapshots and clock
fixtures cannot establish live deployment policy.
