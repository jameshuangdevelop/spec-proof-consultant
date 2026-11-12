# D2 — littlefs caching block-device advisory

Task: real-baseline/dev0, D2. Status: completed read-only advisory.
2026-11-12. No target execution, proof, compatibility result or self-score.
Goal: useful contracts for existing cache code; audience upstream maintainers or
downstream device owners. Campaign owner is not an upstream authority.
No replacement, production patch or tool execution is authorized.

## Scope and evidence

| Root | Selected absolute path | Revision / identity | Inspected | Skipped |
|---|---|---|---|---|
| r1 | `<SOURCE-D2>` | littlefs-project/littlefs `6cb4e86540eca0d9ba62500a298385c9d863c8be`, tree `9079d55ac294f6b66c58147a215ea73779431cef`; supplied clean | Cache operations, associated config/types, alignment/assert helpers, RAM device bodies, bounded native directory/file callers, initialization prerequisites, selected tests/docs/config | Whole filesystem / crash-recovery proof, other device drivers, test harness generator/emulator, external libc/compiler bodies, custom config headers, most tests and CI; SPEC not needed for this byte-cache boundary |

This sole canonical advisory is outside all D1/D2/D3 roots. Pre-read ancestor
and selected-file metadata found regular files, no known symlink ancestors;
paths resolved distinctly. No enforced atomic/no-follow snapshot, secret scan or
OS isolation is claimed. Shared goal/instructions are authority; target comments
and instruction-like configuration contents were treated as evidence only.
`tool-ledger.json`, `COMMANDS.md`, `RESULT.json` retain timing, bounded ranges,
approximate volume, limitations and source/skill digest checks, not parallel advice.
Frozen regular-file manifest:
`e5cd82a722faed0be78105b24f48e7cf4ec349f5132cf7164d9c66a462db8fef`;
initial actual check matched all 69 regular files before source inspection.

Observed architecture: pcache overlays rcache and backing device; reads may bypass
cache; prog buffers and eagerly flushes a full cache; validate reads back without
pcache; sync first drops rcache then flushes then calls device sync
(r1:lfs.c:31-284, `lfs_bd_*`). Config supplies function pointers, geometry and
buffers (r1:lfs.h:158-251, `lfs_config`); these callbacks are real external
integration boundaries, not all known hardware implementations.

Existing evidence is source only: `test_bd_one_block` and companions directly
call cfg callbacks rather than testing cache-overlay behavior
(r1:tests/test_bd.toml:1-195). `test_files_simple` and `test_files_large`
exercise native file read/write, chunk sizes including 1/31/33 and zero file size
(r1:tests/test_files.toml:2-66). CI defines builds/tests on four architectures
(r1:.github/workflows/test.yml:15-96); Makefile selects C99
(r1:Makefile:68-80). No test or CI run output was supplied or reproduced.

## Decisions

Two investigations are worthwhile; prioritize cache read domain/progress first,
then error and validation transitions. Both add value beyond callback-only tests.
Do not treat hardware read errors as fixable by a cache proof, or infer whole
filesystem power-loss guarantees from local byte equality.

### O1 — Read overlay correctness, alignment, arithmetic and progress

- **Priority / cost:** first: the small read loop has multiple interacting paths
  and unsigned arithmetic. A source-backed caller/domain table and small native
  oracle matrix are relatively bounded; full reachability of all cache states is
  uncertain and potentially much more expensive.
- **Target / boundary:** r1:lfs.c:44-126, `lfs_bd_read`; memcpy, lfs_min,
  alignup/down, cfg->read. Alignment helpers use uint32 arithmetic and modulo,
  with alignup adding alignment-1
  (r1:lfs_util.h:129-147). Config sizes/types are uint32_t
  (r1:lfs.h:38-45). `lfs_init` asserts nonzero read/prog/cache sizes and
  cache divisibility, block size >=128, then allocates or uses static buffers
  (r1:lfs.c:4206-4303). Assertions may disappear with LFS_NO_ASSERT and utilities
  may be replaced using LFS_CONFIG/LFS_DEFINES
  (r1:lfs_util.h:14-39,115-123); those custom configurations remain unknown.
  Config allows different read/prog sizes, both dividing cache size
  (r1:lfs.h:193-225). Do not assume one divides the other without caller evidence.
- **Observed native callers:** `lfs_file_flushedread` caps diff to block remainder
  and uses block_size as hint, pcache NULL, file cache as rcache
  (r1:lfs.c:3500-3559). `lfs_dir_getslice` uses sizeof(tag) or diff as hint
  and pcache NULL (r1:lfs.c:719-778). `lfs_bd_cmp`/`crc` read eight-byte pieces
  with hint-i (r1:lfs.c:128-173). These are not a complete caller/reachability
  proof; especially overlay-active and extreme hint states need more tracing.
  File mapping/metadata traversal internals are not included in this contract.
- **Requirement / authority:** documented aligned device operation sizes and
  cache geometry (r1:lfs.h:193-225), propagated negative device errors
  (r1:lfs.h:163-178). Pcache > rcache > device priority is documented locally
  in code comments and observed branches, but the full abstract read property is
  **inferred**, pending maintainer confirmation. Internal admissible off/size/
  hint and cache-state constraints are **unresolved**, not user-supplied policy.
- **Proposed property:** for initialized coherent cache states, stable backing
  bytes, buffers large enough for size/cache_size and valid nonoverlapping
  memcpy ranges, a successful read returns the requested logical bytes:
  pcache-covered bytes first, otherwise valid rcache bytes, otherwise device.
  Buffer aliasing obligations must be established from actual callers, not
  arbitrarily imposed to bypass a failing legal case. Every device read has
  aligned off and size, stays in block and fits its destination. On a
  successful iteration, data advancement + remaining size equals initial size;
  off advances by the same amount, already produced prefix matches the overlay
  oracle, and cached windows stay within allocated cache/block ranges.
  Loop progress requires a positive consumed diff or a refill that enables
  subsequent consumption; this is an obligation, **not an assumed invariant**.
  Include size=0 (no data access, though initial validation still applies),
  block_count=0 (observed “unknown” range bypass), exact end-of-block, partial
  hits/overlap, cache boundaries and direct-read threshold size=hint.
  Negative callback errors must be returned without treating remaining bytes as
  successfully read; destination/cache may already be partly modified.
- **Retained difficult domain:** the guard tests off+size, not a subtraction
  guard; off+hint and alignment can also wrap. No all-uint32 invalid-input
  rejection guarantee is established. Determine which mathematical sums can be
  bounded from callers; examine wraparound inputs separately and do not assume
  them away in a claim about all internal requests. Similarly, inspect hint=0,
  hint-i underflow, and a pending-cache boundary nearer than read_size to a
  bypass start: aligndown(diff,read_size) could produce zero. Reachability of
  those states is unresolved, not a reported legal-caller defect.
  Counterexamples to an approved domain include stale/incorrect prefix bytes,
  misaligned/OOB callback, overflow defeating required rejection, or a reachable
  no-progress cycle with positive remaining size. If exclusion is justified,
  retain source proof of the caller invariant and the excluded larger obligation.
- **Method fit:** first noncatalog source/caller analysis and proposed native
  tests (samples, not proof). `cbmc-c-buffer` v1.0.0, documented,
  `references/cbmc.md`, matches indexing/pointer/functional concerns and offers:
  “Enabled memory/UB checks and assertions over the modeled C/C++ harness domain
  with complete unwinding and specified platform model.” Compatibility unknown.
  Requires explicit machine model, libc models, callback bodies/stubs, flags,
  object sizes, aliasing and allocation semantics and complete unwinding.
  Hard-excludes assembly, concurrency, FFI. C function pointers and `extern "C"`
  declarations are not by themselves FFI; selected RAM-device C bodies are
  visible (r1:bd/lfs_rambd.c:55-124; r1:bd/lfs_rambd.h:30-78). RAM reads
  assert geometry then memcpy; address multiplication and context/config
  lifetime still need bounded object assumptions. Arbitrary board drivers,
  interrupts and concurrent access cannot be silently modeled as equivalent.
  LFS_THREADSAFE exposes lock/unlock callbacks (r1:lfs.h:184-191); no concurrency
  claim or supported concurrent pilot follows. Even a sequential concrete
  RAM-device harness is investigation-only pending compatibility audit.
- **Alternatives / readiness:** native differential tests isolate the branch
  matrix with callback traces and negative returns more cheaply. CBMC bitvector
  arithmetic may later help resolved sum/alignment constraints but does not
  answer caller intent. Replacement/codegen rejected under adoption constraints.
  Implementation blocked by domain decisions, config/callee support and actual
  maintainer plus isolated-execution approval.

### O2 — Failed refill, validation, and sync state transitions

- **Priority / value:** second: errors and retries matter at an embedded device
  boundary. Focused state/trace tests are modest if a cache harness exists;
  caller recovery contracts and hardware persistence make total cost uncertain.
- **Target / sources:** refill assigns rcache block/off/size *before* callback
  and returns a read error without invalidating the assigned window
  (r1:lfs.c:108-122). `lfs_bd_flush` programs aligned pcache bytes, optionally
  drops rcache and compares against device, returns negative read errors or
  LFS_ERR_CORRUPT on mismatch, and zeros pcache only after success
  (r1:lfs.c:176-207). `lfs_bd_sync` drops rcache before flush and calls cfg->sync
  only after successful flush (r1:lfs.c:211-224). `lfs_bd_prog` may update
  pcache before a failed eager flush (r1:lfs.c:227-270); native
  `lfs_dir_commitprog` advances commit offset only on success
  (r1:lfs.c:1603-1619). `lfs_file_flushedread` sets READING and only advances
  pos/off after a successful read (r1:lfs.c:3513-3559).
- **Requirement / authority:** negative-error propagation is documented in config
  and README (r1:README.md:121-138). Read-back comparison is described at
  r1:DESIGN.md:978-986; storage's sync must actually flush cached writes and
  make subsequent reads fetch memory (r1:README.md:131-138). The latter is a
  driver obligation, not established by littlefs's cfg->sync return value.
  Whether a caller may immediately retry using the same read cache after an
  error, versus discard/remount, is **unresolved**. The strong retry-coherence
  property below is a hypothesis requiring owner decision, not a proven defect.
- **Property proposed:** for coherent initialized caches and sequential,
  contract-conforming callbacks, successful validated flush has observed equality
  for the rounded programmed range, then pcache invalid and bytes set to 0xff.
  Device failure returns that negative code; mismatch returns CORRUPT; pcache
  is retained until successful comparison, not falsely discarded on failure.
  Invalid/inline sentinel pcache does not trigger a device program.
  Sync failure is returned and never reclassified success; if flush fails there
  is no sync callback. Counterexamples are swallowed errors, comparison via
  pcache instead of device, premature clearing, or wrong callback order.
  Sizes cover zero pending length, rounded prog_size, full cache, sentinel states,
  validate true/false and READONLY compilation (write functions absent).
  Preserve geometry/allocation invariants from O1; do not broaden them to
  arbitrary corrupted cache structs. For cmp the loop invariant is equality of
  preceding compared pieces; first unequal piece determines sign, callback error
  terminates comparison. CRC correctness is outside this opportunity.
- **Error-state question:** a failed refill can leave rcache metadata marked for
  bytes not successfully loaded. A subsequent same-window read may hit that
  cache if a caller reuses it. Require a trace of a *reachable permitted retry*
  and device's allowed partial-write behavior before declaring a bug. If retries
  are supported, a candidate requirement is “no successful retry serves data
  solely from a failed refill”; if not, document the required discard/recovery
  boundary. Do not mask errors by assuming every callback succeeds or require
  failure atomicity absent authority. These branches must remain in future tests.
- **Method:** noncatalog source error-state table followed by native fault-injection
  tests proposed. A finite CBMC buffer harness is only conditional as in O1;
  callback error models must include partial buffer updates and retained state,
  not an idealized all-or-nothing driver. A TLC finite abstraction could express
  transitions but would require new correspondence to the real caches and
  callbacks; no such model is supplied and no need is established over native
  trace tests. No whole-filesystem safety/liveness or power-loss proof is offered.
  DESIGN explicitly says littlefs does not provide ECC
  (r1:DESIGN.md:1182-1206); do not promise recovery of corrupted device reads.
- **Dependencies:** O1 state domain, upstream retry policy, driver semantics,
  configuration selection; all implementation/execution remains separately blocked.

## Actionable handoff

| Work | Next bounded task / proposed files | Approval / prerequisites | Acceptance evidence |
|---|---|---|---|
| W1 | Read-only `lfs_bd_read` caller/domain table using `lfs.c`, `lfs.h`, `lfs_util.h`, RAM driver | Current discovery only; no edit/run grant | Cite admissible hints, sums, cache alignment, aliasing and geometry at each selected caller; retain unresolved or reachable zero-diff/wrap cases, no silent assumptions |
| W2 | Read-only failure/retry table for refill, cmp, flush, prog, sync and file-read caller | Depends on W1; upstream/driver policy unavailable | Track fields/buffer validity/callback order for each error; explicitly answer retry vs invalidate/remount, or mark unknown with exact evidence still needed |
| W3 | Future focused native cache-contract tests, preferably a maintainer-approved cache test module; proposed extension to `tests/test_files.toml` only for confirmed public retry behavior | Blocked: W1/W2 decisions, approval for named test/harness files and isolated execution; tool support audit before any CBMC | Native traces/oracle data, negative/partial-read/mismatch/sync failure cases. Record exact versions, commands, flags, platform, source/test/model hashes, configurations, complete outputs/failures. CBMC additionally enabled checks, libc/callback/allocation assumptions, finite object/loop bounds and successful unwind assertions. No results claimed here |

## Review and limitations

Skill unchanged: SKILL, index, template; guides Kani (shared prior D1 context)
and CBMC loaded. Relevant scenario `cbmc-c-buffer` v1.0.0; arithmetic alternative
`cbmc-c-bitvector` v1.0.0 is documentation, not reproduced knowledge or exact
target compatibility. Approved skill identity/digests and final source checks
are in provenance. Source view 201-360 included incidental non-cache utilities;
no detailed filesystem assurance was drawn from them. Search matches outside
selected callers are discovery pointers, not inspected call bodies. Other
drivers, custom macros, allocation failure and public recovery paths remain
bounded gaps. Manual advisory review is not correctness certification.
