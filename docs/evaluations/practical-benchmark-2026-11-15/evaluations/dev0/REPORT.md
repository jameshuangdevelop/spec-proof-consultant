# Independent development evaluation

Task: practical-dev-grade-0
Status: completed
Verdict: all three advisories satisfy the frozen advisory-quality gate.
Scores: D1 = 10; D2 = 10; D3 = 10. Exact mean = 10.
No K1–K7 cap triggered. No unresolved high/critical finding.

This is an advisory-quality evaluation, not target verification, compatibility certification, owner approval, or authorization to lock/promote/merge the candidate.

## Identity and independence

The retained independent maps preceded author assignment:
- Produced: 2026-11-15T07:09:06.838224Z.
- Parent receipt: 2026-11-15T07:11:00.156734Z.
- Delivered map SHA-256:
  174ce27868db4bed911e992e4d1eb85e5ccd4dc712af832ced876bf875c528ff.

The original maps remain preserved in this context. No original advisory or map was edited.

Assessed source identities:
- D1: commit 8c535a260ce561eaab4111aafc29038eb9f77ff3,
  tree d0c2d891838c3c188f084bdafa0442e063b04d62.
- D2: commit 3febcb8561554927155923da335ac0549235b0b3,
  tree d1ee844cac447bf4d93c75de52532e79e5529c35.
- D3: commit 29465588d3dfdc80fba5e198037582b8fdb5dd60,
  tree 5e56720c8ea36b1d385362668605d0b40aa645e8.

Source roots resolve under Q/targets/<root_id>.
Commit/tree/cleanliness are supplied frozen metadata; independently recomputed
hashes of all 22 named source leads matched the mapping-phase hashes.

All four supplied author-artifact hashes matched exactly:
- D1: 257dffdba57602f127994bd23b0caeb3827ac7e27b11d6c17fb75da1e1f8c5f4
- D2: ed1d3f7969cbfea019274ca0f8021cbf8d97422de48d0b75cc94795e68723208
- D3: 7e2713d9d22115f4faf62a7dea2018c1c1f0ce92f882da051feae7809e4d95cc
- RESULT: 64536d79380551f30e2fb75fb68eee3a2064fc2f00a10e679250e53e357b6603

Development-scope SHA:
06b2dc593d5f86316fc55f95fe5de8e5bfaa6919d372cb7aa955aa7fffc84ab5.
QUALITY.md independently matched:
a013b447f8792036fd7b8c3a86a42dea9d932fd939ab821e915a7493eb82d942.

The evaluated skill is staged agent-native 0.2.1, supplied aggregate digest
00590d90781e66d1522d49a507f9bbb11e80b53ff3b89c8536bf519d5fd0e02a.
Individual asset hashes were retained during mapping; the aggregate recipe was
not supplied, so independent aggregate recomputation is not claimed.
Trusted-product identity was independently checked during mapping:
544a37baabf4a08d6fc4c5c6a7ef9d64a5226b89,
feat/practical-skill-benchmark, empty porcelain status.

## Citation audit

All decision-driving citations were checked against independently inspected
frozen source, using retained mapping reads and grading-phase rereads.
Named symbols, quoted behavior, configuration applicability and test-versus-
production provenance were checked—not merely path existence.

Audit coverage, in advisory order:
- D1: test definitions and limited append coverage; backend/hasher/features;
  std/alloc requirement, generated include and adjacent iterator;
  insert/remove/swap/shift/append contracts and branches.
- D2: conditional tests and platform-documentation provenance; comparator,
  initialization, rejection/saturation/counter allocation, stop/again;
  ready-queue dispatch, flags/reference accounting, heap helpers;
  queue include/private-field/platform boundaries and build configuration.
- D3: named test expectations and conditional test inclusion;
  public contract/virtual Handler, representation/parser/count/sequence;
  inserter, SetContents/Append, writer serialization/grouping and configuration.

Additional supporting citations were audited in report order:
- D1: tests/map.rs:4, :20, :30, :50; lib.rs generated include; iter.rs::next.
- D2: CMakeLists.txt:44 and :723; SUPPORTED_PLATFORMS.md:19.
- D3: write_batch_test.cc:54, :60, :75, :89, :115.

Several pointers are nearby rather than declaration-exact:
- D1: lib.rs generated include is :396, not :392;
  LineColIterator::next is iter.rs:54, not :48.
- D2: uv_timer_init is timer.c:57; uv_timer_again :112;
  uv__run_timers :164; heap_insert definition heap-inl.h:106;
  configure.ac gnu11 flag :36.
- D3: MemTableInserter begins write_batch.cc:116, not :118;
  InsertInto begins :132, with its Sequence assignment at :134.

These are low precision diagnostics. The real symbols are unambiguous,
the inspected windows contain them, and their substantive claims agree with
source. They do not constitute fabricated citations or materially impair the
handoffs; no score deduction or cap applies.

## Anchored assessment

### D1 — 10/10

G: Real wrapper/config/test/helper boundaries are grounded. In particular,
src/iter.rs is correctly rejected as a map helper; backend and Value bodies
remain explicitly outside closure.

C: O1 distinguishes mapping, returned values and survivor order. It includes
absent/empty/positional cases, well-formed borrowed keys, distinct mutable
append arguments, unresolved collision policy and exceptional behavior.
“Normal return” is a stated investigation domain, not an assertion that panic
or allocation behavior has been verified or approved away.

M: Source investigation and conditional native tests fit delegated collection
semantics. No language-only Kani/Verus pilot is offered. The noncatalog choice
and rejection of an abstract model's currently weak incremental benefit are
reasoned.

A: Tests, observations, inferred collision semantics and future work remain
distinct. No target/tool compatibility or proof is claimed.

D: Removal and nonempty/colliding append add concrete coverage beyond the
inspected insertion-order and empty-destination append examples. One opportunity
is sufficient; no quota applies. The independent shallow-canonicalization lead
was not selected, but no canonicalization guarantee or unsupported blanket
no-work decision is made.

H: All six leads and exclusions are recorded. W1 has source-evidence acceptance;
W2 is a specifically named command-selection artifact; W3 is separately blocked.
No execution invocation has been represented as already run.

### D2 — 10/10

G: Timer/common/heap/public/configuration boundaries are traceable.
Unread queue/platform/callback bodies are named and block dependent work.

C: The candidate includes rejection-before-mutation, saturation, counter wrap,
ready-queue cancellation, rearming before callbacks and transient phases.
It does not impose a falsely global active-membership invariant during every
instruction. Concurrent mutation, clock refresh and platform scheduling remain
unresolved original-domain obligations.

M: tla-state-machine-safety 1.0.0 is accurately conditional on finite abstraction,
adoption and correspondence. Whole-loop CBMC is not represented as supported;
hard exclusions and unread bodies remain barriers. Native traces are a relevant
alternative, and liveness is deferred for missing fairness/progress authority.

A: Finite model safety is not called native C correctness, memory safety or
liveness. Partitioned arithmetic is proposed, not claimed adequate already.

D: The two-stage ready-queue behavior is a substantial source-specific lead.
The source dossier precedes the more uncertain correspondence/model effort.

H: Coverage and gaps are usable. W1 requires phase/action and wrap analysis;
W2 explicitly resolves conditional commands/configuration before execution;
W3 remains blocked on adoption, grants and isolation.

### D3 — 10/10

G: Production parser, public interface, internal adapter, tests, immediate DB
caller and configuration are independently supported. Unread decoder, Slice,
Status, memtable and storage bodies are not silently closed.

C: The report separates public atomic DB updates from parser rollback.
It specifies status plus callback prefix, short headers, malformed records,
count mismatch, extreme signed counts, sequence/append behavior and self-aliasing.
InsertInto's Sequence read preceding Iterate's short-header check is correctly
identified. Broad malformed-input and extreme-size obligations remain unresolved,
not assumed away to claim a ready harness.

M: Native recording-handler tests/source investigation fit the observable
effects. CBMC is an investigation lead, not supported execution; virtual/string/
allocation/callee/model/unwinding prerequisites are explicit. No storage-wide
or concurrent pilot bypasses exclusions.

A: Existing corruption expectations are not test results. Model, test and native
proof boundaries remain distinct; exact support and intended exceptions remain
unknown.

D: Parser side effects are appropriately first; append count/sequence/alias
coverage is second. The incremental value is concrete without inventing a bug.

H: W1–W3 specify scope, dependencies, command selection, acceptance evidence and
blocked implementation. Static/shared test selection and submodule prerequisites
are recognized.

## Independent map challenges and additional negative variations

All following dispositions are source analyses, not executed target tests.

D1-C1 — addressed:
O1 explicitly distinguishes swap and shift removal.
Additional variation: with preserve_order keys [a,b,c,d,e], remove b predicts
[a,e,c,d], whereas shift_remove predicts [a,c,d,e], from map.rs:155–174,
235–251. Absent and last-key cases are retained in the advisory.

D1-C2 — not selected; no material contradiction:
map.rs:371–394 documents shallow sort_keys. The advisory does not claim recursive
canonicalization or universal serialization preservation. Nested [z,a] after
outer sorting remains a useful deferred boundary, not a hidden required task.

D2-C1 — addressed:
Saturation, failed-start preservation, clock/counter wrap and finite arithmetic
correspondence appear in O1/W1–W2.
Additional variation: on an already scheduled valid timer, a null-callback
start returns EINVAL before stop (timer.c:68–94). No callback-latency guarantee
follows from stored due_in or poll-wait arithmetic.

D2-C2 — addressed:
The advisory explicitly includes cancel-other/self, ready-queue phases and
again-before-callback.
Additional variation: due A and B, A restarts B. The inactive stop path removes
B's ready node before new heap insertion. The next dossier must represent this
transition rather than blindly deliver a collected snapshot
(timer.c:97–121,164–191; queue.h:79–91, independently read during mapping).

D3-C1 — addressed:
The partial-prefix corruption example and absence of justified rollback are
explicit.
Additional variation: fully decoded records with a wrong header count generate
callbacks before corruption, because Count is checked after parsing
(write_batch.cc:42–79). This is not evidence of a DB atomicity failure.

D3-C2 — addressed:
O2 retains self-aliasing, signed-count overflow, source/destination sequence and
public-versus-group-size boundaries.
Additional variation: signed Count at INT_MAX followed by positive append raises
a signed-sum obligation; exact machine/domain admissibility remains unresolved,
not a reproduced bug (write_batch.cc:144–148).

## Actions, commands and outcomes

Twenty grading-phase tool calls:
- Four author-artifact reads.
- Targeted source views/searches.
- Two trusted stdlib Bash commands.
No target code, tests, imports, builds, proof tools, installers, network or agents
were executed. No files or Git state were changed by this evaluation.
The complete exact tool arguments and output are retained in this task transcript.

Command 1, shell 779, exit 0, at 2026-11-15T07:16:44.203733Z:
python3 -I -S -B -c 'import pathlib,json,hashlib,sys,datetime; q=pathlib.Path("evidence://campaign"); print("utc",datetime.datetime.now(datetime.timezone.utc).isoformat()); print("python",sys.version); files=["advisories/dev0/D1/assessment.md","advisories/dev0/D2/assessment.md","advisories/dev0/D3/assessment.md","advisories/dev0/RESULT.json","scopes/development.json","protocol/QUALITY.md","protocol/SCORING.json","protocol/OPERATIONS.md"];
for name in files:
 p=q/name; print(name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest())
a=json.loads((q/"advisories/dev0/RESULT.json").read_text()); print("author_json_valid",len(a["artifacts"])); d=json.loads((q/"scopes/development.json").read_text());
for r in d["records"]:
 print("ROOT",r["id"],r["commit"],r["tree"])
 for key in ("production_files","immediate_caller_or_helper_files","configuration_files","test_or_requirement_files"):
  for f in r[key]: print(f,hashlib.sha256((pathlib.Path(r["root"])/f).read_bytes()).hexdigest())'

Outcome: supplied artifact hashes matched, author JSON parsed with three artifacts,
protocol identities recorded and all named source hashes unchanged.
Environment: Darwin; Python 3.10.6, Clang 13.1.6.
This validates data identity/syntax, not advisory semantics.

Command 2, shell 782, exit 0:
python3 -I -S -B -c 'from fractions import Fraction; weights=[Fraction(2),Fraction(2),Fraction(3,2),Fraction(3,2),Fraction(3,2),Fraction(3,2)]; factors=[[1,1,1,1,1,1]]*3; scores=[sum(w*f for w,f in zip(weights,row)) for row in factors]; mean=sum(scores)/len(scores); print("scores",[str(x) for x in scores],"exact_mean",str(mean),"individual_and_mean_gate",all(x>=9 for x in scores) and mean>=9)'

Outcome: scores 10,10,10; exact mean 10; numeric gate true.
Semantic factors were assigned independently before this arithmetic check.

## Original-failure dispositions and limitations

- Reported missing `python`: no target code ran; metadata fallback is diagnostic.
- Initially absent output directory: an authorized outside-root creation,
  according to supplied action record; not a target write.
- Reported plutil JSON-as-plist lint failure: diagnostic only. Exact raw invocation
  and output were not supplied here. Authorized stdlib JSON parsing succeeded.
- Citation offsets: independently reproduced as nearby pointers, not material
  fabrication. Originals preserved.
- Read-window overlaps/overruns: disclosed diagnostics, no invented resource cap.
- No prior failed advisory or repair was supplied; this is initial evaluation.

Author action evidence is the supplied RESULT and handoff, not an independently
available raw execution log. Their lack of target execution is not proven merely
by self-report. No concrete safety/authority/blinding/identity breach is evidenced
in the permitted artifacts; named source hashes corroborate unchanged content.
No action-log absence has been converted into an accusation or a clean-baseline
proof.

Target execution and exact tool compatibility remain untested. Dependency,
platform, exceptional-input and model-correspondence closure remain future work.
Correctly blocked unknowns are not penalized as fabricated support.
No performance comparison, cost saving or human-review timing is established.

Recommended next action: orchestrator may record this initial cohort's qualifying
quality result and apply the separately specified campaign sequence. Candidate
locking, confirmation, later trials, publication and human approval are not this
evaluator's actions. Stop after this grading handoff.
