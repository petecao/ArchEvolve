#!/usr/bin/env python3
"""One fresh a3 author witness after both scheduled batches. Created: 2026-09-26 ET.

This driver never resumes a2, reparses/promotes a1, retries, or claims a gain.
The coordinator must wrap it in TERM at 1170s / KILL after 30s through socket_lane.sh.
"""
import argparse
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.bfs_process import interruption_signals, run_stage, save_receipt
from scripts.dx100_trace_probe import PRIOR_ID
from scripts.dx100_witness_probe import validate_request as validate_original
from swdb import artifacts, dx100_witness, profile, yamlio
from swdb.store import Store

PROBE_ID = 'bfs-dx100-witness-20260926-a3'
FAILED_ID = 'bfs-dx100-witness-20260926-a1'
EXPIRED_ID = 'bfs-dx100-witness-20260926-a2'
FAILED_SHA256 = '9a941cdff315e283b13563bf81ef2f45ba0712bbcf6d31b92f6232488efa3b42'
REQUEST_SHA256 = 'ff0f415ba5e4fc3ac36b36bb32aa782ca875bcc3e5cc1d185b629a9f6e01ebbd'
REQUEST = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/requests/dx100-witness-a3.yaml'
RAW_ROOT = Path('/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925')
DIAGNOSIS = {'path': '/data/yanruj/EvolveSWDB_runs/bfs-dx100-bringup-20260925/'
             'bfs-dx100-witness-20260926-a1-diagnostic-reparse-20260926.json',
             'sha256': '2d7d011e238f06954757fa426dc527bdec54504ffd6fd1890c542b4955f4a7b5'}
DEADLINE = datetime(2026, 9, 26, 15, 40, tzinfo=ZoneInfo('America/New_York'))
OUTER_SECONDS, CLEANUP_SECONDS, CLI_SECONDS = 1200, 30, 1150
BATCHES = {'paired': ('bfs-native-paired-pilot-20260926-a1', 1, {'complete', 'failed'}),
           'provider': ('bfs-provider-initial-20260926-a1', 0,
                        {'initial_submissions_finished', 'failed_or_interrupted'})}
LEASE_GENERATIONS = {'paired': 400, 'provider': 318}
LAUNCHER_IDENTITIES = {'paired': (3034758, 493754291), 'provider': (3033637, 493713694)}
RUNTIME = {'swdb/dx100_witness.py': '2d589162b6595fee0abf4f1db54aa5b1a0964dab3f51aa408ac06505b6014091',
           'scripts/dx100_verify.py': '371657977d56816a37f4885f19923f37175331d2d15b5d7f6e6049d3fa8c1395',
           'scripts/dx100_host_memory.py': '655c5804e26a0d1f8f7738f23ae62268cafe84562dbf8392af6c0169568146fd'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def now():
    return datetime.now(DEADLINE.tzinfo)


def stamp(value):
    require(isinstance(value, str), 'terminal timestamp is missing')
    result = datetime.fromisoformat(value)
    require(result.utcoffset() is not None, 'terminal timestamp must include its zone')
    return result


def launch_budget(current):
    require(current.utcoffset() is not None and (DEADLINE - current).total_seconds() >= OUTER_SECONDS,
            'a3 requires the full 1200-second window; latest launch is 15:20 ET')
    return OUTER_SECONDS - CLEANUP_SECONDS


def reference(ref, limit=2 * 1024**2):
    require(isinstance(ref, dict) and isinstance(ref.get('path'), str)
            and isinstance(ref.get('sha256'), str) and re.fullmatch('[a-f0-9]{64}', ref['sha256']),
            'terminal artifact needs an exact path and SHA-256')
    path = Path(ref['path'])
    require(path.is_absolute() and path.is_file() and not path.is_symlink()
            and path.stat().st_size <= limit, 'terminal artifact is missing, unsafe, or oversized')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, 'terminal artifact is oversized')
    require(hashlib.sha256(raw).hexdigest() == ref['sha256'], 'terminal artifact hash changed')
    return raw


def verify_terminal_processes(identities, proc=Path('/proc'), *, launcher_identity=None):
    require(isinstance(identities, list) and identities, 'terminal audit lacks owned process identities')
    seen = set()
    zombies = 0
    for row in identities:
        require(isinstance(row, dict) and type(row.get('pid')) is int and row['pid'] > 0
                and type(row.get('start_ticks')) is int and row['start_ticks'] >= 0,
                'terminal process identity is malformed')
        key = (row['pid'], row['start_ticks'])
        require(key not in seen, 'terminal audit repeats a process identity')
        seen.add(key)
        retained_zombie = row.get('state') == 'Z'
        if retained_zombie:
            zombies += 1
            require(key == launcher_identity and zombies == 1 and row.get('role') == 'tmux_launcher'
                    and type(row.get('rss_bytes')) is int and row['rss_bytes'] == 0,
                    'only one retained zero-RSS tmux launcher zombie is allowed')
        elif launcher_identity is not None:
            require(row.get('state') == 'absent', 'other owned identities must be retained as absent')
        folder = proc / str(row['pid'])
        try:
            fields = (folder / 'stat').read_text().rsplit(')', 1)[1].split()
            start_ticks = int(fields[19])
        except FileNotFoundError:
            require(not folder.exists(), 'owned process identity cannot be checked')
            continue
        except (IndexError, ValueError):
            raise ValueError('owned process identity cannot be checked') from None
        if start_ticks == row['start_ticks']:
            if retained_zombie:
                require(fields[0] == 'Z' and len(fields) > 21 and fields[21] == '0',
                        'retained tmux launcher is live or has nonzero RSS')
            else:
                require(False, 'a prior owned batch process still exists')
    require(launcher_identity is None or zombies == 1, 'terminal audit must retain its launcher zombie identity')


def verify_identity_coverage(audit, driver, kind):
    observations = json.loads(reference(audit['process_observations']))
    ancestors = observations.get('ancestry')
    require(isinstance(ancestors, list) and ancestors, 'terminal audit lacks retained owned ancestry')
    rows = ancestors + observations.get('owned_processes', [])
    sample_ref = driver['rss']['samples'] if kind == 'paired' else driver['resource_artifact']
    samples = [json.loads(line) for line in reference(sample_ref, 16 * 1024**2).splitlines() if line.strip()]
    require(samples and all(isinstance(sample.get('processes'), list) and sample['processes']
                            for sample in samples), 'terminal audit lacks owned process samples')
    sampled = [row for sample in samples for row in sample['processes']]
    rows += sampled
    require(all(isinstance(row, dict) and type(row.get('pid')) is int and row['pid'] > 0
                and type(row.get('start_ticks')) is int and row['start_ticks'] >= 0 for row in rows),
            'retained process ownership is malformed')
    if kind == 'paired':
        require(type(driver.get('driver_pid')) is int and any(row['pid'] == driver['driver_pid'] for row in sampled),
                'paired resource samples omit the driver identity')
    expected = {(row['pid'], row['start_ticks']) for row in rows}
    declared = {(row['pid'], row['start_ticks']) for row in audit['owned_processes']}
    require(expected <= declared, 'terminal audit omits retained owned process identities')
    if audit['state'] == 'terminal_no_live_owned_processes':
        require(LAUNCHER_IDENTITIES[kind] in {(row['pid'], row['start_ticks']) for row in ancestors},
                'retained launcher zombie is missing from owned ancestry')
    return {'process_observations': audit['process_observations'], 'resource_samples': sample_ref}


def validate_completion(ref, kind, current, proc=Path('/proc')):
    audit = json.loads(reference(ref))
    identity, node, terminal_states = BATCHES[kind]
    allow_zombie = audit.get('state') == 'terminal_no_live_owned_processes'
    cleanup = (audit.get('owned_processes_absent') is False and audit.get('owned_processes_nonrunning') is True
               if allow_zombie else audit.get('state') == 'terminal_and_reaped'
               and audit.get('owned_processes_absent') is True)
    require(audit.get('id') == identity and cleanup and audit.get('lease_released') is True,
            'batch completion audit does not attest terminal cleanup')
    driver = json.loads(reference(audit['driver']))
    lane = json.loads(reference(audit['lane']))['socket_lane']
    exit_text = reference(audit['outer_exit'], 64).decode().strip()
    require(re.fullmatch(r'-?\d+', exit_text) is not None, 'outer exit code is malformed')
    require(driver.get('id') == identity and driver.get('state') in terminal_states,
            'prior batch driver is not terminal')
    require(lane.get('host') == 'mbit10' and type(lane.get('node')) is int and lane['node'] == node
            and lane.get('lease_name') == f'mbit10-evaluation-node{node}'
            and type(lane.get('lease_generation')) is int and lane['lease_generation'] == LEASE_GENERATIONS[kind]
            and type(lane.get('exit_code')) is int and lane['exit_code'] == int(exit_text),
            'terminal lane/outer exit identity differs')
    began, finished = stamp(driver.get('started')), stamp(driver.get('finished'))
    lane_began, lane_ended = stamp(lane.get('started_utc')), stamp(lane.get('ended_utc'))
    observed = stamp(audit.get('observed_at'))
    # socket_lane.sh truncates its UTC stamps to whole seconds.
    require(lane_began <= began <= finished < lane_ended + timedelta(seconds=1)
            and finished <= observed <= current and lane_ended <= observed,
            'prior batch completion timestamps do not precede a3')
    require(all(row.get('state') != 'running' for row in driver.get('stages', []))
            and all(row.get('state') != 'running' for row in driver.get('cells', [])),
            'prior batch retains an active stage or cell')
    launcher_identity = LAUNCHER_IDENTITIES[kind] if allow_zombie else None
    verify_terminal_processes(audit.get('owned_processes'), proc, launcher_identity=launcher_identity)
    ownership = verify_identity_coverage(audit, driver, kind)
    return {'audit': ref, 'id': identity, 'state': driver['state'], 'finished': driver['finished'],
            'lane': audit['lane'], 'outer_exit': audit['outer_exit'], 'driver': audit['driver'],
            'observed_at': audit['observed_at'], 'owned_processes': audit['owned_processes'],
            'cleanup_state': audit['state'], 'launcher_identity': launcher_identity, **ownership}


def validate_history(records, runs):
    failed = records / 'evaluations' / (FAILED_ID + '.yaml')
    require(failed.is_file() and artifacts.file_hash(failed) == FAILED_SHA256,
            'a3 requires the unchanged retained failed a1 record')
    for rid in (EXPIRED_ID, PROBE_ID):
        paths = [records / 'evaluations' / (rid + '.yaml'), runs / rid, runs / (rid + '.driver')]
        require(not any(path.exists() or path.is_symlink() for path in paths),
                f'{rid} record/output already exists; historical evidence cannot be overwritten or resumed')
    return failed


def validate_request(request, prior):
    require(artifacts.digest(request) == REQUEST_SHA256, 'a3 request differs from its exact prospective identity')
    validate_original(request, prior, probe_id=PROBE_ID)


def validate_diagnosis():
    # This exact receipt is a read-only parse of retained a1, never a new verdict.
    diagnostic = json.loads(reference(DIAGNOSIS))
    require(diagnostic.get('kind') == 'diagnostic_reparse'
            and diagnostic.get('no_execution') is True and diagnostic.get('no_historical_promotion') is True
            and diagnostic.get('source_record', {}).get('sha256') == FAILED_SHA256
            and diagnostic.get('diagnostic_parser', {}).get('sha256') == RUNTIME['swdb/dx100_witness.py']
            and diagnostic.get('original_outcome', {}).get('state') == 'failed'
            and diagnostic.get('diagnostic_result', {}).get('completed') is True,
            'pinned a1 reparse does not establish the required diagnosis')


def main():
    started, started_at = time.monotonic(), now()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--lane', type=int, choices=[0], required=True)
    for kind in BATCHES:
        parser.add_argument('--' + kind + '-completion', type=Path, required=True)
        parser.add_argument('--' + kind + '-sha256', required=True)
    args = parser.parse_args()
    allowance = launch_budget(started_at)
    deadline = started + allowance
    require(socket.gethostname().split('.')[0] == 'mbit10', 'a3 execution requires mbit10')
    runs = args.runs_dir.resolve()
    require(runs == RAW_ROOT,
            'a3 uses its fixed historical raw root')
    records = ROOT / 'records'
    failed = validate_history(records, runs)
    store = Store(records)
    request = yamlio.load(REQUEST)
    validate_request(request, store.get(PRIOR_ID, 'evaluation') or {})
    for path, digest in RUNTIME.items():
        require(artifacts.file_hash(ROOT / path) == digest, 'a3 verifier runtime differs from the reviewed correction')
    validate_diagnosis()
    barriers = {kind: validate_completion({'path': str(getattr(args, kind + '_completion').absolute()),
        'sha256': getattr(args, kind + '_sha256')}, kind, now()) for kind in BATCHES}
    machine = store.get('mbit10', 'machine')
    lane = profile._verified_lane(machine, 'mbit10-evaluation-node0')
    launch_budget(now())
    folder = runs / (PROBE_ID + '.driver')
    folder.mkdir(exist_ok=False)
    receipt = {'id': PROBE_ID, 'created': '2026-09-26', 'state': 'running', 'started': started_at.isoformat(),
        'purpose': 'one new author v2 completion execution; no acceleration coverage or gain claim',
        'deadline_et': DEADLINE.isoformat(), 'outer_seconds': OUTER_SECONDS, 'cleanup_reserve_seconds': CLEANUP_SECONDS,
        'automatic_retry_allowed': False, 'gain_claim': False, 'lane': lane, 'stages': [],
        'prior_failure': {'path': str(failed), 'sha256': FAILED_SHA256}, 'expired_a2_executed': False,
        'request': {'path': str(REQUEST), 'sha256': artifacts.file_hash(REQUEST), 'canonical_sha256': REQUEST_SHA256},
        'runtime_sha256': RUNTIME, 'diagnostic_reparse': DIAGNOSIS, 'batch_completion': barriers}
    save_receipt(folder, receipt)
    try:
        receipt['repository_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                                               text=True, timeout=10).strip()
        run_stage(receipt, folder, [sys.executable, str(ROOT / 'scripts/dx100_capacity.py'), '--node', '0',
            '--output', str(folder / 'capacity-inside.json')], timeout=30, deadline=deadline, cwd=ROOT)
        require(artifacts.file_hash(failed) == FAILED_SHA256, 'retained a1 failure changed during preflight')
        for value in barriers.values():
            verify_terminal_processes(value['owned_processes'], launcher_identity=value['launcher_identity'])
        launch_budget(now())
        path = folder / 'request.json'
        path.write_text(json.dumps(request, indent=2) + '\n')
        output = folder / 'evaluation.stdout.json'
        run_stage(receipt, folder, [sys.executable, '-m', 'swdb', 'dx100-execute', str(path),
            '--records', str(records), '--runs-dir', str(runs), '--lane', '0', '--format', 'json'],
            output=output, stderr=folder / 'evaluation.stderr', timeout=CLI_SECONDS, deadline=deadline, cwd=ROOT)
        result = json.loads(output.read_text())
        require(result.get('id') == PROBE_ID and artifacts.digest(result.get('request')) == REQUEST_SHA256
                and result.get('gain_claim') is False, 'public evaluation identity differs from the fixed a3 request')
        dx100_witness.validate_completed_witness(result, verify_artifacts=True)
        require(now() <= DEADLINE and time.monotonic() - started <= allowance, 'a3 completion exceeded its fixed window')
        receipt.update(state='complete', evaluation=PROBE_ID, evaluation_sha256=artifacts.digest(result))
    except BaseException as exc:
        receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        receipt.update(finished=now().isoformat(), host_wall_s=time.monotonic() - started,
                       prior_failure_preserved=failed.is_file() and artifacts.file_hash(failed) == FAILED_SHA256)
        if not receipt['prior_failure_preserved']:
            receipt.update(state='failed', reason='retained a1 failure changed')
        save_receipt(folder, receipt)
    require(receipt['state'] == 'complete', receipt.get('reason', 'a3 execution failed'))
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    with interruption_signals():
        main()
