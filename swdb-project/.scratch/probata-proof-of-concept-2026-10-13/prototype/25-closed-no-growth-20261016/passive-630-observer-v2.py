"""2026-10-16 ET. Read-only observer over settled projected-C generation630.

No native/compiler/verifier/solver, project import, subprocess or remote write.
The actual entry refusal and ordinary not_proven outcome remain untouched.
"""
import ast
import collections
import csv
import hashlib
import io
import json
import re
import signal
import stat
import sys
import time
from pathlib import Path

ROOT=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-615ddf50-t25-closed-no-growth-public-v1')
PROFILE=ROOT/'closed-no-growth-public-v1-profile'
PROJECT=Path('/data1/yanruj/probata-resume-20261016-615ddf50/swdb-project')
SOURCE='615ddf504fed61b9f6c6e4663760d006ecaf255b'
ENTRY_SHA='fe38605db3e05034870dff4e12e523607ba4370e79f8f50a064097a93f49e30a'
EXPECTED_SHA='e51ca215b6f91eefbe6ec62d93d11e1397b32773eaa39f0d8b666a1141816a2b'
RESULT_SHA='b25c1f791c7273f3f79e50b96e4e905cf4bedf6fda5b94e6e2683bcd18d89f30'
LOG_SHA='5ba36b975ccdcf981fe3be4f21597ad1d014f4f30515919e7cdadb4b13a5ac00'


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):digest.update(block)
    return digest.hexdigest()


def pin(path):
    return {'path':str(path),'bytes':Path(path).stat().st_size,'sha256':sha(path)}


def snapshot(root):
    rows=[]
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or not(path.is_file() or path.is_dir()):
            raise ValueError('settled raw tree contains a special or redirected path')
        if path.is_file():rows.append({'relative':str(path.relative_to(root)),**pin(path)})
    return rows


def definitions(raw,names):
    lines=raw.decode().splitlines(keepends=True)
    found={n.name:''.join(lines[n.lineno-1:n.end_lineno]) for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name in names}
    assert set(found)==set(names)
    return found


def main():
    started=time.monotonic();signal.alarm(120)
    attempts=[]
    def audit(name,args):
        if name in {'subprocess.Popen','os.system','os.posix_spawn','os.exec','os.fork','ctypes.dlopen'}:
            attempts.append(name);raise RuntimeError('passive observer forbids external/native execution')
        if name=='open' and len(args)>1 and isinstance(args[1],str) and any(flag in args[1] for flag in 'wax+'):
            raise RuntimeError('passive observer forbids file writes')
    sys.addaudithook(audit)
    before=snapshot(ROOT)
    entry=(PROFILE/'entry.py').read_bytes();expected=json.loads((PROFILE/'expected.json').read_bytes())
    assert sha(PROFILE/'entry.py')==ENTRY_SHA and sha(PROFILE/'expected.json')==EXPECTED_SHA
    assert sha(PROFILE/'result.json')==RESULT_SHA and sha(PROFILE/'projected-c/frama-c.log')==LOG_SHA
    actual=json.loads((PROFILE/'result.json').read_bytes())
    assert actual['producer_complete'] is False and actual['error_type']=='ValueError' and actual['error']=='foreign goal lacks exact surviving constructor call/statement/source binding'
    assert actual['source_commit']==SOURCE and actual['resources']['exit_code']==0
    assert not any(actual['resources'][name] for name in ['out_of_memory','timed_out','output_limit'])
    assert actual['source_typed_bridge_established'] is False and actual['caller_acceptance'] is False
    directory=PROFILE/'projected-c'
    assert sha(directory/'wp_input.c')==expected['wp_input_sha256'] and sha(PROFILE/'projected.c')==expected['projected_sha256']
    assert sha(PROFILE/'lowering.original.c')==expected['lowered_sha256'] and sha(PROFILE/'original.cc')==expected['source_sha256']
    cert=json.loads((PROFILE/'closed-view-certificate.json').read_bytes())
    assert cert['original_lowering_inverse_equal'] is True and cert['source_typed_bridge_established'] is False
    assert cert['caller_premises_added']==[] and cert['current_proof_records_admitted']==[] and cert['cfg']['fallback_reachable'] is False
    anchor=definitions(entry,{'lineage'})['lineage'];scope={}
    exec(compile(anchor,'<reviewed-original-lineage>','exec'),scope)
    assert scope['lineage'](json.loads((PROFILE/'anchors.fresh.json').read_bytes()))==expected['cached_anchor_lineage']
    # Exactly the normal native proof's registered synthetic property form.
    # The actual generation-only entry's unregistered form remains refused.
    helpers=definitions(entry,{'closed_census','common_exports'})
    old="p['status_registered'] is not False or p['description'] != 'wp_smoke_dead_call'"
    new="p['status_registered'] is not True or p['description'] != 'wp_smoke_dead_call'"
    old_origin="p['property_export_origin'] != 'wp-smoke-reference'"
    new_origin="p['property_export_origin'] != 'registered'"
    original=helpers['closed_census']
    assert original.count(old)==1 and original.count(old_origin)==1
    repaired=original.replace(old,new).replace(old_origin,new_origin)
    assert repaired.replace(new,old).replace(new_origin,old_origin)==original
    captured=[]
    def capture(path,value,output_root,policy):
        assert path==directory/'task-census.json' and output_root==ROOT
        captured.append(value)
    namespace={'json':json,'Path':Path,'re':re,'hashlib':hashlib,'sha':sha,'pin':pin,'bounded_json':capture}
    exec(compile(helpers['common_exports']+'\n'+repaired,'<read-only-exact-registered-smoke-observer>','exec'),namespace)
    census=namespace['closed_census'](directory,expected,ROOT,expected['resource_policy'])
    assert captured==[census] and census['native_goals']==21 and census['native_properties']==72
    assert census['ordinary_count']==17 and census['smoke_count']==4
    assert len(census['call_bindings'])==1 and census['call_bindings'][0]['statement_id']==47 and census['call_bindings'][0]['source_line']==129
    assert census['missing_noninternal_tasks']==[]
    outcome=json.loads((directory/'outcome.json').read_bytes())
    assert outcome['verdict']=='not_proven' and outcome['failure_class']=='unclassified_wp_outcome'
    assert outcome['why']==r'not-Valid property has no classified failing goal: assigns *this;'
    inventory=json.loads((directory/'wp-inventory.json').read_bytes());standard=json.loads((directory/'wp-goals.json').read_bytes())
    properties=inventory['properties'];by_property={p['property']:p for p in properties}
    foreign=[g for g in inventory['goals'] if g['function']!=expected['function']]
    assert len(foreign)==1
    foreign_property=by_property[foreign[0]['property']]
    assert foreign_property['function']=='std_vector_int_ctor_count_value' and foreign_property['line']==129
    call_properties=[p for p in properties if isinstance(p.get('call_context'),dict) and p['line']==129]
    assert len(call_properties)==1
    call_property=call_properties[0];context=call_property['call_context']
    assert call_property['function']==expected['function'] and call_property['source_file']==str(directory/'wp_input.c')
    assert context=={'caller':expected['function'],'callee':'std_vector_int_ctor_count_value','source_file':str(directory/'wp_input.c'),
                     'line':129,'statement_id':47,'origin':call_property['origin'],'predicate':context['predicate']}
    ordinary=[g for g in inventory['goals'] if not g['smoke']];smokes=[g for g in inventory['goals'] if g['smoke']]
    assert all(g['results']==['valid'] and g['passed'] is True for g in ordinary)
    assert all(g['passed'] is True and g['results']==['timeout','timeout','timeout'] for g in smokes)
    assert len(standard)==21 and all(g['function']==expected['function'] for g in standard)
    allocator={p['function'] for p in inventory['properties'] if p['extern']}
    assert allocator=={'swdb_alloc_int','swdb_free'} and len(census['extern_properties'])==5
    assert len(outcome['assumptions'])==5 and {a['reference']['id'] for a in outcome['assumptions']}==allocator
    assert not list((PROFILE/'workspace/records/proofs').glob('*.yaml'))
    with (directory/'wp-properties.csv').open() as stream:
        reader=csv.reader(stream,delimiter='\t');csv_fields=next(reader,[])
        assert csv_fields==['directory','file','line','function','property kind','status','property']
        csv_rows=[]
        for values in reader:
            if not values:continue
            if len(values)==len(csv_fields):csv_rows.append(dict(zip(csv_fields,values)))
            elif len(values)==1 and values[0][:1].isspace() and csv_rows:csv_rows[-1]['property']+='\n'+values[0]
            else:raise ValueError('incomplete actual property CSV row')
    def pretty(text):return re.sub(r'\s+',' ',text).strip().rstrip(';').strip()
    def without_keyword(text):return re.sub(r'^(?:requires|ensures|exits|terminates|loop invariant)\s+','',pretty(text))
    csv_bindings=[]
    for row in csv_rows:
        function=row['function'] or None;line=int(row['line']);text=pretty(row['property'])
        candidates=[p for p in properties if p['function']==function and p['line']==line];matches=[]
        for prop in candidates:
            description=pretty(prop['description']);reason=None
            if text in {description,without_keyword(description)}:reason='exact native property/predicate text'
            if row['property kind'].startswith('precondition of ') and prop['origin'] in by_property:
                callee=row['property kind'].removeprefix('precondition of ');origin=by_property[prop['origin']]
                if origin['function']==callee and text==without_keyword(origin['description']):reason='exact declared callee-precondition origin text'
            if prop['emitter']=='rte':
                prefix='assert rte: '+row['property kind']+': '
                if description.startswith(prefix) and pretty(description[len(prefix):])==text:reason='exact native RTE predicate text'
            if reason:matches.append({'property':prop['property'],'reason':reason})
        assert matches,('CSV/native source binding missing',function,line,row['property kind'])
        csv_bindings.append({'function':function,'line':line,'kind':row['property kind'],'status':row['status'],'native_bindings':matches})
    assert csv_rows
    command=json.loads((directory/'command.json').read_bytes())['argv']
    assert not any(x.startswith('-wp-prop') or x in {'-wp-gen','-wp-no-why3-detect'} for x in command)
    assert command[command.index('-wp-fct')+1]==expected['function']
    assert sha(command[command.index('-load-module')+1])==sha(PROFILE/'reader/proof_report.cmxs')
    assert sha(PROFILE/'reader/proof_report.ml')==sha(PROJECT/'swdb/proof_report.ml')
    compiler=json.loads((PROFILE/'compiler-runtime.json').read_bytes())
    assert compiler=={'runtime':expected['linux_project_identity_derivation']['runtime'],'identity':expected['linux_project_identity_derivation']['predicted_identity']}
    source_pins=expected['source_blobs']+expected['test_helper_pins']
    for row in source_pins:assert sha(PROJECT/row['relative'])==row['sha256']
    consumers=json.loads((PROFILE/'source-consumers-0.json').read_bytes())
    for row in consumers['files']:
        assert Path(row['path']).stat().st_size==row['bytes'] and sha(row['path'])==row['sha256']
    runtime_pins=[]
    for row in expected['tools'].values():assert sha(row['path'])==row['sha256'];runtime_pins.append(pin(row['path']))
    for row in expected['wp_artifacts']:assert sha(row['path'])==row['sha256'];runtime_pins.append(pin(row['path']))
    for row in expected['runtime_sources']:
        path=Path(expected['linux_prefix'])/'lib/frama-c-wp/core'/row['name'];assert sha(path)==row['sha256'];runtime_pins.append(pin(path))
    assert sha(expected['why3_config']['path'])==expected['why3_config']['sha256']
    imports=[]
    for key,relative in [('why3_stdlib','share/why3/stdlib'),('wp_why3_support','share/frama-c/share/wp/why3'),('why3_drivers','share/why3/drivers')]:
        root=Path(expected['linux_prefix'])/relative
        actual_members=[]
        for path in sorted(root.rglob('*')):
            assert not path.is_symlink() and (path.is_file() or path.is_dir())
            if path.is_file():actual_members.append({'relative':str(path.relative_to(root)),'sha256':sha(path)})
        assert actual_members==expected['portable_import_surfaces'][key]
        imports.append({'root':str(root),'count':len(actual_members)})
    outer={name:json.loads((ROOT/name).read_bytes()) for name in ['resources.json','outer-resources.json','source-after.json']}
    assert outer['resources.json']['exit_code']==1 and outer['outer-resources.json']['exit_code']==1
    assert not outer['resources.json']['out_of_memory'] and not outer['resources.json']['timed_out']
    assert not outer['outer-resources.json']['out_of_memory'] and not outer['outer-resources.json']['timed_out']
    assert outer['source-after.json']=={'commit':SOURCE,'source_unchanged':True,'tracked_changes':''}
    after=snapshot(ROOT);assert before==after and attempts==[]
    decision={'created':'2026-10-16 ET','observer_status':'passive source/census reconciliation; no proof acceptance',
        'source_commit':SOURCE,'raw':str(ROOT),'raw_unchanged':True,'raw_file_count':len(after),'raw_bytes':sum(r['bytes'] for r in after),
        'actual_entry_result':pin(PROFILE/'result.json'),'actual_entry_refusal_preserved':True,
        'ordinary_reader':{'pin':pin(directory/'outcome.json'),'verdict':outcome['verdict'],'failure_class':outcome['failure_class'],'why':outcome['why'],'constructor_whitelisted':False},
        'native_observation':{'ordinary_native_valid':len(ordinary),'smoke_raw_timeouts_healthy':len(smokes),'not_a_caller_proof':True},
        'registered_property_adaptation':{'changes':2,'inverse_original_function_equal':True,'registered_only':True,'original_function_sha256':hashlib.sha256(original.encode()).hexdigest(),'passive_function_sha256':hashlib.sha256(repaired.encode()).hexdigest(),'no_common_reader_edit':True,'no_raw_metadata_owner_rewrite':True},
        'census':census,'csv':{'pin':pin(directory/'wp-properties.csv'),'rows':len(csv_rows),'fields':csv_fields,'native_bindings':csv_bindings},
        'raw_manifest':after,'source_pins_checked':len(source_pins),'consumer_files_checked':len(consumers['files']),'consumer_bytes':sum(x['bytes'] for x in consumers['files']),
        'runtime_pins':runtime_pins,'import_trees':imports,'source_after_and_guards':outer,'external_native_execution_attempts':attempts,'elapsed_seconds':time.monotonic()-started,
        'source_typed_bridge_established':False,'current_constructor_body_record_admitted':False,'proof_acceptance':False,'caller_acceptance':False,'public_proof_record_created':False,
        'boundary':'All21goals/72properties retained.17nativeordinaryValid+4healthyrawTimeoutsmokes are conditional on unproved constructor summaries and existing allocator/library TCB. Original entryrefusal and ordinary not_proven remain. No full dynamic Python loader closure, source/Typed/body/caller/model/public/universal/ticket acceptance.'}
    raw=(json.dumps(decision,indent=2,sort_keys=True)+'\n').encode();assert len(raw)<4*1024**2
    signal.alarm(0);sys.stdout.buffer.write(raw)


if __name__=='__main__':
    main()
