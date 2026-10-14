# ArchEvolve mode's proof path (`swdb prove --proof-path`)

Created: 2026-10-14 (Eastern Time), Probata proof of concept ticket 18.
Spec: `.scratch/probata-proof-of-concept-2026-10-13/issues/18-archevolve-mode-level-and-handoff.md`; design:
`.scratch/formal-verification-2026-10-09/spec.md` ("ArchEvolve mode"; S1, S6; O1, O7), map decisions 25 items
2, 3, 5 and 26 item 7. Code: `swdb/archevolve_proof.py`. The handoff block: [bfs-handoff-contract-v1.2.md](../bfs-handoff-contract-v1.2.md).

**In one line:** a rewrite proposal's one final candidate artifact, once certified, gets Extensa mode's proof
steps with the same per-candidate budgets, and the team reads the result in the handoff's
`certification_level` block.

## The order

1. `swdb submit` makes the candidate artifact; `swdb certify <contract> --candidate <c>` certifies it.
2. `swdb prove --proof-path bounded ...`: the bounded gate (`swdb.bounded_gate.Gate`, the one Extensa mode
   runs): both rungs at the contract's minimum bounds, threads raised to the method version's `civl_k` on the
   multi-thread rung, `bounded_job_minutes` per job; skips per O7. A refutation, with `--provider-config`,
   calls 13's counterexample-guided repair loop (setting `archevolve`): the mode's allowed bounded correctness
   repair. Each repaired candidate artifact is certified (`swdb.certification.certify`, then the derived
   hook) and runs this same gate. The 5-round cap and the reverted-repair flag are the loop's.
3. The evaluator's measurement of the final candidate artifact (`swdb evaluate`).
4. `swdb prove --proof-path unbounded ...` (S6): a candidate artifact the bounded rungs did not refute
   (proven, timed out, or skipped) runs one unbounded job per proof unit, with the method version's
   `hint_rounds` and `hint_loop_wall_minutes`, whether or not it showed a gain. A refuted candidate
   artifact is refused; so is one that has not run the gate.
5. `swdb handoff-message evaluation_result <evaluation>`: the envelope carries the block.

An uncertified or rejected candidate artifact runs no proof step (exit 1, nothing written). An Extensa
campaign's candidate artifact is refused: its campaign runs its proof steps. ArchEvolve mode has no campaign,
so `provider_calls_proof` and campaign lane-hours do not apply.

## Output

- `bounded`: `{candidate, gate, counterexample_repair, repairs, final_candidate}`. `gate` is the bounded gate's
  result (method version, `budget_minutes`, `k`, `jobs`, `refuted`, `refutations`). `counterexample_repair` is
  null without a refutation, `{state: not_started, reason}` without a provider configuration, else the loop's
  outcome (`state`, `reason`, `cap`, `rounds`, `calls`, `repairs`, `reverted_repairs`). `repairs` lists each
  round's `{round, proposal, candidate, trigger, reverted_repair, gate}`. `final_candidate` is the candidate
  artifact that goes on (the submitted one, or the repair that ended the loop `repaired` or `reverted`), else
  null.
- `unbounded`: `{candidate, method_version, budgets, batch, jobs, level}`; each job has `contract`,
  `position`, `record`, and `verdict`, `stages` (`wp`, `seeds`, hint rounds) and `failure_class`, or
  `skip_reason`.

## The scripted proof plan (`--adapter scripted --plan`)

No real verifier adapter is built yet (21, 22, 46, 47), so `--proof-path` takes only the scripted adapter.
Plan file (YAML), contract fixtures only:

```yaml
plan: archevolve_proof_fixture.1
candidates:                 # row 0: the submitted candidate artifact; row r: the round-r repair; the last repeats
  - threads_1: refuted      # proven (default), refuted, timeout, spurious, or {verdict: ..., <scripted-adapter keys>}
    threads_k: proven
    unbounded: {proven_at: wp}   # wp, seeds, a hint round, or absent (never: hint budget spent);
                                 # also unit_postcondition (default true), bounds, assumptions, tools
    cpp_subset: true        # false: threads_k and the unbounded rung are skipped (outside_cpp_subset)
```

## `swdb certify`'s derived-implementation hook

See [format-v0.4-derived.md](format-v0.4-derived.md#when-one-is-written): a certified enabling rewrite
proposal's result becomes a derived implementation in the store that certified it.
