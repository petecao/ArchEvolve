# YAML files in git are the master copy; SQLite is generated from them

Date: 2026-09-22
Updated: 2026-10-06 ET (narrowing note)

Records are YAML files in git, validated by JSON Schema. A build step generates a
SQLite database from them, and every query runs against that database; agents write
back through the tool, which writes a YAML file and rebuilds. We wanted a real database
for queries and still wanted per-record history, diffs, and review in git.

## Considered Options

- **SQLite as the master copy:** a binary file that git cannot diff, review, or merge.
- **MongoDB:** needs a running server, hosting, and credentials for a few thousand
  records; the lab hosts give no sudo.

## Narrowing note (2026-10-06 ET)

Narrowed by [ADR 0014](0014-main-and-research-databases.md) (proposed): YAML in git is the master copy
of the research database. LANL's database is the team's main database.
