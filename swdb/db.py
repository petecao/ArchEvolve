"""The SQLite database, generated from the records (ADR 0002) and never committed.

`build` deletes the file and recreates every table from the YAML records, so the database
cannot drift from them. Tables are documented in docs/database.md.
"""

import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path

from swdb.store import Store, record_files

SEMANTIC_FIELDS = ["duplicate_target_indices", "index_modified_during_loop", "loop_carried_dependencies",
                   "shared_target_between_threads", "atomic_updates_required", "ordering", "numerical_requirement"]

SCHEMA = f"""
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, status TEXT, path TEXT NOT NULL, json TEXT NOT NULL);
CREATE TABLE applications (id TEXT PRIMARY KEY, name TEXT, commit_hash TEXT, language TEXT, parallel_model TEXT,
    domain TEXT, json TEXT NOT NULL);
CREATE TABLE kernels (id TEXT PRIMARY KEY, name TEXT, application TEXT, baseline_implementation TEXT,
    json TEXT NOT NULL);
CREATE TABLE implementations (id TEXT PRIMARY KEY, name TEXT, kernel TEXT, function TEXT, origin TEXT,
    is_baseline INTEGER NOT NULL, json TEXT NOT NULL);
CREATE TABLE inputs (id TEXT PRIMARY KEY, name TEXT, generator_arguments TEXT, file_path TEXT, json TEXT NOT NULL);
CREATE TABLE input_properties (input TEXT NOT NULL, name TEXT NOT NULL, value TEXT, basis TEXT NOT NULL,
    PRIMARY KEY (input, name));
CREATE TABLE machines (id TEXT PRIMARY KEY, hostname TEXT, cpu_model TEXT, sockets INTEGER, cores_per_socket INTEGER,
    llc_bytes INTEGER, counters_available INTEGER, json TEXT NOT NULL);
CREATE TABLE profiles (id TEXT PRIMARY KEY, implementation TEXT, input TEXT, machine TEXT, complete INTEGER,
    correctness TEXT, started TEXT, bottleneck TEXT, bottleneck_basis TEXT, memory_limit TEXT, json TEXT NOT NULL);
CREATE TABLE metrics (profile TEXT NOT NULL, name TEXT NOT NULL, value REAL, value_json TEXT, unit TEXT,
    basis TEXT, threads INTEGER, array_name TEXT, scope TEXT, tool TEXT);
CREATE TABLE access_patterns (implementation TEXT NOT NULL, pattern TEXT NOT NULL, kernel TEXT, expression TEXT,
    loop TEXT, update_kind TEXT, pattern_class TEXT,
    {", ".join(f"{name} TEXT, {name}_basis TEXT" for name in SEMANTIC_FIELDS)},
    semantics_json TEXT, PRIMARY KEY (implementation, pattern));
CREATE TABLE steps (implementation TEXT NOT NULL, pattern TEXT NOT NULL, position INTEGER NOT NULL,
    array_name TEXT, role TEXT, element_type TEXT, element_bytes INTEGER, element_count TEXT, layout TEXT,
    address_shape TEXT, stride INTEGER, index_transform TEXT, PRIMARY KEY (implementation, pattern, position));
"""


def default_path(records_dir):
    """build/swdb.sqlite next to a folder named `records` (the repo's), otherwise
    build/swdb-<folder name>.sqlite, so sibling records folders get their own files."""
    records_dir = Path(records_dir).resolve()
    name = "swdb.sqlite" if records_dir.name == "records" else f"swdb-{records_dir.name}.sqlite"
    return records_dir.parent / "build" / name


def fingerprint(records_dir):
    """Identifies the exact set of record files: path, size, and modification time of each."""
    digest = hashlib.sha256()
    for path, rel in record_files(Path(records_dir)):
        info = path.stat()
        digest.update(f"{rel}\0{info.st_size}\0{info.st_mtime_ns}\n".encode())
    return digest.hexdigest()


def _meta(db_path):
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            return dict(con.execute("SELECT key, value FROM meta"))
        finally:
            con.close()
    except sqlite3.Error:
        return {}


def is_stale(records_dir, db_path):
    """True unless the database was built from this very folder in its current state."""
    db_path = Path(db_path)
    if not db_path.exists():
        return True
    meta = _meta(db_path)
    return (meta.get("records_dir") != str(Path(records_dir).resolve())
            or meta.get("fingerprint") != fingerprint(records_dir))


def _flag(value):
    """A boolean fact as 1/0, and NULL when unknown (unknown is never false)."""
    return None if value is None else int(bool(value))


def _text(value):
    """Semantic and property values as text: JSON for everything, so true/false/null stay distinct."""
    return json.dumps(value)


def build(records_dir, db_path):
    started = time.monotonic()
    store = Store(Path(records_dir))
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_name(f".{db_path.name}.{os.getpid()}.tmp")   # unique per process; renamed at the end
    if tmp.exists():
        tmp.unlink()
    stamp = fingerprint(records_dir)
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO meta VALUES (?, ?)", [("records_dir", str(Path(records_dir).resolve())),
                                                       ("fingerprint", stamp)])
    kernels = {r.id: r.data for r in store.of_kind("kernel")}
    baselines = {k["baseline_implementation"] for k in kernels.values()}
    for rec in store.records:
        if store.by_id.get(rec.id) is not rec:
            continue
        d = rec.data
        con.execute("INSERT INTO records VALUES (?,?,?,?,?)", (rec.id, rec.kind, d.get("status"), rec.rel, json.dumps(d)))
        getattr(_Insert, rec.kind, lambda *a: None)(con, d, rec.id in baselines, kernels)
    con.commit()
    con.close()
    tmp.replace(db_path)
    return {"records": len(store.records), "seconds": time.monotonic() - started}


class _Insert:
    @staticmethod
    def application(con, d, *_):
        con.execute("INSERT INTO applications VALUES (?,?,?,?,?,?,?)",
                    (d["id"], d["name"], d["source"]["commit"], d["language"], d["parallel_model"], d["domain"],
                     json.dumps(d)))

    @staticmethod
    def kernel(con, d, *_):
        con.execute("INSERT INTO kernels VALUES (?,?,?,?,?)",
                    (d["id"], d["name"], d["application"], d["baseline_implementation"], json.dumps(d)))

    @staticmethod
    def implementation(con, d, is_baseline, kernels):
        con.execute("INSERT INTO implementations VALUES (?,?,?,?,?,?,?)",
                    (d["id"], d["name"], d["kernel"], d["function"], d["origin"]["kind"], int(is_baseline),
                     json.dumps(d)))
        for p in d["access_patterns"]:
            sem = p["semantics"]
            cols = []
            for name in SEMANTIC_FIELDS:
                cols += [_text(sem[name]["value"]), sem[name]["basis"]]
            con.execute(f"INSERT INTO access_patterns VALUES ({','.join('?' * (8 + 2 * len(SEMANTIC_FIELDS)))})",
                        (d["id"], p["id"], d["kernel"], p["expression"], p["loop"], p["update_kind"],
                         pattern_class(p), *cols, json.dumps(sem)))
            for i, s in enumerate(p["steps"]):
                a = s["array"]
                con.execute("INSERT INTO steps VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            (d["id"], p["id"], i, a["name"], a["role"], a["element_type"], a["element_bytes"],
                             a["element_count"], a["layout"], s["address_shape"], s.get("stride"),
                             s.get("index_transform")))

    @staticmethod
    def input(con, d, *_):
        con.execute("INSERT INTO inputs VALUES (?,?,?,?,?)",
                    (d["id"], d["name"], (d.get("generator") or {}).get("arguments"), (d.get("file") or {}).get("path"),
                     json.dumps(d)))
        for name, fact in d["properties"].items():
            con.execute("INSERT INTO input_properties VALUES (?,?,?,?)", (d["id"], name, _text(fact["value"]), fact["basis"]))

    @staticmethod
    def machine(con, d, *_):
        from swdb.machine import llc_bytes

        con.execute("INSERT INTO machines VALUES (?,?,?,?,?,?,?,?)",
                    (d["id"], d["hostname"], d["cpu"]["model"], d["cpu"]["sockets"], d["cpu"]["cores_per_socket"],
                     llc_bytes(d), _flag(d["counters"]["hardware_counters_available"]["value"]), json.dumps(d)))

    @staticmethod
    def profile(con, d, *_):
        b = d["bottleneck"]
        check = next((p["outcome"] for p in d["parts"] if p["part"] == "correctness"), None)
        con.execute("INSERT INTO profiles VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (d["id"], d["implementation"], d["input"], d["machine"], int(d["complete"]),
                     {"complete": "passed", None: None}.get(check, "not_established"),
                     d["environment"]["started"], b["value"], b["basis"], b["memory_limit"], json.dumps(d)))
        for m in d["metrics"]:
            number = m["value"] if isinstance(m["value"], (int, float)) and not isinstance(m["value"], bool) else None
            con.execute("INSERT INTO metrics VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (d["id"], m["name"], number, json.dumps(m["value"]), m["unit"], m["basis"], m.get("threads"),
                         m.get("array"), m.get("scope"), m.get("tool")))


def pattern_class(pattern):
    """The pattern class: the address shapes of the steps, then the update kind."""
    return " > ".join(s["address_shape"] for s in pattern["steps"]) + " : " + pattern["update_kind"]


def _connect(db_path):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def sql(db_path, query):
    con = _connect(db_path)
    try:
        return [dict(row) for row in con.execute(query)]
    except sqlite3.Error as exc:
        from swdb.cli import Failure

        raise Failure(f"SQL error: {exc}") from None
    finally:
        con.close()


def _semantic_column(name):
    if name not in SEMANTIC_FIELDS:
        from swdb.cli import UsageError

        raise UsageError(f"unknown semantic field {name!r}; one of {', '.join(SEMANTIC_FIELDS)}")
    return name


def find(db_path, shapes=(), update=None, semantics=(), kernel=None):
    where, args = [], []
    for shape in shapes:
        where.append("EXISTS (SELECT 1 FROM steps s WHERE s.implementation = p.implementation "
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
    query = "SELECT * FROM access_patterns p" + (" WHERE " + " AND ".join(where) if where else "")
    con = _connect(db_path)
    try:
        rows = con.execute(query + " ORDER BY p.implementation, p.pattern", args).fetchall()
        return [_pattern_out(con, row) for row in rows]
    finally:
        con.close()


def _pattern_out(con, row):
    steps = con.execute("SELECT * FROM steps WHERE implementation = ? AND pattern = ? ORDER BY position",
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
        if con.execute("SELECT 1 FROM kernels WHERE id = ?", (kernel,)).fetchone() is None:
            return None
        found = []
        for impl in con.execute("SELECT * FROM implementations WHERE kernel = ? ORDER BY is_baseline DESC, id", (kernel,)):
            patterns = con.execute("SELECT * FROM access_patterns WHERE implementation = ?", (impl["id"],)).fetchall()
            failing = []
            for name, value in requirements:
                column = _semantic_column(name)
                for p in patterns:
                    if p[f"{column}_basis"] == "unknown" or json.loads(p[column]) != value:
                        failing.append(f"{p['pattern']}.{name} is {json.loads(p[column])!r} ({p[f'{column}_basis']})")
            if not failing:
                found.append({"implementation": impl["id"], "name": impl["name"], "function": impl["function"],
                              "baseline": bool(impl["is_baseline"]), "origin": impl["origin"],
                              "meets": {name: value for name, value in requirements}})
        return found
    finally:
        con.close()
