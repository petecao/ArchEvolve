#!/usr/bin/env python3
"""Generate one bounded baseline BFS workload and register real SG identities.

Created: 2026-09-25 (Eastern Time). Run inside an owned mbit10 socket lane.
"""
import argparse
import json
import os
import resource
import re
import signal
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from swdb import artifacts, bfs_protocol, profile
from swdb.store import Store


def widen_sg(source,destination):
    """Widen actual SG counts/CSR offsets; keep vertex IDs and adjacency bytes."""
    source,destination=Path(source),Path(destination)
    with source.open('rb') as inp,destination.open('xb') as out:
        header=inp.read(9)
        if len(header)!=9 or header[0] not in (0,1):
            raise ValueError('invalid SG32 header')
        m,n=struct.unpack('<ii',header[1:])
        if n<=0 or m<0: raise ValueError('invalid SG32 dimensions')
        expected=9+(1+int(header[0]))*((n+1)*4+m*4)
        if source.stat().st_size!=expected: raise ValueError('invalid SG32 byte length')
        out.write(header[:1]+struct.pack('<qq',m,n))
        for _ in range(1+int(header[0])):
            left=n+1
            while left:
                count=min(left,65536)
                values=struct.unpack('<'+'i'*count,inp.read(count*4))
                out.write(struct.pack('<'+'q'*count,*values));left-=count
            left=m*4
            while left:
                block=inp.read(min(left,1024*1024))
                if not block: raise ValueError('truncated SG neighbors')
                out.write(block);left-=len(block)
        if inp.read(1): raise ValueError('trailing SG bytes')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--id',required=True)
    p.add_argument('--family',choices=['kronecker','uniform_random'],required=True)
    p.add_argument('--scale',type=int,choices=[14,16,18,22],required=True)
    sources=p.add_mutually_exclusive_group(required=True)
    sources.add_argument('--sources',type=int,nargs='+')
    sources.add_argument('--artifact-default-source',action='store_true')
    p.add_argument('--runs-dir',type=Path,required=True)
    p.add_argument('--build-dir',type=Path,required=True)
    p.add_argument('--records',type=Path,default=ROOT/'records')
    p.add_argument('--lane',required=True)
    a=p.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*',a.id):
        raise SystemExit('workload ID must use the record identifier syntax')
    if a.sources is not None and any(v<0 or v>=2**a.scale for v in a.sources):
        raise SystemExit('requested source is outside the generated vertex range')
    if socket.gethostname().split('.')[0]!='mbit10':
        raise SystemExit('this measurement driver requires mbit10')
    if a.scale==22 and a.family!='uniform_random':
        raise SystemExit('scale22 is reserved for the prescribed uniform artifact reference')
    store=Store(a.records)
    profile._verified_lane(store.get('mbit10','machine'),a.lane)
    runs=artifacts.external_directory(a.runs_dir)/a.id
    build=artifacts.external_directory(a.build_dir)/a.id
    if Path('/data1/yanruj') not in build.parents: raise SystemExit('build directory must be under /data1/yanruj')
    if not any(base in runs.parents for base in [Path('/data1/yanruj'),Path('/data/yanruj')]):
        raise SystemExit('raw output must use the authorized host volumes')
    runs.mkdir(exist_ok=False);build.mkdir(exist_ok=False)
    def interrupted(signum,_frame):
        raise InterruptedError(f'workload preparation interrupted by signal {signum}')
    for sig in (signal.SIGTERM,signal.SIGINT,signal.SIGHUP):
        signal.signal(sig,interrupted)
    receipt={'id':a.id,'state':'running','family':a.family,'scale':a.scale,'edge_factor':16,
             'sources':a.sources,'lane':a.lane,'stages':[],
             'bounds':{'compile_s':180,'generate_s':900,'register_s':2400,'address_space_gib':48,'threads':4}}
    def save(): (runs/'driver.json').write_text(json.dumps(receipt,indent=2))
    def bounded(stage,argv,seconds):
        profile._verified_lane(store.get('mbit10','machine'),a.lane)
        before=time.monotonic();out=runs/(stage+'.stdout');err=runs/(stage+'.stderr')
        def limit(): resource.setrlimit(resource.RLIMIT_AS,(48*1024**3,48*1024**3))
        entry={'stage':stage,'argv':list(map(str,argv)),'timeout_s':seconds,'state':'running'}
        receipt['stages'].append(entry);save()
        with out.open('w') as stdout,err.open('w') as stderr:
            child=subprocess.Popen(list(map(str,argv)),cwd=ROOT,stdout=stdout,stderr=stderr,
                env={**os.environ,'OMP_NUM_THREADS':'4'},start_new_session=True,preexec_fn=limit)
            try: child.wait(timeout=seconds)
            except BaseException:
                try: os.killpg(child.pid,signal.SIGKILL)
                except ProcessLookupError: pass
                child.wait();entry.update(state='interrupted_or_timeout',host_wall_s=time.monotonic()-before);save();raise
        entry.update(state='complete' if child.returncode==0 else 'failed',returncode=child.returncode,
                     host_wall_s=time.monotonic()-before,stdout_sha256=artifacts.file_hash(out),stderr_sha256=artifacts.file_hash(err));save()
        if child.returncode: raise RuntimeError(f'{stage} exited {child.returncode}; retained {err}')
        return out
    save()
    try:
        source=ROOT/'apps/dx100/benchmarks/gapbs/src'
        receipt['generator_source_sha256']=artifacts.identify(source)['sha256']
        receipt['repository_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        compiler='g++';binary=build/'converter'
        bounded('compile',[compiler,'-std=c++11','-O3','-fopenmp',source/'converter.cc','-o',binary],180)
        sg32=runs/'graph.sg32';sg64=runs/'graph.sg64'
        generator_command=[str(binary),'-u' if a.family=='uniform_random' else '-g',str(a.scale),'-k','16','-b',str(sg32)]
        bounded('generate',generator_command,900)
        widen_sg(sg32,sg64)
        if a.artifact_default_source:
            picker_source=build/'pick-source.cc'
            picker_source.write_text('#include "benchmark.h"\n#include "command_line.h"\n'
                'int main(int argc,char** argv){CLBase cli(argc,argv,"source-picker");cli.ParseArgs();'
                'Builder builder(cli);Graph g=builder.MakeGraph();SourcePicker<Graph> picker(g);'
                'std::cout<<"SWDB_SOURCE "<<picker.PickNext()<<"\\n";}\n')
            picker=build/'pick-source'
            bounded('compile-source-picker',[compiler,'-std=c++11','-O3','-fopenmp',
                    '-I'+str(source),picker_source,'-o',picker],180)
            output=bounded('pick-source',[picker,'-f',sg32],300)
            selected=[line.split()[1] for line in output.read_text().splitlines() if line.startswith('SWDB_SOURCE ')]
            if len(selected)!=1: raise RuntimeError('actual artifact SourcePicker did not return one source')
            a.sources=[int(selected[0])]
            receipt.update(sources=a.sources,source_selection='pinned_artifact_SourcePicker_first_nonzero_degree',
                           source_picker_sha256=artifacts.file_hash(picker_source))
        representations=[{'id':a.id+'.'+name,'application':app,'path':str(path),'format':fmt,'sha256':artifacts.file_hash(path)}
            for name,app,path,fmt in [('dx100','dx100-gapbs',sg32,'gapbs_sg32le'),('upstream','gapbs',sg64,'gapbs_sg64le')]]
        request={'message_version':'1.0','id':a.id,'kernel':'gapbs-bfs','family':a.family,
            'generator':{'name':'DX100 GAPBS converter','revision':'e4fc4afdf894f295442cef3604667a469fab8e62',
                'command':generator_command,
                # CLBase::ParseArgs enables this for both synthetic families,
                # including commands that do not explicitly request -s.
                'parameters':{'scale':a.scale,'edge_factor':16,'seed':27491095,'symmetrize':True,
                    'explicit_symmetrize_flag':False,
                    'binary_sha256':artifacts.file_hash(binary),'source_sha256':receipt['generator_source_sha256']}},
            'sources':a.sources,'normalization':bfs_protocol.NORMALIZATION,'representations':representations,
            'parser':{'work_dir':str(build),'compile_timeout_s':60,'timeout_s':900}}
        path=runs/'register.json';path.write_text(json.dumps(request,indent=2))
        output=bounded('register',[sys.executable,'-m','swdb','register-workload',path,'--records',a.records,'--format','json'],2400)
        registered=json.loads(output.read_text());receipt.update(state='complete',workload=registered['id'],
            canonical_sha256=registered['definition']['canonical_sha256'],realized=registered['definition']['realized'])
    except BaseException as exc:
        receipt.update(state='failed',reason=f'{type(exc).__name__}: {exc}');save();raise
    save();print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
