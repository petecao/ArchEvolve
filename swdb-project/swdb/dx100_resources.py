"""Own-process-group RSS observations for bounded DX100 jobs. Updated: 2026-09-25."""
import json
from pathlib import Path
import subprocess
import time


def process_group(pgid):
    output = subprocess.check_output(['ps', '-eo', 'pid=,pgid=,rss='], text=True, timeout=10)
    rows = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[1] == str(pgid):
            rows.append({'pid': int(fields[0]), 'rss_kib': int(fields[2])})
    return rows


def observe(path, pgid, processes, start, log, folder, evidence_kind):
    phase = None
    phases = Path(folder) / 'simulation/host-memory-phases.jsonl'
    try:
        with phases.open('rb') as stream:
            stream.seek(max(0, phases.stat().st_size - 16384))
            lines = stream.read(16384).splitlines()
        for line in reversed(lines):
            try:
                phase = json.loads(line)['phase']
                break
            except (ValueError, KeyError):
                pass
    except OSError:
        pass
    row = {'elapsed_s': time.monotonic() - start, 'host_time_ns': time.time_ns(),
           'process_group': pgid, 'processes': processes,
           'rss_kib': sum(item['rss_kib'] for item in processes),
           'log_bytes': log.stat().st_size, 'last_simulator_phase': phase,
           'evidence_kind': evidence_kind, 'host_cost_is_bfs_performance': False}
    with path.open('a') as stream:
        stream.write(json.dumps(row, sort_keys=True) + '\n')
