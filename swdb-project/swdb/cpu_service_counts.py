"""Separate source-normalized native service event proof. Created: 2026-10-06 ET."""
import json
import sys
from pathlib import Path

from swdb import access, artifacts
from swdb.cli import Failure
from swdb.extensa_boundary import closure
from swdb.store import Store


def clock_proof(records, output, llvm_bin, toolchain_flags, command):
    store = Store(records)
    seeds = ['gapbs-bfs-do', 'kron-g16-k16']
    if any(store.get(key) is None for key in seeds):
        raise Failure('service count proof requires the registered counting fixture carrier and input')
    copied = output / 'count-records'
    copied.mkdir()
    for key in closure(store, seeds):
        relative = store.path_of(key)
        destination = copied / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(access.read_record_bytes(Path(records) / relative))
    points, hashes, pipelines, names = {}, [], [], set()
    for invoke in (True, False):
        rows = []
        for n in (32, 64, 96):
            argv = [sys.executable, '-m', 'swdb', 'characterize', '--records', copied,
                '--source', output / 'CpuServiceCount.cpp', '--implementation', seeds[0], '--input', seeds[1],
                '--function', 'service_clock', '--threads', '1', '--fixture',
                '--counting-pipeline', 'source-normalized-v2', '--id', f'calibration.service.clock.{int(invoke)}.{n}',
                '--roi', 'constructed-clock-service', '--llvm-bin', llvm_bin,
                '--output', output / f'count-clock-{int(invoke)}-{n}', '--run-arg', str(n), '--run-arg', str(int(invoke)),
                '--format', 'json', '--timeout-s', '60', '--build-flag=-std=c++17']
            argv.extend('--toolchain-flag=' + flag for flag in toolchain_flags)
            data = json.loads(command(argv).stdout)
            calls = [c for c in data['unmodeled_calls'] if c.get('cost_accounting') == 'opaque_callee'
                     and not c.get('body_counted') and c['execution_count']['value']]
            observed = sum(c['execution_count']['value'] for c in calls)
            if observed != (n if invoke else 0):
                raise Failure('clock service numerator differs from exactly one opaque event per iteration')
            names.update(c['name'] for c in calls)
            rows.append([n, observed])
            hashes.append(artifacts.digest(data))
            pipelines.append({'version': data['counting']['pipeline_version'], 'passes': data['counting']['passes']})
            if sum(p.stat().st_size for p in output.rglob('*') if p.is_file()) > 25 * 1024**2:
                raise Failure('service count proof reached its 25MiB raw budget')
        points['service' if invoke else 'driver'] = rows
    if len(names) != 1 or any(p != pipelines[0] for p in pipelines) or pipelines[0]['version'] != 'source-normalized-v2':
        raise Failure('service ABI or count pipeline is inconsistent')
    root = Path(__file__).parent
    return {'format': 'swdb.cpu-service-count-proof.v1', 'pipeline': pipelines[0],
        'source_sha256': artifacts.file_hash(output / 'CpuServiceWork.h'),
        'count_driver_sha256': artifacts.file_hash(output / 'CpuServiceCount.cpp'),
        'event_abi': next(iter(names)), 'service_validation_points': points['service'],
        'driver_validation_points': points['driver'], 'characterization_sha256': hashes,
        'plugin_source_sha256': artifacts.file_hash(root / 'llvm/Characterize.cpp'),
        'runtime_source_sha256': artifacts.file_hash(root / 'llvm/CountingRuntime.cpp')}
