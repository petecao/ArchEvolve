#!/usr/bin/env python3
"""Register BC workloads on the same graphs as registered BFS workloads (2026-10-03 ET).

Ticket 40. BC (kernel gapbs-bc) reuses the Kronecker and uniform graphs already
generated and registered for BFS: the request copies the source workload's
family, generator and serialized representations, so register-workload re-verifies
the same files and loads the same canonical adjacency under the BC kernel. Only
the kernel, the requested ID and, optionally, the sources change. The BC plug-in
refuses sources without an outgoing edge (BCVerifier is vacuous there).

Real representations live under /data1/yanruj on mbit10; run this there inside
an owned socket lane (ticket 41). Tests call ``build_request`` with fixtures.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swdb import bfs_protocol  # noqa: E402
from swdb.cli import Failure  # noqa: E402
from swdb.store import Store  # noqa: E402

KERNEL = "gapbs-bc"
FAMILIES = {"kronecker", "uniform_random"}


def build_request(store, workload_id, new_id, sources=None, work_dir=None, families=FAMILIES):
    """A register-workload request for BC over a registered workload's exact graph files."""
    data = store.get(workload_id, "workload")
    if data is None:
        raise Failure(f"workload {workload_id!r} does not exist")
    bfs_protocol.verify_immutable(data)
    definition = data["definition"]
    if families is not None and definition["family"] not in families:
        raise Failure(f"BC workloads reuse Kronecker or uniform graphs; {definition['family']!r} is neither")
    representations = [{key: row[key] for key in ("id", "path", "sha256", "format", "application")}
                       for row in definition["representations"]]
    request = {"message_version": "1.0", "id": new_id, "version": 1, "kernel": KERNEL,
               "family": definition["family"], "generator": definition["generator"],
               "normalization": definition["normalization"],
               "sources": list(definition["sources"] if sources is None else sources),
               "representations": representations}
    if work_dir is not None:
        request["parser"] = {"work_dir": str(work_dir), "compile_timeout_s": 60, "timeout_s": 900}
    return request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-workload", required=True, help="registered workload whose graph BC reuses")
    parser.add_argument("--id", required=True, help="requested BC workload ID")
    parser.add_argument("--sources", type=int, nargs="+")
    parser.add_argument("--work-dir", type=Path, help="streaming SG parser folder (large graphs)")
    parser.add_argument("--records", type=Path, default=ROOT / "records")
    parser.add_argument("--request-out", type=Path, required=True, help="where the request JSON is written")
    args = parser.parse_args()
    request = build_request(Store(args.records), args.from_workload, args.id, args.sources, args.work_dir)
    args.request_out.write_text(json.dumps(request, indent=2) + "\n")
    result = subprocess.run([sys.executable, "-m", "swdb", "register-workload", str(args.request_out),
                             "--records", str(args.records), "--format", "json"], cwd=ROOT)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
