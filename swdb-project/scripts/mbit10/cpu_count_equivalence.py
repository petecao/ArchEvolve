#!/usr/bin/env python3
"""External count-only campaign helper, 2026-10-06 ET; no timing recalibration."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

p = argparse.ArgumentParser()
p.add_argument('--runtime', type=Path, required=True)
p.add_argument('--source', type=Path, required=True)
p.add_argument('--records', type=Path, required=True)
p.add_argument('--previous', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--llvm-bin', type=Path, required=True)
p.add_argument('--toolchain-flag', action='append', default=[])
a = p.parse_args()
for name in ('runtime', 'source', 'records', 'previous', 'output', 'llvm_bin'):
    setattr(a, name, getattr(a, name).resolve())
os.chdir(a.runtime)
sys.path.insert(0, str(a.runtime))
from swdb import access, artifacts
from swdb.store import Store

if a.output.exists():
    raise SystemExit('choose a new external output directory')
artifacts.external_directory(a.output)
previous = access.read_record(a.previous)
old_counts = previous['compute_counts']
source_sha = artifacts.file_hash(a.source.with_name('CpuWork.h'))
if any(count['source_sha256'] != source_sha for count in old_counts.values()):
    raise SystemExit('frozen compute source differs from previous counted/timed source')
store = Store(a.records)
selected, pending = {}, ['gapbs-bfs-do', 'kron-g16-k16']
def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)
while pending:
    key = pending.pop()
    if key in selected:
        continue
    record = store.get(key)
    if record is None:
        raise SystemExit('missing count registration ' + key)
    selected[key] = record
    pending.extend(x for x in strings(record) if store.get(x) is not None and x not in selected)
records = a.output / 'records'
records.mkdir()
for key in selected:
    relative = store.path_of(key)
    destination = records / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(access.read_record_bytes(a.records / relative))

active, spawning, pending = None, False, None
class Interrupted(Exception):
    pass
def interrupted(signum, frame):
    global pending
    pending = signum
    if not spawning:
        raise Interrupted(signal.Signals(signum).name)
for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
    signal.signal(sig, interrupted)
started = time.monotonic()
new_counts = {}
try:
    for category in ('integer', 'floating_point', 'branch', 'atomic'):
        points, hashes, pipelines = [], [], []
        for n in (32, 64, 96):
            remaining = 900 - (time.monotonic() - started)
            if remaining <= 0:
                raise SystemExit('900-second count-only wall budget exceeded')
            command = [sys.executable, '-m', 'swdb', 'characterize', '--records', str(records),
                '--source', str(a.source), '--implementation', 'gapbs-bfs-do', '--input', 'kron-g16-k16',
                '--function', 'compute_' + category, '--threads', '1', '--fixture',
                '--counting-pipeline', 'source-normalized-v2',
                '--id', f'calibration.equivalence.v2.{category}.{n}', '--roi', 'constructed-compute-function',
                '--llvm-bin', str(a.llvm_bin), '--output', str(a.output / f'count-{category}-{n}'),
                '--run-arg', category, '--run-arg', str(n), '--format', 'json',
                '--timeout-s', str(min(180, remaining)), '--build-flag=-std=c++17', '--build-flag=-pthread']
            command += ['--toolchain-flag=' + flag for flag in a.toolchain_flag]
            spawning = True
            active = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
            spawning = False
            if pending is not None:
                raise Interrupted(signal.Signals(pending).name)
            stdout, stderr = active.communicate(timeout=remaining)
            if active.returncode:
                raise SystemExit(f'{category}/{n} failed: {stderr[-4000:]}')
            active = None
            if sum(path.stat().st_size for path in a.output.rglob('*') if path.is_file()) > 50 * 1024**2:
                raise SystemExit('50 MiB count-only raw budget exceeded')
            data = json.loads(stdout)
            points.append([n, sum(r['operation_counts'][category]['value'] for r in data['regions'])])
            hashes.append(artifacts.digest(data))
            pipelines.append({'version': data['counting']['pipeline_version'], 'passes': data['counting']['passes']})
        slope = (points[1][1] - points[0][1]) / 32
        base = points[0][1] - 32 * slope
        if slope <= 0 or slope != int(slope) or points[2][1] != 96 * slope + base:
            raise SystemExit(f'non-affine count curve: {category}')
        if any(pipeline != pipelines[0] for pipeline in pipelines) or pipelines[0]['version'] != 'source-normalized-v2':
            raise SystemExit('pipeline identity mismatch')
        old = old_counts[category]
        new_counts[category] = {'old_pipeline': old.get('pipeline', {'version': 'source-normalized-v1', 'passes': ['mem2reg', 'loop-simplify']}),
            'old_pipeline_basis': 'reported' if 'pipeline' in old else 'code_reading',
            'old_pipeline_source_commit': previous.get('source_commit'),
            'old_validation_points': old['validation_points'],
            'new_pipeline': pipelines[0], 'source_sha256': source_sha,
            'old_per_iteration': old['per_iteration'], 'old_per_invocation': old['per_invocation'],
            'per_iteration': int(slope), 'per_invocation': int(base), 'validation_points': points,
            'characterization_sha256': hashes, 'coefficients_identical': (int(slope), int(base)) == (old['per_iteration'], old['per_invocation'])}
finally:
    if active is not None:
        for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
            signal.signal(sig, signal.SIG_IGN)
        try:
            os.killpg(active.pid, signal.SIGTERM)
            active.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(active.pid, signal.SIGKILL)
            active.communicate()
        except ProcessLookupError:
            pass
result = {'format': 'swdb.cpu-calibration-pipeline-equivalence.v1', 'evidence_kind': 'count_only',
    'runtime_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'runtime_dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip()),
    'previous_receipt_sha256': previous.get('receipt_sha256', previous.get('identity_sha256')),
    'host': os.uname().nodename, 'architecture': os.uname().machine,
    'source_sha256': source_sha, 'compiler_version': subprocess.check_output([str(a.llvm_bin / 'clang++'), '--version'], text=True).strip(),
    'toolchain_flags': a.toolchain_flag, 'build_flags': ['-std=c++17', '-pthread'], 'compute_counts': new_counts,
    'all_coefficients_identical': all(value['coefficients_identical'] for value in new_counts.values()),
    'timings_rerun': False, 'raw_directory': str(a.output), 'raw_transferred': False}
result['identity_sha256'] = artifacts.digest(result)
(a.output / 'equivalence.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
