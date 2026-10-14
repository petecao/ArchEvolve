# 18 — ArchEvolve mode level and handoff block

Created: 2026-10-13 22:17 ET
Updated: 2026-10-13 23:15 ET (review fixes); 2026-10-14 09:58 ET (resolved, Answer)
**Type:** slice
**Status:** resolved
**Blocked by:** 16
**Spec:** `../spec.md`; design: [map spec](../../formal-verification-2026-10-09/spec.md) (sections "ArchEvolve mode", "Records and levels", "What a proven verdict asserts" (assumption set, seven kinds), "Refutation, repair and bugs", "Verifier lineup and order", "Testing Decisions" seams 1, 2 and 4; choices S1, S2, S6; open point O1); decisions: [25](../../formal-verification-2026-10-09/issues/25-extensa-loop-proofs-and-ranking.md) items 2-3, 5, [26](../../formal-verification-2026-10-09/issues/26-proof-records.md) items 2, 4, 7, 9, 10
**Time estimate:** about 2 days

**What to build:** In ArchEvolve mode, a rewrite proposal's one final candidate artifact gets the
same proof path as in Extensa mode, with the same budgets. Once certified, it runs the bounded gate.
A refutation calls 13's counterexample-guided repair loop, which counts as the mode's allowed
bounded correctness repair. Then the unbounded rung runs. The team sees the outcome in the handoff: the
`evaluation_result` envelope gains a `certification_level` block in plain words. It gives the
level, each bound as a value or "any", each assumption as one sentence, "says nothing about speed",
and the proof record IDs. When not proven, it gives the highest level reached and the failure class
in words. Every sentence comes from a fixed template; no LLM writes them. The level is reported,
never ranked. Built and tested with the scripted verifier adapter.

## Acceptance

- [x] **Same gate.** A certified ArchEvolve-mode fixture candidate artifact runs the bounded rungs
  at its contract's minimum bounds through `swdb prove`, with the method version's per-candidate
  budgets (the same as Extensa mode's). An uncertified or rejected candidate artifact runs no proof
  step.
- [x] **Refutation calls 13's repair loop.** This ticket tests only the call: a scripted refutation
  on this mode's gate invokes 13's counterexample-guided repair loop as the mode's allowed bounded
  correctness repair (25 item 5), and each repaired candidate artifact it returns comes back
  through this mode's gate. Control: a candidate artifact the gate does not refute opens no repair.
  The 5-round cap, the counterexample's destination and the reverted-repair flag are 13's and
  tested there.
- [x] **Unbounded rung (S6).** A candidate artifact the bounded rung did not refute (proven, timed
  out, or no minimum bounds) goes on to the unbounded rung, which writes one proof record. A refuted
  candidate artifact never reaches it.
- [x] **Block when proven.** Proven unbounded fixture: the block shows the level, every bound
  dimension as "any", each assumption as one sentence, "Says nothing about speed.", and the proof
  record IDs. Proven within bounds fixture: each bound dimension shows its value, thread count
  always among them.
- [x] **Block when not proven.** The block gives the highest level reached and the failure class in
  words (for example "hint budget spent"), plus the proof record IDs of the attempts.
- [x] **Template sentences only.** One fixed template per assumption kind (all seven: assumed
  clause, proof semantics, summary, reduction, trusted tool, written proof, platform choice), plus
  each assumed clause's own sentence. A test renders every kind. Negative controls: free text
  planted in a fixture proof record's assumption entry never reaches the block; an assumption kind
  with no template stops rendering with an error instead of producing text.
- [x] **Dated snapshot.** The block is a snapshot that is dated and names the level-rule version.
  After a pin changes, `swdb candidate-level` reads a lower level, but an already rendered handoff
  keeps its dated snapshot.
- [x] **Reported, never ranked, no speed claim.** The block has no rank or score. The level never
  changes the envelope's performance claim or result class. Control: a proven-unbounded candidate
  artifact with no gain still carries no performance claim.
- [x] **Handoff envelope seam.** Every rendered `evaluation_result` envelope carries the block,
  with "Says nothing about speed." and, when proven, the counting proof record IDs. Negative
  controls: a proven level whose proof record IDs cannot be resolved, or a block missing the speed
  sentence, stops rendering with an error instead of emitting the envelope. The proof records behind
  the block pass `swdb validate` and `swdb build`.

## Notes

- **Not in this ticket:**
  - 14 — Bounded gate in the campaign: the gate inside the Extensa loop.
  - 13 — Counterexample-guided repair: the repair loop this ticket calls, with its 5-round cap,
    the counterexample's destination and the reverted-repair flag.
  - 63 — Experimental enabling contracts and the shared-contracts rule: refusing non-shared
    (experimental) contracts in ArchEvolve mode.
  - 16 — Post-campaign WP phase and budgets: WP scheduling in Extensa mode.
  - 10 — Level rule: computing the level and its snapshot.
  - 11 — Method-version file and failure classes: per-candidate budgets and the failure-class list.
  - 12 — Proposal and promotion fields: repair lineage on proposals; promotion review pins.
  - 19 — Derived implementations: rewrite chains, where each rewrite is one rewrite proposal.
  - 22 — SAW adapter and SAWScript translator, 37 — The proof-hint loop: the real verifiers behind
    the scripted adapter.
- Example block (design spec): "Proven for every graph and every thread count. Assumes: DX100
  follows its proof semantics v3, each rule cited to gem5 source; clang 22.1.8 compiles correctly;
  CPU caches hold no stale copy after a DX100 store (assumed; owner Eric). Says nothing about speed."
- Proven requires certified (O1): an uncertified candidate artifact's block shows the level
  certification gives.
- Assumption (not decided in the map): ArchEvolve mode's existing proposal commands (submit, then
  repair) drive the gate by calling `swdb prove`, and the tests drive those commands with the
  scripted adapter. The confirmed seams name only the proof command, `swdb candidate-level` and the
  handoff envelope for this mode.
- Assumption (not decided in the map): "same budgets" means the method version's per-candidate
  budgets (hint rounds, loop wall time, 15 minutes per bounded job, 5 repair rounds). ArchEvolve
  mode has no campaign, so `provider_calls_proof` and campaign lane-hours do not apply.
- Repair limits: ArchEvolve mode's existing build or correctness repair limit comes from the
  provider configuration (default 2, range 0-5), not D7's 2 (the campaign's certification repairs,
  25 item 3). Counterexample repair runs within the 5 rounds (25 item 5). How the two counts relate
  is 13's (its assumption: counted apart).
- Assumption (not decided in the map): the bounded gate runs after certification and before the
  evaluator's measurement; the unbounded rung runs after the measurement ends, never overlapping a
  timing step or a gem5 simulation, and runs whether or not the candidate artifact shows a gain.
- Assumption (not decided in the map): the plain words for each failure class live beside the
  failure-class list, and the envelope's format version rises with the new block.
- Assumption (not decided in the map): the handoff envelope is checked where it is rendered, not by
  `swdb validate` (it is a message, not a stored record).
- Generality: per contract, kernel and hardware target; nothing BFS- or DX100-specific. Contract
  fixtures only; no held-out kernel (BC, PR, SSSP).
- Tests use the scripted adapter; no real verifier job runs. Full-suite runs on the Mac use at most 2
  test workers.

## Later changes

- 2026-10-14 03:20 ET (main session, from ticket 19's Answer): ticket 19 records derived implementations in the
  Extensa campaign loop only. ArchEvolve mode does not record one yet: `swdb certify` on a rewrite proposal's
  candidate artifact is the hook, and ticket 19 left it unwired (see its Answer, "Gap"). This ticket picks it
  up with its ArchEvolve-mode work, using the scripted-certify pattern for the test. Interface:
  `docs/reference/format-v0.4-derived.md`, `swdb/derived.py`.

## Answer

2026-10-14 09:58 ET. Built test-first on branch `probata-poc/t18`. Every acceptance box is met with the
scripted adapter, a scripted certification and ticket 13's scripted provider; no real verifier, certification
run or provider ran. Interfaces: [`docs/reference/format-v0.4-archevolve-proof.md`](../../../docs/reference/format-v0.4-archevolve-proof.md)
and [`docs/bfs-handoff-contract-v1.2.md`](../../../docs/bfs-handoff-contract-v1.2.md).

**What exists now**

- **`swdb/archevolve_proof.py`** and `swdb prove --proof-path bounded|unbounded --plan P [--provider-config C]`
  (the one proof command, S1). `bounded` runs ticket 14's `Gate` unchanged (minimum bounds, k on the
  multi-thread rung, `bounded_job_minutes`); a refutation calls `counterexample_repair.loop(setting="archevolve")`,
  whose `certify` is the certification command plus the derived hook and whose `gate` is this same Gate (a
  reverted repair gets no job, as in campaigns). `unbounded` (S6) runs one job per proof unit with
  `hint_rounds` / `hint_loop_wall_minutes` and the O7 skips; it refuses a refuted candidate artifact and one
  that never ran the gate. Both refuse an uncertified, rejected or Extensa candidate artifact before any job.
  `ScriptedPlan` is the scripted adapter (rows per repair round, last repeats).
- **`swdb/handoff_level.py`**: the `certification_level` block (`render` = `block` + `check`). Fixed
  templates for the seven assumption kinds (`TEMPLATES`); an assumed clause's sentence is the library clause's
  `statement` plus "(assumed; owner X)"; failure classes in words from the new `words` field of
  `vocab/proof_failure_classes.yaml`; dated `level_rule.snapshot`; `Says nothing about speed.` always.
  `swdb/handoff.py`: every `evaluation_result` envelope carries it, `format_version` 1.2.
- **Derived implementations in ArchEvolve mode** (19's gap): `swdb certify` (`certification.run_cli`) calls
  `archevolve_proof.record_derived` after the record is written; output adds `derived_implementation` or
  `derived_note`. Offloading contract, failed certification or Extensa candidate: none.

**Tests:** `tests/test_archevolve_proof_path.py`, 29 tests (same gate; no proof step for uncertified/rejected;
refutation -> 2 repair rounds each through this gate, control with no repair; unbounded after proven / timeout
/ no minimum bounds, refused when refuted or before the gate, hint budget spent; block proven unbounded,
within bounds, not proven, refuted, uncertified; all seven templates, planted free text absent, missing
template, unknown clause, prose reference; dated snapshot kept after a method-version pin change; never
ranked, content identical apart from the block; unresolvable records and missing speed sentence stop
rendering; validate and build; certify hook and its two controls). Updated assertions: format 1.2 in
`test_functional_evaluation.py` and `test_bfs_acceptance_report.py`. Runs below.

**Runs** (one worker, no xdist, `--report-log`, output under `/tmp/claude/probata-runs/t18/`, no verifier job):
`test_archevolve_proof_path`, `test_format_doc`, `test_proof_records`, `test_level_rule`,
`test_counterexample_repair`, `test_proof_method_version`, `test_functional_evaluation`, `test_extensa_boundary`,
`test_bfs_package_handoff`, `test_derived_implementations`: 325 passed, 1 skipped, `-m "not whole_store"`, 17 min
(`r2.jsonl`, sha256 `64b8b7bdf2cd84813d913d4c243df6e0b496e2ffb36ebca24a298f654fbf345a`); `test_bfs_acceptance_report -k
evaluation_message`: 2 passed (`r3.jsonl`, sha256 `b8eebe740c22afe24aa7cc23d92b8addc16679ef7968ca5bd79ccf7bb87588af`).

**Assumptions** (the map leaves these open):

- Assumption: `swdb submit` leaves the candidate artifact unverified and `swdb certify` certifies it, so the
  gate is driven by `swdb prove --proof-path bounded` after `swdb certify` (the ticket's "submit, then
  repair" note); repaired candidate artifacts are certified and gated inside that call.
- Assumption: the unbounded rung is a separate step (`--proof-path unbounded`) the operator runs after the
  evaluator's measurement; ArchEvolve mode has no campaign timeline, so nothing checks for an open timing
  step. It runs whether or not there is a gain.
- Assumption: `final_candidate` is the submitted candidate artifact when not refuted, else the repair that
  ended the loop `repaired` or `reverted` (a reverted repair keeps its own level), else none.
- Assumption: the unbounded rung needs a gate run first (proof records in a `batch.gate.<candidate>.` batch).
- Assumption: level sentences are generic ("Proven for every size and every thread count (threads: any; ...)",
  "Proven within bounds (...: up to N)"), not BFS words; assumption templates fill only the reference ID,
  which must be an identifier; an assumed clause reference is `<contract>#<clause>` (ticket 10's fixture form).
- Assumption: not proven, `proof_records` lists every proof record of the candidate artifact (skips too);
  `failures` adds `refuted` and `stale` (earlier proof stopped counting) with fixed words beside the failure
  classes and skip reasons.
- Assumption: format 1.2 applies to every evaluation result (1.0 content, or 1.1's functional fields, plus
  the block); the block is checked where it is rendered, not by `swdb validate`.
- Assumption: the ArchEvolve derived implementation lives in the store that certified it (research
  database); nothing reaches LANL's main database before promotion, which is not built.

**Side findings**

- The checked-in examples `docs/bfs-handoff-examples/evaluation-result.*.json` are now stale (they lack the
  block and say format 1.0). Regenerating them renders from the whole 1.2 GB store; the first message timed out
  at 600 s here (store validation), so they were not regenerated. `scripts/bfs_handoff_examples.py --check`
  now keeps each archived snapshot's date. The `whole_store` test `test_checked_in_handoff_examples_are_current`
  fails until someone runs `python3 scripts/bfs_handoff_examples.py --mode extensa --campaign
  extensa-gem5-bfs-20261004-a7` with a longer per-message timeout.
- Under level-rule.1 the multi-thread minimum-bounds derivation caps the `threads_k` record's thread count:
  run at k = 3 with a derivation at threads 2, the level's bounds read threads 2.
- 2026-10-14 (main session, suite fix `0105df78`): the derived-implementation hook moved out of
  `swdb/certification.py` `run_cli` into `swdb.archevolve_proof.certify_cli` (called by `swdb/cli.py`),
  because every frozen candidate, native and lowering_calibration procedure version hashes
  `certification.py`; editing it broke 10 frozen digests. `certification.py` is byte-identical to `c98db87c`
  again. The Answer's mention of `certification.run_cli` (around line 132) is superseded by this line.
