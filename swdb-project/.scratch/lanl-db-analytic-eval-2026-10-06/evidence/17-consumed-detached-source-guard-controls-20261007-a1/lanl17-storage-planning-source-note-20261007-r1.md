# Ticket 17 prospective storage planning

2026-10-07 17:21 ET. Source-only inspection of unchanged28d preparation/capacity/dispatch and approved guard/runbook/accepted-input plan. No SSH, importer, main, Store, test, actual catalog read, new control, cleanup or Git mutation. Parent's **21:06Z snapshot** is inherited, not refreshed here. FinalR17, actual report sizes, allocated bytes and campaign growth remain unknown.

## Admission arithmetic at the inherited snapshot

| Mount / point | Observed free bytes | Unchanged floor | Snapshot margin |
|---|---:|---:|---:|
| /data1, prepare and every campaign dispatch | 23,118,901,248 (21.531GiB) | 21GiB =22,548,578,304 | +570,322,944 B (0.531GiB) |
| /data, prepare or dispatch with sibling released | 46,924,410,880 (43.702GiB) | 24GiB =25,769,803,776 | +21,154,607,104 B (19.702GiB) |
| /data, verified same-population sibling active | same inherited snapshot | 44GiB =47,244,640,256 | **−320,229,376 B (−0.298GiB)** |

28d `capacity`, lines120–128, checks these floors plus global MemAvailable>=80GiB. `prepare` calls it **once before fetch/checkout/copies** (line291); it does not recheck capacity after allocation. The guard's lease recheck is not a second storage observation. Dispatch line446 rechecks capacity after loading the frozen manifest and before launch. `own_other` must prove an active sibling belongs to this exact population; unrelated work is not a reason to use another floor. Nothing here authorizes lowering a floor or bypassing refusal.

Finalize (lines596–635) rechecks all_free but does not call capacity, and export_records has no separate storage observation before either full export checkout. Fresh parent read-only measurements before finalize/export are planning facts; they do not replace unchanged public/job guards.

Current space therefore does not satisfy the sibling-active44GiB gate even before preparation. Passing the initial prepare floors cannot demonstrate that the later21GiB/44GiB gates will pass. A sequential schedule uses the existing released-sibling24GiB branch honestly, with fresh unchanged per-job gates; it does not establish sufficient remaining capacity for all four trajectories.

## Exact allocations from source

| Stage / filesystem | New retained objects | Multiplicity / source |
|---|---|---|
| Prepare /data1 | detached full source checkout at supplied fresh `source` | **1 entire tracked repository**, not just swdb/records; line297. Git objects are shared but checkout files are materialized. Fetch may also grow the shared object store. |
| Prepare /data | `raw/base/{records,library}` | **1 full records tree +1 full library tree**, lines307–308, ordinary copytree. Public freeze adds one policy YAML. |
| Prepare /data1 | pure freeze-export worktree `/data1/yanruj/ArchEvolve-lanl17-freeze-evidence-<actualtag>` | **1 additional full repository checkout** at the sameR, plus new policy/compact receipt/frozen configs; lines230–257,354. No automatic removal. |
| Prepare /data | `raw/catalogs/p1..p4/{records,library}` (full actual campaign IDs) | **4 further full frozen records/library trees**, lines357–361. Thus **5 full raw catalogs**, each includes the policy, and5 library copies. |
| Campaigns /data | `raw/campaign-runs/extensa/<cid>` | Four evolving campaign folders. Their `records` begin with **root reference closure**, not a sixth-through-ninth full team copy: campaign_targets.py377–393. Then protocols, pairing, jobs, materialized source/builds, provider work and outcomes grow. Each attempt also retains helper/argv/log/exit/temporary files; raw originals stay. |
| Finalize /data | base records additions, conditional public-export closures, report/stdout/custody | No new full raw-team copy in28d; public exports add selected closures to base. Actual counts/sizes unknown. Four validated campaign stores remain retained. |
| Finalize /data1 | pure actual-report-export worktree | **1 further full repository checkout** plus selected added records/receipt, lines630–635/export_records. If earlier W remain, total **3 additional full checkouts** over the pre-existing primary. |

LetT be one wholeR checkout's incremental allocated bytes, Y/L the records/library copy allocations, P policy bytes, H additional shared Git/config/metadata/log/temp allocation, and Gj actual retained campaign growth. Approximate preparation deltas are /data1=2T+export additions+sharedGit growth; /data=5(Y+L+P)+H. These are bookkeeping shapes, not measured allocation costs: ordinary copytree duplicates files; filesystem blocks/sparse/compression/reflink behavior and Git fetch must be observed. Do not substitute logical Git blob bytes for `df`/allocated-byte deltas.

Before second simultaneous dispatch, needed /data recovery/headroom includes the existing320,229,376B deficit **plus all preparation allocation and first campaign growth**. A small cleanup that merely crosses44GiB before prepare is insufficient proof. Four20GB campaign limits are **decimal** (80,000,000,000B combined maximum policy allowance), not four20GiB reservations or forecasts; persistent four-campaign growth could exceed this snapshot. Existing source pruning/stop rules remain unchanged.

There are additional independent gates: Campaign._step atcampaign.py576–584 compares its folder usage plus the next8GiB planned job against20,000,000,000B; DX100 execution atcampaign_targets.py1104 checks selected-node36GiB and run-filesystem free>=8GiB+20GiB reserve (**28GiB**) throughdispatch_preflight.py137–162. Global80GiB and helper24/44GiB floors do not replace these job gates.

## Required finite read-only facts before actual prepare

1. Actual admitted final14 pureE/reader and exact finalR/tree/C185F6/dependency pins, clean tracked source, ready reviewed controls and released leases. Resolve actual source/raw/export routes and their filesystem/device IDs; don't inventR or treat a branch label as a size pin.
2. Outcome-free wholeR checkout inventory: tracked file count/logical bytes plus actual allocated bytes of a comparable existing checkout; sorted records/library file sizes and allocated blocks; actual Git common-dir packs and anticipated fetch additions. In particular inventory final14's large report representation/canonical additions; selected gzip changes one exported report representation, not canonical YAML or all full-catalog copies.
3. Fresh per-mount statvfs available bytes, inode availability, concurrent writers/process/cwd/FD references, load/global/selected-node memory and leases immediately before prepare; retain timestamp/units/account/path custody. No source cache eviction or write experiment is needed.
4. Bound the five raw-copy delta and two initial checkout delta with explicit unknown allocation overhead; preserve reserve at later dispatch/export checkpoints. After actual prepare, observe actual per-tree allocated/logical sizes and both mount frees before first/second dispatch, each later queue dispatch and finalize. Original thresholds enforce refusal independently.
5. Read-only inventory any **already consumed owner-controlled Git export checkout** proposed for cleanup: exact path/mode/UID, clean/no needed ignored files, tip/pushed branch/integrated ancestry, retained original receipts/admission/pins, no metadata/raw symlink/process/cwd/FD dependency, and recovered bytes on its actual mount. No ownership/consumption inferred from age or filename.

## Narrow cleanup scope if inventory proves need

No deletable owner path is established by this source note. Existing raw runs, failed attempts, active final14 outputs, sourceC/frozenR checkout, original controls/auth/provider homes, M1/M2/catalogs and future evidence must remain. A future consumed final14 export checkout, or the pureEF freeze-export checkout **after successful push, publication/admission and reference audit**, can be considered under the established owner-specific checkout cleanup procedure;28d load_manifest/finalize consumes EF commit/branch/pins, not its physical checkout. This is a conditional proposal, not cleanup authorization or evidence of current consumption. Retain its Git refs/commits and all raw originals.

Removing a /data1 checkout does not create /data space on a different device. No /data deletion candidate is demonstrated; retain raw evidence and let unchanged floors refuse. Parent chooses an actually supported schedule and exact consumed-owner cleanup only after fresh facts. No cap widening, extra control family, campaign-budget extension or speculative deletion is proposed.

## Inspected source pins

- `/private/tmp/lanl17_parent_helpers_cleanup60_a4.py` — 38,195 bytes; SHA256 `28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414`.
- `/private/tmp/lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.md` — 7,161 bytes; SHA256 `fa0d7f4dc075d2ef756c35563f1ec254811218dfa2e16d339aa537dfb087ad9d`.
- `/private/tmp/lanl17-r1s1-future-actual-input-construction-plan-20261007.md` — 11,817 bytes; SHA256 `e3420b334ce05f7268699b0079987d1d2afc98fe5cb5503e6069a89038b59170`.
- `/private/tmp/lanl17_metadata_dispatch_guard_cleanup60_a4_20261007.py` — 14,577 bytes; SHA256 `9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6`.
- `/Users/yanrujhou/.codex/worktrees/lanl-ticket11/ArchEvolve/swdb-project/swdb/campaign.py` — 79,456 bytes; SHA256 `13e3e66a469c3934dee2f0f372a5c17812f5a680cb451f63766ad889d13c3d1d`.
- `/Users/yanrujhou/.codex/worktrees/lanl-ticket11/ArchEvolve/swdb-project/swdb/campaign_targets.py` — 71,343 bytes; SHA256 `727d4399e4bde1996484e3013770e5ab21ef4a30e8fa7313c4697aaa6359211f`.
- `/Users/yanrujhou/.codex/worktrees/lanl-ticket11/ArchEvolve/swdb-project/swdb/dispatch_preflight.py` — 8,210 bytes; SHA256 `f6cbd73a7d0d60a83ba18ed482672dcbac3d6d90c8f51434142c430f5680f78a`.

## Later exact allocated-checkout observation (separate custody)

Parent supplied a later read-only result at2026-10-07T21:20:44.058313+00:00. Original `/private/tmp/lanl-remote-checkout-storage-observed-20261007-2121.json` remains **unsealed**, fileSHA`a3db41ff00a5f26e2ce7aed196bd624721ca1cc7483ac12147634731e6f676f8` (8482 bytes); unchanged producer is `/private/tmp/lanl-readonly-remote-checkout-storage-20261007.py`. This note does not rerun that producer or convert its original metadata into a new admission.

- 28 registered owner LANL checkouts: all tracked clean, untracked0. Four older paths contain only reported pycache ignored paths; their exact contents/lifetime are not reclassified or removed. Cleanliness alone is not source-consumption/reference clearance.
- Protected C checkout `/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1`:410,288,128 allocatedB; active R14 `/data1/yanruj/ArchEvolve-lanl-generality-final-20261007-a1`:881,299,456 allocatedB; prospective countsource `/data1/yanruj/ArchEvolve-lanl-generality-counts-20261006-a1`:202,219,520 allocatedB. Keep these, primary, all raw and all ignored history. They are observations of those exact existing checkouts, not measured finalR17 cost.
- New free/data1=23,118,819,328B (21.531GiB), margin above21GiB=570,241,024B. Free/data=46,915,514,368B (43.693GiB), **short of44GiB by329,125,888B**. The later snapshot does not reverse the earlier scheduling conclusion.
- As an explicit illustration only, two checkouts at the *observed existing R14* allocation consume1,762,598,912B. Without any recovery they leave/data1 below21GiB by1,192,357,888B (1.110GiB), before additional Git/export growth. FinalR17 is unknown and includes later canonical additions;881MB is a comparator, not capacity clearance or a predicted exact delta. Do not pool the 28 checkout sum with physical raw-catalog allocation.

One concrete duplicate-source comparison from this inventory is detached `ArchEvolve-lanl-bulk-total-services-20261006-a1` and `ArchEvolve-lanl-independent-services-20261006-a1`: both HEAD1703c98717ff303fdaa83b8044ac9b4060fedb78, both275,345,408B, clean/untracked0/no ignored paths. That proves matching tracked revision plus observed sizes, **not** that either physical pathname may be removed. Old allocator/clock/memory/float detached sources likewise match completed receipt history but this inventory contains no current source-reference/owner-process/raw-link/future-control audit. No batch is yet proven eligible; none is proposed for deletion merely from those names.

If the parent investigates a narrowly selected consumed-source batch, first independently bind each exact current HEAD/tree to durable pushed reachable Git objects; actual original service/count/projection receipts and preserved raw paths; no pending source readers/builds/metadata file pin/source_reference or symlink/cwd/FD use; all required future17 source paths are disjoint and available; no ignored or untracked artifact loss. Record how historical source-byte proof remains reconstructible after physical checkout removal, rather than claiming Git revision alone preserves every original path-dependent validation. Only then can owner-specific cleanup be proposed under a separate exact scope. This preparation creates no cleanup guard/control and no clearance. /data1 recovery still cannot fix the separate/data44GiB deficit.
