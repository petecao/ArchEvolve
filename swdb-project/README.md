# EvolveSWDB

Updated: 2026-09-28 (Eastern Time).

ArchEvolve's Software Database: application sources, kernels, implementations,
memory access patterns, optimization strategies, and evaluation evidence.
YAML in `records/` is authoritative; `swdb` validates it and builds a queryable
SQLite index.

**Start with the [30-minute guide](docs/README.md).** It covers querying, adding
records, the BFS workflow, and profiling. Detailed contracts are in
[reference](docs/reference/README.md); dated run history is in
[archive](docs/archive/README.md).

Requires Python 3.12+, PyYAML 6+, and jsonschema 4.10+. From the repository root:

```sh
python3 -m pip install -e .
python3 -m swdb validate
python3 -m swdb find --shape ranged_indirect
python3 -m swdb strategies --pattern gapbs-pr-jacobi/gather-contrib
```

See [CONTEXT.md](CONTEXT.md) for terminology and [ADRs](docs/adr/) for decisions.
Development uses [local Markdown tickets](docs/agents/issue-tracker.md).
