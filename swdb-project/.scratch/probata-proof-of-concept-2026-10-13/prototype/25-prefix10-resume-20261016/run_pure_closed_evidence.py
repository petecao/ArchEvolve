"""2026-10-16 ET. Retained parser, child-free closed source effect public RED/GREEN."""
import ast
import copy
import hashlib
import json
import runpy
import signal
import sys
import traceback
import types
from pathlib import Path

import pytest

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
RETAINED=Path('/private/tmp/probata-t25-caller104-compiler-controls-v1-20261016/pytest/test_public_alias_controls_kee1')


def main():
    stage=sys.argv[1];assert stage in {'red','green-v1','green-v2','green-v3','green-v4','green-v5','green-v6','green-v7','green-v8'}
    output=Path('/private/tmp/probata-resume-20261016-t25-closed-source-evidence-'+stage)
    output.mkdir(exist_ok=False);(output/'swdb').mkdir();(output/'testkit').mkdir()
    signal.alarm(60)
    harness=ast.parse((HERE/'run_pure_closed_view.py').read_bytes())
    node=next(n for n in harness.body if isinstance(n,ast.Assign) and n.targets[0].id=='MODULES')
    names=ast.literal_eval(node.value)+['vector_reallocation_closed_view.py','vector_reallocation_closed_lifetime.py','vector_reallocation_closed_lifetime_parts.py']
    if stage!='red':names+=['vector_reallocation_closed_evidence.py']
    pins=[]
    for name in names:
        raw=(PROJECT/'swdb'/name).read_bytes()
        if name.endswith('.py'):
            imports={a.name for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.Import) for a in n.names}
            imports|={n.module for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.ImportFrom)}
            assert imports<={'hashlib','json','re','pathlib','ast','dataclasses','swdb','swdb.heap_model_vcs','swdb.vector_reallocation_inventory','swdb.vector_reallocation_composition','swdb.vector_reallocation_caller_packets'}
        (output/'swdb'/name).write_bytes(raw);pins.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest()})
    stub=types.ModuleType('swdb.c_lowering')
    for n in ast.parse((PROJECT/'swdb/c_lowering.py').read_bytes()).body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in {'INTEGER_TYPES','FLOAT_TYPES','INTERNAL_TYPES'}:
            setattr(stub,n.targets[0].id,ast.literal_eval(n.value))
    sys.modules['swdb.c_lowering']=stub
    for helper in ['__init__.py','vector_reallocation.py']:
        (output/'testkit'/helper).write_bytes((PROJECT/'tests/testkit'/helper).read_bytes())
    anchor_path=RETAINED/'vector_realloc_v3_no_growth.anchors.json'
    anchors=json.loads(anchor_path.read_bytes());raw=(RETAINED/'vector_realloc_v3_no_growth.c').read_bytes()
    candidate=anchors['vector_reallocation_candidate'];source=PROJECT/'tests/fixtures/proof/vector_reallocation_v3.cc'
    assert hashlib.sha256(raw).hexdigest()==candidate['lowered_sha256']==anchors['c_lowering_sha256']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==candidate['source_sha256']
    lowering=types.SimpleNamespace(text=raw.decode(),sha256=candidate['lowered_sha256'],vector_reallocation_candidate=copy.deepcopy(candidate),function=anchors['function'],models=anchors['models'],source_sha256=candidate['source_sha256'],stdlib_provenance=copy.deepcopy(anchors['stdlib_provenance']),stdlib_substitutions=copy.deepcopy(anchors['stdlib_substitutions']),std_models=tuple(anchors['std_models']['types']),defines=(),summaries=(),probes=())
    test=output/'test_closed_source_evidence.py';test.write_bytes((PROJECT/'tests/test_vector_reallocation_closed_evidence.py').read_bytes())
    attempts=[]
    def audit(name,args):
        if name in {'subprocess.Popen','os.system','os.posix_spawn','os.exec','os.fork','ctypes.dlopen'}:
            attempts.append(name);raise RuntimeError('closed lifetime controls forbid native/process execution')
    sys.addaudithook(audit);sys.dont_write_bytecode=True;sys.path.insert(0,str(output))
    tests=runpy.run_path(str(test));outcomes=[]
    for name,function in tests.items():
        if not name.startswith('test_'):continue
        directory=output/name;directory.mkdir()
        try:
            function((source,copy.deepcopy(lowering)),directory)
            outcomes.append({'name':name,'passed':True})
        except (Exception,pytest.fail.Exception) as error:
            outcomes.append({'name':name,'passed':False,'error':type(error).__name__+': '+str(error),'traceback':traceback.format_exc()})
    raw_bytes=sum(p.stat().st_size for p in output.rglob('*') if p.is_file());assert raw_bytes<4*1024**2
    result={'created':'2026-10-16 ET','stage':stage,'source_pins':pins,'outcomes':outcomes,'passed':sum(r['passed'] for r in outcomes),'failed':sum(not r['passed'] for r in outcomes),'external_native_attempts':attempts,'raw_bytes':raw_bytes,'whole_alarm_seconds':60,'source_typed_bridge_established':False,'caller_acceptance':False}
    (output/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');signal.alarm(0)
    print(json.dumps({'result':str(output/'result.json'),'passed':result['passed'],'failed':result['failed'],'external_native_attempts':attempts}))
    return int(result['failed']!=0 or bool(attempts))


if __name__=='__main__':
    raise SystemExit(main())
