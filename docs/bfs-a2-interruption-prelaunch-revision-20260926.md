# A2 interruption fixture prelaunch correction

Created: 2026-09-26 18:33:27 ET.
Prospective preparation only; no dispatch, retry, runtime mutation or proof promotion.

The original `bfs-a2-interruption-linux-20260926-a1` failed both cases before simulation under tested commit `67313d9b2a45d9f0fb23d935b56e755a3a19fa7f`. It inherited `lane_required: false` for actual mbit10 and asserted node 0 while its helper held node 1. Preserve that failure, generation 404 release, pending-proof absence and independent cleanup receipt. The successful original owned-cleanup fixture on generation 403 remains evidence for its original runtime only.

The public CLI requires an integer `--lane`; simply omitting it failed locally. The corrected test preserves actual mbit10 lane enforcement and derives that integer from `profile._verified_lane(machine, None)` in the parent. The child independently verifies inherited affinity, memory binding and lease. No production guard is modified. Local synthetic hostname/propagation cases and both real subprocess interruption cases pass; actual corrected Linux execution is still required.

## Minimal tested revision

Construct a new reviewed commit whose sole parent is the unchanged 673 commit. Include exactly these three changed paths:

- `tests/test_dx100_interruption.py`: reviewed correction, SHA256 `abfec3c0aa58f3c52506df4f463d1573cef118e8e14547a4298e064d4941aa46`.
- `.scratch/bfs-rewrite-evaluation-2026-09-25/requests/dx100-coverage-a2-20260926.json`: replace only `required_runtime_sha256["tests/test_dx100_interruption.py"]` with that SHA256.
- `scripts/bfs_dx100_coverage_a2.py`: replace only `PLAN_SHA`, using the plan's canonical `artifacts.digest`, not its raw file SHA256. Old canonical value `f24375eca2fcfb304c92bd752c718f71f14e111ed40a2f1211c12172d3c558e7`; proposed value for that sole map substitution `d78c09751d9b56abddcce0a7217983fc1652ef6dc83c09fc55ecf8a9a4d4be5a`.

The actual A2 measurement has never launched. Keep its ID `bfs-dx100-coverage-20260926-a2`, graph, requests, 16:00 earliest/21:00 latest start, 22:00 absolute end, 3,600-second outer budget, cleanup and all inner bounds unchanged. This is a prelaunch runtime correction, not a statistical/protocol revision or extra measurement attempt. No extension if prerequisites miss the cutoff.

## Fresh proof ordering

After the new tested commit is fixed, pin it in a separately reviewed prospective fixture supervisor/auditor revision and use fresh raw IDs `bfs-a2-owned-linux-20260926-a2` and `bfs-a2-interruption-linux-20260926-a2`. Preserve original 3f38/a1 routes and artifacts. Both full tested runtime snapshots include the changed test, plan and driver hash, so both selections need new proofs; the earlier owned-cleanup success cannot be relabeled.

Each corrected fixture retains the existing two exact test cases, its own original 90-second clock (60 work plus shared 30 cleanup), 512-MiB sampled RSS/output bounds and unchanged no-retry rule. Use the normal current helper and fresh host gates. After external zero exit, invoke its separately bounded 60-second auditor once, reopening pending bytes, full tested/supervisor runtime, exact released generation/kernel state, entire retained PID/start union and settled ledger. Keep pending unchanged; only independent successful closure creates a new proof.

Then seal actual A2 admission with the new tested commit and both exact proof references. Keep `validate_linux_proof` full runtime equality unchanged. This note supplies no actual proof, no authorization to weaken production host checks and no native-readback qualification.
