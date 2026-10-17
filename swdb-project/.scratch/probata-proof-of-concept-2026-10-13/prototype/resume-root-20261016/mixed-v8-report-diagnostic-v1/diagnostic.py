"""2026-10-16 ET. INERT all-eight mixed report-schema/predicate diagnostic.

Every predicate is observed independently; a schema mismatch cannot prevent the
other seven contexts from being described. No record, report or premise is
accepted or repaired. Original SMT/C/AST/trace/source bytes stay remote.
"""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import sys
import time

RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-36266e10-mixed-pair-public-v8')
PROFILE=RAW/'mixed-pair-profile'
ROOT=PROFILE/'pytest/test_actual_mixed_pair_bodies_0'
MAX_JSON=4*1024**2
CHECKS=0
GIT_ACTIVE=False

# __REVIEWED_HELPERS__
# __REVIEWED_RAW_MEMBERSHIP_AND_RECORD_ORDER__


def schema(value):
    result={'type':type(value).__name__}
    if isinstance(value,(dict,list)):result['items']=len(value)
    if isinstance(value,dict):result['keys']=sorted(value)
    if isinstance(value,list):result['element_types']=sorted({type(x).__name__ for x in value})
    return result


def predicate(rows,label,fn):
    try:rows.append({'predicate':label,'value':bool(fn())})
    except Exception as exc:rows.append({'predicate':label,'value':None,'exception':type(exc).__name__,'reason':str(exc)[:256]})


def fields(value,names):
    if not isinstance(value,dict):return {'malformed':schema(value)}
    return {k:value[k] for k in names if k in value}


def compact_goal(value):
    return {'schema':schema(value),**fields(value,('goal','property','function','line','smoke','passed','status','solver','seconds'))}


def obtain(directory,name,errors):
    try:return read(directory/name)
    except Exception as exc:
        errors.append({'file':name,'error_type':type(exc).__name__,'reason':str(exc)[:256]})
        return None


def wp_diagnostic(directory,record):
    errors=[];checks=[]
    inventory=obtain(directory,'wp-inventory.json',errors)
    standard=obtain(directory,'wp-goals.json',errors)
    native=inventory.get('goals') if isinstance(inventory,dict) else None
    props=inventory.get('properties') if isinstance(inventory,dict) else None
    predicate(checks,'complete native WP report',lambda:inventory['complete'] is True and inventory['version']=='1')
    predicate(checks,'native goals unique',lambda:len({g['goal'] for g in native})==len(native))
    predicate(checks,'standard goals unique',lambda:len({g['goal'] for g in standard})==len(standard))
    predicate(checks,'complete native/standard WP goal identity',lambda:{g['goal'] for g in native}=={g['goal'] for g in standard})
    predicate(checks,'native/standard property owner',lambda:all(all(g.get(k)=={p['goal']:p for p in standard}[g['goal']].get(k)
        for k in ('goal','property','function','line','smoke','passed')) for g in native))
    predicate(checks,'unique complete native property inventory',lambda:len({p['property'] for p in props})==len(props))
    predicate(checks,'retained full WP query input',lambda:(directory/'wp_input.c').is_file() and not (directory/'wp_input.c').is_symlink())
    result={'record':record['id'],'subject':record['subject'],'directory':str(directory),'predicates':checks,'read_errors':errors,
            'native_document_schema':schema(inventory),'standard_document_schema':schema(standard),
            'native_goals':[compact_goal(g) for g in native] if isinstance(native,list) else schema(native),
            'standard_goals':[compact_goal(g) for g in standard] if isinstance(standard,list) else schema(standard),
            'record_goals':[compact_goal(g) for g in record['goals']],
            'record_pins':fields(record['pins'],('code','contract','method_version','std_models','c_lowering','proof_setup_check')),
            'report_pins':[]}
    for name in ('wp-inventory.json','wp-goals.json','wp-properties.csv','frama-c.log','wp_input.c'):
        try:result['report_pins'].append({'name':name,**pin(directory/name)})
        except Exception as exc:errors.append({'file':name,'error_type':type(exc).__name__})
    if isinstance(native,list) and isinstance(standard,list):
        ns={g.get('goal') for g in native if isinstance(g,dict)};ss={g.get('goal') for g in standard if isinstance(g,dict)}
        result['native_only_goal_ids']=sorted(ns-ss,key=str);result['standard_only_goal_ids']=sorted(ss-ns,key=str)
        result['shared_owner_field_differences']=[]
        for goal in sorted(ns&ss,key=str):
            left=[g for g in native if g.get('goal')==goal];right=[g for g in standard if g.get('goal')==goal]
            if len(left)==len(right)==1:
                mismatch=[k for k in ('goal','property','function','line','smoke','passed') if left[0].get(k)!=right[0].get(k)]
                if mismatch:result['shared_owner_field_differences'].append({'goal':goal,'fields':mismatch})
    try:
        if isinstance(props,list):
            result['properties']=[{**fields(p,('id','property','variant','function','line','status','extern','origin','dependencies')),
                'schema':schema(p),'description_sha256':digest(p.get('description')),'call_context_sha256':digest(p.get('call_context'))} for p in props if isinstance(p,dict)]
            names={p.get('property') for p in props if isinstance(p,dict)}
            result['duplicate_property_labels']=sorted({n for n in names if sum(p.get('property')==n for p in props)>1},key=str)
            result['missing_dependency_labels']=sorted({d for p in props for d in p.get('dependencies',[]) if d not in names},key=str)
            result['unbound_origin_labels']=sorted({p.get('origin') for p in props if p.get('origin') is not None and p.get('origin') not in names},key=str)
            result['property_closure_schema']=schema(inventory.get('property_closure'))
            result['property_closure_sha256']=digest(inventory.get('property_closure'))
    except Exception as exc:errors.append({'section':'property_metadata','error_type':type(exc).__name__,'reason':str(exc)[:256]})
    try:
        raw=read_bytes(directory/'wp-properties.csv').decode();reader=csv.DictReader(io.StringIO(raw),delimiter='\t');rows=list(reader)
        result['CSV']={'headers':reader.fieldnames,'rows':len(rows),'metadata_rows':[]}
        allowed={'kind','file','function','property','goal','id','line','status','variant','origin','extern'}
        for row in rows:
            result['CSV']['metadata_rows'].append({k:(value if k.lower() in allowed else {'sha256':digest(value),'characters':len(value)}) for k,value in row.items()})
    except Exception as exc:errors.append({'file':'wp-properties.csv','error_type':type(exc).__name__,'reason':str(exc)[:256]})
    try:
        log=read_bytes(directory/'frama-c.log').decode();result['printed_export_ids']=re.findall(r'(?m)^\s*(?:\[wp[^\]]*\]\s*)?EXPORT GOAL\s+(\S+)',log)
        result['printed_import_names']=sorted(set(re.findall(r'\(\* use ([\w.]+) \*\)|\[wp:why3:compile\] use\s+(?:import\s+)?([\w.]+)',log)))
    except Exception as exc:errors.append({'file':'frama-c.log','error_type':type(exc).__name__})
    return result


def cbmc_diagnostic(directory,record):
    errors=[];checks=[];document=obtain(directory,'cbmc.json',errors)
    results=[row for message in document if isinstance(message,dict) for row in message.get('result',[])] if isinstance(document,list) else []
    goals={g.get('goal'):g for g in record['goals'] if isinstance(g,dict)}
    predicate(checks,'complete CBMC structured output array',lambda:isinstance(document,list))
    predicate(checks,'complete unique CBMC property IDs',lambda:bool(results) and len({r['property'] for r in results})==len(results))
    predicate(checks,'every actual CBMC property is retained in normal record',lambda:set(goals)=={r['property'] for r in results})
    predicate(checks,'actual CBMC status/record agreement',lambda:all(r['status'].lower()==goals[r['property']]['status'] for r in results))
    wrong=record['subject']['id']=='contract.fixture_pair_pointer_wrong_identity'
    wanted={'swdb_reach.end'}|({'contract.fixture_pair_pointer_wrong_identity#post.ensures1'} if wrong else set())
    predicate(checks,'exact reachability plus intended negative postcondition failures',lambda:{goals[r['property']]['property'] for r in results if r['status']=='FAILURE'}==wanted)
    predicate(checks,'no failed unwind property hidden by result',lambda:not any('unwind' in r['property'].lower() or 'unwind' in r.get('description','').lower() for r in results if r['status']=='FAILURE'))
    agreement=(record.get('settings') or {}).get('agreement',{})
    predicate(checks,'exact bounded49 independent C/C++ draws',lambda:agreement['verdict']=='agree' and agreement['runs']==49 and agreement['sampled'] is False)
    predicate(checks,'physical bounded native output pins',lambda:pin(directory/'differential_c.out')['sha256']==agreement['c_output_sha256'] and pin(directory/'differential_cxx.out')['sha256']==agreement['cxx_output_sha256'])
    replay=(record.get('counterexample') or {}).get('replay',{})
    if wrong:predicate(checks,'original C++ counterexample replay artifact',lambda:replay.get('replayed') is True and (directory/'replay_cxx.cc').is_file() and record['settings']['forms']['cxx']=='refuted (counterexample replayed)')
    result={'record':record['id'],'subject':record['subject'],'directory':str(directory),'predicates':checks,'read_errors':errors,
            'structured_document_schema':schema(document),'all_properties':[{'schema':schema(r),**fields(r,('property','status','sourceLocation')),'description_sha256':digest(r.get('description'))} for r in results],
            'record_goals':[compact_goal(g) for g in record['goals']],
            'agreement':{'schema':schema(agreement),**fields(agreement,('verdict','runs','sampled','c_output_sha256','cxx_output_sha256'))},
            'normal_forms':(record.get('settings') or {}).get('forms'),
            'replay_metadata':{'schema':schema(replay),**fields(replay,('replayed','exit_code'))},'physical_artifact_pins':[]}
    # Do not export trace, input/source text or binary; exact path/size/hash only.
    for relative,row in CONTEXT['raw_regular_pins'].items():
        path=RAW/relative
        if path.parent==directory:result['physical_artifact_pins'].append({'name':path.name,**pin(path)})
    actual={r.get('property') for r in results};result['native_only_property_ids']=sorted(actual-set(goals),key=str);result['record_only_property_ids']=sorted(set(goals)-actual,key=str)
    return result


def main():
    signal.alarm(60);resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));sys.addaudithook(audit)
    before=raw_membership()
    for relative,wanted in CONTEXT['raw_regular_pins'].items():
        got=pin(RAW/relative);need(got['sha256']==wanted['sha256'] and got['bytes']==wanted['bytes'],'exact original raw before diagnostic')
    records=record_order(read(ROOT/'actual-mixed-pair-progress.json'))
    contexts=[]
    for index,record in enumerate(records):
        directory=ROOT/'runs'/record['id']/('wp' if index<6 else 'cbmc')
        try:result=wp_diagnostic(directory,record) if index<6 else cbmc_diagnostic(directory,record)
        except Exception as exc:result={'record':record['id'],'context_error_type':type(exc).__name__,'reason':str(exc)[:256]}
        contexts.append(result)
    for relative,wanted in CONTEXT['raw_regular_pins'].items():need(pin(RAW/relative)['sha256']==wanted['sha256'],'original raw after diagnostic')
    need(raw_membership()==before,'complete raw membership pre/post')
    result={'date':'2026-10-16 ET','classification':'ALL_EIGHT_REPORT_SCHEMA_PREDICATE_DIAGNOSTIC_ONLY','contexts':contexts,
            'checks':CHECKS,'raw_pre_post_equal':True,'original_cold_refusal_preserved':CONTEXT['original_refusal'],
            'records_from_exact_pinned_progress_JSON':'Physical YAML pins are checked by complete raw census; original reader already reconciled exact YAML/progress before its preserved failure. No YAML package execution occurs here.',
            'scientific_or_semantic_cold_acceptance':False,'source_body_Typed_caller_default_public_record_acceptance':False,
            'full_hypothesis_import_task_or_trace_reconstruction_accepted':False,'probe_tools_or_proofs_rerun':False}
    payload=compact(result)+b'\n';need(len(payload)<=512*1024,'compact diagnostic output cap');sys.stdout.buffer.write(payload);return 2


if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        sys.stdout.buffer.write(compact({'classification':'REFUSED_MIXED_REPORT_DIAGNOSTIC','error_type':type(exc).__name__,'reason':str(exc)[:1024],'scientific_acceptance':False})+b'\n');raise SystemExit(1)
