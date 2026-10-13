"""cpud ticket 10: build the reference-closed record view the timing commands run against.

Created 2026-10-13 ET. Why: every `swdb evaluate`/`bfs-profile` save re-validates and re-indexes
the whole store (`workflow.persist` -> `writer.commit` + `db.build`); on the 1.3 GB catalog one save
took over 20 min on mbit10, and an evaluation saves ~4 times per trial. The view keeps only the
records the roots reach through exact ID references, plus the small catalog kinds whole: the same
rule as the test suite's `copy_closure` (tests/conftest.py, 2026-10-09 ET). Each command still
fully validates the view; the new records are then checked inside a full-store copy by
`swdb validate` (run.sh).

Usage (from swdb-project/): python3 make_view.py <records> <view dir> <root id>...
"""
import shutil
import sys
from pathlib import Path

sys.path[:0] = ['.', 'tests']   # run from swdb-project/
from swdb.access import read_record, record_files  # noqa: E402
from testkit.record_ids import record_id  # noqa: E402

WHOLE = {"applications", "kernels", "implementations", "operations", "intrinsics",
         "hardware_targets", "machines", "workloads", "inputs", "strategies"}


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def main(source, target, roots):
    source, target = Path(source), Path(target)
    if target.exists():
        raise SystemExit(f"{target} exists")
    where = {record_id(path): Path(rel) for path, rel in record_files(source)}
    missing = [r for r in roots if r not in where]
    if missing:
        raise SystemExit(f"roots not in {source}: {missing}")
    keep, queue = set(), [*roots, *(rid for rid, rel in where.items() if rel.parts[0] in WHOLE)]
    while queue:
        rid = queue.pop()
        if rid in keep:
            continue
        keep.add(rid)
        queue.extend(t for t in strings(read_record(source / where[rid])) if t in where and t not in keep)
    for rid in sorted(keep):
        (target / where[rid]).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / where[rid], target / where[rid])
    for path in source.rglob("*"):
        rel = path.relative_to(source)
        if path.is_file() and path.suffix not in {".yaml", ".yml"} and not any(p.startswith(".") for p in rel.parts):
            (target / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target / rel)
    print(f"view: {len(keep)} of {len(where)} records")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
