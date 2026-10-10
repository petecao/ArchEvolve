"""Where the database lives. The tool runs from its repo (or an editable install).

Updated: 2026-10-05 ET (code review S13): the mbit10 lab-host locations below are the one copy
the campaign adapters, the dispatch preflight and the lane verification share
(`.claude/rules/remote_server.md`). Hash-pinned or self-hashed modules (for example
`swdb/bfs_native.py`, whose file hash is the BFS v1 verifier identity) keep their literals."""

import os
from pathlib import Path

HOME = Path(os.environ.get("SWDB_HOME", Path(__file__).resolve().parent.parent))
SCHEMAS = HOME / "schemas"
VOCAB = HOME / "vocab"
RECORDS = HOME / "records"

#: Raw run output on mbit10: /data1 first, /data when /data1 has under 20 GB free.
RUN_ROOTS = (Path("/data1/yanruj/EvolveSWDB_runs"), Path("/data/yanruj/EvolveSWDB_runs"))
#: External build folders on mbit10 (never inside the repository).
BUILD_ROOT = Path("/data1/yanruj/EvolveSWDB_builds")
#: MemAcc's socket-lane lease folder (MemAcc ADR 0010); LACT_LEASE_ROOT overrides it.
LEASE_ROOT = "/data1/yanruj/lact-host-lease"


def lease_root():
    """The socket-lane lease folder, read at call time so an override applies."""
    return Path(os.environ.get("LACT_LEASE_ROOT", LEASE_ROOT))
