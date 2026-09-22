"""`swdb validate`: check every record file against its kind's schema and the vocabularies."""

import re
from dataclasses import dataclass, field

import yaml

from swdb import paths, vocab, yamlio
from swdb.problems import Problem
from swdb.schemas import SchemaSet

_REQUIRED = re.compile(r"^'(.+)' is a required property$")


@dataclass
class Result:
    count: int = 0
    problems: list = field(default_factory=list)


def record_files(records_dir):
    """Every .yaml/.yml file under records_dir, skipping hidden files and folders."""
    for path in sorted(records_dir.rglob("*")):
        rel = path.relative_to(records_dir)
        if path.is_file() and path.suffix in {".yaml", ".yml"} and not any(p.startswith(".") for p in rel.parts):
            yield path, rel.as_posix()


def validate_records(records_dir):
    vocabs, problems = vocab.load_all(paths.VOCAB)
    result = Result(problems=list(problems))
    schemas = SchemaSet(paths.SCHEMAS, vocabs)
    for path, rel in record_files(records_dir):
        result.count += 1
        result.problems.extend(sorted(_check_file(path, rel, schemas, vocabs)))
    return result


def _check_file(path, rel, schemas, vocabs):
    try:
        data = yamlio.load(path)
    except yaml.YAMLError as exc:
        return [Problem(rel, "-", f"not valid YAML: {' '.join(str(exc).split())}")]
    if not isinstance(data, dict):
        return [Problem(rel, "-", "a record must be a YAML mapping")]
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
        return [Problem(rel, _join(where, name), schema.get("x-reason", "required field is missing"))]
    if error.validator == "additionalProperties" and isinstance(error.instance, dict):
        known = set(schema.get("properties", {}))
        return [
            Problem(rel, _join(where, key), "unknown key; put experimental fields under `extensions`")
            for key in sorted(set(error.instance) - known)
        ]
    reason = schema.get("x-reason")
    if reason is None and error.validator == "enum" and "x-vocab" in schema:
        reason = f"{error.instance!r} is not in vocabulary {schema['x-vocab']}"
    return [Problem(rel, where or "-", reason or error.message)]


def _dotted(path):
    text = ""
    for part in path:
        text += f"[{part}]" if isinstance(part, int) else (f".{part}" if text else str(part))
    return text


def _join(where, name):
    return f"{where}.{name}" if where else name
