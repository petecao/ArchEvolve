from pathlib import Path
import os,stat,json,subprocess,hashlib,datetime
P=Path;source=P('/data1/yanruj/ArchEvolve-lanl17-source-20261007-a4');primary=P('/data1/yanruj/ArchEvolve');R='5e12a9796432654d88def24ecea617d16ca605b2';uid=os.getuid();control=P('/data1/yanruj/lanl17-failed-prepare-source-recovery-20261008-a1');assert not control.exists();control.mkdir(mode=0o700);os.umask(0o077)
assert source.resolve()==source and source.is_dir() and not source.is_symlink() and source.stat().st_uid==uid
assert hashlib.sha256(P('/usr/bin/git').read_bytes()).hexdigest()=='06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'
def git(p,*args):
 r=subprocess.run(['/usr/bin/git','--no-replace-objects','--no-optional-locks','-c','core.hooksPath=/dev/null','-C',str(p),*args],capture_output=True,timeout=90);assert r.returncode==0,(r.returncode,r.stderr[:512]);return r.stdout.decode()
assert git(source,'rev-parse','HEAD').strip()==R and git(primary,'rev-parse','HEAD').strip()==R
assert git(primary,'rev-parse','origin/yanrujhou_main').strip()==R
assert git(source,'status','--porcelain','--untracked-files=all')==''
assert git(source,'ls-files','--others','--ignored','--exclude-standard')==''
assert git(source,'diff','--name-only')==git(source,'diff','--cached','--name-only')==''
assert not P('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a4').exists()
assert not P('/data1/yanruj/lanl17-dx100-deployment-20261008-a1/dx100-binding-original.json').exists()
refs=[]
for p in P('/proc').iterdir():
 if p.name.isdigit():
  try:
   if p.stat().st_uid==uid and str(source).encode() in (p/'cmdline').read_bytes():refs.append(int(p.name))
  except OSError:pass
assert not refs
fields=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns');stamp=lambda s:{k:getattr(s,'st_'+k) for k in fields}
rows=git(source,'ls-tree','-r','--full-tree','HEAD');tree=git(source,'rev-parse','HEAD^{tree}').strip();gitfile=(source/'.git').read_bytes()
free=lambda:os.statvfs('/data1').f_bavail*os.statvfs('/data1').f_frsize
before={'format':'swdb.lanl17-failed-clean-source-recovery.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(source),'source_original_stat':stamp(source.lstat()),'recoverable_commit':R,'recoverable_tree':tree,'tracked_tree_bytes':len(rows.encode()),'tracked_tree_sha256':hashlib.sha256(rows.encode()).hexdigest(),'original_gitfile_base64':__import__('base64').b64encode(gitfile).decode(),'ignored_untracked_index_worktree_changes':[],'source_consumers':refs,'raw_and_binding_receipt_absent':True,'original_failed_control_retained':'/data/yanruj/EvolveSWDB_runs/lanl17-metadata-prepare-20261007-a4','data1_free_before':free()}
(control/'tracked-tree-original.txt').write_text(rows);(control/'before-original.json').write_text(json.dumps(before,sort_keys=True,indent=2)+'\n')
git(primary,'worktree','remove',str(source))
assert not source.exists() and git(primary,'rev-parse',R+'^{tree}').strip()==tree
out={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_removed':True,'source_path':str(source),'recoverable_commit':R,'recoverable_tree':tree,'data1_free_after':free(),'before_original_sha256':hashlib.sha256((control/'before-original.json').read_bytes()).hexdigest(),'raw_original_target_failed_control_and_shared_primary_retained':True,'no_scientific_or_capacity_admission':True};(control/'after-original.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n');print(json.dumps(out,sort_keys=True))
