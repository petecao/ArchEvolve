# Heap capability runner: prefreeze independent review

2026-10-15 ET. Read-only review at `/private/tmp/probata-resume-t25`, base `e3e91b8e998d6c60c8fc12df0520cbfd7b63026a`. No tests, compilers, WP, Why3, provers, providers, CBMC or remote jobs were launched. Mapping review remains `/private/tmp/probata-t25-first-vc-map-review-v4-final.md`; its three mapping files are unchanged in this runner snapshot.

## Verdict: narrow result-admission correction required before formal freeze

1. **Selected negative target must be the classified failure.** `actual` currently accepts any reader verdict not_proven plus any ordinary open goal. The current shared reader can also return not_proven/UNCLASSIFIED for report/inventory disagreement after accumulating ordinary goals. That is an integrity failure, not a successfully observed semantic negative control. Similarly, a selected lemma property can exist while an unrelated ordinary goal is open. Require an admitted semantic failure class, reject malformed/unclassified/unsupported/integrity failures, and bind the open ordinary goal to the exact selected lemma property. A directly Valid intended lemma must never satisfy an expected-negative row. Keep report completeness and fresh direct result checks unchanged.
2. **Numeric kernel needs its real smoke inventory.** Logical check lemmas can correctly have zero generated smoke; the original numeric C kernel has ordinary function preconditions and must retain a nonempty actual smoke inventory with every smoke passing. Merely supplying -wp-smoke-tests and receiving reader proven is not a nonempty-inventory check. Do not apply a generic zero-smoke exception to that kernel.
3. **Keep generated output outside the checkout before checking source.** Actual mode currently checks clean source, then can mkdir an output inside the checkout and compile/probe the formal tool before its next source check catches the newly untracked files. Reject resolved output under the checkout before mkdir/probe. The existing output-under-immutable-input refusal is appropriate; keep it.
4. **Resource flags must be acceptance conditions.** Explicitly require neither timed_out nor out_of_memory in addition to exit_code0 before reading a leaf as matching expectations. Current watchdog normally produces nonzero on those failures, but the scientific acceptance condition should not depend on that incidental coupling.

The author has been informed. These are bounded runner changes; no mapping or production proof-rule expansion is needed.

## Source, command and budget parts accepted

- Exact expected source SHA and full clean state are checked before formal discovery; actual leaves recheck source and exact packet bytes. Plan mode performs no formal-tool discovery/execution. Wrong-SHA fake-tool marker and real sleep-timeout controls exercise meaningful public boundaries; this reviewer read their code and did not rerun them.
- Shared verifier_lock covers discovery/report-module compilation/all leaves, with root retaining outer process-tree guard and lane ownership. Fresh report module is built from the current pinned source, every job directory is exclusive, cache is none, and reports/normalized C/task files are retained and hashed.
- Per-leaf public timeout reaches the real rss_watchdog.run call unchanged, with8GiB cap. Mandatory RTE/initialization/no-init-filter/smoke flags remain; each isolated check lemma is named, the numeric function selected explicitly, solver set/timeout/par1/machdep recorded. Unknown unsupported option or importer failure remains a nonzero/incomplete-report failure; it must not be counted as an expected negative.
- Original packet/model/translator/runtime/checker/report-source pins are recorded. Physical declared Why3 stdlib files are hashed, while actual import resolution and emitted hypothesis comparison remain explicitly pending. There is no false claim that a requested directory is the resolver's actual selected theory. No c_model record or completed model-body theorem is issued.
- The reader consumes all fresh generated goals and report CSV with global properties retained; there is no function-only filter. Expected-positive rows require nonempty ordinary inventory and reader proven. After the above fixes, selected-target/missing-goal failures can remain explicit failures rather than accidentally qualifying a negative.

Default40 leaves at180s each permit up to7200s of leaf work, plus up to120s report-module compilation, discovery/source checks and cleanup. Two added feasibility targets would permit7560s of leaf work. The outer coordinator budget should either cover that bound plus margin or explicitly label a shorter timeout as a deliberately partial capability probe. The declared plan does not enforce a whole-run disk quota; root should state/monitor the raw-output budget independently.

A generic definitional empty heap and constructive original constructor/destructor premise witnesses are appropriate additional nonvacuity controls. They must remain separately identified feasibility lemmas, with main claims quantified over arbitrary incoming heaps; they cannot become a restricted entry domain or fictitious generated smoke for global lemmas. Any resulting mapping-byte change needs a final changed-byte review.

Read pins for this snapshot:
- `experiment.py`: `6b23754c187ff2ac410476a337d59c28c41ca760082a6168a5a8b5ef6f749431`
- `heap_bridge.mlw`: `2075199d410ccc50e4b472fa58ebaa8bcca304e24f210cd88bad4fd4900825cf`
- `source_vcs.py`: `b6797e8d6a9180c520cd829542253238a04d766b4e2974b1e185761b58b46363`
- `packets.py`: `dc754e9e5e033e4c00a50dae5d9b1ce7e2fdfa47a9dbaf57dd5b74aa43fdd05f`
