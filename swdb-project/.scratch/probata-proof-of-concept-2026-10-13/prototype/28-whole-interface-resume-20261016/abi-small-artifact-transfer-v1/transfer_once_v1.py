"""Exact authorized transfer of four compact retained synthetic metadata files."""
import hashlib
import json
from pathlib import Path
import selectors
import subprocess
import threading
import time

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent / "abi-retained-replay-v1"
def sha(raw): return hashlib.sha256(raw).hexdigest()
def pin(path):
    raw=path.read_bytes();return dict(path=str(path),bytes=len(raw),sha256=sha(raw))
def save(name,value):
    with(HERE/name).open('x')as handle:json.dump(value,handle,sort_keys=True,indent=2);handle.write('\n')
def main():
    assert not(HERE/'invocation.json').exists(),'once-only transfer already attempted'
    policy=json.loads((PACKET/'controls/policy.json').read_bytes())
    rows=[]
    for selected in policy['artifacts']:
        stem='original-first'if selected['family']=='first-source-v10'else'original-memory'
        rows += [dict(local=stem+'-ABI.json',pin=selected['ABI']),dict(local=stem+'-probe.cpp',pin=selected['probe'])]
    remote='''import resource
resource.setrlimit(resource.RLIMIT_AS,(536870912,536870912))
resource.setrlimit(resource.RLIMIT_CPU,(10,12))
import hashlib,json,os,signal,stat,sys
from pathlib import Path
signal.alarm(15)
ROWS=ROWS_LITERAL
PY_SHA=PY_SHA_LITERAL
def stable(st):return {k:getattr(st,k)for k in('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns')}
def readonly(event,args):
 if event=='open':
  _path,mode,flags=args
  if(isinstance(mode,str)and any(c in mode for c in'wax+'))or flags&(1|2|64|512|1024):raise PermissionError('read-only compact ABI transfer')
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.'))or event in{'os.system','ctypes.dlopen','os.mkdir','os.remove','os.unlink','os.rename','os.replace','os.rmdir','os.chmod','os.chown','os.link','os.symlink','os.truncate','os.utime'}:raise PermissionError('no child/native/network/mutation')
sys.addaudithook(readonly)
assert sys.flags.isolated and sys.flags.dont_write_bytecode and sys.flags.no_user_site and sys.flags.safe_path
assert dict(os.environ)=={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'}
assert str(Path(sys.executable).resolve())=='/usr/bin/python3.12'
assert hashlib.sha256(Path('/usr/bin/python3.12').read_bytes()).hexdigest()==PY_SHA
def leases():
 value={p.name:json.loads(p.read_bytes())for p in Path('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')}
 assert len(value)==3 and all(row['state']=='released'for row in value.values());return value
before_leases=leases();metadata=[];payload=[]
for row in ROWS:
 selected=row['pin'];path=Path(selected['path']);before=path.lstat()
 assert selected['bytes']in(127394,127541,1588)and path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode)and before.st_size==selected['bytes']
 with path.open('rb')as handle:raw=handle.read(selected['bytes']+1)
 after=path.lstat()
 assert len(raw)==selected['bytes']and hashlib.sha256(raw).hexdigest()==selected['sha256']and stable(before)==stable(after)
 metadata.append(dict(local=row['local'],pin=selected,before=stable(before),after=stable(after)));payload.append(raw)
assert sum(map(len,payload))==258111
after_leases=leases()
header=json.dumps(dict(schema='exact-compact-two-ABI-transfer-1',files=metadata,total_payload_bytes=258111,leases_before=before_leases,leases_after=after_leases,original_raw_unchanged=True,compiler_native_project_execution=False),sort_keys=True,separators=(',',':')).encode()+b'\\n'
assert len(header)<=16384
sys.stdout.buffer.write(header)
for raw in payload:sys.stdout.buffer.write(raw)
sys.stdout.buffer.flush()
'''
    remote=remote.replace('ROWS_LITERAL',repr(rows)).replace('PY_SHA_LITERAL',repr(policy['runtime_hashes']['/usr/bin/python3.12']))
    source=HERE/'read_exact_small_artifacts_v1.py';source.write_text(remote)
    argv=['ssh','mbit10','/usr/bin/env -i PATH=/usr/bin:/bin LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 /usr/bin/timeout --signal=TERM --kill-after=3s 20s /usr/bin/python3 -I -B -']
    started=time.monotonic();process=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    errors=[]
    def writer():
        try:process.stdin.write(remote.encode());process.stdin.close()
        except(BrokenPipeError,OSError)as error:errors.append(type(error).__name__)
    thread=threading.Thread(target=writer,daemon=True);thread.start()
    selected=selectors.DefaultSelector();selected.register(process.stdout,selectors.EVENT_READ,'stdout');selected.register(process.stderr,selectors.EVENT_READ,'stderr')
    data={'stdout':bytearray(),'stderr':bytearray()};refusal=None
    while selected.get_map():
        if time.monotonic()-started>30:refusal='local30s deadline';process.kill();break
        for key,_ in selected.select(.25):
            chunk=key.fileobj.read1(4096)
            if not chunk:selected.unregister(key.fileobj);continue
            name = key.data
            cap = 300000 if name == 'stdout' else 16384
            if len(data[name])+len(chunk)>cap:refusal=name+' extent cap';process.kill();break
            data[name].extend(chunk)
        if refusal:break
    selected.close();code=process.wait(timeout=5);thread.join(timeout=1)
    with(HERE/'wire.bin').open('xb')as handle:handle.write(data['stdout'])
    with(HERE/'stderr.txt').open('xb')as handle:handle.write(data['stderr'])
    save('invocation.json',dict(argv=argv,stdin=pin(source),returncode=code,local_wall_seconds=time.monotonic()-started,local_refusal=refusal,writer_errors=errors,stdout=pin(HERE/'wire.bin'),stderr=pin(HERE/'stderr.txt')))
    assert code==0 and refusal is None and not data['stderr'],'transfer refused; preserve without retry'
    head,body=bytes(data['stdout']).split(b'\n',1);assert len(head)<=16384
    metadata=json.loads(head);assert metadata['total_payload_bytes']==len(body)==258111 and len(metadata['files'])==4
    offset=0;files=[]
    for original,row in zip(rows,metadata['files']):
        assert row['local']==original['local']and row['pin']==original['pin']and row['before']==row['after']
        raw=body[offset:offset+row['pin']['bytes']];offset+=len(raw)
        assert len(raw)==row['pin']['bytes']and sha(raw)==row['pin']['sha256']
        path=HERE/row['local']
        with path.open('xb')as handle:handle.write(raw)
        files.append(dict(remote=row['pin'],local=pin(path),before=row['before'],after=row['after']))
    assert offset==len(body)
    save('verified-transfer.json',dict(schema=metadata['schema'],files=files,leases_before=metadata['leases_before'],leases_after=metadata['leases_after'],original_raw_unchanged=True,source_or_scientific_admission=False))
    print(json.dumps(dict(returncode=code,files=[row['local']for row in files],total_payload_bytes=offset,verified_transfer=pin(HERE/'verified-transfer.json')),sort_keys=True))
if __name__=='__main__':main()
