# Spec: EvolveSWDB — the ArchEvolve Software Database, first milestone

- Created: 2026-09-22
- Status: ready-for-agent
- Owner: Yan-Ru Jhou
- Repo: private GitHub `ruchou/EvolveSWDB` (empty at creation)
- Glossary: `GLOSSARY.md` of the SW Database. ADRs 0001–0003 in its `docs/adr/`.
  Until the repo exists, both live under `MemAcc/ArchEvolve/SW_Database/`.
- Supersedes: format proposal v0.1 (`FORMAT_PROPOSAL.md`, and the shared doc
  "SW Database Format Proposal"). Where they disagree, this spec wins.

## Problem Statement

ArchEvolve is an evolutionary loop of LLM agents that proposes hardware and software
together for an application. One of its boxes, the Software Database, has to tell the
Controller what each application's kernels compute, how their code touches memory, what
profiling measured, and which implementations exist. Today it does not exist. The HW
Ensemble Agent's worked example (Sparta `sort()`) arrived as a hand-written note with
nearly every field unknown: no code, no array sizes, no semantics, no measurement, and
iteration counts with no stated scope. Nobody can tell measured facts from guesses, and
there is no place to put the answers once someone finds them.

The owner must build this database so that it is correct, reproducible, and easy to
extend while the team keeps changing what it needs. Hardware performance counters are
not available: on mbit10, `perf_event_paranoid` is 4 and the owner is not in the VTune
group.

## Solution

A git repository of records plus a command-line tool, `swdb`.

- **Records** are YAML files, one per record: application, kernel, implementation,
  input, machine, profile. Every record carries the same envelope and a schema version.
  Every semantic fact states its basis.
- **Schemas** (one JSON Schema per record kind) and controlled vocabularies define what
  a valid record is. The format grows by adding optional fields, vocabulary values, or
  record kinds, without breaking old records.
- **`swdb`** validates the records, builds a SQLite database from them, answers queries,
  generates the workload view the HW Ensemble Agent reads, adds new records, and
  profiles an implementation on an input and a machine.
- **Profiling is counter-free:** timing across thread counts, array footprints,
  index-stream features computed from the index arrays themselves, and simulated cache
  misses from cachegrind.
- **The pilot** is gapbs PageRank: its baseline implementation (Gauss-Seidel) and the
  Jacobi implementation, on four inputs. Then the other upstream gapbs kernels.

## User Stories

### Maintaining records

1. As the database owner, I want each record in its own YAML file, so that I can read, diff, and review one record at a time in git.
2. As the database owner, I want every record to start with the same envelope (kind, schema version, ID, status, dates, provenance, notes, extensions), so that every tool can handle any record kind the same way.
3. As the database owner, I want IDs that never change and are never reused, so that references between records never break.
4. As the database owner, I want records to refer to each other by ID and never by file path, so that I can reorganize folders without breaking anything.
5. As the database owner, I want a single command that tells me whether every record is valid, so that I catch mistakes before anyone reads them.
6. As the database owner, I want validation to report the file, the field, and the reason for each error, so that I can fix records quickly.
7. As the database owner, I want validation to fail when a reference points to a missing record, so that the database never contains dangling links.
8. As the database owner, I want validation to fail when a fact says `basis: unknown` but carries a value, so that "unknown" is never quietly turned into a guess.
9. As the database owner, I want validation to fail when a count has no scope or a metric has no unit, so that nobody multiplies numbers of unknown meaning.
10. As the database owner, I want validation to fail on vocabulary values that are not in the vocabulary files, so that typos do not create fake categories.
11. As the database owner, I want unknown keys under `extensions:` to pass validation, so that I can try a new field before making it official.
12. As the database owner, I want to add a vocabulary value by editing one vocabulary file, so that growing the vocabulary never needs a schema change.
13. As the database owner, I want every vocabulary value to carry a one-line meaning, so that people and agents read the same definition.
14. As the database owner, I want a documented rule for minor and major schema versions, so that I know when a change needs a migration.
15. As the database owner, I want deprecated records to stay in place and point to their replacement, so that old references still resolve.
16. As the database owner, I want the format documentation revised to version 0.2, so that the written format matches what the tool enforces.

### Describing applications, kernels, and implementations

17. As the database owner, I want an application record with source origin, pinned commit, license, language, parallel model, and build command, so that anyone can rebuild the exact code.
18. As the database owner, I want small application sources (under about 10 MB) copied into the repo at a pinned upstream commit with a provenance note, so that the repo is self-contained and agents can read the code.
19. As the database owner, I want larger application sources fetched by a script with a pinned commit and checksum, so that the repo stays small.
20. As the database owner, I want gapbs taken from upstream at a pinned commit, not from MemAcc's copy, so that no local additions leak into the baseline.
21. As the database owner, I want a kernel record that states what the kernel computes and its correctness check, and names its baseline implementation, so that a kernel is defined independently of any one piece of code (ADR 0001).
22. As the database owner, I want a correctness check recorded as a command plus a pass criterion (verifier and tolerance), so that anyone can decide whether new code implements the kernel.
23. As the database owner, I want an implementation record holding the code, its location, its loops (trip counts and parallelism), its access patterns, and its semantics, so that everything about how code touches memory sits with that code.
24. As the database owner, I want the baseline implementation's code copied into its record with file and line range, so that the record stays readable even if the source moves.
25. As the database owner, I want non-baseline implementations stored as code files next to their record, with build command and origin, so that the database holds real code, not just names.
26. As the database owner, I want each access pattern described as a chain of steps ending at the array read or updated, so that multi-level and ranged indirection need no special labels (ADR 0003).
27. As the database owner, I want each step to name its array with element type, element size, and element count as a formula over input properties, so that sizes are computed, never guessed from iteration counts.
28. As the database owner, I want each step to carry one address shape (stream with a stride, single-valued indirect with an index transform, ranged indirect, pointer chase, data-dependent merge), so that the HW side can branch on a small, fixed set.
29. As the database owner, I want one update kind per access pattern (read, write, add-update, min/max-update, compare-and-swap, arbitrary), so that updates are described once, at the array they change.
30. As the database owner, I want the semantic fields the HW side asks about (duplicate targets, index modified during the loop, loop-carried dependencies, sharing between threads, atomics required, ordering, numerical requirement) recorded per access pattern with a basis, so that every one of Josh's open questions has a place and a source.
31. As the database owner, I want to record that gapbs PageRank's baseline has a loop-carried dependency (Gauss-Seidel), and that Jacobi does not, so that the difference between the two implementations is explicit.

### Describing inputs and machines

32. As the database owner, I want an input record for a generated graph (tool and arguments) or a file (path, format, checksum), so that the exact data can be recreated.
33. As the database owner, I want an input's properties (node count, edge count, degree distribution, index locality, input density) each with a basis, so that kernel size formulas can be evaluated and the "sparse versus dense input" axis is recorded.
34. As the database owner, I want input properties that only a run can reveal (such as the edge count after the graph is built) filled in by profiling, so that the input record ends up with measured values.
35. As the database owner, I want a machine record captured from the host (CPU model, sockets, cores, cache sizes and sharing, memory, NUMA nodes, OS, counter access) together with the command that captured it, so that every profile states where it ran.

### Profiling

36. As the database owner, I want one command that profiles an implementation on an input and a machine and writes a profile record, so that measurements are reproducible and never typed by hand.
37. As the database owner, I want per-call time taken from the benchmark's own timer over several trials, reported as median and spread, so that timing noise on a shared host is visible.
38. As the database owner, I want timing at 1, 2, 4, 8, and 16 threads inside one socket, so that thread scaling hints at whether the kernel saturates memory.
39. As the database owner, I want every run on mbit10 to go through the host's socket-lane procedure, so that the pilot never disturbs other users' runs or breaks the host rules.
40. As the database owner, I want array footprints computed from element size times element count evaluated on the input, so that footprint versus cache size needs no run.
41. As the database owner, I want index-stream features (duplicate ratio, reuse-distance histogram, fraction of sequential steps, degree skew) computed exactly from the index arrays in the order the implementation visits them, so that the HW side learns how indices behave without counters.
42. As the database owner, I want simulated first-level and last-level cache misses from single-threaded cachegrind, with a timeout, recorded with `basis: simulated`, so that simulated numbers are never confused with measured ones.
43. As the database owner, I want the profile to record the exact command, build flags, compiler, source commit, thread count, binding, and date, so that anyone can repeat the measurement.
44. As the database owner, I want counts recorded with a scope (per sweep, per call, per run) and a note on what they count, so that the Sparta mistake of an unscoped iteration count cannot recur.
45. As the database owner, I want the bottleneck field to say `basis: inferred` (never `measured`) while counters are unavailable, and to list the metrics it rests on, so that nobody mistakes it for a counter-based verdict.
46. As the database owner, I want raw tool output stored outside git on the measuring host, with the record pointing to it, so that the repo stays small and the evidence is kept.
47. As the database owner, I want raw output on mbit10 to go to `/data1`, and to `/data` when `/data1` has under 20 GB free, so that the pilot follows the host storage rule.
48. As the database owner, I want counter-based metrics addable later to the same profile records without a format change, so that VTune access, if granted, slots in.

### Querying

49. As the database owner, I want one command that builds a SQLite database from all records in about a second, so that I get real database queries while the YAML stays the master copy (ADR 0002).
50. As the database owner, I want the build to start from scratch every time, so that the database can never drift from the files.
51. As the database owner, I want to run my own SQL against the built database, so that I can ask questions the tool does not anticipate.
52. As the SW Ensemble Agent, I want to find access patterns by address shape, update kind, and semantic value, so that I can locate kernels with a given behavior.
53. As the SW Ensemble Agent, I want to list the implementations of a kernel that satisfy required semantics (for example no loop-carried dependencies), so that I can answer the Controller's "SW specs" request from the ArchEvolve figure.
54. As the SW Ensemble Agent, I want query results as YAML or JSON, so that I can parse them without scraping text.
55. As the SW Ensemble Agent, I want to add a record (for example a profile I produced) through the tool, which validates it, writes the YAML file where it belongs, and rebuilds the database, so that agent write-back uses the same path as a person.
56. As the SW Ensemble Agent, I want records I add to be marked as agent runs with status draft until a person reviews them, so that unreviewed data is visible as such.
57. As an agent without the tool, I want to read the YAML files directly, so that the database is usable even where `swdb` is not installed.

### Workload view for the HW side

58. As the HW Ensemble Agent, I want a workload view for one implementation on one input and machine in Josh's existing workload format, so that I need no change to consume the database.
59. As the HW Ensemble Agent, I want array element counts in the view evaluated to numbers for that input, so that I never infer sizes from iteration counts.
60. As the HW Ensemble Agent, I want semantic values in the view with their evidence sources listed, so that I can tell reported, simulated, read-from-code, and measured facts apart.
61. As the HW Ensemble Agent, I want unknown facts shown as unknown, never omitted or defaulted, so that my rule "unknown is not false" holds.

### Repository and hosts

62. As the database owner, I want the repo at `~/CLionProjects/EvolveSWDB` on my Mac and `/data1/yanruj/EvolveSWDB` on mbit10, pushed to my private GitHub repo on `main`, so that code reaches the lab host only through git.
63. As the database owner, I want Josh's HW Ensemble drafts copied unchanged into a clearly labeled folder, so that the view generator can be tested against his real format without editing his files.
64. As the database owner, I want the glossary, the ADRs, this spec, and its tickets moved into the new repo, so that the project's documents live with its code.
65. As the database owner, I want the tool to need only Python 3.12, PyYAML, and jsonschema (features available in version 4.10), so that it runs on mbit10's system Python and on my Mac without installing anything else.

### Pilot and extension

66. As the database owner, I want gapbs PageRank recorded first: application, kernel, baseline implementation, Jacobi implementation, four inputs, mbit10 machine, and profiles, so that one kernel goes end to end before I scale.
67. As the database owner, I want the four pilot inputs to be Kronecker and uniform graphs at scale 16 (index data fits the 24 MiB L3) and scale 22 (hundreds of MB), so that the pilot tests whether the same implementation behaves differently per input.
68. As the database owner, I want the pilot to report whether the inferred bottleneck differs between scale 16 and scale 22, so that the decision to separate implementations from profiles is confirmed or revisited.
69. As the database owner, I want the other upstream gapbs kernels (bc, bfs, cc, cc_sv, sssp, tc) recorded after the pilot passes, so that the pattern vocabulary is exercised on pointer chase, compare-and-swap, and data-dependent merge.
70. As a collaborator supplying kernels later, I want a written procedure for adding an application and its kernels, so that I can contribute without learning the whole design.

## Implementation Decisions

### Modules

- **Record format (version 0.2).** Six record kinds: application, kernel, implementation,
  input, machine, profile. Common envelope: `kind`, `schema_version` ("MAJOR.MINOR"),
  `id`, `status` (draft, reviewed, deprecated), `deprecated_by`, `created`, `updated`,
  `provenance` (same shape as the HW side's workload provenance), `notes`, `extensions`.
  Compared with version 0.1, `option` becomes `implementation`, and code, loops, access
  patterns, and semantics move from the kernel to the implementation. The `changes`
  field is dropped: every implementation carries its full semantics.
- **Fact wrapper.** Every semantic fact and the bottleneck is `{value, basis,
  evidence_refs, note}`. Basis vocabulary: measured, simulated, code_reading, reported,
  inferred, unknown. `basis: unknown` requires `value: null`.
- **Access pattern shape.** An access pattern has an ID, an expression, a chain of steps,
  one update kind, and semantics. A step has an array (name, role, element type,
  element size in bytes, element count as a formula over input property symbols) and an
  address shape with its attributes: `stream` (stride; 0 means reuse),
  `single_valued_indirect` (index transform: identity, affine, hash), `ranged_indirect`,
  `pointer_chase`, `data_dependent_merge`.
- **Vocabularies.** One file per term list, each value with a one-line meaning: record
  kinds, provenance kinds, basis, address shapes, update kinds, count scopes (per_sweep,
  per_call, per_run), metric names with units, bottleneck classes, array roles, domains.
- **Schemas.** One JSON Schema per record kind, restricted to features jsonschema 4.10
  supports. Unknown keys are rejected outside `extensions`.
- **Record store.** Loads every record under the records tree, indexes them by ID, and
  resolves references. It is the only module that reads record files.
- **Validator.** Schema check, then rules the schema cannot express: every reference
  resolves; IDs are unique; `basis: unknown` implies `value: null`; every count has a
  scope; every metric has a unit; every vocabulary value exists; element-count formulas
  use only symbols the referenced input defines.
- **Database builder.** Rebuilds a SQLite file from scratch on every run: one table per
  record kind holding the ID, the key fields, and the full record as JSON, plus tables
  for access patterns and steps so the query commands can filter them. The file is
  generated and never committed.
- **Query layer.** `find` filters access patterns by address shape, update kind, and
  semantic values. `implementations` lists a kernel's implementations whose semantics
  meet the required values. Both run against the built database and print YAML or JSON.
- **Workload view generator.** Joins implementation, kernel, application, input, machine,
  and profile into the HW side's workload format. Mapping: `workload_id` = implementation
  ID @ input ID @ machine ID; `patterns[].arrays[].element_count` = the step formula
  evaluated on the input; `semantics` values with the basis moved into evidence;
  `counts`, `bottleneck`, and `metrics` from the profile. Unknown facts stay explicit.
- **Record writer.** `add` validates a new record, writes it to its canonical location
  (derived from kind and ID), and rebuilds the database. Records from agents get
  `provenance.kind: agent_run` and `status: draft`.
- **Profiler.** `profile` takes an implementation, an input, and a machine. It:
  1. builds the implementation;
  2. runs the timing sweep (1, 2, 4, 8, 16 threads, several trials each) and parses the
     benchmark's own timer lines;
  3. runs cachegrind single-threaded with a timeout;
  4. runs the index-stream feature extractor;
  5. computes footprints;
  6. writes raw output outside git and a profile record with every command, flag,
     commit, and date.

  On mbit10 every run enters a socket lane through the host's lane procedure. It never
  runs a multi-threaded job unconfined.
- **Index-stream feature extractor.** A small C++ program built against the
  application's own graph builder. It regenerates the same graph and walks the index
  arrays in the order the implementation visits them, so the features match what the
  kernel sees. It computes the duplicate ratio, a log2-bucketed reuse-distance
  histogram, the fraction of sequential index steps, and the degree skew. Exact
  computation, no sampling.
- **Machine capture.** Records `lscpu`, `uname -r`, memory, NUMA layout, and the value
  of `perf_event_paranoid`, together with the capture command and date.
- **Command line.** `swdb validate | build | find | implementations | view | add |
  profile`. Every command exits non-zero on failure and prints errors to stderr.

### Architectural decisions

- The YAML files in git are the master copy, and SQLite is generated from them
  (ADR 0002).
- Kernel identity is the correctness check (ADR 0001).
- An access pattern is a chain of steps (ADR 0003).
- Profiling is counter-free until hardware counters become available. Counter metrics
  will be added as new metric names, a minor-version change.
- Application sources under about 10 MB are copied into the repo at a pinned upstream
  commit with provenance. Larger ones are fetched by a pinned script.
- The only dependencies are Python 3.12, PyYAML, and jsonschema. The C++ feature
  extractor uses the application's own headers and the system compiler (gcc 13.3 on
  mbit10).

### Hosts

- Development and tests run on the Mac (Apple Silicon). Profiling runs on mbit10
  (Xeon Gold 6326, 2 sockets × 16 cores, 24 MiB L3 per socket, 125 GB RAM). Code
  crosses only through git.
- On mbit10, check the lane leases before each run. Raw output goes to
  `/data1/yanruj/EvolveSWDB_runs/`, overflowing to `/data` below 20 GB free
  (`/data1` had 24 GB free on 2026-09-22).

## Testing Decisions

- **One seam: the `swdb` command line.** Tests run `swdb <command>` as a separate
  process against a temporary records folder built from fixtures. They assert on the
  exit code, the printed YAML or JSON, and the files written. No test imports internal
  functions or reads SQLite tables directly, so internals can change freely.
- **A good test** checks external behavior a user or agent relies on: a record is
  accepted or rejected for a stated reason, a query returns the right records, a view
  has the right fields and values, a profile record contains what the run produced.
- **Every validation rule gets two fixtures,** one record that must pass and one that
  must fail (a positive and a negative control), before the rule is trusted.
- **The view is checked against Josh's real `sparta-sort.input.yaml` format:** field
  names, nesting, and the handling of unknown values.
- **`add` round trip:** a record added through the tool appears in the next `validate`,
  `build`, and query.
- **`profile` on the Mac** uses a stub benchmark that prints gapbs-style timing lines,
  plus a tiny index-array fixture with hand-computed duplicate ratio and reuse
  distances.
- **Tests that need real gapbs, cachegrind, or mbit10** are marked and skipped
  elsewhere: valgrind does not run on macOS/arm64. They run on mbit10 as part of the
  pilot ticket.
- **Pilot acceptance** is itself a check: every pilot record validates, the view for
  each (implementation, input) pair is generated, and each pilot profile's raw files
  exist at the recorded paths.
- **Prior art:** none in the new repo. Use pytest.

## Out of Scope

- Counter-based metrics (cycles, IPC, LLC misses, memory bandwidth) until the owner
  gets VTune group access or counters open up.
- Address tracing of arbitrary binaries (lackey, DynamoRIO) for collaborators' kernels.
  The pilot takes index features straight from the index arrays.
- A server interface (HTTP or MCP). Agents use the command line or read the files.
- Dense GEMV/GEMM applications and collaborators' kernels. Their source and timing are
  the team's decision; this milestone only makes the format and procedure ready for them.
- Evaluator integration, memory traces for a simulator, and any change to the HW
  Ensemble Agent or its format.
- GPU profiling.
- Deleting `MemAcc/ArchEvolve/SW_Database/` (the owner does it after the first push
  checks out).

## Further Notes

- **Open items with other owners:**
  - Josh's cited `schemas/workload.schema.json` is not available. The view targets his
    example file until the schema appears.
  - Whether the Evaluator needs traces is for the Evaluator owner.
  - Which kernels collaborators supply, and when, is for the team.
- **Known facts the pilot records should state** (from the source, `basis:
  code_reading`):
  - gapbs `PageRankPullGS` updates in place within a sweep (Gauss-Seidel).
  - gapbs `pr_spmv.cc` `PageRankPull` reads only the previous sweep's values (Jacobi).
  - `NodeID` is `int32_t`, and `ScoreT` is `float`.
  - `-i` defaults to 20 iterations, `-t` to 1e-4, and `-n` sets the trial count.
- **Glossary terms used here:** application, kernel, correctness check, implementation,
  baseline implementation, access pattern, step, address shape, update kind, pattern
  class, basis, input density, workload view.
