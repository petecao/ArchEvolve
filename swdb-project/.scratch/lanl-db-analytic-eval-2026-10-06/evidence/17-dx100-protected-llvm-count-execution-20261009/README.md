# DX100 protected LLVM count execution

Updated: 2026-10-09 20:06 ET

The exact SG32/explicit-source call plan can now execute through the existing
LLVM counter pipeline. This is an internal count-only component, **not a
registered production characterization adapter, numerical bridge or blind pair**.

[`analytic_dx100_call.execute`](../../../../swdb/analytic_dx100_call.py) derives
the protected wrapper, compiles normalized and instrumented IR, runs one fresh
process and requires one exact source window plus the evaluator-owned independent
original-CSR result check. The receipt binds the plan, observed tool/compiler and
counter artifacts, controlled build/runtime settings, and before/after
source/input/observer/tool bytes. The shared stage recipe is reused by the
existing characterization command; its defaults and archived validators are
preserved. The original evaluator and production records/library are unchanged.

The new path disables default Clang configuration and uses a clean build
environment. On macOS it explicitly selects the installed SDK and records its
settings identity; this does not establish complete compiler-header byte closure.
Observed loaded-image paths and **post-run file hashes** are kept separately;
`runtime_library_byte_continuity` is always unknown. Missing shared-cache file
hashes remain named unknowns. These observations cannot authorize timing transfer.

## Verification and retained failures

- Final component batch: **40 passed in 5.97s**. One test runs real LLVM counters
  on a four-vertex synthetic fixture; the rest exercise wrapper behavior, binding
  and refusal cases. The earlier print-only observer is not the counter test.
- Selected unchanged shared-pipeline regressions: **14 passed, 1 deselected in 47.01s**.
  Together these batches contain **54 final selected passes**; all sessions closed.
- Local environment: Mac ARM, Python 3.12.6, LLVM 22.1.8. No LANL application
  timing, production candidate certification or numerical accuracy is claimed.

The first test extension retained three misplaced-assertion failures (34 passes)
and a raw-counter list/dictionary assertion failure. The next batch retained four
failures (35 passes), including the remainder of that misplaced original test and
an incorrect assumption that inlined instructions keep the DOBFS debug label.
All original test functions and assertions were restored exactly; the protected
window determines counting scope, including inlined instructions attributed to
main. The corrected intermediate batch passed 39 cases, before review fixes.
Disabling ambient compiler configuration then exposed the SDK's previously
implicit selection: one build failure/39 passes. Explicit SDK selection closed
that failure; only the final 40 cases count above. Project/default Python 3.14
and bundled Python 3.13 lacked pytest and failed before collection; the actual
batches used the available Python 3.12.6 environment.

An optional full live-context batch was interrupted at its full-catalog GAPBS
case after 458.03s, with 12 prior passes and exit 2. Its original five-trial case
did not complete and is not a catalog or adapter pass. Exact owned parent 18312
and child 18719 were verified and interrupted; no human process was touched.
The final selected rerun excludes that one case. Earlier partial passes are not counted
again. No complete suite pass is claimed.

Independent Standards and Spec source reviews found one interface readability
issue and two compiler/runtime provenance gaps. Keyword-only stage inputs, clean
build/analysis/archive-extraction controls, disabled default configuration,
post-run hash labeling and final byte checks closed them. All 15 other original
analytic function/class nodes and all original call-shadow test functions remain
AST-identical. The existing characterization command keeps its original default
environment; the new clean environment applies only to this DX100 execution path.

## Remaining scientific requirement

Next use this bounded execution path for exact registered candidate/input
functional command observations and bind the supported MMIO memory effects and
whole-call cost/composition premises. Complete runtime/header byte correspondence
and current 1.7 certification still need evidence. Missing premises stay unknown;
production Extensa continues to emit null/unknown estimates. No outcome timing is
an estimator input and no new gem5 execution/calibration dependency was added.

No SSH, scientific source synchronization, certification, campaign, outcome access
or eligible pair occurred. Original completed actions, negative report/refused
audit, D26/D30 and ticket 17's claimed status (three checked, blindness unchecked)
are unchanged. Human maps/tickets and root rule edit are preserved. This README
copies no source/raw stream or test artifact and creates no exact-original
inventory or new peer receipt.
