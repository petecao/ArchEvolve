"""Reproduce BFS and synthetic mixed-access planning views without APIs or evaluation."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from archevolve.__main__ import reference_context
from archevolve.evidence_select import capability_requests
from archevolve.hardware_planning import plan_hardware, planning_artifacts, query_block
from archevolve.normalize import load_normalized
from archevolve.workload_context import bind_context, request_groups
from tools.render_mermaid import RequestError, load_request


def generate():
    catalog, catalog_hash = load_request(ROOT / 'catalog/hardware-v0.1.yaml')
    context, context_hash = load_request(ROOT / 'examples/bfs.source-observations.yaml')
    case = load_normalized(ROOT / 'examples/received/bfs-sparse.features.v1.2.yaml', reference_context(ROOT))
    case = bind_context(case, context, context_hash, 'examples/bfs.source-observations.yaml')
    requests, _ = capability_requests(case)
    mixed, mixed_hash = load_request(ROOT / 'examples/planning/mixed-access.yaml')
    inputs = [('bfs',case,requests,request_groups(case,requests)),
              ('mixed',mixed['case'],mixed['capability_requests'],mixed['source_groups'])]
    output, plans = {}, {}
    for name, workload, members, source_groups in inputs:
        plan = plan_hardware(workload,members,source_groups)
        results = [query_block(catalog,block) for block in plan['blocks']]
        files = planning_artifacts(plan,results)
        # The full normal CLI stores every catalog contract; this review bundle
        # keeps clause identities and coverage summaries, linked to a pinned catalog.
        compact = [{k:v for k,v in r.items() if k != 'capability_results'} for r in results]
        files['block-catalog-results.yaml'] = yaml.safe_dump({
            'format':'block-catalog-summary-v0.1','catalog_ref':'catalog/hardware-v0.1.yaml',
            'catalog_sha256':catalog_hash,'results':compact},sort_keys=False)
        for file,text in files.items():
            output[name+'/'+file]=text
        plans[name]=plan['counts']
    identity = {'catalog_sha256':catalog_hash,'bfs_input_sha256':case['input_sha256'],
                'source_context_sha256':context_hash,'mixed_fixture_sha256':mixed_hash,
                'code_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in (
                    'tools/demo_hardware_planning.py','archevolve/hardware_planning.py',
                    'archevolve/evidence_select.py','archevolve/hardware_catalog.py','archevolve/normalize.py',
                    'archevolve/workload_context.py','archevolve/__main__.py')}}
    output['manifest.json']=json.dumps({'format':'prelookup-planning-demo-v0.1','identity':identity,
        'llm_calls':0,'evaluation_performed':False,'synthetic_cases':['mixed'],'counts':plans,
        'artifact_sha256':{p:hashlib.sha256(t.encode()).hexdigest() for p,t in output.items()}},indent=2)+'\n'
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    protected=[ROOT/'catalog',ROOT/'examples',ROOT/'archevolve',ROOT/'tools']
    target=args.output_dir.resolve()
    if any(target==p or p in target.parents for p in protected):
        parser.error('Output must be separate from source, input and catalog directories.')
    output=generate()
    existing=[str(args.output_dir/p) for p in output if (args.output_dir/p).exists()]
    if existing:
        parser.error('Use a fresh output directory; existing generated artifacts are preserved.')
    for path,text in output.items():
        file=args.output_dir/path
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_text(text)
    print(f'Wrote {len(output)} offline planning artifacts to {args.output_dir}')


if __name__=='__main__':
    main()
