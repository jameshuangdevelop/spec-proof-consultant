# Optional developer read-budget preflight

This stdlib Python 3.11+ tool runs **from a source checkout only**. Installing
the skill requires no new Python, runtime, CLI, or service. No SKILL payload,
current frozen caps, quality weights, or nine-conclusion threshold changes.

Before actors start, or before authorizing additional reads, check an explicit
**full cumulative** plan against immutable, caller-owned staged UTF-8 text:

```sh
python3 tools/benchmark_read_budget.py --root /owned/staged-corpus plan.json
```

Example `plan.json` (replace the prior observed cost with the actual ledger):

```json
{
  "scopes": ["selector", "reviewer"],
  "operations": [
    {"kind": "observed", "scopes": ["selector"], "source_chars": 5000, "operations": 2},
    {"kind": "read", "scopes": ["selector", "reviewer"], "path": "instructions.txt", "start": 1, "end": 100},
    {"kind": "bounded", "scopes": ["selector"], "source_chars": 93300, "operations": 40}
  ]
}
```

Every operation charges its entire cost to **every** declared root/scope it
serves, including shared instructions. Declare all served roots as unique,
nonempty scope IDs; operation scopes cannot be empty, duplicate, or unknown.
Fields are exact: read operations have `path`, `start`, `end`; observed/bounded
operations have nonnegative integer `source_chars` and positive integer
`operations`. Booleans are not counts. Unknown kinds/fields and duplicate JSON
keys fail closed. Prior observed costs must remain in the plan. Bounded future
output sizes are caller-supplied upper-bound assumptions, not observed results.
Do not split plans, omit served scopes, or reset/refund costs to evade caps.

Each scope defaults to **80 operations / 120000 source characters**. A trusted
operator may supply an optional top-level `limits` object containing exactly
`{"operations": 80, "source_chars": 250000}` (both fields required, positive
integers; booleans, zero, negative values, and unknown fields rejected).
These limits must match a **separately prospectively frozen protocol**.
Larger preparation/review budgets represent a different future policy, not
authority to restart, change the current protocol, rerun the current review,
or retroactively waive old failures. The checker cannot verify that freeze.
The 100-line safety window and 256 KiB snapshot limit are not configurable.

Reads cost one operation and the actual inclusive LF-delimited window, clipped
at EOF (a window wholly beyond EOF contributes zero characters). Unicode
characters, CRLF, and final LF are counted without newline translation;
U+2028/U+2029 do not split LF lines. Requested ranges must be positive integers
and at most **100 lines**, conservative safety headroom; the normative 200-line
absolute cap is unchanged. Even 101, and therefore 201, is rejected.

Snapshots must be regular files no larger than 256 KiB, valid UTF-8 with no
control characters except TAB/CR/LF (DEL is also rejected). Paths must be
relative, without `..`, and have no symlink components, including the corpus
root. Use owned staged text, not live untrusted target roots. This input hygiene
is **not a TOCTOU guarantee or security sandbox** on a shared machine.

Stdout is a JSON summary with `ok`, actually applied `limits`, per-scope `totals`,
measured operation counts (and whole-file SHA-256 for reads), and `reasons`,
never source bodies or private absolute paths. Exit 0 means the supplied plan
fits; exit 1 means a budget/input/I/O failure. Argument usage errors use
argparse's exit 2.
Invalid inputs return empty totals, not a misleading partial approval.
`limits` is null when JSON/plan/limit validation prevents applying any policy;
otherwise it reports the defaults or validated explicit limits, even on failure.
The importable `check_plan(plan, root)` returns the same summary without output.
The checker makes no external fetches, target imports/execution, filesystem
writes, model calls, or persistent services.

## Retained preparation failures

The selector made 65 requests returning 134152 source characters, over 120000.
Its planned public-query maximum 93300 plus reconstructible local windows 47033
already totaled **140333**, predictably over budget before network calls.
The publication reviewer requested 34 source windows totaling **164869**, also
over budget, and only checked retrospectively. Synthetic regression plans
retain both over-budget totals rejected under the original defaults; no raw
private artifacts or target trial is needed. These were operator process
failures, not skill counterexamples.

This optional predictor checks only supplied plans. It does not enforce native
tools or runtime quotas, establish complete scope declarations, validate
bounded-output assumptions, or prove agent compliance, proof correctness, or
target compatibility. Actual runtime-ledger checks remain necessary. Hashes
identify only checked bytes: snapshot changes require a full cumulative
recheck, with prior observed costs retained, not refunded.

All prior failures remain failures; no new advisory grade occurred. This tool
does not permit campaign restart or retroactive acceptance. Any new benchmark
requires separate prospective authorization and freeze. Independent evaluation
and normal contribution review remain separate gates.
