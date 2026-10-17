"""Prepare DX100 reference manifests, preflight bindings, and collect supplied evidence; never execute jobs."""
from pathlib import Path
import argparse
import json
import sys
import subprocess
from hashlib import sha256
import yaml
from archevolve.dx100_validation import prepare,preflight,collect,compare_collections,guest_env_text
from archevolve.parameter_cli import write_fresh
from archevolve.evolution_store import digest
from tools.render_mermaid import load_request,RequestError


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare');p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    for name in ('preflight','collect'):
        p=sub.add_parser(name);p.add_argument('--workflow',type=Path,required=True);p.add_argument('--environment',type=Path,required=True)
        p.add_argument('--output-dir',type=Path,required=True)
        if name=='collect':p.add_argument('--receipt',type=Path,required=True)
    p=sub.add_parser('compare');p.add_argument('--baseline',type=Path,required=True);p.add_argument('--accelerated',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=='prepare':
            workflow,env,build,run,receipt=prepare(args.source_root)
            result=preflight(workflow,env)
            values={'workflow.yaml':workflow,'environment.template.yaml':env,'build-recipes.yaml':build,'run-plan.yaml':run,'receipt.template.yaml':receipt,'preflight.yaml':result}
            files={n:yaml.safe_dump(v,sort_keys=False) for n,v in values.items()}
            files['guest.env']=guest_env_text(workflow)
            templates={
                'build-receipt.template.json':{'format':'dx100-build-receipt-v0.1','workflow_sha256':digest(workflow),
                    'source_commit':workflow['source_commit'],'source_files':workflow['source_files'],'argv':None,
                    'cwd':None,'compiler_version':None,'exit_code':None,'binary_sha256':None,'macro_dump_sha256':None},
                'graph-receipt.template.json':{'format':'dx100-graph-receipt-v0.1','source_commit':workflow['source_commit'],
                    'workload_id':None,'generator_seed':27491095,'generator_options':None,'converter_sha256':None,'graph_sha256':None},
                'exit-events.template.json':{'format':'dx100-exit-events-v0.1','guest_completed':None,'events':[],
                    'roi_stats':'roi.stats.explicit-counters.txt','raw_roi_stats':'roi.stats.txt',
                    'counter_snapshot':'roi-counter-values.json','stats_block_index':0,
                    'wrapper_sha256':workflow['launcher_contract']['wrapper']['sha256'],
                    'note':'Use the wrapper-generated exit-events.json from the real run; this template is not execution evidence.'}}
            for name,value in templates.items():files[name]=json.dumps(value,indent=2)+'\n'
            files['README.md']='# DX100 16K reference validation preparation\n\nNo builds, benchmark runs, simulations or cluster submissions have occurred.\n\nBind environment.template.yaml on the confirmed Linux/x86-64 environment. See the repository guide at docs/designs/dx100-reference-validation/README.md before executing any recipe.\n\n[Workflow](workflow.yaml) · [Build recipes](build-recipes.yaml) · [Run plan](run-plan.yaml) · [Unbound preflight](preflight.yaml)\n'
        elif args.command in ('preflight','collect'):
            workflow,_=load_request(args.workflow);env,_=load_request(args.environment)
            if args.command=='preflight':result=preflight(workflow,env)
            else:
                receipt,_=load_request(args.receipt);result=collect(workflow,env,receipt,args.receipt.parent)
            files={'result.yaml':yaml.safe_dump(result,sort_keys=False),'workflow.snapshot.yaml':args.workflow.read_text(),'environment.snapshot.yaml':args.environment.read_text()}
            if args.command=='collect':files['receipt.snapshot.yaml']=args.receipt.read_text()
        else:
            b,_=load_request(args.baseline);a,_=load_request(args.accelerated);result=compare_collections(b,a)
            files={'comparison.yaml':yaml.safe_dump(result,sort_keys=False)}
        # Retain raw text-sized evidence byte-for-byte. Large binary/graph/library
        # payloads remain explicit content-hashed references, never silently deleted.
        raw={}
        if args.command=='collect':
            excluded={'binary','graph','simulator','ramulator_library'}
            for name,item in result['artifacts'].items():
                if name not in excluded and item['bytes']<=64*1024*1024:
                    data=Path(item['path']).read_bytes()
                    if sha256(data).hexdigest()!=item['sha256']:raise RequestError('Evidence changed during collection: '+name)
                    raw['evidence/'+name]=data
            result['archived_evidence_files']=sorted(raw)
            files['result.yaml']=yaml.safe_dump(result,sort_keys=False)
        write_fresh(args.output_dir,files)
        for name,data in raw.items():
            path=args.output_dir/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        print(json.dumps({'status':result['status'],'output':str(args.output_dir),'target_validated':False}))
        return 0
    except (RequestError,ValueError,TypeError,KeyError,OSError,subprocess.CalledProcessError) as exc:
        print('error: '+str(exc),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
