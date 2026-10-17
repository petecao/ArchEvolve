"""Explicitly author a pinned replay fixture; does not generate model proposals.

Run deliberately after reviewing changed source pins. The replay command never
updates stale pins or changes saved choices on the user's behalf.
"""
from pathlib import Path
from copy import deepcopy
import argparse
import sys
import yaml

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from archevolve.evolution_store import digest
from archevolve.planning_bridge import HardwarePlanningBridge


def fixture():
    # A store is only needed when evaluating, not when reading the planning context.
    bridge=HardwarePlanningBridge(None,ROOT/'examples/received/bfs-sparse.features.v1.2.yaml',
        ROOT/'catalog/hardware-v0.1.yaml',ROOT/'examples/bfs.source-observations.yaml')
    seed=bridge.seed(3)
    parent=digest({'baseline_task':bridge.task_id,'input':bridge.task_input})
    indexed=next(b['id'] for b in bridge.plan['blocks'] if b['family']=='indexed-read')
    cas=next(b['id'] for b in bridge.plan['blocks'] if b['family']=='effect-read_modify_write-cas')
    entries=[]
    for eid,did,target in [('dx100-indexed-reads','dx100-artifact-e4fc4af',indexed),
                           ('maple-indexed-reads-needs-evidence','maple-isca2022',indexed),
                           ('unsupported-dx100-cas','dx100-artifact-e4fc4af',cas)]:
        choices=[{'block_id':b['id'],'action':'retain_cpu'} for b in bridge.plan['blocks']]
        next(c for c in choices if c['block_id']==target).update(action='catalog_option',design_id=did,execution_role='execute')
        content={'parent_ref':parent,'mutation':'placement','design':{'format':'hardware-block-selection-v0.1',
            'bindings':deepcopy(bridge.bindings),'block_choices':choices},
            'rationale':'Hand-authored replay fixture to exercise '+eid+'. This is not an autonomous discovery or a speedup claim.',
            'obligations':['Preserve source behavior; discharge exact catalog mapping, visibility and completion requirements before rewriting.']}
        entries.append({'id':eid,'task_id':bridge.task_id,'core_sha256':digest(seed['core']),'strategy_sha256':digest(seed['strategy']),
                        'history_sha256':digest([]),'content':content})
    return {'format':'saved-hardware-proposals-v0.1',
            'provenance':'Hand-authored BFS replay fixtures: two conditional catalog choices and one intentional unsupported-CAS rejection. No model calls.',
            'entries':entries}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('Output already exists; use a fresh file and review any pin changes.')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(yaml.safe_dump(fixture(),sort_keys=False))


if __name__=='__main__':main()
