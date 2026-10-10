# 5. Contribute records and understand profiling

Updated: 2026-10-09 (Eastern Time). Reading budget: 7 minutes.

[Tutorial](README.md) · [Previous](04-bfs-workflow.md)

## Add a catalog record in a temporary workspace

This optional exercise uses the repository's tiny graph input fixture. It shows
the full write path without changing the project's records or running a
benchmark. Run inside `ArchEvolve/swdb-project/` with chapter 1's dependencies.

```sh
python3 -B - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess

def swdb(*args):
    subprocess.run(["python3", "-B", "-m", "swdb", *map(str, args)], check=True)

with TemporaryDirectory(prefix="swdb-tutorial-") as work:
    root = Path(work)
    records = root / "records"
    records.mkdir()
    index = root / "index.sqlite"
    swdb("add", "tests/fixtures/profile/tiny-input.yaml",
         "--records", records, "--db", index,
         "--agent", "--agent-name", "tutorial")
    swdb("validate", "--records", records)
    swdb("get", "tiny-sym", "--records", records,
         "--db", index, "--format", "json")
PY
```

The fixture refers to a checked-in edge list and hash. Its node count is read
from code; edge counts remain unknown. `add --agent` records draft status and
agent provenance at `inputs/tiny-sym.yaml`; `get` retrieves that identity.
The temporary directory is removed when the block exits.

## Extend the catalog deliberately

For a new application, work through these dependencies:

1. **Application:** pin the source revision, license, language, and build context.
   Small unchanged source copies can live under `apps/NAME/` with dated
   provenance. Larger sources need a pinned fetch/checksum procedure.
2. **Kernel and baseline implementation:** define the computation and executable
   correctness check, then describe actual code, build/run templates, loops,
   and access patterns. Assemble both records before validating their mutual
   references. A format `0.4` implementation also names application,
   source baseline, evaluator, and scoped verification explicitly.
3. **Input:** provide either a generator or a file/hash, with every property
   needed by array-size and loop formulas. Use `null` with `basis: unknown` for
   facts not yet established.
4. **Profile:** let the profiling tool retain correctness outcomes, measurements,
   environment, and raw-output locations. Review the evidence before treating
   the record as reviewed.

Copy a similar record, then re-establish its facts. Describe duplicate indices,
index modification, dependencies, sharing, atomic requirements, ordering, and
numerical requirements. A compare-and-swap retry loop keeps update kind `compare_and_swap`,
even when implementing a minimum. Record aliases to avoid double-counted footprints.

For a new strategy, first check whether its **target plus typed effect** already
exists. Tile sizes and prefetch distances are parameters, not new identities.
Record machine-checkable preconditions, remaining `unchecked` requirements, and
reported benefits with sources. Catalog intrinsic records retain exact names,
headers, ISA requirements, lane/element widths, and memory behavior. Accelerator
intrinsics also need typed-library semantics, lowerings, and certifications. Derived
implementations name the strategies they apply and intrinsics they call.

Use the [application checklist](../reference/adding-an-application.md) and
[strategy checklist](../reference/adding-a-strategy.md) when authoring. Keep IDs
stable; replacements receive new IDs, while old records remain deprecated with
`deprecated_by` links. Record statuses (`draft`, `reviewed`, `deprecated`) differ
from ticket statuses.

Sealed workloads and protocols use `register-workload` and `freeze-protocol`;
assembled packages use `profile-package`. `add` is not the creation interface for
those records. Typed-library entries belong in `library/`, not `add`; validate
their clauses, code pins, and dependency hashes. Certification and promotion
create evidence/review records without rewriting normative content. Agent reviews
must record delegation and attribution. Experimental fields belong under
`extensions` where supported.

## Understand what ordinary profiling collects

```mermaid
flowchart TD
    B[Build implementation] --> C[Correctness check]
    C --> T[Timing by thread count]
    T --> F[Footprints and index-stream features]
    F --> G[Separate Cachegrind diagnostic]
    G --> P[Profile record and external raw files]
```

The ordinary profiler defaults to five trials at each of 1, 2, 4, 8, and 16
threads. It checks correctness before timing. An explicitly permitted unfinished
check remains unverified/incomplete. Cachegrind is a separate single-threaded
diagnostic; its cache metrics have `basis: simulated`. Index-stream features
describe properties such as repetition and locality in the declared visit order.
BFS uses the separate evaluator/protocol machinery from chapter 4.

On mbit10, check both socket leases and the legacy lease, then use the current
socket-lane wrapper. Permit at most two measurement jobs, one per socket.
Check source commit, disk, load, and counter availability. Builds/sources belong
under `/data1/yanruj/`; raw output stays outside git on its producing host.
Sync through git without updating a measuring checkout.

The local Mac is ARM and mbit10 is x86_64. Local catalog exercises need neither
OpenMP nor a simulator; running native or simulated workloads has additional
toolchain and host prerequisites. Read the [profiling guide](../mbit10-profiling.md),
[host rules](../../../.claude/rules/remote_server.md), and
[mbit10 procedure](../../../.claude/skills/mbit10-runs/SKILL.md) before remote work.

## Troubleshoot by the failing boundary

| Symptom | First action |
|---|---|
| Unknown key or value | Read the named schema/vocabulary; check whether an extension field is appropriate |
| Dangling ID or source excerpt mismatch | Check the referenced record, source root, pinned revision, and exact lines |
| Strategy is `undetermined` | Inspect `unknown_fields` and `check_by_hand`; gather the missing facts |
| Indexing failed after metadata persisted | Inspect the retained record, fix the cause, then run `build` |
| Missing metrics or incomplete package | Read collection parts, correctness, scope, and explicit incompleteness reasons |
| Remote artifacts are unverified | Verify on their producing host when needed; metadata alone cannot refresh them |
| Build passes but comparison is rejected | Inspect exact protocol, source, workload, ROI, target, and repetition bindings |
| Certification stops a campaign with `infrastructure_failure` | Fix the compiler, trusted files, or configuration named by `stop_detail`; candidate repair does not address these errors |

For code changes, follow the [ArchEvolve rules](../../../AGENTS.md),
[SWDB rules](../../AGENTS.md), [local ticket workflow](../agents/issue-tracker.md),
and relevant ADRs. Work on `yanrujhou_main` within `swdb-project/`. Claim a
ticket before its work; resolve it with an answer and a context pointer in its
map. Use focused tests for the component you changed and record validation for
catalog changes. The general test command is `python3 -B -m pytest`; development
test dependencies can be installed with `python3 -m pip install -e '.[test]'`.

You have finished the reading path. Use the [component map](03-components.md)
to find code and the [reference index](../reference/README.md) for exact contracts.
