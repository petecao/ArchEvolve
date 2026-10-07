# Freeze unknown analytic parameters

Updated: 2026-10-06 ET.

`fill-target-parameters` writes one new target-description version from a registered
characterization, its profile and the base target's declared numerical unknowns.
Every non-null answer has basis `estimated` and a reason. A null answer keeps basis
`unknown`. The base record and its known facts stay unchanged.

```bash
python3 -m swdb fill-target-parameters --records records \
  --characterization "$CHARACTERIZATION_ID" --profile "$PROFILE_ID" \
  --target-description "$BASE_TARGET_ID" --provider-config "$PROVIDER_CONFIG" \
  --output "$FRESH_OUTPUT" --id "$NEW_TARGET_ID" --format json
```

Add `--prepare-only` to write the bounded inputs without launching a provider.
The provider workspace contains exactly `characterization.json`, `profile.json`
and `parameters.json`, with a total limit of 10 MiB. It contains typed count facts,
profile structure and supported mechanism parameters. Timings, PMU ratios, source
and evaluator code, paths, free-form annotations and other candidates are omitted;
sealed snapshots and omission hashes preserve their custody.

The closed response must answer each declared unknown once with its parameter
identity, value, unit, basis and reason. Known-parameter overrides, duplicates,
wrong units, invalid domains and incomplete responses are rejected. A successful
all-null response also freezes the base ID/version; it cannot be retried to tune
assumptions. Actual providers use the existing launcher pins, enforced guard,
read-only workspace, event audit and login/process cleanup.

Only recognized numerical rate/cost contracts are fillable. Missing layout,
capacity, observation coverage, worker transfer, composition premises or failed
CPU service compatibility remain structural gaps. A numeric answer cannot waive
one of those gaps or change the observation policy.

Freeze a fresh estimate protocol using the new target, then run `estimate`. Its
`llm_parameters` lists the estimated facts and recomposes half/base/double
scenarios for each complete trial before taking the median. Unknown whole-call
totals remain null, with null impacts and ranks. Historical receipts remain
validatable after implementation changes; new execution requires a current
frozen protocol.

The [ticket10 execution and recovery receipt](../../.scratch/lanl-db-analytic-eval-2026-10-06/evidence/10-estimation-role-runbook.md)
records the actual guarded run and its evidence boundaries. See the
[analytic format](format-v0.4-analytic.md) for count, target and estimate fields.
