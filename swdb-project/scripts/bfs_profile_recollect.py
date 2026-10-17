#!/usr/bin/env python3
"""Recollect real BFS diagnostics without repeating valid primary runs. Updated 2026-09-25."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, profile
from swdb.cli import _require_valid
from bfs_diagnostic_driver import preflight, bounded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', required=True)
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--records', type=Path, default=Path('records'))
    parser.add_argument('--lane', required=True)
    parser.add_argument('--baseline-evaluation', default='bfs-native-smoke-20260925-a1.evaluation')
    parser.add_argument('--changed-evaluation', default='bfs-profile-smoke-20260925-a3.evaluation')
    args = parser.parse_args()
    store = _require_valid(args.records)
    preflight(args, store, profile)
    folder = args.runs_dir/(args.id+'.driver'); folder.mkdir(parents=True, exist_ok=False)
    receipt = {'id':args.id, 'state':'running', 'stages':[]}
    def save(): (folder/'driver.json').write_text(json.dumps(receipt, indent=2))
    serial = 0
    def call(command, *rest):
        nonlocal serial
        serial += 1
        profile._verified_lane(store.get('mbit10', 'machine'), args.lane)
        argv = [sys.executable, '-m', 'swdb', command, *map(str, rest), '--records', str(args.records), '--format', 'json']
        out, err = folder/f'{serial:02}-{command}.stdout.json', folder/f'{serial:02}-{command}.stderr.txt'
        entry = {'argv':argv, 'state':'running', 'timeout_seconds':1350}; receipt['stages'].append(entry); save()
        try: result = bounded(argv, out, err, 1350, cwd=ROOT)
        except BaseException:
            entry['state']='interrupted_or_timeout'; save(); raise
        entry.update(result, state='complete' if result['returncode']==0 else 'failed',
                     stdout_sha256=artifacts.file_hash(out), stderr_sha256=artifacts.file_hash(err)); save()
        if result['returncode']: raise RuntimeError(f'{command} failed; retained {folder}')
        return json.loads(out.read_text())
    profiles = []
    for role, evaluation_id in [('baseline', args.baseline_evaluation), ('changed', args.changed_evaluation)]:
        evaluation = call('get', evaluation_id)
        if evaluation['correctness']['state'] != 'passed': raise RuntimeError('primary correctness unavailable')
        request = {'message_version':'1.0', 'id':args.id+'.'+role+'-profile', 'evaluation':evaluation_id,
                   'memory':True, 'repetitions':1,
                   'budget':{'discovery_seconds':120, 'build_seconds':180, 'run_seconds':180, 'total_seconds':1200}}
        if profiles: request['correspondence'] = profiles[0]['id']
        path = folder/(role+'.json'); path.write_text(json.dumps(request, indent=2))
        result = call('bfs-profile', path, '--runs-dir', args.runs_dir, '--lane', args.lane)
        memory = [row for row in result['executions'] if row['kind'] == 'memory']
        if len(memory) != len(evaluation['context']['sources']) or not all(
                row['correctness']['passed'] and row.get('counter_validation', {}).get('state') == 'valid' for row in memory):
            raise RuntimeError('all sources require independently checked, validated memory executions')
        query = call('bfs-hotspots', result['id'], '--kind', 'function', '--evaluation', evaluation_id)
        if query['memory_validation']['state'] != 'consistent' or not all(row.get('available') for row in query['dynamic_memory']):
            raise RuntimeError('counter validation or requested modeled event coverage failed')
        profiles.append(result)
    before, after = profiles
    functions = call('bfs-hotspots', after['id'], '--kind', 'function')
    loops = call('bfs-hotspots', after['id'], '--kind', 'loop')
    helper = [row for row in functions['regions'] if row['name'] == 'SWDBDiscoveredHelper']
    helper_loops = [row for row in loops['regions'] if row['function'] == 'SWDBDiscoveredHelper']
    if not helper or len(helper_loops) != 2 or not all(row['metrics']['invocations'] > 0 for row in helper+helper_loops):
        raise RuntimeError('changed source helper and nested loop rediscovery failed')
    chain = call('get', after['id'], '--chain')
    summary = {'baseline_profile':before['id'], 'changed_profile':after['id'], 'evaluations':[args.baseline_evaluation,args.changed_evaluation],
               'state':'passed', 'dynamic_rows':[len(row['dynamic_memory']) for row in profiles],
               'diagnostic_executions':[len(row['executions']) for row in profiles],
               'function_rank':next(i+1 for i,row in enumerate(functions['regions']) if row['name']=='SWDBDiscoveredHelper'),
               'new_loops':len(helper_loops), 'retrieved_records':len(chain['records']), 'gain_claim':False}
    receipt['state']='passed'; save()
    (folder/'summary.json').write_text(json.dumps(summary, indent=2)); print(json.dumps(summary, indent=2))


if __name__ == '__main__': main()
