"""The LANL core of the generated database (LANL-shaped-db spec, 2026-10-09). Created 2026-10-11 ET.

LANL tables carry LANL's names and only the slide's columns, plus an integer `id` and the
guessed link columns. They never reference a `swdb_` table, so deleting every `swdb_` table
leaves a database in LANL's shape that still passes `PRAGMA foreign_key_check`.

Each LANL table group is one module `swdb/lanl_<group>.py` with:

- `ORDER`: an int; groups run in (`ORDER`, module name) order, so a group can look up the
  integer IDs of the groups before it (ticket number x 10 by convention: kernels are 20);
- `SCHEMA`: the group's `CREATE TABLE` statements, with declared foreign keys;
- `GUESSED`: (table, column, reason) for each column the slide does not show;
- `fill(rows, store)`: inserts the rows through `rows.add` (or `rows.add_once` for a row several
  records name), which records each row's origin.

A new group is a new file; nothing else needs editing. Being top-level `swdb/*.py`, each
group file is part of `db.BUILDER`, so changing one makes older database files stale.
"""

import importlib
from pathlib import Path

#: The `swdb_` tables the LANL groups share: where each LANL row came from, and which LANL
#: columns (and tables) are guesses rather than what the slide shows.
SCHEMA = """
CREATE TABLE swdb_row_origins (table_name TEXT NOT NULL, row_id INTEGER NOT NULL,
    record_id TEXT NOT NULL REFERENCES swdb_records(id), record_field TEXT NOT NULL,
    PRIMARY KEY (table_name, row_id, record_id, record_field));
CREATE INDEX swdb_row_origins_by_record ON swdb_row_origins (table_name, record_id, record_field);
CREATE TABLE swdb_guessed_columns (table_name TEXT NOT NULL, column_name TEXT NOT NULL, reason TEXT NOT NULL,
    PRIMARY KEY (table_name, column_name));
"""


def groups():
    """Every LANL table group module (`swdb/lanl_*.py`), in build order."""
    names = sorted(path.stem for path in Path(__file__).parent.glob("lanl_*.py"))
    modules = [importlib.import_module(f"swdb.{name}") for name in names]
    return sorted(modules, key=lambda module: (module.ORDER, module.__name__))


class Rows:
    """Inserts LANL rows, each with its origin in `swdb_row_origins`.

    Integer IDs are assigned in insertion order, so a group that inserts in a fixed order
    (sorted by record ID) gets the same IDs on every build of the same records."""

    def __init__(self, con):
        self.con = con
        self._once = {}   # (table, key) -> id, for add_once

    def add(self, table, values, record_id, record_field="id"):
        """Insert one row (`values`: column -> value, `id` left out) and return its new `id`.
        `record_id` and `record_field` name the YAML record and field the row was read from;
        `record_field` is a dotted path with bracketed list indexes (`code[0]`, `parts[2].outcome`)."""
        names = list(values)
        cursor = self.con.execute(f'INSERT INTO "{table}" ({", ".join(names)}) VALUES ({", ".join("?" * len(names))})',
                                  [values[name] for name in names])
        self.origin(table, cursor.lastrowid, record_id, record_field)
        return cursor.lastrowid

    def add_once(self, table, key, values, record_id, record_field="id"):
        """The `id` of the row of `table` for `key`: inserted with `values` on the first call for
        that key; on a later call, `record_id` and `record_field` only add an origin to it."""
        if (table, key) not in self._once:
            self._once[table, key] = self.add(table, values, record_id, record_field)
        else:
            self.origin(table, self._once[table, key], record_id, record_field)
        return self._once[table, key]

    def origin(self, table, row_id, record_id, record_field="id"):
        """One more origin for an existing row (a row that several records name)."""
        self.con.execute("INSERT OR IGNORE INTO swdb_row_origins VALUES (?,?,?,?)",
                         (table, row_id, record_id, record_field))

    def id_of(self, table, slug):
        """The `id` of the row of `table` whose `slug` is `slug` (None if there is none)."""
        row = self.con.execute(f'SELECT id FROM "{table}" WHERE slug = ?', (slug,)).fetchone()
        return None if row is None else row[0]


def evaluated_implementation(store, evaluation):
    """The implementation an evaluation ran, or None when it ran something else. Shared by the
    groups that count an evaluation's outcome or timing as an implementation's (`Validation_results`,
    `performance_runs`). An evaluation runs the candidate its `request.candidate` names (an
    aggregate, which has no request candidate, names it as `candidate`); with no candidate it ran
    its `implementation`. Only a candidate that is the implementation's unchanged source
    (`artifact_role: source_baseline`) is that implementation. A rewrite candidate's results are
    not its baseline's, so they stay in the `swdb_` tables."""
    request = evaluation.get("request") or {}
    named = request.get("candidate")
    if named is None:
        named = evaluation.get("candidate")
    if named is None:
        return evaluation.get("implementation")
    candidate = store.get(named, "candidate") if isinstance(named, str) else None
    if candidate is None or candidate.get("artifact_role") != "source_baseline":
        return None
    return candidate.get("implementation")


def evaluation_workload(evaluation):
    """(workload ID, the record field naming it) of an evaluation: `request.workload.id`, or
    `request.workload` when it is a bare ID."""
    workload = (evaluation.get("request") or {}).get("workload")
    if isinstance(workload, dict):
        return workload.get("id"), "request.workload.id"
    return workload, "request.workload"


def build(con, store):
    """Create and fill every LANL table group, after the `swdb_` tables are filled."""
    con.executescript(SCHEMA)
    rows = Rows(con)
    for group in groups():
        con.executescript(group.SCHEMA)
        con.executemany("INSERT INTO swdb_guessed_columns VALUES (?,?,?)", group.GUESSED)
        group.fill(rows, store)
