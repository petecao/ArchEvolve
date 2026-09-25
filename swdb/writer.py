"""The record writer: `swdb add`, and the profiler's write-back.

Every write validates the whole records folder as it would be afterwards and writes
nothing unless that passes. New records go to their canonical place, derived from kind
and ID (`<kind plural>/<id>.yaml`). Records from agents are marked draft and carry an
`agent_run` provenance entry until a person reviews them.
"""

import contextlib
import datetime
import fcntl
from pathlib import Path

import yaml

from swdb import yamlio
from swdb.cli import Failure
from swdb.store import PLURAL, Record, Store, canonical_path
from swdb.validate import validate_records


def today():
    """Today's date in Eastern Time (the repo's date convention)."""
    try:
        from zoneinfo import ZoneInfo

        return datetime.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    except Exception:   # no tz database: fall back to UTC-4, the EDT offset
        return (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=4)).date().isoformat()


def mark_agent(data, agent_name):
    data["status"] = "draft"
    provenance = data.setdefault("provenance", [])
    if not isinstance(provenance, list):
        raise Failure("provenance must be a list")
    if not any(isinstance(p, dict) and p.get("kind") == "agent_run" for p in provenance):
        ids = {p.get("id") for p in provenance if isinstance(p, dict)}
        pid = "agent-run" if "agent-run" not in ids else f"agent-run-{len(ids)}"
        provenance.append({"id": pid, "kind": "agent_run",
                           "description": f"Added by {agent_name} through swdb add --agent on {today()}; "
                                          "draft until a person reviews it.", "uri": None})
    return data


def add(records_dir, file, agent=False, agent_name="agent"):
    try:
        data = yamlio.load(Path(file))
    except (OSError, yaml.YAMLError) as exc:
        raise Failure(f"cannot read {file}: {' '.join(str(exc).split())}") from None
    if not isinstance(data, dict) or not isinstance(data.get("kind"), str) or not isinstance(data.get("id"), str):
        raise Failure(f"{file}: a record must be a mapping with text fields kind and id")
    if data["kind"] in {"workload", "protocol"}:
        raise Failure("sealed workload/protocol records must be created through register-workload/freeze-protocol")
    if data["kind"] == "profile_package" and (data.get("completeness") != "fixture" or "package_version" in data):
        raise Failure("assembled profile packages must be created through profile-package; raw add accepts explicit fixtures only")
    if agent:
        mark_agent(data, agent_name)
    return commit(records_dir, new=[data])[0]


def commit(records_dir, new=(), replace=()):
    """Validate and write: `new` records go to their canonical place (which must be free and
    whose IDs must be unused); `replace` records overwrite the file their ID lives in.
    Returns the written paths relative to records_dir."""
    records_dir = Path(records_dir)
    with _locked(records_dir):
        return _commit(records_dir, new, replace)


@contextlib.contextmanager
def _locked(records_dir):
    """One writer at a time per records folder (two profiles may finish together)."""
    with open(records_dir / ".swdb.lock", "a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def _commit(records_dir, new, replace):
    store = Store(records_dir)
    extra, replaced, targets = [], {}, []
    for data in new:
        kind = data.get("kind")
        if kind not in PLURAL:
            raise Failure(f"unknown record kind {kind!r}")
        if store.get(data["id"]) is not None:
            raise Failure(f"ID {data['id']!r} is already used by {store.path_of(data['id'])}; nothing written")
        rel = canonical_path(kind, data["id"])
        if (records_dir / rel).exists():
            raise Failure(f"{rel} already exists; nothing written")
        extra.append(Record(rel, data))
        targets.append((rel, data))
    for data in replace:
        rel = store.path_of(data["id"])
        if rel is None:
            raise Failure(f"cannot replace {data['id']!r}: no such record")
        replaced[rel] = data
        targets.append((rel, data))
    result = validate_records(records_dir, extra=extra, replace=replaced)
    if result.problems:
        details = "\n".join(str(p) for p in result.problems)
        raise Failure(f"validation failed; nothing written:\n{details}")
    for rel, data in targets:
        path = records_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(yamlio.dumps(data), encoding="utf-8")
        tmp.replace(path)
    return [rel for rel, _ in targets]
