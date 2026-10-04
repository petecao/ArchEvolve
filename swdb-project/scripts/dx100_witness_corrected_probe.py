#!/usr/bin/env python3
"""One diagnosed progress-parser correction proof. Created: 2026-09-26 ET."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.bfs_process import interruption_signals
from scripts.dx100_trace_probe import run
from scripts.dx100_witness_probe import validate_request as validate_original
from swdb.artifacts import file_hash

PROBE_ID = 'bfs-dx100-witness-20260926-a2'
REQUEST = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/requests/dx100-witness-a2.yaml'
FAILED = ROOT / 'records/evaluations/bfs-dx100-witness-20260926-a1.yaml'
FAILED_SHA256 = '9a941cdff315e283b13563bf81ef2f45ba0712bbcf6d31b92f6232488efa3b42'


def validate_request(request, prior):
    if not FAILED.is_file() or file_hash(FAILED) != FAILED_SHA256:
        raise ValueError('corrective proof requires the unchanged retained failed a1 record')
    validate_original(request, prior, probe_id=PROBE_ID)


if __name__ == '__main__':
    with interruption_signals():
        run(request_file=REQUEST, validator=validate_request,
            purpose='one diagnosed progress-parser correction; a1 remains failed; no comparison or gain claim')
