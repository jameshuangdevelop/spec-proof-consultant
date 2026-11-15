# D2 — caching block-device read advisory

Status: recommendation only, 2026-11-12; no target execution, proof, grading,
approval or repair. Addressed to littlefs maintainers/downstream device owners.
Use existing production code; proposed harnesses/tests require separate approval.
Campaign authority is read-only advice, not upstream requirements authority.

## Scope and evidence

| Root | Selected absolute root | Identity |
|---|---|---|
| r1 | <SOURCE-D2> | HEAD 6cb4e86540eca0d9ba62500a298385c9d863c8be; tree 9079d55ac294f6b66c58147a215ea73779431cef; tracked status empty before inspection |

Inspected lfs_bd_read, drop/zero/flush/sync/prog/cmp/crc context, bounded immediate
read callers, config validation, cache types, alignment helpers, RAM device body
and header, selected tests, Makefile/CI and README/device design search hits.
Not inspected: whole directory/file algorithms, all callers, CRC body, physical
device drivers, test runners, generated test translation units, platform libc.
SPEC.md hashed but not interpreted: no on-disk-format proof is proposed.
No power-loss, whole-filesystem, concurrency or real-flash correctness claim.

Existing artifacts: r1:tests/test_bd.toml:1-100 explicitly says it tests the
underlying device, not littlefs cache composition; tests exercise cfg callbacks.
r1:tests/test_files.toml:1-66 has mount/write/read round trips and chunk variations.
r1:.github/workflows/test.yml:19-100 describes architecture/test jobs. No result
was reproduced. Presence does not establish a pass or cover the proposed cases.

Output is outside all selected roots. Before-read ancestor/regular-file checks
found no scoped symlinks. Non-atomic metadata/hash checks are not a sandbox.
All views used <=100 inclusive lines; searches returned <=20 matches without
context. Budget, UTC and hash rechecks are retained in COMMANDS.md.

## Decisions

Two opportunities. Prioritize a source-only reachability/contract decision before
an original-code bounded read harness. Arithmetic/progress questions must not be
silently removed from a harness by assuming the desired invariant. Do not repair
production as part of this advisory. Defer crash models and write/erase proofs;
these add uncertain correspondence and do not answer the selected read boundary.

### O1 — Establish arithmetic and progress obligations, with concrete challenges

- **Priority:** first, high potential impact if reachable; low-cost read-only
  clarification compared with whole-filesystem proof. This is a question, not
  a confirmed bug or executed counterexample.
- **Target/call boundary:** r1:lfs.c:44-125 (`lfs_bd_read`), :128-174 (`cmp`/`crc`),
  :2886-2917 (`lfs_ctz_find`) and :3500-3579 (`lfs_file_flushedread`/read).
  File reads pass NULL pcache and block_size hint; ctz accepts a caller pcache.
  Full provenance of non-null pcache at every call remains unread.
  r1:lfs.c:230-270 (`lfs_bd_prog`) can initialize pcache offset aligned to
  prog_size; read-cache refill aligns to read_size (:110).
- **Requirement status:** size/alignment constraints are **documented** in
  r1:lfs.h:193-227; uint32_t sizes/offsets at :39-45. Initialization assertions
  r1:lfs.c:4236-4251 require nonzero read/prog/cache sizes, divisibility and
  block_size>=128, but do not visibly assert read_size==prog_size.
  **Inferred:** every successful nonterminal read-loop iteration should consume
  bytes or prepare a cache that permits progress next iteration; arithmetic
  should preserve requested block bounds. **Unresolved:** reachable-state
  invariants on hint, pcache offsets, maximum offsets and callback failure cache
  reuse. Owner decision required; repository assertions are not universal input
  validation (LFS_NO_ASSERT disables them, r1:lfs_util.h:112-117).
- **Property/domain:** initialized sequential lfs/cache/config state, active cache
  buffers of cache_size, positive request or zero-length edge, valid device block
  (block_count zero disables the local bound check). Derive actual caller bounds,
  not only `off+size<=block_size` evaluated with wrapping uint32 arithmetic.
  Track mathematical `initial_size = consumed + remaining`,
  data pointer = initial pointer + consumed, off = initial off + consumed where
  representable; on refill establish positive future cache coverage.
  Reject/resolve any state that loops with unchanged off/size/cache.
- **Concrete source-derived challenge A:** block_size=128, cache_size=16,
  read_size=4, prog_size=1; pcache for requested block has off=1,size=1,
  rcache invalid, request off=0,size=8,hint=8. These size divisibility constraints
  fit the viewed initialization subset. At :58-72 pcache caps diff to 1;
  bypass condition :91 holds, aligndown(1,4)=0 (:94), callback receives size 0,
  and success leaves off/size unchanged (:101-104). A zero-read-success callback
  is consistent with the viewed RAM read body. Whether this local state and
  request coexist on a real caller path is **unknown**. Do not label it an
  exploitable hang, or assume pcache read-alignment without evidence.
- **Challenge B:** 32-bit off=0xfffffffe,size=4 makes off+size wrap to 2, so the
  first guard alone does not reject a mathematical out-of-block request.
  `off+hint` and `a+alignment-1` can also wrap (r1:lfs_util.h:135-140).
  This is a guard sufficiency challenge, not evidence that public calls supply it.
  Include hint=0, maximum hint, cache-boundary and non-overflow invalid requests
  in the decision record. Do not replace these with tiny-buffer assumptions and
  call the result universal.
- **Method:** noncatalog source reachability/requirements analysis first.
  `cbmc-c-bitvector` 1.0.0 (`references/cbmc.md`) is a later conditional candidate:
  bit-precise enabled checks/assertions in the modeled domain with complete
  unwinding and explicit platform assumptions; compatibility **unknown**.
  Unsigned wrap is defined C behavior, not automatically a UB failure: explicit
  semantic bounds/progress assertions are needed. No execution here.
- **Alternatives/prerequisites:** native regression cases after reachability and
  intent decisions can expose sampled failures; they are not proofs.
  A finite transition model cannot establish caller reachability in C.
  No new exclusion such as read_size==prog_size is approved by this report.

### O2 — Original-code cache precedence, callback bounds and error propagation

- **Priority:** second; useful narrow component guarantee if O1 resolves domains.
  Moderate setup cost: static function access, function-pointer resolution,
  complete loop bound and libc model inspection.
- **Target/config/callees:** r1:lfs.c:44-125 uses lfs_min/aligndown/alignup,
  memcpy, assertions and cfg->read. Helpers at r1:lfs_util.h:123-140 were read;
  cfg callback interface at r1:lfs.h:163-168 and RAM callback at
  r1:bd/lfs_rambd.c:55-73 were read. RAM callback is C, not a missing foreign
  body merely because its header has C++ linkage guards. Real device bodies and
  libc models remain unknown. LFS_CONFIG/LFS_DEFINES can replace helpers
  (r1:lfs_util.h:14-39); proposed initial configuration excludes those overrides,
  records LFS_READONLY/assert/logging settings, and assumes single-threaded use.
  LFS_THREADSAFE lock wrappers are outside the claim.
- **Requirement:** negative device errors propagate (**documented**,
  r1:lfs.h:163-168; r1:README.md:121-123); multiple-of-read_size callbacks and
  configured cache geometry are documented at r1:lfs.h:193-227.
  Priority pcache > rcache > device is **inferred from implementation**
  r1:lfs.c:58-89 (comments included), not independently approved intent.
  Owner must approve logical read precedence and error-side-state expectations.
- **Property/domain:** after O1 defines valid states, proposed initial pilot uses
  block_size=128, two device blocks, read/prog sizes from {1,2,4,8}, cache_size=16,
  all fitting offsets/request sizes and arbitrary data; retain legal pcache/rcache
  overlap and NULL pcache cases. Valid disjoint live allocations for output,
  read cache, program cache and device; confirm this corresponds to callers,
  not an invented universal no-alias contract. Full-width arithmetic is a
  separate O1 obligation, not covered by this small storage pilot.
  On success output[j] equals pcache byte if valid there, else rcache byte if
  valid there, else coherent device byte. Cache refill may replace rcache; use
  the initial logical overlay as oracle and require rcache initially coherent.
  Every device request is in-block, aligned, and writes within its output
  allocation. Zero-size request does not touch destination or call read when
  the initial guard accepts it. Preserve bytes outside requested output.
- **Errors/state:** first nonzero negative callback return is returned unchanged,
  with no later device calls in that invocation. Do not require output rollback:
  an earlier prefix may already have been copied. Refill updates rcache metadata
  before the callback (:109-121); no cache rollback/invalidation-on-error guarantee
  is established. Whether retry can reuse a failed refill is unresolved and must
  be included in the contract/reachability task, not assumed safe.
  Positive callback results violate the viewed `err<=0` assertion contract.
  Cache drop invalidates block; zero fills buffer with 0xff and invalidates block
  (:31-42), not cryptographic secure erasure.
- **Counterexamples:** stale-device bytes override dirty pcache, skipped bytes at
  cache overlap, out-of-bounds memcpy/callback, wrong negative error, false
  success, or failed-refill reuse inconsistent with the approved error contract.
  Include invalid block and non-wrapping off+size>block_size => CORRUPT cases,
  but do not generalize guard behavior to wrapping inputs.
- **Method:** `cbmc-c-buffer` 1.0.0, bundled CBMC guide/index; compatibility
  **unknown**, no claim of a supported pilot yet. Conditional assurance:
  enabled memory/UB checks and assertions over the modeled C/C++ harness domain
  with complete unwinding and specified platform model. Excludes assembly,
  concurrency, FFI; no real-flash, power-loss, unbounded sizes or unmodeled
  callbacks. Pin release and explicit malloc/check defaults; CBMC 6 documentation
  changes these, so neither a version nor standard checks are invented.
- **Alternatives:** direct native cache tests with a recording RAM callback offer
  lower-cost sampled evidence; existing test_bd cases bypass this cache code.
  TLC would require a separately justified finite abstraction and would not
  check C memcpy/pointer behavior. No production rewrite proposed.

## Actionable handoff

| Work | Bounded next task / proposed artifact | Dependency / authority | Acceptance |
|---|---|---|---|
| D2-W1 | Read-only caller/reachability and owner-intent record `D2-read-domain.md` | Advice authorized only; owner decisions unavailable | Resolve or explicitly retain challenges A/B, hint bounds, cache alignment/alias/coherence, refill-error retry and all non-null pcache caller obligations |
| D2-W2 | Read-only `D2-command-plan.md`: select pinned CBMC/compiler model and optional native test invocation | W1; execution/implementation blocked | Exact versions, cwd r1, include paths/C99/defines/machine model, static-entry wrapper referencing unchanged lfs.c, callback/libc model inventory, assertions/check flags, loop bounds and unwind completeness strategy |
| D2-W3 | Separately proposed harness/native test files outside production sources | W1/W2 plus actual named owner and isolated execution approval | No source replacement; cover precedence/negative cases; preserve counterexamples and complete output, source/harness/model identity, assumptions, failures, version/commands and correspondence |

W3 is not authorized or executed. W2 is a command-selection task, not an invented
working invocation. Cost/compatibility remain unknown until prerequisite answers.

## Review and limitations

Uses actual supplied skill/template/index and CBMC guide, with no engine or old
answers. At most two opportunities; no report validation or recommendation score.
Hash/Git freshness is recorded separately and is non-atomic. No proof, approved
contract, complete call graph or whole-filesystem guarantee is established.
