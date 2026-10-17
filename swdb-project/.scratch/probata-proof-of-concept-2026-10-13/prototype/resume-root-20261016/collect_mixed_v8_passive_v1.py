"""2026-10-16 ET. Read-only mixed V8 settlement metadata, no science rerun."""
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import stat
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-36266e10-mixed-pair-public-v8')
SOURCE = Path('/data1/yanruj/probata-resume-20261016-36266e10')
SHA = '36266e101e0484f3c2cf5f3fae4322d5de648d85'
PROFILE = RAW / 'mixed-pair-profile'
signal.alarm(180)
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
START = time.monotonic()


def need(value, text):
    if not value:
        raise ValueError(text)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def pin(path):
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode), 'physical regular hash input')
    h = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        count = 0
        while True:
            block = os.read(fd, 1048576)
            if not block:
                break
            h.update(block)
            count += len(block)
        after = os.fstat(fd)
        need((before.st_ino, before.st_size, before.st_mtime_ns) ==
             (after.st_ino, count, after.st_mtime_ns), 'stable hash input')
    finally:
        os.close(fd)
    return {'bytes': count, 'sha256': h.hexdigest()}


def data(path, cap=4 * 1024**2):
    st = path.lstat()
    need(stat.S_ISREG(st.st_mode) and st.st_size <= cap, 'bounded physical metadata read')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        value = b''
        while len(value) <= cap:
            block = os.read(fd, min(1048576, cap + 1 - len(value)))
            if not block:
                break
            value += block
        need(len(value) == st.st_size <= cap, 'complete metadata read')
    finally:
        os.close(fd)
    return value


def read(path):
    return json.loads(data(path))


def git(root, *args):
    return subprocess.check_output(['/usr/bin/git', '--no-replace-objects', '--no-optional-locks',
        '-c', 'core.fsmonitor=false', '-c', 'core.preloadIndex=false', '-c', 'index.threads=1',
        '-C', str(root), *args], timeout=20).decode().strip()


def census():
    rows, pending, total = [], [RAW], 0
    while pending:
        root = pending.pop()
        need(stat.S_ISDIR(root.lstat().st_mode), 'physical traversed raw directory')
        with os.scandir(root) as stream:
            children = sorted(stream, key=lambda entry: entry.name)
        for item in children:
            path = root / item.name
            st = path.lstat()
            row = {'relative': str(path.relative_to(RAW)), 'mode': st.st_mode, 'inode': st.st_ino,
                   'mtime_ns': st.st_mtime_ns, 'bytes': st.st_size}
            if stat.S_ISDIR(st.st_mode):
                row['kind'] = 'directory'
                pending.append(path)
            elif stat.S_ISREG(st.st_mode):
                row.update(kind='regular', **pin(path))
                total += st.st_size
            elif stat.S_ISLNK(st.st_mode):
                row.update(kind='symlink', literal_target=os.readlink(path))
            else:
                row['kind'] = 'special'
            rows.append(row)
            need(len(rows) <= 20000 and total <= 268435456, 'closed raw metadata extent cap')
    return sorted(rows, key=lambda row: Path(row['relative']).parts)


def record_summary(row):
    goals = row.get('goals', [])
    return {'id': row.get('id'), 'subject': row.get('subject'), 'adapter': row.get('job', {}).get('adapter'),
        'verdict': row.get('verdict'), 'failure_class': row.get('failure_class'),
        'evidence_kind': row.get('evidence_kind'), 'pins': row.get('pins'),
        'goal_status_census': dict(Counter(('smoke:' if g.get('smoke') else 'ordinary:') + str(g.get('status')) for g in goals)),
        'goals': [{k: g[k] for k in ('goal', 'property', 'function', 'line', 'smoke', 'status', 'solver', 'seconds') if k in g} for g in goals],
        'unproven_properties': row.get('unproven_properties'),
        'assumptions': row.get('assumptions'),
        'agreement': row.get('settings', {}).get('agreement'), 'forms': row.get('settings', {}).get('forms'),
        'rss_cap_bytes': row.get('settings', {}).get('rss_cap_bytes'),
        'counterexample_replay': {k: v for k, v in row.get('counterexample', {}).get('replay', {}).items()
                                  if k in ('replayed', 'verdict', 'exit_code', 'returncode', 'reason')}}


def main():
    leases = {}
    for name in ('mbit10-evaluation-node0', 'mbit10-evaluation-node1', 'mbit10-evaluation'):
        leases[name] = read(Path('/data1/yanruj/lact-host-lease') / (name + '.meta.json'))
    preflight = {'leases': leases, 'load': os.getloadavg(), 'uptime': Path('/proc/uptime').read_text()[:128].strip(),
        'disk_free': {p: os.statvfs(p).f_bavail * os.statvfs(p).f_frsize for p in ('/data1', '/data')},
        'evaluated_source': {'branch': git(SOURCE, 'rev-parse', '--abbrev-ref', 'HEAD'), 'sha': git(SOURCE, 'rev-parse', 'HEAD')},
        'primary_source': {'branch': git(Path('/data1/yanruj/ArchEvolve'), 'rev-parse', '--abbrev-ref', 'HEAD'),
                           'sha': git(Path('/data1/yanruj/ArchEvolve'), 'rev-parse', 'HEAD')}}
    initial = census()
    metadata = {}
    for path in sorted(RAW.glob('*.json')):
        if path.name in {'launch.json', 'mixed-linux-admission.json', 'mixed-project-runtime.json',
                         'mixed-source-before.json', 'mixed-source-after.json', 'mixed-native-runtime-before.json',
                         'mixed-native-runtime-after.json'}:
            value = read(path)
            if path.name == 'launch.json':
                value = {key: value.get(key) for key in ('source_commit', 'source', 'node', 'timeout_seconds', 'rss_cap_bytes',
                                                       'workers', 'reviewed_wrapper_reuse', 'raw_root')}
            elif path.name in ('mixed-source-before.json', 'mixed-source-after.json'):
                value = {key: value.get(key) for key in ('count', 'total_bytes', 'trees', 'source_commit')}
            elif path.name == 'mixed-project-runtime.json':
                value = {key: value.get(key) for key in ('lowering_identity', 'model_hashes', 'source_checker_identities', 'scope')}
            elif path.name.startswith('mixed-native-runtime'):
                value = {'top_level_keys': list(value), 'complete_value_digest': sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())}
            else:
                value = {key: value.get(key) for key in ('source_commit', 'actual_socket_affinity', 'rss_cap_bytes', 'node')}
        else:
            value = read(path)
        metadata[path.name] = {**pin(path), 'value': value}
    progress_paths = [RAW / r['relative'] for r in initial if r['kind'] == 'regular' and Path(r['relative']).name == 'actual-mixed-pair-progress.json']
    progress = []
    if len(progress_paths) == 1:
        progress = read(progress_paths[0])
    record_paths = [RAW / r['relative'] for r in initial if r['kind'] == 'regular' and '/records/proofs/' in r['relative'] and r['relative'].endswith('.yaml')]
    physical = []
    if record_paths:
        import yaml
        physical = [yaml.safe_load(data(path)) for path in record_paths]
    by_id = {row['id']: row for row in physical}
    agreement = bool(progress) and len(progress) == len(physical) and all(by_id.get(row['id']) == row for row in progress)
    junit = None
    junit_path = PROFILE / 'junit.xml'
    if junit_path.exists():
        root = ET.fromstring(data(junit_path))
        cases = list(root.iter('testcase'))
        junit = {**pin(junit_path), 'cases': len(cases), 'failures': len(list(root.iter('failure'))),
                 'errors': len(list(root.iter('error'))), 'skips': len(list(root.iter('skipped'))),
                 'case_names': [c.attrib for c in cases],
                 'failure_messages': [{k: n.attrib[k][:1024] for k in ('type', 'message') if k in n.attrib}
                                      for n in list(root.iter('failure')) + list(root.iter('error'))]}
    logs = {}
    for path in (RAW / 'acceptance.log', RAW / 'worker.log', PROFILE / 'pytest.log', PROFILE / 'progress-observer.jsonl'):
        if path.exists():
            text = data(path, 4 * 1024**2).decode(errors='replace')
            lines = [line[:1024] for line in text.splitlines() if re_status(line)]
            logs[str(path.relative_to(RAW))] = {**pin(path), 'status_lines': lines[-24:]}
    current_tools = []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            comm = (process / 'comm').read_text().strip()
            if comm in {'frama-c', 'frama-c.exe', 'alt-ergo', 'why3server', 'z3', 'cvc5', 'cbmc', 'clang-22', 'pytest'}:
                current_tools.append({'pid': int(process.name), 'comm': comm})
        except (FileNotFoundError, ProcessLookupError):
            continue
    final = census()
    need(initial == final, 'settled raw remained byte-identical during collection')
    output = {'schema': 'mixed-v8-passive-settlement-1', 'date': '2026-10-16 ET', 'raw_root': str(RAW),
        'source_commit': SHA, 'preflight': preflight, 'current_selected_tools': current_tools,
        'raw_manifest': initial, 'raw_pre_post_equal': True,
        'raw_type_counts': dict(Counter(r['kind'] for r in initial)),
        'regular_bytes': sum(r['bytes'] for r in initial if r['kind'] == 'regular'),
        'metadata': metadata, 'junit': junit, 'progress_path_count': len(progress_paths),
        'progress_pin': pin(progress_paths[0]) if len(progress_paths) == 1 else None,
        'progress_records': [record_summary(row) for row in progress],
        'physical_records': [{'relative': str(path.relative_to(RAW)), **pin(path)} for path in record_paths],
        'progress_and_physical_records_equal': agreement, 'logs': logs,
        'current_source_clean': git(SOURCE, 'status', '--porcelain', '--untracked-files=all') == '',
        'scope': 'Read-only producer/JUnit/eight-record/guard/retention metadata collection; no cold proof-term, import or hypothesis semantic acceptance; no rerun or remote mutation.',
        'elapsed_seconds': time.monotonic() - START}
    encoded = json.dumps(output, sort_keys=True, indent=2, allow_nan=False).encode() + b'\n'
    need(len(encoded) <= 2 * 1024**2, 'compact output cap')
    sys.stdout.buffer.write(encoded)


def re_status(line):
    return any(token in line for token in ('passed', 'failed', 'error', 'ERROR', 'FAILED', 'PRODUCER_', 'REFUSED',
                                          '"records"', '"status"', '"primary_error"', '"reason"'))


if __name__ == '__main__':
    main()
