# Device timeout triage and next component design — 2026-10-16 ET

The useful next component is the exact-source `index_safe` / `missing_index` pair,
each in its own complete TU. The blended run exhausted its deadline before either
root had a completed external ordinary result. Repeating all six roots would again
mix substantial pipeline costs with the smaller initialization-transfer question.
This is design only: no source, observer, flags, proof budgets or admissions change.

The settled original remains normal `TimeoutExpired`, weak unexecuted, no proof
acceptance. The passive cold V2 and independent review retain the original six
recovered inspection events, lease handoff and separate later clearance. This note
does not repair the old producer's property-identity refusal by inventing aliases.

## What the partial run actually retained

The guarded pure triage consumed the primary raw log/journal and the root-dispatched
cold output: 707 modified callbacks, 328 actual goal IDs, no removed/cleared events,
and no first-to-last actual identity change. All 328 literal GIDs occur in the old
generation inventory. This is a partial observation census, not a final proof graph.

| Attributed root | Ordinary / smoke | Latest unique external result pairs | Sum of reported external prover_time | Material unresolved observation |
|---|---:|---:|---:|---|
| pipeline_safe | 64 / 21 | 97 | 337.224 s | postcondition and payload-init each timeout with all three provers |
| wrong_prefix | 63 / 21 | 94 | 247.238 s | payload-init timeout with all three provers |
| missing_source | 61 / 21 | 29 | 88.053 s | stream-load requires_6: AE/Z3 timeout, CVC5 unknown; 14 contradictory internal smokes |
| index_safe | 34 / 7 | 18 | 24 s | all 18 completed external observations belong to six smokes; no ordinary external result recorded |
| missing_index | 29 / 7 | 0 | 0 s | no external result recorded; all seven smokes lack an external attempt observation |

The per-root goal attribution uses exact function/body or callee-and-call-line
coordinates, preserving each actual property string. It does not substitute the
baseline property name. Pipeline has 62 ordinary goals with a raw Valid result,
wrong-prefix 62, missing-source 60. Index roots have none; seven index-safe and six
missing-index ordinary rows have passed=true with empty results. Those are retained
trivial/status flags, not completed external observations or independent proof claims.

The table sums each latest `(goal,prover)` result once. Its total is696.514043s;
244s are reported smoke times. It is an accounting aid, not elapsed CPU/wall time.
Primary `ProverTask.ml:142` overwrites `solver_time` with the goal's Qed time, so
summing that field across provers would triple-count Qed. `ProverWhy3.ml:1298–1314`
constructs an Unknown result without passing Why3's measured time, so a recorded
unknown with prover_time=0 does not establish zero solver work. Raw callback rows
repeat prior results; summing all707 events would also overcount. Outer wall time
760.559555875s, and the original timeout/cleanup records, remain authoritative.

The positive pipeline's two difficult obligations are not just missing-source
negatives. The retained Alt-Ergo task for its initialization goal has a quantified
memory/initialization formula, a `memcpy` chain for command outputs and final
`select(init_mask, produced_address)=true`. The range-loop completeness/lexicographic
relations remain in its antecedent. This establishes a real solver task was emitted;
three timeouts do not establish that the contract is false, that the mask is fresh,
or that a new premise/lemma is appropriate. The small gather-only index pair removes
that range-loop algorithm from the named component while preserving its real stores,
pointer-output interface and payload read. The pipeline/wrong-prefix worlds remain
preserved and open for later analysis of their existing tasks.

## Why 107 raw property strings differ

All107 differences are `property` only and all belong to callee-precondition goals:
pipeline37, missing-source37, wrong-prefix11, index-safe11, missing-index11. Every
pair has the same literal name stem after removing its final numeric suffix. That
is a diagnostic observation only; the reader correctly refuses identity equivalence.
For example a fixed pipeline const-call GID has baseline property
`dxc_const_i32_requires_7` and actual property `dxc_const_i32_requires_2`.

Installed primary sources explain a concrete mechanism:

- `property.ml:1108` gives `IPPropertyInstance` the underlying property's
  naming parts. Distinct call instances therefore compete for the same callee
  precondition basename.
- `property.ml:1138–1156` allocates and caches unique suffixes on the **first**
  `Property.Names.get_prop_name_id` query. This getter changes a naming registry.
- `wpPropId.ml:320–390` uses separate WP uniqueness tables for origin predicates,
  call sites and final GIDs; equal GIDs do not make kernel property strings equal.
- `wpo.ml:571–598` calls modified hooks when a goal is added, before proving it;
  `wpo.ml:654–697` calls them again on result updates. The actual result journal
  calls the naming getter in its row callback. The old generation workflow did
  not use that journal, so its later reporter naming queries have a different
  first-query order.

No actual within-run name changed across the707 callbacks. This evidence supports
registry-order drift as the explanation; it does not reconstruct the missing final
kernel property graph, prove all107 predicate objects equivalent, or authorize
suffix stripping in an admission reader. Preserve the original refusal and literal
IDs. In a future **new** source component, load the same observation hooks in both
fresh generation and proof stages, retain all first observations, and demand exact
source/origin/call-context/formula closure prospectively. Any remaining mismatch is
another retained refusal, not an automatically admitted alias.

## The apparent final files are early snapshots

`backend-bindings.json`, `per-prover-final.json` and `wp-inventory.json` respectively
have mtimes1792161219.070582149,1792161219.070668816 and1792161219.072592450. The
journal was created at1792161219.163189 and last updated at1792161975.502783467;
the failed result was written at1792161976.559198170. These files precede the proof
callbacks; their empty goal arrays do not describe a completed final universe.

This fits exact command/source ordering. `proof_command:837–843` has a parse/print
shot, a `-then` WP shot, then a report shot. Installed `kernel.ml:796–809` defines
`-load-module` in the global Extending stage; `cmdline.ml:1011–1019` processes it
before execution shots. `cmdline.ml:922–952` runs plug-in mains for each shot, and
`boot.ml:14–30` applies `Boot.Main` before printing. The read-only observers and
reporter register `Boot.Main.extend`; they can therefore write valid empty snapshots
during the initial parse-only shot. Their boolean `complete_snapshot` / `complete`
means completion of that callback's iteration, not completion of the later proof.
The killed proof never overwrote them with its final universe. Existing cold V2
keeps this explicitly partial; future consumers should also require the expected
generation/proof phase and nonempty exact actual universe before final acceptance.

## Smallest sound next stage, subject to root admission

1. Prepare two new TUs by replacing the other four **entire root contract/body
   spans** with newline-preserving blanks. Preserve all bytes of the kept root's
   contract, body, local names, stores, calls and read, its original line numbers,
   preamble/include, full unchanged `dxc_summaries.h`, every declaration/predicate/
   global and any helper body. There are no device helper definitions in this
   header; all opaque declarations remain. No `-wp-fct`, property/behavior filter,
   new assumption, weakened frame, changed result, or selected-goal omission.
2. Before formal admission, independently check exact span hashes and the complete
   root/world conservation map for all original five normal roots plus the separate
   weak root. Confirm no kept body/header references another removed root. This is
   a named per-root modular component, not a whole-original-TU proof or full C++
   theorem. Preserve the original blended TUs and all historical raw unchanged.
3. Add a separately reviewed read-only **append-only first-observation binding
   stream** to the observer. Its existing `observe` already computes and caches a
   first snapshot via `GOAL.get_descr`/`Pcond.pretty` without reduction. On first
   observation, append and flush that snapshot together with the already-created
   GID, short ID, backend property ID, function/file/line/smoke and phase tag. Do
   not add an early kernel naming-getter call: join the existing journal's literal
   property string by GID **within the same invocation**. Keep the final complete
   reporter, native report and DAG mandatory; the stream only improves retention
   after interruption. It neither changes goals/statuses nor supplies proof facts.
   Distinct output paths prevent an empty early Boot callback from erasing it.
4. Root may admit fresh generation first for the two new TUs with matching observer
   and journal hooks, full body/RTE/init/smoke census, no external solver and no
   assumed old41/36 counts. Capture exact phase/source/formula mappings. Freeze and
   review those artifacts before proof. A source-derived focused scope is explicit;
   it does not qualify the remaining pipeline, negative-prefix or weak world.
5. If generation is coherent, propose separate fixed per-root proof windows (e.g.
   150s each, shared total≤360s including setup), full three-prover portfolio30s,
   smoke2s,par1,8GiB/cache-none and all ordinary/init/RTE/smoke goals. A timeout of
   the first root must retain its partials and leave a separately recorded decision
   about the second; there is no automatic retry, phase promotion or extra budget.
   `index_safe` is the positive transfer test; `missing_index` is a source-identical
   no-index-store negative. Neither outcome is assumed. A smoke contradiction in a
   negative remains diagnostic, and a healthy nonproof remains distinct from a
   proved counterexample. Source Typed/alias/NoFrom/alignment residuals stay visible.

This next stage addresses an actual unobserved ordinary transfer question under a
complete smaller source world. It does not rerun the old pipeline positive merely
to repair reporting, and it does not erase the three known costly normal obligations.
The omitted-output weak payload question, all remaining source/lifetime/Graph/TD/
fresh-Codex counted-run requirements remain open. Root chooses all new admissions.

Pure triage resources: direct watchdog60s/1GiB, one Python child,0.039232250s,
25,509,888B peakRSS,129,129B output,exit0/no timeout/OOM. The child hook refused
subprocess/exec/spawn/posix_spawn/fork/system/ctypes loading. No compiler, native,
formal, provider, SSH, B/c6, reader main or old proof entry ran.
