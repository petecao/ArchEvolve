#!/usr/bin/env python3
"""Import T17 a3's retained record dependency closure (2026-09-29 ET).

Copies authoritative metadata only, preserving IDs, hashes and external raw paths.
Existing records must be identical. A named implementation may retain current
annotations only when all source/build/evaluator identity fields remain identical.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swdb import artifacts, db, writer
from swdb.cli import Failure
from swdb.store import Record, Store

SEEDS = [f"bfs-t17-routes-20260928-a3.{role}.{family}.aggregate"
         for role in ("baseline", "candidate") for family in ("uniform18", "kronecker18")]
SEEDS += ["bfs-t17-ac10-companion-20260928-a3.execute"]
ANNOTATIONS = {"updated", "extensions", "loops", "access_patterns", "notes"}


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retained-records", type=Path, action="append", required=True,
                        help="repeat for a separate companion runtime; overlay ID collisions must be identical")
    parser.add_argument("--records", type=Path, default=ROOT / "records")
    parser.add_argument("--prefer-current-implementation", action="append", default=[],
                        help="retain a named implementation's current source annotations, after checking source/build/evaluator equality")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if any(args.records.resolve() == root.resolve() for root in args.retained_records):
        raise Failure("import needs distinct retained and current record folders")
    merged = {}
    for root in args.retained_records:
        overlay = Store(root)
        if overlay.problems:
            raise Failure(f"record parsing failed in {root}; nothing imported")
        for item in overlay.records:
            previous = merged.get(item.id)
            if previous and artifacts.digest(previous.data) != artifacts.digest(item.data):
                raise Failure(f"retained metadata overlays disagree on {item.id}; nothing imported")
            merged[item.id] = Record(str(root / item.rel), item.data)
    retained = Store(args.retained_records[0], indexed_records=list(merged.values()))
    current = Store(args.records)
    if current.problems:
        raise Failure("record parsing failed; nothing imported")
    prefer = set(args.prefer_current_implementation)
    seen, needed, equal, annotations = set(), {}, [], []

    def visit(identifier):
        if identifier in seen:
            return
        seen.add(identifier)
        original = retained.get(identifier)
        if original is None:
            if current.get(identifier) is None:
                raise Failure(f"missing dependency {identifier}; nothing imported")
            return
        existing = current.get(identifier)
        if existing is not None:
            if artifacts.digest(original) != artifacts.digest(existing):
                left = {k: v for k, v in original.items() if k not in ANNOTATIONS}
                right = {k: v for k, v in existing.items() if k not in ANNOTATIONS}
                if (identifier not in prefer or original.get("kind") != "implementation"
                        or existing.get("kind") != "implementation" or left != right):
                    raise Failure(f"metadata collision with different content: {identifier}; nothing imported")
                annotations.append({"id": identifier, "retained_sha256": artifacts.digest(original),
                                    "current_sha256": artifacts.digest(existing), "source_identity_unchanged": True})
            else:
                equal.append(identifier)
            return
        needed[identifier] = original
        for reference in strings(original):
            if reference in retained.by_id or reference in current.by_id:
                visit(reference)

    for identifier in SEEDS:
        visit(identifier)
        aggregate = retained.get(identifier, "evaluation")
        if aggregate is None:
            raise Failure(f"retained a3 seed {identifier} is unavailable")
        # Packages point at primary executions, so discover this reverse edge
        # explicitly; forward reference traversal then retains their dependencies.
        primary_ids = {row["evaluation"] for row in aggregate.get("component_evaluations", [])}
        for package in retained.of_kind("profile_package"):
            if package.data.get("evaluation") in primary_ids:
                visit(package.id)
    # Atomic writer validates the complete prospective current store before any
    # new file is persisted. No raw source, binary, input or log is copied.
    written = writer.commit(args.records, new=list(needed.values())) if needed else []
    if written:
        db.build(args.records, db.default_path(args.records))
    summary = {"created": "2026-09-29", "retained_records": [str(root.resolve()) for root in args.retained_records],
               "current_records": str(args.records.resolve()), "seeds": SEEDS,
               "imported": [{"id": rid, "sha256": artifacts.digest(data),
                              "kind": data["kind"]} for rid, data in sorted(needed.items())],
               "identical_existing": sorted(equal), "current_annotations_retained": annotations,
               "written_paths": written, "raw_files_moved": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"imported": len(needed), "identical_existing": len(equal),
                      "annotations_retained": annotations, "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
