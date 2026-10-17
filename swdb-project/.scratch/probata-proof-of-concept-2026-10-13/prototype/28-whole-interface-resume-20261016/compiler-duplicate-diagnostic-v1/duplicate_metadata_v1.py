"""2026-10-16 ET. INERT first-duplicate metadata diagnostic, never JSON admission.

No raw AST output, repair, filter, compiler, child or project import. Main requires
separate root admission. Reads original V10 gzip and leaves every byte unchanged.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('duplicate metadata forbids '+event)
sys.addaudithook(no_child)
POLICY_SHA='8d86faea6d8235c9431acddae4d28e08831afaaca1ebc506e9363d66e8e32517'
ENTRY_SHA='095eee7198167f5e89ae3a64deb2c42e8097951d957a91de0a7c8fd6efb60810'
CODEC_SHA='aae4a423216fcdca6b16f9eba370ec4c83615ed61ae79dd4b3d09e3bed1702ef'
MINIFIER_SHA='b866e14fe3ca210de178aab71f5c8a662e15f818a5ca485095487b005ae51897'
RAW_NAME='probata-resume-20261016-t28-full-tu-2baf722f-v10'
class Refused(ValueError):pass
class DuplicateFound(Exception):
    def __init__(self,metadata):self.metadata=metadata

def need(ok,message):
    if not ok:raise Refused(message)
def position(reader):return reader.count-(len(reader.buffer)-reader.at)
def pin(path):
    path=Path(path);before=path.lstat();fields=('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns')
    need(path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode),'canonical physical diagnostic input required')
    with path.open('rb') as stream:value=hashlib.file_digest(stream,'sha256').hexdigest()
    need(tuple(getattr(before,k) for k in fields)==tuple(getattr(path.lstat(),k) for k in fields),'diagnostic input changed')
    return {'path':str(path),'bytes':before.st_size,'sha256':value}
def document(path,limit=8388608):
    need(Path(path).lstat().st_size<=limit,'bounded diagnostic metadata required')
    def pairs(rows):
        result={}
        for key,value in rows:need(key not in result,'metadata duplicate key');result[key]=value
        return result
    def bad(_):raise Refused('nonfinite metadata')
    return json.loads(Path(path).read_bytes(),object_pairs_hook=pairs,parse_constant=bad)
def load(path,expected):
    before=pin(path);need(before['sha256']==expected,'exact diagnostic primitive required')
    raw=Path(path).read_bytes();need(hashlib.sha256(raw).hexdigest()==expected and pin(path)==before,'primitive changed before compile')
    ns={'__name__':'passive_duplicate_primitive','__file__':str(path)};exec(compile(raw,str(path),'exec'),ns);return ns
class NullSink:
    def write(self,value):need(len(value)<=65536,'reviewed write bound differs');return len(value)

def locate(source,base,check):
    """Strict original parser prefix; stop at first duplicate, never repair it."""
    class Diagnostic(base['Minifier']):
        def __init__(self):
            super().__init__(source,NullSink(),raw_limit=2147483648,retained_limit=134217728,check=check)
            self.frames=[];self.active=[];self.last_token=None;self.string_value=None
        def emit(self,value):
            for item in self.active:item['hash'].update(value);item['bytes']+=len(value)
            self.last_token={'bytes':len(value),'sha256':hashlib.sha256(value).hexdigest()}
            if len(value)<=128 and value.isascii():self.last_token['ascii_token']=value.decode('ascii')
            return super().emit(value)
        def string(self,*,key=False):
            result=super().string(key=key);self.string_value=result;return result
        def value(self,depth=0,field='$'):
            r=self.reader;r.whitespace();start=position(r);byte=r.peek()
            category={123:'object',91:'array',34:'string',116:'true',102:'false',110:'null'}.get(byte,'number')
            tracker={'hash':hashlib.sha256(),'bytes':0};self.active.append(tracker);self.string_value=None
            need(depth<=256,'diagnostic complete JSON depth bound');self.max_depth=max(self.max_depth,depth)
            self.tokens+=1;need(self.tokens<=20000000,'diagnostic token count bound')
            context={}
            if byte==123:
                self.objects+=1;self.emit(r.take());r.whitespace();seen={};charged=0
                frame={'field':field,'object_start':start,'metadata':context,'keys_seen':[]};self.frames.append(frame)
                if r.peek()!=125:
                    while True:
                        key_start=position(r);key=self.string(key=True);key_end=position(r);token=dict(self.last_token)
                        r.whitespace();need(r.take()==b':','diagnostic JSON object colon required');self.emit(b':');r.whitespace()
                        if key in seen:
                            second={'key_span':[key_start,key_end],'key_token':token,'value_start':position(r),
                                'value_kind':{123:'object',91:'array',34:'string',116:'true',102:'false',110:'null'}.get(r.peek(),'number')}
                            # Observe only a scalar second value. Composite content
                            # is never skipped/repaired or used as an accepted node.
                            if r.peek() not in (123,91):second['scalar_value']=self.value(depth+1,field=key)
                            report={'decoded_key':key[:256],'decoded_key_complete':len(key)<=256,
                                'decoded_key_utf8_sha256':hashlib.sha256(key.encode('utf-8','surrogatepass')).hexdigest(),
                                'decoded_key_codepoints':len(key),'first':seen[key],'second':second,
                                'object_start':start,'object_metadata':dict(context),
                                'ancestor_context':[{'field':f['field'],'object_start':f['object_start'],'metadata':dict(f['metadata']),
                                    'preceding_keys':f['keys_seen'][-20:]} for f in self.frames[-12:]],
                                'strict_refusal':'duplicate compiler JSON key','strict_JSON_accepted':False,'AST_repaired_or_projected':False}
                            raise DuplicateFound(report)
                        count=len(key.encode('utf-8','surrogatepass'))+64;charged+=count;self.key_bytes+=count;self.keys+=1
                        self.peak_key_bytes=max(self.peak_key_bytes,self.key_bytes)
                        need(len(seen)<1024 and self.key_bytes<=16777216,'diagnostic live key census bound')
                        value=self.value(depth+1,field=key);seen[key]={'key_span':[key_start,key_end],'key_token':token,'value':value}
                        frame['keys_seen'].append(key[:128])
                        if key in {'kind','id','name','mangledName','file','line','offset','isImplicit','valueCategory','opcode'} and value['kind'] not in ('object','array'):
                            context[key]=value.get('preview','')
                        if key in {'loc','range','begin','end','spellingLoc','expansionLoc'} and value.get('object_metadata'):
                            context[key]=value['object_metadata']
                        r.whitespace();marker=r.take();need(marker in (b',',b'}'),'diagnostic object delimiter required');self.emit(marker)
                        if marker==b'}':break
                        r.whitespace()
                else:self.emit(r.take())
                self.frames.pop();self.key_bytes-=charged
            elif byte==91:
                self.arrays+=1;self.emit(r.take());r.whitespace();index=0
                if r.peek()!=93:
                    while True:
                        self.value(depth+1,field=field+'['+str(index)+']');index+=1;r.whitespace();marker=r.take()
                        need(marker in (b',',b']'),'diagnostic array delimiter required');self.emit(marker)
                        if marker==b']':break
                else:self.emit(r.take())
            else:super().scalar()
            self.active.pop();summary={'kind':category,'raw_span':[start,position(r)],'minified_bytes':tracker['bytes'],'minified_sha256':tracker['hash'].hexdigest()}
            if category=='string':summary['preview']=self.string_value[:128];summary['preview_complete']=len(self.string_value)<=128
            elif category not in ('object','array'):
                # Scalar lexemes are bounded at128B in the original parser.
                summary['preview']=self.last_token
            if context:summary['object_metadata']=context
            return summary
    parser=Diagnostic()
    try:parser.run()
    except DuplicateFound as found:return found.metadata
    raise Refused('expected first strict duplicate was not reproduced; original policy remains unchanged')

def inspect(raw):
    started=time.monotonic();raw=Path(raw);need(raw.is_absolute() and raw.resolve(strict=True)==raw and raw.name==RAW_NAME,'exact V10 raw required')
    control=raw/'control';out=raw/'component';policy_path=control/'linux_compiler_capture_policy_v10.json'
    need(pin(policy_path)['sha256']==POLICY_SHA,'exact original policy required');policy=document(policy_path)
    result=document(out/'result.json');need(result['accepted'] is False and result['error']=={'type':'Refused','message':'duplicate compiler JSON key'}
        and result['after_input_errors']==[] and result['bytecode_cache_present'] is False,'preserved exact duplicate refusal required')
    receipt=document(out/'caller.ast.gzip.json');gzip_pin=pin(out/'caller.ast.json.gz')
    need((gzip_pin['bytes'],gzip_pin['sha256'])==(receipt['compressed_bytes'],receipt['compressed_sha256']),'original gzip receipt differs')
    need(not os.path.lexists(out/'caller.ast.identity.json') and not os.path.lexists(out/'caller.ast.minified.json'),'no completed identity/admission may be inferred')
    inputs=[pin(policy_path),gzip_pin,pin(out/'caller.ast.gzip.json'),pin(out/'result.json')]
    for name,expected in (('linux_compiler_capture_v10.py',ENTRY_SHA),('lossless_gzip_v2.py',CODEC_SHA),('strict_minify_v2.py',MINIFIER_SHA)):
        row=pin(control/name);need(row['sha256']==expected and {k:row[k] for k in ('bytes','sha256')}==policy['controller_files'][name],'reviewed primitive/control differs');inputs.append(row)
    entry=load(control/'linux_compiler_capture_v10.py',ENTRY_SHA);zlib_module,zbefore=entry['bind_zlib'](policy)
    codec=load(control/'lossless_gzip_v2.py',CODEC_SHA);base=load(control/'strict_minify_v2.py',MINIFIER_SHA)
    def check():need(time.monotonic()-started<90,'bounded metadata diagnostic deadline exceeded')
    with (out/'caller.ast.json.gz').open('rb') as stream:
        decoded=codec['DecodeReader'](zlib_module,stream,receipt,expanded_limit=2147483648,compressed_limit=134217728,check=check)
        report=locate(decoded,base,check)
        while decoded.read(65536):check()
        need(decoded.verified,'entire original raw/gzip identity must verify')
    need(entry['bind_zlib'](policy)[1]==zbefore,'diagnostic zlib/runtime binding changed')
    for row in inputs:need(pin(row['path'])==row,'passive diagnostic input changed')
    need(not EVENTS,'no child permitted')
    return {'schema':'first-strict-duplicate-metadata-1','raw_root':str(raw),'inputs':inputs,'first_duplicate':report,
        'full_raw_bytes':receipt['expanded_bytes'],'full_raw_sha256':receipt['expanded_sha256'],'gzip_bytes':gzip_pin['bytes'],'gzip_sha256':gzip_pin['sha256'],
        'complete_decoder_identity_verified':True,'wall_seconds':time.monotonic()-started,'child_events':EVENTS,
        'strict_policy_relaxed':False,'AST_source_call_ABI_or_proof_admission':False,'actual_compiler_rerun':False}
if __name__=='__main__':
    need(len(sys.argv)==2 and __debug__ and sys.flags.isolated and sys.dont_write_bytecode,'isolated no-bytecode diagnostic requires original raw')
    value=json.dumps(inspect(sys.argv[1]),sort_keys=True,allow_nan=False);need(len(value.encode())<=32768,'compact metadata output cap exceeded');print(value)
