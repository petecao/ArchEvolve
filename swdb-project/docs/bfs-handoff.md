# BFS workflow

Updated: 2026-09-30 (Eastern Time).

[Guide](README.md) · [Workflow reference](reference/README.md#bfs-contracts)
· [Dated handoff and results](archive/bfs-handoff-20260927.md)

Run shell examples inside `ArchEvolve/swdb-project/` (`cd swdb-project` from
the monorepo root).

The BFS workflow connects selected optimization intent to exact source,
independent evaluation, and a comparison under a frozen policy. The SW/HW
producer selects the intent; the worker applies it; the evaluator owns the graph,
trusted driver, verifier, ROI, target configuration, and comparison policy.
A failure or regression is a retained outcome, not permission to search for a
new strategy.

## The sequence

| Step | Public interface | What must be retained |
|---|---|---|
| Identify source | `source-snapshot`; `baseline-candidate` for unchanged code | Exact source manifest, hashes, source context, protected inputs |
| Establish observations | `evaluate` for native execution; DX100 build/checkpoint/execute interfaces | Exact binary, workload, target, ROI, and independent correctness |
| Discover and profile | `bfs-profile` or `dx100-profile`; `bfs-hotspots` | Discovered functions/loops, timing scope, dynamic-memory evidence, gaps |
| Package evidence | `profile-package` | Source snapshot plus matching workload, source vertices, target, threads, ROI |
| Inspect strategies | `profile-strategies`; `strategy-regions` | Applicable strategies and unresolved requirements; no performance promise |
| Apply selected intent | `submit`; bounded `repair` when eligible | Original payload, permitted files, provider bounds, edits, candidate, failures |
| Compare | Frozen protocol, exact evaluations, `compare-evaluations` | Explicit baseline, compatible repetitions and identities, gain/regression/inconclusive decision |
| Report and hand off | `bfs-coverage`; `get --chain`; `handoff-message` | Required cells, missing evidence, failures, and linked versioned messages |

These are workflow stages, not a shell script. Execution requests need the exact
schemas and target-specific procedures in the reference. An unchanged baseline
uses its own candidate artifact without a fabricated patch.

## Keep these distinctions

- **Kernel and source context:** upstream GAPBS and DX100 share `gapbs-bfs`, but
  each implementation retains its own application, source baseline, build, and
  evaluator. Source ancestry does not implicitly choose a comparison baseline.
- **Candidate and correctness:** materializing or compiling code does not prove
  correctness. Missing, interrupted, and incorrect evaluations remain distinct.
- **Package and acceptance:** a complete package needs the required observations;
  its correctness and frozen-policy qualification are checked independently.
- **Primary and diagnostic timing:** native BFS ROI wall time, diagnostic thread
  CPU time, simulated ROI ticks, and simulated per-thread elapsed intervals are
  different quantities. Region timing cannot replace primary ROI timing.
- **Fixtures and execution:** contract fixtures exercise interfaces. Their ratios
  cannot establish empirical gains or fill required execution cells.
- **Metadata and raw verification:** a hash/path in a record is not a fresh check
  of the file. Inaccessible remote artifacts remain `remote_unverified`.

Frozen comparisons bind workload identity, ordered sources, repetitions, target,
threads, build/instrumentation, ROI, verifier, and profitability policy. Simulator
comparisons also bind the model and runtime identities. Do not retrofit missing
bindings into an old freeze. Retain superseding protocols and fresh evidence.

Accelerator use requires observed instruction execution and completed unit traces;
full-tile, tail-tile, and competing-parent coverage are separate obligations.
Source support or a hardware-operation label alone cannot satisfy them.

## Rewrite and handoff boundaries

Proposals accept natural language, structured instructions, annotated source, or
a patch. They identify the source/package, selected regions, intent, required
operations, and editable files. Verifier and ROI protections remain evaluator
owned. Bounded repair addresses eligible build/correctness failures while
preserving the intent and scope; a valid regression does not trigger tuning.

The [provisional handoff contract](bfs-handoff-contract-v1.md) defines profile
package, rewrite proposal, and evaluation result messages. Its format version is
independent of record `schema_version`. The checked-in
[examples](bfs-handoff-examples/) are labeled test clients; they do not establish
live collaborator integration. The contract is retained unchanged because an
acceptance request pins its hash.

```sh
python3 -m swdb handoff-message profile_package PACKAGE_ID --format json
python3 -m swdb get PROPOSAL_ID --chain --format json
python3 scripts/bfs_handoff_examples.py --check
```

## Final report regeneration — 2026-09-27

The retained request selects explicit protocols and reference comparisons.
Regenerate its assessment from `ArchEvolve/swdb-project/`:

```sh
query_dir=$(mktemp -d "${TMPDIR:-/tmp}/bfs-acceptance.XXXXXX")
python3 -B -m swdb bfs-coverage \
  .scratch/bfs-rewrite-evaluation-2026-09-25/requests/acceptance-report-20260927-e1.json \
  --db "$query_dir/index.sqlite" --format json > "$query_dir/report.json"
```

Read the per-cell workflow, accelerator, package, comparison, and raw-verification
states separately, then AC01–AC20, `gain_gate`, `accounting`, and
`selection_audit`. Exit zero means the query succeeded, not that acceptance passed.
When evidence or selections change, create a new dated request. Preserve the
original request and its contract hash.

The [2026-09-27 handoff](archive/bfs-handoff-20260927.md#final-report-regeneration--2026-09-27)
reported incomplete acceptance and no qualified gain. Treat dated counts and
ratios there as a snapshot; the command above produces a fresh assessment for
that request's selections. Its [resume checkpoint](../.scratch/bfs-rewrite-evaluation-2026-09-25/resume.md)
records the older campaign's pause, not the latest status of all BFS work.

Later retained T17 comparisons report `gain` for
[Kronecker](../records/comparison_results/bfs-t17-handoff-20260929-a1.kronecker18.yaml)
and [uniform-random](../records/comparison_results/bfs-t17-handoff-20260929-a1.uniform18.yaml)
workloads. Both declare `joint_hardware_software` attribution: source changes
and accelerator presence differ. These records do not establish a software-only
gain or change the older request's selections. Remote raw files were not
reverified by this local documentation review. Consult newer requests before
continuing execution.
