"""The LANL core of the generated database (LANL-shaped-db spec, 2026-10-09). Created 2026-10-11 ET.

LANL tables carry LANL's names and only the slide's columns, plus an integer `id` and the
guessed link columns. They never reference a `swdb_` table, so deleting every `swdb_` table
leaves a database in LANL's shape that still passes `PRAGMA foreign_key_check`.

Each LANL table group is one module `swdb/lanl_<group>.py` with:

- `ORDER`: an int; groups run in (`ORDER`, module name) order, so a group can look up the
  integer IDs of the groups before it (ticket number x 10 by convention: kernels are 20);
- `SCHEMA`: the group's `CREATE TABLE` statements, with declared foreign keys;
- `GUESSED`: (table, column, reason) for each column the slide does not show;
- `fill(rows, store)`: inserts the rows through `rows.add`, which records each row's origin.

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

    def add(self, table, values, record_id, record_field="id"):
        """Insert one row (`values`: column -> value, `id` left out) and return its new `id`.
        `record_id` and `record_field` name the YAML record and field the row was read from;
        `record_field` is a dotted path with bracketed list indexes (`code[0]`, `parts[2].outcome`)."""
        names = list(values)
        cursor = self.con.execute(f'INSERT INTO "{table}" ({", ".join(names)}) VALUES ({", ".join("?" * len(names))})',
                                  [values[name] for name in names])
        self.origin(table, cursor.lastrowid, record_id, record_field)
        return cursor.lastrowid

    def origin(self, table, row_id, record_id, record_field="id"):
        """One more origin for an existing row (a row that several records name)."""
        self.con.execute("INSERT OR IGNORE INTO swdb_row_origins VALUES (?,?,?,?)",
                         (table, row_id, record_id, record_field))

    def id_of(self, table, slug):
        """The `id` of the row of `table` whose `slug` is `slug` (None if there is none)."""
        row = self.con.execute(f'SELECT id FROM "{table}" WHERE slug = ?', (slug,)).fetchone()
        return None if row is None else row[0]


def build(con, store):
    """Create and fill every LANL table group, after the `swdb_` tables are filled."""
    con.executescript(SCHEMA)
    rows = Rows(con)
    for group in groups():
        con.executescript(group.SCHEMA)
        con.executemany("INSERT INTO swdb_guessed_columns VALUES (?,?,?)", group.GUESSED)
        group.fill(rows, store)
