# Counterexample-guided repair (`swdb repair <proof record>`)

Created: 2026-10-14 (Eastern Time), Probata proof of concept ticket 13.
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/13-counterexample-guided-repair.md`; design:
`.scratch/formal-verification-2026-10-09/spec.md` ("Refutation, repair and bugs"); glossary:
counterexample-guided repair, reverted repair, spurious counterexample.

**In one line:** a refuted proof record sends its counterexample to the rewriting role, which makes a
new candidate artifact; the loop runs at most `budgets.counterexample_repair_rounds` rounds (5), one
provider call each, and flags a repair that no longer applies the contract.

## Who calls what

| Caller | Entry | Setting |
|---|---|---|
| ArchEvolve mode (18), anyone outside campaigns | `swdb repair <proof> --runs-dir D --provider-config P` (one round) | `archevolve` |
| The evaluation (RQ4, O1, O5) | `swdb repair <proof> --evaluation-run ...` (one round) | `evaluation` |
| `swdb campaign` (14), ArchEvolve mode (18) | `swdb.counterexample_repair.loop(records, proof, runs_dir=, provider_config=, certify=, gate=, setting=)` | `campaign` / any |

`swdb.counterexample_repair` owns the cap and the reverted-repair flag for every mode; callers never
re-implement either. `--run-index N` (1-3) puts the run field on the new proposal.

## What a round does

1. **Filter (`repairable`).** Only a `refuted` proof record with its counterexample inline, about a
   candidate artifact's proof unit, starts a round. A `spurious_counterexample` record (or any record with
   `unreplayed_counterexample`) is refused by name: it is a tool or encoding failure, never repaired.
   Anything else `not_proven`, `proven` or a skip is refused too. Nothing is written; no call opens.
2. **Checks before any record or call:** the record pins the candidate artifact's current tree; the
   candidate artifact has a proposal (its request, intent and profile package are kept); outside an
   evaluation repair run it must be certified (O1 applies to the evaluation only); round r =
   (round of the refuted candidate artifact's own lineage, or 0) + 1; round r > cap is refused as
   "budget spent" (a loop outcome, not a proof failure class); a round whose call already opened on that
   candidate artifact is not repeated.
3. **One rewriting-role repair call** in the guarded rewriting workspace over the refuted tree. The
   workspace shows `.swdb-context/counterexample.json` (format `swdb.counterexample.v1`) and
   `.swdb-context/refuted-candidate.diff`; the manifest's `repair_inputs` holds `{path, sha256, bytes}` of
   each. The attempt is recorded with `call: counterexample_repair`, `role: rewriting` (never a
   proof-hint call; repair calls stay in the rewriting total).
4. **A new candidate artifact:** proposal `<root proposal>.cex-repair-<round>` with `repair_lineage`
   ([format-v0.4-proof.md](format-v0.4-proof.md#run-fields-and-repair-lineage-ticket-12)), `provider_pin`
   (when the provider is Codex or Claude or a fixture emulating one) and `repair_budget {counterexample_repair_rounds,
   round, setting}`; candidate `<proposal>.candidate-1` with `parent_candidate`. Its state is `unverified`:
   it is certified and gated by `swdb prove`'s bounded rungs before anything else uses it. No record of
   the refuted candidate artifact changes.

`swdb repair` output: the new proposal (exit 0 on `candidate_created`, 1 otherwise), or, when the cap is
reached, `{outcome: {state: unresolved, stage: counterexample_repair, reason}, loop: {state: budget_spent}}`
with exit 1 and nothing written.

## The contract-match check (reverted repair)

Deterministic, no LLM; runs on every repaired candidate artifact; result in `attempts[].contract_match`
and `repair_lineage.reverted_repair`.

- `equals_baseline`: the repaired tree's normalized content hash (C/C++ files without comments and
  layout, other files by bytes) equals the baseline implementation's (its source snapshot).
- `drops_offload`: an offload call the refuted candidate artifact made in its editable files is gone.
  The contract's offload calls are the function names in the `signature` of every intrinsic it uses,
  directly or through library operations.

A flagged repair stays a candidate artifact at its own level; it never counts as a repair.

## The loop (`loop`)

Each round: `repair_round`, then `certify(candidate)`, then `gate(candidate) -> [proof record IDs]`.
Round r repairs what round r-1 made, citing its refutation. Outcomes (never a failure class):
`repaired` (not refuted; counts as a repair), `reverted` (flagged; ends the loop), `budget_spent`,
`certification_failed` (the build or correctness repair cap may apply), `provider_failed`. A spurious
counterexample from the gate never continues the loop. The result lists `calls`, `repairs`,
`reverted_repairs` and the `chain` of rounds.

Ticket 14 (2026-10-14 ET): optional `charge`. Before each round's call, once the cap allows the round, the
loop calls `charge()`; it returns a callable the loop calls with the round's proposal (None if the round
raised), or None to refuse the call, which ends the loop `calls_refused`. A campaign charges its D7 ledger
and lane-hours here. In a campaign, `gate` returns no proof record for a flagged (reverted) repair: it
applies no contract, so it gets no bounded job.

## The guard

- **Counterexamples** (`provider_workspace.refuse_counterexamples`): any provider-visible file holding
  the `swdb.counterexample.v1` format name, or a `counterexample` / `unreplayed_counterexample` key in a
  JSON or YAML file, is refused before a call opens, in every agent-role workspace (profiling,
  estimation, independent test generation, synthesis, the campaign roles) and every rewriting workspace,
  except the one counterexample file of a counterexample repair workspace.
- **The authors' accelerated functions** (O5): the rewriting workspace (and the prompt-only route) refuses
  them, except in an evaluation repair run (`--evaluation-run`) whose refuted candidate artifact is the
  tree the workspace shows. The mark is the manifest's `evaluation_repair {refuted_candidate,
  tree_sha256}`; campaigns and ArchEvolve mode never set it.
