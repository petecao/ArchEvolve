"""Run source-bound saved hardware proposals through the offline evolution loop."""
from pathlib import Path
import argparse
import sys
import yaml

from archevolve.evolution_runtime import OfflineEvolution
from archevolve.evolution_store import EvolutionStore
from archevolve.planning_bridge import HardwarePlanningBridge,SavedHardwareProposals,export_run,reflection_exchange,replay_reflection
from tools.render_mermaid import load_request,RequestError


def unavailable(request):
    raise RequestError('No live proposal or evaluator adapter is connected.')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    run=sub.add_parser('run')
    for name in ('input','catalog','source-context','proposals','store','output-dir'):
        run.add_argument('--'+name,type=Path,required=True)
    for command in ('export','export-reflection','replay-reflection'):
        p=sub.add_parser(command);p.add_argument('--store',type=Path,required=True)
        if command=='export':p.add_argument('--output-dir',type=Path,required=True)
        if command=='export-reflection':
            p.add_argument('--kind',choices=['strategy','reflector'],default='strategy')
            p.add_argument('--output',type=Path,required=True)
        if command=='replay-reflection':p.add_argument('--response',type=Path,required=True)
    args=parser.parse_args(argv);store=None
    try:
        if args.command=='run':
            if args.store.exists() or args.output_dir.exists():raise RequestError('Use fresh store and output paths.')
            document,_=load_request(args.proposals)
            store=EvolutionStore(args.store)
            proposer=SavedHardwareProposals(store,document)
            bridge=HardwarePlanningBridge(store,args.input,args.catalog,args.source_context)
            OfflineEvolution.initialize(store,**bridge.seed(len(document['entries'])))
            loop=OfflineEvolution(store,proposer,bridge.evaluate)
            try:
                loop.run_epoch()
            finally:
                export_run(store,args.output_dir)
            print(f'Replayed {len(loop.history())} proposals. No model calls or hardware evaluations. Report: {args.output_dir / "README.md"}')
        else:
            if not args.store.is_file():raise RequestError('Store does not exist.')
            store=EvolutionStore(args.store)
            loop=OfflineEvolution(store,unavailable,unavailable)
            if loop.policy['mode']!='offline_planning':raise RequestError('This command requires a structural planning campaign.')
            if args.command=='export':export_run(store,args.output_dir)
            elif args.command=='export-reflection':
                if args.output.exists():raise RequestError('Reflection output exists; use a fresh path.')
                exchange=reflection_exchange(loop,args.kind)
                args.output.parent.mkdir(parents=True,exist_ok=True)
                args.output.write_text(yaml.safe_dump(exchange,sort_keys=False))
                print('Exported exact reflection context; fill response separately: '+str(args.output))
            else:
                exchange,_=load_request(args.response)
                ref=replay_reflection(loop,exchange)
                print('Saved pending revision '+ref+'. Not activated; structural feedback cannot prove a performance gain.')
        return 0
    except (RequestError,ValueError,OSError,TypeError) as exc:
        print('error: '+str(exc),file=sys.stderr);return 2
    finally:
        if store:store.close()


if __name__=='__main__':raise SystemExit(main())
