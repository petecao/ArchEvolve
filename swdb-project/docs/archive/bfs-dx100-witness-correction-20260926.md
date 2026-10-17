# Bounded correction of the author completion parser

Navigation updated: 2026-09-28 (Eastern Time).

Created: 2026-09-26 (Eastern Time).
Updated: 2026-09-26 (Eastern Time).

The first v2 proof ended unsuccessfully at 09:03 ET. The simulator emitted the
protected author PASS sequence and a matching successful exit syscall, but the
parser rejected unconditional CPU progress messages in the redirected trace.
The failed record and its exact runtime remain unchanged; see
[the audited failure](../evidence/bfs-dx100-witness-20260926-a1.yaml).

The correction accepts only the pinned CPUProgressEvent grammar, retaining
those observations separately with CPU, tick, counter, and numeric checks.
Progress cannot supply any part of an exit witness. Unknown or contradictory
records still fail. Independent review found and closed a metadata-only tick
ordering defect before this follow-up. New execution binds the corrected parser
hash; no old result is promoted by reparsing its trace.

The user authorized continued implementation and evaluation and reaffirmed
broad approval at 08:54 ET. Specific evidence/provider exports remain held by
automatic approval review; they are not prerequisites for this code correction.
This plan names **one corrective
attempt**, `bfs-dx100-witness-20260926-a2`, after the diagnosed implementation
repair. It is distinct from the consumed a1 attempt and the expired original
pilot. The absolute end remains **2026-09-26 10:00 ET**; do not dispatch unless
at least 1,200 seconds remain. There is no automatic retry or deadline extension.

The a2 request changes only the evaluation ID relative to a1. It keeps the exact
unchanged author binary, model, graph/source, checkpoint, four guest cores,
8 MiB/16-way MAA LLC, 16 GB guest memory, traversal ROI, 10^10 post-ROI ticks,
48 GiB sampled RSS, 2 GiB raw cap, 750-second simulation and 1,100-second adapter
caps. Use the existing 1,200-second outer envelope with its 30-second cleanup
reserve. The client requires the exact retained a1 failure file hash before
submission and uses the original request-identity guard.

Before dispatch, review and commit the correction, run the parser/adapter tests,
and reparse the existing 2,761-byte trace on mbit10 with the new parser as a
read-only diagnosis. That reparse is not a successful execution. Verify the
fresh checkout, helper, both socket leases and legacy lease, all inputs and
checkpoint hashes, 52 GiB node/64 GiB global admission gates, and disk reserves.
Run through `socket_lane.sh` in a named tmux session on a free lane; use a new
`witness-a2-dispatch1` receipt prefix. Reusing the idle dedicated witness checkout
is permitted because a1 retained immutable runtime copies; historical checkouts
remain pinned. No other owned measurement may be active at dispatch.

Execute `python3 scripts/dx100_witness_corrected_probe.py --runs-dir
/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925 --lane N` inside that lane.
Audit public retrieval and retain either success or failure. This tiny proof
does not establish full/tail or competing-parent coverage, a candidate matrix
cell, a native freeze, artifact reproduction, or any performance gain.
