# EvolveSWDB

Updated: 2026-09-22

The Software Database of ArchEvolve: records of applications, their kernels, the
implementations of those kernels, inputs, machines, and profiles, plus the `swdb` tool
that validates and queries them. The YAML records in `records/` are the master copy;
anything else (such as a SQLite database) is generated from them.

## Quick start

Requires Python 3.12 with PyYAML and jsonschema (4.10 or newer). Run from the repo root
(`pip install -e .` also installs a `swdb` command):

```
python3 -m swdb validate                          # check every record in records/
python3 -m swdb build                             # regenerate build/swdb.sqlite from the records
python3 -m swdb find --shape ranged_indirect      # access patterns by shape, update kind, semantics
python3 -m swdb implementations gapbs-pr --require loop_carried_dependencies=false
python3 -m swdb sql "select * from steps"         # your own SQL (tables: docs/database.md)
python3 -m swdb view gapbs-pr-gs kron-g16-k16 mbit10   # workload view for the HW Ensemble Agent
python3 -m swdb add new-record.yaml [--agent]     # validate, write to its canonical place, rebuild
python3 -m swdb capture-machine --id mbit10 --ssh mbit10   # machine record, read-only capture
python3 -m swdb profile <impl> <input> <machine> --runs-dir <outside git>   # see docs/mbit10-profiling.md
python3 -m pytest                                 # tests (need pytest; a C++ compiler for some)
```

Every command takes `--records D` to work on another records folder. Query commands take
`--format yaml|json`. Exit codes: 0 success, 1 the check or command failed, 2 usage error.
Errors print to stderr as `file: field: reason`.

## Layout

| Folder | Holds |
|---|---|
| `records/` | the database: one YAML file per record, one folder per record kind |
| `schemas/` | one JSON Schema per record kind, plus the shared envelope |
| `vocab/` | controlled vocabularies, one file per term list, each value with a meaning |
| `swdb/` | the tool |
| `tools/index_features/` | the C++ index-stream feature extractor, built against gapbs's headers |
| `apps/gapbs/` | gapbs, copied unchanged from upstream at the pinned commit |
| `scripts/mbit10/` | running profiles inside a socket lane on mbit10 |
| `tests/` | tests; each drives `swdb` (or the extractor) as a separate process |
| `docs/` | decision records (`adr/`), the database tables, the mbit10 procedure |
| `archevolve/hw_ensemble/` | Joshveer Grewal's HW Ensemble drafts, copied unchanged |
| `.scratch/` | spec and tickets (local Markdown tracker) |

## Documents

- Glossary: [CONTEXT.md](CONTEXT.md)
- Decisions: [docs/adr/](docs/adr/)
- Spec and tickets: [.scratch/evolveswdb-2026-09-22/](.scratch/evolveswdb-2026-09-22/)
- Database tables: [docs/database.md](docs/database.md)
- Profiling on mbit10: [docs/mbit10-profiling.md](docs/mbit10-profiling.md)
- Format proposal v0.1 (superseded where the spec differs): [docs/format-proposal-v0.1.md](docs/format-proposal-v0.1.md)
