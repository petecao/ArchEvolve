"""The format document covers every field the schemas define. Created 2026-09-22."""

import json

from conftest import REPO

DOC = REPO / "docs" / "format-v0.2.md"


def schema_fields():
    names = {}

    def walk(node, where):
        if not isinstance(node, dict):
            return
        for name, sub in node.get("properties", {}).items():
            names.setdefault(name, where)
            walk(sub, f"{where}.{name}")
        for key in ("items", "additionalProperties", "if", "then", "not"):
            walk(node.get(key), where)
        for key in ("allOf", "anyOf", "oneOf"):
            for sub in node.get(key, []):
                walk(sub, where)
        for name, sub in node.get("$defs", {}).items():
            walk(sub, f"$defs.{name}")

    for path in sorted((REPO / "schemas").glob("*.schema.json")):
        walk(json.loads(path.read_text()), path.name.split(".")[0])
    return names


def test_every_schema_field_is_in_the_format_document():
    doc = DOC.read_text()
    missing = sorted(f"{where}.{name}" for name, where in schema_fields().items() if f"`{name}`" not in doc)
    assert not missing, f"fields not documented in {DOC.name}: {missing}"


def test_the_check_would_catch_a_missing_field(tmp_path):
    # negative control: the same check on a document without one field fails
    doc = DOC.read_text().replace("`undirected_alias`", "undirected alias")
    missing = [name for name in schema_fields() if f"`{name}`" not in doc]
    assert missing == ["undirected_alias"]


def test_every_vocabulary_a_schema_uses_is_named_in_the_document():
    doc = DOC.read_text()
    used = set()

    def walk(node):
        if isinstance(node, dict):
            if "x-vocab" in node:
                used.add(node["x-vocab"])
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for path in (REPO / "schemas").glob("*.schema.json"):
        walk(json.loads(path.read_text()))
    assert sorted(v for v in used if f"`{v}`" not in doc and v not in doc) == []


def test_document_states_the_versioning_rule():
    doc = DOC.read_text()
    for phrase in ("**Minor**", "**Major**", "**Deprecation**", "deprecated_by"):
        assert phrase in doc
