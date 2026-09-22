"""Command line: `swdb <command>`. Exit 0 = success, 1 = the check failed, 2 = usage error."""

import argparse
import sys
from pathlib import Path

from swdb import paths
from swdb.validate import validate_records


def main(argv=None):
    parser = argparse.ArgumentParser(prog="swdb", description="ArchEvolve Software Database tool.")
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("validate", help="check every record against its schema and the vocabularies")
    check.add_argument(
        "--records", type=Path, default=paths.RECORDS, help="records folder (default: the repo's records/)"
    )

    args = parser.parse_args(argv)
    if args.command == "validate":
        return _validate(args.records)
    return 2


def _validate(records_dir):
    if not records_dir.is_dir():
        print(f"swdb: records folder not found: {records_dir}", file=sys.stderr)
        return 2
    result = validate_records(records_dir)
    for problem in result.problems:
        print(problem, file=sys.stderr)
    if result.problems:
        files = len({problem.file for problem in result.problems})
        print(
            f"FAILED: {len(result.problems)} error(s) in {files} file(s); {result.count} record(s) checked",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {result.count} record(s) valid")
    return 0
