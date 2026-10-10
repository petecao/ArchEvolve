# Queued p2 attempt1 — source-only a5 execution worksheet R1

No SSH, provider, campaign, collector or control was executed. These private files are preparation, not admission evidence. Choice: run serially on node0 after p1 release32 and b08 AFTER, then fresh actual preflight. This preserves original budgets and the successful a2 dispatcher unchanged.

## Exact BEFORE config

`/private/tmp/lanl17-p2-before-action-config-20261008-a5.json` is ready for parent review. It is the actual p1 BEFORE action config with exactly campaign p1→p2 and the two BEFORE output routes changed; source pins and 300s remote/420s local waits are unchanged. Fresh remote output directory: `/data/yanruj/EvolveSWDB_runs/lanl17-p2-before-custody-20261008-a5`; actual output will be custody.json. Fresh local capture choice: `/private/tmp/lanl17-p2-before-capture-20261008-a5` (must be absent).

Existing parent capture invocation (parent only):

```text
python3 -B /private/tmp/lanl17_capture_metadata_action_20261008.py /private/tmp/lanl17-p2-before-action-config-20261008-a5.json /private/tmp/lanl17-p2-before-capture-20261008-a5
```

Exact embedded remote BEFORE command:

```text
/usr/bin/python3.12 -B /data1/yanruj/ArchEvolve-lanl17-source-20261007-a5/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-selected-trajectory-controls-20261007-a2r1s1/lanl17_compact_attempt_custody_a2r1_20261007.py before --project /data1/yanruj/ArchEvolve-lanl17-source-20261007-a5/swdb-project --final-r 5e12a9796432654d88def24ecea617d16ca605b2 --helper /data1/yanruj/lanl17-control-cleanup60-20261007-a4.py --manifest /data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/manifest.json --manifest-file-sha256 b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1 --campaign extensa-gem5-bfs-20261006-p2 --attempt 1 --publication /data/yanruj/EvolveSWDB_runs/lanl17-first-publication-custody-20261008-a5.json --publication-file-sha256 e1fa63af665bea9937375b4be17fe3de7f013a1da0e1106e36817c828fc3d5e1 --expected-uid 114316761 --expected-user yanruj --output /data/yanruj/EvolveSWDB_runs/lanl17-p2-before-custody-20261008-a5
```

Retain the original generic capture packet/stdout, transport and config/stdin pins. Decode the exact collected custody bytes into the planned local custody.json using an exclusive owned0600 file; do not reconstruct JSON from parsed fields. Pin its actual bytes, whole-file SHA and sealed identity after it exists. Do not reuse p1 before fields/hash.

B08 writer/source is the unchanged 24818-byte collector SHA `b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c`; the config rechecks this source and original FIRST 7701-byte SHA `e1fa63af665bea9937375b4be17fe3de7f013a1da0e1106e36817c828fc3d5e1`. B08 independently verifies exact helper28 (38195 bytes, SHA `28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414`), S/R/185PythonF6 and M2 original/file hash. No resume or baselines-only flags; attempt1.

## Dispatcher argv and bootstrap config drafts

`lanl17-p2-dispatch-parent-argv-draft-20261008-a5-a2.json` contains the exact successful p1 a2 argv structure with p2 routes and selected node0. It is explicitly non-executable: four values are typed required-future-input objects, and the parent admission flag is omitted pending actual review. Fill from actual observations:

- `--before-sha256`: exact whole-file SHA of actual p2 custody.json; supplied planned local and remote p2 routes must hold identical original bytes.
- `--expected-primary`: freshly verify actual PRIMARY HEAD and origin/yanrujhou_main still equal scientific R `5e12a9796432654d88def24ecea617d16ca605b2`; supply that exact R only after live equality verification. This original custody/finalize binding is mandatory. If external administrative advancement or other drift is observed, do not substitute a new HEAD or weaken the binding; stop dispatch and preserve the observed discrepancy.
- `--parent-exclusive-checked-utc`: fresh parent observation after p2 BEFORE with unchanged exclusive campaign state; UTC offset0.
- `--valid-until-utc`: actual bounded dispatch validity end after current time; UTC offset0. Historical p1 times are not copied.
- Insert `--parent-exclusive-state-unchanged-reviewed` only when the parent has actually reviewed that state. Source requires FIRST.checked_utc ≤ p2 BEFORE.checked_utc ≤ exclusive ≤ now ≤ end.

`lanl17-p2-dispatch-bootstrap-config-draft-20261008-a5-a2.json` shows the corresponding CONFIG fields by AST literal extraction from successful p1 stdin. Scientific M2/FIRST original pins and published environment are retained; all p2-before pin values and future admission values are null. Do not pass the draft to BOOT. The unchanged dispatcher constructs real CONFIG from actual original bytes and finalized CLI inputs.

Dispatcher source remains `/private/tmp/lanl17_capture_reviewed_normal_campaign_dispatch_20261008_a2r1.py`,29470 bytes,SHA `76de56fc103d0ffa3d1b197fa93e474e4db4aef78698e69abb9197b994d8e8e3`. Native local SSH remains1584560 bytes/SHA `c7f9f9779c1dd141b04889c6cb214859d0702687e7fde34511bb5fa7af8951f1`; local cleanup source remains912 bytes/SHA `bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289`. The successful source needs no p2 derivative because campaign/node are CLI parameters. Transport wait stays900s; fresh dispatch capture path is `/private/tmp/lanl17-normal-campaign-dispatch-capture-20261008-a5-p2-a2`.

Direct H command generated by unchanged dispatcher:

```text
/usr/bin/python3.12 -B /data1/yanruj/lanl17-control-cleanup60-20261007-a4.py dispatch --manifest /data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5/manifest.json --campaign extensa-gem5-bfs-20261006-p2 --node 0 --attempt 1
```

Published hook/request a2 remain original exact paths/pins and environment from successful dispatcher; PREP5 marker restore is unchanged and HOME/CODEX_HOME remain actual account values. H must remain the exact scientific helper bytes with its tightened0600 mode. No scientific or source budget edits.

## Facts still needed at launch

P2 is queued, not admitted. Await p1 completed wrapper, released matching acquired generation, original exits/stop, release32 and b08 AFTER before reusing node0. Current reviewed dispatcher conservatively requires all three native leases released and p2 campaign/attempt1 absent, then rereads stable generation before H exec. Recheck actual PRIMARY/S/source/control bytes, native routes and future originals. H retains fresh fetched native wrapper and full frozen inventory/provider checks.

Serial capacity floors from unchanged helper28: MemAvailable ≥80GiB (85899345920 bytes), /data1 free ≥21GiB (22548578304 bytes), /data free ≥24GiB (25769803776 bytes). Parallel helper path would require /data ≥44GiB; this worksheet chooses serial and does not relax floors. No fresh capacity facts are asserted here. If actual floors fail, that is a genuine dispatch blocker; wait for coordination/capacity rather than changing controls.

Per-campaign limits stay iterations8, plateau4, lane_hours24, provider calls3/iteration+setup1, disk20GB (20000000000 bytes), lanes1; paired estimates enabled and protocol sources[0]. Child87000s/outer88200s/KILL60s and administrative transport/preflight waits remain original. Continue existing status tables every30min during actual execution; release/after checklist is `/private/tmp/lanl17-a5-release-after-worksheet-20261008.md`.

## Private preparation pins

| File | Bytes | SHA256 |
|---|---:|---|
| lanl17-p2-before-action-config-20261008-a5.json | 1917 | `4d459584b9f37fb6b8319c1642df2ab52af9ac51685ad29284d49bfb17e8e97c` |
| lanl17-p2-dispatch-parent-argv-draft-20261008-a5-a2.json | 2613 | `b2a84f9b8ce93671de2fe53bb677f88570684461ce20ffa44c50de2fd4fbc734` |
| lanl17-p2-dispatch-bootstrap-config-draft-20261008-a5-a2.json | 4205 | `0aef414acbbd503f32b59d22967591e04d157cebabb2550f8287a14d59d1bcf5` |
| lanl17-p2-before-exact-p1-derivation-20261008-a5.diff | 868 | `e0bcac9625860a4e5a0f4823cdd1052c601c7126b558366a3e5607ac202cdbb8` |

Derivation checklist: `/private/tmp/lanl17-p2-source-only-derivation-checklist-20261008-a5.json`; source-only AST read, no import/main execution or remote invocation. Only private preparation files were created; repository and historical originals untouched.

R1 correction: the expected-primary draft input remains a future live verification, constrained to exact scientific R above. Prior worksheet bytes remain preserved; this R1 supersedes its PRIMARY wording. No control source, executable before config, source budget or remote state changed.
