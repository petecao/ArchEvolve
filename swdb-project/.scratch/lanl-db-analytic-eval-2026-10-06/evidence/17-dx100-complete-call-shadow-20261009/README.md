# DX100 complete-call counting shadow

Updated: 2026-10-09 19:32 ET

This is a bounded preparation component for the DX100 pair path. It is **not a
registered production counting adapter or a completed numerical bridge**.

[`analytic_dx100_call.prepare`](../../../../swdb/analytic_dx100_call.py) derives a
functional counting wrapper from the existing protected DX100 BFS evaluator.
It selects the registered SG32 file and explicit source instead of the original
generated-input trial lambda. Graph construction precedes the sole marked BFS
call; the returned parent object and independent original-graph check remain
after it. The default simulator evaluator is unchanged byte for byte.

The plan binds canonical candidate/snapshot/workload digests, actual source and
SG bytes, the function, derived wrapper, arguments and required counting
environment. It rejects changed source/input records, SG64 substitution,
out-of-range sources, source macros and compiler flags that replace markers or
introduce unbound headers. A changed evaluator boundary refuses derivation.
Preparation executes no candidate and writes no output. Its digest is a plan
identity, not an execution or certification receipt.

## Local verification

- Final new component batch: **29 passed in 1.72s**.
- Existing original-graph evaluator regressions: **13 passed in 6.14s**.
- The 42 selected passes include compiled synthetic C++ fixtures for connected
  and isolated sources, invalid parent trees, malformed SG input, marker order,
  compiler substitutions and Python-equal but canonically different records.
  Fixture observer functions print marker events; they are not LLVM counters.
- Environment: Mac ARM, Python 3.13.14, Apple clang 21.0.0. These tests establish
  wrapper behavior, not LANL application timing, certification or agreement.

The initial component batch passed 15 cases before review. Spec review found
compiler-flag marker substitution and Python equality/type confusion; both were
fixed with explicit regression cases. During that fixture extension, an
incorrect call to the graph-normalization helper caused 28 failures and one pass
in 0.65s, before those 28 test bodies reached the component. The fixture call was
corrected; only the final 29 cases count toward the total above. No full suite or
new production counter run is claimed.

Final independent Standards and Spec reviews against `ddca8e93` closed both
findings and reported no remaining actionable issue. The reviewers checked
source and documentation; they did not run tests or scientific work.

## Remaining boundary

Next connect this exact call plan to actual protected LLVM counter execution and
bind observed compiler/runtime/counter artifacts. Functional/MMIO memory effects,
target costs and complete-call composition remain unsupported. The old candidate
certification remains incompatible with current 1.7 defaults; fresh certification
is required before an eligible evaluator path, and does not itself prove timing.

Production Extensa still emits null/unknown estimates. No fresh certification,
scientific source synchronization, campaign, outcome access or numerical pair
occurred. Original report/audit/history and D30 are unchanged. Ticket 17 remains
claimed, with three report/guard items checked and D26 unchecked. Human tickets,
maps and the root cleanup-rule edit are preserved. This note contains no copied
source/capture stream, exact-original inventory or new peer receipt.
