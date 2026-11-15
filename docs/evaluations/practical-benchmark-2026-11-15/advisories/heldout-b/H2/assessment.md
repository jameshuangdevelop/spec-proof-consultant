# Proof-readiness advisory

Status: recommendation only; no target execution or verifier result.
Date: 2026-11-15. Task: practical-heldout-author-b, H2.
User goal: bounded source-grounded assessment of the selected Python-library slice.
Adoption: read-only planning; actual owner implementation/execution grants absent.

## Scope and evidence

| Root ID | Selected absolute root | Revision / dirty state | Inspected areas | Skipped / unknown areas and why |
|---|---|---|---|---|
| r1 | evidence://campaign/targets/H2 | commit c3364059663df1ddce32799d6b1922af89a345f6; tree 2dc6021d44a8b2f512ce75e977fd2ea4355b3b3e; tracked status empty before and after | Signal connect, contexts, dispatch, receiver lookup/disconnect; utilities and package entry; context tests; targeted signal-test search/muting window; pyproject first 100 lines | Remaining cleanup/namespace and test bodies mostly unread; stdlib weakref/contextmanager and callback bodies unexamined; docs, lockfile, changes, unlisted files, target instructions, nested/vendor/generated/private/binary areas excluded |

Output: evidence://campaign/advisories/heldout-b/H2/assessment.md, outside all selected roots.
All 6 named files were metadata checked (regular, below 256 KiB) and had content inspection. Small explicit windows/searches only; no truncated output, no window above 100 lines, no recursive dump or exhaustive coverage. No cumulative codepoint/syscall budget enforced. Parent real-path/type inspection was non-atomic, partly after source reads; this shared host is not a sandbox. Untracked content was not inspected.

Existing assurance: `r1:tests/test_context.py:10` `test_temp_connection`, `:27` sender filtering, and `:52` normal/BaseException cleanup assertions. `r1:tests/test_signals.py:466` `test_mute_signal` checks suppression within one context. Searches show weak-reference and async tests, but search hits are not full semantic coverage. No tests were executed and no passing result provenance supplied.

## Decisions

One high-value intent-resolution opportunity: temporary contexts use destructive exit assignments, not saved-state restoration. Source trace reasoning exposes important nesting/pre-existing-state questions without running Python. This is not a declaration of a bug: wording does not settle all interactions. Resolve intent first, then conditionally add native tests. A finite model would currently encode an unapproved choice and adds little before contract clarification. No native Python proof scenario in the bundled index.

### O1 — Resolve context exit semantics under nesting and existing connections

- Priority and rationale: high for specification work, implementation priority undecided. Test helpers can unexpectedly unmute or disconnect an existing receiver, changing later observations. Low-cost source-backed decision work precedes any material behavior change.
- Target and boundary: `r1:src/blinker/base.py:168` `Signal.connected_to` calls connect with weak=False and finally calls disconnect without the sender argument. `r1:src/blinker/base.py:192` `muted` sets is_muted=True, then unconditionally False on exit. Dispatch early-outs on that flag in `r1:src/blinker/base.py:204` `send` and `:255` `send_async`.
  `r1:src/blinker/base.py:91` `connect` updates receiver/sender maps, weak references and optional receiver_connected notification. `:326` `receivers_for` unions ANY and sender-specific receiver IDs; `:364` `disconnect` defaults to ANY, and `:388` `_disconnect` removes the receiver globally for ANY. `r1:src/blinker/_utilities.py:42` `make_id` handles bound methods and equal str/int values; `:60` `make_ref` uses WeakMethod/ref. `r1:src/blinker/__init__.py:7` exports Signal.
  stdlib contextmanager/weakref behavior, cleanup callbacks beyond the read window, receiver notification side effects, reentrant dispatch and event-loop/thread scheduling are not closed. The sequential source trace does not claim thread safety, cancellation semantics or weakref timing.
- Requirement: **documented**, `r1:src/blinker/base.py:171` says the receiver is disconnected on context exit; `:193` says receivers are disabled until the with block exits. **Unresolved** whether nested mute blocks preserve the outer mute and whether connected_to should preserve prior registrations or other senders. Actual requirement authority and owner approval absent. Existing single-context tests observe behavior, not approval for either interpretation.
- Property/domain: evidence task covers one Signal, one receiver, two distinct integer senders plus ANY, up to two nested contexts, previously muted/unmuted states, pre-existing receiver connections and normal/exception exits. Strong references and serial operations give a transparent initial trace; weak references, reentrant notification exceptions and async cancellation remain explicit additional cases, not excluded from the full API.
  Candidate restoration contract (**unresolved**): exit restores the relevant pre-entry state; while any nested mute remains active no receiver is invoked; connected_to exit does not remove unrelated pre-existing sender registrations. Candidate destructive contract (**documented in part, unresolved in scope**): exit unconditionally unmutes/disconnects as the present implementation does. Postconditions and invariants must be selected by the owner, not weakened for a pass.
  Source-derived counterexample to restoration: enter outer muted, enter/exit inner muted, then send while still inside outer; inner finally sets False, so a live synchronous receiver can be reached. Likewise, connect receiver to sender 1, use connected_to(receiver, sender=2), exit; disconnect(receiver) removes all sender registrations. These are static traces/hypotheses about runtime behavior, **unexecuted**, and conditional counterexamples to restoration rather than proven defects. Loop invariants are not relevant to context enter/exit; the proposed state invariant is preservation of the owner-selected context/registration policy.
- Method: explicit **noncatalog source-only contract investigation**, then conditional native regression tests. Native tests observe concrete behavior and do not prove all interleavings. pyproject declares Python >=3.9 (`r1:pyproject.toml:15`), pytest and pytest-asyncio (`:43`), and pytest configuration (`:74`); no installed-version compatibility was checked.
- Alternatives: `tla-state-machine-safety` version 1.0.0, locked references/tlc.md, permits a separately accepted finite abstraction; assurance is invariant checking for the explored finite TLA+ model and recorded configuration, subject to constraints and complete exploration. It does not settle intent or prove Python/contextmanager/callback correspondence. Defer until an actual state policy and abstraction adoption are approved. Liveness modeling lacks an approved progress/fairness goal. Rust/C native scenarios do not match; replacement/codegen adoption is absent.
- Dependencies/readiness: owner must choose destructive versus restoration semantics, including backward compatibility, existing weak/strong connections, ANY and notification errors. No product repair is authorized and a material contract change must be escalated.

## Actionable handoff

| Work ID | Next bounded task / proposed files | Depends on | Approval and readiness | Acceptance / evidence required |
|---|---|---|---|---|
| W1 | Read-only `H2-context-policy.md` outside targets: source trace table and requirement decision request | Current cited evidence | Proposed evidence work; actual owner policy decision absent | Distinguish observed assignments from intended semantics; include nesting, prior mute, sender/ANY registrations, exceptions and notification failure questions; retain unresolved cases |
| W2 | Read-only command-selection artifact `H2-context-test-invocation.md` | W1, approved test interpretation | Proposed/unexecuted; no execution grant | Pin Python/pytest/plugin versions, working directory and exact focused arguments, dependency/isolation plan, and any fixture boundary outside allowed source; do not run installer/import or test collection |
| W3 | Conditional native context regressions, proposed tests/test_context.py and tests/test_signals.py in a separately authorized writable checkout | W1, W2 and owner-approved contract | **Blocked** on actual implementation/execution grants, intent and isolation | Positive single-context cases plus nested/pre-existing-state/other-sender/ANY and normal/BaseException exits; add notification/cancellation cases only after boundary resolution; preserve failing traces, complete output and exact source/tool identity |

## Review and limitations

Manual review checked citations, r1 labels, guide limits and blocked dependency order. Commit/tree and tracked dirty state unchanged on post-inspection recheck. No target execution/import/install/test/build/proof, network or source modification occurred. Exact locked skill 0.2.1, index, TLC guide, template and examples were used; no CLI-era skill. Unknown runtime compatibility remains unknown. This report establishes neither approved restoration intent nor exhaustive callback/GC/async behavior nor recommendation correctness. Escalate the contract decision and actual grants; do not repair from this advisory alone.
