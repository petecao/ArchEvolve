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

from swdb.store import Record, Store, record_files
from swdb.strategy import SEMANTIC_FIELDS, entry, pattern_outcome

SCHEMA = f"""
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, status TEXT, path TEXT NOT NULL, json TEXT NOT NULL);
CREATE TABLE applications (id TEXT PRIMARY KEY, name TEXT, commit_hash TEXT, language TEXT, parallel_model TEXT,
    domain TEXT, json TEXT NOT NULL);
CREATE TABLE kernels (id TEXT PRIMARY KEY, name TEXT, application TEXT, baseline_implementation TEXT,
    json TEXT NOT NULL);
CREATE TABLE implementations (id TEXT PRIMARY KEY, name TEXT, kernel TEXT, function TEXT, origin TEXT,
    is_baseline INTEGER NOT NULL, json TEXT NOT NULL);
CREATE TABLE implementation_contexts (implementation TEXT PRIMARY KEY, application TEXT NOT NULL,
    source_ancestor TEXT, source_baseline TEXT, comparison_baseline TEXT, json TEXT NOT NULL);
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
CREATE TABLE machine_flags (machine TEXT NOT NULL, flag TEXT NOT NULL, PRIMARY KEY (machine, flag));
CREATE TABLE intrinsics (id TEXT PRIMARY KEY, name TEXT, isa_family TEXT, isa_extensions TEXT, header TEXT,
    memory_kind TEXT, address_shape TEXT, element_bits INTEGER, lanes INTEGER, json TEXT NOT NULL);
CREATE TABLE strategies (id TEXT PRIMARY KEY, name TEXT, target TEXT, json TEXT NOT NULL);
CREATE TABLE strategy_effects (strategy TEXT NOT NULL, position INTEGER NOT NULL, kind TEXT NOT NULL, json TEXT NOT NULL,
    PRIMARY KEY (strategy, position));
CREATE TABLE strategy_intrinsics (strategy TEXT NOT NULL, intrinsic TEXT NOT NULL, PRIMARY KEY (strategy, intrinsic));
CREATE TABLE applied_strategies (implementation TEXT NOT NULL, position INTEGER NOT NULL, strategy TEXT NOT NULL,
    target TEXT NOT NULL, parameters_json TEXT NOT NULL, PRIMARY KEY (implementation, position));
CREATE TABLE implementation_intrinsics (implementation TEXT NOT NULL, intrinsic TEXT NOT NULL,
    PRIMARY KEY (implementation, intrinsic));
CREATE TABLE intrinsic_extensions (intrinsic TEXT NOT NULL, extension TEXT NOT NULL, PRIMARY KEY (intrinsic, extension));
CREATE TABLE library_entries (id TEXT PRIMARY KEY, kind TEXT NOT NULL, path TEXT NOT NULL, content_sha256 TEXT NOT NULL,
    tier TEXT, status TEXT, derived_from TEXT, json TEXT NOT NULL);
CREATE TABLE library_dependencies (entry TEXT NOT NULL, dependency TEXT NOT NULL, content_sha256 TEXT NOT NULL,
    PRIMARY KEY (entry, dependency));
CREATE TABLE library_clauses (entry TEXT NOT NULL, clause TEXT NOT NULL, role TEXT, discharge_mode TEXT,
    negative_control TEXT, statement TEXT, PRIMARY KEY (entry, clause));
CREATE TABLE statements (implementation TEXT NOT NULL, statement TEXT NOT NULL, function TEXT, path TEXT,
    first_line INTEGER, last_line INTEGER, revision TEXT, code TEXT, basis TEXT, depends_on TEXT,
    agent_claims INTEGER NOT NULL, json TEXT NOT NULL, PRIMARY KEY (implementation, statement));
CREATE TABLE statement_steps (implementation TEXT NOT NULL, statement TEXT NOT NULL, pattern TEXT NOT NULL,
    step INTEGER NOT NULL, PRIMARY KEY (implementation, statement, pattern, step));
"""


# identifies the code that builds the file: any change to the swdb package (tables, how rows
# are filled, which records load) makes older files stale; a rebuild takes about a second
BUILDER = hashlib.sha256(b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py")))).hexdigest()

def default_path(records_dir):
    """build/swdb.sqlite next to a folder named `records` (the repo's), otherwise
    build/swdb-<folder name>.sqlite, so sibling records folders get their own files."""
    records_dir = Path(records_dir).resolve()
    name = "swdb.sqlite" if records_dir.name == "records" else f"swdb-{records_dir.name}.sqlite"
    return records_dir.parent / "build" / name


def library_dir(records_dir):
    """The typed library a records folder uses (the repository's beside `records`)."""
    from swdb.library import default_root
    return Path(default_root(Path(records_dir))).resolve()


def library_files(records_dir):
    """Every regular file of that library folder (YAML entries and pinned code), sorted."""
    root = library_dir(records_dir)
    if not root.is_dir():
        return []
    return [(path, path.relative_to(root).as_posix()) for path in sorted(root.rglob("*"))
            if path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts]


def fingerprint(records_dir):
    """Identifies the exact set of record files and, since ticket 46 (2026-10-03 ET), of the
    typed library folder's files: path, size, and modification time of each."""
    digest = hashlib.sha256()
    for path, rel in record_files(Path(records_dir)):
        info = path.stat()
        digest.update(f"{rel}\0{info.st_size}\0{info.st_mtime_ns}\n".encode())
    for path, rel in library_files(records_dir):
        info = path.stat()
        digest.update(f"library/{rel}\0{info.st_size}\0{info.st_mtime_ns}\n".encode())
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
    """True unless the database was built from this very folder in its current state, by the
    same database code (a newer swdb may add tables or fill them differently)."""
    db_path = Path(db_path)
    if not db_path.exists():
        return True
    meta = _meta(db_path)
    return (meta.get("records_dir") != str(Path(records_dir).resolve())
            or meta.get("fingerprint") != fingerprint(records_dir)
            or meta.get("builder") != BUILDER)


def _flag(value):
    """A boolean fact as 1/0, and NULL when unknown (unknown is never false)."""
    return None if value is None else int(bool(value))


def _text(value):
    """Semantic and property values as text: JSON for everything, so true/false/null stay distinct."""
    return json.dumps(value)


def build(records_dir, db_path):
    started = time.monotonic()
    # fingerprint first: a record written while the store loads makes the stamp older than
    # the files, so the next query rebuilds instead of trusting a stale database
    stamp = fingerprint(records_dir)
    store = Store(Path(records_dir))
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = db_path.with_name(f".{db_path.name}.{os.getpid()}.tmp")   # unique per process; renamed at the end
    if tmp.exists():
        tmp.unlink()
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO meta VALUES (?, ?)", [("records_dir", str(Path(records_dir).resolve())),
                                                       ("library_dir", str(library_dir(records_dir))),
                                                       ("fingerprint", stamp), ("builder", BUILDER)])
    kernels = {r.id: r.data for r in store.of_kind("kernel")}
    baselines = {k["baseline_implementation"] for k in kernels.values()}
    for rec in store.records:
        if store.by_id.get(rec.id) is not rec:
            continue
        d = rec.data
        con.execute("INSERT INTO records VALUES (?,?,?,?,?)", (rec.id, rec.kind, d.get("status"), rec.rel, json.dumps(d)))
        getattr(_Insert, rec.kind, lambda *a: None)(con, d, rec.id in baselines, kernels)
        if rec.kind == "implementation":
            context = store.source_context(d)
            con.execute("INSERT INTO implementation_contexts VALUES (?,?,?,?,?,?)",
                        (rec.id, context["application"], context["source_ancestor"], context["source_baseline"],
                         context["comparison_baseline"], json.dumps(context)))
    _library(con, records_dir, store)
    con.commit()
    con.close()
    tmp.replace(db_path)
    return {"records": len(store.records), "seconds": time.monotonic() - started}


def _library(con, records_dir, store):
    """Ticket 46 (2026-10-03 ET): typed library entries, their dependency pins and clauses.

    Tier and status are derived from the records exactly as `swdb.library` derives them;
    an entry whose state cannot be derived (for example an invalid library) gets NULL."""
    from swdb.library import Library, derived_from
    root = library_dir(records_dir)
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
        con.execute("INSERT INTO library_entries VALUES (?,?,?,?,?,?,?,?)",
                    (entry_id, data.get("kind"), library.files[entry_id].relative_to(root).as_posix(),
                     library.content_sha256(entry_id), state["tier"], state["status"], derived_from(data),
                     json.dumps(data)))
        con.executemany("INSERT INTO library_dependencies VALUES (?,?,?)",
                        [(entry_id, pin["id"], pin["content_sha256"]) for pin in pins])
        clauses = data.get("clauses") if isinstance(data.get("clauses"), list) else []
        con.executemany("INSERT OR IGNORE INTO library_clauses VALUES (?,?,?,?,?,?)",
                        [(entry_id, c.get("id"), c.get("role"), c.get("discharge_mode"),
                          (c.get("negative_control") or {}).get("id"), c.get("statement"))
                         for c in clauses if isinstance(c, dict) and isinstance(c.get("id"), str)])


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
        con.executemany("INSERT INTO implementation_intrinsics VALUES (?,?)",
                        [(d["id"], i) for i in d.get("uses_intrinsics", [])])
        con.executemany("INSERT INTO applied_strategies VALUES (?,?,?,?,?)",
                        [(d["id"], i, a["strategy"], a["target"], json.dumps(a["parameters"]))
                         for i, a in enumerate(d.get("applies", []))])
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
        # Ticket 46 (2026-10-03 ET): the statements index (statement annotations, ticket 35).
        statements = (d.get("extensions") or {}).get("statements") or {}
        for row in statements.get("annotations", []):
            source = row.get("source") or {}
            lines = source.get("lines") or [None, None]
            con.execute("INSERT INTO statements VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (d["id"], row["id"], statements.get("function"), source.get("path"), lines[0], lines[-1],
                         source.get("revision"), row.get("code"), row.get("basis"),
                         json.dumps(row.get("depends_on", [])), len(row.get("agent_claims", [])), json.dumps(row)))
            con.executemany("INSERT OR IGNORE INTO statement_steps VALUES (?,?,?,?)",
                            [(d["id"], row["id"], step["pattern"], step["step"])
                             for step in row.get("access_pattern_steps", [])])

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
        con.executemany("INSERT INTO machine_flags VALUES (?,?)", [(d["id"], f) for f in d["cpu"].get("flags", [])])

    @staticmethod
    def strategy(con, d, *_):
        con.execute("INSERT INTO strategies VALUES (?,?,?,?)", (d["id"], d["name"], d["target"], json.dumps(d)))
        con.executemany("INSERT INTO strategy_effects VALUES (?,?,?,?)",
                        [(d["id"], i, e["kind"], json.dumps(e)) for i, e in enumerate(d["effect"])])
        con.executemany("INSERT INTO strategy_intrinsics VALUES (?,?)", [(d["id"], i) for i in d.get("common_intrinsics", [])])

    @staticmethod
    def intrinsic(con, d, *_):
        con.execute("INSERT INTO intrinsics VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (d["id"], d["name"], d.get("isa_family"), json.dumps(d.get("isa_extensions", [])), d.get("header"),
                     d["memory_kind"], d["address_shape"], d["element_bits"], d["lanes"], json.dumps(d)))
        con.executemany("INSERT INTO intrinsic_extensions VALUES (?,?)", [(d["id"], e) for e in d.get("isa_extensions", [])])

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
    rows = sql(selected, "SELECT path, json FROM records ORDER BY path")
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
        return _meeting(con, kernel, requirements)
    finally:
        con.close()


def _meeting(con, kernel, requirements):
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
            context = json.loads(con.execute("SELECT json FROM implementation_contexts WHERE implementation = ?",
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
    row = con.execute("SELECT json FROM strategies WHERE id = ?", (strategy_id,)).fetchone()
    if row is None:
        raise _failure(f"strategy {strategy_id!r} does not exist")
    data = json.loads(row["json"])
    if data["target"] != target:
        raise _usage(f"strategy {strategy_id!r} targets {data['target']}, not {target}")
    return data


def _strategies(con, target):
    return [json.loads(r["json"]) for r in con.execute("SELECT json FROM strategies WHERE target = ? ORDER BY id", (target,))]


def _pattern_facts(con, row):
    steps = con.execute("SELECT address_shape FROM steps WHERE implementation = ? AND pattern = ? ORDER BY position",
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
        row = con.execute("SELECT * FROM access_patterns WHERE implementation = ? AND pattern = ?", (impl, pattern)).fetchone()
        if row is None:
            raise _failure(f"access pattern {target!r} does not exist")
        facts = _pattern_facts(con, row)
        return [entry(s, *pattern_outcome(s, facts)) for s in _strategies(con, "access_pattern")]
    finally:
        con.close()


def _implementation(con, impl_id):
    row = con.execute("SELECT json FROM implementations WHERE id = ?", (impl_id,)).fetchone()
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
        rows = con.execute(f"SELECT * FROM access_patterns WHERE implementation = ? AND loop IN "
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
    rows = con.execute("SELECT id, input, machine FROM profiles WHERE implementation = ? AND complete = 1 "
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
        if con.execute("SELECT 1 FROM strategies WHERE id = ?", (strategy_id,)).fetchone() is None:
            raise _failure(f"strategy {strategy_id!r} does not exist")
        newest = {}   # implementation -> {(input, machine): profile}, each read once
        found = []
        for impl_id in [a["implementation"] for a in allowed]:
            entries = [{"strategy": r["strategy"], "target": r["target"], "parameters": json.loads(r["parameters_json"]),
                        "position": r["position"]}
                       for r in con.execute("SELECT * FROM applied_strategies WHERE implementation = ? AND strategy = ? "
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
        records = {row["id"]: json.loads(row["json"]) for row in con.execute("SELECT id, json FROM records")}
        return compare_records(records, implementation, baseline, profile, baseline_profile, protocol)
    finally:
        con.close()
