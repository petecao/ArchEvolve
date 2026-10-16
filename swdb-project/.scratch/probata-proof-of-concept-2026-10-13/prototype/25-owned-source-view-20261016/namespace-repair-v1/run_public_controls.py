"""2026-10-16 ET. No-child source/Heap packet public RED/GREEN runner."""
import hashlib,json,runpy,signal,sys,traceback
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]

def main():
    stage=sys.argv[1]
    if stage not in {'namespace-repair-v1'}:raise ValueError('explicit fresh stage required')
    root=Path('/private/tmp/probata-resume-20261016-t25-owned-source-'+stage);root.mkdir(exist_ok=False);(root/'swdb').mkdir()
    names=['std_models.py','c_lowering.py','vector_owned_transfer.py','vector_owned_state.mlw','heap_reallocation.mlw']
    if not stage.startswith('red'):names+=['vector_owned_source_view.py','vector_owned_effects.mlw']
    pins=[]
    for name in names:
        raw=(PROJECT/'swdb'/name).read_bytes();(root/'swdb'/name).write_bytes(raw);pins.append({'path':name,'sha256':hashlib.sha256(raw).hexdigest()})
    test=root/'test_source_view.py';test.write_bytes((PROJECT/'tests/test_vector_owned_source_view.py').read_bytes())
    attempts=[]
    def audit(event,args):
        if event in {'subprocess.Popen','os.system','os.posix_spawn','os.exec','os.fork','ctypes.dlopen','socket.connect'}:
            attempts.append(event);raise RuntimeError('pure source-view controls rejected '+event)
    sys.addaudithook(audit);sys.path.insert(0,str(root));sys.dont_write_bytecode=True;signal.alarm(30)
    tests=runpy.run_path(str(test));outcomes=[]
    for name,function in tests.items():
        if not name.startswith('test_'):continue
        directory=root/name;directory.mkdir()
        try:function(directory);outcomes.append({'name':name,'passed':True})
        except(Exception,pytest.fail.Exception)as error:outcomes.append({'name':name,'passed':False,'error':type(error).__name__+': '+str(error),'traceback':traceback.format_exc()})
    size=sum(p.lstat().st_size for p in root.rglob('*') if p.is_file()and not p.is_symlink())
    if size>8*1024**2:raise ValueError('source-view pure raw bound exceeded')
    result={'date':'2026-10-16 ET','stage':stage,'source_pins':pins,'outcomes':outcomes,'passed':sum(r['passed']for r in outcomes),'failed':sum(not r['passed']for r in outcomes),'external_native_attempts':attempts,'raw_bytes':size,'actual_formal_run':False}
    path=root/'result.json';path.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');signal.alarm(0);print(json.dumps({'result':str(path),'passed':result['passed'],'failed':result['failed'],'attempts':attempts}));return int(result['failed']!=0 or bool(attempts))
if __name__=='__main__':raise SystemExit(main())
