# Ticket 17 prospective campaign runbook

Created: 2026-10-06 ET. Preparation only: no population freeze or campaign dispatch has occurred. The parent owns mbit10 source synchronization, two socket lanes, provider auth restoration, dispatch and compact Git export.

The current real paired adapter has no verified exact registered SG / complete-call MMIO numeric correspondence. All real forecasts therefore remain structural unknowns. Fresh campaigns are still required to audit ordering and unchanged flow-A selection, but cannot establish D30 accuracy. The expected primary result is zero eligible pairs, unsupported rank/interval/top3 and a recommendation to retain flow A. Twenty unknowns, repeated trials, aliases or synthetic fixtures cannot satisfy the twenty-pair requirement. Yan-Ru retains ticket 18's final choice.

## Population and immutable source

Four unexecuted campaign YAMLs pair K/uniform g18 edge factors 14, 15, 17 and 18, each source 0 and four workers. Exact registered canonical graphs and SG32/SG64 representation hashes are in source-only receipt `17-prospective-inputs-mbit10-20261006-a2.json` (identity `79d97e7702f24f061cc162063948c57da231d4b47f5c270ab040657e151d7f17`). Its setup/validation checked both widths, source zero, canonical adjacency and collisions against earlier registered graphs. Input registration is not statistical preregistration.

The drafts retain the existing protected scalar baseline `typed-library-bfs-gem5-20261003-a2.baseline`, one shared per-class baseline, required correctness companions, timing-only candidate selection, eight iterations, four plateau iterations, 24 lane-hours per campaign, three provider calls per iteration plus one setup call, 20 GB storage and one lane per campaign. No default trajectory guarantees twenty unique eligible pairs. Keep all normal stops and refusal paths; do not extend budgets after outcomes to achieve a count.

Before freeze, the parent must seal one final clean checkout W containing final generic 10/11/12/16/17 changes. Pin Git commit, portable all-Python estimator digest, baseline candidate record/artifact, model-build evaluation and simulator/configuration source hashes, guest compiler/version/flags, actual source/backend and protected ROI. Preserve actual functional-to-MMIO differences: a FUNC trial-lambda observation is not a rate-rebindable MMIO complete-call observation. Pin exact input/canonical representation identities, companion tuple/configuration and known prior exposure separately. A fresh campaign ID does not make a historical artifact or companion tuple fresh.

Future typed reports may be appended elsewhere while W remains unchanged. Campaign freeze, all launches/resumes and final `agreement-report` must execute the same immutable W. No hot changes to `swdb/**/*.py`; a changed portable bundle refuses continuation/report and requires a new prospective population before any timing. Do not rewrite the old policy or count receipts.

## Provider scaffold and lane preflight

The source-only provider scaffold contains the official configured entrypoint `/data1/yanruj/.npm-global/bin/codex`, never credentials or model/effort overrides. Actual10a2 verified CLI 0.153.0, entrypoint SHA `61b0194f3bb6534439c8d26a3ed57d0805f84b884588b761795323eeb92fcf70`, and official native binary `/data1/yanruj/.npm-global/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex` SHA `fce635028842bfe9257140e8b7d53162732945e2f356fc35225be0702b4974be`. Recheck these outcome-free identities before sealing W. The adapter verifies the official npm package/dependency/architecture before native launch. Code pins `gpt-5.6-sol` / `xhigh`; retain this source identity.

The socket wrapper must preserve the account HOME and restore the original verified `CODEX_HOME=/data1/yanruj/.codex` before campaign launch. Verify the environment value and directory existence in the actual leased child, without reading auth files or printing tokens. Use the already proven task-token lane setup/restoration method from actual10a2; never source a shell fragment that silently repurposes CODEX_HOME. The guarded provider creates its own isolated role workspace/home through the established provider runner.

Read fresh socket leases, wrapper identity, active processes, memory/storage and load before dispatch. At most two campaigns may run concurrently, one on each free socket lane; each retains `budgets.lanes: 1`. Queue the remaining two prospectively frozen configurations. No worker starts an unleased lane or competes with elapsed native calibration. Preserve the wrapper's resource checks and the campaign's 20 GB/24-hour bounds. If infrastructure interrupts a campaign, preserve its receipt and resume under unchanged W/config/provider; never fabricate a completed iteration.

## Public population freeze

Work from `W/swdb-project`. Parent-selected absolute variables below are placeholders, not extra configuration fields. Put all four final YAML files and the provider scaffold under the immutable project evidence directory. Keep the configured runs root identical in the YAML and CLI. Use an isolated copied team store for this population; preserve canonical historical bytes.

```sh
python3 -m swdb validate --records "$lanl17_records"
python3 -m swdb agreement-freeze \
  --campaign-file "$lanl17_configs/extensa-gem5-bfs-20261006-p1.yaml" \
  --campaign-file "$lanl17_configs/extensa-gem5-bfs-20261006-p2.yaml" \
  --campaign-file "$lanl17_configs/extensa-gem5-bfs-20261006-p3.yaml" \
  --campaign-file "$lanl17_configs/extensa-gem5-bfs-20261006-p4.yaml" \
  --provider-config "$lanl17_configs/provider-codex.yaml" \
  --records "$lanl17_records" --mode extensa \
  --campaign extensa-gem5-bfs-20261006-p1 --format json > "$lanl17_receipts/population-freeze.json"
lanl17_policy_id=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "$lanl17_receipts/population-freeze.json")
```

Retain the entire policy record, policy ID/hash, UTC freeze time, Git source commit, estimator hash, config hashes and parent outcome-free preflight/source manifest in Git before the first campaign outcome. The repeated identical freeze returns the original timestamp/identity; it cannot replace a post-outcome policy. The policy fixes D30 and the dependency method before data. Parent must confirm no matching campaign outcome ledger exists before first launch.

## Actual fresh campaigns

Within the parent's verified socket wrapper and original CODEX_HOME restoration, use the public command for each of p1–p4:

```sh
python3 -m swdb campaign "$lanl17_campaign_file" \
  --records "$lanl17_records" --provider-config "$lanl17_configs/provider-codex.yaml" \
  --runs-root "$lanl17_runs" --format json > "$lanl17_receipts/$lanl17_campaign_id-result.json"
```

Use real providers and real gem5 evaluators; never `--fixture`. Optional `--baselines-only` is an actual outcome route, so it occurs only after the same population freeze. Continue it using `--resume` with the same W, config, store and retained ledger. The existing campaign invokes all pilot/shared-baseline/companion/candidate outcome boundaries; estimates must be durable before any outcome request is opened. Timing alone chooses candidates and plateau. No estimate determines selection or candidate acceptance.

Retain raw runs on mbit10. Per campaign layout is `$lanl17_runs/extensa/CAMPAIGN/{records,state.json,pairing,exports,...}`. The stopped campaign summary embeds paired estimates and outcome-access contexts/timestamps. Validate each campaign store before export. Preserve non-success stop reasons, budget use, interruptions and zero-candidate campaigns as actual receipts, not eligible pairs.

## Compact export and final report

```sh
python3 -m swdb validate --records "$lanl17_runs/extensa/$lanl17_campaign_id/records"
python3 -m swdb campaign-export "$lanl17_campaign_file" \
  --records "$lanl17_records" --runs-root "$lanl17_runs" \
  --candidate "$lanl17_export_candidate" --format json
python3 -m swdb agreement-report --policy "$lanl17_policy_id" \
  --campaign-records "$lanl17_runs/extensa/extensa-gem5-bfs-20261006-p1/records" \
  --campaign-records "$lanl17_runs/extensa/extensa-gem5-bfs-20261006-p2/records" \
  --campaign-records "$lanl17_runs/extensa/extensa-gem5-bfs-20261006-p3/records" \
  --campaign-records "$lanl17_runs/extensa/extensa-gem5-bfs-20261006-p4/records" \
  --records "$lanl17_records" --mode extensa \
  --campaign extensa-gem5-bfs-20261006-p1 --format json > "$lanl17_receipts/agreement-report.json"
python3 -m swdb validate --records "$lanl17_records"
```

`campaign-export` exports only named non-rejected candidate closures/claims; repeat `--candidate` for selected artifacts. Do not invent a candidate when a campaign stops before a valid artifact. The final report reads each complete validated campaign store directly and retains all four summary snapshots/hashes, so no invented public summary-export command is needed. Parent Git export includes compact policy/report/summary/paired records and immutable source/config manifests; raw binary/timing logs and large SG/source artifacts remain remote. Preserve original Extensa/research tags and byte hashes. The team boundary still refuses these records recursively; export does not promote them.

## Fixed statistical interpretation and recommendation

D30 stays exactly: at least 20 unique eligible DX100 pairs, Kendall tau at least 0.6, 95% interval lower bound at least 0.3, and gem5's best surviving estimate top three in every campaign. Current real forecasts lack the proved numeric bridge, so eligible count is zero, estimate errors/tau/interval/top-three are unavailable and the primary gate is unsupported. Receipt ordering can be verified independently without implying numerical accuracy, freshness of all content, native speedup or hardware correctness.

The conditional mathematical method is tie-aware [Kendall tau-b](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kendalltau.html), with percentile resampling of connected dependency components. Link shared generator seed across families, repeated candidate artifacts, provider trajectory/parent lineage, reused baseline outcomes and campaign trajectory transitively. All eight planned graphs share seed 27491095, so four campaign IDs do not prove four independent components. Unknown dependency closure, fewer than four supported independent components, fewer than 9500 defined bootstrap draws or degenerate ranking/distribution yields an unsupported interval. The method freezes 10000 draws, seed 20261006 and linear 2.5/97.5 percentiles. These statistical premises cannot repair absent application estimates.

After actual receipts, present a compact table: planned/observed campaigns, observed comparison rows, unique eligible pairs (0), receipt-order state, tau/95% interval (unavailable), top-three (unsupported), D30 (unsupported), selection (unchanged flow A). Recommend retaining flow A; ticket 18 remains Yan-Ru's final decision. Any future gem5-fitted research model must use a separate version/population and remain refused by team protocols; it cannot retroactively replace this primary report.

The tested source prerequisite is recorded in `17-source-prerequisite-proof-20261006.json`: ten final public/mathematical checks, two post-integration public boundary/report checks and 631 canonical records validated. Ticket 17 remains claimed; this establishes implementation readiness, not actual campaign agreement.

Parent-owned external controls are `/private/tmp/lanl17_parent_helpers.py` and `/private/tmp/lanl17_parent_helpers_README.md`. The control SHA256 is `f68cd91b1302177038c5e9388d6e57b2ca205df3dacb3b81fb009c43f2047957`. Portable metadata/holder controls are in `/private/tmp/lanl17_parent_helpers_local_proof.json`. The mandatory real Linux descendant cleanup probe is `/private/tmp/lanl17_parent_helpers_linux_smoke.py`, SHA256 `6b032df7f1f1eacb6a62c5d6c3581efc3e19f8696d23800f4b58de8b6b7230f0`; it has not been executed locally. Parent inspection and a successful sealed mbit10 smoke are required before helper preparation. The helper rechecks live SG/baseline/model/runtime/config files on every dispatch/resume/finalize, restores the verified original CODEX_HOME through a task token, preserves account HOME and freezes/exports policy before outcomes. All application raw output stays remote. The external README supplies exact final-W preparation, two-lane queue/resume and four-store report/export commands.
