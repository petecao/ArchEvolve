# Actual PR / final CPU service replay

Prepared: 2026-10-07 ET. **Preparation only; actual model export and acceptance are pending.** Parent owns SSH, lanes, capacity checks and bounded child execution. No application, compiler, provider, calibration or rate fitting is invoked here.

Use the real model-exported `mbit10.cpu.lanl20261006.t1.services.v1`, its full semantic SHA-256, and a clean final source/ref containing every count/model dependency. Initial final C is `f893fed400347ed23d92e917d8bde21b75e5375d`, complete Python bundle `f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3`. A metadata-only descendant is suitable when its complete bundle is identical. Any code change requires a fresh explicit source/bundle gate.

Create a fresh external replay folder and copy the final source's records/library there. Pin the prior file inventory, source HEAD/clean state, complete bundle and real exported target before the two public commands. Keep the prototype protocol/estimate in this isolated replay catalog. The reviewed nine-report helper creates its own fresh eighteen-record closure.

Set `FINAL_SOURCE` to the exact clean project checkout, `FINAL_SOURCE_SHA` to its full HEAD, `FINAL_BUNDLE_SHA` to the verified complete bundle, `CPU_TD_SHA` to the real exported target's semantic hash, and `REPLAY_RAW` to the fresh external folder. Set `REPLAY_REQUEST` and `REPLAY_CHECKER` to the exact delivered, hash-verified preparation files in the external control folder (or the owned Git evidence paths). These files can be staged separately while the frozen C checkout remains immutable. Use SWDB cwd and explicit `PYTHONPATH` for external helpers:

```sh
cd "$FINAL_SOURCE/swdb-project"
export PYTHONPATH="$FINAL_SOURCE/swdb-project"
export PYTHONDONTWRITEBYTECODE=1
export OMP_THREAD_LIMIT=16
```

Parent launches these child argv under its inspected bounds and process-group/subreaper cleanup: freeze 400 s, estimate 600 s, checker 200 s. The recipe is lane-neutral; parent records the actual confinement/leases and keeps elapsed jobs isolated.

```sh
python3 -m swdb freeze-protocol \
  "$REPLAY_REQUEST" \
  --records "$REPLAY_RAW/records" --format json
```

Save stdout as `freeze.json`; obtain `PR_PROTOCOL_ID` from its `id`. The request pins the actual immutable PR count scope: original Jacobi implementation plus registered CPU source snapshot, `kron-g16-k16`, `-g 16 -k 16 -n 5`, `gapbs.functional_trial_lambda.v1`, T1. Actual characterization semantic/file hashes remain `73b9bd54…` / `168204cc…`; all five source lists are empty.

```sh
python3 -m swdb estimate \
  --records "$REPLAY_RAW/records" \
  --characterization pagerank.jacobi.kron-g16.cpu.t1.characterization.generality.a1 \
  --target-description mbit10.cpu.lanl20261006.t1.services.v1 \
  --protocol "$PR_PROTOCOL_ID" \
  --id generality.pagerank.cpu.kron-g16.t1.estimate.final-admission.a1 --format json

python3 "$REPLAY_CHECKER" \
  --source "$FINAL_SOURCE" --source-sha "$FINAL_SOURCE_SHA" \
  --estimator-sha256 "$FINAL_BUNDLE_SHA" --target-sha256 "$CPU_TD_SHA" \
  --records "$REPLAY_RAW/records" --protocol "$PR_PROTOCOL_ID" \
  --estimate generality.pagerank.cpu.kron-g16.t1.estimate.final-admission.a1 \
  --output "$REPLAY_RAW/actual-pr-services-acceptance.json"
```

The checker reads canonical metadata through the public Store/access boundary, verifies registered source/input/ROI proof and frozen dependency identities, and requires clean exact source/bundle pins. The CPU target and every scoped selector retain exactly the four BF/BC g16/g17 T1 characterizations with unchanged hashes. Aggregate and each of the five trial bounds must explicitly include both `service_scope.characterization_allowlist` and `memory_scenario.characterization_allowlist`. Whole-call/trial seconds, ratio, baseline and PR error band stay null. Zero, a numeric substitute, a borrowed band, expanded/re-pinned PR admission, or changed trial/source/target pins fails acceptance. No service parameters are modified.

Keep all prior catalog/source/library bytes unchanged; the isolated catalog may add only its new protocol and estimate. Seal child exit/cleanup metadata and original target/model-export custody alongside the checker proof. Preserve any failed attempt. Actual acceptance is recorded only after the real export and both public commands pass.

## Nine-report acceptance

Use the unchanged reviewed helpers in `/private/tmp/lanl14_final_helpers_README.md`, pinning the final executable SHA/ref, identical complete bundle, actual CPU semantic target hash, filled DX target and data-only MAPLE target. Their preparation/dispatch/export source hashes remain those in `14-final-acceptance-preparation-20261007.json`.

Acceptance requires all nine unique BF/BC/Jacobi × CPU/DX100/MAPLE pairs, exact T1/T4/T2 and target-specific ROI/argv/source identities, six actual new count cases and three strictly admitted immutable historical counts. Freeze a new DX BFS reference first; all nine protocols/estimates and the report module manifest use the same final estimator/mechanism code. Verify every exact trial formula input/bound/overhead/missing fact and all unmapped loops. Aggregate medians are diagnostic and are never summed into whole-call costs. Unknown required costs remain null; PR receives no four-scope CPU service/band transfer; MAPLE is estimate-only without paired timing/accuracy. Ratios and baselines remain null across these distinct protocols/targets.

After exit zero, canonical validation, clean source, prior-byte preservation, released leases and empty owned-process cleanup, export exactly nine protocols, nine estimates and the reviewed compact report/request/custody paths. Ticket 14 remains claimed until actual replay plus this all-nine closure is verified. The six successful a1 count receipts remain immutable; recovery was unused.
