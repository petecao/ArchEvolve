"""Controlled vocabularies: one YAML file per term list, each value with a meaning.

Schemas refer to a vocabulary by name (`"x-vocab": "<name>"`); adding a value to the
file extends what records may say without touching any schema. A vocabulary may name
extra per-value fields under `fields:` (for example `metrics` gives each name a `unit`).
"""

import yaml

from swdb import yamlio
from swdb.problems import Problem


class Vocabs(dict):
    """{name: [values]}, plus `entries[name][value]` for each value's full entry."""

    def __init__(self):
        super().__init__()
        self.entries = {}

    def entry(self, name, value):
        return self.entries.get(name, {}).get(value)


def load_all(vocab_dir):
    """Return (Vocabs, [Problem]) for every vocabulary file in vocab_dir."""
    vocabs, problems = Vocabs(), []
    for path in sorted(vocab_dir.glob("*.yaml")):
        where = f"vocab/{path.name}"
        try:
            data = yamlio.load(path)
        except yaml.YAMLError as exc:
            problems.append(Problem(where, "-", f"not valid YAML: {_first_line(exc)}"))
            continue
        found = _check(where, path.stem, data)
        if found:
            problems.extend(found)
            continue
        vocabs[data["name"]] = [entry["value"] for entry in data["values"]]
        vocabs.entries[data["name"]] = {entry["value"]: entry for entry in data["values"]}
    return vocabs, problems


def _check(where, stem, data):
    if not isinstance(data, dict):
        return [Problem(where, "-", "a vocabulary must be a YAML mapping")]
    problems = []
    unknown = sorted(set(data) - {"name", "description", "fields", "values"})
    problems += [Problem(where, key, "unknown key") for key in unknown]
    if data.get("name") != stem:
        problems.append(Problem(where, "name", f"must equal the file name {stem!r}"))
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        problems.append(Problem(where, "description", "required, one line"))
    extra = data.get("fields", [])
    if not isinstance(extra, list) or not all(isinstance(name, str) for name in extra):
        return problems + [Problem(where, "fields", "must be a list of field names")]
    values = data.get("values")
    if not isinstance(values, list) or not values:
        return problems + [Problem(where, "values", "required, a non-empty list")]
    keys = {"value", "meaning", *extra}
    seen = set()
    for i, entry in enumerate(values):
        field = f"values[{i}]"
        if not isinstance(entry, dict) or set(entry) != keys:
            problems.append(Problem(where, field, f"each entry has exactly {', '.join(sorted(keys))}"))
            continue
        if not isinstance(entry["value"], str) or not entry["value"]:
            problems.append(Problem(where, f"{field}.value", "must be a non-empty string"))
        elif entry["value"] in seen:
            problems.append(Problem(where, f"{field}.value", f"duplicate value {entry['value']!r}"))
        else:
            seen.add(entry["value"])
        if not isinstance(entry["meaning"], str) or not entry["meaning"].strip():
            problems.append(Problem(where, f"{field}.meaning", "must be a one-line meaning"))
    return problems


def _first_line(exc):
    return str(exc).strip().splitlines()[0]
