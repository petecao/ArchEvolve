"""Immutable constructed total-cell resource recipe. Created: 2026-10-06 ET.

Gross exact allocator-event costs include measured loop control. Transfer is inferred, never
physical instruction latency or a proven application upper bound.
"""
import argparse
import copy
import json
import math
import sys
import time
from pathlib import Path

from swdb import artifacts, paths, writer
from swdb.analytic import _load
from swdb.cli import Failure
from swdb.cpu_calibration import stats
from swdb.cpu_service_calibration import identity, validate_record as validate_source
from swdb.problems import Problem
from swdb.store import Record, Store

KIND='cpu_allocator_resource_calibration'
# Version1 admits only this already measured shared source; future recipes require a new version.
NATIVE_SOURCE={'CpuAllocatorWork.h':'6a4f4198d6ac45ca0c23ba130f423f3f47cf50b2ca9637376c0a8db77af4fe55',
    'CpuAllocatorTimer.cpp':'da4bd29ab0ff509742fca87750a173ff5827eedbd429e22cd0c210533b5a8c83',
    'CpuAllocatorCount.cpp':'6711bec276c97492543a370cc891b365b03948dc1cba3d1f154fdc58f3cbdf8f'}
RECIPE={'id':'gross_allocator_loop_resource_v1','denominator':'source_normalized_exact_allocator_events',
    'elapsed':'gross_uninstrumented_work_loop_only','includes_loop_control':True,
    'composition':'max_with_counted_compute_resource','transfer_basis':'inferred',
    'physical_instruction_latency':False,'proven_application_upper_bound':False,
    'freeze_scope':'after_independent_service_collection_before_application_timing',
    'minimum_gross_window_s':.05,'paired_rates_used':False}


def _services(source, identifier):
    if source.get('settings',{}).get('group')!='allocator_v1':
        raise Failure('total-cell recipe requires independent allocator_v1 calibration')
    from swdb.cpu_allocator_calibration import NAMES,ABI,REGIME
    if source['evidence_kind']=='native' and source.get('context',{}).get('source_sha256')!=NATIVE_SOURCE:
        raise Failure('resource requires frozen allocator source identity for this recipe version')
    result=[];seen=set()
    for service in source['services']:
        if service['unit']!='seconds/call':
            raise Failure('total-cell recipe requires exact allocator event units')
        scope=service.get('scope',{});op=scope.get('operation');size=scope.get('size_bytes')
        if (op not in NAMES or scope.get('event_abi')!=ABI[NAMES.index(op)] or type(size) is not int or
            not 0<size<=1048576 or scope.get('worker_scope')!='serial' or scope.get('allocator_regime')!=REGIME or
            scope.get('transfer_basis')!='inferred' or scope.get('payload_touch') is not False or
            service['id']!=f'allocator.{op}.{size}' or (op,size) in seen or
            {'operation':op,'size_bytes':size} not in source['settings'].get('cells',[])):
            raise Failure('total-cell recipe requires exact allocator ABI/size/operation and source semantics')
        seen.add((op,size))
        row=copy.deepcopy(service)
        row['paired_residual']={k:copy.deepcopy(service[k]) for k in ('parameter','seconds_per_event','missing')}
        gross=stats([t['gross_seconds']/t['events'] for t in service['trials']])
        driver=stats([t['driver_seconds']/t['events'] for t in service['trials']])
        resolved=all(math.isfinite(t['gross_seconds']) and t['gross_seconds']>=RECIPE['minimum_gross_window_s'] for t in service['trials'])
        row['paired_admission']={'admitted':False,'minimum_window_s':.05,
            'missing':(['paired_driver_window_resolution'] if any(t['driver_seconds']<.05 for t in service['trials']) else []) +
                      (['paired_gross_window_resolution'] if any(t['gross_seconds']<.05 for t in service['trials']) else [])}
        row['cost_basis']=RECIPE['id']
        row['gross_seconds_per_event']=gross
        row['driver_seconds_per_event']=driver
        row['seconds_per_event']=copy.deepcopy(gross)
        row['missing']=[] if resolved else ['total_cell_elapsed_resolution']
        row['parameter']={'value':gross['median'] if resolved else None,
            'basis':('reported' if source['evidence_kind']=='fixture' else 'inferred') if resolved else 'unknown',
            'unit':'seconds/call','source':f'Constructed total-cell resource {identifier}; {source["id"]}/{service["id"]}; gross uninstrumented elapsed / exactly proved logical allocator events, includes measured loop control; inferred transfer and maximum with counted compute resources, no physical latency or upper-bound claim.'}
        result.append(row)
    if not result:raise Failure('allocator calibration has no cells')
    return result


def _resolve(ctx, identifier):
    if hasattr(ctx,'passed'):
        source=ctx.passed(identifier,'cpu_service_calibration')
        if source is None:raise Failure('source calibration must resolve and pass its schema')
        return source
    if isinstance(ctx,Store):return _load(ctx,identifier,'cpu_service_calibration')
    raise Failure('resource recipe validation requires its typed source closure')


def validate_record(record, ctx):
    data=record.data
    if data.get('identity_sha256')!=identity(data):
        yield Problem(record.rel,'identity_sha256','resource calibration content identity differs')
    try:
        source=_resolve(ctx,data['source_calibration'])
        problems=list(validate_source(Record(Path(source['id']),source),None))
        if problems:raise Failure('invalid source calibration: '+str(problems[0]))
        finished=source.get('context',{}).get('end_state',{}).get('time_ns')
        if source['evidence_kind']=='native' and (type(finished) is not int or type(data.get('frozen_ns')) is not int or data['frozen_ns']<finished):
            raise Failure('gross allocator recipe must freeze after source service collection')
        exact={'recipe':RECIPE,'source_calibration_sha256':artifacts.digest(source),
            'source_receipt_sha256':source['receipt_sha256'],'calibration_sources':[source['id']],
            'target':source['target'],'threads':source['threads'],'backend':source['backend'],
            'evidence_kind':source['evidence_kind'],'context':source['context'],'settings':source['settings'],
            'services':_services(source,data['id'])}
        for key,value in exact.items():
            if data.get(key)!=value:
                yield Problem(record.rel,key,'resource recipe or retained inputs differ from typed source calibration')
    except (Failure,KeyError,TypeError,ValueError,ZeroDivisionError) as exc:
        yield Problem(record.rel,'source_calibration',str(exc))


def derive(args):
    from swdb.archevolve import require_team_safe
    from swdb import workflow
    if workflow.CREATION_TAGS.get('mode')=='extensa':raise Failure('CPU resource recipe requires team context')
    store=Store(args.records)
    source=_load(store,args.source_calibration,'cpu_service_calibration')
    problems=list(validate_source(Record(Path(source['id']),source),None))
    if problems:raise Failure('invalid source calibration: '+str(problems[0]))
    if source['evidence_kind']=='fixture' and not args.fixture:
        raise Failure('reported resource fixture requires --fixture; never native measurement')
    require_team_safe(store,source,command='derive-cpu-allocator-resource')
    data={'kind':KIND,'schema_version':'0.4','id':args.id,'status':'draft',
        'created':writer.today(),'updated':writer.today(),
        'provenance':[{'id':'total-cell-resource','kind':'source_code',
            'description':'Distinct inferred total-cell recipe frozen after independent service collection and before application timing over independently measured/event-counted cells; includes measured loop control, conditional maximum with counted compute resources, never application timing.', 'uri':None}],
        'format':'swdb.cpu-allocator-resource-calibration.v1','recipe':copy.deepcopy(RECIPE),'frozen_ns':time.time_ns(),
        'source_calibration':source['id'],'source_calibration_sha256':artifacts.digest(source),
        'source_receipt_sha256':source['receipt_sha256'],'calibration_sources':[source['id']],
        **{k:copy.deepcopy(source[k]) for k in ('target','threads','backend','evidence_kind','context','settings')},
        'services':_services(source,args.id)}
    data['identity_sha256']=identity(data)
    writer.commit(args.records,new=[data])
    return data


def main():
    parser=argparse.ArgumentParser(description='derive a distinct inferred total-cell allocator resource from immutable independent allocator-loop trials; no native timing')
    parser.add_argument('--records',type=Path,default=paths.RECORDS)
    parser.add_argument('--source-calibration',required=True)
    parser.add_argument('--id',required=True)
    parser.add_argument('--fixture',action='store_true')
    parser.add_argument('--format',choices=['yaml','json'],default='json')
    args=parser.parse_args()
    try:
        from swdb.cli import _emit
        _emit(derive(args),args.format)
    except (Failure,KeyError,TypeError,ValueError,OSError) as exc:
        print(str(exc),file=sys.stderr);return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
