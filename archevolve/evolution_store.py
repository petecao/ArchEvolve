"""Content-addressed offline experiment memory; SQLite supplies durable transactions."""

import hashlib
import json
from pathlib import Path
import sqlite3


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class EvolutionStore:
    """Single-coordinator store. Hashes detect changes, not truth or authorship."""

    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS objects (hash TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY, kind TEXT NOT NULL,
                object_hash TEXT NOT NULL REFERENCES objects(hash));
        ''')
        self.db.commit()

    def put(self, value):
        key = digest(value)
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO objects VALUES (?, ?)", (key, canonical(value)))
        return key

    def get(self, key):
        row = self.db.execute("SELECT payload FROM objects WHERE hash=?", (key,)).fetchone()
        if row is None:
            raise ValueError(f"Unknown memory reference: {key}")
        value = json.loads(row[0])
        if digest(value) != key:
            raise ValueError(f"Corrupt memory object: {key}")
        return value

    def append(self, kind, value):
        key = digest(value)
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO objects VALUES (?, ?)", (key, canonical(value)))
            self.db.execute("INSERT INTO events(kind, object_hash) VALUES (?, ?)", (kind, key))
        return key

    def events(self, kind=None):
        sql, args = "SELECT kind, object_hash FROM events", ()
        if kind is not None:
            sql += " WHERE kind=?"
            args = (kind,)
        return [{"kind": k, "ref": h, "record": self.get(h)}
                for k, h in self.db.execute(sql + " ORDER BY seq", args)]

    def export(self):
        return {"format": "archevolve-offline-memory-1", "events": self.events(),
                "objects": {h: self.get(h) for (h,) in self.db.execute("SELECT hash FROM objects ORDER BY hash")}}

    def close(self):
        self.db.close()
