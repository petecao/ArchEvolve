# T17/T20 controlled-simulator next steps

Navigation updated: 2026-09-28 (Eastern Time).

Prepared: 2026-09-26 (Eastern Time). Updated: 2026-09-26 22:17 ET.
Local source/record audit only; no dispatch,
provider call, transfer, new allowance, or protocol is created by this document.
The [dependency inventory](../../.scratch/bfs-rewrite-evaluation-2026-09-25/observations/candidate-simulator-dependencies-20260926.json)
pins the records and code inspected. Host-only identities below come from retained
observations and still need live artifact verification before reuse.

The four scalar v2 builds have since completed, although their enclosing
preparation failed during final storage observation. Their individual build
records and binaries require the exact retained-build checks; the failed
preparation remains failed. T17's diagnostic build and retained-primary reuse
are now implemented and independently reviewed locally. The diagnostic export
was rejected by automatic approval review and has not reached mbit10. Any future
runtime must include the reviewed transient SQLite storage repair and pass its
required Linux proof. See the current [ticket map](../../.scratch/bfs-rewrite-evaluation-2026-09-25/map.md)
for actual execution and transfer state. The tables below retain the original
dependency audit; they are not authority to repeat completed compilations.

T17 can next reuse its existing changed candidate and successful primary build.
T20 cannot yet enter compilation: its actual annotated submission is unresolved
and has no candidate. The context supplement remains held. Neither T16's author
protocols nor the native publisher authorizes these complete-call comparisons.
Keep the [selected campaign strategies](../../.scratch/bfs-rewrite-evaluation-2026-09-25/campaign-plan.md):
T17 offloads through changed `DOBFS` and waits for the old-parent destination;
T20 adds the annotated upstream top-down helper while preserving its direction
policy. Neither substitutes the unchanged `DOBFSMAA` author entry point.

## Exact build dependencies

All new builds use `DOBFS`, `bfs.complete_call.v1`, model build
`bfs-dx100-build-20260925-a2`, target `dx100-e4fc4af-4c`, and the original-adjacency
adapter `dx100.complete_call.v2`. A diagnostic is a separate binary, never a
replacement for primary timing.

| Role | Existing candidate/build | Work still needed |
| --- | --- | --- |
| T17 baseline, `dx100-bfs-scalar` | `bfs-dx100-compile-20260925-a1.candidate`; its `.primary.build` and `.diagnostic.build` are v1 | Two new v2 builds, `accelerated: false`, diagnostic flag false/true |
| T20 baseline, `gapbs-bfs-do` | `bfs-upstream-compile-20260925-a1.candidate`; its `.primary.build` and `.diagnostic.build` are v1 | Two new v2 builds, `accelerated: false`, diagnostic flag false/true |
| T17 candidate | `bfs-campaign-preparation-20260925-a1.dx100-instructions.candidate-1`; primary `bfs-t17-build-only-20260926-a1` passed | Reopen/import exact existing primary metadata when its transfer is cleared; one new v2 diagnostic build with `accelerated: true` |
| T20 candidate | `bfs-campaign-preparation-20260925-a1.upstream-annotated` is unresolved | Explicitly approved context continuation must first produce a candidate under the unchanged intent; then primary and diagnostic v2 builds with `accelerated: true` |

T17's retained primary binary SHA-256 is
`852e62314b7114079975fe25d70da4e77596490bcfa89fb4f7c64af585485527`;
its source manifest is
`ca09d2f439a56f295c5ccdc5e18a5fd5a4c2c9726005365f8125cc1d8979740a`.
Its build has no correctness/timing evidence. The source/proposal packet and
build record are not present in the local catalog at this audit; their held
transfer is not presumed approved. Keep the original proposal/package lineage.

The smallest unblocked build preparation is the **DX100 scalar baseline's two
v2 build requests**, followed by T17's diagnostic request once its canonical
candidate is available in the chosen execution Store. Reuse the completed model;
do not rebuild gem5 or reinterpret the old v1 builds. Assign distinct unused IDs
and finite build/outer/storage budgets before any future invocation. This plan
does not replenish the consumed T17 build-only attempt or the expired pilot.

## Freeze the source-specific comparison before timing candidates

Use T15's actual simulator packages, unchanged-baseline/reference repeatability,
selected workload IDs and feasibility reasons. Preferred scale-18 registrations
are `bfs-20260925-uniform18.cd2169a5c421baf7` and
`bfs-20260925-kronecker18.48de8267ac2098d5`, with ordered sources
`[0, 1234, 7777]`; they are not selected here in advance of T15's result.
Preserve isolates/fallbacks. Size selection cannot use a generated candidate's
gain ([spec D13](../../.scratch/bfs-rewrite-evaluation-2026-09-25/spec.md), lines 254–262).

Prepare one `controlled_simulator` freeze per source/candidate treatment. Pin
four guest cores, complete-call ROI, exact per-role compiler/version/flags/v2
adapter, model-build digest and simulator, actual BASE/MAA configurations with
matched CPU/cache/memory/clock, and disclosed accelerator/software differences.
The existing matched control is BASE/MAA at 8 MiB/16-way LLC; its author traversal
ROI cannot be copied into this freeze. Pin the complete instrumentation mappings,
including original-graph contracts, suppressed events, verifier/parser/observer
hashes, debug flags and post-seal trace settings. SG32 and SG64 formats differ by
application even when loaded adjacency is equivalent.

Take region IDs and collector/library/pass/runtime hashes from the **new exact
diagnostic builds**. Freeze explicit baseline/candidate correspondence, scope and
attribution for selected-region ratios; discover candidate helpers without
inventing annotations. Carry T15's accepted two-replay, zero-warmup sampling and
fixed profitability policy, including the 1.05 floor, 95% interval and 2,000
resamples, with recorded seed/spread bound. `required_accelerator_cases` applies
to every timed replay when populated; declare applicability from pilot evidence,
not an assumption that every source produces a full tile. Actual candidate
coverage on both families remains required; A2's unchanged-author graph does not
certify either candidate.

Publish using public `freeze-protocol`, retain its **returned** content-addressed
ID and fresh `get --chain`, then seal canonical inputs and runtime identity before
the future Linux proofs/dispatch. `bfs_freeze_pilot.py` publishes native protocols
only; there is no automatic controlled-candidate freeze generator.

## Execute the existing public interfaces

Every call uses the same selected authoritative records and an explicitly
accounted external SQLite cache. The following is the operation order, not a
dispatchable request manifest or a new clock:

```sh
"$PY" -m swdb dx100-compile BUILD.json --records "$RECORDS" --db "$RAW/swdb.sqlite" --runs-dir "$RAW" --lane "$NODE" --format json
"$PY" -m swdb freeze-protocol FREEZE.json --records "$RECORDS" --db "$RAW/swdb.sqlite" --format json
"$PY" -m swdb dx100-execute CELL.json --records "$RECORDS" --db "$RAW/swdb.sqlite" --runs-dir "$RAW" --lane "$NODE" --format json
"$PY" -m swdb dx100-profile PROFILE.json --records "$RECORDS" --db "$RAW/swdb.sqlite" --runs-dir "$RAW" --format json
"$PY" -m swdb profile-package PACKAGE.json --records "$RECORDS" --db "$RAW/swdb.sqlite" --format json
"$PY" -m swdb aggregate-evaluations GRID.json --records "$RECORDS" --db "$RAW/swdb.sqlite" --format json
"$PY" -m swdb compare-evaluations COMPARISON.json --records "$RECORDS" --db "$RAW/swdb.sqlite" --format json
"$PY" -m swdb get "$RETURNED_ID" --chain --records "$RECORDS" --db "$RAW/swdb.sqlite" --format json
```

For each frozen family, run baseline/candidate roles over each ordered source and
two fresh replays. `CELL.json` names the exact `candidate_build`, binary,
registered representation, source, configuration, v2 verification and
`protocol_trial: {source_position, repetition}`. Primary requests bind the frozen
protocol/role; separate diagnostics bind the same cell and their own build.
Reuse a checkpoint only for the second replay of that exact source/binary/configuration.
Assemble a package for every primary/diagnostic pair. Aggregate each role/family,
then compare with explicit `comparison_baseline: dx100-bfs-scalar` or
`gapbs-bfs-do` and all component-to-package `region_packages` bindings.
With three sources and two replays, each source-specific candidate comparison
needs 24 primary plus 24 diagnostic executions across both roles/families,
24 packages, four aggregates and two comparisons. These are pending cells,
not completed samples or a grant of their summed worst-case runtime.

The reviewed `bfs_simulator_series.py --primary-build ID` path now reuses an exact
completed primary in a frozen complete-call series, independently of
`--diagnostic-build`. It verifies the retained build before and after the grid
and issues no primary compilation. See the
[reuse contract](bfs-simulator-primary-reuse-20260926.md). Its local tests are
orchestration evidence, not guest execution. A sealed finite candidate manifest
and current Linux/runtime admission are still required. The existing T15/T16
batch coordinator admits unchanged author series, not these candidates.

Before dispatch, Root/Host must seal that manifest's original finite clock,
existing resource caps, current runtime/Linux ownership proof and live lane
admission. No such candidate campaign allowance is instantiated here. Retain
failures without automatic retries or a strategy change. A repaired candidate
needs fresh compatible evidence on both families. T17/T20 each require actual
correctness, acceleration and profiling, but neither individually requires a
gain; T21's overall gain obligation remains separate.
