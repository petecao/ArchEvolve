"""2026-10-16 ET. Inert exact-header closure successor, never actual projection."""
import ast
import hashlib
import json
from pathlib import Path
import sys
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('inert projection preparation refuses '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'runtime-projection-v1';PROJECT=WHOLE.parents[3]
def pin(path):
    data=path.read_bytes();return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def save(name,value):(HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
source=(OLD/'runtime_projection_v1.py').read_text();edits=[]
for before,after in [
    ("SOURCE_SHA='3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'", "SOURCE_SHA='3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'\nHEADER_PINS={'MAA.hpp':'4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd',\n 'MAA_gem5.hpp':'5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174'}"),
    ("headers={name:file_pin(Path(project)/'apps/dx100/benchmarks/API'/name)[0].decode('ascii') for name in ('MAA.hpp','MAA_gem5.hpp')}",
     "headers={name:file_pin(Path(project)/'apps/dx100/benchmarks/API'/name,expected)[0].decode('ascii') for name,expected in HEADER_PINS.items()}"),
    ("    need(declarations==api['inventory'](project),'actual two-header declaration binding changed')", "    need(declarations==api['inventory'](project),'actual two-header declaration binding changed')\n    need(api['HEADER_PINS']==HEADER_PINS,'exact source header pin matrix differs')\n    header_pins=[file_pin(project/'apps/dx100/benchmarks/API'/name,expected)[1] for name,expected in HEADER_PINS.items()]"),
    ("identity={'schema':'whole-interface-source-cxx-runtime-1','components':pins,", "identity={'schema':'whole-interface-source-cxx-runtime-1','components':pins,'source_headers':header_pins,"),
    ("    for pin in pins:file_pin(pin['path'],pin['sha256'])", "    for pin in [*pins,*header_pins]:file_pin(pin['path'],pin['sha256'])")]:
    assert source.count(before)==1;edits.append({'old':before,'new':after});source=source.replace(before,after,1)
(HERE/'runtime_projection_v2.py').write_text(source)
restored=source
for edit in reversed(edits):assert restored.count(edit['new'])==1;restored=restored.replace(edit['new'],edit['old'],1)
assert restored==(OLD/'runtime_projection_v1.py').read_text()
save('runtime-projection-v2-inverse.json',{'date':'2026-10-16 ET','predecessor':pin(OLD/'runtime_projection_v1.py'),'successor':pin(HERE/'runtime_projection_v2.py'),
    'edits':edits,'exact_text_and_AST_inverse':ast.dump(ast.parse(restored))==ast.dump(ast.parse((OLD/'runtime_projection_v1.py').read_bytes())),
    'behavioral_edit':'pin enum reread and retain/finally recheck two exact source headers only','actual_execution':False})
ns={'__name__':'synthetic_projection_strings','__file__':str(HERE/'test_runtime_projection_v2.py')}
exec(compile((HERE/'test_runtime_projection_v2.py').read_bytes(),'synthetic_projection_strings','exec'),ns)
(HERE/'synthetic-runtime-header-v2.hpp').write_text(ns['HEADER'])
(HERE/'synthetic-projected-original-v2.cpp').write_text(ns['R']['check_edits'](ns['SOURCE'],ns['edits']()))
save('synthetic-declarator-edits-v2.json',{'scope':'synthetic textual inverse only; declaration IDs are fixtures, no actual TU admission','edits':ns['edits'](),
    'runtime_route_instances':ns['INSTANCES'],'source_declarations':ns['INVENTORY'],'actual_TU_or_projection_executed':False})
report=None;log=HERE/'pure-runtime-projection-controls.log'
if log.exists():
    report=json.loads(log.read_text().splitlines()[-1]);assert report['tests']==13 and report['failures']==report['errors']==report['skips']==0 and report['child_events']==[]
    assert report['projection_sha256']==pin(HERE/'runtime_projection_v2.py')['sha256'] and report['header_sha256']==pin(HERE/'synthetic-runtime-header-v2.hpp')['sha256']
files=[pin(HERE/name) for name in ('runtime_projection_v2.py','test_runtime_projection_v2.py','prepare_runtime_projection_v2.py','README.md','runtime-projection-v2-inverse.json',
    'synthetic-runtime-header-v2.hpp','synthetic-projected-original-v2.cpp','synthetic-declarator-edits-v2.json')]
if log.exists():files.append(pin(log))
inputs=[pin(WHOLE/name) for name in ns['R']['PINS']]+[pin(WHOLE/'source_call_fixture_v2.cpp')]
inputs+=[pin(PROJECT/'apps/dx100/benchmarks/API'/name) for name in ns['R']['HEADER_PINS']]
assert not EVENTS
save('runtime-projection-source-packet-v2.json',{'date':'2026-10-16 ET','status':'SOURCE ONLY; header closure successor of original expression/control/assertion projection proposal',
    'files':files,'inputs':inputs,'validation':report,'predecessor_packet':pin(OLD/'runtime-projection-source-packet-v1.json'),
    'source_names':26,'source_declarations':27,'typed_arity_routes':132,'declarator_edits':9,
    'complete_actual_TU_projection_exercised':False,'actual_projected_compiler_or_native':False,'generated_lowered_C_used_as_counterpart':False,
    'root_owned_receiver_context_and_physical_mapping_required':True,'shared_concrete_memory_MMIO_value_model_is_explicit_TCB':True,
    'generic_raw_MMIO_Cxx_execution_admitted':False,'public_proof':False,'current_0_2':False,'full_ticket28':False})
print(json.dumps(pin(HERE/'runtime-projection-source-packet-v2.json'),sort_keys=True))
