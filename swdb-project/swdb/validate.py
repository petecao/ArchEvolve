"""`swdb validate`: check every record against its kind's schema, then the rules a schema
cannot express (references, unique IDs, formulas, code excerpts; see rules.py)."""

import re
from dataclasses import dataclass, field

from swdb import paths, rules, vocab
from swdb.problems import Problem
from swdb.schemas import SchemaSet
from swdb.store import Store

_REQUIRED = re.compile(r"^'(.+)' is a required property$")


@dataclass
class Result:
    count: int = 0
    problems: list = field(default_factory=list)
    store: Store = None
    vocabs: dict = None


def validate_records(records_dir, extra=None, replace=None, library_root=None):
    """Validate the records folder as it would be after writing `extra` (new store.Record
    objects) and `replace` ({relative path: new data} for records already on disk)."""
    result = _validate_store(Store(records_dir), extra=extra, replace=replace)
    from swdb.library import Library, default_root
    root = library_root or default_root(records_dir)
    if root.exists():
        result.problems.extend(Library(root, result.store).validate())
    from swdb.campaign import validate_campaign_dir   # ticket 52: campaigns/extensa/*.yaml
    result.problems.extend(validate_campaign_dir(records_dir))
    return result


def _validate_store(store, extra=None, replace=None):
    """Validate one freshly loaded store, applying the proposed changes in memory.

    The writer calls this only with the store it loaded under its current lock;
    this is not a cache and must not be reused across independent writes.
    Updated: 2026-09-25.
    """
    vocabs, problems = vocab.load_all(paths.VOCAB)
    for rel, data in (replace or {}).items():
        store.replace(rel, data)
    for record in extra or []:
        store.add(record)
    result = Result(count=len(store.records) + len(store.problems), problems=list(problems) + list(store.problems),
                    store=store)
    schemas = SchemaSet(paths.SCHEMAS, vocabs, store.index())
    passed = []
    seen = {}
    for record in store.records:
        found = sorted(_check_record(record, schemas, vocabs))
        rid = record.id
        if isinstance(rid, str):
            if rid in seen:
                found.append(Problem(record.rel, "id", f"duplicate ID {rid!r}; also used by {seen[rid]}"))
            else:
                seen[rid] = record.rel
        result.problems.extend(found)
        if not found:
            passed.append(record)
    result.vocabs = vocabs
    context = rules.Context(store, vocabs, store.dir, paths.HOME, valid={r.rel for r in passed})
    for record in passed:
        result.problems.extend(sorted(rules.check(record, context)))
    return result


def _check_record(record, schemas, vocabs):
    data, rel = record.data, record.rel
    kind = data.get("kind")
    if not isinstance(kind, str):
        return [Problem(rel, "kind", "required field is missing or not text")]
    if kind not in vocabs.get("record_kinds", []):
        return [Problem(rel, "kind", f"{kind!r} is not in vocabulary record_kinds")]
    validator = schemas.for_kind(kind)
    if validator is None:
        return [Problem(rel, "kind", f"no schema for kind {kind!r} yet")]
    return [problem for error in validator.iter_errors(data) for problem in _describe(rel, error)]


def _describe(rel, error):
    """Translate one jsonschema error into problems that name the exact field."""
    where = _dotted(error.absolute_path)
    schema = error.schema if isinstance(error.schema, dict) else {}
    if error.validator == "required":
        match = _REQUIRED.match(error.message)
        name = match.group(1) if match else "?"
        reason = schema.get("x-required-reasons", {}).get(name) or schema.get("x-reason") or "required field is missing"
        return [Problem(rel, _join(where, name), reason)]
    if error.validator == "additionalProperties" and isinstance(error.instance, dict):
        known = set(schema.get("properties", {}))
        return [
            Problem(rel, _join(where, key), "unknown key; put experimental fields under `extensions`")
            for key in sorted(set(error.instance) - known)
        ]
    reason = schema.get("x-reason")
    if reason is None and error.validator == "enum" and "x-vocab" in schema:
        reason = f"{error.instance!r} is not in vocabulary {schema['x-vocab']}"
    if reason is None and error.validator == "x-ref":
        reason = error.message
    return [Problem(rel, where or "-", reason or error.message)]


def _dotted(path):
    text = ""
    for part in path:
        text += f"[{part}]" if isinstance(part, int) else (f".{part}" if text else str(part))
    return text


def _join(where, name):
    return f"{where}.{name}" if where else name
