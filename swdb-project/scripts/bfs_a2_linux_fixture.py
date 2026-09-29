#!/usr/bin/env python3
"""Two bounded A2 Linux contract selections against fixed prelaunch code. Updated 2026-09-26 ET.

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
    'PYTEST_ADDOPTS','PYTEST_PLUGINS','PYTHONOPTIMIZE','LD_PRELOAD','LD_LIBRARY_PATH',
    'GCC_EXEC_PREFIX','COMPILER_PATH','LIBRARY_PATH','CPATH','CPLUS_INCLUDE_PATH','C_INCLUDE_PATH')), 'PYTHONNOUSERSITE':'1',
    'PYTHONDONTWRITEBYTECODE':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','PATH':'/usr/bin:/bin'}
if __name__ == '__main__':
    if any(os.environ.get(key) != value for key,value in PYTHON_INPUTS.items()) or not sys.flags.no_user_site or sys.flags.optimize != 0:
        raise SystemExit('fixture runner requires the declared isolated Python environment with assertions enabled')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import bfs_owned_execution as own
from scripts.bfs_process import interruption_signals, save_receipt
from scripts.bfs_native_campaign import campaign_runtime, validate_root_entries
from scripts.bfs_simulator_batch import allocated_bytes, lease_observation
from swdb import artifacts
from swdb.store import Store

LIMIT_BYTES = 512 * 1024**2
TESTED_COMMIT = '5a0b15fe666b2d094a2b2b9847ff5a30ef16fb4f'
SELECTIONS = {
    'owned_cleanup': ('bfs-a2-owned-linux-20260926-a2',
        ['tests/test_bfs_dx100_coverage_a2.py::test_linux_a2_reaps_detached_child'], {
            'test_linux_a2_reaps_detached_child[False]',
            'test_linux_a2_reaps_detached_child[True]'}),
    'dx100_interruption': ('bfs-a2-interruption-linux-20260926-a2',
        ['tests/test_dx100_interruption.py::test_public_interruption_is_durable_before_postmortem'], {
            'test_public_interruption_is_durable_before_postmortem[raises]',
            'test_public_interruption_is_durable_before_postmortem[stalls]'})}
RUNTIME_OUTPUT_BYTES = 4 * 1024**2
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


def runtime_command():
    program = ("import json;from scripts.bfs_dx100_coverage_a2 import runtime_identity;"
               "print(json.dumps(runtime_identity(" + repr(TESTED_COMMIT) + ")))" )
    return [sys.executable, '-c', program]


def tested_inventory(root):
    root = Path(root)
    require(root == root.resolve() and root != ROOT and Path('/data1/yanruj') in root.parents,
            'tested A2 checkout must be a distinct regular data1 root')
    # This current supervisor only reads the historical tree; it never imports it.
    return campaign_runtime(TESTED_COMMIT, root=root)


def read_runtime(path, tested_root):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'A2 runtime output is missing or unsafe')
    with path.open('rb') as stream: raw = stream.read(RUNTIME_OUTPUT_BYTES+1)
    require(len(raw) <= RUNTIME_OUTPUT_BYTES, 'A2 runtime output exceeded4MiB')
    value = json.loads(raw)
    require(isinstance(value, dict) and value.get('repository_commit') == TESTED_COMMIT
            and value.get('root') == str(tested_root)
            and set(value) == {'repository_commit','root','files','python','python_version',
                              'a2_plan','project_config','test_files'},
            'A2 runtime does not identify the exact tested checkout')
    require(value['python'] == reference(Path(sys.executable).resolve()), 'tested Python differs')
    return value


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


def execute(kind, folder, begin, end, deadline, code, runtime, tested_root, pane, lane, pytest_runtime):
    """Test seam uses real stage orchestration; main owns fixed host/path admission."""
    folder.mkdir(parents=True, exist_ok=False); (folder/'tmp').mkdir()
    budget_path = folder/'cleanup-ledger.json'
    binding = own.SharedCleanup.create(budget_path, end.isoformat(), deadline=deadline)
    budget = own.SharedCleanup(budget_path, binding, deadline)
    owner = own.Owned(budget)
    driver = own.identity(os.getpid())
    receipt = {'id': SELECTIONS[kind][0], 'created': '2026-09-26', 'state': 'running',
        'evidence_kind': 'contract_fixture', 'code_commit': TESTED_COMMIT, 'supervisor_commit': code, 'kind': kind,
        'started': begin.isoformat(), 'outer_deadline': end.isoformat(), 'stages': [],
        'bounds': {'outer_seconds':90, 'work_seconds':60, 'cleanup_seconds':30,
                   'sampled_rss_bytes':LIMIT_BYTES, 'output_bytes':LIMIT_BYTES},
        'cleanup_verified': False, 'automatic_retry_allowed': False, 'supervisor_runtime':runtime, 'tested_root':str(tested_root),
        'pytest':pytest_runtime, 'python_environment':PYTHON_INPUTS,
        'process_observations': {'driver_identity':driver, 'pane_identity':pane,
                                'ancestry':own.ancestry(driver,pane)},
        'cleanup_budget':{'path':str(budget_path),'binding':binding,'budget_seconds':30}}
    samples = folder/'resources.jsonl'; machine = None; failure = None; guard = None
    def observe():
        require(time.monotonic() < deadline and datetime.now(own.ET) <= end, 'fixture original deadline exceeded')
        sample = owner.sample()
        require(sample['rss_bytes'] <= LIMIT_BYTES, 'fixture sampled RSS limit exceeded')
        used = allocated_bytes([folder]); require(used <= LIMIT_BYTES, 'fixture output limit exceeded')
        for name in ('runtime-before.json','runtime-after.json'):
            output = folder/name
            require(not output.exists() or output.stat().st_size <= RUNTIME_OUTPUT_BYTES,
                    'A2 runtime output exceeded4MiB')
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
        tested_tree = tested_inventory(tested_root)
        def snapshot(label):
            path = folder/('runtime-'+label+'.json')
            remaining = work_end-time.monotonic()
            require(remaining > 0, 'A2 metadata stage has no work allowance')
            own.run_stage(receipt,folder,runtime_command(),timeout=min(10,remaining),deadline=work_end,
                cwd=tested_root,owned=owner,monitor=guard.check,env=child_environment(folder),
                output=path,stderr=folder/('runtime-'+label+'.stderr'))
            require(time.monotonic() < work_end, 'A2 metadata readback exceeded work allowance')
            value = read_runtime(path,tested_root)
            receipt.setdefault('tested_runtime_snapshots',{})[label] = reference(path)
            return value
        before = snapshot('before')
        args = command(kind,folder)
        require(time.monotonic() < work_end, 'fixture setup consumed work allowance')
        row = own.run_stage(receipt,folder,args,timeout=work_end-time.monotonic(),deadline=work_end,
            cwd=tested_root,owned=owner,monitor=guard.check,env=child_environment(folder),
            output=folder/'pytest.stdout',stderr=folder/'pytest.stderr')
        require(time.monotonic() < work_end, 'fixture readback has no remaining work allowance')
        receipt['testcases'] = junit_cases(folder/'junit.xml',SELECTIONS[kind][2])
        after = snapshot('after')
        require(before == after and tested_inventory(tested_root) == tested_tree,
                'tested A2 runtime changed during fixture')
        receipt['runtime'] = before
        require(campaign_runtime(code) == runtime and pytest_identity() == pytest_runtime, 'supervisor runtime changed during tests')
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
                if failure is None:
                    proof = {'format':'swdb.bfs.linux-fixture.v1','kind':kind,'host':'mbit10','platform':'linux',
                        'evidence_kind':'contract_fixture','state':'tests_passed_cleanup_unverified','returncode':0,'code_commit':TESTED_COMMIT,
                        'started':begin.isoformat(),'finished':receipt['finished'],'command':receipt['command'],
                        'stdout':reference(folder/'pytest.stdout'),'junit':reference(folder/'junit.xml'),
                        'independent_cleanup_verified':False,'driver':reference(folder/'driver.json'),
                        'pytest':pytest_runtime, 'python_environment':PYTHON_INPUTS}
                    proof.update(runtime=receipt['runtime'],supervisor_commit=code,
                        supervisor_runtime=runtime,tested_runtime_snapshots=receipt['tested_runtime_snapshots'])
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


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kind',choices=SELECTIONS)
    parser.add_argument('--expected-supervisor-commit',required=True)
    parser.add_argument('--tested-checkout',type=Path,required=True)
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
    runtime=campaign_runtime(args.expected_supervisor_commit)
    tested_root=args.tested_checkout.absolute()
    tested_inventory(tested_root)
    test_runtime=pytest_identity()
    require(test_runtime['version']==args.pytest_version and test_runtime['module']['sha256']==args.pytest_sha256,
            'fixture pytest changed')
    folder=RAW_BASE/SELECTIONS[args.kind][0]
    require(folder == folder.resolve() and not folder.exists(),'fixture root exists or is unsafe; no retry')
    with interruption_signals():
        execute(args.kind,folder,begin,end,deadline,args.expected_supervisor_commit,runtime,tested_root,
                {'pid':args.pane_pid,'start_ticks':args.pane_start_ticks},args.lane,test_runtime)


if __name__ == '__main__': main()
