"""Create parameter templates, enumerate reviewed configurations, compare imported evidence."""
import argparse
import json
from pathlib import Path
import sys
import yaml

from archevolve.parameter_exploration import template, enumerate_configurations, evaluation_template, compare_evaluations
from tools.render_mermaid import load_request, RequestError


def artifacts(candidate, space):
    plan=enumerate_configurations(candidate,space)
    output={'candidate.snapshot.yaml':yaml.safe_dump(candidate,sort_keys=False),
            'parameter-space.snapshot.yaml':yaml.safe_dump(space,sort_keys=False),
            'exploration.yaml':yaml.safe_dump(plan,sort_keys=False),
            'evaluations.template.yaml':yaml.safe_dump(evaluation_template(plan),sort_keys=False)}
    for config in plan['configurations']:
        root='configurations/'+config['id']+'/'
        output[root+'configuration.yaml']=yaml.safe_dump(config,sort_keys=False)
        output[root+'software-handoff.yaml']=yaml.safe_dump(config['software_handoff'],sort_keys=False)
        output[root+'evaluation-binding.template.yaml']=yaml.safe_dump({'configuration_id':config['id'],
            'implementation':{'configuration_sha256':config['sha256'],'software_sha256':None,'hardware_sha256':None,'build_sha256':None},
            'evaluation':None},sort_keys=False)
    lines=['# Bounded parameter exploration','', '**Offline enumeration only; no hardware/software execution or cost estimation.**','',
           'Status: `'+plan['status']+'`. Synthetic: `'+str(plan['synthetic']).lower()+'`.','',
           f"Checked {plan['combinations_checked']} combinations; emitted {len(plan['configurations'])} configurations. Truncated: {plan['truncated']}.",'',
           'Unknown legality fields block enumeration; unknown software impacts remain pending; unknown costs remain null.',
           'All artifact references use the bundle root. Candidate snapshots and catalog reference values are unchanged.','',
           '[Plan and rejections](exploration.yaml) · [Frozen space](parameter-space.snapshot.yaml) · [Original candidate](candidate.snapshot.yaml)','']
    if plan['unknowns']:
        lines += ['## Unresolved inputs','']+['- '+x for x in plan['unknowns']]+['']
    for c in plan['configurations']:
        lines.append('- ['+c['id']+'](configurations/'+c['id']+'/configuration.yaml): `'+json.dumps(c['identity']['values'],sort_keys=True)+'`')
    output['README.md']='\n'.join(lines)+'\n'
    return output,plan


def write_fresh(directory,output):
    if directory.exists():
        raise RequestError('Choose a fresh output directory; existing artifacts are never overwritten.')
    directory.mkdir(parents=True)
    for name,value in output.items():
        path=directory/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(value)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    t=sub.add_parser('template')
    t.add_argument('--candidate',type=Path,required=True)
    t.add_argument('--input-sha256',required=True)
    t.add_argument('--catalog-sha256',required=True)
    t.add_argument('--output',type=Path,required=True)
    t.add_argument('--synthetic',action='store_true')
    dx=sub.add_parser('dx100-candidates',help="Import Eric's source-supported tile candidates without admitting a legal domain")
    dx.add_argument('--candidate',type=Path,required=True)
    dx.add_argument('--input-sha256',required=True)
    dx.add_argument('--catalog-sha256',required=True)
    handoff=Path(__file__).resolve().parents[1]/'docs/designs/dx100-parameter-domain'
    dx.add_argument('--contract',type=Path,default=handoff/'contract.yaml')
    dx.add_argument('--verification',type=Path,default=handoff/'verification.json')
    dx.add_argument('--published-results',type=Path,default=handoff/'published-dx100-calibration.json')
    dx.add_argument('--max-candidates',type=int,default=6)
    dx.add_argument('--output-dir',type=Path,required=True)
    for name in ('enumerate','compare'):
        p=sub.add_parser(name)
        p.add_argument('--candidate',type=Path,required=True)
        p.add_argument('--space',type=Path,required=True)
        p.add_argument('--output-dir',type=Path,required=True)
        if name=='compare':
            p.add_argument('--evaluations',type=Path,required=True)
            p.add_argument('--cohort',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        candidate,_=load_request(args.candidate)
        if args.command=='dx100-candidates':
            from archevolve.dx100_parameter_adapter import prepare_candidates
            output,result=prepare_candidates(candidate,args.input_sha256,args.catalog_sha256,
                args.contract,args.verification,args.published_results,args.max_candidates)
            write_fresh(args.output_dir,output)
            print(json.dumps({'output':str(args.output_dir),'status':result['status'],
                              'candidates':result['candidate_count'],'admitted_configurations':0}))
        elif args.command=='template':
            if args.output.exists(): raise RequestError('Template output exists; choose a new file.')
            value=template(candidate,args.input_sha256,args.catalog_sha256,args.synthetic)
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(yaml.safe_dump(value,sort_keys=False))
            print('Wrote unresolved parameter template: '+str(args.output))
        else:
            space,_=load_request(args.space)
            if args.command=='enumerate':
                output,result=artifacts(candidate,space)
            else:
                batch,_=load_request(args.evaluations); cohort,_=load_request(args.cohort)
                result=compare_evaluations(candidate,space,batch,cohort)
                output={'comparison.yaml':yaml.safe_dump(result,sort_keys=False),
                        'evaluations.received.yaml':args.evaluations.read_text(),'cohort.snapshot.yaml':args.cohort.read_text(),
                        'parameter-space.snapshot.yaml':args.space.read_text(),'candidate.snapshot.yaml':args.candidate.read_text()}
            write_fresh(args.output_dir,output)
            print(json.dumps({'output':str(args.output_dir),'status':result.get('status',result.get('frontier',{}).get('status')),'configurations':len(result.get('configurations',[]))}))
        return 0
    except (RequestError,ValueError,OSError,TypeError) as exc:
        print('error: '+str(exc),file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
