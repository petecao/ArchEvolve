# Weak paper sanity check

Created: 2026-10-06 ET. Updated: 2026-10-09 ET (code review: subject kernel, required differences, baseline system).

Run the read-only reporter with a sealed paper request and content-pinned canonical estimates:

```sh
python3 scripts/paper_sanity_check.py --records records \
  --request .scratch/lanl-db-analytic-eval-2026-10-06/evidence/13-dx100-paper-sanity-request-20261006-a1.json \
  --output /absolute/fresh/report-directory
```

The command writes `report.json` and `report.md` into a new directory. It refuses changed request seals, changed estimate pins, uncited or duplicate comparison kernels, unqualified numbers, and existing output. It also refuses:

- an estimate whose subject (a candidate, through its implementation, or an implementation) does not resolve to the cited kernel;
- a fixture estimate;
- a comparison without `input` and `configuration` difference rows;
- a non-null estimated ratio without a `baseline_system` difference row. An estimator ratio compares two codes on one target description, not the paper's baseline system.

Each row records the estimate's subject, input, target, description and baseline (`estimate_scope`), read from the record itself. Record reads use the shared access boundary. It performs no estimate, parameter filling, provider call, or canonical write.

The request format is `swdb.paper-sanity-request.v1`. `source` pins the cited PDF URI and exact SHA-256. Each observation has a kernel, label, positive ratio, ratio unit, `reported` basis, page/figure/table locator, `approximate: true`, finite nonnegative `reading_uncertainty`, and input/core/algorithm/configuration scope. `comparisons` optionally joins a kernel to an estimate ID and semantic SHA-256 plus explicit scope differences. Seal the complete request except `identity_sha256` with `swdb.artifacts.digest`. The output has its own content seal.

Khadem et al., [ISCA 2025 paper, v2](https://arxiv.org/pdf/2505.23073v2), Figure 9 on PDF page 9 shows approximate bars of 2.9× BFS, 2.2× BC, and 1.2× PageRank. These are manual plot readings with a conservative ±0.1× reading resolution, not exact table values or statistical intervals. Section 5 and Table 3 on PDF page 8 specify uniform graphs of scale 20–22 and average degree 15, four Skylake-like simulated cores, and 10 MB baseline versus 8 MB DX100 LLC. Its BFS uses bottom-up traversal.

The actual frozen ticket 10 BFS estimate uses a registered scale-16 Kronecker input, the whole DOBFS functional trial lambda, and four requested software threads. It has no complete whole-call cost or ratio. The report preserves this as `unknown` and `incomparable`; requested software threads do not establish paper-equivalent hardware cores. BC and PageRank have no DX estimate supplied to this report yet. Later estimates can be added in a new sealed request without rewriting this historical report.

This comparison is a weak sanity check. Different graph, algorithm/ROI, cache, and execution configurations prevent an estimator-accuracy claim. No paper bar is imported into target parameters or error bands. The reporter lives outside `swdb/`, preserving the generic estimator bundle.
