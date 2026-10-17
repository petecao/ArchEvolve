#!/usr/bin/env python3
"""Fixed T17 data-only preparation and guarded driver entry. Created 2026-09-27 ET."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import tarfile
import time

COMMIT='8cbfee600f23416a8e9578fa8d3ce3f0e19fced8'
EVIDENCE='efdadb8b1e7ff22562d07e9f63007198a6b6352d'
RUNTIME=Path('/data1/yanruj/EvolveSWDB_supervision_recovery_runtime_20260927_a1')
DISPATCH=Path('/data/yanruj/EvolveSWDB_runs/bfs-t17-diagnostic-build-only-20260926-a1.dispatch')
RECORDS=DISPATCH/'record-view/records'
PYTHON_SHA='e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'
OVERLAYS={
 'records/proposals/bfs-campaign-preparation-20260925-a1.dx100-instructions.yaml':'a556d0ca47c2f04661eaa9af35c6c86b5fff0afd22a76ebcd9f6d5df5b1551f6',
 'records/candidates/bfs-campaign-preparation-20260925-a1.dx100-instructions.candidate-1.yaml':'2a4691b9036c7ecbbae4be956ece6d602e55a2a0f296f45a958f7e91c2ce9ac4',
 'records/evaluations/bfs-t17-build-only-20260926-a1.yaml':'d5ed1ec5b43665379a2b8d59cc2b4cbc582502beb62f5184041079e606229215'}


def require(value,why):
    if not value:raise RuntimeError(why)


def digest(data):return hashlib.sha256(data).hexdigest()
def reference(path):return {'path':str(path),'sha256':digest(Path(path).read_bytes())}
def git(*args):
    # Evidence objects are fetched into the separate operator checkout, never the active runtime.
    source=Path(__file__).resolve().parents[4] if any(arg.startswith(EVIDENCE) for arg in args) else RUNTIME
    return subprocess.check_output(['git','-C',str(source),*args],timeout=15)


def guard(manifest, expected):
    require(digest(manifest.read_bytes())==expected,'manifest hash differs')
    value=json.loads(manifest.read_text());require(value['commit']==COMMIT,'manifest commit differs')
    require(RUNTIME==RUNTIME.resolve() and git('rev-parse','HEAD').decode().strip()==COMMIT,'runtime root/commit differs')
    wanted=value['files'];actual=set();begin=time.monotonic()
    import os
    for folder,dirs,files in os.walk(RUNTIME,followlinks=False):
        if Path(folder)==RUNTIME:dirs[:]=[d for d in dirs if d!='.git'];files=[f for f in files if f!='.git']
        require(time.monotonic()-begin<15 and len(actual)<=8192,'inventory exceeds bound')
        for name in dirs+files:require(not (Path(folder)/name).is_symlink(),'runtime symlink')
        for name in files:
            p=Path(folder)/name;rel=str(p.relative_to(RUNTIME));actual.add(rel)
            require(rel in wanted and p.stat().st_size==wanted[rel]['bytes'] and digest(p.read_bytes())==wanted[rel]['sha256'],'runtime bytes differ: '+rel)
    require(actual==set(wanted),'runtime files missing')
    require(digest(Path(sys.executable).resolve().read_bytes())==PYTHON_SHA,'Python changed')
    require(sys.flags.no_user_site and sys.dont_write_bytecode and not sys.flags.optimize,'isolated Python flags required')


def materialize(complete_partial=False):
    require(not DISPATCH.exists() or complete_partial,'dispatch already exists; never overwrite prepared evidence')
    archive=git('archive','--format=tar',COMMIT,'records')
    require(len(archive)<=32*1024**2,'record archive exceeds bound')
    overlays={name:git('show',EVIDENCE+':'+name) for name in OVERLAYS}
    require(all(digest(data)==OVERLAYS[name] for name,data in overlays.items()),'overlay bytes differ')
    records={};excluded=[]
    allowed_sources={'records/implementations/gapbs-cc-sv/cc_sv.cc','records/implementations/gapbs-pr-jacobi/pr_spmv.cc'}
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as tar:
        members=tar.getmembers();require(len(members)<=4096,'too many archive entries')
        for member in members:
            path=Path(member.name)
            require(path.parts[0]=='records' and not path.is_absolute() and '..' not in path.parts,'unsafe archive path')
            if member.isdir():continue
            require(member.isfile() and member.size<=4*1024**2,'unsafe record archive member')
            data=tar.extractfile(member).read()
            if path.suffix!='.yaml':
                require(member.name in allowed_sources,'unexpected non-record source')
                excluded.append({'path':member.name,'bytes':len(data),'sha256':digest(data),'retained_in':'records-base.tar'})
                continue
            require(member.name not in records,'duplicate archive record')
            records[member.name]=data
    for name,data in overlays.items():
        require(name not in records or records[name]==data,'base/overlay conflict')
        records[name]=data
    reused=[]
    if DISPATCH.exists():
        require(DISPATCH==DISPATCH.resolve() and not DISPATCH.is_symlink(),'unsafe partial dispatch')
        require({p.name for p in DISPATCH.iterdir()} <= {'records-base.tar','record-view'},'partial dispatch contains sealed or unknown evidence')
        require((DISPATCH/'records-base.tar').is_file() and (DISPATCH/'records-base.tar').read_bytes()==archive,'retained archive changed')
        for path in DISPATCH.rglob('*'):
            require(not path.is_symlink(),'partial view symlink')
            if path.is_dir() or path==DISPATCH/'records-base.tar':continue
            require(path.is_relative_to(RECORDS),'unexpected partial file')
            name='records/'+str(path.relative_to(RECORDS))
            require(name in records and path.read_bytes()==records[name],'partial record changed')
            reused.append(name)
    else:
        DISPATCH.mkdir();RECORDS.mkdir(parents=True)
        with (DISPATCH/'records-base.tar').open('xb') as stream:stream.write(archive)
    provenance=[{'commit':COMMIT,'tree':git('rev-parse',COMMIT+':records').decode().strip(),
                 'archive':reference(DISPATCH/'records-base.tar'),'scope':'all base YAML records',
                 'non_record_sources_retained_in_archive':excluded,'identical_partial_records_reused':sorted(reused)}]
    for name,data in records.items():
        dest=RECORDS/Path(*Path(name).parts[1:]);dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():
            with dest.open('xb') as stream:stream.write(data)
    for name,data in overlays.items():
        provenance.append({'commit':EVIDENCE,'path':name,'blob':git('rev-parse',EVIDENCE+':'+name).decode().strip(),'sha256':digest(data),'bytes':len(data)})
    files=[{'path':str(p.relative_to(RECORDS)),'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in sorted(RECORDS.rglob('*.yaml'))]
    value={'format':'swdb.bfs.record-view.v1','created':'2026-09-27','records':str(RECORDS),'git_provenance':provenance,'files':files}
    from scripts.bfs_linux_fixture_audit import write_new
    write_new(DISPATCH/'record-view-manifest.json',value)


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=('prepare','invoke'));p.add_argument('--manifest',type=Path,required=True);p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--proof',type=Path);p.add_argument('--proof-sha256');p.add_argument('--node',type=int,choices=(0,1));p.add_argument('--complete-partial-view',action='store_true')
    args,rest=p.parse_known_args();guard(args.manifest,args.manifest_sha256)
    require(socket.gethostname().split('.')[0]=='mbit10' and sys.platform=='linux','requires mbit10')
    sys.path.insert(0,str(RUNTIME))
    if args.mode=='invoke':
        script=RUNTIME/'scripts/bfs_t17_diagnostic_build.py';sys.argv=[str(script),*rest];runpy.run_path(str(script),run_name='__main__');return
    require(not rest and args.proof is not None and args.proof_sha256 and args.node is not None,'unresolved preparation pins')
    from scripts import bfs_t17_diagnostic_build as diagnostic
    from scripts import bfs_scalar_v2_builds as scalar
    from scripts.bfs_native_campaign import campaign_runtime
    from scripts.bfs_linux_fixture_audit import write_new
    from scripts.bfs_owned_execution import stamp
    runtime=campaign_runtime(COMMIT);prepared=stamp()
    proof={'path':str(args.proof),'sha256':args.proof_sha256}
    scalar.validate_proof(proof,runtime,diagnostic.stamp(prepared),require_storage_case=True)
    diagnostic.load_request();materialize(args.complete_partial_view)
    manifest=reference(DISPATCH/'record-view-manifest.json');diagnostic.validate_record_view(manifest)
    guard(args.manifest,args.manifest_sha256)
    admission={'format':'swdb.bfs.t17-diagnostic-build-admission.v1','id':diagnostic.RUN_ID,'request_sha256':diagnostic.REQUEST_SHA,
      'code_commit':COMMIT,'runtime':runtime,'node':args.node,'prepared_at':stamp(),'record_view':manifest,'linux_proof':proof}
    write_new(DISPATCH/'admission.json',admission)
    print(json.dumps({'admission':reference(DISPATCH/'admission.json'),'record_view':manifest,'records':len(diagnostic.record_inventory()),'runtime':runtime,'node':args.node,'prepared_at':admission['prepared_at']}))


if __name__=='__main__':main()
