# Ticket 36 final acceptance review

Updated: 2026-10-15 ET. Scoped independent ticket review; not the whole-effort two-axis review. Read-only source/evidence inspection at ticket worktree `5128dffc`. No tests, compiler, Frama-C, solver, provider or remote jobs were invoked by this reviewer.

Current disposition: **pending setup129 terminal closure and one targeted production prelaunch input-mutation control.** No new production source vulnerability was found. The latter is a coverage gap against the implementation's explicit postgate plan: `test_planned_input_hash_detects_changed_lowering` supplies an already-wrong scripted manifest at initial admission, whereas the plan asks to exercise mutation after generation at the real final prelaunch boundary. The existing external report-compiler stand-in can mutate its output directory's `wp_input.c` after `_wp` copies it and before `check_generated`; the public proof command should fail `input_hash` with no verifier marker or new record. That targeted control may reach formal-half parsing and needs coordinator admission.

## Ten-item crosswalk

| Acceptance item | Evidence and review boundary |
|---|---|
| Always first | `test_setup_failure_stops_batch_without_starting_later_jobs`, successful setup/method attestation control, real WP3 and bounded2 run attestations. Await setup129 terminal evidence. |
| Generated assumes only | Scripted SAW/harness negative controls refuse unattributed assumptions. Actual bounded caller pins its independently proven `contract.fixture_cbmc_clamp` summary and exact two generated assumption IDs. Input-domain restrictions remain the documented bounds/formal-precondition boundary. |
| Hazard probes/placements | Three public no-launch controls cover deleted/mis-originated probes and missing placement. Ticket27 closure supplies exact historical hazard/source integration evidence; do not relabel those records b493 or later checker evidence. |
| Contract/summary/lowering/plan hashes | Public contract and admitted-summary mutations occur after planning; driver mutation also hits final replay. Actual records retain contract/summary/lowering/generated input/run-plan/method hashes. A real post-generation input-mutation control remains needed as described above. |
| Frozen flags/session/environment | Public refusal controls cover cache update/offline, warning overrides, machdep, sessions, FRAMAC_WP variables, RTE/filter-init switches and full command prefixes. Actual WP3 flags retain fresh cache-none, RTE/init, smoke and frozen prover order/budget. |
| Method-version match | Dedicated execution-method check version/hash controls plus changed-reader/failure-vocabulary cases; runtime fallback, same-version driver, selected-command and effective-context controls. Retain cwd-sensitive translator context and exact final replay. |
| Per-property reading | Fresh actual facts13 plus complete inventory/JSON/CSV replay. Hidden lemma, call precondition, callee termination and untried target remain nonproof. Three unexpected Externs stop with no record; exact maa-summary Extern remains an assumption entry. |
| Doctored cache | Facts case11 fills/poisons real WP cache, demonstrates offline poisoned output, then reads fresh cache-none outcome. False target remains not_proven; cache artifacts are negative evidence. |
| Smoke | Facts6/7 retain contradictory-precondition/invariant vacuity and original failing goal classes. WP safe fill has three passing smoke goals. The unconditional scalar has no generated smoke goals while smoke generation remains enabled; its narrow test-only assertion replay preserves the original failed pytest. |
| Failure classes | Per-goal failure replay preserves timeout/unknown; unclassified properties and unexpected Externs stop batch. No WP timeout is called a refutation. Bounded seeded case is separately refuted only with its recorded source-level replay at x=41. |

## Accepted exact-source evidence inspected so far

Runtime repair, truthful effective-context control and scalar assertion correction have separate independent receipts. The actual optional-parser wrapper only changes optional parser discovery; it forwards real compilation and frontend traces. Full standard/allocation certificates remain mandatory.

The facts/production compact packet is explicitly partial. Its two local cold-audit hashes and source/checker/reference/file/error fields were independently matched: facts13, 40 references/126 files, zero errors; production3, 34 references/94 files, zero errors. Original production pytest remains one failure/two passes after five collected; corrected scalar assertions are retained-record replay, not a new green pytest run.

The bounded2 cold audit SHA-256 is `8cc80bdb4968b96ca322634e1655a71d52dafd87fcc64db04984facfb82fbf98`; its retained metadata reports zero errors, 29 references and 88 files. Four actual records are three proven and one refuted. The refutation retains original C++ replay with x=41. The summary record proves before the caller; the caller pins its proof record/content and exactly two postcondition assumption IDs. Guard exit0, no timeout/OOM, source-after clean2033. Remote files were audited by the recorded procedure, not independently re-read during this review.

All these actual records remain bound to source `2033c1746eeab02b1d59d4d910a4e31b3e726da8` and setup/reading checker `b493fec5c0c7f5e43ea7f0d45426e73f689c696ea16d35f5abc34b7476d28104`. Setup129 uses the exact reviewed `74edef` test follow-up with this checker. Later ticket28 checker changes must stay separate. A ticket-local reviewed acceptance freeze is the coherent gate for ticket36; requiring final production freeze59 would cycle through37/38/58. Drafts1/2 remain immutable; final method/source freeze belongs to59.

## Targeted generated-input coverage update — 2026-10-15 ET

The production last-prelaunch mutation coverage gap is now closed by the reviewed test-only control. It mutates actual copied `wp_input.c` in the external report-compiler boundary and checks exact input_hash refusal, retained changed text, compilation reached, no verifier marker and no proof record. Guarded GREEN: one pass, exit0, no timeout/OOM; no installed Frama-C/WP/solver is reachable under the explicit stand-in environment. See `/private/tmp/probata-t36-generated-input-independent-review-20261015.md`, SHA-256 `00556fe999c1399a53eef9dc9b4ba2ad36d9d257fa14f0112fc4a6d65cbb793d`. The earlier pending disposition is superseded on this one coverage point; setup129 terminal evidence remains outstanding.
