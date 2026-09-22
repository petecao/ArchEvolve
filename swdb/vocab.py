"""Controlled vocabularies: one YAML file per term list, each value with a meaning.

Schemas refer to a vocabulary by name (`"x-vocab": "<name>"`); adding a value to the
file extends what records may say without touching any schema.
"""

import yaml

from swdb import yamlio
from swdb.problems import Problem


def load_all(vocab_dir):
    """Return ({name: [values]}, [Problem]) for every vocabulary file in vocab_dir."""
    vocabs, problems = {}, []
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
    return vocabs, problems


def _check(where, stem, data):
    if not isinstance(data, dict):
        return [Problem(where, "-", "a vocabulary must be a YAML mapping")]
    problems = []
    if data.get("name") != stem:
        problems.append(Problem(where, "name", f"must equal the file name {stem!r}"))
    if not isinstance(data.get("description"), str) or not data["description"].strip():
        problems.append(Problem(where, "description", "required, one line"))
    values = data.get("values")
    if not isinstance(values, list) or not values:
        return problems + [Problem(where, "values", "required, a non-empty list")]
    seen = set()
    for i, entry in enumerate(values):
        field = f"values[{i}]"
        if not isinstance(entry, dict) or set(entry) != {"value", "meaning"}:
            problems.append(Problem(where, field, "each entry has exactly `value` and `meaning`"))
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
