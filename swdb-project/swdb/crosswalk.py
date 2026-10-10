"""Validate the slide-based LANL crosswalk. Created 2026-10-06 ET.

This document is compatibility metadata, not a research-database record or an import.
"""

import json

import yaml
from jsonschema import Draft202012Validator

from swdb import paths, yamlio
from swdb.problems import Problem


def validate_crosswalk(path):
    """Return problems for a standalone YAML/JSON crosswalk, without changing any records."""
    try:
        document = yamlio.load(path)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [Problem(str(path), "-", str(exc))]
    schema = json.loads((paths.SCHEMAS / "compatibility/main_crosswalk.schema.json").read_text())
    validator = Draft202012Validator(schema)
    return [Problem(str(path), _field(error.absolute_path), error.message)
            for error in validator.iter_errors(document)]


def _field(parts):
    result = ""
    for part in parts:
        result += f"[{part}]" if isinstance(part, int) else (f".{part}" if result else str(part))
    return result or "-"
