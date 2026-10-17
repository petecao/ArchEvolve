# Conditional metadata-only a3 continuation

Unexecuted preparation only. Parent may select this path solely after actual a2 has ended unsuccessfully because of a metadata processing cap, the lease is released, cleanup has no survivors, and parent has sealed its completed-record inventory. A successful or still-running a2, a null/unsupported whole-call estimate, mismatched pins or another scientific failure must not be resumed. Preserve all a1/a2 raw data and custody.

Source C/F6, the already published target, all nine calibrations, four characterizations, exact two per-kernel protocol requests, five-trial original-driver recipes and per-kernel band policy are unchanged. No binder, native command, count collection, provider invocation or application timing is present in this continuation. Existing complete target/protocol/positive estimate records are verified and reused; only missing public freeze/estimate commands are issued. Both exact per-kernel request JSON snapshots are retained in the new raw folder even when their protocols are reused, for the later band-report comparison. Full public metadata validation remains required before success.

The sealed a2 processing-failure receipt uses the existing fields and adds:
`original_a1_failure_custody_identity: 8ddb9825fb7ccefff7088ea550af290379f8ea48744065b9d156196b7947db5a`.
The helper checks that against the unchanged a2/failure-custody.json and sealed a2 preregistration, which must pin the original active a2 helper181f6c9d…, limits8000/8200/1100/1000, native/provider commands0 and unchanged science. It preserves the original a1 completed manifest as a subset of the new actual a2 manifest. The compact a3 export retains both failure custodies.

Administrative envelopes only: metadata1800s, final validation1400s, inner15000s, outer15200s, unchanged45s cleanup reserve. Native900s remains a separate unchanged scientific collector deadline and is never invoked here.

After parent actual inspection, source/hash review, current wrapper/lease/capacity preflight and actual failed-a2 custody:

```
python3 /data1/yanruj/lanl-cpu-controls-20261007-a1/lanl-dispatch-cpu-model-continuation-a3.py \
  --failure-receipt /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-model-20261006-a2/processing-failure-custody.json
```

Only after actual a3 success/release and local admission:

```
python3 /data1/yanruj/lanl-cpu-controls-20261007-a1/lanl-export-cpu-model-continuation-a3.py
```

Fresh raw: /data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-model-20261006-a3.
Fresh export checkout/branch: /data1/yanruj/ArchEvolve-lanl-cpu-model-evidence-20261006-a3; codex/lanl-cpu-model-evidence-a3.
Exactly seven cumulative model records plus one compact receipt are exported additively over C; original source/proof paths remain unchanged. Downstream paths are not adapted before the actual a2 result.

Portable proof: lanl-cpu-model-continuation-a3-mocked-proof.json,14 passing checks. Preparation proof uses explicit literal/cap replacements and exact reversal of custody-only insertions; all other bytes match a2, and seven scientific selection/admission functions are AST-identical. All original a2 helper bytes remain unchanged.
