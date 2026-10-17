"""2026-10-16 ET. Admitted original public V4 passive preflight; no children/writes."""
import hashlib
import json
import os
from pathlib import Path
import signal
import stat
import sys
RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-1433b8f5-t25-closed-source-public-v4')
REPO=Path('/data1/yanruj/probata-resume-20261016-1433b8f5')
SOURCE='1433b8f58baa63538d1e8aa8a33d9ce566826407'
signal.alarm(30)
def need(ok,reason):
    if not ok:raise ValueError(reason)
def audit(event,values):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in ('os.system','ctypes.dlopen'):
        raise RuntimeError('read-only preflight forbids child/native/network')
    if event=='open':
        path,mode,flags=values
        need(not ((isinstance(mode,str) and any(c in mode for c in 'wax+')) or flags&os.O_ACCMODE!=os.O_RDONLY or flags&(os.O_CREAT|os.O_TRUNC|os.O_APPEND)),'preflight write refused')
    if event in ('os.mkdir','os.remove','os.rmdir','os.rename','os.link','os.symlink','os.truncate','os.chmod','os.chown','os.utime'):
        raise RuntimeError('preflight mutation refused')
sys.addaudithook(audit)
def read(path,cap=1048576):
    before=path.lstat();need(stat.S_ISREG(before.st_mode) and before.st_size<=cap,'bounded regular preflight input')
    raw=path.read_bytes();after=path.lstat()
    fields=('st_dev','st_ino','st_mode','st_size','st_mtime_ns','st_ctime_ns')
    need(all(getattr(before,k)==getattr(after,k) for k in fields) and len(raw)==before.st_size,'preflight metadata changed')
    return raw,{'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
try:
    need(sys.flags.isolated and sys.dont_write_bytecode and __debug__,'isolated nonoptimized preflight')
    need(RAW.resolve(strict=True)==RAW and REPO.resolve(strict=True)==REPO and RAW.is_dir() and (REPO/'swdb-project').is_dir(),'original source/raw physical paths')
    dot=REPO/'.git'
    if dot.is_dir():gitdir=dot.resolve(strict=True)
    else:
        value,pin=read(dot,4096);prefix='gitdir: ';text=value.decode().strip();need(text.startswith(prefix),'worktree Git directory pointer')
        gitdir=(REPO/text[len(prefix):]).resolve(strict=True)
    head,headpin=read(gitdir/'HEAD',4096)
    need(head.decode().strip()==SOURCE,'original source must retain exact detached HEAD')
    pins={};metadata={}
    for name in ('lane.json','resources.json','outer-resources.json','source-after.json'):
        raw,pin=read(RAW/name);pins[name]=pin;metadata[name]=json.loads(raw)
    lane=metadata['lane.json']['socket_lane']
    need(lane['node']==0 and lane['lease_generation']==619 and lane['ended_utc']=='2026-10-16T21:28:57Z' and lane['exit_code']==0,'original finite G619 settlement')
    for name in ('resources.json','outer-resources.json'):
        row=metadata[name];need(row['exit_code']==0 and not row['out_of_memory'] and not row['timed_out'],'original healthy whole-tree resources')
    need(metadata['source-after.json']=={'commit':SOURCE,'source_unchanged':True,'tracked_changes':''},'original source-after evidence')
    readers=[];checked=0
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit() or int(directory.name)==os.getpid():continue
        try:
            command=(directory/'cmdline').read_bytes()
        except (FileNotFoundError,ProcessLookupError):continue
        need(len(command)<=1048576,'process command metadata cap');checked+=1
        if bytes(RAW) in command or bytes(REPO) in command:
            readers.append({'pid':int(directory.name),'argv_bytes':len(command),'argv_sha256':hashlib.sha256(command).hexdigest()})
    need(not readers,'original source/raw still has a producer or reader process')
    print(json.dumps({'status':'PASS_ORIGINAL_SETTLED_PREFLIGHT','source_commit':SOURCE,'raw_root':str(RAW),'head':headpin,'metadata':pins,
        'processes_scanned':checked,'matching_original_source_or_raw_processes':readers,'unrelated_current_lanes_ignored':True,
        'native_tool_or_child_or_project_import':False,'raw_or_source_mutation':False,'scientific_acceptance':False},sort_keys=True))
except Exception as error:
    print(json.dumps({'status':'PREFLIGHT_REFUSED','error':type(error).__name__,'reason':str(error)[:2048],'scientific_acceptance':False},sort_keys=True))
    raise SystemExit(1)
