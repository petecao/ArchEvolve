"""The SQLite database, generated from the records (ADR 0002) and never committed.

`build` deletes the file and recreates every table from the YAML records, so the database
cannot drift from them. Tables are documented in docs/reference/database.md.
Updated: 2026-10-06 ET: all connections are owned by swdb.access (ADR 0014).
Updated: 2026-10-11 ET: every table carries the `swdb_` prefix (LANL-shaped-db ticket 01), which
frees the LANL table names; a file with the old names has no `swdb_meta`, so it reads as stale.
Updated: 2026-10-11 ET: `swdb.lanl` adds the LANL core after the `swdb_` tables, and a build
fails if `PRAGMA foreign_key_check` reports a row (LANL-shaped-db ticket 02).
"""

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path

from swdb import access, lanl
from swdb.store import Record, Store, record_files
from swdb.strategy import SEMANTIC_FIELDS, entry, pattern_outcome

SCHEMA = f"""
CREATE TABLE swdb_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE swdb_records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, status TEXT, path TEXT NOT NULL, json TEXT NOT NULL);
CREATE TABLE swdb_applications (id TEXT PRIMARY KEY, name TEXT, commit_hash TEXT, language TEXT, parallel_model TEXT,
    domain TEXT, json TEXT NOT NULL);
CREATE TABLE swdb_kernels (id TEXT PRIMARY KEY, name TEXT, application TEXT, baseline_implementation TEXT,
    json TEXT NOT NULL);
CREATE TABLE swdb_implementations (id TEXT PRIMARY KEY, name TEXT, kernel TEXT, function TEXT, origin TEXT,
    is_baseline INTEGER NOT NULL, json TEXT NOT NULL);
CREATE TABLE swdb_implementation_contexts (implementation TEXT PRIMARY KEY, application TEXT NOT NULL,
    source_ancestor TEXT, source_baseline TEXT, comparison_baseline TEXT, json TEXT NOT NULL);
CREATE TABLE swdb_inputs (id TEXT PRIMARY KEY, name TEXT, generator_arguments TEXT, file_path TEXT, json TEXT NOT NULL);
CREATE TABLE swdb_input_properties (input TEXT NOT NULL, name TEXT NOT NULL, value TEXT, basis TEXT NOT NULL,
    PRIMARY KEY (input, name));
CREATE TABLE swdb_machines (id TEXT PRIMARY KEY, hostname TEXT, cpu_model TEXT, sockets INTEGER, cores_per_socket INTEGER,
    llc_bytes INTEGER, counters_available INTEGER, json TEXT NOT NULL);
CREATE TABLE swdb_profiles (id TEXT PRIMARY KEY, implementation TEXT, input TEXT, machine TEXT, complete INTEGER,
    correctness TEXT, started TEXT, bottleneck TEXT, bottleneck_basis TEXT, memory_limit TEXT, json TEXT NOT NULL);
CREATE TABLE swdb_metrics (profile TEXT NOT NULL, name TEXT NOT NULL, value REAL, value_json TEXT, unit TEXT,
    basis TEXT, threads INTEGER, array_name TEXT, scope TEXT, tool TEXT);
CREATE TABLE swdb_access_patterns (implementation TEXT NOT NULL, pattern TEXT NOT NULL, kernel TEXT, expression TEXT,
    loop TEXT, update_kind TEXT, pattern_class TEXT,
    {", ".join(f"{name} TEXT, {name}_basis TEXT" for name in SEMANTIC_FIELDS)},
    semantics_json TEXT, PRIMARY KEY (implementation, pattern));
CREATE TABLE swdb_steps (implementation TEXT NOT NULL, pattern TEXT NOT NULL, position INTEGER NOT NULL,
    array_name TEXT, role TEXT, element_type TEXT, element_bytes INTEGER, element_count TEXT, layout TEXT,
    address_shape TEXT, stride INTEGER, index_transform TEXT, PRIMARY KEY (implementation, pattern, position));
CREATE TABLE swdb_machine_flags (machine TEXT NOT NULL, flag TEXT NOT NULL, PRIMARY KEY (machine, flag));
CREATE TABLE swdb_intrinsics (id TEXT PRIMARY KEY, name TEXT, isa_family TEXT, isa_extensions TEXT, header TEXT,
    memory_kind TEXT, address_shape TEXT, element_bits INTEGER, lanes INTEGER, json TEXT NOT NULL);
CREATE TABLE swdb_strategies (id TEXT PRIMARY KEY, name TEXT, target TEXT, json TEXT NOT NULL);
CREATE TABLE swdb_strategy_effects (strategy TEXT NOT NULL, position INTEGER NOT NULL, kind TEXT NOT NULL, json TEXT NOT NULL,
    PRIMARY KEY (strategy, position));
CREATE TABLE swdb_strategy_intrinsics (strategy TEXT NOT NULL, intrinsic TEXT NOT NULL, PRIMARY KEY (strategy, intrinsic));
CREATE TABLE swdb_applied_strategies (implementation TEXT NOT NULL, position INTEGER NOT NULL, strategy TEXT NOT NULL,
    target TEXT NOT NULL, parameters_json TEXT NOT NULL, PRIMARY KEY (implementation, position));
CREATE TABLE swdb_implementation_intrinsics (implementation TEXT NOT NULL, intrinsic TEXT NOT NULL,
    PRIMARY KEY (implementation, intrinsic));
CREATE TABLE swdb_intrinsic_extensions (intrinsic TEXT NOT NULL, extension TEXT NOT NULL, PRIMARY KEY (intrinsic, extension));
CREATE TABLE swdb_library_entries (id TEXT PRIMARY KEY, kind TEXT NOT NULL, path TEXT NOT NULL, content_sha256 TEXT NOT NULL,
    tier TEXT, status TEXT, derived_from TEXT, json TEXT NOT NULL);
CREATE TABLE swdb_library_dependencies (entry TEXT NOT NULL, dependency TEXT NOT NULL, content_sha256 TEXT NOT NULL,
    PRIMARY KEY (entry, dependency));
CREATE TABLE swdb_library_clauses (entry TEXT NOT NULL, clause TEXT NOT NULL, role TEXT, discharge_mode TEXT,
    negative_control TEXT, statement TEXT, PRIMARY KEY (entry, clause));
CREATE TABLE swdb_statements (implementation TEXT NOT NULL, statement TEXT NOT NULL, function TEXT, path TEXT,
    first_line INTEGER, last_line INTEGER, revision TEXT, code TEXT, basis TEXT, depends_on TEXT,
    agent_claims INTEGER NOT NULL, json TEXT NOT NULL, PRIMARY KEY (implementation, statement));
CREATE TABLE swdb_statement_steps (implementation TEXT NOT NULL, statement TEXT NOT NULL, pattern TEXT NOT NULL,
    step INTEGER NOT NULL, PRIMARY KEY (implementation, statement, pattern, step));
CREATE TABLE swdb_statement_facts (implementation TEXT NOT NULL, statement TEXT NOT NULL, position INTEGER NOT NULL,
    field TEXT NOT NULL, value TEXT, basis TEXT, evidence TEXT, PRIMARY KEY (implementation, statement, position));
CREATE TABLE swdb_library_pattern_keys (entry TEXT NOT NULL, key_position INTEGER NOT NULL, update_kind TEXT,
    step_count INTEGER NOT NULL, PRIMARY KEY (entry, key_position));
CREATE TABLE swdb_library_pattern_key_steps (entry TEXT NOT NULL, key_position INTEGER NOT NULL, step INTEGER NOT NULL,
    role TEXT, address_shape TEXT, PRIMARY KEY (entry, key_position, step));
"""


# identifies the code that builds the file: any change to the swdb package (tables, how rows
# are filled, which records load) makes older files stale
BUILDER = hashlib.sha256(b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py")))).hexdigest()

def default_path(records_dir):
    """build/swdb.sqlite next to a folder named `records` (the repo's), otherwise
    build/swdb-<folder name>.sqlite, so sibling records folders get their own files."""
    records_dir = Path(records_dir).resolve()
    name = "swdb.sqlite" if records_dir.name == "records" else f"swdb-{records_dir.name}.sqlite"
    return records_dir.parent / "build" / name


def library_dir(records_dir, library=None):
    """The typed library a records folder uses (the repository's beside `records`), or
    `library` when a caller names one (ticket 55: `swdb campaign --library`)."""
    from swdb.library import default_root
    return Path(library if library is not None else default_root(Path(records_dir))).resolve()


def library_files(records_dir, library=None):
    """Every regular file of that library folder (YAML entries and pinned code), sorted."""
    root = library_dir(records_dir, library)
    if not root.is_dir():
        return []
    return [(path, path.relative_to(root).as_posix()) for path in sorted(root.rglob("*"))
            if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts]


def fingerprint(records_dir, library=None):
    """Identifies the exact set of record files and, since ticket 46 (2026-10-03 ET), of the
    typed library folder's files: path, size, and modification time of each."""
    digest = hashlib.sha256()
    for path, rel in record_files(Path(records_dir)):
        info = path.stat()
        digest.update(f"{rel}\0{info.st_size}\0{info.st_mtime_ns}\n".encode())
    for path, rel in library_files(records_dir, library):
        info = path.stat()
        digest.update(f"library/{rel}\0{info.st_size}\0{info.st_mtime_ns}\n".encode())
    return digest.hexdigest()


def meta(db_path):
    """The built database's `swdb_meta` table ({} when unreadable); public since 2026-10-05 ET (code review F15)."""
    try:
        return {row["key"]: row["value"] for row in access.query(db_path, "SELECT key, value FROM swdb_meta")}
    except sqlite3.Error:
        return {}


def is_stale(records_dir, db_path, library=None):
    """True unless the database was built from this very folder (and library folder) in its
    current state, by the same database code (a newer swdb may add tables or fill them differently)."""
    db_path = Path(db_path)
    if not db_path.exists():
        return True
    found = meta(db_path)
    return (found.get("records_dir") != str(Path(records_dir).resolve())
            or found.get("library_dir") != str(library_dir(records_dir, library))
            or found.get("fingerprint") != fingerprint(records_dir, library)
            or found.get("builder") != BUILDER)


def _flag(value):
    """A boolean fact as 1/0, and NULL when unknown (unknown is never false)."""
    return None if value is None else int(bool(value))


def _text(value):
    """Semantic and property values as text: JSON for everything, so true/false/null stay distinct."""
    return json.dumps(value)


def build(records_dir, db_path, library=None):
    started = time.monotonic()
    # fingerprint first: a record written while the store loads makes the stamp older than
    # the files, so the next query rebuilds instead of trusting a stale database
    stamp = fingerprint(records_dir, library)
    store = Store(Path(records_dir))
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_name(f".{db_path.name}.{os.getpid()}.tmp")   # unique per process; renamed at the end
    if tmp.exists():
        tmp.unlink()
    con = access.create_index(tmp)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO swdb_meta VALUES (?, ?)", [("records_dir", str(Path(records_dir).resolve())),
                                                       ("library_dir", str(library_dir(records_dir, library))),
                                                       ("fingerprint", stamp), ("builder", BUILDER)])
    kernels = {r.id: r.data for r in store.of_kind("kernel")}
    baselines = {k["baseline_implementation"] for k in kernels.values()}
    for rec in store.records:
        if store.by_id.get(rec.id) is not rec:
            continue
        d = rec.data
        con.execute("INSERT INTO swdb_records VALUES (?,?,?,?,?)", (rec.id, rec.kind, d.get("status"), rec.rel, json.dumps(d)))
        getattr(_Insert, rec.kind, lambda *a: None)(con, d, rec.id in baselines, kernels)
        if rec.kind == "implementation":
            context = store.source_context(d)
            con.execute("INSERT INTO swdb_implementation_contexts VALUES (?,?,?,?,?,?)",
                        (rec.id, context["application"], context["source_ancestor"], context["source_baseline"],
                         context["comparison_baseline"], json.dumps(context)))
    _library(con, records_dir, store, library)
    from swdb import derived     # Probata PoC 19: contract lineage and rewrite links, computed on read
    derived.index(con, store, library_dir(records_dir, library))
    lanl.build(con, store)
    tables = [name for (name,) in con.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY rowid")]
    lanl_rows = {name: con.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
                 for name in tables if not name.startswith("swdb_")}
    broken = con.execute("PRAGMA foreign_key_check").fetchall()
    con.commit()
    con.close()
    if broken:
        tmp.unlink()
        raise _failure("database build broke its foreign keys (table, rowid, parent, key): "
                       + "; ".join(map(str, broken[:5])))
    tmp.replace(db_path)
    # lanl_rows: rows per LANL core table, so a build reports the core without a second query
    return {"records": len(store.records), "seconds": time.monotonic() - started,
            "lanl_rows": lanl_rows, "swdb_tables": len(tables) - len(lanl_rows)}


def _library(con, records_dir, store, library_root=None):
    """Ticket 46 (2026-10-03 ET): typed library entries, their dependency pins and clauses.

    Tier and status are derived from the records exactly as `swdb.library` derives them;
    an entry whose state cannot be derived (for example an invalid library) gets NULL."""
    from swdb.library import Library, derived_from
    root = library_dir(records_dir, library_root)
    if not root.is_dir():
        return
    library = Library(root, store)
    for entry_id, data in sorted(library.entries.items()):
        try:
            state = library.state(entry_id)
        except Exception:  # noqa: BLE001 -- a broken entry is still indexed, without derived state
            state = {"tier": None, "status": None}
        try:
            pins = library.dependency_pins(entry_id)
        except ValueError:
            pins = []
        con.execute("INSERT INTO swdb_library_entries VALUES (?,?,?,?,?,?,?,?)",
                    (entry_id, data.get("kind"), library.files[entry_id].relative_to(root).as_posix(),
                     library.content_sha256(entry_id), state["tier"], state["status"], derived_from(data),
                     json.dumps(data)))
        con.executemany("INSERT INTO swdb_library_dependencies VALUES (?,?,?)",
                        [(entry_id, pin["id"], pin["content_sha256"]) for pin in pins])
        clauses = data.get("clauses") if isinstance(data.get("clauses"), list) else []
        con.executemany("INSERT OR IGNORE INTO swdb_library_clauses VALUES (?,?,?,?,?,?)",
                        [(entry_id, c.get("id"), c.get("role"), c.get("discharge_mode"),
                          (c.get("negative_control") or {}).get("id"), c.get("statement"))
                         for c in clauses if isinstance(c, dict) and isinstance(c.get("id"), str)])
        # Ticket 55 (2026-10-04 ET): pattern keys as rows, one per key pattern and one per
        # key step, so the site finder matches them against `swdb_steps` in SQL. A malformed key
        # pattern (not a list of equal-length roles and shapes) is indexed as written; it
        # can never match, because its steps cannot all equal one chain.
        keys = data.get("pattern_key") if isinstance(data.get("pattern_key"), list) else []
        for position, key in enumerate(keys):
            if not isinstance(key, dict):
                continue
            roles = key.get("roles") if isinstance(key.get("roles"), list) else []
            shapes = key.get("address_shapes") if isinstance(key.get("address_shapes"), list) else []
            con.execute("INSERT INTO swdb_library_pattern_keys VALUES (?,?,?,?)",
                        (entry_id, position, key.get("update_kind"), max(len(roles), len(shapes))))
            con.executemany("INSERT INTO swdb_library_pattern_key_steps VALUES (?,?,?,?,?)",
                            [(entry_id, position, step, roles[step] if step < len(roles) else None,
                              shapes[step] if step < len(shapes) else None)
                             for step in range(max(len(roles), len(shapes)))])


class _Insert:
    @staticmethod
    def application(con, d, *_):
        con.execute("INSERT INTO swdb_applications VALUES (?,?,?,?,?,?,?)",
                    (d["id"], d["name"], d["source"]["commit"], d["language"], d["parallel_model"], d["domain"],
                     json.dumps(d)))

    @staticmethod
    def kernel(con, d, *_):
        con.execute("INSERT INTO swdb_kernels VALUES (?,?,?,?,?)",
                    (d["id"], d["name"], d["application"], d["baseline_implementation"], json.dumps(d)))

    @staticmethod
    def implementation(con, d, is_baseline, kernels):
        con.execute("INSERT INTO swdb_implementations VALUES (?,?,?,?,?,?,?)",
                    (d["id"], d["name"], d["kernel"], d["function"], d["origin"]["kind"], int(is_baseline),
                     json.dumps(d)))
        con.executemany("INSERT INTO swdb_implementation_intrinsics VALUES (?,?)",
                        [(d["id"], i) for i in d.get("uses_intrinsics", [])])
        con.executemany("INSERT INTO swdb_applied_strategies VALUES (?,?,?,?,?)",
                        [(d["id"], i, a["strategy"], a["target"], json.dumps(a["parameters"]))
                         for i, a in enumerate(d.get("applies", []))])
        for p in d["access_patterns"]:
            sem = p["semantics"]
            cols = []
            for name in SEMANTIC_FIELDS:
                cols += [_text(sem[name]["value"]), sem[name]["basis"]]
            con.execute(f"INSERT INTO swdb_access_patterns VALUES ({','.join('?' * (8 + 2 * len(SEMANTIC_FIELDS)))})",
                        (d["id"], p["id"], d["kernel"], p["expression"], p["loop"], p["update_kind"],
                         pattern_class(p), *cols, json.dumps(sem)))
            for i, s in enumerate(p["steps"]):
                a = s["array"]
                con.execute("INSERT INTO swdb_steps VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            (d["id"], p["id"], i, a["name"], a["role"], a["element_type"], a["element_bytes"],
                             a["element_count"], a["layout"], s["address_shape"], s.get("stride"),
                             s.get("index_transform")))
        # Ticket 46 (2026-10-03 ET): the statements index (statement annotations, ticket 35).
        statements = (d.get("extensions") or {}).get("statements") or {}
        for row in statements.get("annotations", []):
            source = row.get("source") or {}
            lines = source.get("lines") or [None, None]
            con.execute("INSERT INTO swdb_statements VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (d["id"], row["id"], statements.get("function"), source.get("path"), lines[0], lines[-1],
                         source.get("revision"), row.get("code"), row.get("basis"),
                         json.dumps(row.get("depends_on", [])), len(row.get("agent_claims", [])), json.dumps(row)))
            con.executemany("INSERT OR IGNORE INTO swdb_statement_steps VALUES (?,?,?,?)",
                            [(d["id"], row["id"], step["pattern"], step["step"])
                             for step in row.get("access_pattern_steps", [])])
            # Ticket 55 (2026-10-04 ET): recorded statement facts (never agent claims); the
            # site finder reads legality facts from here. Values are JSON text.
            con.executemany("INSERT INTO swdb_statement_facts VALUES (?,?,?,?,?,?,?)",
                            [(d["id"], row["id"], i, f.get("field"), _text(f.get("value")), f.get("basis"),
                              f.get("evidence"))
                             for i, f in enumerate(row.get("annotation_facts", [])) if isinstance(f, dict)])

    @staticmethod
    def input(con, d, *_):
        con.execute("INSERT INTO swdb_inputs VALUES (?,?,?,?,?)",
                    (d["id"], d["name"], (d.get("generator") or {}).get("arguments"), (d.get("file") or {}).get("path"),
                     json.dumps(d)))
        for name, fact in d["properties"].items():
            con.execute("INSERT INTO swdb_input_properties VALUES (?,?,?,?)", (d["id"], name, _text(fact["value"]), fact["basis"]))

    @staticmethod
    def machine(con, d, *_):
        from swdb.machine import llc_bytes

        con.execute("INSERT INTO swdb_machines VALUES (?,?,?,?,?,?,?,?)",
                    (d["id"], d["hostname"], d["cpu"]["model"], d["cpu"]["sockets"], d["cpu"]["cores_per_socket"],
                     llc_bytes(d), _flag(d["counters"]["hardware_counters_available"]["value"]), json.dumps(d)))
        con.executemany("INSERT INTO swdb_machine_flags VALUES (?,?)", [(d["id"], f) for f in d["cpu"].get("flags", [])])

    @staticmethod
    def strategy(con, d, *_):
        con.execute("INSERT INTO swdb_strategies VALUES (?,?,?,?)", (d["id"], d["name"], d["target"], json.dumps(d)))
        con.executemany("INSERT INTO swdb_strategy_effects VALUES (?,?,?,?)",
                        [(d["id"], i, e["kind"], json.dumps(e)) for i, e in enumerate(d["effect"])])
        con.executemany("INSERT INTO swdb_strategy_intrinsics VALUES (?,?)", [(d["id"], i) for i in d.get("common_intrinsics", [])])

    @staticmethod
    def intrinsic(con, d, *_):
        con.execute("INSERT INTO swdb_intrinsics VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (d["id"], d["name"], d.get("isa_family"), json.dumps(d.get("isa_extensions", [])), d.get("header"),
                     d["memory_kind"], d["address_shape"], d["element_bits"], d["lanes"], json.dumps(d)))
        con.executemany("INSERT INTO swdb_intrinsic_extensions VALUES (?,?)", [(d["id"], e) for e in d.get("isa_extensions", [])])

    @staticmethod
    def profile(con, d, *_):
        b = d["bottleneck"]
        check = next((p["outcome"] for p in d["parts"] if p["part"] == "correctness"), None)
        con.execute("INSERT INTO swdb_profiles VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (d["id"], d["implementation"], d["input"], d["machine"], int(d["complete"]),
                     {"complete": "passed", None: None}.get(check, "not_established"),
                     d["environment"]["started"], b["value"], b["basis"], b["memory_limit"], json.dumps(d)))
        for m in d["metrics"]:
            number = m["value"] if isinstance(m["value"], (int, float)) and not isinstance(m["value"], bool) else None
            con.execute("INSERT INTO swdb_metrics VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (d["id"], m["name"], number, json.dumps(m["value"]), m["unit"], m["basis"], m.get("threads"),
                         m.get("array"), m.get("scope"), m.get("tool")))


def pattern_class(pattern):
    """The pattern class: the address shapes of the steps, then the update kind."""
    return " > ".join(s["address_shape"] for s in pattern["steps"]) + " : " + pattern["update_kind"]


def _connect(db_path):
    return access.open_index(db_path)


def sql(db_path, query):
    con = _connect(db_path)
    try:
        return [dict(row) for row in con.execute(query)]
    except sqlite3.Error as exc:
        raise _failure(f"SQL error: {exc}") from None
    finally:
        con.close()


def query_store(records_dir, db_path=None):
    """Validated, freshness-checked SQLite record snapshot for public queries.

    Updated: 2026-09-27. Raw-artifact verification remains the query owner's job.
    A single SELECT supplies roots, ancestors and descendants from one snapshot.
    """
    from swdb.cli import _require_valid

    _require_valid(records_dir)
    selected = db_path if db_path is not None else default_path(records_dir)
    if is_stale(records_dir, selected):
        build(records_dir, selected)
    rows = sql(selected, "SELECT path, json FROM swdb_records ORDER BY path")
    return Store(Path(records_dir), indexed_records=[Record(row["path"], json.loads(row["json"])) for row in rows])


def _semantic_column(name):
    if name not in SEMANTIC_FIELDS:
        raise _usage(f"unknown semantic field {name!r}; one of {', '.join(SEMANTIC_FIELDS)}")
    return name


def find(db_path, shapes=(), update=None, semantics=(), kernel=None, strategy=None):
    """Access patterns matching the filters. With `strategy` (an access-pattern strategy ID),
    each is reported with its legality outcome instead, and illegal ones are left out."""
    where, args = [], []
    for shape in shapes:
        where.append("EXISTS (SELECT 1 FROM swdb_steps s WHERE s.implementation = p.implementation "
                     "AND s.pattern = p.pattern AND s.address_shape = ?)")
        args.append(shape)
    if update:
        where.append("p.update_kind = ?")
        args.append(update)
    for name, value in semantics:
        column = _semantic_column(name)
        where.append(f"p.{column} = ? AND p.{column}_basis != 'unknown'" if value is not None
                     else f"p.{column}_basis = 'unknown'")
        if value is not None:
            args.append(_text(value))
    if kernel:
        where.append("p.kernel = ?")
        args.append(kernel)
    query = "SELECT * FROM swdb_access_patterns p" + (" WHERE " + " AND ".join(where) if where else "")
    con = _connect(db_path)
    try:
        rows = con.execute(query + " ORDER BY p.implementation, p.pattern", args).fetchall()
        if strategy is None:
            return [_pattern_out(con, row) for row in rows]
        chosen = _strategy(con, strategy, "access_pattern")
        found = []
        for row in rows:
            outcome, _, unknown = pattern_outcome(chosen, _pattern_facts(con, row))
            if outcome != "illegal":
                found.append({"implementation": row["implementation"], "pattern": row["pattern"],
                              "outcome": outcome, "unknown_fields": unknown})
        return found
    finally:
        con.close()


def _pattern_out(con, row):
    steps = con.execute("SELECT * FROM swdb_steps WHERE implementation = ? AND pattern = ? ORDER BY position",
                        (row["implementation"], row["pattern"])).fetchall()
    sem = json.loads(row["semantics_json"])
    return {
        "implementation": row["implementation"], "kernel": row["kernel"], "pattern": row["pattern"],
        "expression": row["expression"], "pattern_class": row["pattern_class"], "update_kind": row["update_kind"],
        "steps": [{"array": s["array_name"], "role": s["role"], "address_shape": s["address_shape"]} for s in steps],
        "semantics": {name: {"value": sem[name]["value"], "basis": sem[name]["basis"]} for name in SEMANTIC_FIELDS},
    }


def implementations(db_path, kernel, requirements):
    """A kernel's implementations whose every access pattern has each required value, with a
    known basis (unknown is not false, so it never satisfies a requirement)."""
    con = _connect(db_path)
    try:
        return _meeting(con, kernel, requirements)
    finally:
        con.close()


def _meeting(con, kernel, requirements):
    if con.execute("SELECT 1 FROM swdb_kernels WHERE id = ?", (kernel,)).fetchone() is None:
        return None
    found = []
    for impl in con.execute("SELECT * FROM swdb_implementations WHERE kernel = ? ORDER BY is_baseline DESC, id", (kernel,)):
        patterns = con.execute("SELECT * FROM swdb_access_patterns WHERE implementation = ?", (impl["id"],)).fetchall()
        failing = []
        for name, value in requirements:
            column = _semantic_column(name)
            for p in patterns:
                if p[f"{column}_basis"] == "unknown" or json.loads(p[column]) != value:
                    failing.append(f"{p['pattern']}.{name} is {json.loads(p[column])!r} ({p[f'{column}_basis']})")
        if not failing:
            context = json.loads(con.execute("SELECT json FROM swdb_implementation_contexts WHERE implementation = ?",
                                             (impl["id"],)).fetchone()["json"])
            found.append({"implementation": impl["id"], "name": impl["name"], "function": impl["function"],
                          "baseline": bool(impl["is_baseline"]), "origin": impl["origin"],
                          "source_context": context,
                          "meets": {name: value for name, value in requirements}})
    return found


# --- strategies ---------------------------------------------------------------------

def _usage(message):
    from swdb.cli import UsageError

    return UsageError(message)


def _failure(message):
    from swdb.cli import Failure

    return Failure(message)


def _strategy(con, strategy_id, target):
    row = con.execute("SELECT json FROM swdb_strategies WHERE id = ?", (strategy_id,)).fetchone()
    if row is None:
        raise _failure(f"strategy {strategy_id!r} does not exist")
    data = json.loads(row["json"])
    if data["target"] != target:
        raise _usage(f"strategy {strategy_id!r} targets {data['target']}, not {target}")
    return data


def _strategies(con, target):
    return [json.loads(r["json"]) for r in con.execute("SELECT json FROM swdb_strategies WHERE target = ? ORDER BY id", (target,))]


def _pattern_facts(con, row):
    steps = con.execute("SELECT address_shape FROM swdb_steps WHERE implementation = ? AND pattern = ? ORDER BY position",
                        (row["implementation"], row["pattern"])).fetchall()
    return {"steps": [{"address_shape": s["address_shape"]} for s in steps], "update_kind": row["update_kind"],
            "semantics": json.loads(row["semantics_json"])}


def _split(text, what):
    if "/" not in text:
        raise _usage(f"expected <implementation>/<{what}>, got {text!r}")
    return text.split("/", 1)


def strategies_for_pattern(db_path, target):
    """Every access-pattern strategy, with its legality for one access pattern."""
    impl, pattern = _split(target, "pattern")
    con = _connect(db_path)
    try:
        row = con.execute("SELECT * FROM swdb_access_patterns WHERE implementation = ? AND pattern = ?", (impl, pattern)).fetchone()
        if row is None:
            raise _failure(f"access pattern {target!r} does not exist")
        facts = _pattern_facts(con, row)
        return [entry(s, *pattern_outcome(s, facts)) for s in _strategies(con, "access_pattern")]
    finally:
        con.close()


def _implementation(con, impl_id):
    row = con.execute("SELECT json FROM swdb_implementations WHERE id = ?", (impl_id,)).fetchone()
    if row is None:
        raise _failure(f"implementation {impl_id!r} does not exist")
    return json.loads(row["json"])


def loop_and_children(impl, loop_id):
    """The loop's ID and every loop nested under it, at any depth."""
    found, frontier = {loop_id}, [loop_id]
    while frontier:
        parent = frontier.pop()
        for loop in impl["loops"]:
            if loop.get("parent") == parent and loop["id"] not in found:
                found.add(loop["id"])
                frontier.append(loop["id"])
    return found


def strategies_for_loop(db_path, target):
    """Every loop strategy, checked against every access pattern in the loop and its child
    loops: legal only when all of them pass, illegal when any known value contradicts,
    otherwise undetermined, naming `<pattern>.<field>` for each unknown."""
    impl_id, loop_id = _split(target, "loop")
    con = _connect(db_path)
    try:
        impl = _implementation(con, impl_id)
        if loop_id not in {loop["id"] for loop in impl["loops"]}:
            raise _failure(f"loop {target!r} does not exist")
        loops = loop_and_children(impl, loop_id)
        rows = con.execute(f"SELECT * FROM swdb_access_patterns WHERE implementation = ? AND loop IN "
                           f"({','.join('?' * len(loops))}) ORDER BY pattern", (impl_id, *sorted(loops))).fetchall()
        patterns = [(row["pattern"], _pattern_facts(con, row)) for row in rows]
        found = []
        for strategy in _strategies(con, "loop"):
            reasons, unknown = [], []
            for name, facts in patterns:
                _, why, missing = pattern_outcome(strategy, facts)
                reasons += [f"{name}: {text}" for text in why]
                unknown += [f"{name}.{field}" for field in missing]
            outcome = "illegal" if reasons else "undetermined" if unknown or not patterns else "legal"
            extra = [] if patterns else [f"loop {loop_id} and its child loops record no access patterns"]
            found.append(entry(strategy, outcome, reasons, unknown, extra))
        return found
    finally:
        con.close()


def strategies_for_input(db_path, impl_id):
    """Every input strategy for one implementation's input. Their preconditions are prose, so
    each is undetermined and its conditions are listed to check by hand."""
    con = _connect(db_path)
    try:
        _implementation(con, impl_id)
        return [entry(strategy, "undetermined", [], []) for strategy in _strategies(con, "input")]
    finally:
        con.close()


def _newest_complete(con, impl_id):
    """{(input, machine): newest complete profile ID} for one implementation."""
    rows = con.execute("SELECT id, input, machine FROM swdb_profiles WHERE implementation = ? AND complete = 1 "
                       "ORDER BY started, id", (impl_id,)).fetchall()
    return {(r["input"], r["machine"]): r["id"] for r in rows}   # later rows win: the newest


def applying(db_path, kernel, strategy_id, requirements=()):
    """A kernel's implementations that apply one strategy, each with its applies entries, its
    derived_from baseline, and per (input, machine) the newest complete profile of both."""
    con = _connect(db_path)
    try:
        allowed = _meeting(con, kernel, requirements)
        if allowed is None:
            return None
        if con.execute("SELECT 1 FROM swdb_strategies WHERE id = ?", (strategy_id,)).fetchone() is None:
            raise _failure(f"strategy {strategy_id!r} does not exist")
        newest = {}   # implementation -> {(input, machine): profile}, each read once
        found = []
        for impl_id in [a["implementation"] for a in allowed]:
            entries = [{"strategy": r["strategy"], "target": r["target"], "parameters": json.loads(r["parameters_json"]),
                        "position": r["position"]}
                       for r in con.execute("SELECT * FROM swdb_applied_strategies WHERE implementation = ? AND strategy = ? "
                                            "ORDER BY position", (impl_id, strategy_id))]
            if not entries:
                continue
            baseline = _implementation(con, impl_id)["origin"].get("derived_from")
            for one in {impl_id, baseline} - {None} - set(newest):
                newest[one] = _newest_complete(con, one)
            mine, theirs = newest[impl_id], newest.get(baseline, {})
            found.append({
                "implementation": impl_id, "applies": entries, "derived_from": baseline,
                "pairing_kind": "historical_ancestry", "gain_claim": False,
                "source_context": next(a["source_context"] for a in allowed if a["implementation"] == impl_id),
                "profiles": [{"input": i, "machine": m, "profile": mine.get((i, m)), "baseline_profile": theirs.get((i, m))}
                             for i, m in sorted(set(mine) | set(theirs))],
            })
        return found
    finally:
        con.close()


def compare(db_path, implementation, baseline, profile, baseline_profile, protocol):
    """Compare exactly selected evidence; ancestry is never a substitute comparator."""
    from swdb.comparison import compare_records

    con = _connect(db_path)
    try:
        records = {row["id"]: json.loads(row["json"]) for row in con.execute("SELECT id, json FROM swdb_records")}
        return compare_records(records, implementation, baseline, profile, baseline_profile, protocol)
    finally:
        con.close()


# Fine-grained attribution ticket 02 (2026-10-11 ET): attribution reports, appended as one
# additive block. SWDB-only tables carry the `swdb_` prefix (LANL-shaped database rule);
# unknown values are NULL. Documented in docs/reference/database.md.
SCHEMA += """
CREATE TABLE swdb_attributions (id TEXT PRIMARY KEY, baseline_estimate TEXT NOT NULL, candidate_estimate TEXT NOT NULL,
    baseline_source TEXT NOT NULL, candidate_source TEXT NOT NULL, target_description TEXT NOT NULL,
    target_description_sha256 TEXT NOT NULL, input TEXT NOT NULL, threads INTEGER NOT NULL, evidence_kind TEXT NOT NULL,
    baseline_seconds REAL, candidate_seconds REAL, total_speedup REAL, amdahl_ceiling REAL, json TEXT NOT NULL,
    unattributed_flagged INTEGER);
CREATE TABLE swdb_attribution_groups (attribution TEXT NOT NULL, origin TEXT NOT NULL, baseline_seconds REAL,
    candidate_seconds REAL, baseline_share REAL, candidate_share REAL, realized_speedup REAL, drift REAL,
    unknown_regions INTEGER NOT NULL, PRIMARY KEY (attribution, origin));
CREATE TABLE swdb_attribution_regions (attribution TEXT NOT NULL, side TEXT NOT NULL, region TEXT NOT NULL,
    origin TEXT NOT NULL, reason TEXT NOT NULL, path TEXT, first_line INTEGER, last_line INTEGER, seconds REAL,
    sites TEXT NOT NULL, mixed INTEGER NOT NULL, matched_region TEXT, PRIMARY KEY (attribution, side, region));
"""


def _insert_attribution_report(con, d):
    whole = d["whole_program"]
    con.execute("INSERT INTO swdb_attributions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (d["id"], d["baseline_estimate"]["id"], d["candidate_estimate"]["id"], d["baseline_source"]["id"],
                 d["candidate_source"]["id"], d["target_description"]["id"], d["target_description"]["sha256"],
                 d["input"], d["threads"], d["evidence_kind"], whole["baseline_seconds"], whole["candidate_seconds"],
                 whole["total_speedup"], whole["amdahl_ceiling"], json.dumps(d), whole["unattributed_flagged"]))
    con.executemany("INSERT INTO swdb_attribution_groups VALUES (?,?,?,?,?,?,?,?,?)",
                    [(d["id"], g["origin"], g["baseline_seconds"], g["candidate_seconds"], g["baseline_share"],
                      g["candidate_share"], g["realized_speedup"], g.get("drift"), len(g["unknown"])) for g in d["groups"]])
    con.executemany("INSERT INTO swdb_attribution_regions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    [(d["id"], r["side"], r["region"], r["origin"], r["reason"], r["path"],
                      r["lines"][0] if r["lines"] else None, r["lines"][1] if r["lines"] else None,
                      r["seconds"], json.dumps(r["sites"]), int(r["mixed"]), r["matched_region"]) for r in d["regions"]])


# Fine-grained attribution ticket 05 (2026-10-11 ET): the rewritten group split by origin.
SCHEMA += """
CREATE TABLE swdb_attribution_origins (attribution TEXT NOT NULL, origin TEXT NOT NULL, baseline_seconds REAL,
    candidate_seconds REAL, baseline_share REAL, candidate_share REAL, unknown_regions INTEGER NOT NULL,
    PRIMARY KEY (attribution, origin));
"""


def _insert_attribution_origins(con, d):
    con.executemany("INSERT INTO swdb_attribution_origins VALUES (?,?,?,?,?,?,?)",
                    [(d["id"], o["origin"], o["baseline_seconds"], o["candidate_seconds"], o["baseline_share"],
                      o["candidate_share"], len(o["unknown"]))
                     for g in d["groups"] for o in g.get("origins", [])])


# Fine-grained attribution ticket 06 (2026-10-11 ET): the `this_iteration` comparison (previous
# accepted candidate -> candidate), only for reports given a previous candidate. Inside it,
# `baseline_*` columns mean the previous accepted candidate.
SCHEMA += """
CREATE TABLE swdb_attribution_iterations (attribution TEXT PRIMARY KEY, iteration INTEGER NOT NULL,
    previous_estimate TEXT NOT NULL, previous_source TEXT NOT NULL, earlier_sources TEXT NOT NULL,
    previous_seconds REAL, candidate_seconds REAL, total_speedup REAL, amdahl_ceiling REAL);
CREATE TABLE swdb_attribution_iteration_groups (attribution TEXT NOT NULL, origin TEXT NOT NULL, baseline_seconds REAL,
    candidate_seconds REAL, baseline_share REAL, candidate_share REAL, realized_speedup REAL, drift REAL,
    unknown_regions INTEGER NOT NULL, PRIMARY KEY (attribution, origin));
CREATE TABLE swdb_attribution_iteration_regions (attribution TEXT NOT NULL, side TEXT NOT NULL, region TEXT NOT NULL,
    origin TEXT NOT NULL, reason TEXT NOT NULL, path TEXT, first_line INTEGER, last_line INTEGER, seconds REAL,
    sites TEXT NOT NULL, last_changed_iteration INTEGER, PRIMARY KEY (attribution, side, region));
"""


def _insert_attribution_iteration(con, d):
    this = d.get("this_iteration")
    if this is None:
        return
    whole = this["whole_program"]
    con.execute("INSERT INTO swdb_attribution_iterations VALUES (?,?,?,?,?,?,?,?,?)",
                (d["id"], this["iteration"], this["previous_estimate"]["id"], this["previous_source"]["id"],
                 json.dumps([pin["id"] for pin in this["earlier_sources"]]), whole["baseline_seconds"],
                 whole["candidate_seconds"], whole["total_speedup"], whole["amdahl_ceiling"]))
    con.executemany("INSERT INTO swdb_attribution_iteration_groups VALUES (?,?,?,?,?,?,?,?,?)",
                    [(d["id"], g["origin"], g["baseline_seconds"], g["candidate_seconds"], g["baseline_share"],
                      g["candidate_share"], g["realized_speedup"], g.get("drift"), len(g["unknown"]))
                     for g in this["groups"]])
    con.executemany("INSERT INTO swdb_attribution_iteration_regions VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    [(d["id"], r["side"], r["region"], r["origin"], r["reason"], r["path"],
                      r["lines"][0] if r["lines"] else None, r["lines"][1] if r["lines"] else None,
                      r["seconds"], json.dumps(r["sites"]), r.get("last_changed_iteration"))
                     for r in this["regions"]])


# Fine-grained attribution ticket 07 (2026-10-11 ET): one headroom row per region and named
# limit (ticket 08 adds `catalog_bound` rows below), and the next-iteration ranking. Headroom rows
# come from the cumulative `regions`; `this_iteration` region floors stay in the JSON column.
SCHEMA += """
CREATE TABLE swdb_attribution_headroom (attribution TEXT NOT NULL, side TEXT NOT NULL, region TEXT NOT NULL,
    limit_name TEXT NOT NULL, limit_seconds REAL, limiting_term TEXT, headroom REAL, reason TEXT,
    missing TEXT NOT NULL, PRIMARY KEY (attribution, side, region, limit_name));
CREATE TABLE swdb_attribution_ranking (attribution TEXT NOT NULL, position INTEGER NOT NULL, side TEXT NOT NULL,
    region TEXT NOT NULL, tier TEXT NOT NULL, limit_name TEXT NOT NULL, value REAL, reason TEXT,
    PRIMARY KEY (attribution, position));
"""


def _insert_attribution_headroom(con, d):
    floors = [(d["id"], r["side"], r["region"], h["limit"], r["resource_floor"]["seconds"],
               r["resource_floor"]["limiting_term"], h["value"], h["reason"], json.dumps(r["resource_floor"]["missing"]))
              for r in d["regions"] for h in r["headroom"] if h["limit"] == "resource_floor"]
    con.executemany("INSERT INTO swdb_attribution_headroom VALUES (?,?,?,?,?,?,?,?,?)", floors)
    con.executemany("INSERT INTO swdb_attribution_ranking VALUES (?,?,?,?,?,?,?,?)",
                    [(d["id"], r["position"], r["side"], r["region"], r["tier"], r["limit"], r["value"], r["reason"])
                     for r in d["ranking"]])


# Fine-grained attribution ticket 08 (2026-10-11 ET): one `catalog_bound` headroom row per
# region (`limiting_term` holds the entry that gives the bound), and one row per region and
# site-finder-matched entry with that entry's own estimate or unknown reason. Rows come from
# the cumulative `regions`; `this_iteration` catalog bounds stay in the JSON column.
SCHEMA += """
CREATE TABLE swdb_attribution_catalog (attribution TEXT NOT NULL, side TEXT NOT NULL, region TEXT NOT NULL,
    entry TEXT NOT NULL, kind TEXT, seconds REAL, reason TEXT, site_finder_regions TEXT NOT NULL, mixed INTEGER NOT NULL,
    missing TEXT NOT NULL, PRIMARY KEY (attribution, side, region, entry));
"""


def _insert_attribution_catalog(con, d):
    rows = [r for r in d["regions"] if "catalog_bound" in r]
    con.executemany("INSERT INTO swdb_attribution_headroom VALUES (?,?,?,?,?,?,?,?,?)",
                    [(d["id"], r["side"], r["region"], h["limit"], r["catalog_bound"]["seconds"], r["catalog_bound"]["entry"],
                      h["value"], h["reason"], json.dumps(r["catalog_bound"]["missing"]))
                     for r in rows for h in r["headroom"] if h["limit"] == "catalog_bound"])
    con.executemany("INSERT INTO swdb_attribution_catalog VALUES (?,?,?,?,?,?,?,?,?,?)",
                    [(d["id"], r["side"], r["region"], e["entry"], e["kind"], e["seconds"], e["reason"],
                      json.dumps(e["site_finder_regions"]), int(r["catalog_bound"]["mixed"]), json.dumps(e["missing"]))
                     for r in rows for e in r["catalog_bound"]["entries"]])


# Fine-grained attribution ticket 09 (2026-10-11 ET): the split check, only for reports given
# region profiles. One verdict row per report, one gap row per side and group; the measured
# scopes stay in the JSON column. `within_rule` is NULL when a share is unknown.
SCHEMA += """
CREATE TABLE swdb_attribution_split_checks (attribution TEXT PRIMARY KEY, verdict TEXT NOT NULL, rule_id TEXT NOT NULL,
    max_abs_share_gap REAL NOT NULL, baseline_profile TEXT NOT NULL, candidate_profile TEXT NOT NULL, reasons TEXT NOT NULL,
    baseline_load_average TEXT, candidate_load_average TEXT);
CREATE TABLE swdb_attribution_split_gaps (attribution TEXT NOT NULL, side TEXT NOT NULL, origin TEXT NOT NULL,
    estimated_share REAL, measured_share REAL, measured_seconds REAL NOT NULL, gap REAL, within_rule INTEGER,
    PRIMARY KEY (attribution, side, origin));
"""


def _insert_attribution_split(con, d):
    check = d.get("split_check")
    if check is None:
        return
    profiles = check["profiles"]
    con.execute("INSERT INTO swdb_attribution_split_checks VALUES (?,?,?,?,?,?,?,?,?)",
                (d["id"], check["verdict"], check["rule"]["id"], check["rule"]["max_abs_share_gap"],
                 profiles["baseline"]["id"], profiles["candidate"]["id"], json.dumps(check["reasons"]),
                 json.dumps(profiles["baseline"]["load_average"]), json.dumps(profiles["candidate"]["load_average"])))
    seconds = {(m["side"], m["origin"]): m["seconds"] for m in check["measured_shares"]}
    con.executemany("INSERT INTO swdb_attribution_split_gaps VALUES (?,?,?,?,?,?,?,?)",
                    [(d["id"], g["side"], g["origin"], g["estimated_share"], g["measured_share"],
                      seconds[g["side"], g["origin"]], g["gap"], None if g["within_rule"] is None else int(g["within_rule"]))
                     for g in check["gaps"]])


# Fine-grained attribution ticket 10 (2026-10-11 ET): what the site finder needs to order its
# regions by a report's ranking (spec F20, F23); the verdict comes from ticket 09's
# `swdb_attribution_split_checks` (no row = not checked).
# One `swdb_attribution_site_finder` row per report given `--site-finder`, with the kernel and
# target its pinned summary ran under; one join row per cumulative region and site-finder region.
SCHEMA += """
CREATE TABLE swdb_attribution_site_finder (attribution TEXT PRIMARY KEY, campaign_summary TEXT NOT NULL,
    iteration INTEGER NOT NULL, kernel TEXT, target TEXT, created TEXT NOT NULL);
CREATE TABLE swdb_attribution_site_finder_regions (attribution TEXT NOT NULL, side TEXT NOT NULL, region TEXT NOT NULL,
    site_finder_region TEXT NOT NULL, PRIMARY KEY (attribution, side, region, site_finder_region));
"""


def _insert_attribution_site_finder(con, d):
    finder = d.get("site_finder")
    if finder is None:
        return
    con.execute("INSERT INTO swdb_attribution_site_finder VALUES (?,?,?,?,?,?)",
                (d["id"], finder["campaign_summary"]["id"], finder["iteration"], finder.get("kernel"),
                 finder.get("target"), str(d["created"])))
    con.executemany("INSERT INTO swdb_attribution_site_finder_regions VALUES (?,?,?,?)",
                    sorted({(d["id"], r["side"], r["region"], sf) for r in d["regions"]
                            for sf in (r.get("catalog_bound") or {}).get("site_finder_regions", [])}))


# Review fix (2026-10-11 ET, finding 10): one explicit, ordered list of the attribution inserts,
# each run exactly once per report, instead of six chained reassignments of `_Insert.attribution`.
_ATTRIBUTION_INSERTS = (_insert_attribution_report, _insert_attribution_iteration, _insert_attribution_origins,
                        _insert_attribution_headroom, _insert_attribution_catalog, _insert_attribution_split,
                        _insert_attribution_site_finder)


def _insert_attribution(con, d, *_):
    for insert in _ATTRIBUTION_INSERTS:
        insert(con, d)


_Insert.attribution = staticmethod(_insert_attribution)


# Probata proof of concept ticket 04 (2026-10-14 ET): proof records (ADR 0016), in the SWDB
# extension only; nothing enters a LANL core table. One row per record, plus its content-hash set
# (one row per single pin, summary or build constant), assumption set and bounds. A pin that does
# not apply has NULL ref and sha256 and its sentence in not_applicable. Unbounded is NULL value with
# unbounded = 1. Ticket 11 (2026-10-14 ET): a skip record has NULL verdict, log_path and log_sha256,
# its skip_reason, and no bounds or assumption rows. Ticket 10 (2026-10-14 ET): replay_label (refuted
# records only; NULL when absent). Documented in docs/reference/database.md.
SCHEMA += """
CREATE TABLE swdb_proofs (id TEXT PRIMARY KEY, subject_kind TEXT NOT NULL, subject_id TEXT, candidate TEXT,
    function TEXT, verdict TEXT, route TEXT, failure_class TEXT, skip_reason TEXT, has_counterexample INTEGER NOT NULL,
    replay_label TEXT, evidence_kind TEXT NOT NULL, adapter TEXT, host TEXT, log_path TEXT, log_sha256 TEXT,
    json TEXT NOT NULL);
CREATE TABLE swdb_proof_pins (proof TEXT NOT NULL, kind TEXT NOT NULL, position INTEGER NOT NULL, ref TEXT,
    sha256 TEXT, function TEXT, proof_record TEXT, value TEXT, not_applicable TEXT,
    PRIMARY KEY (proof, kind, position));
CREATE TABLE swdb_proof_assumptions (proof TEXT NOT NULL, position INTEGER NOT NULL, kind TEXT NOT NULL,
    ref TEXT NOT NULL, sha256 TEXT NOT NULL, sentence TEXT NOT NULL, PRIMARY KEY (proof, position));
CREATE TABLE swdb_proof_bounds (proof TEXT NOT NULL, dimension TEXT NOT NULL, value INTEGER,
    unbounded INTEGER NOT NULL, PRIMARY KEY (proof, dimension));
"""


def _insert_proof(con, d, *_):
    subject, job, log = d["subject"], d.get("job") or {}, (d.get("evidence") or {}).get("adapter_log") or {}
    con.execute("INSERT INTO swdb_proofs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (d["id"], subject["kind"], subject.get("id"), subject.get("candidate"), subject.get("function"),
                 d.get("verdict"), d.get("route"), d.get("failure_class"), d.get("skip_reason"), int("counterexample" in d),
                 d.get("replay_label"), d["evidence_kind"], job.get("adapter"), job.get("host"), log.get("path"), log.get("sha256"), json.dumps(d)))
    pins = []
    for kind, pin in d["pins"].items():
        if kind == "summaries":
            pins += [(d["id"], kind, i, p["id"], p["sha256"], None, p["proof_record"], None, None)
                     for i, p in enumerate(pin)]
        elif kind == "build_constants":
            pins += [(d["id"], kind, i, p["name"], None, None, None, json.dumps(p["value"]), None)
                     for i, p in enumerate(pin)]
        else:
            pins.append((d["id"], kind, 0, pin.get("id"), pin.get("sha256"), pin.get("function"), None, None,
                         pin.get("not_applicable")))
    con.executemany("INSERT INTO swdb_proof_pins VALUES (?,?,?,?,?,?,?,?,?)", pins)
    con.executemany("INSERT INTO swdb_proof_assumptions VALUES (?,?,?,?,?,?)",
                    [(d["id"], i, a["kind"], a["reference"]["id"], a["reference"]["sha256"], a["sentence"])
                     for i, a in enumerate(d.get("assumptions") or [])])
    con.executemany("INSERT INTO swdb_proof_bounds VALUES (?,?,?,?)",
                    [(d["id"], name, None if value == "unbounded" else value, int(value == "unbounded"))
                     for name, value in (d.get("bounds") or {}).items()])


_Insert.proof = staticmethod(_insert_proof)


# Probata proof of concept ticket 19 (2026-10-14 ET): derived implementations' contract lineage (one row per
# entry) and every rewrite link (derived implementations, and candidate artifacts built on one), with whether
# it still matches and its proof route, computed on read by `swdb.derived.link_rows` (ADR 0016). SWDB
# extension only. Documented in docs/reference/database.md.
SCHEMA += """
CREATE TABLE swdb_contract_lineage (implementation TEXT NOT NULL, position INTEGER NOT NULL, contract TEXT NOT NULL,
    version TEXT, content_sha256 TEXT NOT NULL, PRIMARY KEY (implementation, position));
CREATE TABLE swdb_rewrite_links (subject_kind TEXT NOT NULL, subject TEXT NOT NULL, position INTEGER NOT NULL,
    contract TEXT, contract_sha256 TEXT, predecessor TEXT, predecessor_snapshot TEXT,
    predecessor_snapshot_sha256 TEXT, result_candidate TEXT, result_snapshot TEXT, result_sha256 TEXT,
    certification TEXT, proof_route TEXT NOT NULL, matches INTEGER NOT NULL, reason TEXT,
    PRIMARY KEY (subject_kind, subject, position));
"""
# Probata proof of concept ticket 12 (2026-10-14 ET): the fields the evaluation's paired statistics
# query, in the SWDB extension only (no LANL core table gains a field). One `swdb_proof_jobs` row per
# proof record (ticket 12 owns its field list); worker_core is a core number or "unpinned" (NULL:
# written before ticket 12); batch_load_end is NULL for a record that sampled the load at start only.
# One `swdb_run_fields` row per proposal or proof record that carries a run index or provider pin
# (S10), and one `swdb_repair_lineage` row per proposal with repair lineage. Documented in
# docs/reference/database.md.
SCHEMA += """
CREATE TABLE swdb_proof_jobs (proof TEXT PRIMARY KEY, adapter TEXT NOT NULL, host TEXT NOT NULL, worker_core,
    wall_seconds REAL NOT NULL, cpu_seconds REAL NOT NULL, batch_load_start REAL NOT NULL, batch_load_end REAL,
    peak_rss_bytes INTEGER NOT NULL, batch TEXT NOT NULL, position INTEGER NOT NULL);
CREATE TABLE swdb_run_fields (record TEXT PRIMARY KEY, record_kind TEXT NOT NULL, run_index INTEGER,
    provider_kind TEXT, provider_model TEXT, provider_effort TEXT);
CREATE TABLE swdb_repair_lineage (proposal TEXT PRIMARY KEY, refuted_candidate TEXT NOT NULL,
    counterexample_record TEXT NOT NULL, round INTEGER NOT NULL, reverted_repair INTEGER NOT NULL);
"""


def _insert_run_fields(con, d):
    pin = d.get("provider_pin") or {}
    if "run_index" in d or pin:
        con.execute("INSERT INTO swdb_run_fields VALUES (?,?,?,?,?,?)",
                    (d["id"], d["kind"], d.get("run_index"), pin.get("kind"), pin.get("model"), pin.get("effort")))


def _insert_proof_job(con, d, *_):
    _insert_proof(con, d)
    job = d["job"]
    load = job["batch_load"]
    start, end = (load["start"], load["end"]) if isinstance(load, dict) else (load, None)
    con.execute("INSERT INTO swdb_proof_jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (d["id"], job["adapter"], job["host"], job["worker_core"], job["wall_seconds"], job["cpu_seconds"],
                 start, end, job["peak_rss_bytes"], job["batch"], job["position"]))
    _insert_run_fields(con, d)


def _insert_proposal(con, d, *_):
    _insert_run_fields(con, d)
    lineage = d.get("repair_lineage")
    if lineage:
        con.execute("INSERT INTO swdb_repair_lineage VALUES (?,?,?,?,?)",
                    (d["id"], lineage["refuted_candidate"], lineage["counterexample_record"], lineage["round"],
                     int(lineage["reverted_repair"])))


_Insert.proof = staticmethod(_insert_proof_job)
_Insert.proposal = staticmethod(_insert_proposal)
