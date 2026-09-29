#!/usr/bin/env python3
"""Real bounded Claude interpretation and native BFS diagnostics. Updated 2026-09-25.

Run inside an owned mbit10 lane. These small correctness cases do not assess gains.
"""
import argparse
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
    parser.add_argument('--routes',nargs='+',choices=['natural_language','structured_instructions','annotated_source'],
                        default=['natural_language','structured_instructions','annotated_source'])
    parser.add_argument('--reevaluate',help='retain a new evaluation of an existing candidate after an evaluator fix')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    args.runs_dir=args.runs_dir.resolve()
    folder=args.runs_dir/(args.id+'.driver')
    folder.mkdir(parents=True,exist_ok=False)
    provider=folder/'provider.json'
    provider.write_text(json.dumps({'kind':'claude','command':['claude'],'timeout_s':300,
                                   'max_repairs':1,'total_seconds':600,'budget_usd':5}))
    serial=0
    def call(command,*rest):
        nonlocal serial
        serial+=1
        argv=[sys.executable,'-m','swdb',command,*map(str,rest),
              '--records',str(args.records),'--format','json']
        result=subprocess.run(argv,cwd=root,capture_output=True,text=True,timeout=700)
        (folder/f'{serial:02}-{command}.stdout.json').write_text(result.stdout)
        (folder/f'{serial:02}-{command}.stderr.txt').write_text(result.stderr)
        if result.returncode:
            print(f'{command} failed; retained {folder}',file=sys.stderr)
            print(result.stderr,file=sys.stderr)
            # All route failures remain durable; caller may continue other routes.
            if not result.stdout.strip():
                return {'outcome':{'state':'failed','reason':result.stderr},'_cli_failed':True}
        return json.loads(result.stdout)
    summary=[]
    if args.reevaluate:
        previous=call('get',args.reevaluate)
        request=dict(previous['request'])
        request['id']=args.id+'.evaluator-fixed'
        path=folder/'reevaluate.json';path.write_text(json.dumps(request,indent=2))
        evaluated=call('evaluate',path,'--runs-dir',args.runs_dir,'--lane',args.lane)
        call('get',evaluated['id'],'--chain')
        summary.append({'route':'retained_candidate_evaluation','previous_evaluation':args.reevaluate,
            'evaluation':evaluated['id'],'correctness':evaluated.get('correctness',{}).get('state'),
            'accepted':evaluated.get('correctness',{}).get('state')=='passed' and
                       len(evaluated.get('timing',[]))==3 and not evaluated.get('gain_claim'),
            'trials':len(evaluated.get('timing',[])),'gain_claim':False})
    for route,implementation in [('natural_language','dx100-bfs-scalar'),
                                  ('structured_instructions','gapbs-bfs-do'),
                                  ('annotated_source','gapbs-bfs-do')]:
        if route not in args.routes:
            continue
        rid=args.id+'.'+route.replace('_','-')
        source=call('source-snapshot',implementation,'--id',rid+'.source','--runs-dir',args.runs_dir)
        if 'artifact' not in source:
            summary.append({'route':route,'stage':'snapshot','outcome':source});continue
        package=call('fixture-package',source['id'],'--id',rid+'.package')
        path='benchmarks/gapbs/src/bfs.cc' if implementation=='dx100-bfs-scalar' else 'src/bfs.cc'
        original=(Path(source['artifact']['path'])/path).read_text()
        if route=='natural_language':
            intent=('Remove the redundant parent[v] = u store immediately following successful '
                    'compare_and_swap(parent[v], curr_val, u) in the scalar TDStep. The successful '
                    'CAS already performs that write. Preserve the CAS, queue insertion, scout count, '
                    'and every other algorithmic step. Do not change the accelerator branch.')
            payload={'kind':route,'content':intent}
            parameters={'remove_redundant_post_cas_store':True}
        elif route=='structured_instructions':
            intent='Change only the DOBFS default alpha direction-switch parameter from 15 to 14.'
            parameters={'old_alpha':15,'new_alpha':14}
            payload={'kind':route,'content':{'function':'DOBFS','operation':'replace_default_parameter',
                'parameter':'alpha','old_value':15,'new_value':14,
                'preserve':['beta parameter','all traversal and verification code','ROI boundaries']}}
        else:
            intent='Interpret the annotation at DOBFS: change only default alpha from 15 to 16.'
            parameters={'old_alpha':15,'new_alpha':16}
            marker='int alpha = 15'
            if original.count(marker)!=1:
                raise SystemExit('pinned annotation location no longer matches')
            annotated=original.replace(marker,'/* SWDB REQUEST: change this alpha default from 15 to 16; preserve all other code. */ '+marker)
            payload={'kind':route,'content':{'files':{path:annotated}}}
        proposal={'message_version':'1.0','id':rid+'.proposal',
                  'producer':{'name':'swdb-bounded-instruction-diagnostic-client','role':'sw','test_client':True},
                  'implementation':implementation,'source_snapshot':source['id'],'profile_package':package['id'],
                  'source_sha256':source['artifact']['sha256'],'regions':[r['id'] for r in source['regions']],
                  'intent':intent,'parameters':parameters,
                  'constraints':{'editable_files':[path],'preserve_correctness':True,'preserve_roi':True},
                  'payload':payload,'required_operations':[]}
        proposal_file=folder/(rid+'.proposal.json');proposal_file.write_text(json.dumps(proposal,indent=2))
        submitted=call('submit',proposal_file,'--provider-config',provider,'--runs-dir',args.runs_dir)
        if 'candidate' not in submitted:
            summary.append({'route':route,'stage':'interpretation','proposal':submitted.get('id'),
                            'outcome':submitted.get('outcome')});continue
        evaluation_request={'message_version':'1.0','id':rid+'.evaluation','candidate':submitted['candidate'],
            'machine':'mbit10','threads':1,'sources':[0,3,8],'repetitions':1,'roi':'bfs.complete_call.v1',
            'budget':{'build_seconds':180,'run_seconds':30,'total_seconds':300},
            'comparison_baseline':implementation,'workload':{'family':'diagnostic',
                'graph':{'num_vertices':10,'directed':True,
                         'edges':[[0,1],[0,2],[1,3],[2,3],[3,4],[4,5],[5,3],[6,7]]}}}
        request_file=folder/(rid+'.evaluation.json');request_file.write_text(json.dumps(evaluation_request,indent=2))
        evaluation=call('evaluate',request_file,'--runs-dir',args.runs_dir,'--lane',args.lane)
        if evaluation.get('outcome',{}).get('state')!='complete':
            repaired=call('repair',evaluation['id'],'--provider-config',provider,'--runs-dir',args.runs_dir)
            if repaired.get('outcome',{}).get('state')=='candidate_created':
                evaluation_request.update(id=rid+'.repair-evaluation',candidate=repaired['candidate'])
                request_file=folder/(rid+'.repair-evaluation.json')
                request_file.write_text(json.dumps(evaluation_request,indent=2))
                evaluation=call('evaluate',request_file,'--runs-dir',args.runs_dir,'--lane',args.lane)
        chain=call('get',evaluation['id'],'--chain')
        success=(evaluation.get('correctness',{}).get('state')=='passed' and
                 len(evaluation.get('timing',[]))==3 and not evaluation.get('gain_claim'))
        summary.append({'route':route,'proposal':submitted['id'],'evaluation':evaluation['id'],
                        'correctness':evaluation.get('correctness',{}).get('state'),'accepted':success,
                        'trials':len(evaluation.get('timing',[])),'gain_claim':False,
                        'records_retrieved':len(chain.get('records',{}))})
    (folder/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
    return 0 if len(summary)==len(set(args.routes))+bool(args.reevaluate) and all(x.get('accepted') for x in summary) else 1

if __name__=='__main__':
    raise SystemExit(main())
