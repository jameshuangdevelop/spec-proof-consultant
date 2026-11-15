# Proof-readiness advisory

Status: recommendation only; no target execution or verifier result.
Date: 2026-11-15. Task: practical-confirm-author, single confirmation cohort.
User goal: bounded source-grounded write-batch specification/verification planning,
not storage-wide persistence/recovery assurance. Adoption: read-only planning;
actual owner implementation and execution grants absent.

## Scope and evidence

| Root ID | Selected absolute root | Revision / dirty state | Inspected areas | Skipped / unknown areas and why |
|---|---|---|---|---|
| r1 | evidence://campaign/targets/D3 | commit `29465588d3dfdc80fba5e198037582b8fdb5dd60`; tree `5e56720c8ea36b1d385362668605d0b40aa645e8`; initial/final read-only Git status empty | `db/write_batch.cc` 1–180, public/internal batch headers 1–100, batch tests 1–150; bounded `db/db_impl.cc` 1206–1278 and 1281–1333 after relationship search; `db/db_impl.h` 120–145; `CMakeLists.txt` 1–100 plus source/test search; `.gitmodules` 1–30 | Coding/Slice/Status/MemTable/dbformat bodies, recovery callers, storage/log/environment/locking implementations, most DBImpl source, third-party tests/dependencies unread. All scope exclusions retained, including unlisted storage files, table/port, target instructions, nested/symlink/vendor/generated/build/private/binary areas. |

Output: `evidence://campaign/advisories/confirmation/D3/assessment.md`,
outside all selected roots. Eight named leads were regular and below 256 KiB;
root and parent real paths matched. These are non-atomic metadata checks, not
no-follow enforcement, credential detection or a sandbox.

Requested source windows totaled 812 lines plus a 34-line native citation
cross-check (846 total), with EOF-short reads. No window
exceeded 150 (preferred 100); eight files versus initial allowance 250. Searches
had explicit result limits; no comprehensive call graph or tool-reported file
truncation. No cumulative character/syscall counter. Source HEAD/tree and full
status rechecked unchanged; concurrent edit-and-revert cannot be ruled out.

Existing assurance: `r1:db/write_batch_test.cc:54` Empty, line 60 Multiple,
line 75 Corruption, line 89 Append, line 115 ApproximateSize. Corruption asserts
a prefix effect and ParseError, not rollback. CMake names `leveldb_tests`
and `db/write_batch_test.cc` (lines 313 and 340); dependencies include excluded
googletest submodule (`r1:.gitmodules:1`). No tests were run and no passing result
provenance was supplied. Assertions in source/tests are not approved intent.

## Decisions

Prioritize one parser/handler contract lead: distinguish successful ordered
iteration from partial callback effects on malformed input. Do not translate
the public “atomically to a DB” comment into all-or-nothing Iterate behavior.
The inspected test expressly observes a parsed prefix after corruption.
Native trace tests and source contracts are more ready than a supported CBMC
claim; a bounded pilot stays conditional on callee/C++/machine-model closure.

Deferred: append self-aliasing and count/sequence overflow need owner decisions
and additional callee evidence; no defect is established. DBImpl group batching
and storage atomicity/recovery/concurrency are outside this proposed property.
No storage-wide model or repair is proposed.

### O1 — Ordered iteration and explicit partial-effects-on-corruption contract

- Priority/rationale: high within this small slice. A caller assuming parse
  failure implies no side effects could mishandle batches. A recording handler
  contract adds direct trace assertions and malformed/count cases beyond the
  inspected MemTable-oriented examples. Expected test cost modest; verifier
  boundary/compatibility cost unknown. This is a risk hypothesis, not a bug.
- Target/boundary: `r1:db/write_batch.cc:42` `WriteBatch::Iterate` rejects a
  header shorter than 12 bytes, consumes tags and length-prefixed fields, calls
  Handler::Put/Delete as it parses, and checks count only after consumption
  (line 75). `WriteBatchInternal::SetContents` at line 139 asserts at least the
  header length, so a short-header test must not bypass its precondition with an
  invalid call. `Count` at line 82 reads fixed32 into int; encoding/decoding,
  Slice, Status and allocation bodies are unread. `MemTableInserter` at line
  116 and `InsertInto` at line 132 invoke unread `MemTable::Add` and increment
  sequence per callback. `r1:db/db_impl.cc:1245` uses InsertInto after logging;
  BuildBatchGroup (line 1281, header declaration `r1:db/db_impl.h:135`) uses
  Append while holding the mutex. Those concurrent/storage callers are not part
  of a supported isolated parser harness.
  `r1:CMakeLists.txt:17`–23 selects C++17 by default; lines 55–83 disable
  exceptions/RTTI by compiler branch. Tool support for these features, virtual
  Handler dispatch, std::string and library allocation is unknown.
- Requirement: **documented** ordered batch updates
  (`r1:include/leveldb/write_batch.h:5`–14) and Handler operations (lines 35–39);
  **inferred** Iterate callback order and partial-effects error behavior from
  `r1:db/write_batch.cc:42`–79 and
  `r1:db/write_batch_test.cc:75`–86. Owner authority and approval to specify that
  behavior are unresolved. The public DB-atomicity statement does not document
  Iterate rollback. Thread constraints at public header lines 16–19 require
  synchronization when mutation is possible, not automatic race freedom.
- Property: candidate byte-sequence domain for later tests/bounded investigation:
  12–64-byte representations, Put/Delete records with zero-length, binary and
  short keys/values, valid and malformed length encodings, unknown tags,
  truncated fields, and header-count mismatches. Bound choice needs approval;
  actual API allows larger data. Require valid backing storage and a live
  recording Handler that copies slices and does not mutate the batch, throw,
  destroy it or reenter Iterate. Those handler restrictions need approval;
  permitted adversarial/reentrant handlers must not silently disappear.
  For fully valid records with count equal to parsed records, return OK and
  deliver exactly their ordered operation trace including duplicate keys.
  For a malformed record/tag, return corruption after exactly the fully parsed
  preceding records' callbacks, with no callback for the malformed record or
  later records. For valid data with count mismatch, return corruption after
  all parsed callbacks, not rollback. Loop invariant: consumed input consists
  of complete preceding records plus the current parser progress; the callback
  trace equals the complete valid prefix and the remaining Slice stays within
  original storage. `found` counts encountered record tags and must not be
  mistaken for successfully delivered callbacks at an error point.
  Counterexamples: wrong operation/bytes/order, callback for an incomplete
  record, OK on mismatch, extra callback, invalid Slice access or arithmetic UB.
  Large count/int-conversion/overflow behavior and short-header reachability
  remain W1 questions, not assumed safe. Error-code checks should not mistake
  a specific message string for an approved stable interface.
- Method: first **noncatalog source inspection/native recording-handler tests**,
  non-proof sampled behavior. Candidate `cbmc-c-buffer` 1.0.0 from bundled
  `references/cbmc.md` is **compatibility unknown**, not a supported pilot.
  Guide provenance: staged 0.2.1 index, catalog snapshot
  `9ce3702cb69a0944cb4db4d5b318cf118cf00509`, documented, sources checked
  2026-11-05, no reproduced verifier result.
  Exact conditional assurance: “Enabled memory/UB checks and assertions over
  the modeled C/C++ harness domain with complete unwinding and specified
  platform model.” Requires flags/includes/data model, real callee bodies,
  allocation/loop bounds and sound environment modeling. Hard exclusions:
  assembly, concurrency, FFI. A concurrent DB-wide pilot is excluded; C++ linkage
  itself is not FFI. Isolation of original Iterate/callees is only proposed;
  unread parser bodies must not be replaced by always-success stubs.
  Not an unbounded heap/loop guarantee or universal C++ support.
- Alternatives: native malformed-input/trace tests first, fuzzing/sanitizers only
  after separate authorization (executed-input evidence, not exhaustive proof).
  Defer CBMC until scope/intent/compatibility closure; a TLC abstraction would
  not establish byte parser memory safety. No verified-source replacement.
- Dependencies/readiness: owner-approved partial-effects contract and handler
  domain, extended safe callee scope, real C++/allocation/parser models,
  approved finite bounds, exact toolchain/configuration, actual grants and
  appropriate isolation. Unknowns block implementation, not honest evidence.

## Actionable handoff

| Work ID | Next bounded task / proposed files | Depends on | Approval and readiness | Acceptance / evidence required |
|---|---|---|---|---|
| W1 | Read-only `batch-iterate-contract.md` outside target; enumerate parser/handler/count/short-header questions and required callee-scope request | O1 | Current selected evidence only; owner authority and added source scope absent | Cited ordered/partial-effect behavior, reachable malformed-input construction, count/alias/reentrant limits or explicit unknowns; no false DB-atomicity inference |
| W2 | Read-only `batch-check-invocation.md` outside target | W1 and owner method decision | Selection only; no build/verifier invocation grant | Resolve exact native-test build/filter and trusted C++ versions/configuration or CBMC release/check inventory/machine model/includes/unwind/allocation settings, in an approved isolated work directory; inspect support without execution |
| W3 | Conditional direct recording-handler cases in `db/write_batch_test.cc`; optional separately scoped original-parser harness only if W2 establishes support | W1/W2, approved bounds/contract, actual implementation/execution grants and isolation | Blocked; no production repair authorized | Valid empty/binary/duplicate-key traces plus truncated key/value, unknown tag, overlong/malformed length and count-mismatch cases; record source/test/harness tree, versions, exact commands, domains/configuration, complete output/failures; tests versus complete bounded checks reported separately |

W2 is the required read-only invocation-selection artifact before any future
execution. No command/tool installation is implied to be supported or approved.
Any CBMC evidence must also retain successful unwinding assertions, enabled
checks, assumptions/stubs, incomplete exploration/timeouts and correspondence
to original code. Stop with explicit unknowns if the boundary cannot be closed.

## Review and limitations

Manual citation, root ID, guide and approval/dependency review only. No prior
outputs/private maps/feedback read, no target execution/import/build/test/proof,
network, source writes, promotion or nested agents. The shared data-only metadata
probe initially failed because `python` was missing (127); Python 3 then provided
metadata only. Final identity matched scope. No result here establishes target
compatibility, exhaustive coverage, recommendation correctness, implementation
proof, persistence/rollback semantics or approval.
