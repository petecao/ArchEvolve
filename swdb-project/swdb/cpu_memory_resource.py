"""Immutable constructed total-cell resource recipe. Created: 2026-10-06 ET.

Gross useful-request costs include driver work. Transfer is inferred, never
physical instruction latency or a proven application upper bound.
"""
import argparse
import copy
import json
import math
import sys
from pathlib import Path

from swdb import artifacts, paths, writer
from swdb.analytic import _load
from swdb.cli import Failure
from swdb.cpu_calibration import stats
from swdb.cpu_service_calibration import identity, validate_record as validate_source
from swdb.problems import Problem
from swdb.store import Record, Store

KIND='cpu_memory_resource_calibration'
RECIPE={'id':'gross_constructed_resource_v1','denominator':'source_normalized_logical_requests',
    'elapsed':'gross_uninstrumented_native_cell','includes_driver_work':True,
    'composition':'max_with_compute','transfer_basis':'inferred',
    'physical_instruction_latency':False,'proven_application_upper_bound':False}


def _services(source, identifier):
    if source.get('settings',{}).get('group')!='memory_v1':
        raise Failure('total-cell recipe requires independent memory_v1 calibration')
    result=[]
    for service in source['services']:
        if service['unit']!='seconds/request':
            raise Failure('total-cell recipe requires logical request units')
        row=copy.deepcopy(service)
        row['paired_residual']={k:copy.deepcopy(service[k]) for k in ('parameter','seconds_per_event','missing')}
        gross=stats([t['gross_seconds']/t['events'] for t in service['trials']])
        driver=stats([t['driver_seconds']/t['events'] for t in service['trials']])
        resolved=all(math.isfinite(t['gross_seconds']) and t['gross_seconds']>0 for t in service['trials'])
        row['cost_basis']=RECIPE['id']
        row['gross_seconds_per_request']=gross
        row['driver_seconds_per_request']=driver
        row['seconds_per_event']=copy.deepcopy(gross)
        row['missing']=[] if resolved else ['total_cell_elapsed_resolution']
        row['parameter']={'value':gross['median'] if resolved else None,
            'basis':('reported' if source['evidence_kind']=='fixture' else 'inferred') if resolved else 'unknown',
            'unit':'seconds/request','source':f'Constructed total-cell resource {identifier}; {source["id"]}/{service["id"]}; gross uninstrumented elapsed / exactly proved logical requests, includes driver work; inferred transfer and max composition with compute, no physical latency or upper-bound claim.'}
        result.append(row)
    if not result:raise Failure('memory calibration has no cells')
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
    require_team_safe(store,source,command='derive-cpu-memory-resource')
    data={'kind':KIND,'schema_version':'0.4','id':args.id,'status':'draft',
        'created':writer.today(),'updated':writer.today(),
        'provenance':[{'id':'total-cell-resource','kind':'source_code',
            'description':'Prospective inferred total-cell recipe over independently measured/request-counted cells; includes driver work, max composition, never application timing.', 'uri':None}],
        'format':'swdb.cpu-memory-resource-calibration.v1','recipe':copy.deepcopy(RECIPE),
        'source_calibration':source['id'],'source_calibration_sha256':artifacts.digest(source),
        'source_receipt_sha256':source['receipt_sha256'],'calibration_sources':[source['id']],
        **{k:copy.deepcopy(source[k]) for k in ('target','threads','backend','evidence_kind','context','settings')},
        'services':_services(source,args.id)}
    data['identity_sha256']=identity(data)
    writer.commit(args.records,new=[data])
    return data


def main():
    parser=argparse.ArgumentParser(description='derive a distinct inferred total-cell memory resource from immutable independent service trials; no native timing')
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
