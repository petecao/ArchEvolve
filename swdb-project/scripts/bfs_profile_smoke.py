#!/usr/bin/env python3
"""Real native baseline/changed-helper discovery and memory diagnostics. Updated 2026-09-25.

Run on mbit10 lane 1. Results are pre-freeze diagnostics, never speedup claims.
"""
import argparse
import difflib
import json
import subprocess
import sys
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id',required=True)
    parser.add_argument('--runs-dir',type=Path,required=True)
    parser.add_argument('--records',type=Path,default=Path('records'))
    parser.add_argument('--lane',required=True)
    parser.add_argument('--baseline-evaluation',default='bfs-native-smoke-20260925-a1.evaluation')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    folder=args.runs_dir/(args.id+'.driver');folder.mkdir(parents=True,exist_ok=False)
    serial=0
    def call(command,*rest):
        nonlocal serial
        serial+=1
        result=subprocess.run([sys.executable,'-m','swdb',command,*map(str,rest),
            '--records',str(args.records),'--format','json'],cwd=root,capture_output=True,text=True,timeout=1500)
        (folder/f'{serial:02}-{command}.stdout.json').write_text(result.stdout)
        (folder/f'{serial:02}-{command}.stderr.txt').write_text(result.stderr)
        if result.returncode: raise RuntimeError(f'{command} failed: {result.stderr}; retained {folder}')
        return json.loads(result.stdout)
    def request(kind,data):
        file=folder/(data['id']+'.json');file.write_text(json.dumps(data,indent=2))
        return call(kind,file,'--runs-dir',args.runs_dir,'--lane',args.lane)
    baseline=call('get',args.baseline_evaluation)
    profiling={'message_version':'1.0','id':args.id+'.baseline-profile','evaluation':baseline['id'],
        'memory':True,'budget':{'discovery_seconds':120,'build_seconds':180,'run_seconds':180,'total_seconds':1200}}
    before=request('bfs-profile',profiling)
    if not before['regions'] or not any(x.get('available') and x.get('counter_validation',{}).get('state')=='valid' for x in before['dynamic_memory']):
        raise RuntimeError('baseline automatic regions or dynamic memory missing: '+json.dumps(before['outcome'])+' '+str(before['reasons']))
    source=call('get',baseline['source_snapshot'])
    base_candidate=call('get',baseline['candidate'])
    path='benchmarks/gapbs/src/bfs.cc'
    original=(Path(source['artifact']['path'])/path).read_text()
    changed=(Path(base_candidate['artifact']['path'])/path).read_text()
    helper='''uint64_t SWDBDiscoveredHelper(const Graph &g) {
  volatile uint64_t checksum = 0;
  for (int repeat = 0; repeat < 2000; ++repeat)
    for (NodeID vertex = 0; vertex < g.num_nodes(); ++vertex)
      checksum += static_cast<uint64_t>(g.out_degree(vertex)) + repeat;
  return checksum;
}

'''
    needle='pvector<NodeID> DOBFS('
    if changed.count(needle)!=1: raise RuntimeError('pinned DOBFS definition changed')
    changed=changed.replace(needle,helper+needle)
    body=changed.index('{',changed.index(needle))+1
    changed=changed[:body]+'\n  volatile uint64_t diagnostic_checksum = SWDBDiscoveredHelper(g);\n  (void)diagnostic_checksum;\n'+changed[body:]
    patch=''.join(difflib.unified_diff(original.splitlines(keepends=True),changed.splitlines(keepends=True),
        fromfile='a/'+path,tofile='b/'+path))
    proposal={'message_version':'1.0','id':args.id+'.proposal',
        'producer':{'name':'swdb-real-discovery-client','role':'sw','test_client':True},
        'implementation':source['implementation'],'source_snapshot':source['id'],'profile_package':baseline['profile_package'],
        'source_sha256':source['artifact']['sha256'],'regions':[r['id'] for r in source['regions']],
        'intent':'Introduce actual new helper/loop work solely to demonstrate automatic changed-source rediscovery; no performance gain intended.',
        'constraints':{'editable_files':[path],'preserve_correctness':True,'preserve_roi':True},
        'payload':{'kind':'patch','content':patch},'required_operations':[]}
    file=folder/'proposal.json';file.write_text(json.dumps(proposal,indent=2))
    submitted=call('submit',file,'--runs-dir',args.runs_dir)
    evaluation=dict(baseline['request'],id=args.id+'.evaluation',candidate=submitted['candidate'])
    evaluation['budget']={'build_seconds':180,'run_seconds':60,'total_seconds':600}
    after_eval=request('evaluate',evaluation)
    assert after_eval['correctness']['state']=='passed' and len(after_eval['timing'])==3
    after=request('bfs-profile',dict(profiling,id=args.id+'.changed-profile',evaluation=after_eval['id'],correspondence=before['id']))
    functions=call('bfs-hotspots',after['id'],'--kind','function','--evaluation',after_eval['id'])
    loops=call('bfs-hotspots',after['id'],'--kind','loop')
    new_function=[r for r in functions['regions'] if r['name']=='SWDBDiscoveredHelper']
    new_loops=[r for r in loops['regions'] if r['function']=='SWDBDiscoveredHelper']
    assert new_function and new_loops and all(r['metrics']['invocations']>0 for r in new_function+new_loops)
    assert not any(r['function']=='SWDBDiscoveredHelper' for r in before['regions'])
    assert functions['memory_validation']['state']=='consistent'
    assert all(x.get('counter_validation',{}).get('state')=='valid' for x in after['dynamic_memory'])
    assert any(x.get('available') and x.get('value',0)>0 for x in after['dynamic_memory'])
    assert all(x['correctness']['passed'] for x in after['executions'])
    chain=call('get',after['id'],'--chain')
    summary={'baseline_profile':before['id'],'changed_profile':after['id'],'evaluation':after_eval['id'],
        'function_rank':next(i+1 for i,r in enumerate(functions['regions']) if r['name']=='SWDBDiscoveredHelper'),
        'new_loops':len(new_loops),'dynamic_rows':sum(x.get('available',False) for x in after['dynamic_memory']),
        'checked_diagnostic_executions':len(after['executions']),'retrieved_records':len(chain['records']),
        'coverage':after['outcome'],'gain_claim':False}
    (folder/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
