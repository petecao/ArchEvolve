#!/usr/bin/env python3
"""Prepare one bounded clarification of the unchanged upstream strategy. 2026-09-27 ET.

No provider calls, compilation, simulation, or historical mutation. Generated
request data carries exact read-only source excerpts and build-only evidence.
"""
import copy
from decimal import Decimal, ROUND_FLOOR
import hashlib
import json
from pathlib import Path

PRIOR_ID='bfs-campaign-preparation-20260925-a1.upstream-annotated-context1'
NEW_ID='bfs-campaign-preparation-20260925-a1.upstream-annotated-context2'
PRIOR_RECORD_SHA='3ee48461ccb757686a3c32c42151d3e8758916c5ee1cbb902e0612e0a2baa6f8'
PRIOR_COMMIT='1b2250670077a2f48c7dd8b28333685c4f757982'
SOURCE_PATH='apps/dx100/benchmarks/gapbs/src/bfs.cc'
SOURCE_SHA='6835fc42dfadcb60c1c3fae543f736903977f135fd7c55cd495c0e481b572465'
SOURCE_ID='bfs-native-pilot-20260925-dx10018-a1.uniform-random.package.v1.source'
BUILD_PATH='records/evaluations/bfs-t17-build-only-20260926-a1.yaml'
BUILD_SHA='d5ed1ec5b43665379a2b8d59cc2b4cbc582502beb62f5184041079e606229215'
BUILD_BINARY_SHA='852e62314b7114079975fe25d70da4e77596490bcfa89fb4f7c64af585485527'
INITIAL_USED=Decimal('62.419636563397944')
CONTEXT1_USED=Decimal('104.55376222543418')
PRIOR_FLOOR=Decimal('1737')
REMAINDER=PRIOR_FLOOR-CONTEXT1_USED
NEXT_ALLOWANCE=int(REMAINDER.to_integral_value(rounding=ROUND_FLOOR))
CONFIG={'kind':'claude','command':['/data1/yanruj/.npm-global/bin/claude'],
        'timeout_s':600,'max_repairs':2,'total_seconds':NEXT_ALLOWANCE,'budget_usd':10}


def require(ok,reason):
    if not ok:raise ValueError(reason)


def budget():
    return {'original_provider_allowance_seconds':1800,'initial_used_seconds':float(INITIAL_USED),
       'initial_floor_remaining_seconds':1737,'context1_used_seconds':float(CONTEXT1_USED),
       'cumulative_used_seconds':float(INITIAL_USED+CONTEXT1_USED),
       'remaining_after_prior_floor_seconds':float(REMAINDER),'next_allowance_seconds':NEXT_ALLOWANCE,
       'initial_discarded_fraction_seconds':str(Decimal(1800)-INITIAL_USED-PRIOR_FLOOR),
       'second_discarded_fraction_seconds':str(REMAINDER-Decimal(NEXT_ALLOWANCE)),
       'per_call_seconds':600,'per_call_usd':10,'maximum_later_build_repairs':2,
       'budget_policy':'No clock reset or refund. Context2 and later bounded build repairs share the remaining1632 seconds.'}


def build_request(prior,source_bytes,build):
    require(prior['id']==PRIOR_ID and prior['outcome']['state']=='unresolved'
            and len(prior['attempts'])==1 and prior['repair_budget']['repairs']==0
            and Decimal(str(prior['repair_budget']['used_seconds']))==CONTEXT1_USED,
            'context1 state or consumed provider time differs')
    old=prior['request'];require(old['id']==PRIOR_ID and old['hardware_target']=='dx100-e4fc4af-4c'
                                and old['require_executable_backend'] is True,'original requested target differs')
    require(hashlib.sha256(source_bytes).hexdigest()==SOURCE_SHA,'pinned reference BFS source changed')
    target=old['parameters']['read_only_context']['target']
    require(target['id']==old['hardware_target'] and target['backend']['readiness']=='built'
            and target['backend']['id']=='dx100-gem5-se','retained target backend is not built')
    require(build['id']=='bfs-t17-build-only-20260926-a1' and build['outcome']['state']=='complete'
            and build['outcome']['stage']=='candidate_build'
            and build['request']['hardware_target']==target['id']
            and build['build']['binary_sha256']==BUILD_BINARY_SHA, 'T17 build-only evidence differs')
    stages=[s for s in build['stages'] if s['stage']=='candidate_compile']
    require(len(stages)==1 and stages[0]['returncode']==0 and stages[0]['state']=='complete','T17 compiler stage did not pass')
    argv=stages[0]['command']
    require(all(flag in argv for flag in ('-DGEM5','-DMAA','-DNUM_CORES=4','-DTILE_SIZE=16384')),
            'retained T17 DX100 build flags differ')
    lines=source_bytes.decode().splitlines(keepends=True)
    excerpts=[{'path':SOURCE_PATH,'source_snapshot':SOURCE_ID,'file_sha256':SOURCE_SHA,
               'lines':[lo,hi],'text':''.join(lines[lo-1:hi])} for lo,hi in ((63,64),(366,403))]
    new=copy.deepcopy(old);new['id']=NEW_ID
    new['parameters']['predecessor_proposal']=PRIOR_ID
    new['parameters']['original_unresolved_reason']=prior['outcome']['reason']
    new['parameters']['target_execution_clarification']={
      'scope':'Read-only clarification of the unchanged submitted strategy, target and source mapping. It adds no editable file, operation, optimization, or execution permission to the worker. The trusted evaluator handles later build and execution.',
      'requested_target':{'id':old['hardware_target'],'require_executable_backend':True,
                          'backend':copy.deepcopy(target['backend'])},
      'profile_vs_target':'The supplied native profile package records the historical CPU baseline build and measurements. Its native compiler command does not select the target for this proposal. The proposal explicitly requests dx100-e4fc4af-4c with require_executable_backend=true; the public target declares dx100-gem5-se readiness built.',
      'read_only_scope_clarification':'The retained read_only_context.scope says these headers are not editable_files and do not authorize a different optimization. That protects the submitted edit/strategy scope; it does not declare the requested DX100 backend unavailable or forbid the trusted evaluator from later executing a candidate on it.',
      'planned_evaluation':'After a candidate is produced, the trusted evaluator plans a source-identified DX100 complete-call build and bounded simulation under the existing protocol and budget. The existing T17 primary build demonstrates the build route with GEM5, MAA, NUM_CORES=4, TILE_SIZE=16384, the pinned DX100 API include directory, and m5 ABI source. That is a different candidate and proves only that retained build; it is not correctness, execution, profitability, or acceptance evidence for this proposal.',
      'retained_build_only_evidence':{'id':build['id'],'record_path':BUILD_PATH,'record_file_sha256':BUILD_SHA,
          'candidate':build['request']['candidate'],'compiler_command':argv,'returncode':0,
          'binary_sha256':BUILD_BINARY_SHA,'evidence_limit':'Other candidate build only; no new candidate test or simulated result.'},
      'slot_mapping':'The pinned bfs.cc declarations use tiles0 through tiles5 plus tilesi and tilesj, and regs0 through regs5 plus last_i_regs and last_j_regs. There are no declared tiles6/tiles7 arrays in this allocation block. DOBFSMAA serializes get_new_tile<int>() and get_new_reg<int>() allocations inside an omp critical section within its parallel region, indexed by omp_get_thread_num(). The exact excerpts below are reference context for the already submitted strategy, not permission to change it.',
      'roi_requirement':'Preserve the submitted computation and all trusted correctness/ROI protections. Any candidate allocation, initialization, slot setup, and required work must remain inside the requested DOBFS complete-call ROI. Do not move required setup outside DOBFS or outside timed scope.',
      'reference_source_excerpts':excerpts}
    require({k:v for k,v in old.items() if k not in ('id','parameters')}==
            {k:v for k,v in new.items() if k not in ('id','parameters')},'strategy, payload or protected scope changed')
    require(old['parameters']['read_only_context']==new['parameters']['read_only_context'],'prior headers/context changed')
    return new


def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('repo',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();root=args.repo.resolve();out=args.output.resolve()
    import sys
    sys.path.insert(0,str(root))
    from swdb import yamlio
    prior_path=root/'records/proposals'/(PRIOR_ID+'.yaml');build_path=root/BUILD_PATH
    require(hashlib.sha256(prior_path.read_bytes()).hexdigest()==PRIOR_RECORD_SHA,'exact closed context1 metadata differs')
    require(hashlib.sha256(build_path.read_bytes()).hexdigest()==BUILD_SHA,'exact retained T17 record differs')
    request=build_request(yamlio.load(prior_path),(root/SOURCE_PATH).read_bytes(),yamlio.load(build_path))
    require(not out.exists(),'fresh context2 preparation folder required');out.mkdir(parents=True)
    for name,value in [('upstream-annotated-context2.proposal.json',request),('upstream-annotated-context2.provider.json',CONFIG),
                       ('budget.json',budget())]:
        (out/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'state':'request_prepared_prompt_not_rendered','provider_calls':0,'output':str(out),
                      'request_bytes':(out/'upstream-annotated-context2.proposal.json').stat().st_size,'budget':budget()}))


if __name__=='__main__':main()
