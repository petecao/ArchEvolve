"""2026-10-16 ET. Freeze inert original compiler fixture/adapter proposal."""
import ast
import hashlib
import json
from pathlib import Path
import sys


def deny(event,args):
    if event.startswith(("subprocess.","os.exec","os.spawn","os.posix_spawn","os.fork","socket.")) or event in {"os.system","ctypes.dlopen"}:
        raise RuntimeError("compiler fixture preparation refuses "+event)


sys.addaudithook(deny)
HERE=Path(__file__).resolve().parent


def pin(path):
    path=Path(path).resolve(strict=True);raw=path.read_bytes()
    return {"path":str(path),"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}


def prepare():
    module=HERE/'compiler_unit_adapter_v2.py'
    namespace={'__file__':str(module),'__name__':'inert_compiler_preparation'}
    exec(compile(ast.parse(module.read_bytes()),str(module),'exec'),namespace)
    recipe=namespace['capture_recipe'](
        compiler='/data/yanruj/EvolveSWDB_runs/probata-source-gate-native-20261015-1102-node0/compiler-bin/clang++',
        project='/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project',
        raw='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v2')
    recipe.update(status='INERT PROPOSAL ONLY: actual compiler controller/runtime/guard/source admission missing',
        prospective_source_commit='2baf722fdaa6cba24b859eae3172a6f597417d72',
        compiler_role='Exact native-selected LLVM22 wrapper/driver; no compiler/linker/native/version call made',
        staged_original_inputs=[pin(HERE/'source_call_fixture_v2.cpp'),pin(HERE/'compiler_abi_probe_v1.cpp'),
            pin(HERE/'compiler_include_v1/gem5/m5ops.h')],
        root_must_bind_exact_pinned_caller_configuration=True, separate_abi_probe_proves_arbitrary_caller_configuration=False,
        public_admission=False)
    (HERE/'compiler-capture-plan-v2.json').write_text(json.dumps(recipe,sort_keys=True,indent=2)+'\n')
    project=HERE.parents[3]
    paths=[module,HERE/'test_compiler_unit_adapter_v2.py',HERE/'prepare_compiler_unit_adapter_v2.py',
        HERE/'compiler_abi_probe_v1.cpp',HERE/'source_call_fixture_v2.cpp',HERE/'source-call-fixture-v2-inverse-delta.json',
        HERE/'compiler_include_v1/gem5/m5ops.h',HERE/'compiler-capture-plan-v2.json',
        HERE/'pure-compiler-unit-adapter-v2-red.log',HERE/'pure-compiler-unit-adapter-v2-green.log',HERE/'compiler-unit-v2-inverse-delta.json',HERE/'compiler-unit-source-packet-v1.json',
        HERE/'README-compiler-unit-adapter-v2.md',HERE/'new-0.2-contract-design-v1.json',HERE/'prepare_new_0_2_contract_design_v1.py',
        HERE/'source-dispatch-preparation-v2.json',HERE/'source_dispatch_v2.py',HERE/'whole_interface_v3.py',
        project/'apps/dx100/benchmarks/API/MAA.hpp',project/'apps/dx100/benchmarks/API/MAA_gem5.hpp',
        project/'tests/testkit/dx100_initialized_register.py']
    result={'date':'2026-10-16 ET','status':'SOURCE ONLY: compiler unit/ABI/contract/public-route preparation',
        'files':[pin(path) for path in paths],
        'counts':{'pure_tests':13,'synthetic_ABI_roots':29,'contract_entries':26,'source_declarations':27,'typed_arity_instances':132},
        'source_MMIO_TCB_explicitly_permitted':True,'optional_hardware_body_theorem_required':False,
        'actual_original_TU_ABI_observed':False,'actual_compiler_native_verifier_network_child':False,
        'production_files_edited':False,'actual_controller_admitted':False,'public_admission':False,'current_0_2':False,'full_ticket28':False,
        'unresolved_required_production_gates':['Root-selected actual compiler/source/runtime/resource/recipe admission and retained same-TU evidence within caps',
            'Original caller macro/pragma configuration versus fixed source/MMIO profile; separate probe is not that evidence',
            'Scoped expression/descriptor/local initialization and complete CPU-access lowering',
            'New isolated model/entry and actual positive/negative public source verdicts with independent reconciliation']}
    output=HERE/'compiler-unit-source-packet-v2.json';output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(pin(output),sort_keys=True))


if __name__=='__main__':prepare()
