# D2 — littlefs caching block-device advisory

Task real-v2/dev0; freshcontextv2ordinal3. 2026-11-12.
Status: completed read-only discovery, no target execution, proof, self-score,
implementation or upstream approval. Audience: filesystem/device integration owners.
Goal: contracts on existing lfs_bd_read and its cache/callback boundary, not a
replacement or a whole-filesystem/power-loss guarantee.

## Scope and evidence

| Root | Absolute root | Identity | Inspected | Skipped / unknown |
|---|---|---|---|---|
| r2 (D2) | <SOURCE-D2> | littlefs-project/littlefs; commit 6cb4e86540eca0d9ba62500a298385c9d863c8be; tree 9079d55ac294f6b66c58147a215ea73779431cef; detached/clean before | Cache operations lfs.c:1-325, immediate cmp/crc/flush callers; bounded metadata and file-read callers, init/deinit; associated header/types/config, utility helpers, RAM device, test excerpts, configuration/docs | Full metadata/CTZ/filesystem, public lock wrapper bodies, actual hardware callbacks, test runner/generator, most test cases and CI workflow remainder; no transitive whole-filesystem coverage |

Output is outside all three selected roots in the new dev0-ee8d0e6 directory.
Boundary precheck found no known symlinks or nested Git roots. No-follow,
atomicity, secret detection and OS sandbox enforcement are not claimed.
COMMANDS.md logs loaded ranges and estimates; BEFORE-AFTER.json records identity.
Discovery: 27 source read/search operations, conservative source-character bound
below 85,000; estimates are not enforced tool limits.

Observed architecture: lfs_bd_read is **static internal production C**, not a
public API or test helper (r2:lfs.c:44-126). Cache priority is program cache then
read cache then configured device callback. `lfs_bd_cmp` and `lfs_bd_crc` use
8-byte temporary chunks (r2:lfs.c:128-175). Metadata reads pass sizeof(tag) or
requested diff as hints (r2:lfs.c:719-790, `lfs_dir_getslice`); file data reads
pass block_size, and return errors before cursor advancement
(r2:lfs.c:3500-3578, `lfs_file_flushedread`, `lfs_file_read_`).
These callers do not exhaust the grep-discovered call graph.

Existing evidence is not a pass: tests/test_bd.toml explicitly tests the supplied
device rather than littlefs caching (r2:tests/test_bd.toml:1-120,
`test_bd_one_block`, `test_bd_two_block`). File tests include EOF, varied
sizes/chunk sizes and inline modes (r2:tests/test_files.toml:2-66).
Build config is C99 (r2:Makefile:70-76); tests are transformed/runner-linked
(35-50), not directly runnable TOML. CI defines architecture jobs and test/coverage
commands (r2:.github/workflows/test.yml:15-117); neither scripts nor results were
executed or supplied. DESIGN explicitly delegates ECC to the device and respects
reported errors (r2:DESIGN.md:1182-1206). SPEC is an on-disk specification, not
proof of cache behavior (r2:SPEC.md:1-29).

## Decisions

Two opportunities. First establish a small, realistic cache read contract and
its arithmetic/caller obligations. Second resolve the failure/retry boundary,
which a happy-path RAM-device check cannot settle. No confirmed bug or production
repair is claimed. Native contract tests are the preferred near-term method.

### O1 — Overlay read semantics, aligned callbacks and progress

- **Priority / value:** high; cache mistakes can return wrong data or issue invalid
  device accesses. Moderate contract/harness design cost; finite-check cost
  unknown. Adds branch/overlay assertions beyond broad file round trips.
- **Target / call boundary:** r2:lfs.c:44-126, `lfs_bd_read`; default
  `lfs_min`, `lfs_aligndown`, `lfs_alignup` at r2:lfs_util.h:125-141;
  memcpy and configured `read`. RAM callback body is available, not an invented
  unknown FFI: r2:bd/lfs_rambd.c:55-73, `lfs_rambd_read`, backed by context and
  RAM config (r2:bd/lfs_rambd.h:30-52). It checks alignment/range then copies
  memory. The actual deployment's callback and libc/tool models remain unknown.
  Initialization asserts nonzero read/prog/cache sizes and divisibility at
  r2:lfs.c:4226-4251, installs/allocates buffers and invalidates caches at
  4279-4304. Cache drop/zero only invalidate block, not all metadata
  (r2:lfs.c:31-42).
- **Requirement / authority:** documented config requires read operations in
  read_size multiples, block_size a read/prog multiple and cache_size a multiple
  and factor of block_size (r2:lfs.h:194-224); error propagation is documented
  at 157-162. Overlay priority is **inferred intended behavior**, supported by
  implementation comments, not approved by the campaign. No upstream or actual
  device owner has signed off the proposed proposition.
- **Domain / preconditions:** configured C99 deployment, uint32_t offsets/sizes
  (r2:lfs.h:38-45), valid lfs/cfg/cache pointers and allocated cache_size buffers,
  active cache intervals within the selected block and initialized bytes;
  invalid-block sentinels must not be interpreted as valid content.
  Output is writable for requested size and does not overlap source caches or
  device storage where memcpy would be undefined. Stable device data during a
  sequential read, conforming callbacks return 0 after writing requested bytes
  or a negative error; no unmodeled concurrent modification.
  Those are proposed caller/environment obligations to trace, not all proven
  from types or automatically valid for every public caller.
- **Proposition:** for mathematical off+size within block and a valid block
  (or internal block_count=0 phase), successful output at each requested byte
  equals pcache if its matching valid interval covers that byte, otherwise
  rcache if its valid coherent interval covers it, otherwise device content.
  No writes outside destination/read-cache storage; pcache/device bytes unchanged.
  Each issued device request is read_size-aligned, within block/device range and
  allocated buffer. Return the first negative callback error without further I/O.
  Empty requests do no copying/I/O, but still undergo the initial range guard.
  Invalid checked ranges return LFS_ERR_CORRUPT before callbacks. Do not equate
  that checked guard with safe rejection of all overflowing uint32_t arguments.
- **Invariant / boundaries:** loop conserves initial requested size =
  copied+remaining; off=initial_off+copied, data=initial_data+copied; copied prefix
  agrees with the overlay; every memcpy/directed read has positive progress, or
  a successful refill establishes a cache window covering current off so the next
  iteration progresses. Cases: zero length, exact block end, block_count=0,
  invalid block, empty/disjoint/overlapping caches, cache boundary at off,
  program priority, aligned bypass versus unaligned refill, and small sizes.
  `off+size`, cache-end additions, `off+hint`, and alignup's addition are uint32_t
  arithmetic: wrapping is **not assumed safe**.
  Hints of zero/huge values and hints smaller than the current chunk are retained
  caller-contract questions, not dropped inputs to get a pass.
  In particular aligned off, 0<size<read_size and hint=0 can produce a zero-sized
  refill from the inspected arithmetic. Reachability from real callers is
  unresolved; it is a source-derived challenge, not a reproduced hang.
  File callers using block_size hints retain a large-geometry overflow obligation.
- **Counterexamples:** any byte sourced from lower-priority stale cache, unaligned
  or out-of-range callback, overwritten sentinel beyond requested output, zero
  progress on a reachable legal state, or wrapped arithmetic evading rejection.
  Invalid configuration is not promised a clean runtime error: many checks are
  assertions and may be compiled away (r2:lfs_util.h:112-119).
- **Method / limits:** noncatalog source contract table first; proposed native
  branch/overlay tests. Conditional `cbmc-c-buffer` v1.0.0, references/cbmc.md:
  enabled memory/UB checks and assertions over the modeled C/C++ harness domain,
  **with complete unwinding and specified platform model**. Pin architecture,
  pointer widths, flags, libc models, callback target and finite block/cache
  bounds. Unsigned arithmetic policy needs explicit assertions; UB checks alone
  do not prove the overlay/progress property.
  No assembly/concurrency/FFI in a supported pilot. Function-pointer calls to
  available RAM C bodies are not by themselves FFI, but real hardware calls,
  custom utils and LFS_THREADSAFE/concurrent deployment remain outside this
  unexecuted investigation. Compatibility unknown, implementation blocked.
- **Alternatives / readiness:** do not force a TLC filesystem model or a verified
  replacement: neither checks this C routine without separate correspondence,
  and replacement is not authorized. Finite block tests are cheaper but not an
  all-size proof. Establish actual caller hint/cache invariants before selecting
  bounds; any narrower pilot must retain the full-domain obligations above.

### O2 — Failed refill and cache validity on retry

- **Priority / value:** second but resolve before claiming a reusable read
  invariant; high possible impact, low initial read-only investigation cost,
  uncertain follow-up. Happy-path RAM callback always returns zero
  (r2:bd/lfs_rambd.c:55-73) and cannot validate this boundary.
- **Observation / requirement:** lfs_bd_read writes rcache.block/off/size
  **before** invoking the refill callback and returns its error without dropping
  the cache (r2:lfs.c:107-123). Later cache hits consume those metadata and bytes
  at 74-88. Negative errors must propagate (r2:lfs.h:157-162;
  r2:README.md:119-125); recovery/retry guarantees and what bytes a failed read
  may leave are **unresolved**. The first is documented upstream intent; the
  stronger cache-validity proposition below is inferred and needs owner approval.
- **Domain / proposition:** start with a valid cache/read request under O1's
  config and memory obligations, allow callback failure without full output
  initialization, including a partial write, then retry on the same cache.
  Proposed safety invariant: cached bytes served as successful data derive only
  from successful reads or an explicitly approved validity/recovery protocol.
  Errors propagate on the failing call; no promise of transactional destination
  contents or unchanged file position across a multi-block partial read.
  A failing direct bypass and a failing refill are distinct cases. No new loop
  invariant beyond O1; inter-call validity is the important state invariant.
  Observable counterexample: failed refill marks the interval valid, next call
  succeeds by serving uninitialized/old/partially updated bytes without a successful
  device read. This is a **static hypothesis** until valid caller/retry lifecycle
  and callback contract are established, not an asserted upstream vulnerability.
- **Caller evidence / gap:** `lfs_file_flushedread` returns the error at
  r2:lfs.c:3544-3550 before per-chunk pos/off increments at 3553-3556;
  `lfs_file_read_` at 3563-3578 delegates without visible retry invalidation.
  Metadata caller also returns error directly (719-790). Public wrapper/recovery
  bodies and full cache lifecycle were not inspected, so end-to-end retry support
  remains unknown. Do not assume every caller reinitializes the cache.
- **Method / alternatives:** noncatalog read-only lifecycle investigation, then
  proposed native fault-injection regression if the callback contract permits
  retries. Conditional CBMC buffer scenario only after approving a sound failing
  callback model; asserting callback success would erase this very obligation.
  Finite tests/checks do not establish flash persistence, ECC, power-loss resilience
  or all hardware drivers. No production modification recommended.
- **Dependencies:** upstream/device owner decision on failed-read output and
  permitted reuse, bounded caller/wrapper inspection authorization if expansion
  is needed, then separate editing/execution and compatibility grants. Blocked.

## Actionable handoff

| Work | Next bounded task / proposed files | Authority / dependencies | Acceptance evidence |
|---|---|---|---|
| W1 | Read-only contract table for lfs_bd_read, align helpers, inspected cmp/crc/file/metadata callers; propose tests/test_bd.toml or a separate cache-focused native test file without editing | Discovery only authorized; approve overlay/hint/domain and actual target config before implementation | Per-branch byte and callback expectations; empty/end/overlap/bypass/refill cases; mathematical versus uint32_t arithmetic; trace hint>0 and nonwrapping obligations or retain unknown/reachable challenge |
| W2 | Read-only failed-refill lifecycle trace in named read callers, propose test_files.toml fault cases without editing | Need retry/output contract decision; broader public-wrapper scope if required; no upstream approval | Distinguish bypass/refill and failure before/after partial output; same-cache retry or documented mandatory recovery; source-backed proof of reachability or explicit unknown; do not silently invalidate cache in a model |

Later approved execution must retain exact C/CBMC versions, architecture and flags
(assertions/read-only/threadsafe/custom config), source/harness/callback identities,
commands, finite sizes, enabled checks, loop bounds, unwinding completeness,
assumptions, full output including failures and isolation record. No command in
the inspected Makefile/CI or any proposed task has run. Tests are samples; finite
checks do not cover every geometry or unmodeled driver. A fix, if later warranted,
requires its own separately approved production task, not this advisory.

## Review and limitations

Loaded unchanged approved SKILL, index, template and CBMC v1.0.0 guidance; no new
catalog entry/research promotion. Kani was loaded for D1, not applied to C.
Manual citation/intent/approval review only. No private evaluator evidence,
old reports or feedback. Boundaries outside inspected callers, configuration
overrides and hardware remain unknown; do not certify a whole filesystem.
Shared before/after checks detect some changes, not concurrent atomicity or
correctness. This is ready for independent evaluation, not self-approved.
