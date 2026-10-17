"""Pure synthetic streaming work estimate; no actual retained TU or children.

Fixed finite local work: 2 MiB complete plus a 543412150-byte prospective
synthetic stream whose walk is stopped at 20 seconds. No target runtime speed
or successful complete actual census is inferred from this Mac measurement.
"""
import hashlib
import json
from pathlib import Path
import sys
import time
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;EVENTS=[]
def audit(event,args):
    if event.startswith(('subprocess.','socket.','os.exec','os.spawn','os.posix_spawn','os.fork')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('synthetic throughput forbids '+event)
sys.addaudithook(audit)
def load(path,digest):
    raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
    ns={'__name__':'inert_synthetic_only','__file__':str(path)};exec(compile(raw,str(path),'exec'),ns);return ns
S=load(WHOLE/'compiler-duplicate-census-v2/complete_duplicate_census_v2.py','d265c49485057cbd43cfd913cfc905683090866174b45d863f22121331d997b3')
B=load(WHOLE/'streaming-minify-v1/strict_minify_v2.py','b866e14fe3ca210de178aab71f5c8a662e15f818a5ca485095487b005ae51897')
nodes=[]
for i in range(32):
    node={'id':hex(i+1),'kind':'BuiltinType','type':{'qualType':'unsigned long'},
        'loc':{'offset':i*32,'file':'/synthetic/only.cpp','line':i+1,'col':3,'tokLen':4},
        'range':{'begin':{'offset':i*32,'col':3,'tokLen':4},'end':{'offset':i*32+16,'col':19,'tokLen':1}}}
    nodes.append(json.dumps(node,indent=6,separators=(',',': ')).encode())
nodes[0]=b'{"id":"0x1","kind":"UsingType","type":{"qualType":"Alias"},"decl":{"id":"0x2","kind":"UsingShadowDecl","name":"Alias"},"type":{"qualType":"unsigned long"},"inner":[]}'
BLOCK=b',\n'.join(nodes)+b',\n'
PREFIX=b'{"id":"0x0","kind":"TranslationUnitDecl","inner":[\n'
LAST=json.dumps({'id':'0xffff','kind':'BuiltinType','type':{'qualType':'int'}},indent=2).encode()+b']}'
class Stream:
    def __init__(self,size):
        count=(size-len(PREFIX)-len(LAST))//len(BLOCK)
        assert count>0
        self.parts=[(PREFIX,1),(BLOCK,count),(LAST,1),(b' ',size-len(PREFIX)-count*len(BLOCK)-len(LAST))]
        self.index=0;self.at=0;self.total=0;self.target=size;self.blocks=count
    def read(self,size):
        out=bytearray()
        while len(out)<size and self.index<len(self.parts):
            value,repeats=self.parts[self.index];length=len(value)*repeats
            if self.at==length:self.index+=1;self.at=0;continue
            amount=min(size-len(out),len(value)-self.at%len(value),length-self.at)
            out.extend(value[self.at%len(value):self.at%len(value)+amount]);self.at+=amount
        self.total+=len(out);return bytes(out)
def run(size,seconds):
    source=Stream(size);started=time.monotonic();cpu=time.process_time()
    def check():
        if time.monotonic()-started>=seconds:raise TimeoutError('synthetic work-estimate deadline')
    result=None;error=None
    try:result=S['census'](source,B,check)
    except TimeoutError as exc:error=str(exc)
    elapsed=time.monotonic()-started;used=time.process_time()-cpu
    return {'target_bytes':size,'source_read_bytes_including_at_most_64KiB_lookahead':source.total,
        'complete':result is not None,'deadline_seconds':seconds,'wall_seconds':elapsed,'CPU_seconds':used,
        'source_read_MiB_per_wall_second':source.total/1048576/elapsed,'error':error,
        'complete_values':None if result is None else result['values'],'complete_duplicate_events':None if result is None else result['duplicate_events'],
        'synthetic_block_count':source.blocks,'synthetic_block_sha256':hashlib.sha256(BLOCK).hexdigest(),
        'actual_TU_bytes_read':False,'actual_target_runtime_measured':False}
if __name__=='__main__':
    rows=[run(2097152,20),run(543412150,20)]
    assert rows[0]['complete'] and rows[0]['source_read_bytes_including_at_most_64KiB_lookahead']==2097152
    assert not EVENTS and not S['EVENTS']
    print(json.dumps({'date':'2026-10-16 ET','scope':'synthetic Mac streaming throughput only; no actual full-TU/main/compiler/remote',
        'rows':rows,'child_events':EVENTS+S['EVENTS'],'hard_address_space_or_external_CPU_cap_applied':False,
        'complete_actual_success_or_linux_rate_inferred':False},sort_keys=True))
