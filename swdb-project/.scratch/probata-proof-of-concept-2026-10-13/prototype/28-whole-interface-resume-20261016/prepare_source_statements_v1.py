"""2026-10-16 ET. Freeze statement/source integration successor, no children."""
import ast
import hashlib
import json
from pathlib import Path
import sys


def deny(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        raise RuntimeError('statement preparation refuses '+event)


sys.addaudithook(deny)
HERE=Path(__file__).resolve().parent


def pin(path):
    path=Path(path).resolve(strict=True);raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def own(name):
    path=HERE/name;ns={'__file__':str(path),'__name__':'inert_statement_preparation'}
    exec(compile(ast.parse(path.read_bytes()),str(path),'exec'),ns)
    return ns


def prepare():
    controls=own('test_source_statements_v1.py');case=controls['Controls']('test_07_complete_scoped_source_preserves_calls_writes_assertion_and_cleanup')
    directory=HERE/'statement-synthetic-fixture-v1';directory.mkdir(exist_ok=True)
    case.source=directory/'caller.cpp';case.declarations=controls['API']['inventory'](HERE.parents[3])
    lower,_=case.make();result=lower.lower()
    (HERE/'source-statements-synthetic-v1.c').write_text('/* INERT synthetic metadata emitted body; no actual compiler/proof admission. */\n'+result['text'])
    receipt={'date':'2026-10-16 ET','status':'SYNTHETIC COMPILER METADATA ONLY; no actual observation',
        'source_cpp':pin(case.source),'selected_assert_header_synthetic':pin(directory/'selected-assert.h'),
        'generated_C':pin(HERE/'source-statements-synthetic-v1.c'),
        'original_full_tu_sha256':result['original_full_tu_sha256'],'calls':len(result['call_bindings']),
        'CPU_projection_records':len(result['CPU_projections']),'assertions':len(result['assertions']),
        'public_admission':False,'actual_compiler_run':False}
    (HERE/'source-statements-synthetic-v1.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    schema=json.loads((HERE/'source-integration-schema-v1.json').read_bytes())
    schema['source_policy_exact_fields']['source_implementation_pins']['required_modules']=[pin(HERE/name) for name in (
        'whole_interface_v4.py','source_dispatch_v3.py','compiler_unit_adapter_v2.py','source_argument_staging_v2.py','source_program_globals_v1.py','source_statements_v1.py')]
    schema['source_policy_exact_fields']['assertion_header_pin']={'format':'exact admitted canonical physical assert header path/bytes/SHA-256 from actual compiler dependency closure'}
    schema['source_policy_exact_fields']['statement_preparation_sha256']={'format':'actual original-unit-linked emitted C / all call / CPU / assertion / lifetime record receipt'}
    schema['source_statement_scope']='source_statements_v1 no-parameter scalar-return slice; unsupported source forms refuse'
    schema['source_kind_predecessor_unchanged']=True
    schema['source_policy_exact_fields']['execution_mode']['entry_obligation']='Static initialization facts also require the admitted entry context to exclude intervening mutations before source entry; reused state needs an explicit successor'
    schema['call_binding_record']['base']='exact source_dispatch_v3.bind_dispatch return object; same record schema and renderer semantics as V2, using whole_interface_v4 direct-site lookup'
    schema['cpu_access_record']['base']='source_argument_staging_v2 projections plus source_statements_v1 complete supported body consumer'
    schema['cpu_access_record']['lifetime']='single initialized descriptor copies and exact active ordinary origin scopes at every pointer use; pointer assignment/return/unknown calls refuse; pending checks at scope exit are additional'
    (HERE/'source-integration-schema-v2.json').write_text(json.dumps(schema,sort_keys=True,indent=2)+'\n')
    names=['source_statements_v1.py','test_source_statements_v1.py','prepare_source_statements_v1.py','README-source-statements-v1.md',
        'source-statements-synthetic-v1.c','source-statements-synthetic-v1.json','source-integration-schema-v2.json',
        'source_argument_staging_v2.py','source_program_globals_v1.py','whole_interface_v4.py','source_dispatch_v3.py','compiler_unit_adapter_v2.py',
        'pure-source-statements-v1-first.log','pure-source-statements-v1-second.log','pure-source-statements-v1-green.log',
        'pure-source-statements-v1-final.log','pure-source-statements-v1-final-v2.log','unrelated-macro-call-source-packet-v1.json',
        'source-staging-preparation-v1.json','compiler-unit-source-packet-v2.json','source_call_fixture_v2.cpp']
    packet={'date':'2026-10-16 ET','status':'SOURCE ONLY: scoped statement + source kind integration proposal',
        'files':[pin(HERE/name) for name in names]+[pin(case.source),pin(directory/'selected-assert.h')],
        'counts':{'statement_controls':14,'narrow_macro_controls':9,'argument_CPU_controls':13,'source_global_controls':3,
            'source_name_contracts':26,'source_declarations':27,'typed_arity_instances':132,'actual_compiler_observations':0},
        'source_kind':'dx100-whole-interface-source-v1','model_kind':'dx100-whole-interface-checked-body-1',
        'owned_MMIO_source_semantics_TCB_accepted':True,'optional_hardware_body_theorem_required':False,
        'production_edited':False,'actual_receiver_draw_source_context_admitted':False,'actual_public_0_2':False,'full_ticket28':False}
    out=HERE/'source-statements-preparation-v1.json';out.write_text(json.dumps(packet,sort_keys=True,indent=2)+'\n')
    print(json.dumps(pin(out),sort_keys=True))


if __name__=='__main__':prepare()
