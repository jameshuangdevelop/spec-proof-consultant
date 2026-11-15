# Independent confirmation evaluation

Task: practical-confirm-grade
Status: completed
Verdict: confirmation cohort qualifies under frozen QUALITY/SCORING.
This is advisory-quality acceptance, not human approval, target compatibility,
execution success, implementation readiness or campaign-wide acceptance.

## Identity and evidence

Q=evidence://campaign

Evaluated canonical files:
- Q/advisories/confirmation/D1/assessment.md
  SHA256 5d6bf1bbd1d8c913deb4a13544cf558e3eb9eca4214e764c388575a28160fb3b
- Q/advisories/confirmation/D2/assessment.md
  SHA256 fbcbfd2b3816557204e55fe1efe98da29f367dc500c0fb781fa0a1672d7ebaee
- Q/advisories/confirmation/D3/assessment.md
  SHA256 4af7eead67044562bdb73f03e59f7dd92cbfc86c711dc90c22ae9941a880174e

All three hashes independently matched the handoff and cohort RESULT.json.
Operational evidence: Q/advisories/confirmation/RESULT.json.
There are no per-root RESULT.json files; three attempted reads failed before
the cohort-level file was located. This is not an author delivery failure.

Skill: exact Q/locked/proof-readiness/, version 0.2.1.
Source commit recorded by LOCK:
29df86f38291093e90055f30c00361930d5d27cd.
Every locked file's SHA256 independently matched LOCK.json again during grading.

Development scope SHA256:
06b2dc593d5f86316fc55f95fe5de8e5bfaa6919d372cb7aa955aa7fffc84ab5.

Selected source identities:
D1 HEAD 8c535a260ce561eaab4111aafc29038eb9f77ff3
   supplied tree d0c2d891838c3c188f084bdafa0442e063b04d62
D2 HEAD 3febcb8561554927155923da335ac0549235b0b3
   supplied tree d1ee844cac447bf4d93c75de52532e79e5529c35
D3 HEAD 29465588d3dfdc80fba5e198037582b8fdb5dd60
   supplied tree 5e56720c8ea36b1d385362668605d0b40aa645e8

Detached HEADs were independently read. All 22 authorized named-file hashes
matched the identities retained during pre-author mapping. Full-tree cleanliness
and tree IDs remain supplied metadata rather than an independent complete-tree
audit. Sequential identity checks are not an atomic snapshot guarantee.

Original map retained unchanged:
produced 2026-11-15T07:24:32.612225Z,
SHA256 b317632b53ec9b9fbff0e39d110807b4afb274b160a9a5d46af86071d87d8de9.
Receipt time is supplied orchestrator metadata. No old development reports,
grades, feedback, heldout/reserve scopes or live logs were inspected.

## Scores and anchor judgments

Weights G/C/M/A/D/H = 2/2/1.5/1.5/1.5/1.5.
All factors below are 1. Raw and final scores are 10 for each report.
Exact mean is 10. No K1–K7 cap or unresolved high/critical finding established.

### D1

G: Removal implementation, feature selection, documented behavior, matching
tests, public exports and build-script effects are accurately cited. Unread
Value, container implementations and downstream callers are explicitly bounded.

C: O1 distinguishes binding preservation from traversal order, specifies missing
and existing keys and first/middle/last positions, and labels the small sampled
domain as tests rather than an API restriction. Documentation is not treated as
owner approval. Panic/OOM/destruction and recursive Value behavior are not proved.

M: Noncatalog source investigation/native tests fit the wrapper and read-only
adoption constraints. Rust alone is not used to claim Kani/Verus eligibility.
Dependency support and adaptation remain unresolved.

A: Observations, hypotheses, proposed tests and proof are distinguished. There
is no passing-test or exact-tool-compatibility assertion.

D: Removal ordering is a useful concrete priority beyond the inspected examples.
Append collisions and shift-insert index behavior are expressly deferred for
dependency/intent investigation. The omitted hash/nested-sort branch does not
make this bounded, non-exhaustive removal recommendation materially deficient.

H: All named leads and skipped boundaries are recorded. W1/W2 have measurable
source-evidence and invocation-selection acceptance. W3 remains separately
blocked on intent, support, grants and isolation.

### D2

G: Start/stop/again, two-phase dispatch, heap helpers, active flags and platform
configuration are traceable to source. The report explicitly leaves queue
implementation, platform fields, callbacks and loop/time callers unresolved.

C: The proposed model represents ready-list cancellation/restart rather than
assuming all initially due callbacks fire. Membership invariants and observable
counterexamples are concrete. Numeric domains, wrap, reentrancy and lifetime
authority are unresolved W1 obligations, not assumptions used to claim success.

M: tla-state-machine-safety 1.0.0 is accurately conditional on accepted finite
abstraction and correspondence. CBMC is not presented as a supported event-loop
pilot; pointer/callback closure and applicable hard exclusions are preserved.

A: The quoted TLC assurance is finite-model invariant checking under completed
exploration/configuration, not C correctness, liveness, race freedom or heap
safety. Compatibility remains unknown.

D: Callback cancellation and repeat-rearm ordering are source-specific,
incrementally useful questions. Arithmetic is acknowledged as a separate
possible lead without forcing a second task. Existing test bodies are honestly
unavailable rather than counted as passing assurance.

H: The transition artifact, invocation-selection prerequisite and conditional
model artifacts provide usable acceptance evidence. Further source scope,
model adoption and execution are not implied to be authorized.

### D3

G: Parser branches, handler effects, delayed count validation, corruption test,
caller logging/insertion, batch grouping and C++ configuration are accurately
grounded. Missing coding/Slice/Status/MemTable implementations are not hidden.

C: The report separates ordered DB updates from Iterate rollback. Valid,
truncated, unknown-tag and count-mismatch inputs have explicit trace/error
conditions. Handler restrictions and finite bounds require approval; larger
count/length and short-header construction obligations remain outstanding.

M: Source contracts and recording-handler tests are appropriate first steps.
cbmc-c-buffer 1.0.0 is conditional, with C++/allocation/callee/machine-model
requirements and assembly/concurrency/FFI exclusions preserved.

A: Native samples, potential complete bounded checks and storage-wide assurance
are distinguished. No parser, persistence, rollback or verifier pass is asserted.

D: Partial effects on corruption are a concrete high-value lead corroborated by
production and existing test source. Append alias/count/sequence questions and
DB-wide batching are appropriately deferred rather than silently verified.

H: W1 requests reachable malformed-input construction and missing callee scope.
W2 resolves actual commands/configuration before execution. W3 remains blocked
and specifies trace cases, bounds, provenance, complete output and failures.

## Independent citation audit

All decision-driving citations were checked against inspected source or the
locked guides; at least three other citations per report were also audited.
Repeated citations were checked for their distinct claims, not file existence.

D1:
- src/map.rs:1–69: MapImpl/hashers/capacity configuration.
- src/map.rs:130–299: insert, shift_insert, all six removal interfaces,
  documented order, borrowed-key bounds, append delegation.
- Cargo.toml:1–70: Rust minimum, dependency ranges and feature matrix.
- src/lib.rs:365–445: std/alloc requirement, Map export, public map module.
- Additional citations in report order: tests/map.rs:4, :20, :30; also :50,
  src/iter.rs:3 and build.rs:19–29. Tests are source artifacts, not runs.

D2:
- src/timer.c:37–198: comparator, rejection, saturation, counter increment,
  stop/again, due-in/timeout and extraction/rearm/callback ordering.
- src/uv-common.h:291–355 and retained mapping windows: flags/count/init.
- src/heap-inl.h:60–160 plus retained complete helper inspection.
- include/uv.h:1008–1030: public timer description/private-field dependency.
- CMakeLists.txt:19–24, :180–215; configure.ac:30–41.
- Additional artifact citations: CMakeLists.txt:721, :722, :723, followed by
  SUPPORTED_PLATFORMS.md:3 and its tier descriptions.
- Locked TLC/CBMC guides independently inspected during mapping and hash-checked
  again during grading.

D3:
- db/write_batch.cc:26–148: parser, Count, encoding calls, Inserter and Append.
- include/leveldb/write_batch.h:5–72: order/atomicity/threading/Handler API.
- db/db_impl.cc:1206–1278 and :1281–1333; db/db_impl.h:129–139.
- CMakeLists.txt:17–83 and :308–343; .gitmodules:1–6.
- Additional citations in report order: write_batch_test.cc:54 Empty,
  :60 Multiple, :89 Append; also :115 ApproximateSize.
- Corruption :75–86 and PrintContents :12–51 independently support the
  decision-driving prefix-effect distinction.

Minor pointers described below do not change attribution or recommendation.

## Findings, prioritized

No high, critical or material medium defect established.

Low / diagnostic D2:
configure.ac's gnu11 flag is line 36, not 37; heap_remove starts at line 150,
not 149. Both symbols/claims are immediately inspectable and correct.
These are not fabricated/misattributed evidence and trigger no cap.

Low / diagnostic D3:
The coverage sentence says no window exceeded 150, but both its coverage table
and RESULT.json disclose write_batch.cc:1–180. That 180-line request is below
the ordinary 200-line boundary. The contradictory bookkeeping sentence is not
evidence of unsafe reading, omitted semantic coverage or a quality-gate failure.

Shared diagnostic:
RESULT.json records a failed python metadata probe, exit 127, subsequently
performed with python3. This is not target execution or a failed product check.
The original failed operation remains recorded.

## Pre-author challenge dispositions and negative variations

These are source reasoning, not executed target tests.

D1-order — addressed:
For preserve_order keys a,b,c, ordinary remove(a) must not be assigned the
stable-survivor contract of shift_remove(a). O1 explicitly preserves that
distinction and covers missing/first/middle/last and entry-returning variants.

D1-merge-hash — bounded defer/partial:
Append collisions and shift-insert index behavior are deferred explicitly.
Hash order independence and shallow nested sorting are outside the selected
removal opportunity; no contrary guarantee is claimed. No mandatory task quota.

D2-deadline — bounded defer:
Saturation and start-ID wrap are identified; unconditional lifetime FIFO and
liveness are rejected. UINT64_MAX-2 plus delay 3, INT_MAX+1 timeout differences,
and counter rollover remain useful separate numeric cases, not executed results.

D2-ready-lifecycle — addressed:
A callback stopping/restarting another already-ready timer is included.
Extraction before dispatch and repeat rearm before callback are preserved.
Queue/platform/callback correspondence remains blocked, not proved.

D3-corruption-prefix — addressed:
A valid Put followed by truncated Delete may leave a prior callback effect.
A fully parsed body with wrong header count produces callbacks before corruption.
The advisory expressly rejects rollback inference and adds those trace cases.

D3-append-count — bounded defer:
Self-append, count and sequence overflow are deferred with unresolved authority
and callee evidence. INT_MAX+1 count arithmetic is an investigation obligation,
not a reproduced bug. No storage-wide atomicity or append proof is asserted.

Original-failure dispositions:
No earlier development failures were supplied or accessed, so none were
regraded or erased. The known metadata failure and citation/bookkeeping
diagnostics are retained above. This is the single confirmation evaluation.

## Actions and reproduction record

Evaluator environment: Darwin, shared environment, no sandbox.
Tools: native view and parallel reads; trusted own stdlib Python only.
All shell commands used python3 -I -S -B -c with literal data-only scripts.
No production, test, schema, evidence or Git-state changes were made.
No evaluation files were written; this is the complete inline report/result.

Exact executed commands, parameters and complete stdout are preserved in this
same-task tool transcript:
- Session 800: advisory ancestor/type/hash checks and every locked skill hash.
- Session 801: numbered bounded D1 citation reads.
- Session 802: numbered bounded D2 citation reads.
- Session 803: numbered bounded D3 citation reads.
- Session 804: development scope hash, source detached HEADs, ancestor lstat
  checks and all 22 named-file SHA256 values.
- Session 805: Fraction-based exact weighted-score and mean calculation.
All six commands completed with exit zero. Their outputs establish only the
reported data reads/hash/arithmetic results, not target correctness.

Citation-read script used in sessions 801–803:
import pathlib; root=pathlib.Path(<literal selected root>);
for f,a,z in <literal file/range tuples>:
    print("FILE",f)
    lines=(root/f).read_text().splitlines()
    for n in range(a,min(z,len(lines))+1):
        print(str(n)+": "+lines[n-1])

Exact tuple expansions:
801/D1:
[("src/map.rs",130,299),("tests/map.rs",1,70),("Cargo.toml",1,70),
 ("src/lib.rs",365,445),("src/iter.rs",1,20),("build.rs",15,34)]
802/D2:
[("src/timer.c",37,100),("src/timer.c",101,198),
 ("src/heap-inl.h",60,72),("src/heap-inl.h",101,160),
 ("src/uv-common.h",291,355),("include/uv.h",1008,1030),
 ("CMakeLists.txt",19,24),("CMakeLists.txt",180,215),
 ("CMakeLists.txt",710,730),("configure.ac",30,41),
 ("SUPPORTED_PLATFORMS.md",1,27)]
803/D3:
[("db/write_batch.cc",26,100),("db/write_batch.cc",101,148),
 ("include/leveldb/write_batch.h",5,72),("db/write_batch_test.cc",50,137),
 ("db/db_impl.cc",1206,1278),("db/db_impl.cc",1281,1333),
 ("db/db_impl.h",129,139),("CMakeLists.txt",17,83),
 ("CMakeLists.txt",308,343),(".gitmodules",1,6)]

Additional view reads:
D1/src/map.rs:1–69; D3/db/write_batch_test.cc:12–51.
Earlier independent mapping inspection and source identities were retained,
not replaced by the author's implementation summary.

Recorded author actions were audited as supplied operational claims:
the exact listed Git/nl/sed/hash commands are read-only; reported report writes
are outside all selected roots; no listed command executes assessed code.
Raw author action logs were not supplied or accessed. Therefore absence of
unlisted unsafe actions is not independently certified. No observed K2 action
is inferred merely from missing logs.

## Limitations and next action

No target tests, builds, imports, proof tools, installations or network were
authorized or executed. No dynamic reproduction, exact target compatibility,
complete call closure or whole-tree atomic identity is established.
Ancestor checks are non-atomic and do not create isolation. Hidden runtime
context, full syscall accounting and costs remain unavailable.

The reports correctly block future implementation/model execution on actual
intent, support, scope/adoption and grants. Those unresolved future-work
prerequisites are not unresolved high/critical defects in these advisories.

Next action: orchestrator may retain this immutable confirmation grade.
No confirmation repair/retry, new scope, implementation, merge or promotion
is authorized by this result. Evaluator stops here.
