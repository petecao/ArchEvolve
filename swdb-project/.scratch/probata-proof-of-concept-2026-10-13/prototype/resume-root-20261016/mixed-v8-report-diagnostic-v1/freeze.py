"""2026-10-16 ET. Freeze inert all-eight diagnostic; never run its main."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
POC=HERE.parents[2]
OLD=HERE.with_name('mixed-v8-cold-v1')


def pin(path):
    b=path.read_bytes();return {'path':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}


def write(path,value):
    with path.open('xb') as stream:stream.write((json.dumps(value,indent=2,sort_keys=True)+'\n').encode())


def definitions(path,names):
    source=path.read_text();lines=source.splitlines(True)
    found={n.name:''.join(lines[n.lineno-1:n.end_lineno]) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name in names}
    assert set(found)==set(names);return found


def main():
    prior_entry=OLD/'entry.py';assert pin(prior_entry)['sha256']=='7154ecc6fdc030157be5cfed925f855b3b20f72091c95202281a27ab2d024e87'
    names=('need','sha','compact','digest','identity','physical','read_bytes','pin','read','audit')
    helpers=definitions(prior_entry,names)
    body=definitions(OLD/'observer.py',('record_order','raw_membership'))
    old_context=json.loads((OLD/'context.json').read_bytes())
    context={k:old_context[k] for k in ('raw_regular_pins','raw_membership','aliases','model_names')}
    refusal=POC/'evidence/t25-mixed-v8-cold-root-actual-v1-stdout-20261016.json'
    execution=POC/'evidence/t25-mixed-v8-cold-root-execution-v1-20261016.json'
    assert pin(execution)['sha256']=='2c4f18d4cd0292bc514046114a5cfa3d6b73ee160233df734f0a67a7c468a0ce'
    context['original_refusal']={'pin':pin(refusal),'record':json.loads(refusal.read_bytes()),'execution':pin(execution)}
    context_text=json.dumps(context,indent=2,sort_keys=True)+'\n';(HERE/'context.json').write_text(context_text)
    source=(HERE/'diagnostic.py').read_text().replace('# __REVIEWED_HELPERS__','\n\n'.join(helpers.values())).replace('# __REVIEWED_RAW_MEMBERSHIP_AND_RECORD_ORDER__','CONTEXT=json.loads('+repr(context_text)+')\n\n'+'\n\n'.join(body.values()))
    compile(ast.parse(source),'<inert-report-diagnostic>','exec')
    with (HERE/'entry.py').open('xb') as stream:stream.write(source.encode())
    assert definitions(HERE/'entry.py',names)==helpers
    command={'date':'2026-10-16 ET','status':'INERT_ROOT_SOURCE_REVIEW_AND_ADMISSION_REQUIRED','host':'mbit10',
             'stdin':pin(HERE/'entry.py'),'argv_after_root_scoped_preflight':['/usr/bin/python3','-I','-B','-'],
             'closed_environment':{'HOME':'/nonexistent','PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'},
             'outer_timeout_seconds':90,'inner_alarm_seconds':60,'address_space_bytes':512*1024**2,
             'stdout_cap_bytes':512*1024,'expected_completed_exit':2,'remote_writes':False,
             'project_or_PyYAML_or_native_or_compiler_or_solver_imports_and_calls':False,
             'scope':'Read all6WP+2CBMC existing report schemas and evaluate all remaining V1 predicates independently; no report repair, normalization, proof or semantic adoption.'}
    write(HERE/'command.json',command)
    packet={'date':'2026-10-16 ET','schema':'mixed-v8-all-report-predicate-diagnostic-1','state':'FROZEN_INERT',
            'inputs':[pin(OLD/'source-packet.json'),pin(prior_entry),pin(OLD/'observer.py'),pin(OLD/'context.json'),pin(refusal),pin(execution)],
            'outputs':[pin(HERE/name) for name in ('diagnostic.py','context.json','entry.py','command.json','pure_controls.py','pure-controls.log','freeze.py','README.md')],
            'read_helpers_byte_exact':{name:hashlib.sha256(text.encode()).hexdigest() for name,text in helpers.items()},
            'raw_membership_and_record_order_byte_exact_V1':True,'raw_regular_files':len(context['raw_regular_pins']),
            'contexts':{'WP':6,'CBMC':2},'controls':{'passed':8,'child_native_network_attempts':[]},
            'original_refusal_preserved':context['original_refusal'],'scientific_cold_acceptance':False,
            'source_body_Typed_caller_default_or_public_record_acceptance':False,'root_exact_review_and_admission_before_query':True}
    write(HERE/'source-packet.json',packet)
    print(json.dumps({'packet':pin(HERE/'source-packet.json'),'entry':pin(HERE/'entry.py'),'command':pin(HERE/'command.json')},indent=2))


if __name__=='__main__':main()
