#!/usr/bin/env python3
"""Regenerate or check the D06 handoff example messages from actual records.

Created: 2026-09-27 (Eastern Time). Updated: 2026-10-06 ET; 2026-10-14 ET (the check keeps the archived
date of an evaluation result's certification_level snapshot). Every example is rendered as the public
`swdb handoff-message` command renders it (2026-10-14 ET: in this process, from one validated store
snapshot), from an existing master record, so the examples
track the current record formats. This driver reads records only; it runs no
evaluation, contacts no collaborator, and makes no performance claim.

    python3 scripts/bfs_handoff_examples.py            # rewrite the examples
    python3 scripts/bfs_handoff_examples.py --check    # fail if any is stale
"""
import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "docs" / "bfs-handoff-examples"
MANIFEST = FOLDER / "manifest.json"


def renderer(records, db, mode, campaign):
    """Render messages as `swdb handoff-message` does, from one validated store snapshot.

    2026-10-14 ET: validating the full store takes minutes, and the command validates it on every call, so
    the driver validates once (`db.query_store`) and renders each message in this process with the same
    mode, campaign tags and team guard the command applies."""
    sys.path.insert(0, str(ROOT))
    from argparse import Namespace
    from swdb import archevolve, handoff
    from swdb import db as swdb_db
    from swdb.cli import Failure
    context = Namespace(mode=mode, campaign=campaign, command="handoff-message", records=records, db=db,
                        format="json")
    with archevolve.command_mode(context):
        store = swdb_db.query_store(records, db)

    def render(message, record_id):
        try:
            with archevolve.command_mode(context):
                archevolve.guard_cli(Namespace(**vars(context), message=message, id=record_id))
                data = handoff.render(store, message, record_id)
        except Failure as exc:
            raise SystemExit(f"handoff-message {message} {record_id} failed: {exc}") from None
        return json.dumps(json.loads(json.dumps(data)), indent=2, sort_keys=True) + "\n"
    return render


def _keep_snapshot_time(text, archived):
    """The rendered text with the archived certification_level snapshot time (2026-10-14 ET, Probata PoC 18).

    An evaluation result's certification_level block is a snapshot dated when it is rendered; the check
    compares everything else, so a re-render on another day is not stale for its date alone."""
    try:
        old = json.loads(archived)["content"]["certification_level"]["snapshot"]["at"]
        message = json.loads(text)
        message["content"]["certification_level"]["snapshot"]["at"] = old
    except (ValueError, KeyError, TypeError):
        return text
    return json.dumps(message, indent=2, sort_keys=True) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="compare instead of writing")
    parser.add_argument("--records", type=Path, default=ROOT / "records")
    parser.add_argument("--mode", choices=["archevolve", "extensa"], default="archevolve",
                        help="explicit rendering policy for historical backend-linked examples")
    parser.add_argument("--campaign", help="required Extensa rendering context; creates no campaign records")
    args = parser.parse_args(argv)
    manifest = json.loads(MANIFEST.read_text())
    stale = []
    with tempfile.TemporaryDirectory(prefix="bfs-handoff-examples-") as scratch:
        db = Path(scratch) / "index.sqlite"
        render = renderer(args.records, db, args.mode, args.campaign)
        for row in manifest["examples"]:
            text = render(row["message"], row["record"])
            target = FOLDER / row["file"]
            if args.check:
                if not target.is_file() or target.read_text() != _keep_snapshot_time(text, target.read_text()):
                    stale.append(row["file"])
            else:
                target.write_text(text)
    if stale:
        print("stale handoff examples: " + ", ".join(stale), file=sys.stderr)
        return 1
    print(("checked " if args.check else "wrote ") + str(len(manifest["examples"])) + " handoff examples")
    return 0


if __name__ == "__main__":
    sys.exit(main())
