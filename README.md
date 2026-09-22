# EvolveSWDB

Updated: 2026-09-22

The Software Database of ArchEvolve: records of applications, their kernels, the
implementations of those kernels, inputs, machines, and profiles, plus the `swdb` tool
that validates and queries them. The YAML records in `records/` are the master copy;
anything else (such as a SQLite database) is generated from them.

## Quick start

Requires Python 3.12 with PyYAML and jsonschema (4.10 or newer). Run from the repo root:

```
python3 -m swdb validate              # check every record in records/
python3 -m swdb validate --records D  # check the records in folder D
python3 -m pytest                     # run the tests (needs pytest)
```

`pip install -e .` also installs a `swdb` command. Exit codes: 0 success, 1 check failed,
2 usage error. Errors print as `file: field: reason`.

## Layout

| Folder | Holds |
|---|---|
| `records/` | the database: one YAML file per record, one folder per record kind |
| `schemas/` | one JSON Schema per record kind, plus the shared envelope |
| `vocab/` | controlled vocabularies, one file per term list, each value with a meaning |
| `swdb/` | the tool |
| `tests/` | tests; each drives `swdb` as a separate process |
| `docs/adr/` | decision records |
| `archevolve/hw_ensemble/` | Joshveer Grewal's HW Ensemble drafts, copied unchanged |
| `.scratch/` | spec and tickets (local Markdown tracker) |

## Documents

- Glossary: [CONTEXT.md](CONTEXT.md)
- Decisions: [docs/adr/](docs/adr/)
- Spec and tickets: [.scratch/evolveswdb-2026-09-22/](.scratch/evolveswdb-2026-09-22/)
- Format proposal v0.1 (superseded where the spec differs): [docs/format-proposal-v0.1.md](docs/format-proposal-v0.1.md)
