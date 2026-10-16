"""Generate optional generalization hypotheses for an existing minimum hardware plan."""
import argparse
from pathlib import Path
import sys

from archevolve.generalizations import generalization_artifacts
from archevolve.hardware_planning import query_block
from archevolve.parameter_cli import write_fresh
from tools.render_mermaid import load_request,RequestError


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--catalog',type=Path,default=Path('catalog/hardware-v0.1.yaml'))
    parser.add_argument('--max-proposals',type=int,default=32)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        plan,_=load_request(args.plan);catalog,_=load_request(args.catalog)
        if plan.get('format')!='hardware-plan-v0.1':raise RequestError('Expected a minimum hardware plan.')
        results=[query_block(catalog,b) for b in plan['blocks']]
        files=generalization_artifacts(plan,results,args.max_proposals)
        files['minimum-plan.snapshot.yaml']=args.plan.read_text()
        files['catalog.snapshot.yaml']=args.catalog.read_text()
        write_fresh(args.output_dir,files)
        print('Wrote optional proposals with unresolved support and cost: '+str(args.output_dir/'generalizations.md'))
        return 0
    except (RequestError,ValueError,TypeError,KeyError,OSError) as exc:
        print('error: '+str(exc),file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
