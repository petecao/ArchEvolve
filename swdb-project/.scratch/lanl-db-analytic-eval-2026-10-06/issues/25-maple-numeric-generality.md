# 25 — MAPLE and PageRank numeric generality

Created: 2026-10-09 23:10 ET (ticket 14 code review, finding F4)
**Type:** slice
**Status:** needs-triage
**Blocked by:** 14
**Spec:** `../spec.md`
**Time estimate:** 1–2 days plus mbit10 lane time for 3 fresh PageRank counts

**Why it exists:** Ticket 14 showed story 59 only structurally. The estimator ran unchanged on all nine pairs, but no PageRank or MAPLE estimate has a number. See [ticket 14's code review note](14-generality-maple-pagerank.md#code-review-2026-10-09).

**What to build:** one numeric PageRank estimate and one numeric MAPLE estimate (or a stated, permanent reason why MAPLE cannot have one), with no estimator code change.

## Work

1. **New MAPLE description version.** Never edit `maple-isca2022.fpga-reference.t2`; add a new version.
   - Key its offload mechanisms to MAPLE operation records built from the catalog's MAPLE operations (read/gather through PRODUCE_PTR/CONSUME, loop fetch), per story 32.
   - Or leave out `fetch_queue` until such a binding exists, and say so in the description.
   - Declare `composition_contract.resource_domain_overlap`, or keep a single domain.
2. **Run the estimation role on the new MAPLE version** (D19). It fills the unknown rates once and freezes them, with halve/double sensitivity.
3. **Re-count PageRank on mbit10** after the region-mapping and pure-intrinsic fixes from the 2026-10-09 review land. Then:
   - its loops map to existing region IDs (D33);
   - `llvm.fabs` is counted as an operation, not an opaque call.
4. **Estimate** PageRank on CPU, DX100 and MAPLE, plus BFS and BC on the new MAPLE version, with one unchanged estimator bundle.

## Acceptance

- [ ] At least one PageRank estimate has a number, or each remaining unknown is named as structural with its cause.
- [ ] A MAPLE estimate has a number, or the ticket records why MAPLE cannot have one without an executable MAPLE interface.
- [ ] The canonical ticket-14 records stay unchanged and still validate.

## Yan-Ru decides first

- Whether this is worth doing before ticket 20 (XSBench), which needs a numeric estimator path.
- Who writes MAPLE operation records. The catalog leaves payload and index types, queue binding and memory route unknown.
- Whether the LLM may fill MAPLE rates that its FPGA reference (60 MHz, 2 cores) bounds only loosely.
