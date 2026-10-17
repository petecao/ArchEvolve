"""2026-10-16 ET. Freeze inert staging/global/source-policy interface proposal."""
import ast
import hashlib
import json
from pathlib import Path
import sys


def deny(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        raise RuntimeError('source staging preparation refuses '+event)


sys.addaudithook(deny)
HERE=Path(__file__).resolve().parent


def pin(path):
    path=Path(path).resolve(strict=True);raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def prepare():
    path=HERE/'whole_interface_v3.py';api={'__file__':str(path),'__name__':'inert_source_inventory'}
    exec(compile(ast.parse(path.read_bytes()),str(path),'exec'),api)
    declarations=api['inventory'](HERE.parents[3])
    headers={row['header_path']:row['header_sha256'] for row in declarations}
    schema={'date':'2026-10-16 ET','status':'INERT integration schema; no actual source/public admission',
      'source_policy_exact_fields':{
        'kind':{'literal':'dx100-whole-interface-source-v1'},
        'entry':{'literal':'semantics.dx100_bfs_0_2'},
        'model_kind':{'literal':'dx100-whole-interface-checked-body-1'},
        'source_headers':{'exact_path_sha256_map':headers},
        'source_implementation_pins':{'required_modules':[pin(HERE/name) for name in ('whole_interface_v3.py','source_dispatch_v2.py','compiler_unit_adapter_v2.py','source_argument_staging_v1.py','source_program_globals_v1.py')]},
        'actual_capture_receipt_sha256':{'format':'actual root-reconciled lowercase SHA-256'},
        'actual_original_source_sha256':{'format':'lowercase SHA-256 of exact original physical source bytes'},
        'actual_full_tu_sha256':{'format':'lowercase SHA-256 of retained raw original full-TU JSON'},
        'actual_abi_observation_sha256':{'format':'lowercase SHA-256 of retained separate literal ABI observation'},
        'source_globals_observation_sha256':{'format':'lowercase SHA-256 of source_program_globals_v1 observation from the actual same TU'},
        'execution_mode':{'literal':'fresh-cxx-program-globals'},
        'program_context_receipt_sha256':{'format':'actual root-admitted fresh-program interpretation'},
        'source_atlas_sha256':{'format':'actual source-declaration-pinned ordinary objects/physical cells; complete MMIO exclusion'},
        'receiver_state_binding_sha256':{'format':'separate checked source host globals, scope bookkeeping and explicit device/ordinary allocation state; no hidden reset'},
        'harness_draw_plan_sha256':{'format':'model identity bound independent full-domain uint32 draw plan; no desired-value assumption'},
        'model_assembly_sha256':{'format':'actual ABI/atlas checked-body assembly and all source/model input pins'}},
      'call_binding_record':{
        'base':'exact source_dispatch_v2.bind_dispatch return object, preserving its fresh whole_interface_v3 binding and dispatch_plan',
        'staging_statements':'one original pure expression evaluation per effective argument; source defaults remain exact pinned literals',
        'staging_grammar':{'literal':'closed pure scalar/local/descriptor v1'},
        'source_RTE_and_local_lifetime_checks_required':True,'receiver_state_binding_required':True,'harness_draw_plan_required':True,'public_admission':False},
      'cpu_access_record':{'base':'source_argument_staging_v1.cpu_load/cpu_store/array_initializer return',
        'complete_access_inventory':'every original pointer use must be projected, deliberately handled by exact ordinary source semantics, or refused; no omitted-access inference from output count',
        'scope':'original same-caller TU node, direct physical source span, unchanged TU and declared type'},
      'initial_source_scope':'the byte-pinned source_call_fixture_v2.cpp under actual original configuration and fresh program globals',
      'source_body_MMIO_TCB_explicit':True,'optional_hardware_refinement_required':False,
      'production_registration_authorized_by_this_packet':False,'actual_public_current_0_2':False}
    (HERE/'source-integration-schema-v1.json').write_text(json.dumps(schema,sort_keys=True,indent=2)+'\n')
    names=['source_argument_staging_v1.py','source_program_globals_v1.py','test_source_argument_staging_v1.py',
      'test_source_program_globals_v1.py','prepare_source_staging_v1.py','README-source-staging-v1.md','source-integration-schema-v1.json',
      'pure-source-argument-staging-v1-first.log','pure-source-argument-staging-v1-second.log','pure-source-argument-staging-v1-green.log',
      'pure-source-program-globals-v1-first.log','compiler-unit-source-packet-v2.json','source-dispatch-preparation-v2.json',
      'whole_interface_v3.py','source_dispatch_v2.py','compiler_unit_adapter_v2.py','source_call_fixture_v2.cpp','new-0.2-contract-design-v1.json']
    result={'date':'2026-10-16 ET','status':'SOURCE ONLY: original argument/CPU/global consumer preparation',
      'files':[pin(HERE/name) for name in names]+[pin(path) for path in sorted(headers)],
      'controls':{'argument_CPU_tests':13,'source_global_tests':3,'synthetic_type_arity_call_routes':132,'source_globals':12,'actual_observations':0},
      'source_MMIO_semantics_TCB_permitted':True,'compiler_or_native_or_verifier_or_network_child':False,
      'production_edited':False,'complete_scoped_original_source_lowering':False,'actual_capture_admission':False,
      'actual_public_0_2_admission':False,'full_ticket28':False,
      'required_next_gates':['Independent source/integration review','Actual original-TU/ABI/globals capture and root raw reconciliation',
          'Complete scoped local/control/assertion/CPU lowering with original source UB obligations and final rechecks',
          'Explicit model receiver bookkeeping and source local allocation binding plus independent harness draws',
          'Root-reviewed production seams and actual paired public fixtures followed by independent cold audit']}
    out=HERE/'source-staging-preparation-v1.json';out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(pin(out),sort_keys=True))


if __name__=='__main__':prepare()
