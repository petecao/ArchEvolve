#!/usr/bin/env python3
"""One prospective v2 author completion observation. Created: 2026-09-26 ET."""
from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.bfs_process import interruption_signals
from scripts.dx100_trace_probe import PRIOR_ID, run

PROBE_ID = 'bfs-dx100-witness-20260926-a1'
REQUEST = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/requests/dx100-witness-a1.yaml'


def validate_request(request, prior, *, probe_id=PROBE_ID):
    if prior.get('id') != PRIOR_ID or prior.get('evidence_kind') != 'execution':
        raise ValueError('witness probe requires the exact retained real a6 evaluation')
    expected = deepcopy(prior['request'])
    expected['id'] = probe_id
    expected['verification'].update(checker='dx100.bfs.verifier.v2',
                                    max_ticks=10**10, post_roi_trace='SyscallBase')
    if request != expected:
        raise ValueError('witness probe may change only ID, explicit v2 checker, '
                         'post-ROI tick limit, and SyscallBase trace')


if __name__ == '__main__':
    with interruption_signals():
        run(request_file=REQUEST, validator=validate_request,
            purpose='prospective v2 author completion observations; no comparison or gain claim')
