"""2026-10-16 ET. Pin inert proposal and synthetic text/header artifacts only."""
import hashlib
import json
from pathlib import Path
import sys
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('inert projection preparation refuses '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;PROJECT=WHOLE.parents[3]
ns={'__name__':'synthetic_projection_strings','__file__':str(HERE/'test_runtime_projection_v1.py')}
exec(compile((HERE/'test_runtime_projection_v1.py').read_bytes(),'synthetic_projection_strings','exec'),ns)
def pin(path):
    data=path.read_bytes();return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def save(name,value):(HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
(HERE/'synthetic-runtime-header-v1.hpp').write_text(ns['HEADER'])
source=ns['R']['check_edits'](ns['SOURCE'],ns['edits']())
(HERE/'synthetic-projected-original-v1.cpp').write_text(source)
save('synthetic-declarator-edits-v1.json',{'scope':'synthetic textual inverse only; declaration IDs are fixtures, no actual TU admission','edits':ns['edits'](),
    'runtime_route_instances':ns['INSTANCES'],'source_declarations':ns['INVENTORY'],'actual_TU_or_projection_executed':False})
log=HERE/'pure-runtime-projection-controls.log';report=json.loads(log.read_text().splitlines()[-1])
assert report['tests']==11 and report['failures']==report['errors']==report['skips']==0 and report['child_events']==[]
assert report['projection_sha256']==pin(HERE/'runtime_projection_v1.py')['sha256']
assert report['header_sha256']==pin(HERE/'synthetic-runtime-header-v1.hpp')['sha256']
files=[pin(HERE/name) for name in ('runtime_projection_v1.py','test_runtime_projection_v1.py','prepare_runtime_projection_v1.py','README.md',
    'synthetic-runtime-header-v1.hpp','synthetic-projected-original-v1.cpp','synthetic-declarator-edits-v1.json','pure-runtime-projection-controls.log')]
inputs=[pin(WHOLE/name) for name in ns['R']['PINS']]
inputs+=[pin(WHOLE/'source_call_fixture_v2.cpp')]+[pin(PROJECT/'apps/dx100/benchmarks/API'/name) for name in ('MAA.hpp','MAA_gem5.hpp')]
assert not EVENTS
save('runtime-projection-source-packet-v1.json',{'date':'2026-10-16 ET','status':'SOURCE ONLY; original expression/control/assertion projection proposal',
    'files':files,'inputs':inputs,'validation':report,'source_names':26,'source_declarations':27,'typed_arity_routes':132,'declarator_edits':9,
    'complete_actual_TU_projection_exercised':False,'actual_projected_compiler_or_native':False,'generated_lowered_C_used_as_counterpart':False,
    'root_owned_receiver_context_and_physical_mapping_required':True,'shared_concrete_memory_MMIO_value_model_is_explicit_TCB':True,
    'generic_raw_MMIO_Cxx_execution_admitted':False,'public_proof':False,'current_0_2':False,'full_ticket28':False})
print(json.dumps(pin(HERE/'runtime-projection-source-packet-v1.json'),sort_keys=True))
