"""2026-10-16 ET. Root-authorized finite source9-V3 passive metadata collection.

No compiler/verifier/native helper/version query or proof rerun. No raw mutation.
Raw source/formula/AST/SMT bytes stay remote; only compact statuses/pins are emitted.
"""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import stat
import subprocess
import sys

RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-032e1851-owned-source9-public-v3')
PROFILE=RAW/'owned-source9-public-v3-profile'
SOURCE=Path('/data1/yanruj/probata-resume-20261016-032e1851')
TARGETS=['move.destination_header','move.source_empty','move.incoming_frame','move.owner_correspondence',
         'swap.left_header','swap.right_header','swap.temporary_lifetime','swap.incoming_frame','swap.owner_correspondence']


def need(value,label):
    if not value:raise ValueError(label)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def identity(st):return (st.st_dev,st.st_ino,st.st_mode,st.st_nlink,st.st_size,st.st_mtime_ns,st.st_ctime_ns)


def parents(path):
    rows=[(p,p.lstat()) for p in reversed(path.parents)]
    need(path.is_absolute() and '..' not in path.parts and all(stat.S_ISDIR(st.st_mode) for p,st in rows),'physical canonical ancestors')
    return rows


def data(path,cap=4*1024**2):
    path=Path(path);chain=parents(path);st=path.lstat()
    need(stat.S_ISREG(st.st_mode) and st.st_size<=cap,'bounded regular metadata')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        need(identity(st)==identity(os.fstat(fd)),'physical original metadata fd')
        blocks=[];remaining=cap+1
        while remaining:
            block=os.read(fd,min(65536,remaining))
            if not block:break
            blocks.append(block);remaining-=len(block)
        raw=b''.join(blocks)
        need(len(raw)==st.st_size and len(raw)<=cap and identity(st)==identity(os.fstat(fd))==identity(path.lstat()),'stable complete bounded metadata')
        need(all(identity(old)==identity(p.lstat()) for p,old in chain),'stable ancestors')
        return raw
    finally:os.close(fd)


def physical_pin(path):
    path=Path(path);chain=parents(path);st=path.lstat();need(stat.S_ISREG(st.st_mode),'regular hash input')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        need(identity(st)==identity(os.fstat(fd)),'original hash fd')
        h=hashlib.sha256();count=0
        while True:
            b=os.read(fd,1024*1024)
            if not b:break
            h.update(b);count+=len(b)
        need(count==st.st_size and identity(st)==identity(os.fstat(fd))==identity(path.lstat()),'stable hash input')
        need(all(identity(old)==identity(p.lstat()) for p,old in chain),'stable hash ancestors')
        return {'bytes':count,'sha256':h.hexdigest()}
    finally:os.close(fd)


def extent():
    pending=[RAW];rows=[];total=0
    while pending:
        directory=pending.pop();st=directory.lstat();need(stat.S_ISDIR(st.st_mode),'physical census directory')
        with os.scandir(directory) as stream:children=sorted(stream,key=lambda e:e.name)
        for child in children:
            path=directory/child.name;s=path.lstat();r={'relative':str(path.relative_to(RAW))}
            if stat.S_ISDIR(s.st_mode):r['kind']='directory';pending.append(path)
            elif stat.S_ISREG(s.st_mode):
                total+=s.st_size;need(total<=2*1024**3,'bounded raw extent');r.update(kind='regular',**physical_pin(path))
            elif stat.S_ISLNK(s.st_mode):r.update(kind='symlink',target=os.readlink(path))
            else:r.update(kind='special',mode=stat.S_IFMT(s.st_mode))
            rows.append(r);need(len(rows)<=10000,'bounded raw membership')
        need(identity(st)==identity(directory.lstat()),'stable settled traversal')
    return sorted(rows,key=lambda r:Path(r['relative']).parts)


def read_json(path):
    def pairs(rows):
        out={}
        for k,v in rows:need(k not in out,'unique metadata key');out[k]=v
        return out
    return json.loads(data(path),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('finite JSON')))


def command(argv):return subprocess.check_output(argv,timeout=30,text=True,env={'PATH':'/usr/bin:/bin','HOME':'/nonexistent','LC_ALL':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_OPTIONAL_LOCKS':'0'})


def git_state(path):
    prefix=['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-c','core.preloadIndex=false','-c','index.threads=1','-C',str(path)]
    return {'branch':command(prefix+['rev-parse','--abbrev-ref','HEAD']).strip(),
            'commit':command(prefix+['rev-parse','HEAD']).strip(),
            'dirty':bool(command(prefix+['status','--porcelain','--untracked-files=all']).strip())}


def summarize(value):
    if isinstance(value,dict):
        return {k:({'items':len(v),'canonical_sha256':digest(canonical(v))} if isinstance(v,(list,dict)) and len(v)>50 else summarize(v)) for k,v in value.items()}
    if isinstance(value,list):
        return {'items':len(value),'canonical_sha256':digest(canonical(value))} if len(value)>50 else [summarize(v) for v in value]
    return value


def main():
    result={'date':'2026-10-16 ET','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'raw_root':str(RAW),'raw_payload_transferred':False,'science_or_proof_rerun':False,'raw_mutation':False}
    result['connection_preflight']={'uptime':command(['/usr/bin/uptime']).strip(),
        'disk':command(['/usr/bin/df','-B1','/data1','/data']).strip(),'logged_sessions':len(command(['/usr/bin/who']).splitlines()),
        'leases':{},'source':git_state(SOURCE),'primary_source':git_state(Path('/data1/yanruj/ArchEvolve'))}
    for name in ['mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1']:
        path=Path('/data1/yanruj/lact-host-lease')/(name+'.meta.json')
        try:result['connection_preflight']['leases'][name]=read_json(path)
        except FileNotFoundError:result['connection_preflight']['leases'][name]={'absent':True}
    result['metadata']={};result['metadata_pins']={};result['log_status_snippets']={}
    for relative in ['lane.json','launch.json','resources.json','outer-resources.json','source-before.json','source-after.json',
                     'owned-source9-public-root-early-preflight.json','owned-source9-public-v3-profile/result.json',
                     'owned-source9-public-v3-profile/root-siblings-before.json','owned-source9-public-v3-profile/root-siblings-after.json']:
        path=RAW/relative
        try:value=read_json(path)
        except FileNotFoundError:continue
        result['metadata'][relative]=summarize(value);result['metadata_pins'][relative]=physical_pin(path)
    result['leaves']=[]
    for target in TARGETS:
        leaf=PROFILE/('leaf-'+target);r={'id':target,'exists':leaf.exists(),'metadata':{},'pins':{}}
        if not leaf.exists():result['leaves'].append(r);continue
        need(stat.S_ISDIR(leaf.lstat().st_mode),'physical leaf')
        for name in ['resources.json','outcome.json','task-census.json','command.json','wp-goals.json','wp-inventory.json']:
            path=leaf/name
            try:value=read_json(path)
            except FileNotFoundError:continue
            r['pins'][name]=physical_pin(path)
            if name in ['resources.json','outcome.json','task-census.json','command.json']:r['metadata'][name]=summarize(value)
            elif name=='wp-goals.json':r['goal_report_shape']={'type':type(value).__name__,'items':len(value) if isinstance(value,(list,dict)) else None}
        r['report_files']={name:physical_pin(leaf/name) for name in ['frama-c.log','wp-properties.csv','wp-normalized.c'] if (leaf/name).exists()}
        resource=r['metadata'].get('resources.json',{})
        if resource.get('exit_code',0)!=0 or r['metadata'].get('outcome.json',{}).get('verdict')=='not_proven':
            log=leaf/'frama-c.log'
            if log.exists():
                text=data(log,cap=4*1024**2).decode('utf-8','replace')
                selected=[line[:512] for line in text.splitlines() if re.search(r'User Error|syntax error|Typing error|Fatal|\bError\b|\bTimeout\b|Proved goals|Scheduled goals|WP goals',line)]
                r['native_status_snippet']=selected[-12:]
        result['leaves'].append(r)
    for name in ['acceptance.log','worker.log']:
        path=RAW/name
        if path.exists():
            text=data(path,cap=1024**2).decode('utf-8','replace')
            selected=[line[:512] for line in text.splitlines() if re.search(r'REFUSED|Error|Exception|Traceback|status|exit|timeout|timed_out|out_of_memory',line,re.I)]
            result['log_status_snippets'][name]={'pin':physical_pin(path),'selected_lines':selected[-10:]}
    lane=result['metadata'].get('lane.json',{}).get('socket_lane',{})
    result['settled_by_explicit_end_and_resources']=bool(lane.get('ended_utc') and 'outer-resources.json' in result['metadata'] and 'resources.json' in result['metadata'])
    if result['settled_by_explicit_end_and_resources']:
        before=extent();after=extent();need(before==after,'stable full settled retention census')
        result['retention']={'regular_files':sum(r['kind']=='regular' for r in after),'directories':sum(r['kind']=='directory' for r in after),
                             'bytes':sum(r.get('bytes',0) for r in after),'symlinks':[r for r in after if r['kind']=='symlink'],
                             'specials':[r for r in after if r['kind']=='special'],'pre_post_equal':True,
                             'manifest_sha256':digest(canonical(after)),'manifest':after}
    payload=canonical(result)+b'\n';need(len(payload)<=1024**2,'compact output cap');sys.stdout.buffer.write(payload)


if __name__=='__main__':main()
