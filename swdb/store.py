"""The record store: the only module that reads record files.

It loads every record under a records folder, indexes them by ID, and resolves
references between them. Records refer to each other by ID, never by file path.
"""

from dataclasses import dataclass

import yaml

from swdb import yamlio
from swdb.problems import Problem

PLURAL = {"application": "applications", "kernel": "kernels", "implementation": "implementations",
          "input": "inputs", "machine": "machines", "profile": "profiles",
          "strategy": "strategies", "intrinsic": "intrinsics"}


@dataclass
class Record:
    rel: str     # path relative to the records folder
    data: dict

    @property
    def kind(self):
        return self.data.get("kind")

    @property
    def id(self):
        return self.data.get("id")


class Store:
    def __init__(self, records_dir):
        self.dir = records_dir
        self.records = []      # every file that parsed to a mapping
        self.problems = []     # files that could not be read as records
        self.by_id = {}        # first record seen for each ID
        for path, rel in record_files(records_dir):
            self._load(path, rel)

    def _load(self, path, rel):
        try:
            data = yamlio.load(path)
        except yaml.YAMLError as exc:
            self.problems.append(Problem(rel, "-", f"not valid YAML: {' '.join(str(exc).split())}"))
            return
        if not isinstance(data, dict):
            self.problems.append(Problem(rel, "-", "a record must be a YAML mapping"))
            return
        self.add(Record(rel, data))

    def add(self, record):
        self.records.append(record)
        if isinstance(record.id, str) and record.id not in self.by_id:
            self.by_id[record.id] = record

    def replace(self, rel, data):
        """Swap in new data for the record read from `rel` (used to validate before writing)."""
        for i, record in enumerate(self.records):
            if record.rel == rel:
                self.records[i] = Record(rel, data)
                self.by_id = {}
                for rec in self.records:
                    if isinstance(rec.id, str) and rec.id not in self.by_id:
                        self.by_id[rec.id] = rec
                return
        raise KeyError(rel)

    def path_of(self, record_id):
        record = self.by_id.get(record_id)
        return None if record is None else record.rel

    def get(self, record_id, kind=None):
        record = self.by_id.get(record_id)
        if record is None or (kind is not None and record.kind != kind):
            return None
        return record.data

    def of_kind(self, kind):
        return [r for r in self.records if r.kind == kind and self.by_id.get(r.id) is r]

    def index(self):
        return {rid: rec.kind for rid, rec in self.by_id.items()}

    # --- references that need more than one hop -------------------------------------

    def application_of(self, data):
        """The application record behind a kernel, implementation, or profile (or None)."""
        kind = data.get("kind")
        if kind == "application":
            return data
        if kind == "kernel":
            return self.get(data.get("application"), "application")
        if kind == "implementation":
            kernel = self.get(data.get("kernel"), "kernel")
            return self.application_of(kernel) if kernel else None
        if kind == "profile":
            impl = self.get(data.get("implementation"), "implementation")
            return self.application_of(impl) if impl else None
        return None


def canonical_path(kind, record_id):
    """Where `swdb add` writes a record: <kind plural>/<id>.yaml under the records folder."""
    return f"{PLURAL[kind]}/{record_id}.yaml"


def record_files(records_dir):
    """Every .yaml/.yml file under records_dir, skipping hidden files and folders."""
    for path in sorted(records_dir.rglob("*")):
        rel = path.relative_to(records_dir)
        if path.is_file() and path.suffix in {".yaml", ".yml"} and not any(p.startswith(".") for p in rel.parts):
            yield path, rel.as_posix()
