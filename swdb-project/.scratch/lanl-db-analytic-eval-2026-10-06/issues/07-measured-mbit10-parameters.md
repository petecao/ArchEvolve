# 07 — Measured mbit10 parameters

Created: 2026-10-06
**Type:** slice
**Status:** resolved
**Blocked by:** 04
**Spec:** `../spec.md`
**Time estimate:** 2–3 h plus about 1 h of lane time (mbit10)

**What to build:** Microbenchmarks measure effective bandwidth per access type and requests in flight per thread on mbit10, inside a socket lane. The results become a new mbit10 target-description version with basis `measured`, and the fixture estimate re-runs with it.

## Acceptance

- [x] The two-lane procedure is followed: leases checked, socket-lane entry, load and commit recorded.
- [x] Free disk is checked first; raw output stays in the runs folder, never in git.
- [x] Values carry repetitions and spread.
- [x] The re-run estimate cites the new description version's hash.

## Comments

2026-10-06 ET: Claimed on `codex/lanl-ticket07`, based exactly on integration `86b2a9a`. Public seams: CPU measurement runner and calibration import/target-description commands; copied-store fixture checks. Parent owns mbit10 dispatch; real receipts and hash-bound estimate rerun are required for resolution.

2026-10-06 ET: Runnable source checks: 7 public runner/import tests passed before the merge-access correction; a bounded local LLVM 22 fixture completed all four count curves (integer `26*n+8`, FP `8*n+5`, branch `5*n+3`, atomic `n`) and 12 native fixture cells within 16 MiB raw output. Those rates remain fixture/reported. Source review then corrected merge payload counts to `4*N-2` (two comparison reads, selected-head reread, output write; final tail read/write) and made ranged begin/end offsets explicit. Real mbit10 receipt and canonical-hash fixture rerun remain pending parent dispatch. [Commands and conventions](../../../docs/reference/cpu-calibration.md).


## Answer

Resolved 2026-10-06 ET. The bounded portable native runner, public importer and
typed calibration binder deliver measured per-thread target descriptions without
Gem5. Public tests cover useful source-byte numerators, balanced aggregation,
fixture classification, unknown unsaturated curves, process-group cleanup and
immutable native provenance; source is `97f5f19`/`40435a9`, typed binding `3b00e27`.
[Conventions and commands](../../../docs/reference/cpu-calibration.md).

| Evaluation | Socket / evidence | Result |
|---|---|---|
| Native primary a1 | node0 generation 467; [receipt](../evidence/cpu-calibration-mbit10-20261006-a1.json) | 80 cells × 7 trials; unsaturated T1/2/4/8 remain unknown |
| Preregistered a2 | node0 generation 468; [preregistration](../evidence/cpu-chain-extension-preregistration-20261006-a2.md), [receipt](../evidence/cpu-calibration-mbit10-20261006-a2.json) | 75 cells × 7 trials; all five T values admit the unchanged plateau criterion |
| Final v2 numerator proof | node0 generation 472; [receipt](../evidence/cpu-count-equivalence-mbit10-20261006-a2.json) | Twelve count points unchanged under corrected `cda8f2d`; no timing rerun |
| Typed binding + T1 fixture | node0 generation 473; [receipt](../evidence/bound-calibration-fixture-mbit10-20261006-a1.json) | Exit 0; 584 records valid; target/protocol/Python-bundle hashes verified |

Each dispatch used an isolated clean Git source, socket lease, NUMA/core binding,
preflight load/free-disk check and explicit unavailable governor/turbo metadata.
Raw output remains under `/data/yanruj/EvolveSWDB_runs/`; compact metadata only
entered Git. The primary and repeat contexts are separate; old 10 target bytes and
all native elapsed/work trials are preserved. Per-parameter repetitions, elapsed
spread and curve premises stay in typed `cpu_calibration` evidence and extensions.

Fresh IDs are `mbit10.cpu.lanl20261006a2.v2.t{1,2,4,8,16}` with resolvable
`mbit10.cpu.lanl20261006a2.v2.calibration.t{1,2,4,8,16}` dependencies. The T1
[description](../../../records/target_descriptions/mbit10.cpu.lanl20261006a2.v2.t1.yaml)
canonical SHA256 is `a5d6c34b6d1d4be0c90a3ade95f9941ae64c9b5e76270aa26889db8cf8a499d2`.
The [actual LLVM22 T1 stream estimate](../../../records/estimates/lanl.bound-v2.fixture.20261006.estimate.yaml)
cites that hash and frozen protocol `lanl.bound-v2.fixture.20261006.b48d17424e89d461`,
with known estimated seconds `2.2471697927392882e-08`. The combined source is
`b5acc909`; Python-bundle SHA256
`645fc669120506b9d87aa32859d72aac928cb6a8e419d48ddc9e54a258595017`.
This rerun remains `contract_fixture`, not CPU accuracy validation.

Verification: 14 public calibration tests passed, 14 shared query/protocol checks
passed, and the combined 05/07 compatibility batch passed 7. Receipt canonical
identity, 17 exact file hashes, 5 canonical target hashes, 10 original byte strings
and frozen T1 snapshot/protocol/bundle checks passed locally after Git transfer;
local `swdb validate` also passed 584 records. Latest integration `8ad4a00` is merged
with no conflict; all edits stay within `swdb-project/`.

Effective concurrency is inferred from measured plateau inputs, not physical MSHR
capacity. Bandwidth uses useful source bytes; compute rates use counted constructed
work, not physical issue throughput. Cache stream rates retain footprint/sharing
scope and do not establish cached dependent-load latency or page-fault service.
The frozen T4 BFS/BC reports retain unknown whole-call totals; independent service
costs and the CPU error band remain ticket 11.

## Code review 2026-10-09

2026-10-09 23:10 ET. The resolution stands; the four acceptance items hold. The
review found two code gaps and two limits worth stating.

- **Commit recorded from the wrong place (fixed).** `cpu-calibrate` read `commit` and
  `dirty` from the caller's working directory (`swdb/cpu_calibration.py`, the context
  block in `calibrate`). A lane started from another checkout would have recorded that
  checkout's commit. It now uses `git -C <ArchEvolve checkout>`, pins `machine_sha256`,
  refuses raw output inside the checkout, and requires native output under
  `/data1|/data/yanruj/EvolveSWDB_runs`. The 2026-10-06 receipts are unaffected. The
  commits recorded in the a1 and a2 descriptions (`97f5f19`, `40435a9`) are ArchEvolve
  commits and match the `source_commit` in their compact evidence.
- **Test copies (fixed).** Four binding tests in `tests/test_cpu_calibration.py` copied
  the whole ~1 GB catalog. They now copy only the record closure.
- **Bandwidth per access type (known gap, not changed).** Only the stream rate is a
  mechanism parameter. The measured indirect and merge rates are kept only in
  `extensions.cpu_calibration.series`, and no estimator model reads them. The merge
  cell's inputs alternate strictly, so it is a best case for branch prediction. See
  [cpu-calibration.md](../../../docs/reference/cpu-calibration.md).
- **Never validated against timing.** The CPU error band of ticket 11 was frozen on a
  services description that replaces this ticket's measured stream, latency and cache
  mechanisms. So these measured values have never been compared with native timing.
  See ticket 11's code-review note.
