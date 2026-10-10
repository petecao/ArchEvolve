#!/usr/bin/env python3
"""Regenerate or check the D06 handoff example messages from actual records.

Created: 2026-09-27 (Eastern Time). Updated: 2026-10-06 ET. Every example is rendered through the public
`swdb handoff-message` command from an existing master record, so the examples
track the current record formats. This driver reads records only; it runs no
evaluation, contacts no collaborator, and makes no performance claim.

    python3 scripts/bfs_handoff_examples.py            # rewrite the examples
    python3 scripts/bfs_handoff_examples.py --check    # fail if any is stale
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "docs" / "bfs-handoff-examples"
MANIFEST = FOLDER / "manifest.json"


def render(message, record_id, records, db, mode, campaign):
    command = [sys.executable, "-B", "-m", "swdb", "handoff-message", message, record_id,
               "--records", str(records), "--db", str(db), "--format", "json", "--mode", mode]
    if campaign is not None:
        command.extend(["--campaign", campaign])
    done = subprocess.run(command,
                          cwd=ROOT, capture_output=True, text=True, timeout=600)
    if done.returncode != 0:
        raise SystemExit(f"handoff-message {message} {record_id} failed: {done.stderr.strip()}")
    return json.dumps(json.loads(done.stdout), indent=2, sort_keys=True) + "\n"


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
        for row in manifest["examples"]:
            text = render(row["message"], row["record"], args.records, db, args.mode, args.campaign)
            target = FOLDER / row["file"]
            if args.check:
                if not target.is_file() or target.read_text() != text:
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
