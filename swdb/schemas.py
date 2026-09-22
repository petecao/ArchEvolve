"""Schema loading: envelope + kind schema, merged, with vocabularies expanded.

Every record is checked against one merged schema: the envelope's fields plus its
kind's fields. Cross-file `$ref` is avoided on purpose, because resolving it differs
between jsonschema 4.10 (mbit10's system Python) and newer releases.
"""

import copy
import json

from jsonschema import Draft202012Validator


class UnknownVocabulary(ValueError):
    pass


class SchemaSet:
    def __init__(self, schema_dir, vocabs):
        self._dir = schema_dir
        self._vocabs = vocabs
        self._envelope = _read(schema_dir / "envelope.schema.json")
        self._validators = {}

    def for_kind(self, kind):
        """Return a validator for records of this kind, or None if the kind has no schema yet."""
        if kind not in self._validators:
            path = self._dir / f"{kind}.schema.json"
            if not path.exists():
                self._validators[kind] = None
            else:
                schema = _expand_vocab(_merge(self._envelope, _read(path)), self._vocabs)
                Draft202012Validator.check_schema(schema)
                self._validators[kind] = Draft202012Validator(schema)
        return self._validators[kind]


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _merge(envelope, kind_schema):
    """Envelope and kind fields in one object schema; a field in both must satisfy both."""
    merged = copy.deepcopy(kind_schema)
    properties = copy.deepcopy(envelope["properties"])
    for name, sub in kind_schema.get("properties", {}).items():
        properties[name] = {"allOf": [properties[name], sub]} if name in properties else sub
    merged["properties"] = properties
    merged["required"] = list(dict.fromkeys(envelope.get("required", []) + kind_schema.get("required", [])))
    merged["allOf"] = envelope.get("allOf", []) + kind_schema.get("allOf", [])
    merged["additionalProperties"] = False
    merged["type"] = "object"
    return merged


def _expand_vocab(node, vocabs):
    """Turn every {"x-vocab": name} into an enum of that vocabulary's current values."""
    if isinstance(node, dict):
        node = {key: _expand_vocab(value, vocabs) for key, value in node.items()}
        name = node.get("x-vocab")
        if name is not None:
            if name not in vocabs:
                raise UnknownVocabulary(f"schema refers to vocabulary {name!r}, which does not exist")
            node["enum"] = list(vocabs[name])
        return node
    if isinstance(node, list):
        return [_expand_vocab(item, vocabs) for item in node]
    return node
