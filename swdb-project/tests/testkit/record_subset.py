"""Copy real fixture dependencies without parsing unrelated evidence. Created 2026-10-08 ET.

The catalog's top-level ID headers are small even when a record body is large.
Only records reachable from explicit fixture roots are parsed and copied; the
public commands still validate every copied record and its references.
"""

import re
import shutil
from pathlib import Path

import yaml

from swdb import yamlio

HEADER_BYTES = 64 * 1024
ID_LINE = re.compile(r"^(?:id|'id'|\"id\")\s*:")


def _header_id(path):
    remaining = HEADER_BYTES
    with path.open("rb") as stream:
        while remaining:
            line = stream.readline(remaining + 1)
            if not line or len(line) > remaining:
                break
            remaining -= len(line)
            text = line.decode("utf-8-sig")
            if ID_LINE.match(text):
                header = yaml.safe_load(text)
                rid = header.get("id") if isinstance(header, dict) else None
                if isinstance(rid, str) and rid:
                    return rid
                break
    raise ValueError(f"record lacks a text ID in its bounded header: {path}")


def _index(source):
    result = {}
    for path in sorted(source.rglob("*")):
        rel = path.relative_to(source)
        if any(part.startswith(".") for part in rel.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"fixture catalog contains a symlink: {path}")
        if path.is_file() and path.suffix in {".yaml", ".yml"}:
            rid = _header_id(path)
            if rid in result:
                raise ValueError(f"duplicate fixture record ID: {rid}")
            result[rid] = path
    return result


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)


def copy_record_subset(source, destination, roots):
    """Copy original files for all known ID references, including semantic evidence.

    Missing roots, duplicate IDs and invalid selected records refuse the fixture.
    Unknown schema references are rejected by the unchanged public validation;
    prose and vocabulary strings are not guessed to be record IDs.
    """
    source, destination = Path(source), Path(destination)
    index = _index(source)
    roots = list(roots)
    if not roots or any(not isinstance(rid, str) or rid not in index for rid in roots):
        raise ValueError(f"fixture roots are missing from the catalog: {roots}")
    selected, pending = set(), list(roots)
    while pending:
        rid = pending.pop()
        if rid in selected:
            continue
        data = yamlio.load(index[rid])
        if not isinstance(data, dict) or data.get("id") != rid:
            raise ValueError(f"selected fixture record/header ID differs: {index[rid]}")
        selected.add(rid)
        references = _strings({key: value for key, value in data.items() if key not in {"id", "kind"}})
        pending.extend(ref for ref in references if ref in index and ref not in selected)
    for rid in sorted(selected):
        path = index[rid]
        target = destination / path.relative_to(source)
        if target.exists():
            if target.is_symlink() or target.read_bytes() != path.read_bytes():
                raise ValueError(f"fixture copy would replace an existing record: {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    return selected
