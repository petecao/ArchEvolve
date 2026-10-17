# Public nine-pair report projection

Updated: 2026-10-07 ET. Preparation; actual final reports are pending.

`scripts/generality_report.py` projects exact pinned estimates through the shared record access boundary. Its public seam accepts a sealed `swdb.generality-report-request.v1` JSON file containing exactly nine `(kernel,target)` rows: `bfs`, `bc`, `pagerank` × `cpu`, `dx100`, `maple`. The reference is fresh BFS/DX100. Each row pins `subject`, `implementation`, `characterization`, `protocol`, and `estimate` with copied-record-relative `path`, record `id`, and the full `artifacts.digest(record)` SHA-256. Estimate `protocol_sha256` separately names the frozen protocol identity seal; the two hashes have different payloads.

```sh
python3 scripts/generality_report.py --records "$EXTERNAL_RECORDS" --request "$SEALED_REQUEST" --output "$NEW_REPORT_FOLDER"
```

The parent helper first performs public canonical validation and nine fresh freeze/estimate calls on one final complete estimator bundle. This projector then checks source/kernel/Jacobi registration, target/thread/ROI/argv/trial identities, target snapshots, exact current bundle, MAPLE estimate-only status, and absent PR CPU error-band transfer. Every exact trial region bound/overhead/input and unknown is retained. Root region inputs are labeled diagnostic; root seconds/bounds are per-region medians and cannot be summed into whole-call seconds. Whole-call totals and ratios remain null wherever the public estimator leaves them unknown. Source loops without mappings remain visible.

Independent fixtures prove projection behavior and contradictory frozen target/trial identity refusal. They do not claim executed application evidence. The canonical protocol seal field was corrected by an additional RED→GREEN compatibility slice. The projector lives outside `swdb/**/*.py`; no estimator/mechanism module, observer, runtime, count ID, or historical record changes.
