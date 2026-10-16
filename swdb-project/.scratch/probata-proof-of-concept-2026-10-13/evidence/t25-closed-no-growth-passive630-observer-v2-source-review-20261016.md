# Projected-C 630 passive observer V2 — independent source review

Date: 2026-10-16 ET. Reviewer: `caller_assess`.

Decision: **PASS for read-only metadata reconciliation.** Static review only: this reviewer did not execute the observer, import project code, use SSH, or run compiler/native/verifier/solver tools. Actual passive output remains a separate reconciliation gate. No second proof run is required for this correction.

| Fixed input | SHA-256 |
| --- | --- |
| `prototype/25-closed-no-growth-20261016/passive-630-observer-v2.py` | 4acfa5118c4541206289fcd833f686f9afbc5e9ad0ce413ed230ec0e2981ecb1 |
| Retained unexecuted observer V1 | 075e66e9a594db1009ddf6e047c4ec2a7fb93157e155f3bab58678e12aed8dae |
| Actual admitted projected entry | fe38605db3e05034870dff4e12e523607ba4370e79f8f50a064097a93f49e30a |
| Actual expected bytes | e51ca215b6f91eefbe6ec62d93d11e1397b32773eaa39f0d8b666a1141816a2b |
| Actual original refusal result | b25c1f791c7273f3f79e50b96e4e905cf4bedf6fda5b94e6e2683bcd18d89f30 |
| Actual complete Frama-C log | 5ba36b975ccdcf981fe3be4f21597ad1d014f4f30515919e7cdadb4b13a5ac00 |

The observer pins the settled raw namespace and source 615ddf504fed61b9f6c6e4663760d006ecaf255b. It extracts only the retained entry's lineage and census/common-export functions by AST, binds the complete entry bytes, and adapts precisely two conditions in a RAM-only copy: synthetic smoke `status_registered` false to true and export origin `wp-smoke-reference` to `registered`. Exact inverse equality is checked. Only the exact registered normal-proof form is accepted. The original entry, reports, metadata owners, verdict reader and every raw artifact remain unchanged; `bounded_json` is captured in RAM rather than writing a task census.

All 21 goal IDs and 72 native properties must remain complete/unique, match standard WP JSON, close property dependencies/origins, and retain all ordinary/smoke rows. The only permitted native owner exception is the constructor synthetic call smoke: exact IPOther/description, non-Extern, no dependency/origin, matching native property owner/line, goal/property/line/smoke/passed fields, root ordinary call-precondition, input call text and original fresh source/anchor lineage. The V2 postcheck independently requires callee `std_vector_int_ctor_count_value`, statement47, physical line129, root-owned call instance and exact call_context source/caller/callee/origin/line fields. Native callee and standard caller owners are preserved, never rewritten or filtered.

V2 fixes V1's insufficient plain DictReader check: it requires the exact seven-column TSV header, reconstructs Frama-C33's unquoted indented multiline predicate continuations, refuses malformed rows, and binds every normalized CSV row by native function/line and exact pretty predicate, callee-precondition origin or RTE predicate. Every normalized row/status and its native binding are returned. Status strings are observations, not proof promotion.

The unchanged common-export function streams the original log, records every export's exact range/hash/declaration index and unique native owner, keeps internal-Qed-only inventory explicit, and refuses missing noninternal task evidence. It does not rewrite task text or claim a semantic hypothesis proof. The source/runtime/import/consumer pins and entire raw-tree before/after snapshots are checked. The exact retained source-after dictionary must report source commit615, unchanged source and no tracked changes; inner/outer recorded failures must be ordinary exit1 rather than timeout/OOM. These are recorded metadata assertions and physical source-byte checks, not a new proof execution or broad dynamic-loader closure claim.

The observer requires 17 ordinary native Valid/passed goals and four healthy raw-timeout/passed smoke goals, while preserving the ordinary outcome `not_proven` / `unclassified_wp_outcome` and exact reason `not-Valid property has no classified failing goal: assigns *this;`. Only the existing five allocator/free Extern assumptions are allowed. The constructor is not whitelisted or admitted. No public proof record may exist. The original entry's ValueError refusal must retain its exact bytes/hash. Source-Typed/current-constructor/proof/caller/public-record acceptance remain false in the separate compact decision.

Execution policy: 120-second alarm, stdlib only; an audit hook rejects external/native child creation and file-write opens. A final compact JSON size bound is 4 MiB. The only projected action approved by this review is the already authorized passive observer under read-only SSH. Source/Typed allocation/lifetime, current constructor/body record, complete original caller observer and full task/import/hypothesis semantic closure remain pending.
