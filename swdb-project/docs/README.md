# EvolveSWDB guide

Updated: 2026-09-28 (Eastern Time).

EvolveSWDB is ArchEvolve's Software Database. It connects application source,
kernels, implementations, memory access patterns, optimization strategies, and
evaluation evidence. The `swdb` tool validates and queries these records and
supports a source-to-evaluation BFS workflow.

**New to the project? Follow the [tutorial](tutorial/README.md)** for a 10-minute
overview, then up to 30 minutes on records, code components, BFS, and contributing.
It includes diagrams, query examples, and an optional local exercise. The pages
below remain short task-oriented guides.

## Read this in 30 minutes

Read these five pages in order: about 2,800 words, roughly 19 minutes at 150
words per minute. The 30-minute budget leaves room to inspect the examples;
reference links are for lookup when doing a specific task.

| Page | What you will learn | Budget |
|---|---|---|
| This page | Model, setup, first queries | 5 min |
| [Records and queries](database.md) | Evidence, storage, finding useful records | 5 min |
| [Adding records](adding-an-application.md) | Applications, implementations, strategies, review | 7 min |
| [BFS workflow](bfs-handoff.md) | Rewrite, evaluate, compare, interpret results | 8 min |
| [Profiling on mbit10](mbit10-profiling.md) | Host rules and measurement procedure | 5 min |

Stop there for onboarding. [Reference](reference/README.md) contains field-level
contracts and detailed procedures. [Archive](archive/README.md) contains dated
plans, run diagnoses, and superseded formats. Neither is required reading.

## The model

An **application** is source at a pinned version. A **kernel** is a computation
identified by its correctness check; several applications can implement the same
kernel. An **implementation** is code that passes that check. A **candidate
artifact** is submitted code whose correctness still needs evaluation.

An implementation contains **access patterns**: chains of array-access steps
ending at a target array, with an update kind such as read or compare-and-swap.
An **optimization strategy** describes a reusable change to an access pattern,
loop, or input. It holds no executable code. Parameters such as tile size do not
create a new strategy identity.

A **profile** records observations for an implementation, input, and machine.
The BFS workflow additionally retains exact source snapshots, profile packages,
rewrite proposals, candidate artifacts, evaluations, frozen protocols, and
comparisons. A comparison names its baseline explicitly; source ancestry does
not select the performance comparator.

Use [CONTEXT.md](../CONTEXT.md) for the full glossary and [ADRs](adr/) for the
reasoning behind these decisions.

## Start here

Use Python 3.12 or newer with PyYAML 6+ and jsonschema 4.10+. From the repository
root, `python3 -m pip install -e .` installs the package and the `swdb` command.
The module form below also works with dependencies already installed.

```sh
python3 -m swdb validate
python3 -m swdb find --shape ranged_indirect
python3 -m swdb implementations gapbs-pr --require loop_carried_dependencies=false
python3 -m swdb strategies --pattern gapbs-pr-jacobi/gather-contrib
python3 -m swdb view gapbs-pr-gs kron-g16-k16 mbit10
```

Queries refresh the generated index as needed. Query output defaults to YAML;
use `--format json` for JSON. Use `python3 -m swdb COMMAND --help` for each
command's options, including supported `--records` and `--db` overrides.
Exit codes are 0 for success, 1 for a failed check/command, and 2 for usage errors.
Errors go to stderr.

## Where things live

| Location | Purpose |
|---|---|
| [`records/`](../records/) | Authoritative YAML, one file per record |
| [`schemas/`](../schemas/), [`vocab/`](../vocab/) | Valid fields and controlled terms |
| [`swdb/`](../swdb/) | CLI, validation, queries, workflow implementation |
| [`apps/`](../apps/), [`tools/`](../tools/) | Application sources and analysis tools |
| [`tests/`](../tests/) | Verification; run with `python3 -m pytest` |
| [`.scratch/`](../.scratch/) | Local specs, tickets, campaign requests, observations |
| [`agents/`](agents/) | Maintainer/agent tracker conventions |

YAML in git is the master copy. SQLite is disposable. Large source snapshots,
binaries, graphs, and raw measurements live outside git on their producing host;
records retain their paths and hashes. A remote path in a record does not mean
its contents were verified on your computer.
