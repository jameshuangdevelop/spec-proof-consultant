# Provisional end-to-end example

`rust-buffer` is deliberately tiny source data. The assessment command in the root
README reads it without compiling Rust or running its test.

With `--goal memory-safety --adoption no-production-changes`, expect:

| Scenario | Decision | Why |
|---|---|---|
| `kani-rust-slices` | Provisional candidate | Rust function and buffer/indexing signals |
| `kani-rust-unsafe-memory` | More information required | No observed unsafe-operation signal |
| Verus scenarios | Excluded | Production adaptation disallowed by selected adoption constraint |
| CBMC scenarios | Excluded | No inspected C/C++ source |
| TLA+ scenarios | Excluded | Requested goal does not select state-model exploration |
| Dafny replacement | Excluded | Verified-source replacement is not allowed by the adoption constraint |

The detailed backlog has a ready source-inspection task and a blocked harness
pilot. Their low confidence is independent of planning priority. Existing
`sums_a_prefix` is an observed test artifact, not proof it passes and not evidence
that invalid lengths should panic, return an error, or be prohibited by contract.

The agent should inspect `prefix_sum` and its callers, then record whether
`length <= buffer.len()` is a legitimate precondition or an unresolved API behavior.
Only after explicit approval and compatibility inspection should another agent
propose a harness with a declared buffer domain and complete unwinding checks.
Do not silently assume away invalid inputs merely to pass verification.

Generated assessments contain absolute roots, observed Git identity/status, and
file hashes. Generate them locally with the documented commands instead of treating
a checked-in machine-specific snapshot as permanently fresh. All generated
verification outcomes remain **not-run**, and these fixtures are not a benchmark
of recommendation correctness.
