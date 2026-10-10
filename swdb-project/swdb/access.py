"""Record and generated-index access boundary (ADR 0014).

Created: 2026-10-06 ET. Store and query modules use this interface instead of
opening record files or SQLite themselves. This research-database implementation
keeps YAML authoritative; a future main-database adapter belongs at this boundary.
Index creation writes only SWDB's generated index, never a main-database file.
"""

import hashlib
import json
import os
import sqlite3
from pathlib import Path

from swdb import yamlio


def read_record_bytes(path):
    """Read the exact source bytes used for record export and content hashes."""
    return Path(path).read_bytes()


def record_hash(path):
    """The SHA-256 of a record's exact source bytes, without YAML normalization."""
    return hashlib.sha256(read_record_bytes(path)).hexdigest()


def open_index(db_path):
    """Open an existing generated index read only; a missing index stays missing.

    URI encoding preserves caller-selected filenames containing ?, #, or %.
    The caller owns the connection and must close it after its query snapshot.
    """
    con = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def create_index(db_path):
    """Open the builder's temporary generated index for writing (research DB only)."""
    return sqlite3.connect(Path(db_path))


def query(db_path, statement, parameters=()):
    """Read one SQL result as dictionaries; always close its index connection."""
    con = open_index(db_path)
    try:
        return [dict(row) for row in con.execute(statement, parameters)]
    finally:
        con.close()


# Per-process parse cache (2026-09-27 ET). A long-lived writer such as the paired
# native collector persists several times per trial, and every persist reloads
# the whole folder. Unchanged files are served from their canonical JSON text,
# keyed by the file's inode, size, and modification/change times observed both
# before and after parsing. Callers always receive fresh objects. Records that
# do not survive a JSON round trip unchanged are never cached.
_PARSED = {}
_PARSED_LIMIT = 256 * 1024**2
_parsed_bytes = 0


def _stamp(path):
    st = os.stat(path)
    return st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns


def read_record(path):
    """Parse one record, returning fresh data even when its unchanged bytes are cached."""
    global _parsed_bytes
    name = os.path.abspath(path)
    before = _stamp(path)
    cached = _PARSED.get(name)
    if cached is not None and cached[0] == before:
        return json.loads(cached[1])
    # JSON's exponent-only numbers (1e-6) are not YAML 1.1 numeric scalars.
    # Preserve their numeric meaning for canonical receipt hashes.
    data = json.loads(read_record_bytes(path)) if Path(path).suffix.lower() == '.json' else yamlio.load(path)
    try:
        text = json.dumps(data, allow_nan=False)
        cacheable = json.loads(text) == data and _stamp(path) == before
    except (TypeError, ValueError, RecursionError):
        cacheable = False
    if cacheable:
        if _parsed_bytes + len(text) > _PARSED_LIMIT:
            _PARSED.clear(); _parsed_bytes = 0
        previous = _PARSED.pop(name, None)
        if previous is not None:
            _parsed_bytes -= len(previous[1])
        _PARSED[name] = (before, text); _parsed_bytes += len(text)
    return data


def record_files(records_dir):
    """Every .yaml/.yml file under records_dir, skipping hidden files and folders."""
    for path in sorted(records_dir.rglob("*")):
        rel = path.relative_to(records_dir)
        if path.is_file() and path.suffix in {".yaml", ".yml"} and not any(p.startswith(".") for p in rel.parts):
            yield path, rel.as_posix()
