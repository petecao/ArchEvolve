# Prospective17 storage shape and reserve gates

Source-only; selected17 mains remain NOT RUN. No capacity admission, cleanup subset or future allocation is established. I read unchanged28d and the prior planning note/original passive allocation metadata; no SSH, target imports/main/tests, Git or worktree writes. Parent supplied the current `/data1` free value below; it is not refreshed here.

## Incremental allocation expressions

Let `A_R`, `A_EF`, `A_ER` be **actual incremental allocated bytes** for the full tracked source-R, pure freeze-export and pure report-export checkouts, respectively. These include all tracked repository files, not merely code or records. Export worktrees start at the exact same source commit and then add output closure. Let `J_s` be shared Git object/fetch/commit growth; `B_s` external guest-build growth; `Q_s` persistent configured provider-home growth; `U_s` other retained metadata/cache overhead. None is measured by this audit.

| Retained stage | Prospective `/data1` consumption beyond present primary | `/data` consumption beyond present raw trees |
|---|---|---|
| prepare | `A_R + A_EF + J_prepare + U_prepare` | Five full frozen record/library copies plus config/freeze/log/temp overhead |
| dispatch all four | previous prepare consumption + `B_4 + Q_4 + J_campaigns + U_campaigns` | prepare copies + four campaign closure/source/provider/job/run/attempt growths |
| finalize | `A_R + A_EF + A_ER + B_4 + Q_4 + J_final + U_final` | previous raw growth + selected campaign closures added to base + final report/validation/export metadata |

There is no extra full Git checkout at each dispatch. `prepare` creates R at28d:297, copies records/library to raw/base at307–308, creates full EF through230–259/354, then creates four more frozen record/library copies at357–361. `finalize` adds selected closures to base at612–621 and creates full ER through230–259/635; it does not remove R/EF. No automatic checkout recovery is assumed. Git objects are shared, working files materialized; logical blob totals are not allocated-byte measurements. If frozen records/library cost `Y_f/L`, the five-copy term is `5×(Y_f+L)` plus copy overhead, including the newly frozen policy in each copy.

## Where reserves are actually checked

28d:120–128 requires `/data1 ≥21GiB` (22,548,578,304 B), `/data ≥24GiB` with sibling released or **44GiB** with a proved owned same-population sibling active, and global MemAvailable≥80GiB. `prepare`:291 checks **before** fetch/new R/copies/EF;363 checks leases only. Every dispatch:439–446 checks current capacity before creating its attempt/launch, so p1–p4 each need a fresh unchanged pass. `finalize`:599 checks all leases free; neither finalize nor `export_records` calls capacity. Future passive facts before ER are therefore required planning/custody facts, not an existing finalize capacity gate.

Independently, `campaign.py`:576–586 refuses a job if current campaign-folder logical usage plus planned8GiB exceeds20,000,000,000 B. `campaign_targets.py`:69–70/921/1100–1108 supplies gem5 8 GiB storage and 36 GiB selected-node memory. `dispatch_preflight.py`:11/136–162 requires run-filesystem free≥8+20=**28GiB**, at every corresponding job preflight. The 24/44 helper gates do not replace28GiB; four20GB policy limits are not reservations, forecasts or bounds on external `/data1` guest builds.

## Destinations and unknown overhead

- `28d`:166–168/550–567 puts campaign runs under `/data/.../<M2>/campaign-runs/extensa/<cid>`, per-attempt temporary under raw/attempts; campaign_targets:255–258 creates records, runs, jobs and campaign.sqlite there. Initial per-campaign stores copy **root closure** (379–393), not another complete team catalog. Base source and candidate snapshots live under campaign `base/source` and `sources/<candidate>/source` (397–401/454–460).
- Providers: campaign.py:654–659 writes `provider/<invocation>`; provider_roles:158–190 creates workspace/provider-home beneath that raw call folder. provider_guard:868–877 confines runtime HOME/CODEX_HOME there and TMPDIR to workspace/build. Login source remains `/data1/yanruj/.codex` (28d:28/88–99/538–547); session copy/refresh may change retained login-home state (`provider_login`:388–408). No authentication content was read. Provider output, synthetic builds and session caches are unmeasured growth, not zero.
- Guest compiler outputs live at `/data1/yanruj/EvolveSWDB_builds/<evaluation-id>` (`dx100_candidate.py`:332–337), outside the raw campaign-folder20GB check. Compile request storage_gib1 (campaign_targets:1032–1036) is a per-job limit, not total build allocation. `_builds`/`_companion_cache` and access parse cache are in-memory maps (campaign_targets:1019–1028/1139–1142;access.py:53–85); build reuse can avoid work but does not prove zero retained disk growth. Pinned model/toolchain identities are read dependencies of the selected population; this audit does not establish current physical availability or prescribe a rebuild.

## Inherited arithmetic, not cleanup clearance

Parent's latest supplied pre-E-removal free `/data1` is **21,605,621,760 B**, 942,956,544 B below21GiB. PRIMARY's ~300MB additions are **already included**; do not subtract/add them again. Old original snapshot01:54:07Z pins E allocation 1,181,626,368 B, required 11 allocation 2,278,719,488 B, optional 7 allocation 1,043,107,840 B. Conditional recovery arithmetic only:

| Hypothetical recovered bytes, all subject to actual separate custody | Remaining free | Margin above21GiB BEFORE new R/EF/build/Git allocation |
|---|---:|---:|
| E only | 22,787,248,128 | 238,669,824 |
| E + old required11 total | 25,065,967,616 | 2,517,389,312 |
| E + old required11 + optional7 total | 26,109,075,456 | 3,560,497,152 |

These are stale-size arithmetic alternatives, **not selected subsets/removal admission or promised recovered space**. Needed recovery for a stage s is at least `max(0, 21GiB − current_free + prospective_delta_data1(s))`, with current concurrent writes measured separately. Even an initial prepare pass does not guarantee subsequent dispatch21GiB passes after R+EF allocation. Fresh `/data` facts must independently cover five copies, trajectories and24/28/44 floors; recovery on `/data1` cannot increase `/data` capacity. Unknown finalR checkout allocation, output closure sizes, filesystem allocation, shared Git growth, provider/build/cache retention prevent a numerical future budget.

## Exact inspected pins

- `/private/tmp/lanl17_parent_helpers_cleanup60_a4.py` —38195 B / `28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414`.
- Prior note `/private/tmp/lanl17-storage-planning-source-note-20261007-r1.md` —13212 B / `c4f6b466d711fee54050109261a6ff43a5b73e0bc7bb2444c8b3d29c3ac281f2`.
- Original UNSEALED allocation `/private/tmp/lanl-remote-checkout-storage-observed-20261008-0154.json` —8830 B / `e0593e7e3e8c3b3e01bef630e0facb244069f18eb38820cbc9794888c6749b0d`.
- `/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve/swdb-project/swdb/campaign.py` — 79456 B / `13e3e66a469c3934dee2f0f372a5c17812f5a680cb451f63766ad889d13c3d1d`.
- `/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve/swdb-project/swdb/campaign_targets.py` — 71343 B / `727d4399e4bde1996484e3013770e5ab21ef4a30e8fa7313c4697aaa6359211f`.
- `/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve/swdb-project/swdb/dispatch_preflight.py` — 8210 B / `f6cbd73a7d0d60a83ba18ed482672dcbac3d6d90c8f51434142c430f5680f78a`.
- `/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve/swdb-project/swdb/paths.py` — 1221 B / `788ec6ee5b17e77ec6ca0ab1b3034f7763a69cd71569d119af44a7c85f92b0ef`.
- `/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve/swdb-project/swdb/dx100_candidate.py` — 23980 B / `7d48201fc2d87d4ed52946cab6cbe834e1772841d89aac964fa7ab172427f676`.
- `/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve/swdb-project/swdb/provider_roles.py` — 15013 B / `fc870562690da9832f809b18d2f237150d39e16ac5981aeb7a17311d6d523522`.
- `/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve/swdb-project/swdb/provider_guard.py` — 56088 B / `c2e39fc81be981a08c4f1e8c38b44edba2121ad27f46be3c5e649c13e4789e36`.
- `/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve/swdb-project/swdb/provider_login.py` — 18546 B / `a658e5564f58158e83b60d825141b2510443f646a91d28518a746873b3ac96ba`.
- `/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve/swdb-project/swdb/access.py` — 3744 B / `b068908472747d7c6c5afc8ee7af8067c667e9bb4ef6d45db5d1e1a860154b40`.
