"""A read-only `Store` over the checkout's real records that parses a record only when asked.
Created 2026-10-13 ET (suite closure).

`Store(REPO / "records")` parses the whole ~1.3 GB store (minutes per call, and gigabytes of
memory) even when a test reads three records. `real_store()` answers `get`, `path_of` and
`of_kind` from the per-process ID index (`conftest._catalog_index`) and parses only the files
asked for, the same way `Store` does. Any whole-store use (`records`, `by_id` iteration,
`index()`) falls back to loading everything, so results never differ from `Store`.
Each call returns a fresh store, so a test's mutations of returned data never reach another test.
"""

from pathlib import Path

from conftest import REPO, _catalog_index
from swdb.store import PLURAL, Store


class _LazyIds(dict):
    """`Store.by_id` that loads one record on first lookup; iteration loads all."""

    def __init__(self, store):
        super().__init__()
        self._store = store

    def _ensure(self, rid):
        if not dict.__contains__(self, rid) and isinstance(rid, str):
            self._store._load_id(rid)

    def get(self, rid, default=None):
        self._ensure(rid)
        return dict.get(self, rid, default)

    def __getitem__(self, rid):
        self._ensure(rid)
        return dict.__getitem__(self, rid)

    def __contains__(self, rid):
        self._ensure(rid)
        return dict.__contains__(self, rid)

    def _all(self):
        self._store._load_all()

    def __iter__(self):
        self._all()
        return dict.__iter__(self)

    def __len__(self):
        self._all()
        return dict.__len__(self)

    def keys(self):
        self._all()
        return dict.keys(self)

    def values(self):
        self._all()
        return dict.values(self)

    def items(self):
        self._all()
        return dict.items(self)


class RealStore(Store):
    """`Store(REPO / "records")` with on-demand parsing (see module docstring)."""

    def __init__(self):
        self.dir = REPO / "records"
        self.problems = []
        self._records = []
        self._loaded = set()
        self._complete = False
        self.by_id = _LazyIds(self)

    def _load_rel(self, rel):
        rel = Path(rel).as_posix()
        if rel not in self._loaded:
            self._loaded.add(rel)
            self._load(self.dir / rel, rel)

    def _load_id(self, rid):
        rel = _catalog_index().get(rid)
        if rel is not None:
            self._load_rel(rel)

    def _load_all(self):
        if not self._complete:
            self._complete = True
            for rel in sorted(Path(r).as_posix() for r in _catalog_index().values()):
                self._load_rel(rel)

    def add(self, record):
        self._records.append(record)
        if isinstance(record.id, str) and not dict.__contains__(self.by_id, record.id):
            dict.__setitem__(self.by_id, record.id, record)

    @property
    def records(self):
        self._load_all()
        return self._records

    def of_kind(self, kind):
        folder = PLURAL.get(kind)
        if folder is None:
            return super().of_kind(kind)
        for rid, rel in _catalog_index().items():
            if Path(rel).parts[0] == folder:
                self._load_rel(rel)
        return [r for r in self._records if r.kind == kind and dict.get(self.by_id, r.id) is r]


def real_store():
    """A fresh read-only lazy `Store` over the checkout's records."""
    return RealStore()


def lazy_store_seam(monkeypatch, module):
    """Make `module.Store(path)` lazy when `path` is the checkout's records folder.

    For script readers that require that exact folder and then call `Store(...)` on it; any
    other folder still gets a plain `Store`. The records read are unchanged."""
    real = (REPO / "records").resolve()
    monkeypatch.setattr(module, "Store",
                        lambda path, **kw: real_store() if not kw and Path(path).resolve() == real else Store(path, **kw))
