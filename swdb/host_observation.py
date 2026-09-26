"""Bounded, read-only host condition receipts. Updated: 2026-09-25."""

from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import subprocess
import time

from swdb import artifacts

COMMANDS = (
    ('date', '--iso-8601=seconds'), ('uptime',), ('who',),
    ('df', '-h', '/data1', '/data'), ('free', '-h'),
    ('cat', '/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor'),
    ('cat', '/sys/devices/system/cpu/intel_pstate/no_turbo'),
    ('lscpu',), ('numactl', '--hardware'), ('uname', '-a'),
    ('git', 'rev-parse', '--abbrev-ref', 'HEAD'), ('git', 'rev-parse', 'HEAD'),
)


def attach(data, folder, cwd, **bounds):
    """Retain one receipt in the evaluation/profile's existing evidence chain."""
    observed = capture(folder, cwd, **bounds)
    data['context']['host_observation'] = observed
    data['raw_artifacts'].append({'host': data['context']['host'], 'kind': 'host_observation', **observed})
    return observed


def capture(folder, cwd, *, total_seconds=15, per_command_seconds=3, evidence_kind='execution'):
    """Unavailable controls remain explicit; collection never changes host policy."""
    started = time.monotonic()
    deadline = started + total_seconds
    observed = {'format': 'swdb.host-observation.v1', 'host': socket.gethostname(),
                'started': datetime.now(timezone.utc).isoformat(), 'cwd': str(cwd),
                'evidence_kind': evidence_kind, 'host_cost_is_bfs_performance': False,
                'budget': {'total_seconds': total_seconds, 'per_command_seconds': per_command_seconds}, 'commands': []}
    for command in COMMANDS:
        row = {'command': list(command)}
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            row.update(state='not_collected', reason='host observation budget exhausted', returncode=None)
        else:
            timeout = min(per_command_seconds, remaining)
            row['timeout_seconds'] = timeout
            try:
                result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
                row.update(state='complete' if result.returncode == 0 else 'unavailable',
                           returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
            except subprocess.TimeoutExpired as exc:
                def text(value):
                    return value.decode(errors='replace') if isinstance(value, bytes) else value or ''
                row.update(state='timed_out', returncode=None, stdout=text(exc.stdout), stderr=text(exc.stderr))
            except OSError as exc:
                row.update(state='unavailable', returncode=None, reason=str(exc))
        observed['commands'].append(row)
    observed.update(finished=datetime.now(timezone.utc).isoformat(), host_wall_s=time.monotonic() - started)
    path = Path(folder) / 'host-observation.json'
    with path.open('x') as stream:
        stream.write(json.dumps(observed, indent=2, sort_keys=True) + '\n')
    return {'path': str(path), 'sha256': artifacts.file_hash(path),
            'host_wall_s': observed['host_wall_s'], 'evidence_kind': evidence_kind,
            'unavailable_commands': sum(row['state'] != 'complete' for row in observed['commands'])}
