"""Recover only integrated, pushed export checkouts; read-only without --remove."""
import argparse,datetime,hashlib,json,os,pathlib,subprocess
P=pathlib.Path;root=P('/data1/yanruj');repo=root/'ArchEvolve'
source=root/'ArchEvolve-lanl-cpu-model-validation-20261006-a1'
ROWS=[
 ('ArchEvolve-lanl-count-evidence-20261006','codex/lanl-bound-estimate-evidence','68df1ddbab971ca6cb51f66ae74ae2f4cb62acca'),
 ('ArchEvolve-lanl-cpu-t1-evidence-20261006','codex/lanl-cpu-t1-count-evidence','a15d9eade7d90e210fd4a37f30bbab9ab6612d72'),
 ('ArchEvolve-lanl-functional-count-evidence-20261006-a2','codex/lanl-functional-object-count-evidence-a2','c01c0e5645f87718128b4605261d0cb4dabcd84a'),
 ('ArchEvolve-lanl-functional-evidence-20261006','codex/lanl-functional-bfs-evidence','31b4de8a81fe4ade8e497565903bce14b2c475b8'),
 ('ArchEvolve-lanl-openmp-projection-evidence-20261006-a1','codex/lanl-openmp-projection-evidence-a1','538adc376f945eee9741da1dc1806cb5e22f37b5'),
 ('ArchEvolve-lanl-prospective-input-evidence-20261006-a2','codex/lanl-prospective-input-evidence-a2','490abaf96eb564b8f5b58ecf2beb1f615e523a27'),
 ('ArchEvolve-lanl-root-projection-evidence-20261006','codex/lanl-root-projection-evidence','a5d983ac09fbc5b36babc4989d83ca4b87fe7e6a'),
 ('ArchEvolve-lanl-service-evidence-20261006','codex/lanl-byte-read-service-evidence','294c2d340bdc38c52c5234e0b3689a3a8b60ad2a')]
def git(path,*args):return subprocess.check_output(['git','-C',str(path),*args],text=True,timeout=120).strip()
def free():
 st=os.statvfs('/data1');return st.f_bavail*st.f_frsize
def inside(target,path):return target==str(path) or target.startswith(str(path)+'/')
def source_guard():
 assert git(source,'rev-parse','HEAD')=='f893fed400347ed23d92e917d8bde21b75e5375d'
 assert not git(source,'status','--porcelain')
def all_free():
 for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation'):
  assert json.loads((root/'lact-host-lease'/(name+'.meta.json')).read_text())['state']=='released'
def referenced_metadata(paths):
 patterns=[str(p).encode() for p in paths];hits=[]
 for base in (repo/'swdb-project/records',repo/'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence'):
  for file in base.rglob('*'):
   if not file.is_file() or file.suffix not in ('.json','.yaml','.md','.py'):continue
   tail=b''
   with file.open('rb') as stream:
    for chunk in iter(lambda:stream.read(1024*1024),b''):
     data=tail+chunk
     if any(v in data for v in patterns):hits.append(str(file));break
     tail=data[-256:]
 return hits
def main():
 args=argparse.ArgumentParser(description=__doc__);args.add_argument('--remove',action='store_true');args=args.parse_args()
 assert os.uname().nodename.split('.')[0]=='mbit10' and os.getuid()!=0
 all_free();source_guard()
 paths=[root/name for name,_,_ in ROWS]
 facts=[]
 for name,branch,commit in ROWS:
  p=root/name;assert p.is_dir() and not p.is_symlink()
  assert git(p,'rev-parse','HEAD')==commit and git(p,'branch','--show-current')==branch and not git(p,'status','--porcelain')
  assert git(repo,'rev-parse','refs/heads/'+branch)==git(repo,'rev-parse','origin/'+branch)==commit
  subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor',commit,'origin/yanrujhou_main'],check=True,timeout=120)
  ignored=git(p,'ls-files','--others','--ignored','--exclude-standard').splitlines()
  assert all('__pycache__/' in f and f.endswith('.pyc') or f.startswith('swdb-project/.pytest_cache/') or f in ('swdb-project/build/swdb.sqlite','swdb-project/records/.swdb.lock') for f in ignored),(str(p),ignored)
  facts.append({'path':str(p),'branch':branch,'commit':commit,'ignored_disposable_files':ignored})
 assert not referenced_metadata(paths),'Current authoritative/evidence metadata references an export checkout'
 checked=0
 for proc in P('/proc').glob('[0-9]*'):
  refs=[proc/'cwd']
  try:refs+=list((proc/'fd').iterdir())
  except (FileNotFoundError,PermissionError):pass
  for ref in refs:
   try:target=os.readlink(ref)
   except OSError:continue
   assert not any(inside(target,p) for p in paths),'An active process uses an export checkout'
   checked+=1
 links=0
 for run in P('/data/yanruj/EvolveSWDB_runs').iterdir():
  if not run.name.startswith(('lanl-','lanl17-')):continue
  for folder,dirs,files in os.walk(run,followlinks=False):
   for name in dirs+files:
    ref=P(folder)/name
    if not ref.is_symlink():continue
    resolved=str(ref.resolve());assert not any(inside(resolved,p) for p in paths),'Raw evidence references an export checkout'
    links+=1
 before=free();all_free();source_guard()
 if args.remove:
  for name,branch,commit in ROWS:
   all_free();git(repo,'worktree','remove',str(root/name));assert not (root/name).exists()
   assert git(repo,'rev-parse','refs/heads/'+branch)==git(repo,'rev-parse','origin/'+branch)==commit
 source_guard()
 print(json.dumps({'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Only eight exact, clean, pushed, origin-main ancestor exports; Git branches, every raw and execution checkout retained. Unintegrated failure export retained.','removed':args.remove,'exports':facts,'current_metadata_references':0,'process_references_checked':checked,'raw_links_checked':links,'free_before_bytes':before,'free_after_bytes':free(),'recovered_bytes':free()-before,'source_C_preserved':True}))
if __name__=='__main__':main()
