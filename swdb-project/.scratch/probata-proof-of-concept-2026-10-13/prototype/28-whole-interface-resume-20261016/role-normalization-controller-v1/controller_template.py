"""2026-10-16 ET. INERT passive transform controller; root admission required.

No compiler, child, socket, external compressor, original artifact mutation,
expanded normalized file, JSON DOM, source/call/ABI/public admission or reset.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import time

POLICY_B64='__POLICY_B64__'
NORMALIZER_B64='__NORMALIZER_B64__'
CENSUS_B64='__CENSUS_B64__'
RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v10')
OUT=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-role-gzip-2baf722f-v1')
TOTAL=268435456;FILE=134217728;RESERVE=1048576;FLOOR=53687091200
START=time.monotonic()
OWNED_OUTPUT_ROOT=False
FILES={'control/controller.py','control/normalizer.py','control/census.json','control/policy.json',
    'component/inputs-before.json','component/inputs-after.json','component/caller.normalized.json.gz',
    'component/rename-manifest.jsonl','component/transport.json','component/inverse.json','result.json'}
DIRS={OUT,OUT/'control',OUT/'component'}
class Refused(ValueError):pass
def need(ok,message):
    if not ok:raise Refused(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def document(raw):
    def unique(rows):
        out={}
        for key,value in rows:need(key not in out,'duplicate controller JSON key');out[key]=value
        return out
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(Refused('nonfinite metadata')))
def stable(value):return tuple(getattr(value,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns'))
def pin(path):
    path=Path(path);before=path.lstat()
    need(path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode),'canonical physical input required')
    with path.open('rb') as stream:value=hashlib.file_digest(stream,'sha256').hexdigest()
    need(stable(before)==stable(path.lstat()),'physical input changed while hashing')
    return {'path':str(path),'bytes':before.st_size,'sha256':value}
def check():need(time.monotonic()-START<885,'passive transform work deadline reached')
def audit(event,args):
    if event=='open':
        path,mode,flags=args
        writable=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or flags&(1|2|64|512|1024)
        if writable:
            need(isinstance(path,(str,bytes,os.PathLike)),'named new output required')
            target=Path(os.fsdecode(path))
            need(str(target) in {str(OUT/name) for name in FILES} and flags&os.O_EXCL and flags&os.O_CREAT,
                'only exclusive fixed fresh-output writes allowed')
    if event=='os.mkdir':need(Path(args[0]) in DIRS,'only fixed fresh output directories allowed');return
    if event in {'os.system','os.remove','os.unlink','os.rename','os.replace','os.rmdir','os.chmod','os.chown','os.link','os.symlink','os.truncate',
        'os.utime','os.chdir','os.putenv','os.unsetenv','ctypes.dlopen','resource.setrlimit'} or event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')):
        raise PermissionError('passive transform forbids mutation/child/network: '+event)
def extent():
    total=0
    for root in (OUT,OUT/'control',OUT/'component'):
        need(root.resolve(strict=True)==root and stat.S_ISDIR(root.lstat().st_mode),'physical fixed output directory required')
        for path in root.iterdir():
            metadata=path.lstat()
            if path in DIRS:need(stat.S_ISDIR(metadata.st_mode),'fixed output directory changed');continue
            need(path.relative_to(OUT).as_posix() in FILES and path.resolve(strict=True)==path
                and stat.S_ISREG(metadata.st_mode) and metadata.st_nlink==1 and metadata.st_size<=FILE,'unexpected output topology/file extent')
            total+=metadata.st_size
    need(total<=TOTAL,'aggregate retained cap exceeded');return total
def write_gate(amount,final=False):
    need(type(amount) is int and 0<=amount<=65536,'bounded physical output chunk required')
    need(time.monotonic()-START<(900 if final else 885),'passive finalization deadline reached')
    need(extent()+amount<=TOTAL-(0 if final else RESERVE),'projected aggregate retained quota refused')
    need(shutil.disk_usage(OUT).free>=FLOOR+amount,'50 GiB disk floor refused')
class Sink:
    def __init__(self,name,final=False):
        need(name in FILES,'fixed new output name required');self.path=OUT/name;self.final=final
        need(self.path.parent.resolve(strict=True)==self.path.parent and stat.S_ISDIR(self.path.parent.lstat().st_mode),
            'physical fixed output parent required')
        self.handle=self.path.open('xb',buffering=0)
        actual=self.path.lstat();opened=os.fstat(self.handle.fileno())
        need(self.path.resolve(strict=True)==self.path and (actual.st_dev,actual.st_ino)==(opened.st_dev,opened.st_ino)
            and stat.S_ISREG(actual.st_mode) and actual.st_nlink==1,'exclusive physical output identity differs')
    def write(self,value):
        need(type(value) is bytes,'physical binary output required')
        need(self.handle.tell()+len(value)<=FILE,'physical file cap refused')
        for begin in range(0,len(value),65536):
            part=value[begin:begin+65536];write_gate(len(part),self.final)
            need(self.handle.write(part)==len(part),'short physical output write')
        return len(value)
    def close(self):self.handle.close()
def save(name,value,final=False):
    raw=canonical(value)+b'\n';need(len(raw)<=RESERVE,'bounded compact transform metadata required')
    output=Sink(name,final)
    try:output.write(raw)
    finally:output.close()
def stage(name,raw):
    output=Sink(name)
    try:output.write(raw)
    finally:output.close()
def load(raw,name,expected):
    need((len(raw),sha(raw))==(expected['bytes'],expected['sha256']),'exact primitive bytes required before execution')
    ns={'__name__':'passive_transform_primitive','__file__':name};exec(compile(raw,name,'exec'),ns);return ns
def read_input(path,policy):
    path=Path(path);expected=policy['physical_inputs'][str(path)]
    need(expected['bytes']<=8388608,'bounded selected metadata/code read required')
    raw=path.read_bytes();need((len(raw),sha(raw))==(expected['bytes'],expected['sha256']),'selected metadata/code changed before use');return raw
def input_check(policy):
    rows=[]
    for path,expected in policy['physical_inputs'].items():
        actual=pin(path);need({k:actual[k] for k in ('bytes','sha256')}==expected,'selected original/source/control/runtime input differs: '+path);rows.append(actual)
    return rows
def main():
    global OWNED_OUTPUT_ROOT
    need(__debug__ and sys.flags.isolated and sys.dont_write_bytecode and len(sys.argv)==2 and sys.argv[1]==str(OUT),'exact isolated fresh output argument required')
    need(not os.path.lexists(OUT) and OUT.parent.resolve(strict=True)==OUT.parent and stat.S_ISDIR(OUT.parent.lstat().st_mode),'fresh physical output parent required')
    need(shutil.disk_usage(OUT.parent).free>=FLOOR+TOTAL,'50 GiB floor plus planned retained allowance required')
    policy_raw=base64.b64decode(POLICY_B64,validate=True);policy=document(policy_raw)
    normalizer_raw=base64.b64decode(NORMALIZER_B64,validate=True);census_raw=base64.b64decode(CENSUS_B64,validate=True)
    need((len(normalizer_raw),sha(normalizer_raw))==(policy['normalizer']['bytes'],policy['normalizer']['sha256']) and
         (len(census_raw),sha(census_raw))==(policy['census']['bytes'],policy['census']['sha256']),'exact reviewed source/census payload required')
    need(type(globals().get('SOURCE_BYTES')) is bytes,'exact bootstrap source bytes required')
    sys.addaudithook(audit)
    before=input_check(policy);census=document(census_raw);old_result=document(read_input(RAW/'component/result.json',policy))
    need(old_result['accepted'] is False and old_result['error']=={'type':'Refused','message':'duplicate compiler JSON key'} and old_result['after_input_errors']==[],
        'original V10 refusal must remain exact')
    commands=document(read_input(RAW/'component/commands.json',policy));need(commands==policy['original_commands'] and len(commands)==4
        and all(type(row['returncode']) is int and row['returncode']==0 for row in commands),'exact original four zero-exit compiler phases required')
    need(census['complete_decoder_identity_verified'] is True and census['census']['unknown_or_mismatched_duplicate_events']==0
        and census['census']['duplicate_events']==census['census']['prospective_role_renames']==116,'exact complete known-role census required')
    for directory in (OUT,OUT/'control',OUT/'component'):directory.mkdir()
    OWNED_OUTPUT_ROOT=True
    stage('control/controller.py',SOURCE_BYTES);stage('control/normalizer.py',normalizer_raw);stage('control/census.json',census_raw);stage('control/policy.json',policy_raw)
    save('component/inputs-before.json',before)
    entry_path=RAW/'control/linux_compiler_capture_v10.py'
    entry=load(read_input(entry_path,policy),str(entry_path),policy['physical_inputs'][str(entry_path)])
    original_policy=document(read_input(RAW/'control/linux_compiler_capture_policy_v10.json',policy));zlib,zbefore=entry['bind_zlib'](original_policy)
    base_path=RAW/'control/strict_minify_v2.py';codec_path=RAW/'control/lossless_gzip_v2.py'
    base=load(read_input(base_path,policy),str(base_path),policy['physical_inputs'][str(base_path)])
    codec=load(read_input(codec_path,policy),str(codec_path),policy['physical_inputs'][str(codec_path)])
    normalizer=load(normalizer_raw,str(OUT/'control/normalizer.py'),policy['normalizer'])
    gzip_receipt=document(read_input(RAW/'component/caller.ast.gzip.json',policy))
    compressed=Sink('component/caller.normalized.json.gz');manifest=Sink('component/rename-manifest.jsonl')
    try:
        with (RAW/'component/caller.ast.json.gz').open('rb') as original:
            decoded=codec['DecodeReader'](zlib,original,gzip_receipt,expanded_limit=2147483648,compressed_limit=FILE,check=check)
            transport=normalizer['compress_normalize'](decoded,compressed,manifest,base,codec,zlib,check)
            need(decoded.verified,'complete original gzip/raw identity required')
    finally:compressed.close();manifest.close()
    transformed=transport['normalization'];observed=census['census']
    renamed={'prospective_role_normalization_eligible','prospective_normalization_refused','prospective_normalized_file_cap_fit','normalized_AST_retained_or_admitted','schema'}
    need(all(transformed[key]==value for key,value in observed.items() if key not in renamed),'normalizer original census identities differ')
    need(transformed['plain_normalized_file_cap_fit'] is False and transformed['normalized_bytes']==178924116
        and transformed['role_normalization_and_expanded_cap_eligible'] is True,'separate measured expanded/plain extent gates differ')
    with (OUT/'component/caller.normalized.json.gz').open('rb') as source:
        manifest_bytes=(OUT/'component/rename-manifest.jsonl').read_bytes()
        inverse=normalizer['verify_inverse_gzip'](zlib,source,manifest_bytes,transport,codec,check)
    need(entry['bind_zlib'](original_policy)[1]==zbefore,'selected zlib/runtime changed')
    after=input_check(policy);need(after==before,'selected original/source/runtime inputs changed')
    need(pin(OUT/'control/normalizer.py')['sha256']==policy['normalizer']['sha256'] and pin(OUT/'control/census.json')['sha256']==policy['census']['sha256']
        and pin(OUT/'control/controller.py')['sha256']==sha(SOURCE_BYTES) and pin(OUT/'control/policy.json')['sha256']==sha(policy_raw),'staged controls changed')
    save('component/transport.json',transport);save('component/inverse.json',inverse);save('component/inputs-after.json',after)
    outputs=[pin(OUT/name) for name in sorted(FILES) if name!='result.json']
    save('result.json',{'schema':'passive-paired-type-gzip-transform-result-1','normalization_complete':True,'original_capture_accepted':False,
        'original_capture_refusal':old_result['error'],'source_call_ABI_public_or_full28_admission':False,'compiler_or_native_or_solver_executed':False,
        'output_root':str(OUT),'outputs':outputs,'input_pins':before,'zlib_binding':zbefore,'selected_inputs_unchanged':True,
        'wall_seconds':time.monotonic()-START,'expanded_normalized_limit_bytes':201326592,'physical_file_limit_bytes':FILE,'aggregate_retained_limit_bytes':TOTAL},final=True)
    print(json.dumps({'normalization_complete':True,'result':pin(OUT/'result.json'),'source_call_ABI_or_public_admission':False},sort_keys=True))
if __name__=='__main__':
    try:main()
    except Exception as error:
        # Partial outputs never receive a completed transport certificate.
        if OWNED_OUTPUT_ROOT and OUT.is_dir() and not os.path.lexists(OUT/'result.json'):
            try:save('result.json',{'normalization_complete':False,'error':{'type':type(error).__name__,'message':str(error)[:1024]},
                'original_capture_accepted':False,'source_call_ABI_public_or_full28_admission':False,'wall_seconds':time.monotonic()-START},final=True)
            except Exception:pass
        raise
