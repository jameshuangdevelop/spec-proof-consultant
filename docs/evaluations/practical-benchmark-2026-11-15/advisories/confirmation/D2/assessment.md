# Proof-readiness advisory

Status: recommendation only; no target execution or verifier result.
Date: 2026-11-15. Task: practical-confirm-author, single confirmation cohort.
User goal: bounded source-grounded timer/common-library planning, not a
cross-platform operational proof. Adoption: read-only planning; actual owner
implementation/execution grants absent; shared environment is not a sandbox.

## Scope and evidence

| Root ID | Selected absolute root | Revision / dirty state | Inspected areas | Skipped / unknown areas and why |
|---|---|---|---|---|
| r1 | evidence://campaign/targets/D2 | commit `3febcb8561554927155923da335ac0549235b0b3`; tree `d1ee844cac447bf4d93c75de52532e79e5529c35`; initial/final read-only status empty | `src/timer.c` 1–200, `src/heap-inl.h` 1–300 (EOF-short); `src/uv-common.h` 245–365, `src/uv-common.c` 260–300; `include/uv.h` 1005–1035; `CMakeLists.txt` 1–55, 180–215, 710–730; `configure.ac` and `SUPPORTED_PLATFORMS.md` 1–100; targeted named-file symbol/config searches | Platform implementations, queue helper body, timer private-field definitions, actual loop callers/time updates, callback clients, tests and most common/public header code unread. Supplied exclusions retained: docs, tools, platform source, external libraries, unlisted trees, target instructions, symlinks/submodules/vendor/build/private/binary areas. |

Output: `evidence://campaign/advisories/confirmation/D2/assessment.md`,
outside all selected roots. Named leads were regular files below 256 KiB;
selected and parent real paths matched. No atomic no-follow or secret-detection
guarantee and no execution isolation is supplied by these checks.

Budget: eight named files (250 initial allowance); requested source windows
totaled 1005 lines plus a 14-line native citation cross-check (1019 total),
some EOF-short. One 121-line header window exceeded the
preferred 100 but not 200; all others at most 100. Searches had explicit result
limits and do not establish call closure; no reported text-file truncation.
No cumulative codepoint/syscall checker. Final revision/full status unchanged,
but sequential reads are not an atomic snapshot.

Existing assurance: `r1:CMakeLists.txt:721`–723 lists timer test filenames.
Their bodies/results were not inspected: no test coverage or passing claim.
`r1:SUPPORTED_PLATFORMS.md:3` lists tiers and platforms, not evidence that this
slice was verified. Source observations below are not approved temporal promises.

## Decisions

One useful evidence-first lead is the timer's two-phase heap-to-ready-queue
dispatch, including callback cancellation/restart effects. A separate finite
state model is conditional, not an established implementation verification.
Avoid claiming eventual delivery, scheduler fairness, race freedom, cross-platform
support or FIFO order across counter wrap. Native integration tests should be
considered only after existing test bodies can be inspected under a new scope.

Loaded `references/tlc.md` and `references/cbmc.md` from staged skill 0.2.1.
Both use index provenance: catalog snapshot
`9ce3702cb69a0944cb4db4d5b318cf118cf00509`, documented scenarios 1.0.0,
primary-source check 2026-11-05, no local verifier reproduction.

### O1 — Timer ready-queue cancellation and dispatch safety contract

- Priority/rationale: medium-high planning priority. Lifecycle/queue transitions
  determine whether callbacks remain dispatchable after another callback stops
  or restarts a timer. Explicit transition correspondence could catch mistaken
  requirements/models before costly execution. Model cost/state-space size and
  incremental benefit over unread tests remain unknown.
- Target/boundary: `r1:src/timer.c:67` `uv_timer_start` rejects closing/null-cb
  before stopping; lines 78–86 saturate deadline on addition wrap and allocate
  `start_id`. `timer_less_than` at line 37 compares timeout then start ID.
  `uv_timer_stop` at line 97 removes an active timer from the heap, otherwise
  removes its queue node, then initializes the queue node. `uv_timer_again`
  at line 112 rearms nonzero repeat. `uv__run_timers` at line 164 drains due
  heap nodes into a local ready queue before invoking callbacks, removing each
  ready node and rearming it before callback (lines 185–191).
  `r1:src/uv-common.h:291`–320 implements flags/active counts; line 348
  initializes handles. `r1:src/heap-inl.h:106` `heap_insert` and line 149
  `heap_remove` manipulate pointer-linked nodes; `heap_min` at line 67 reads
  the minimum. These observations do not verify heap/queue memory safety.
  The public timer type uses unread `UV_TIMER_PRIVATE_FIELDS`
  (`r1:include/uv.h:1016`); platform layouts/time callers and callback bodies
  are not closed. CMake uses C11 extensions (lines 21–23), common timer source
  (line 201) and Windows-specific defines (line 207); configure selects gnu11
  (`r1:configure.ac:37`). None establishes a verifier-supported compilation.
- Requirement: **inferred**, owner authority/approval unresolved. Candidate
  safety contract: an eligible due timer enters ready state once; stopping or
  restarting another ready timer before selection removes that old pending
  delivery; dispatch selects only still-ready timers and rearms repeating
  timers before executing their callback. The public description
  `r1:include/uv.h:1012`–1014 says future wakeup, not this full contract.
  Owner must settle reentrancy, lifetime/close rules, clock progression and
  wrap ordering. Do not infer “every due timer must fire this pass.”
- Property/domain: proposed separate finite model with three distinct live
  timer identities, one serialized loop, explicit heap-set/ordered ready-list,
  active flags, callback presence, repeat/deadline and selected timer state.
  Include start(null-cb/closing), valid start/restart, stop(active/ready/idle),
  again(zero/nonzero repeat), due extraction and callback actions that stop or
  restart another timer. Preconditions: properly initialized handles/loop,
  valid lifetimes and queue membership; no unapproved concurrent operations or
  recursive loop dispatch. These are proposed model boundaries, not proven
  real-world guarantees; if such inputs are permitted, scope must be revised.
  At transition boundaries each timer occurs at most once in heap and at most
  once in ready, never both; heap membership agrees with active flag for this
  modeled timer-only slice. Dispatch must consume a current ready entry;
  cancellation/restart removes its pending occurrence before another selection.
  Preserve pointer-free membership correspondence explicitly. Counterexamples:
  duplicate membership, dispatch after cancellation without a fresh eligibility
  event, or active/count imbalance. Model numeric domains and wrap transitions
  must be settled in W1; do not silently exclude counter rollover, deadline
  saturation, clock changes or relevant reentrancy to obtain a pass. No
  unbounded numeric or temporal guarantee is proposed.
- Method: `tla-state-machine-safety` 1.0.0, bundled `references/tlc.md`.
  Requires accepted separate abstraction, finite constants and implementation
  correspondence review. Compatibility **unknown** until TLC/TLA+ tools/Java
  and model configuration are pinned. Exact conditional assurance: “Invariant
  checking for the explored finite TLA+ model and recorded configuration,
  subject to constraints and complete exploration.” No catalog hard exclusion
  exists, but that does not make correspondence automatic. Not C implementation
  correctness, unbounded theorem, liveness, heap safety or platform support.
- Alternatives: source-only transition/requirement table first; native stateful
  tests later observe actual schedules but are not exhaustive model checking.
  Defer `tla-concurrency-liveness`: fairness/progress promises and scheduler
  boundary unresolved. Defer CBMC for the event-loop slice: pointer/queue/callback
  closure is incomplete; catalog hard-excludes concurrency, assembly and FFI.
  Serialized callbacks alone are not proof of absence of those exclusions.
  Pure due-in arithmetic could be reviewed separately, but no quota-driven
  second task is needed before lifecycle intent is resolved.
- Dependencies/readiness: approved safety requirements and abstraction,
  permitted-operation/lifetime/time domains, queue/platform/callback scope,
  compatibility and actual grants. Evidence work is possible in current slice;
  model writing/execution and any target test changes remain separately blocked.

## Actionable handoff

| Work ID | Next bounded task / proposed files | Depends on | Approval and readiness | Acceptance / evidence required |
|---|---|---|---|---|
| W1 | Read-only `timer-transition-contract.md` outside target, linking start/stop/again/extract/dispatch to lines; list missing boundaries | O1 | Current evidence scope only; owner decisions and additional source scope unresolved | Include stop/restart of another ready timer, repeat rearm order, rejection without mutation, numeric-wrap/reentrancy questions, and approved versus inferred requirements |
| W2 | Read-only `timer-model-invocation.md` command-selection artifact outside target | W1 and acceptance of a separate finite abstraction | No tool invocation approval | Pin TLC/TLA+ tools/Java, exact arguments, model/config paths, isolated working directory, finite constants, constraints and completion criteria without running code |
| W3 | Conditional separate `TimerSafety.tla` / `TimerSafety.cfg` outside source roots | W1/W2, actual model-write/execution grants and isolation | Blocked; neither owner grants nor supported configuration established | Retain exact source/model/config identity, correspondence table, versions/commands, numeric abstraction justification, explored states, complete output/failures and completeness status; finite-model result only |

W2 must resolve invocation before W3 execution; it is not execution permission.
Reject an abstraction that omits a relevant approved input merely to finish.
Future native-test work needs separate expanded test/caller scope and approval,
not an assumed grant based on filenames.

## Review and limitations

Manual review of citations, r1 assignment, guide provenance and dependency order;
no verification was performed. No prior outputs/private mapping read; no target
execution, builds/tests/imports/proof commands, network, source writes or agents.
One shared metadata command failed (`python` missing, exit 127); Python 3 was
used only for metadata. The final Git identity matched the selected scope.
This advisory does not establish compatibility, recommendation correctness,
exhaustive coverage, safety of execution or approval.
