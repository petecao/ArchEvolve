"""2026-10-16 ET. Compact root receipt for the exact settled30-control run.

Read retained metadata only. Never launch a compiler/verifier, copy raw payload,
change a lease, or infer a watchdog field that was not recorded.
"""
from pathlib import Path
import datetime
import hashlib
import json
import os
import xml.etree.ElementTree as ET

RAW = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-dcdecf31-t25-pair-pointer-controls-v2')
SOURCE = 'dcdecf317a0e9b34f3ce12d5b914eb823c439fbc'
CAP = 8589934592

def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def load(name):
    path = RAW/name
    assert path.stat().st_size < 128000
    return json.loads(path.read_bytes())

actual = {name: load(name) for name in ('lane.json', 'launch.json', 'outer-resources.json',
          'resources.json', 'focus-result.json', 'source-after.json')}
lane = actual['lane.json']['socket_lane']
assert lane['exit_code'] == 0 and lane['ended_utc'] and lane['lease_generation'] == 615 and lane['node'] == 0
launch = actual['launch.json']
assert launch['source_commit'] == SOURCE and launch['rss_cap_bytes'] == CAP and launch['workers'] == 1
assert launch['timeout_seconds'] == 1200
assert hashlib.sha256(launch['command'][-1].encode()).hexdigest() == 'dfa74eb143f71f7a703cb7346d9d9dafa1c6ff11dbd92997c515aea308e44011'
for name in ('outer-resources.json', 'resources.json'):
    row = actual[name]
    assert row['exit_code'] == 0 and not row['out_of_memory'] and not row['timed_out']
    assert row['peak_rss_bytes'] <= CAP
census = actual['focus-result.json']
assert census['exit_code'] == 0 and census['cases'] == 30 and not any(census[k] for k in ('failures', 'errors', 'skips'))
assert census['cache_absent'] is True and actual['source-after.json']['source_unchanged'] is True
assert actual['source-after.json']['commit'] == SOURCE
junit = ET.parse(RAW/'junit.xml').getroot()
cases = list(junit.iter('testcase'))
assert len(cases) == 30 and not any(list(junit.iter(k)) for k in ('failure', 'error', 'skipped'))
for name, digest in {'execute.py': 'ea774376014605a6ad31356a35abccef729f42e327ce07f4075853743dbcb612',
                     'watch.py': '4485ae66aa50c65f2b579f84836576aa67b54431978da71cac6eea6a68ecd07c'}.items():
    assert pin(RAW/name)['sha256'] == digest
selected, failures, races = [], [], []
for proc in Path('/proc').iterdir():
    if not proc.name.isdecimal():
        continue
    try:
        if proc.stat().st_uid != os.getuid():
            continue
        # Finite selected-name scan, not a universal absence assertion. This
        # does not inspect inaccessible OS-session cwd/environ/fd surfaces.
        command = (proc/'cmdline').read_bytes().replace(b'\0', b' ')
        if str(RAW).encode() in command:
            selected.append({'pid': int(proc.name), 'selected_raw_reference': True})
    except FileNotFoundError:
        races.append(int(proc.name))
    except PermissionError:
        failures.append(int(proc.name))
assert not selected and not failures, {'selected': selected, 'read_failures': failures}
leases = {p.name: json.loads(p.read_bytes()) for p in Path('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')}
files = [p for p in RAW.rglob('*') if p.is_file() and not p.is_symlink()
         and not any(q.is_symlink() for q in p.parents if q != RAW)]
names = ['lane.json', 'launch.json', 'resources.json', 'outer-resources.json', 'source-after.json',
         'focus-result.json', 'junit.xml', 'execute.py', 'watch.py', 'run.sh', 'dispatch-argv.json']
result = {'date': '2026-10-16 ET', 'observed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'status': 'ROOT_CONTROLS_PASSED', 'source_commit': SOURCE, 'raw_root': str(RAW),
    'cases': 30, 'failures': 0, 'errors': 0, 'skips': 0, 'cache_absent': True,
    'guard': {**actual['resources.json'], 'rss_cap_bytes': CAP, 'workers': 1, 'whole_seconds': 1200},
    'outer': actual['outer-resources.json'], 'actual': actual,
    'formal_WP_CBMC_disabled': True, 'actual_flags': {'SWDB_PAIR_ACTUAL': '0', 'SWDB_MIXED_PAIR_ACTUAL': '0'},
    'physical_metadata_pins': {name: pin(RAW/name) for name in names},
    'raw_files': len(files), 'raw_bytes': sum(p.stat().st_size for p in files),
    'finite_selected_process_scan': {'selected': selected, 'read_failures': failures, 'exited_races': races,
       'scope': 'Owned cmdline references to this exact raw root only; no universal or inaccessible-private-surface claim'},
    'leases_at_observation': leases,
    'watchdog_boundary': 'Successful retained guard/outer results and exact wrapper bytes; no separately recorded final-null field is invented.',
    'scope': '11 pure initializedness cases and19 actual Clang/native/explicit parser-error stand-in controls. No formal WP/CBMC or eight-record/full-ticket acceptance.',
    'raw_payload_transferred': False}
print(json.dumps(result, indent=2))
