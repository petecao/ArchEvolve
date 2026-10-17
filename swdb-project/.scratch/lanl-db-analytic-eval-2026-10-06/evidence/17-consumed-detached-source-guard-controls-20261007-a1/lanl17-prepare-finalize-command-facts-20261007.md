# Ticket17 prepare/finalize command facts

2026-10-07 ET. Source-only extraction from unchanged selected28/fa/9c and the existing runbook/construction contract. No helper/import/Store/test/SSH/Git mutation or project write. Final R, M2, publication, campaigns and actual17 admission remain unavailable. The a4 paths below are the existing prospective routes; their freshness is an actual parent preflight, not a fact established here.

## Exact parent command shapes

Only `REQUIRED_FINAL_R_40HEX` is an unresolved commit placeholder. The cleanup identities are the original actual a4 identities retained in the separate durable actual-proof archive, not the compact wrapper identities. The first proof uses original default canonical ensure_ascii=true; the supervisor proof uses false. Neither original is rewritten to add a policy field.

Prepare uses the later selected clean immutable C project. Its repository must already contain final R, with all185 Python Git modes/blobs equal C/F6. This guard check happens **before** helper prepare fetches the primary. Preserve C HEAD and primary retention.lock.

```sh
lanl17_final_r=REQUIRED_FINAL_R_40HEX
env SWDB_LANL17_ORIGINAL_CODEX_HOME=/data1/yanruj/.codex \
  CODEX_HOME=/data1/yanruj/.codex \
  timeout --signal=TERM --kill-after=60s 18300s python3 /data1/yanruj/lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py \
  --action prepare --final-source-sha "$lanl17_final_r" \
  --guard-sha256 9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6 \
  --project /data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1/swdb-project \
  --control /data/yanruj/EvolveSWDB_runs/lanl17-metadata-prepare-20261007-a4 \
  --cleanup-proof /data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a4/receipt.json \
  --cleanup-proof-identity 18e58a44476709cc7520f9760ac94161cd67248e39ff662fbfb16378855d7ca1 \
  --supervisor-proof /data/yanruj/EvolveSWDB_runs/lanl17-metadata-supervisor-fixture-20261007-a4/receipt.json \
  --supervisor-proof-identity ea9751eef12bc519be0c4159813e29fa5aa378693c6a31caea137599c5db744b -- \
  --source-sha "$lanl17_final_r" \
  --cleanup-proof /data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a4/receipt.json \
  --source-ref codex/lanl-analytic-eval \
  --source /data1/yanruj/ArchEvolve-lanl17-source-20261007-a4 \
  --raw /data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a4 \
  --tag 20261007-a4
```

Finalize has exactly one helper-tail flag: `--manifest`. This path must be the original M2 produced by the successful prepare above; its bytes/identity and the actual policy/EF are unknown until then. Finalize's project must be that M2's detached source at exact R.

```sh
env SWDB_LANL17_ORIGINAL_CODEX_HOME=/data1/yanruj/.codex \
  CODEX_HOME=/data1/yanruj/.codex \
  timeout --signal=TERM --kill-after=60s 78300s python3 /data1/yanruj/lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py \
  --action finalize --final-source-sha "$lanl17_final_r" \
  --guard-sha256 9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6 \
  --project /data1/yanruj/ArchEvolve-lanl17-source-20261007-a4/swdb-project \
  --control /data/yanruj/EvolveSWDB_runs/lanl17-metadata-finalize-20261007-a4 \
  --cleanup-proof /data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a4/receipt.json \
  --cleanup-proof-identity 18e58a44476709cc7520f9760ac94161cd67248e39ff662fbfb16378855d7ca1 \
  --supervisor-proof /data/yanruj/EvolveSWDB_runs/lanl17-metadata-supervisor-fixture-20261007-a4/receipt.json \
  --supervisor-proof-identity ea9751eef12bc519be0c4159813e29fa5aa378693c6a31caea137599c5db744b -- \
  --manifest /data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a4/manifest.json
```

These are parent command facts, not executable clearance. GNUtimeout must directly parent python3/python3.12 and the exact guard; an intermediate wrapper would fail `parent_envelope`. Each helper-tail flag occurs once, with no extra flags. Guard control directories must be fresh immediate children of RUNS named `lanl17-metadata-*`, separate from raw. Prepare source/raw must be fresh immediate children of their approved parents; no overwrite of occupied attempts. There is no standalone export action: prepare and finalize each perform their own public Git export.

## Prerequisites and finite allowances

| Gate | Exact source requirement |
| --- | --- |
| Source/dependencies | Parent first admits actual11 and actual14, then selects/delivers full40hex R/tree. C/F6 Python185 and processesbcc9 remain exact; final R object is already present in prepare's cleanup-project repository. Clean detached source at R, unchanged config/policy/raw inputs thereafter. |
| Host/account | Linux mbit10, non-root; receipts owned by the executing UID. Parent verifies the intended account/UID separately. Account HOME remains `pwd` home. Restored CODEX_HOME is `/data1/yanruj/.codex`; auth existence only, no credential reads. |
| Leases | Node0, node1 and legacy leases all released before and immediately before metadata exec; prepare/finalize helper also rechecks all_free. Metadata uses no socket lease. |
| Actual controls | Exact28d helper, fa703 supervisor, 9c5d guard, F6, processesbcc9; exact original4d/a848 a4 proof paths/identities, passed and subreaper/survivors{} with no providers/outcomes. Fixtures are cleanup evidence only. |
| Prepare capacity | MemAvailable≥80GiB, `/data1`≥21GiB, `/data`≥24GiB before allocation. Dispatch separately requires `/data`≥44GiB if the owned sibling is active. These are unchanged floors, not proof two full R checkouts and five raw catalogs will fit. |
| Native/source prerequisites | Fresh fetched MemAcc wrapper byte-match; tmux/numactl/strace/timeout available. Exact official Codex entry/native hashes and `codex-cli 0.153.0`, provider_guard ABI≥4. Eight distinct canonical SG workload identities, source0 outdegree>0 and both app representations; baseline artifact/source, T4 template and actual simulation build/runtime files checked. |
| Frozen campaign config | CIDs `extensa-gem5-bfs-20261006-p1..p4`; budgets exactly iterations8, plateau4, lane_hours24, per-iteration provider calls3/setup1, disk_gb20, lanes1; paired estimates enabled, sources[0]. Only copied runs_root becomes this raw's `campaign-runs`. |
| Finalize | Retained sealed M2 at `raw/manifest.json`, exact R/helper/F6/original cleanup proof; unchanged configs/library/frozen records/live source-input-model pins/provider/wrapper. All four actual fresh stores and original stopped receipts must exist. No fixtures or manufactured summaries. |

| Metadata action | Supervisor wait | Inner TERM / hardkill grace | Direct parent TERM / grace |
| --- | ---: | ---: | ---: |
| prepare | 18000s | 18120s /60s | 18300s /60s |
| finalize | 78000s | 78120s /60s | 78300s /60s |

Nested prepare validation3600s, public freeze6000s; finalize per-campaign validation3600s, conditional public export6000s each, agreement-report14400s, final validation3600s. Fixed Git operations120s and CLI-version10s. These administrative caps have no runtime guarantee. Separate actual campaign bounds remain87000s inner/88200s enclosing/kill60; they are not enlarged by metadata allowances. Failure retains raw and any atomically published records; inspect before conditional reuse, never infer completion or blindly replay.

## Original output/receipt retention

1. **Every metadata action:** exact outer start/exit/stdout/stderr originals; control `preregistration.json` (original seal false), `supervisor-receipt.json` (false), `helper.stdout`/`helper.stderr` (unsealed). Retain file sizes/SHA and original source-policy pins. Registration binds action/UTC/R/cleanupHEAD/F6/source/raw/project, all control/process hashes, both actual-proof fileSHA/identity, limits/direct parent PID/start/argv hash, released leases, helper-tail/child argv hashes and HOME/auth-existence scope. Supervisor binds actual UTC/elapsed/deadline/state/timed_out/signal, child/outer exits, control hashes/F6/UID, subreaper/owned cleanup/survivors/errors. Successful administrative cleanup alone does not admit population or campaigns.
2. **Every public helper command:** raw `<name>.argv.json`, `<name>.stdout`, `<name>.stderr`, `<name>.exit-code.txt`. Exit file is written only after the wait returns; preserve its absence on interruption. Names: `validate-before-freeze`, `population-freeze`; finalize `validate-<CID>`, conditional `export-<CID>`, `final-agreement-report`, `validate-final-export`. Original command/log contents remain remote; reviewed compact metadata contains bounded allowed fields/hash custody only.
3. **Prepare:** original `manifest-before-freeze.json`, unchanged copied configs, initial records/library inventory, public policy, nested **M1** in freeze receipt and final **M2** `manifest.json` (seal true). M2 adds original `freeze_export` to M1 and changes identity; never rewrite either. Retain original source/provider/wrapper/capacity/leases/live baseline/input/model pins, policy ID/identity/frozen_at and frozen-base file hashes. Freeze receipt `swdb.lanl17-freeze-receipt.v1` retains M1/public policy, outcomes_opened0/population_frozen. Public Git EF branch `codex/lanl17-freeze-evidence-20261007-a4`, sole parent R, exact tree/additions/configs/policy and `17-freeze-mbit10-20261007-a4.json`; checkout `ArchEvolve-lanl17-freeze-evidence-20261007-a4`. Helper stdout returns manifest path/R/policy/export branch+commit+paths/raw_transferredfalse/dispatches0. Preserve actual publication evidence before any dispatch/outcome.
4. **Campaigns/finalize:** every original numbered dispatch/stopped receipt plus release/ownership and before/after b08 custody; all four exact public stores, original validation outputs, full validated index, selected component/reference bodies and actual public campaign-export stdout. Finalize exports named completed non-rejected candidate closures only; rejected/interrupted materialized roots require separate original selected-body custody under E342. It requires execution summaries/targetdx100_gem5, but summary existence is not the strict auditor's substantive normal-terminal evidence.
5. **Final report/export:** original public report, `swdb.lanl17-actual-agreement-compact.v1` (seal true: M2/stopped_attempts/public_report/source_clean/raw_transferredfalse), `final-export.json` and stdout. ER branch `codex/lanl17-actual-report-evidence-20261007-a4`, sole parent R/exact additions/tree and `17-actual-report-mbit10-20261007-a4.json`; checkout `ArchEvolve-lanl17-actual-report-evidence-20261007-a4`. Original helper asserts observed_campaigns4, eligible_dx100_pairs0, gateunsupported, do_not_switch_to_flow_b, selectionunchanged_timing_only. These tokens cannot replace strict6a trajectory/component/preceding-forecast/dependency/publication checks or demonstrate attained numeric agreement.

## Concrete route and readiness dispositions

- Earlier primary `--project /data1/yanruj/ArchEvolve/swdb-project` example conflicts with preserved untracked retention.lock. The later archived selection above uses clean immutable C, with R delivered to its object database first. Helper prepare still fetches/creates its new detached worktree through PRIMARY; it does not ask to clean/remove that lock.
- The original guard note's “new Linux checks NOTRUN” is creation history. Separate exact actual a4 receipts now supply identities above; do not overwrite the preparation or substitute earlier69/166 receipts. Actual prepare/finalize/population/campaign/report prereqs still do not exist.
- Existing capacity observations are not prepare/dispatch clearance. Final R sizes are unknown; 28 allocates a new detached source W and full EF W on `/data1`, plus base+four raw record/library catalogs on `/data`; ER later adds another full W. Actual finite size/free-space planning and all-three-released live guards are necessary without floor bypass or speculative deletion.

## Exact source pins and pointers

- `/private/tmp/lanl17_parent_helpers_cleanup60_a4.py`: `28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414`; run_cli171, prepare280, load_manifest368, finalize596, main640.
- `/private/tmp/lanl17_metadata_supervisor_cleanup60_a4.py`: `fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0`; load_context34, supervise49, main97.
- `/private/tmp/lanl17_metadata_dispatch_guard_cleanup60_a4_20261007.py`: `9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6`; limits36, direct parent73, tails79, main88.
- Guard note `/private/tmp/lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.md`: `fa0d7f4dc075d2ef756c35563f1ec254811218dfa2e16d339aa537dfb087ad9d`.
- Accepted construction plan `/private/tmp/lanl17-r1s1-future-actual-input-construction-plan-20261007.md`: `e3420b334ce05f7268699b0079987d1d2afc98fe5cb5503e6069a89038b59170`.
- Existing evidence `17-prospective-campaign-runbook.md`: `b19675814b5c0a098f9cb6d05697b37de697774f10b291ad6025be6b07a7ce5d`; historical prior-helper examples stay exact.
- Evidence `17-cleanup60-metadata-controls-20261007-a4/README.md`: `50370a84537adf51ccb9a2ba54896308801fb61e59e0b02027b8596c1519013e`; later C-project selection. Actual proof archive `17-cleanup60-controls-actual-20261007-a4/` retains original smoke fileSHA `873d36971b55e903731c9ab44a93ba5f1d8f3c563d0cf6dcefb2a48c8a6b063e` and supervisor fileSHA `12546c476589f3eceb6f779f53b710b8bd623c643b3417461fd4f21774c07436`.
