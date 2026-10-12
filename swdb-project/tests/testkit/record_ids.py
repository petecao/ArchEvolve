"""Record IDs read from a YAML file's top-level `id:` line, without parsing the record.
Created 2026-10-11 ET (LANL-shaped-db review fixes, finding 9).

Catalog records can be large (estimates reach hundreds of MB), so fixtures that only need IDs
read this one line. `conftest.make_records(...).copy_closure` and the tests that list every
record of a folder share this one pattern."""

import re

#: A top-level `id:` line (no indent), its value without surrounding blanks.
ID_LINE = re.compile(rb"^id:[ \t]*(.+?)[ \t]*$", re.M)


def record_id(path):
    """The ID on the one top-level `id:` line of `path`; a clear error if there is not exactly one."""
    ids = ID_LINE.findall(path.read_bytes())
    if len(ids) != 1:
        raise ValueError(f"{path}: expected one top-level `id:` line, found {len(ids)}: "
                         f"{[i.decode(errors='replace') for i in ids[:3]]}")
    return ids[0].decode()


def record_ids(root, *folders):
    """IDs of every `*.yaml` record in each of `folders` under `root`, in path order; a missing
    folder has none."""
    return [record_id(path) for folder in folders for path in sorted((root / folder).glob("*.yaml"))]
