#!/usr/bin/env python3
"""Three bounded Linux process-contract selections. Created 2026-09-26 ET.

This supervisor never runs an empirical workload or asserts independent terminal
cleanup. Every selection has one original 90-second clock and no retry.
"""
import argparse
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import resource
import socket
import sys
import time
import xml.etree.ElementTree as XML

PYTHON_INPUTS = {**dict.fromkeys(('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','PYTHONUSERBASE',
    'PYTHONOPTIMIZE','PYTEST_ADDOPTS','PYTEST_PLUGINS','LD_PRELOAD','LD_LIBRARY_PATH')), 'PYTHONNOUSERSITE':'1',
    'PYTHONDONTWRITEBYTECODE':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'}
if __name__ == '__main__':
    if (any(os.environ.get(key) != value for key,value in PYTHON_INPUTS.items())
            or not sys.flags.no_user_site or sys.flags.optimize != 0):
        raise SystemExit('fixture runner requires the declared isolated Python environment with assertions enabled')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import bfs_owned_execution as own
from scripts.bfs_process import interruption_signals, save_receipt
from scripts.bfs_native_campaign import campaign_runtime
from scripts.bfs_simulator_batch import CLEANUP_RUNTIME, allocated_bytes, lease_observation
from swdb import artifacts
from swdb.store import Store

LIMIT_BYTES = 512 * 1024**2
SELECTIONS = {
    'owned_cleanup': ('bfs-simulator-owned-linux-20260927-a8',
        ['tests/test_bfs_owned_execution.py', '-k', 'linux'], {
            'test_linux_owned_stage_reaps_detached_child[False]',
            'test_linux_owned_stage_reaps_detached_child[True]',
            'test_linux_nested_interruption_uses_one_cleanup_budget',
            'test_linux_term_resistant_nested_cleanup_keeps_final_kill_reserve',
            'test_linux_storage_observation_handles_sqlite_journal_unlink'}),
    'dx100_interruption': ('bfs-simulator-interruption-linux-20260927-a8',
        ['tests/test_dx100_interruption.py::test_public_interruption_is_durable_before_postmortem'], {
            'test_public_interruption_is_durable_before_postmortem[raises]',
            'test_public_interruption_is_durable_before_postmortem[stalls]'}),
    'native_campaign_owned_cleanup': ('bfs-native-campaign-owned-linux-20260927-b2',
        ['tests/test_bfs_native_execution.py::test_linux_campaign_reaps_detached_child'], {
            'test_linux_campaign_reaps_detached_child[False]',
            'test_linux_campaign_reaps_detached_child[True]'})}
RAW_BASE = Path('/data/yanruj/EvolveSWDB_runs')


def require(value, reason):
    if not value: raise ValueError(reason)


def stamp(value):
    result = datetime.fromisoformat(value)
    require(result.utcoffset() is not None, 'fixture clock needs explicit zone')
    return result


def reference(path):
    return {'path': str(Path(path).absolute()), 'sha256': artifacts.file_hash(path)}


def junit_cases(path, expected):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 4*1024**2,
            'fixture JUnit missing, unsafe or oversized')
    cases = XML.fromstring(path.read_bytes()).findall('.//testcase')
    names = [case.get('name') for case in cases]
    require(len(names) == len(expected) and set(names) == expected and all(
        not any(case.find(key) is not None for key in ('failure', 'error', 'skipped')) for case in cases),
        'fixture selection failed, skipped, duplicated or omitted a required case')
    return names


def command(kind, folder):
    return [sys.executable, '-m', 'pytest', *SELECTIONS[kind][1], '-q', '-p', 'no:cacheprovider',
            '--junitxml='+str(folder/'junit.xml'), '--basetemp='+str(folder/'pytest')]


def child_environment(folder):
    env = dict(os.environ)
    for key,value in PYTHON_INPUTS.items():
        if value is None: env.pop(key,None)
        else: env[key]=value
    env['TMPDIR']=str(folder/'tmp')
    return env


def pytest_identity():
    import pytest
    return {'version':pytest.__version__,'module':reference(Path(pytest.__file__).resolve())}


def _execute(kind, folder, begin, end, deadline, code, runtime, pane, lane, pytest_runtime, *, supplement=False):
    """Test seam uses real stage orchestration; main owns fixed host/path admission."""
    if supplement:
        rid, args, expected_cases = supplement_configuration(folder)
        from scripts.bfs_simulator_batch import runtime_identity
        supplement_runtime = runtime_identity()
    else:
        rid, args, expected_cases = SELECTIONS[kind][0], command(kind,folder), SELECTIONS[kind][2]
    folder.mkdir(parents=True, exist_ok=False); (folder/'tmp').mkdir()
    budget_path = folder/'cleanup-ledger.json'
    binding = own.SharedCleanup.create(budget_path, end.isoformat(), deadline=deadline)
    budget = own.SharedCleanup(budget_path, binding, deadline)
    owner = own.Owned(budget)
    driver = own.identity(os.getpid())
    receipt = {'id': rid, 'created': '2026-09-26', 'state': 'running',
        'evidence_kind': 'contract_fixture', 'code_commit': code, 'kind': kind,
        'started': begin.isoformat(), 'outer_deadline': end.isoformat(), 'stages': [],
        'bounds': {'outer_seconds':90, 'work_seconds':60, 'cleanup_seconds':30,
                   'sampled_rss_bytes':LIMIT_BYTES, 'output_bytes':LIMIT_BYTES},
        'cleanup_verified': False, 'automatic_retry_allowed': False, 'runtime':runtime,
        'pytest':pytest_runtime, 'python_environment':PYTHON_INPUTS,
        'process_observations': {'driver_identity':driver, 'pane_identity':pane,
                                'ancestry':own.ancestry(driver,pane)},
        'cleanup_budget':{'path':str(budget_path),'binding':binding,'budget_seconds':30}}
    if supplement:
        receipt.update(kind='supervision_supplement',created='2026-09-27',runtime_sha256=supplement_runtime,
                       work_deadline=(begin+timedelta(seconds=60)).isoformat(),standard_proof_kind=False)
    samples = folder/'resources.jsonl'; machine = None; failure = None; guard = None
    def observe():
        require(time.monotonic() < deadline and datetime.now(own.ET) <= end, 'fixture original deadline exceeded')
        sample = owner.sample()
        require(sample['rss_bytes'] <= LIMIT_BYTES, 'fixture sampled RSS limit exceeded')
        used = allocated_bytes([folder]); require(used <= LIMIT_BYTES, 'fixture output limit exceeded')
        for root, reserve in ((RAW_BASE,30*1024**3),(Path('/data1'),10*1024**3)):
            fs = os.statvfs(root); require(fs.f_bavail*fs.f_frsize >= reserve, 'fixture free-space reserve violated')
        row = {**sample, 'output_bytes':used}
        if machine is not None: row['lane'] = lease_observation(machine,lane)
        with samples.open('a') as stream: stream.write(json.dumps(row)+'\n')
        return row
    try:
        guard = own.Monitor(observe); guard.start()
        machine = Store(ROOT/'records').get('mbit10')
        observe()
        require(campaign_runtime(code) == runtime and pytest_identity() == pytest_runtime, 'fixture runtime changed before dispatch')
        work_end = deadline-30
        require(time.monotonic() < work_end, 'fixture setup consumed work allowance')
        row = own.run_stage(receipt,folder,args,timeout=work_end-time.monotonic(),deadline=work_end,
            cwd=ROOT,owned=owner,monitor=guard.check,env=child_environment(folder),
            output=folder/'pytest.stdout',stderr=folder/'pytest.stderr')
        require(time.monotonic() < work_end, 'fixture readback has no remaining work allowance')
        receipt['testcases'] = junit_cases(folder/'junit.xml',expected_cases)
        if supplement: require(runtime_identity() == supplement_runtime, 'supplement runtime changed during tests')
        require(campaign_runtime(code) == runtime and pytest_identity() == pytest_runtime, 'fixture runtime changed during tests')
        require(time.monotonic() < work_end, 'fixture readback exceeded work allowance')
        receipt.update(state='complete',command=args,returncode=row['returncode'])
    except BaseException as exc:
        failure = exc; receipt.update(state='failed',reason=f'{type(exc).__name__}: {exc}')
    finally:
        if guard: guard.interrupt = False  # Keep telemetry during bounded teardown.
        try: receipt['cleanup'] = own.verified_finish(owner)
        except BaseException as exc:
            failure = failure or exc; receipt.update(state='failed',cleanup_error=f'{type(exc).__name__}: {exc}')
        try:
            if guard:
                with budget.reservation() as until: guard.stop(until)
        except BaseException as exc:
            failure = failure or exc; receipt.update(state='failed',monitor_shutdown_error=f'{type(exc).__name__}: {exc}')
        try:
            with budget.reservation():
                observe()
                receipt['process_observations']['owned_processes'] = list(owner.history.values())
                receipt['resource_samples'] = reference(samples)
                receipt['resource_validation'] = own.validate_samples(samples,begin.isoformat(),own.stamp())
                receipt['cleanup_accounting'] = budget.snapshot()
                receipt.update(finished=own.stamp(),elapsed_seconds=(datetime.now(own.ET)-begin).total_seconds())
                save_receipt(folder,receipt)
                observe()
                receipt['resource_samples'] = reference(samples)
                receipt['resource_validation'] = own.validate_samples(samples,begin.isoformat(),own.stamp())
                receipt['finished'] = own.stamp(); save_receipt(folder,receipt)
                require(time.monotonic() < deadline and allocated_bytes([folder]) <= LIMIT_BYTES,
                        'fixture final persistence exceeded bounds')
                if failure is None and not supplement:
                    proof = {'format':'swdb.bfs.linux-fixture.v1','kind':kind,'host':'mbit10','platform':'linux',
                        'evidence_kind':'contract_fixture','state':'tests_passed_cleanup_unverified','returncode':0,'code_commit':code,
                        'started':begin.isoformat(),'finished':receipt['finished'],'command':receipt['command'],
                        'stdout':reference(folder/'pytest.stdout'),'junit':reference(folder/'junit.xml'),
                        'independent_cleanup_verified':False,'driver':reference(folder/'driver.json'),
                        'pytest':pytest_runtime, 'python_environment':PYTHON_INPUTS}
                    if kind == 'native_campaign_owned_cleanup': proof['runtime'] = runtime
                    else:
                        names=(*CLEANUP_RUNTIME,'swdb/dx100.py','tests/test_dx100_interruption.py','tests/test_bfs_owned_execution.py')
                        proof['runtime_sha256']={name:runtime['files'][name] for name in names}
                    with (folder/'proof.pending.json').open('x') as stream: json.dump(proof,stream,indent=2);stream.write('\n')
                    require(time.monotonic() < deadline and allocated_bytes([folder]) <= LIMIT_BYTES,
                            'fixture proof publication exceeded bounds')
        except BaseException as exc:
            failure = failure or exc; receipt.update(state='failed',finalization_error=f'{type(exc).__name__}: {exc}')
            # Attempt a durable failed driver only within a new remaining shared
            # reservation. If accounting is exhausted, nonzero outer status and
            # missing independent closure still forbid admitting pending bytes.
            try:
                with budget.reservation():
                    save_receipt(folder,receipt)
            except BaseException as secondary:
                receipt['failure_persistence_error']=f'{type(secondary).__name__}: {secondary}'
    if failure is not None: raise failure
    return receipt



def execute(kind, folder, begin, end, deadline, code, runtime, pane, lane, pytest_runtime):
    """Preserved standard three-selection callable."""
    return _execute(kind,folder,begin,end,deadline,code,runtime,pane,lane,pytest_runtime)


def supplement_configuration(folder):
    """Private fixed group stage; this is never a standard admission proof."""
    from scripts import bfs_simulator_recovery as recovery
    from scripts.bfs_simulator_batch import PLAN_DIR, validate_plan
    if Path(folder) == RAW_BASE/(recovery.GROUP_ID+'.dispatch')/'supplement':
        group_id, selectors, key, count = recovery.GROUP_ID, recovery.SUPPLEMENT_SELECTORS, 't15-supervision-recovery', 42
    elif Path(folder) == RAW_BASE/(recovery.PROTOCOL_GROUP_ID+'.dispatch')/'supplement':
        group_id, selectors, key, count = recovery.PROTOCOL_GROUP_ID, recovery.PROTOCOL_SUPPLEMENT_SELECTORS, 't16-protocol-recovery', 66
    elif Path(folder) == RAW_BASE/(recovery.SEAL_GROUP_ID+'.dispatch')/'supplement':
        group_id, selectors, key, count = recovery.SEAL_GROUP_ID, recovery.SEAL_SUPPLEMENT_SELECTORS, 't16-seal-recovery', 66
    else:
        group_id, selectors, key, count = recovery.LEASE_GROUP_ID, recovery.LEASE_SUPPLEMENT_SELECTORS, 't15-lease-recovery', 51
        require(Path(folder) == RAW_BASE/(group_id+'.dispatch')/'supplement', 'supplement requires its fixed group root')
    plan=json.loads((PLAN_DIR/(recovery.IDS[key]+'.json')).read_text())
    validate_plan(plan,key)
    names=plan['accounting']['preparation_reservation']['supplement_testcases']
    require(len(names)==len(set(names))==count,'supplement exact case inventory changed')
    args=[sys.executable,'-m','pytest',*selectors,'-q','-p','no:cacheprovider',
          '--junitxml='+str(Path(folder)/'junit.xml'),'--basetemp='+str(Path(folder)/'pytest')]
    return group_id+'.supplement',args,set(names)


def execute_supplement(folder, begin, end, deadline, code, runtime, pane, lane, pytest_runtime):
    """One private fixed-case stage under the existing 90/60/30 supervision."""
    require(end-begin==timedelta(seconds=90) and 0 <= (datetime.now(own.ET)-begin).total_seconds() <= 5,
            'supplement requires its original 90-second outer clock')
    require(lane in (0,1) and Path(folder)==Path(folder).resolve(), 'supplement lane or root is invalid')
    return _execute(None,folder,begin,end,deadline,code,runtime,pane,lane,pytest_runtime,supplement=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind',choices=SELECTIONS)
    parser.add_argument('--expected-commit',required=True)
    parser.add_argument('--python-sha256',required=True)
    parser.add_argument('--pytest-version',required=True);parser.add_argument('--pytest-sha256',required=True)
    parser.add_argument('--outer-started',required=True);parser.add_argument('--outer-deadline',required=True)
    parser.add_argument('--pane-pid',type=int,required=True);parser.add_argument('--pane-start-ticks',type=int,required=True)
    parser.add_argument('--lane',type=int,choices=(0,1),required=True)
    args=parser.parse_args();begin,end=stamp(args.outer_started),stamp(args.outer_deadline)
    require(end-begin == timedelta(seconds=90) and 0 <= (datetime.now(own.ET)-begin).total_seconds() <= 5,
            'fixture requires its original 90-second outer clock')
    deadline=time.monotonic()+(end-datetime.now(own.ET)).total_seconds()
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10','fixture requires mbit10/Linux')
    require(Path('/data1/yanruj') in ROOT.parents,'fixture code must be on data1')
    require(artifacts.file_hash(Path(sys.executable).resolve()) == args.python_sha256,'fixture Python changed')
    resource.setrlimit(resource.RLIMIT_AS,(LIMIT_BYTES,LIMIT_BYTES))
    runtime=campaign_runtime(args.expected_commit)
    test_runtime=pytest_identity()
    require(test_runtime['version']==args.pytest_version and test_runtime['module']['sha256']==args.pytest_sha256,
            'fixture pytest changed')
    folder=RAW_BASE/SELECTIONS[args.kind][0]
    require(folder == folder.resolve() and not folder.exists(),'fixture root exists or is unsafe; no retry')
    with interruption_signals():
        execute(args.kind,folder,begin,end,deadline,args.expected_commit,runtime,
                {'pid':args.pane_pid,'start_ticks':args.pane_start_ticks},args.lane,test_runtime)


if __name__ == '__main__': main()
