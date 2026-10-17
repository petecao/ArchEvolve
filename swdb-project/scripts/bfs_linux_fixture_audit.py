#!/usr/bin/env python3
"""Independently close the five fixed Linux fixture routes. Dated 2026-09-26 ET.

Run after the outer wrapper exits, using the same pinned Python environment.
This process never signals, claims a lease, executes tests, or rewrites pending
evidence. Its separate 60-second audit bound does not extend the fixture's 90s.
"""
import argparse
from datetime import datetime, timedelta
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import bfs_owned_execution as own
from scripts import bfs_linux_fixture as standard
from scripts import bfs_a2_linux_fixture as a2
from scripts.bfs_native_campaign import campaign_runtime
from scripts.bfs_simulator_batch_terminal import finite, identity, timestamp

LIMIT = 512 * 1024**2
LEASE_ROOT = Path('/data1/yanruj/lact-host-lease')


def require(value, reason):
    if not value: raise ValueError(reason)


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate audit JSON field')
        result[key] = value
    return result


class Reader:
    """Bounded exact-byte reads; retain every checked input for a second pass."""
    def __init__(self, deadline):
        self.deadline, self.total, self.inputs = deadline, 0, {}

    def check(self):
        require(time.monotonic() < self.deadline, 'post-exit audit deadline exceeded')

    def raw(self, ref, maximum=16*1024**2):
        self.check()
        require(isinstance(ref, dict) and set(ref) == {'path', 'sha256'}
                and isinstance(ref['sha256'], str) and re.fullmatch('[0-9a-f]{64}', ref['sha256']),
                'invalid exact audit reference')
        path = Path(ref['path'])
        require(path.is_absolute() and path == path.resolve() and path.is_file()
                and not path.is_symlink(), 'audit reference is missing or unsafe')
        with path.open('rb') as stream: raw = stream.read(maximum+1)
        self.total += len(raw)
        require(len(raw) <= maximum and self.total <= LIMIT
                and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'audit artifact changed or read bound exceeded')
        self.inputs[str(path)] = (dict(ref), maximum)
        self.check()
        return raw

    def json(self, ref, maximum=16*1024**2):
        return json.loads(self.raw(ref, maximum), object_pairs_hook=unique)

    def recheck(self):
        for ref, maximum in list(self.inputs.values()): self.raw(ref, maximum)


def reference(path):
    return {'path': str(Path(path).absolute()), 'sha256': own.file_hash(path)}


def cleanup(value, path):
    require(isinstance(value, dict) and value.get('state') == 'all_owned_descendants_absent'
            and value.get('errors') == [] and value.get('subreaper') is True
            and value.get('direct_reaped') is True and value.get('shared_budget') == path,
            'fixture cleanup declaration failed or is incomplete')


def ledger_check(reader, ref, driver, begin, end):
    value = reader.json(ref, 256*1024)
    declared = driver['cleanup_budget']
    require(declared == {'path':ref['path'], 'binding':own.SharedCleanup.binding_of(value), 'budget_seconds':30}
            and value.get('format') == own.FORMAT and type(value.get('budget_seconds')) is int
            and value['budget_seconds'] == 30 and timestamp(value['absolute_end']) == end
            and identity(value['creator']) == identity(driver['process_observations']['driver_identity'])
            and value.get('reservations') == {}, 'fixture cleanup ledger binding or settlement differs')
    created = timestamp(value['created'])
    require(begin <= created <= timestamp(driver['finished']), 'cleanup ledger creation escapes fixture clock')
    finite(value['monotonic_end'], 'cleanup monotonic end', positive=True)
    events, charges, last = value.get('events'), [], created
    require(isinstance(events,list) and 0 < len(events) <= 2048, 'settled cleanup events missing or oversized')
    for event in events:
        grant = finite(event.get('seconds'), 'cleanup grant', positive=True)
        charge = finite(event.get('elapsed_seconds'), 'cleanup charge', positive=True)
        start, finish = timestamp(event['started']), timestamp(event['finished'])
        require(type(event.get('pid')) is int and event['pid'] > 0
                and event.get('purpose') in {'grace','cleanup_or_finalization'}
                and event.get('exceeded_grant') is False and charge <= grant <= 30
                and created <= start <= finish <= end and last <= finish,
                'cleanup event exceeded its grant or original clock')
        charges.append(charge); last = finish
    spent = finite(value.get('spent_seconds'), 'cleanup total')
    require(spent <= 30 and math.isclose(spent, math.fsum(charges), rel_tol=0, abs_tol=1e-9),
            'cleanup total differs from settled charges')
    return {'ledger':ref, 'binding':declared['binding'], 'spent_seconds':spent, 'events':len(events)}


def lease_snapshot(node, generation, lane, begin, end, root=LEASE_ROOT):
    result = {}
    for name in ('mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1'):
        path = root/(name+'.meta.json'); before = path.read_bytes()
        value = json.loads(before, object_pairs_hook=unique)
        with (root/(name+'.lease')).open('rb') as stream:
            try:
                fcntl.flock(stream,fcntl.LOCK_SH|fcntl.LOCK_NB); held = False
            except BlockingIOError: held = True
            finally: fcntl.flock(stream,fcntl.LOCK_UN)
        require(path.read_bytes() == before and value.get('state') == ('held' if held else 'released'),
                'lease metadata changed or disagrees with kernel lock')
        if name == f'mbit10-evaluation-node{node}':
            lease = value.get('lease', {})
            require(type(lease.get('generation')) is int and lease['generation'] >= generation
                    and lease.get('lease_name') == name and lease.get('host') == 'mbit10',
                    'fixture released lease generation or interval differs')
            acquired = timestamp(lease['acquired_at'])
            if lease['generation'] == generation:
                require(not held, 'fixture lease is still held')
                require(begin-timedelta(seconds=1) <= acquired <= end
                        and timestamp(lane['ended_utc']) <= timestamp(value['released_at']) < end+timedelta(seconds=1),
                        'fixture released lease generation or interval differs')
            else:
                # The helper advances generations under the same exclusive
                # lock. A later acquisition after our helper ended proves our
                # generation released; it does not admit another job here.
                require(timestamp(lane['ended_utc']) <= acquired <= timestamp(own.stamp()),
                        'successor lease acquisition does not establish fixture release')
                if not held:
                    require(acquired <= timestamp(value['released_at']) <= timestamp(own.stamp()),
                            'successor lease release interval differs')
        result[name] = {'path':str(path), 'sha256':hashlib.sha256(before).hexdigest(),
                        'metadata':value, 'kernel_held':held}
    return result


def process_snapshot(rows, pane, inspect=own.identity):
    result = []
    for key in sorted(rows):
        current = inspect(key[0])
        if current is None or identity(current) != key:
            result.append({'pid':key[0], 'start_ticks':key[1], 'state':'absent',
                           'current_identity':current})
        else:
            require(key == pane and current.get('state') == 'Z' and current.get('rss_bytes') == 0,
                    'live, unknown or non-pane zombie fixture process remains')
            result.append({**current,'role':'tmux_launcher'})
    return result


def runtime_check(reader, driver, pending, route, code):
    runtime = driver['supervisor_runtime'] if route == 'a2' else driver['runtime']
    require(Path(runtime['root']) == ROOT and campaign_runtime(code,root=ROOT) == runtime,
            'supervisor runtime changed after fixture')
    require(pending.get('pytest') == driver.get('pytest') == standard.pytest_identity(), 'pytest identity differs')
    reader.raw(runtime['python']); reader.raw(driver['pytest']['module'])
    if route == 'a2':
        require(pending.get('supervisor_commit') == driver.get('supervisor_commit') == code
                and pending.get('supervisor_runtime') == runtime
                and pending.get('tested_runtime_snapshots') == driver.get('tested_runtime_snapshots'),
                'separate A2 supervisor identity differs')
        refs = driver['tested_runtime_snapshots']
        before = reader.json(refs['before'],4*1024**2); after = reader.json(refs['after'],4*1024**2)
        require(before == after == driver.get('runtime') == pending.get('runtime')
                and before.get('repository_commit') == a2.TESTED_COMMIT
                and before.get('root') == driver['tested_root'], 'tested A2 runtime snapshots differ')
        current = campaign_runtime(a2.TESTED_COMMIT,root=Path(driver['tested_root']))
        bound = {**before['files'], **before['test_files'], 'pyproject.toml':before['project_config']}
        require(set(current['files']) <= set(bound), 'A2 runtime omits an actual tested file')
        for name, sha in current['files'].items():
            require(bound[name] == {'path':str(Path(driver['tested_root'])/name),'sha256':sha},
                    'tested A2 file changed after fixture')
        for ref in (before['python'],before['a2_plan'],before['project_config']): reader.raw(ref)
        require(before['python'] == runtime['python'] and before['python_version'] == runtime['python_version'],
                'tested and supervisor Python differ')
    elif driver['kind'] == 'native_campaign_owned_cleanup':
        require(pending.get('runtime') == runtime, 'native proof runtime differs')
    else:
        names = (*standard.CLEANUP_RUNTIME,'swdb/dx100.py','tests/test_dx100_interruption.py','tests/test_bfs_owned_execution.py')
        require(pending.get('runtime_sha256') == {name:runtime['files'][name] for name in names},
                'simulator proof runtime subset differs')
    return runtime


def audit(route, kind, pending_ref, lane_ref, exit_ref, ledger_ref, code, node, generation, *,
          reader, inspect=own.identity, leases=lease_snapshot, check_runtime=runtime_check):
    runner = a2 if route == 'a2' else standard
    require(route in {'a2','standard'} and kind in runner.SELECTIONS
            and re.fullmatch('[0-9a-f]{40}',code) and type(node) is int and node in (0,1)
            and type(generation) is int and generation > 0, 'invalid fixed fixture audit selection')
    pending = reader.json(pending_ref); driver = reader.json(pending['driver'])
    folder = Path(pending_ref['path']).parent
    require(Path(pending_ref['path']).name == 'proof.pending.json'
            and pending['driver']['path'] == str(folder/'driver.json')
            and driver.get('id') == runner.SELECTIONS[kind][0] and driver.get('kind') == kind
            and driver.get('state') == 'complete' and type(driver.get('returncode')) is int and driver['returncode'] == 0
            and pending.get('format') == 'swdb.bfs.linux-fixture.v1' and pending.get('kind') == kind
            and pending.get('host') == 'mbit10' and pending.get('platform') == 'linux'
            and pending.get('evidence_kind') == driver.get('evidence_kind') == 'contract_fixture'
            and pending.get('state') == 'tests_passed_cleanup_unverified'
            and type(pending.get('returncode')) is int and pending['returncode'] == 0
            and pending.get('independent_cleanup_verified') is False and driver.get('cleanup_verified') is False
            and driver.get('automatic_retry_allowed') is False
            and pending.get('code_commit') == driver.get('code_commit') == (a2.TESTED_COMMIT if route=='a2' else code),
            'pending fixture or successful driver identity differs')
    begin, end, finish = map(timestamp,(driver['started'],driver['outer_deadline'],driver['finished']))
    require(end-begin == timedelta(seconds=90) and begin <= finish <= end
            and pending.get('started') == driver['started'] and pending.get('finished') == driver['finished']
            and driver.get('bounds') == {'outer_seconds':90,'work_seconds':60,'cleanup_seconds':30,
                                        'sampled_rss_bytes':LIMIT,'output_bytes':LIMIT},
            'fixture bounds or retained original clock differ')
    require(driver.get('python_environment') == pending.get('python_environment') == runner.PYTHON_INPUTS,
            'fixture Python environment differs')
    runtime = check_runtime(reader,driver,pending,route,code)
    command = list(runner.command(kind,folder)); command[0] = driver['command'][0]
    require(driver['command'] == pending.get('command') == command
            and Path(command[0]).resolve() == Path(runtime['python']['path']), 'fixture pytest command differs')
    reader.raw(pending['stdout']); reader.raw(pending['junit'],4*1024**2)
    require(pending['stdout']['path'] == str(folder/'pytest.stdout')
            and pending['junit']['path'] == str(folder/'junit.xml'), 'pytest output path differs')
    cases = runner.junit_cases(folder/'junit.xml',runner.SELECTIONS[kind][2])
    require(set(driver.get('testcases',[])) == set(cases), 'driver and JUnit testcase sets differ')
    stages = driver.get('stages',[])
    require(len(stages) == (3 if route=='a2' else 1), 'fixture stage set differs')
    rows = {}; proc = driver['process_observations']; driver_key, pane = identity(proc['driver_identity']), identity(proc['pane_identity'])
    def include(items):
        require(isinstance(items,list) and len(items)<=own.MAX_IDENTITIES, 'owned identity list exceeds bound')
        for item in items: rows[identity(item)] = item
        require(len(rows)<=own.MAX_IDENTITIES, 'owned identity union exceeds bound')
    ancestors = proc['ancestry']; include(ancestors)
    require(ancestors and identity(ancestors[0]) == driver_key and identity(ancestors[-1]) == pane
            and len({identity(row) for row in ancestors}) == len(ancestors)
            and all(left.get('parent_pid') == right['pid'] for left,right in zip(ancestors,ancestors[1:])),
            'captured owned ancestry does not end at the exact pane')
    include(proc['owned_processes']); cleanup(driver['cleanup'],ledger_ref['path']); include(driver['cleanup']['observed'])
    last = begin
    for index,stage in enumerate(stages):
        start, stopped = timestamp(stage['started']), timestamp(stage['finished'])
        expected = command if route=='standard' or index==1 else [command[0],*a2.runtime_command()[1:]]
        output_name = 'pytest.stdout' if expected==command else ('runtime-before.json' if index==0 else 'runtime-after.json')
        require(stage.get('output')==str(folder/output_name), 'stage output differs from its declared role')
        if route=='a2' and index!=1:
            key='before' if index==0 else 'after'
            require(driver['tested_runtime_snapshots'][key]=={'path':stage['output'],'sha256':stage['stdout_sha256']},
                    'A2 runtime snapshot is disconnected from its actual child output')
        require(stage.get('state')=='complete' and type(stage.get('returncode')) is int and stage['returncode']==0
                and stage.get('command')==expected and last<=start<=stopped<=finish
                and start < begin+timedelta(seconds=60)
                and 0 < finite(stage.get('timeout_s'),'stage allowance') <= 60
                and start+timedelta(seconds=stage['timeout_s'])<=begin+timedelta(seconds=60)
                and stage.get('identity',{}).get('parent_pid')==driver_key[0]
                and (route!='a2' or index==1 or stage['timeout_s']<=10), 'fixture stage failed or escaped its declared clock')
        last=stopped; include([stage['identity']]); cleanup(stage['cleanup'],ledger_ref['path']); include(stage['cleanup']['observed'])
        for key,hash_key in (('output','stdout_sha256'),('stderr','stderr_sha256')):
            reader.raw({'path':stage[key],'sha256':stage[hash_key]})
    samples=reader.raw(driver['resource_samples'],64*1024**2)
    require(driver['resource_samples']['path']==str(folder/'resources.jsonl'),'resource path differs')
    coverage=own.validate_samples(folder/'resources.jsonl',driver['started'],driver['finished'])
    require(coverage['peak_sampled_rss_bytes']<=LIMIT,'fixture sampled RSS exceeded512MiB')
    lane_rows=0
    for raw in samples.splitlines():
        sample=json.loads(raw,object_pairs_hook=unique); include(sample['processes'])
        require(type(sample.get('output_bytes')) is int and 0<=sample['output_bytes']<=LIMIT,'fixture sampled output exceeded bound')
        require(driver_key in {identity(row) for row in sample['processes']},'resource sample omits driver')
        if 'lane' in sample:
            held=sample['lane'].get('leases',{}).get(f'mbit10-evaluation-node{node}',{}).get('metadata',{})
            require(held.get('state')=='held' and type(held.get('lease',{}).get('generation')) is int
                    and held['lease']['generation']==generation
                    and held['lease'].get('lease_name')==f'mbit10-evaluation-node{node}'
                    and held['lease'].get('host')=='mbit10', 'sampled fixture lane differs from terminal generation')
            lane_rows+=1
    require(lane_rows>0,'resource samples contain no verified fixture lane')
    require(driver_key in rows and pane in rows,'terminal union omits driver or pane')
    lane=reader.json(lane_ref)['socket_lane']; name=f'mbit10-evaluation-node{node}'
    lane_start,lane_end=timestamp(lane['started_utc']),timestamp(lane['ended_utc'])
    require(lane.get('host')=='mbit10' and type(lane.get('node')) is int and lane['node']==node
            and lane.get('lease_name')==name and type(lane.get('lease_generation')) is int
            and lane['lease_generation']==generation and type(lane.get('exit_code')) is int and lane['exit_code']==0
            and begin-timedelta(seconds=1)<=lane_start<=finish
            and finish<lane_end+timedelta(seconds=1) and lane_end<end+timedelta(seconds=1)
            and reader.raw(exit_ref,32).strip()==b'0', 'outer/helper exit, generation or interval differs')
    require(timestamp(own.stamp())>=finish and timestamp(own.stamp())>=lane_end,
            'fixture terminal observations are in the future')
    first_leases=leases(node,generation,lane,begin,end); first=process_snapshot(rows,pane,inspect)
    budget=ledger_check(reader,ledger_ref,driver,begin,end)
    reader.recheck()
    second_leases=leases(node,generation,lane,begin,end); second=process_snapshot(rows,pane,inspect)
    # Each snapshot independently establishes release of the fixture generation.
    # Later users may acquire/release the lane between those observations.
    reader.check()
    return {'format':'swdb.bfs.fixture-terminal.v1','id':driver['id'],'state':'passed',
        'evidence_kind':'contract_fixture','route':route,'kind':kind,'code_commit':pending['code_commit'],
        'supervisor_commit':code,'observed_at':own.stamp(),'fixture_started':driver['started'],
        'fixture_finished':driver['finished'],'outer_deadline':driver['outer_deadline'],
        'pending':pending_ref,'driver':pending['driver'],'lane':lane_ref,'outer_exit':exit_ref,
        'lease_generation':generation,'lease_released':True,'lease_observations':[first_leases,second_leases],
        'process_observations':[first,second],'owned_processes':second,'cleanup_ledger':budget,
        'cleanup_state':'terminal_no_live_owned_processes' if any(row['state']=='Z' for row in second) else 'terminal_and_reaped',
        'auditor':reference(__file__),
        'sampling_limit':'unobserved short-lived processes cannot be reconstructed','testcases':cases,
        'resource_validation':coverage,'empirical_evidence':False}, pending


def write_new(path,value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
    fd=os.open(Path(path).parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def seal(audit_value,pending,folder,reader):
    folder=Path(folder); audit_path=folder/'terminal-audit.json'; proof_path=folder/'proof.json'
    require(not audit_path.exists() and not proof_path.exists(),'fixture audit/proof already exists; no overwrite')
    reader.check(); write_new(audit_path,audit_value); reader.check()
    proof={**pending,'state':'passed','independent_cleanup_verified':True,
           'pending':audit_value['pending'],'terminal_audit':reference(audit_path),'audited_at':audit_value['observed_at']}
    # The passed filename is linked only after its bytes/fsync satisfy the audit
    # deadline. A failed later audit never overwrites this route's existing proof.
    staging=folder/'proof.sealed-staging.json'
    write_new(staging,proof); reader.check()
    linked=False
    try:
        os.link(staging,proof_path); linked=True
        fd=os.open(folder,os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
        reader.check()
        result=reference(proof_path)
        reader.check()
        return result
    except BaseException:
        # Withdraw only this invocation's new link; retained pending/audit/staged
        # bytes survive. No preexisting name can reach this branch.
        if linked and proof_path.stat().st_ino==staging.stat().st_ino:proof_path.unlink()
        raise


def main():
    deadline=time.monotonic()+60
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('route',choices=('standard','a2'));parser.add_argument('kind')
    parser.add_argument('--expected-supervisor-commit',required=True)
    for name in ('pending','lane','outer-exit','ledger'):
        parser.add_argument('--'+name,required=True);parser.add_argument('--'+name+'-sha256',required=True)
    parser.add_argument('--node',type=int,choices=(0,1),required=True);parser.add_argument('--generation',type=int,required=True)
    args=parser.parse_args()
    require(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10','post-exit audit requires mbit10/Linux')
    runner=a2 if args.route=='a2' else standard
    require(args.kind in runner.SELECTIONS and not sys.flags.optimize and sys.flags.no_user_site
            and all(os.environ.get(k)==v for k,v in runner.PYTHON_INPUTS.items()),'audit Python environment or selection differs')
    pending=Path(args.pending)
    require(pending==runner.RAW_BASE/runner.SELECTIONS[args.kind][0]/'proof.pending.json','audit fixture root differs')
    def ref(name):return {'path':getattr(args,name),'sha256':getattr(args,name+'_sha256')}
    reader=Reader(deadline)
    value,proof=audit(args.route,args.kind,ref('pending'),ref('lane'),ref('outer_exit'),ref('ledger'),
        args.expected_supervisor_commit,args.node,args.generation,reader=reader)
    print(json.dumps(seal(value,proof,pending.parent,reader)))


if __name__=='__main__': main()
