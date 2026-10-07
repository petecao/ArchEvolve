# Ticket 17 metadata cap revision

Date: 2026-10-07 ET. Population freezing and all four campaigns remain **NOT RUN**. Ticket 17 remains claimed. C/F6, D30, selection and plateau remain fixed.

Transfer exact `17-metadata-caps-helper-20261007-a2.py` bytes to `/data1/yanruj/lanl17-control-caps-20261007-a2.py`. Its SHA256 is `09136ee553984b2c0cf929a6746f037aa4e1874f863aa2e83e0e0842a8b65ed9`. Original control `31e` and its a1 receipt remain unchanged.

Exactly four complete source lines differ:

| Call | Original cap | New cap |
| --- | ---: | ---: |
| Prepare: validate-before-freeze | 900 s | 1400 s |
| Prepare: population-freeze | 900 s | 1400 s |
| Finalize: each of four campaign validations | 900 s | 1400 s |
| Finalize: validate-final-export | 1200 s | 1400 s |

Reversing only those four lines reproduces the original bytes. Every other helper byte is identical, including export caps of 900 s, agreement-report at 1200 s, campaign limits of 24 lane-hours, cleanup at 600 s, outer allowance of 1200 s, disk at 20 GB, iterations at 8, plateau at 4, provider/lease/source guards and statistical policy. These are administrative allowances, not measured upper bounds; see `11-metadata-processing-source-audit-20261007.md`.

All **seven** existing budget-module cases passed in 2018.83 s, and all 14 portable controls passed. The earlier denominator of 8 was a counting error. An additional existing plateau test had already finished in 0.07 s; it is recorded separately and does not pad the required gate. Fixture numbers are not experimental evidence.

The parent ran the fresh bounded Linux smoke once on node 1 generation 543, 05:57:26–05:57:42Z, exit 0. Exact wrapper: `17-linux-cleanup-smoke-mbit10-20261007-a2.json` (SHA256 `ba6c9686b2847866e582949de96f2e188e299e5fe947b5ce5ce6a605ba21e99a`). Receipt seal: `3b2ab676c70098fb054fe40396dabc77d935817ae7eed72bc92d541c727e92d0`; raw receipt SHA256: `b1c34be10178dad05c9bfad64da7a19ea0961162ded1becc0982060111ec4232`. Helper `09136`, unchanged smoke `4d0` and actual processes.py bcc9 are pinned. Same-group and escaped-session descendants were terminated/reaped, the unrelated sibling survived, and there were no survivors, provider calls or application outcomes. The read-only checker correction did not rerun the smoke. Original a1 compact receipt is retained separately.

After native application timings and required downstream model/report gates finish, the parent may prepare a fresh source/raw/tag using exact final W/ref that preserves F6:

```sh
timeout --signal=TERM --kill-after=40s 4500s python3 /data1/yanruj/lanl17-control-caps-20261007-a2.py prepare \
  --source-sha FULL_FINAL_40_HEX_W --source-ref codex/FINAL_SOURCE_REF \
  --source /data1/yanruj/ArchEvolve-lanl17-NEW_TAG \
  --raw /data/yanruj/EvolveSWDB_runs/lanl17-NEW_TAG --tag NEW_TAG \
  --cleanup-proof /data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a2/smoke/receipt.json
```

Recheck live source/config/provider/model/baseline/input identities and inspect the completed policy Git export before any outcome. This revision is preparation, not dispatch authorization. A manifest sealed to `31e` refuses this new helper. Every dispatch/resume/finalize rechecks exact helper/processes/source, SG representations, baseline/model/runtime/config pins, original CODEX_HOME restoration, wrapper/lease/NUMA identity. One actual campaign per lane, at most two concurrently; stopped infrastructure attempts remain distinct from completed trajectories. Raw outputs stay remote.

After four genuine stores complete, finalize under the same helper/manifest:

```sh
timeout --signal=TERM --kill-after=40s 12000s python3 /data1/yanruj/lanl17-control-caps-20261007-a2.py finalize \
  --manifest /data/yanruj/EvolveSWDB_runs/lanl17-NEW_TAG/manifest.json
```

Retain the arguments/recovery rules from `17-prospective-campaign-runbook.md` and the inspected external README. A metadata timeout after durable publication does not justify rerunning scientific outcomes or inventing a new policy timestamp. Current unsupported SG/MMIO correspondence admits no numeric pairs or flow-B switch. Four actual validated stores and unchanged D30 remain required.
