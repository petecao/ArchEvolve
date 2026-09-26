#!/usr/bin/env python3
"""Retain explicit BFS workflow contract fixtures through public commands.

Created: 2026-09-25 (Eastern Time). Synthetic compiler/timing fixtures never
establish native performance, simulated acceleration, or an empirical regression.
Raw files use a new /private/tmp directory; master records are never overwritten.
"""
import argparse
import copy
import datetime
import difflib
import json
import os
from pathlib import Path
import platform
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, bfs_protocol, workflow

PROGRAM = '''#!/usr/bin/env python3
import collections,json,os,sys,time
from pathlib import Path
mode=os.environ.get('SWDB_CONTRACT_CASE','pass')
if mode=='timeout': time.sleep(10)
if mode=='missing': sys.exit(0)
tokens=Path(sys.argv[1]).read_text().split(); n=int(tokens[1]); source=int(sys.argv[2])
adj=[[] for _ in range(n)]
for i in range(4,len(tokens),2): adj[int(tokens[i])].append(int(tokens[i+1]))
parents=[-1]*n; parents[source]=source; queue=collections.deque([source])
while queue:
 u=queue.popleft()
 for v in adj[u]:
  if parents[v]==-1: parents[v]=u; queue.append(v)
if mode=='incorrect':
 print('Verification: PASS (deliberately misleading contract fixture)')
 parents[source]=-1
Path(sys.argv[3]).write_text(json.dumps({'format':'swdb.bfs.native.trial.v1',
 'source':source,'configured_threads':int(os.environ['OMP_NUM_THREADS']),
 'roi':'bfs.complete_call.v1','parents':parents,
 'duration_s':float(os.environ.get('SWDB_CONTRACT_DURATION','0.1'))}))
'''


def capture_machine(rid, raw):
    keys = ['machdep.cpu.brand_string', 'hw.machine', 'hw.physicalcpu', 'hw.logicalcpu',
            'hw.memsize', 'hw.packages', 'hw.perflevel0.physicalcpu', 'hw.perflevel0.l1dcachesize']
    captured = subprocess.check_output(['sysctl', *keys], text=True, timeout=15)
    path = raw / 'machine-sysctl.txt'; path.write_text(captured)
    values = dict(line.split(': ', 1) for line in captured.splitlines())
    physical, logical, packages = (int(values[key]) for key in ('hw.physicalcpu', 'hw.logicalcpu', 'hw.packages'))
    memory = int(values['hw.memsize'])
    result = workflow.record('machine', rid, hostname=socket.gethostname().split('.')[0], lane_required=False,
        cpu={'model': values['machdep.cpu.brand_string'], 'architecture': values['hw.machine'],
             'sockets': packages, 'cores_per_socket': physical // packages, 'threads_per_core': logical // physical,
             'logical_cpus': logical, 'max_mhz': None, 'flags': []},
        caches=[{'level': 1, 'type': 'data', 'size_bytes': int(values['hw.perflevel0.l1dcachesize']),
                 'instances': int(values['hw.perflevel0.physicalcpu']), 'shared_by': 'core'}],
        memory_bytes=memory, numa_nodes=[{'node': 0, 'cpus': f'0-{logical-1}', 'memory_bytes': memory}],
        os={'kernel': platform.release(), 'distribution': 'macOS ' + platform.mac_ver()[0]},
        counters={'perf_event_paranoid': None, 'hardware_counters_available':
                  {'value': None, 'basis': 'unknown', 'note': 'Counter availability was not probed; contract fixtures use no counters.'}},
        capture={'command': 'sysctl ' + ' '.join(keys), 'date': datetime.datetime.now(datetime.timezone.utc).isoformat()},
        notes=['Local hardware identity for explicit contract fixtures only; no performance comparison with mbit10.',
               'Cache list captures only perflevel0 L1 data caches; other levels and ISA flags were not surveyed.',
               'NUMA entry denotes one logical fixture locality domain, not an independently surveyed physical topology.'],
        extensions={'contract_fixture_host': True, 'capture_artifact': {'path': str(path), 'sha256': artifacts.file_hash(path)}})
    # The catalog machine schema predates versioned workflow messages.
    result.pop('message_version'); result.pop('producer')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--records', type=Path, default=ROOT / 'records')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.id): parser.error('invalid record prefix')
    if platform.system() != 'Darwin': parser.error('this explicit local fixture driver captures macOS hardware')
    args.records = args.records.resolve()
    raw = Path(tempfile.mkdtemp(prefix=args.id + '-', dir='/private/tmp'))
    started = time.monotonic()
    receipt = {'id': args.id, 'classification': 'contract_fixture', 'state': 'running', 'gain_claim': False,
               'empirical_regression': False, 'raw': str(raw), 'stages': [], 'total_budget_seconds': 3600}
    def save():
        receipt['elapsed_seconds'] = time.monotonic() - started
        (raw / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    def call(command, *rest, expected=0, env=None):
        remaining = 3600 - (time.monotonic() - started)
        if remaining <= 0: raise TimeoutError('contract demonstration budget exhausted')
        plain = command in {'add', 'build', 'validate'}
        argv = [sys.executable, '-m', 'swdb', command, *map(str, rest), '--records', str(args.records)]
        if not plain: argv += ['--format', 'json']
        index = len(receipt['stages']); out = raw / f'{index:02}-{command}.stdout'; err = raw / f'{index:02}-{command}.stderr'
        entry = {'command': argv, 'stdout': str(out), 'stderr': str(err), 'state': 'running'}
        receipt['stages'].append(entry); save()
        with out.open('w') as stdout, err.open('w') as stderr:
            child = subprocess.Popen(argv, cwd=ROOT, stdout=stdout, stderr=stderr, env={**os.environ, **(env or {})}, start_new_session=True)
            try: child.wait(timeout=min(900, remaining))
            except BaseException:
                os.killpg(child.pid, signal.SIGTERM)
                try: child.wait(timeout=10)
                except subprocess.TimeoutExpired: os.killpg(child.pid, signal.SIGKILL); child.wait()
                raise
        entry.update(returncode=child.returncode, state='complete' if child.returncode == expected else 'unexpected_outcome',
                     stdout_sha256=artifacts.file_hash(out), stderr_sha256=artifacts.file_hash(err)); save()
        if child.returncode != expected: raise RuntimeError(f'{command} failed its expected result; see {err}')
        return {'message': out.read_text()} if plain else json.loads(out.read_text())
    def request(command, value, *rest, **options):
        path = raw / (value['id'] + '.request.json'); path.write_text(json.dumps(value, indent=2) + '\n')
        return call(command, path, *rest, **options)
    def patch(original, before, after):
        if before not in original: raise ValueError('fixture patch anchor missing')
        return ''.join(difflib.unified_diff(original.splitlines(True), original.replace(before, after).splitlines(True),
                                          fromfile='a/src/bfs.cc', tofile='b/src/bfs.cc'))
    save()
    try:
        machine = capture_machine(args.id + '.local-host', raw)
        request('add', machine)
        original_impl = call('get', 'gapbs-bfs-do')
        reference = copy.deepcopy(original_impl)
        reference.update(id=args.id + '.independent-reference', name='Explicit contract reference: unchanged upstream DOBFS',
            created=machine['created'], updated=machine['updated'],
            origin={'kind': 'application_source', 'derived_from': None, 'description': 'Independent catalog identity for the unchanged source; contract demonstration only.'},
            source_baseline=args.id + '.independent-reference',
            verification={'status': 'unchecked', 'evidence': [], 'scope': 'Contract fixture identity; no performance or correctness certification inherited.'})
        reference['notes'].append('Explicit fixture reference identity; actual application source bytes remain unchanged.')
        request('add', reference)
        source = call('source-snapshot', 'gapbs-bfs-do', '--id', args.id + '.source', '--runs-dir', raw)
        package = call('fixture-package', source['id'], '--id', args.id + '.fixture-package')
        text = (Path(source['artifact']['path']) / 'src/bfs.cc').read_text()
        base = {'message_version': '1.0', 'producer': {'name': 'swdb-contract-demonstration-client', 'role': 'sw', 'test_client': True},
            'implementation': 'gapbs-bfs-do', 'source_snapshot': source['id'], 'source_sha256': source['artifact']['sha256'],
            'profile_package': package['id'], 'regions': [source['regions'][0]['id']],
            'intent': 'Explicit contract fixture; no empirical timing or strategy benefit is claimed.',
            'parameters': {'evidence_classification': 'contract_fixture'},
            'constraints': {'editable_files': ['src/bfs.cc'], 'preserve_correctness': True, 'preserve_roi': True},
            'payload': {'kind': 'patch', 'content': patch(text, 'int alpha = 15', 'int alpha = 14')}, 'required_operations': []}
        for name in ('stale-source', 'unsupported-operation', 'protected-verifier'):
            value = copy.deepcopy(base); value['id'] = args.id + '.' + name
            if name == 'stale-source': value['source_sha256'] = '0' * 64
            elif name == 'unsupported-operation': value['required_operations'] = [{'operation': 'deliberately-unsupported-contract-operation'}]
            else: value['payload']['content'] = patch(text, 'bool BFSVerifier', 'bool AlteredVerifier')
            result = request('submit', value, '--runs-dir', raw, expected=1)
            if result['outcome']['state'] not in {'rejected', 'unresolved', 'failed'} or 'candidate' in result:
                raise ValueError('negative proposal did not remain non-success')
        submitted = request('submit', {**base, 'id': args.id + '.candidate-proposal'}, '--runs-dir', raw)
        source_ref = call('source-snapshot', reference['id'], '--id', args.id + '.reference-source', '--runs-dir', raw)
        baseline = call('baseline-candidate', source_ref['id'], '--id', args.id + '.reference-candidate', '--runs-dir', raw)
        compiler = raw / 'explicit-fixture-compiler'
        compiler.write_text('#!' + sys.executable + '\nimport os,sys\nfrom pathlib import Path\n'
            "if '--version' in sys.argv: print('SWDB explicit contract fixture compiler v1'); sys.exit(0)\n"
            "if os.environ.get('SWDB_CONTRACT_CASE')=='build-failure': sys.exit(7)\n"
            f"p=Path(sys.argv[sys.argv.index('-o')+1]);p.write_text({PROGRAM!r});p.chmod(0o755)\n")
        compiler.chmod(0o755)
        graph = {'num_vertices': 5, 'directed': True, 'edges': [[0,1],[0,2],[1,3],[2,3]]}
        graph_path = raw / 'fixture-graph.json'; graph_path.write_text(json.dumps(graph))
        workload = request('register-workload', {'message_version': '1.0', 'id': args.id + '.workload', 'version': 1,
            'kernel': 'gapbs-bfs', 'family': 'contract_fixture', 'generator': {'name': 'explicit correctness fixture',
            'revision': 'fixture-v1', 'parameters': {}}, 'normalization': bfs_protocol.NORMALIZATION, 'sources': [0,4],
            'representations': [{'id': args.id + '.json', 'application': 'gapbs', 'format': 'json_graph',
                                'path': str(graph_path), 'sha256': artifacts.file_hash(graph_path)}]})
        build = {'compiler': str(compiler), 'flags': ['-std=c++11', '-O2']}
        evaluation = {'message_version': '1.0', 'candidate': submitted['candidate'], 'machine': machine['id'],
            'threads': 1, 'sources': [0], 'repetitions': 1, 'roi': 'bfs.complete_call.v1', 'fixture': True,
            'comparison_baseline': reference['id'], 'build': build, 'workload': {'id': workload['id']},
            'budget': {'build_seconds': 10, 'run_seconds': 2, 'total_seconds': 120}}
        states = {'build-failure': 'failed', 'incorrect': 'incorrect', 'timeout': 'timed_out',
                  'budget': 'budget_exhausted', 'missing': 'missing_observation'}
        for mode, state in states.items():
            value = copy.deepcopy(evaluation); value['id'] = args.id + '.' + mode
            if mode == 'timeout': value['budget']['run_seconds'] = 0.05
            if mode == 'budget': value['budget']['total_seconds'] = 0.001
            result = request('evaluate', value, '--runs-dir', raw, expected=1, env={'SWDB_CONTRACT_CASE': mode})
            if result['outcome']['state'] != state or result['evidence_kind'] != 'contract_fixture':
                raise ValueError('failure fixture had the wrong durable outcome')
        settings = {'mode': 'native', 'kernel': 'gapbs-bfs', 'workloads': [workload['id']], 'threads': 1, 'roi': 'bfs.complete_call.v1',
            'targets': {role: {'id': machine['id'], 'configuration': {}} for role in ('baseline','candidate')},
            'builds': {role: {**build, 'adapter':'gapbs_native','compiler_version':['SWDB explicit contract fixture compiler v1']} for role in ('baseline','candidate')},
            'instrumentation': {role: {'template_sha256': artifacts.file_hash(ROOT/'tools/bfs_native/driver.cc.in'), 'treatment':'included'} for role in ('baseline','candidate')},
            'correctness': {'coverage':'every_timed_trial','verifier':'swdb.bfs.structural.v1','required_cases':[]},
            'sampling': {'repetitions':5,'warmups':0,'aggregation':'geomean_source_median_ratio'},
            'profitability': {'minimum_speedup':1.05,'maximum_relative_spread':0.1,'confidence':0.95,'bootstrap_resamples':2000,'bootstrap_seed':20260925},
            'differences': {'software':['Explicit fixture source identity differs; artificial durations establish no performance.'],'accelerator':[],'configuration':[]}, 'region_pairs':[]}
        frozen = request('freeze-protocol', {'message_version':'1.0','id':args.id+'.fixture-protocol','version':1,'settings':settings})
        completed = {}
        for role, candidate, duration in [('baseline',baseline['id'],'0.05'),('candidate',submitted['candidate'],'0.10')]:
            value = {**evaluation, 'id':args.id+'.'+role+'.evaluation','candidate':candidate,
                     'protocol':frozen['id'],'protocol_role':role,'sources':[0,4],'repetitions':5,
                     'budget':{'build_seconds':10,'run_seconds':2,'total_seconds':900}}
            completed[role] = request('evaluate', value, '--runs-dir', raw, env={'SWDB_CONTRACT_CASE':'pass','SWDB_CONTRACT_DURATION':duration})
        comparison = request('compare-evaluations', {'message_version':'1.0','id':args.id+'.comparison','protocol':frozen['id'],
            'baseline_evaluation':completed['baseline']['id'],'candidate_evaluation':completed['candidate']['id'],
            'comparison_baseline':reference['id']})
        if comparison['decision']['state'] != 'fixture_comparison' or comparison['metrics']['fixture_ratio'] != 0.5 or comparison['gain_claim']:
            raise ValueError('unfavorable fixture comparison crossed its evidence boundary')
        call('build')
        chain = call('get', comparison['id'], '--chain')
        report = request('bfs-coverage', {'message_version':'1.0','id':args.id+'.coverage','candidate_protocols':[],
                                        'artifact_reference_comparisons':[],'controlled_reference_comparisons':[]})
        if any(report['criteria'][key]['state'] != 'satisfied_by_retained_metadata' for key in ('AC08','AC09','AC14')):
            raise ValueError('durable contract coverage remains incomplete')
        if report['gain_claim'] or report['criteria']['AC17']['state'] != 'incomplete' or any(c['state'] != 'incomplete' for c in report['matrix']):
            raise ValueError('contract fixtures incorrectly satisfied empirical acceptance')
        call('validate')
        receipt.update(state='complete', comparison=comparison['id'], fixture_ratio=0.5, contract_criteria=['AC08','AC09','AC14'],
                       retrieved_records=len(chain['records']), report_identity=report['identity_sha256'])
    except BaseException as exc:
        receipt.update(state='failed', reason=f'{type(exc).__name__}: {exc}'); save(); raise
    save(); print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
