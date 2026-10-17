# EvolveSWDB

Updated: 2026-09-28 (Eastern Time).

ArchEvolve's Software Database: application sources, kernels, implementations,
memory access patterns, optimization strategies, and evaluation evidence.
YAML in `records/` is authoritative; `swdb` validates it and builds a queryable
SQLite index.

**Start with the [tutorial](docs/tutorial/README.md): a 10-minute overview and
up to 30 more minutes on records, components, BFS, and contributing**, with diagrams
and code examples. The [task guides](docs/README.md) cover querying, adding records,
the BFS workflow, and profiling. Detailed contracts are in
[reference](docs/reference/README.md); dated run history is in
[archive](docs/archive/README.md).

Requires Python 3.12+, PyYAML 6+, and jsonschema 4.10+. From the repository root:

```sh
python3 -m pip install -e .
python3 -m swdb validate
python3 -m swdb find --shape ranged_indirect
python3 -m swdb strategies --pattern gapbs-pr-jacobi/gather-contrib
```

See [GLOSSARY.md](GLOSSARY.md) for terminology and [ADRs](docs/adr/) for decisions.
Development uses [local Markdown tickets](docs/agents/issue-tracker.md).
