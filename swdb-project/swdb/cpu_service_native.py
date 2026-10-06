"""Native service context admission; no application timing input. Created: 2026-10-06 ET."""
import platform
import re
import shutil
import socket
from pathlib import Path

from swdb import artifacts, paths
from swdb.cli import Failure
from swdb.store import Store


def prepare(args, output):
    if args.fixture:
        return None
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise Failure('native service calibration requires its registered Linux x86_64 target')
    if not args.llvm_bin or args.min_trial_s < .05 or args.repetitions < 7:
        raise Failure('native service calibration requires LLVM22, >=0.05s trials and >=7 repetitions')
    machine = Store(args.records).get(args.machine, 'machine')
    if not machine or socket.gethostname().split('.')[0] != machine['hostname']:
        raise Failure('native service calibration must run on its registered machine')
    from swdb.profile import _verified_lane
    from swdb.cpu_calibration import _physical_cpus, _host_state
    lane = _verified_lane(machine, args.lane)
    cpus = _physical_cpus()
    if not cpus:
        raise Failure('native service calibration needs a physical core inside its verified lane')
    if not any(output.is_relative_to(root) for root in (Path('/data1/yanruj'), Path('/data/yanruj'))):
        raise Failure('native service raw output must use the project data mounts')
    ancestor = next(p for p in (output, *output.parents) if p.exists())
    free = shutil.disk_usage(ancestor).free
    if free < 20 * 1024**3:
        raise Failure('native service raw output needs at least 20GiB free')
    return {'lane': lane, 'cpus': cpus[:1], 'machine_sha256': artifacts.digest(machine),
        'system': 'Linux', 'start_state': _host_state(), 'free_disk_bytes': free}


def loaded_libraries(binary, command):
    output = command(['ldd', binary]).stdout
    rows = {}
    for line in output.splitlines():
        match = re.search(r'(?:=>\s*)?(/[^\s]+)\s+\(', line)
        if match:
            path = Path(match.group(1)).resolve()
            rows[path.name] = {'path': str(path), 'sha256': artifacts.file_hash(path)}
    if not any(name.startswith('libstdc++') for name in rows) or not any(name.startswith('libc.so') for name in rows):
        raise Failure('cannot establish loaded C/C++ runtime identities')
    return rows


def validate(raw):
    context, settings = raw['context'], raw['settings']
    def require(condition, reason):
        if not condition:
            raise Failure(reason)
    require(raw['threads'] == 1 and context.get('system') == 'Linux' and context.get('architecture') == 'x86_64', 'native service requires Linux/x86_64 serial T1 scope')
    require(context.get('host', '').split('.')[0] == raw['machine'], 'native service host/target differs')
    require(context.get('dirty') is False and re.fullmatch('[0-9a-f]{40}', str(context.get('commit'))), 'native service needs clean committed source')
    require('(verified:' in str(context.get('lane')), 'native service needs a verified socket lane')
    require(context.get('instrumented_timer') is False and re.search(r'clang version 22\.', context.get('compiler_version', '')), 'native service needs uninstrumented LLVM22 timing')
    require(7 <= settings['repetitions'] <= 11 and settings['min_trial_s'] >= .05 and 0 < settings['max_wall_s'] <= 900, 'native service timing budget/sampling differs')
    require(settings.get('iteration_cap') == 134217728 and settings.get('resident_payload_bytes') == 0 and settings.get('raw_output_cap_bytes') == 25 * 1024**2, 'native service construction budgets differ')
    require(isinstance(context.get('cpus'), list) and len(context['cpus']) == 1 and type(context['cpus'][0]) is int and context['cpus'][0] >= 0, 'native service needs one actual physical worker core')
    for key in ('binary_sha256', 'machine_sha256'):
        require(re.fullmatch('[0-9a-f]{64}', str(context.get(key))), 'native service missing ' + key)
    source = context['source_sha256']
    require(set(source) == {'CpuServiceWork.h', 'CpuServiceTimer.cpp', 'CpuServiceCount.cpp'} and all(re.fullmatch('[0-9a-f]{64}', str(v)) for v in source.values()), 'native service shared source identities differ')
    libraries = context.get('loaded_libraries', {})
    require(isinstance(libraries, dict) and any(k.startswith('libstdc++') for k in libraries) and any(k.startswith('libc.so') for k in libraries), 'native service C/C++ ABI identities unavailable')
    require(all(isinstance(v, dict) and re.fullmatch('[0-9a-f]{64}', str(v.get('sha256'))) for v in libraries.values()), 'native service runtime hash missing')
    require(len(raw['services']) == 1 and raw['services'][0]['id'] == 'clock.now', 'native service supports the counted clock construction only')
    service = raw['services'][0]
    require(len(service['trials']) == settings['repetitions'] and all(type(t.get('events')) is int and 0 < t['events'] <= 134217728 for t in service['trials']), 'native service event workload exceeds its construction cap')
    proof = service['denominator'].get('proof')
    require(isinstance(proof, dict) and proof.get('format') == 'swdb.cpu-service-count-proof.v1', 'native service requires separate counted numerator proof')
    require(proof['source_sha256'] == source['CpuServiceWork.h'] and proof['count_driver_sha256'] == source['CpuServiceCount.cpp'], 'native timed/count shared source differs')
    require(proof['pipeline'] == {'version': 'source-normalized-v2', 'passes': ['function(sroa,mem2reg),cgscc(inline),function(loop-simplify)']}, 'native service count recipe differs')
    require(proof['service_validation_points'] == [[32,32],[64,64],[96,96]] and proof['driver_validation_points'] == [[32,0],[64,0],[96,0]], 'native service event count coefficient differs')
    require(len(proof['characterization_sha256']) == 6 and all(re.fullmatch('[0-9a-f]{64}', str(v)) for v in proof['characterization_sha256']), 'native service lacks six count receipt identities')
    require(bool(proof.get('event_abi')) and all(re.fullmatch('[0-9a-f]{64}', str(proof.get(k))) for k in ('plugin_source_sha256', 'runtime_source_sha256')), 'native service ABI/observer identity missing')
    require(service['unit'] == 'seconds/call' and service['denominator']['level'] == 'source_normalized_work', 'native service unit/denominator differs')

