# Proof-readiness advisory — D2 / dev-confirm-ee8d0e6

Status: completed advisory; no target execution, proof or compatibility result.
2026-11-12. Task real-baseline/dev-confirm. Audience: littlefs maintainers and
downstream block-device owners. Prefer existing production cache operations;
no source replacement or repair is authorized. The campaign owner authorizes
read-only discovery, not upstream requirements or implementation.

## Scope and evidence

| Root | Selected absolute root | Revision / dirty state | Inspected | Skipped/unknown |
|---|---|---|---|---|
| r1 | <SOURCE-D2> | littlefs-project/littlefs; 6cb4e86540eca0d9ba62500a298385c9d863c8be; tree 9079d55ac294f6b66c58147a215ea73779431cef; clean Git status | Cache helpers/read/cmp/crc/flush/sync/prog/erase; config/types; default alignment helpers; full RAM backend/header; selected initialization, metadata/file/CTZ/relocation/migration caller ranges; tests/test_bd 1–145 and test_files sync case; README/DESIGN excerpts; Makefile 1–100; CI 1–180 | Whole filesystem/format invariants, allocator/CRC body, full migration, all callers' upstream data provenance, hardware callback implementations, custom utility overrides, test runner/generator, other backends, SPEC format details and remaining CI/test cases |

This report is outside **all three** selected roots. Supplied regular-file
inventory paths were checked for symlink components, regular types and hashes
before source reads; metadata search found no symlinks or nested .git outside
the selected roots' own .git. Known path boundaries are not an atomic read
sandbox or secret detector. COMMANDS.md records operations, limits and
before/after hashes/Git metadata. No target command ran.

## Decisions

Two bounded contract investigations are useful; do not jump to a
whole-filesystem/power-loss proof. The actual configured device is a material
boundary: callbacks at `r1:lfs.h:157-200`, `lfs_config`, are ordinary C function
pointers, not evidence of FFI. RAM callback bodies are available at
`r1:bd/lfs_rambd.c:56-131`, `lfs_rambd_read/prog/erase/sync`; they memcpy,
erase is a no-op, sync is a no-op. They neither model flash bit transitions nor
faulting/durable hardware. `r1:README.md:131-135` requires sync to flush cached
writes and ensure subsequent reads fetch memory. A RAM-only result would not
discharge that obligation.

Existing evidence is substantial but different in scope. `r1:tests/test_bd.toml:1-29`,
`test_bd_one_block`, directly tests callbacks (its header explicitly says not
littlefs); later two/last-block cases in the inspected range do likewise.
`r1:tests/test_files.toml:364-450`, `test_files_reentrant_write_sync`, specifies
reentrant sync/readback cases across chunk/inline dimensions. CI
`r1:.github/workflows/test.yml:15-110` declares multi-architecture tests and
coverage, explicitly excluding more aggressive power-loss tests from that
coverage collection. None of these artifacts is a supplied or reproduced pass.
Use them before inventing another framework or claiming no coverage exists.

### O1 — Read overlay, alignment and progress contract (priority 1)

- **Value/effort:** cache reads sit underneath metadata/file reads; wrong cache
  precedence silently returns incorrect bytes. A contract/caller table is
  small; covering all legal cache states/arithmetic is materially harder.
  Incremental value is explicit overlap and progress obligations rather than
  more raw-device roundtrip tests.
- **Target/call boundary:** `r1:lfs.c:31-126`, `lfs_cache_drop/zero`,
  `lfs_bd_read`: pending program cache takes priority over read cache, then
  aligned bypass or refill. Helpers `r1:lfs_util.h:127-145`,
  `lfs_min/max/aligndown/alignup`, operate on uint32_t; alignment-up adds before
  aligning. Cache fields at `r1:lfs.h:371-376`, `lfs_cache_t`; uint32 offset/size
  types at `r1:lfs.h:38-46`.
  Immediate consumers include cmp/crc (`r1:lfs.c:128-173`),
  metadata tag/slice reads (`r1:lfs.c:719-779`, `lfs_dir_getslice`),
  file reads (`r1:lfs.c:3500-3559`, `lfs_file_flushedread`),
  CTZ pointer reads (`r1:lfs.c:2887-2915`, `lfs_ctz_find`) and relocation
  (`r1:lfs.c:3287-3317`, `lfs_file_relocate`).
  File reads use block-size hints and clip to the current block; metadata
  reads use tag/diff hints; cmp/crc subtract their loop position from hint.
  Caller-site search also found migration reads
  (`r1:lfs.c:5402-5407`, `lfs1_bd_read`). This inventory is not a proof of
  all callers' reachable states. CRC body and broader metadata arithmetic are
  uninspected, so no native claim includes those complete call chains.
- **Requirement/class/authority:** documented config sizes/callback error
  propagation in `r1:lfs.h:157-225`, `lfs_config`; cache_size is a multiple of
  read/prog sizes and a factor of block_size; block_size is a multiple of both.
  `r1:lfs.c:4206-4247`, `lfs_init`, asserts nonzero read/prog/cache sizes and
  divisibility, block_size>=128. Static cache buffer capacities are documented
  at `r1:lfs.h:244-250`. Overlay correctness/progress is an **inferred** internal
  contract from the implementation/callers, not an approved public guarantee.
  Exact allowed hints, arithmetic maxima, cache-state validity and aliasing
  need maintainer/downstream confirmation. No authority to narrow them is granted.
- **Proposed property:** a well-formed sequential device/config and coherent
  caches, valid destination of requested length disjoint from cache buffers
  unless supported overlap is established; optional pcache; nonnull rcache.
  For an accepted in-block request, each successful returned byte equals the
  pending pcache byte where covered, else coherent rcache/device byte. No output
  byte beyond requested size is written; every device read has aligned offset
  and size and stays within the block. The callback's first negative result is
  propagated; previously copied output may be partial, not transactionally
  rolled back. Invalid block or out-of-block request should return CORRUPT
  according to the observed guard, with block_count==0 meaning the upper block
  bound is not yet known. This is not a guarantee of sensible physical block
  IDs when count is zero.
  Loop invariant: copied+remaining=original size, off advances by copied count,
  copied prefix matches the overlay, cache windows/buffer extents are valid.
  Progress requires positive consumed diff, or a successful refill that permits
  positive consumption on the next iteration. Include zero size at block end,
  fully cached, uncached, overlapping pcache/rcache, bytes before/at/after each
  window, read/cache boundaries, exact block end, and callback errors on either
  direct or refill paths.
- **Counterexamples/retained obligations:** wrong precedence, invalid memcpy,
  unaligned device call, zero-progress cycle, or wrapped uint32 guard/refill
  calculation. `off+size`, `off+hint`, alignment-up, and cache-window end
  arithmetic must not simply be assumed nonwrapping to claim all legal inputs.
  A source-derived **hypothetical** private-helper call with aligned off,
  0<size<read_size and hint=0 can refill zero bytes when caches miss:
  direct bypass is unavailable, alignup(off+0)==off, so size does not shrink.
  It is not a reproduced bug or established reachable filesystem input.
  Determine whether actual callers establish the needed hint/progress invariant;
  retaining hint=0 in the investigation is essential, not an excuse to suppress
  a failure. Likewise, resolve representable out-of-range sums before promising
  universal rejection. The whole caller-validity claim remains blocked.
- **Method/fit:** noncatalog source/caller-contract audit first.
  `cbmc-c-buffer` 1.0.0, bundled `references/cbmc.md`, fits actual indexing and
  finite buffer correctness; assurance: enabled memory/UB checks and assertions
  over the modeled C/C++ harness domain with complete unwinding and specified
  platform model. `cbmc-c-bitvector` 1.0.0 can investigate the arithmetic:
  bit-precise enabled checks/assertions in the modeled domain with complete
  unwinding and explicit platform assumptions. Neither proves unbounded loops,
  unmodeled devices or portability across unspecified machines.
  A future static-allocation RAM-backed pilot could use one 128-byte block,
  cache 16, read/prog divisors of 16, bounded requests/state sequences; it would
  not cover all config sizes or the uint32 extremes, which need a retained
  separate arithmetic/caller obligation.
  Exact CBMC release/flags/libc/function-pointer support is unknown.
  Hard exclusions: assembly, concurrency, FFI. An unseen hardware callback is
  unknown, not automatically FFI; actual foreign bodies would exclude the
  native pilot. No ready/supported pilot is claimed.
- **Alternatives/prerequisites:** instrumented native cases can sample overlay
  and callback traces, not exhaust legal states. They likely cost less initially.
  Do not replace production with a model implementation. Resolve intent,
  reachable-state/config/callee boundaries, target data model and approvals first.

### O2 — Failure-state and flush/sync protocol (priority 2)

- **Value/cost:** prevents conflating “negative error returned” with safe retry
  or durable success. Small trace contracts are cheap to write; fault-state
  reachability and caller recovery are higher uncertainty. This complements
  reentrant sync tests rather than claiming they are absent.
- **Target/boundary:** `r1:lfs.c:177-224`, `lfs_bd_flush/sync`, program an
  aligned pending range, optionally drop rcache and read/compare, clear pcache
  only after successful validation, and call sync only after flush succeeds.
  `r1:lfs.c:228-275`, `lfs_bd_prog`, eagerly flushes full pcache.
  `r1:lfs.c:3397-3415`, `lfs_file_flush`, handles CORRUPT via relocation;
  `r1:lfs.c:3434-3451`, `lfs_file_sync_`, propagates flush/sync errors.
  Read refill sets cache metadata *before* callback success
  (`r1:lfs.c:108-122`, `lfs_bd_read`), so post-error cache validity cannot be
  inferred merely from the return code.
- **Requirement:** documented error propagation at `r1:lfs.h:163-182` and
  `r1:README.md:121-135`; write-readback rationale at
  `r1:DESIGN.md:977-987`; respect for device errors but no built-in ECC at
  `r1:DESIGN.md:1195-1206`. Inferred: the precise helper trace/state transitions.
  **Unresolved:** which objects may be retried after each error and whether
  invalidating failed refill metadata is a callee or caller responsibility.
  Do not invent a promise that a failed read leaves output or caches unchanged.
- **Proposed domain/property:** same valid config/storage boundary as O1,
  plus valid pending pcache with aligned off, size<=cache_size and aligned-up
  program span within block/buffer, nonaliasing cache descriptors/buffers,
  validate true/false, and empty/null/inline sentinels. Preconditions themselves
  need caller evidence, not just assumptions in a harness. With a real pending
  block and successful prog, validate=true compares against device (not pending
  pcache); mismatch returns CORRUPT, negative read/prog returns that error,
  pcache is not zeroed on these failures. Successful flush zeroes cache bytes
  to 0xff and drops its block; absent/inline pending blocks do not program.
  Sync drops rcache, flushes, and invokes device sync only after flush success;
  a sync error is returned even though pcache may already be cleared.
  State invariant: dirty cached bytes remain available until successful flush,
  but this alone does not prove rollback, retry safety or durability.
  On read error, explicitly classify partially changed output and cache metadata;
  a subsequent cache hit without successful fill is a counterexample to any
  proposed *safe automatic retry* contract unless a caller invalidates/abandons
  that cache first. Also challenge false readback success, lost dirty bytes,
  sync invoked after failed flush, and incorrectly equating validation with
  persistence. No loop invariant beyond O1/cmp's processed-prefix invariant is
  needed for the straight-line flush/sync protocol.
- **Method/assurance:** source-state/trace table and proposed native injected
  errors first, **non-proof**. Conditional CBMC buffer scenario as O1 only
  after modeling a named callback contract; a nondeterministic fault model is
  an explicit abstraction, not observed RAM/hardware behavior. Actual RAM
  callbacks never produce these error traces and sync has no persistence model.
  Need both abstraction-to-callback obligations and caller recovery evidence.
  Whole filesystem power-loss and concurrent access remain outside this task.
- **Alternatives/readiness:** no new TLC model now: it would add finite
  abstraction/correspondence work without answering who may retry the actual
  cache first. No Dafny replacement: adoption is not authorized. Unknown recovery
  intent and device semantics block implementation, not bounded source inquiry.

## Actionable handoff

| Work | Next bounded task / proposed files | Dependencies / actual approval | Acceptance / evidence |
|---|---|---|---|
| W1 | Read-only contract table for lfs_bd_read and immediate callers in lfs.c, lfs.h, lfs_util.h | Present read-only campaign grant only; owner authority for helper domain unresolved | For each caller: hint relation, overflow bounds, coherent cache/alias obligations, error invalidation/retry path, or explicit unproved obligation; include O1 counterexamples |
| W2 | Read-only flush/sync/error transition table in the same scope and supplied RAM device | Owner/downstream resolves retry and durability contracts; broader recovery inspection needs separate scope if necessary | Trace per prog/read/mismatch/sync failure, dirty-cache disposition, caller handling and backend-vs-real-device differences cited |
| W3 | Separately proposed focused test fixture / external CBMC harness against unchanged lfs.c (no implementation now) | Blocked: W1/W2, named owner approval, pinned release/compiler/machine model, callback/libc support, explicit write/execution authority and disposable isolation | Source/config/harness/model hashes; exact commands/versions/flags/includes, check inventory, allocation/error semantics, complete output/failures, bounds and successful unwind checks; report any incomplete exploration, residual domains and correspondence |

Configuration prerequisite: `LFS_CONFIG`/`LFS_DEFINES` can replace defaults
(`r1:lfs_util.h:14-39`); LFS_NO_ASSERT removes assertions
(`r1:lfs_util.h:111-119`), so they are not release input validation.
LFS_READONLY removes write paths; LFS_THREADSAFE adds lock callbacks
(`r1:lfs.h:184-192`) without proving concurrency correctness.
Makefile (`r1:Makefile:68-93`) declares C99/optimization/debug flags but does
not pin a verifier model. Static buffers can avoid allocator bodies in a
*named smaller pilot*, not establish allocation/error correctness generally.
No native concurrency claim is permitted by the loaded CBMC scenarios.

## Review and limitations

No bugs, safe retries, proof, exact compatibility or runtime were established.
Citations distinguish production, tests and documented/inferred/unresolved
requirements. There is no new catalog knowledge/promotion. Source identity was
rechecked for handoff. Large lfs.c was intentionally not dumped; searched
caller sites are discovery evidence, not complete semantic call-graph coverage.
SPEC format, ECC, CRC computation, allocation, migration and power-loss protocol
are outside these detailed properties; including them would need new bounded
scope and correspondence work, not a broader assurance label.
