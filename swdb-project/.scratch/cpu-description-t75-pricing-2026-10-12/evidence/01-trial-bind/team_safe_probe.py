"""C3 team-safe probe for the services.v2 inputs. Created: 2026-10-12 ET (cpud ticket 01).

Runs `swdb.archevolve.require_team_safe` (the gate `cpu_service_binding.bind` calls) once per
value, plus once over the full trial-bind input list, and prints one JSON document. Read-only.
Run from `swdb-project/`:

    python3 .scratch/cpu-description-t75-pricing-2026-10-12/evidence/01-trial-bind/team_safe_probe.py [--records records]
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT))
from swdb import artifacts, workflow  # noqa: E402
from swdb.archevolve import require_team_safe  # noqa: E402
from swdb.cli import Failure  # noqa: E402
from swdb.store import Store  # noqa: E402

PROBES = ['fga03.t75-baseline.uniform22.t1.characterization.a2',
          'fga03.t75-candidate.uniform22.t1.characterization.a2',
          'mbit10.cpu.lanl20261006a2.v2.t1',
          'mbit10.cpu.lanl20261006.t1.services.v1']
# Every input the C4 trial bind passes (services.v1 bind inputs + the two t75 counts).
BIND_INPUTS = ['mbit10.cpu.lanl20261006a2.v2.t1',
               'bfs.kron-g16.t1.characterization.objects.a1', 'bc.kron-g16.t1.characterization.objects.a1',
               'bfs.kron-g17.t1.characterization.objects.a1', 'bc.kron-g17.t1.characterization.objects.a1',
               'fga03.t75-baseline.uniform22.t1.characterization.a2',
               'fga03.t75-candidate.uniform22.t1.characterization.a2',
               'mbit10.cpu.lanl20261006.service.clock.a2', 'mbit10.cpu.lanl20261006.resource.allocator.a1',
               'mbit10.cpu.lanl20261006.resource.allocator-extra.a1', 'mbit10.cpu.lanl20261006.resource.memory.a1',
               'mbit10.cpu.lanl20261006.resource.float-memory.a1', 'mbit10.cpu.lanl20261006.service.byte-read.a1',
               'mbit10.cpu.lanl20261006.resource.bulk-total.a1', 'mbit10.cpu.lanl20261006.resource.bulk-total.a2',
               'mbit10.cpu.lanl20261006.service.openmp.a1']


def probe(store, values):
    start = time.monotonic()
    try:
        require_team_safe(store, *values, command='probe')
        outcome, reason = 'pass', None
    except Failure as error:
        outcome, reason = 'refused', str(error)
    return {'values': values, 'outcome': outcome, 'reason': reason,
            'sha256': {v: artifacts.digest(store.get(v)) for v in values if store.get(v) is not None},
            'seconds': round(time.monotonic() - start, 2)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--records', type=Path, default=PROJECT / 'records')
    args = parser.parse_args()
    start = time.monotonic()
    store = Store(args.records)
    load_s = round(time.monotonic() - start, 1)
    missing = [v for v in BIND_INPUTS + PROBES if store.get(v) is None]
    rows = [probe(store, [v]) for v in PROBES] + [probe(store, BIND_INPUTS)]
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=PROJECT, capture_output=True, text=True).stdout.strip()
    print(json.dumps({'format': 'cpud01.team-safe-probe.v1', 'gate': 'swdb.archevolve.require_team_safe',
                      'command': 'probe', 'commit': head, 'records': str(args.records),
                      'creation_mode': workflow.CREATION_TAGS.get('mode'), 'store_load_s': load_s,
                      'missing_ids': missing, 'probes': rows,
                      'all_pass': not missing and all(r['outcome'] == 'pass' for r in rows)}, indent=1))
    return 0 if not missing and all(r['outcome'] == 'pass' for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
