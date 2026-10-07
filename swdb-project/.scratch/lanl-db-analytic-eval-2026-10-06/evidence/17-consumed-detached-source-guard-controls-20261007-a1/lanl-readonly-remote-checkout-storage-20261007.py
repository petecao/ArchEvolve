"""Read-only owned LANL checkout allocation and cleanliness metadata."""
import datetime,json,os,pathlib,socket,subprocess
P=pathlib.Path;assert socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==114316761
primary=P('/data1/yanruj/ArchEvolve')
def run(*args):return subprocess.check_output(args,text=True,timeout=60).strip()
rows=[]
for stanza in run('git','-C',str(primary),'worktree','list','--porcelain').split('\n\n'):
 fields={r.split(' ',1)[0]:r.split(' ',1)[1] for r in stanza.splitlines() if ' ' in r}
 p=P(fields['worktree'])
 if p==primary or not str(p).startswith('/data1/yanruj/ArchEvolve-lanl-'):continue
 assert p.is_dir() and not p.is_symlink() and p.stat().st_uid==os.getuid()
 allocated=int(run('du','-sk',str(p)).split()[0])*1024
 ignored=run('git','-C',str(p),'ls-files','--others','--ignored','--exclude-standard','--directory').splitlines()
 untracked=run('git','-C',str(p),'ls-files','--others','--exclude-standard').splitlines()
 rows.append({'path':str(p),'head':fields['HEAD'],'branch':fields.get('branch'),'allocated_bytes':allocated,
  'tracked_dirty':bool(run('git','-C',str(p),'diff','--name-only')) or bool(run('git','-C',str(p),'diff','--cached','--name-only')),
  'untracked_paths':untracked[:100],'untracked_count':len(untracked),'ignored_paths':ignored[:100],'ignored_count':len(ignored)})
assert len(rows)<=40
print(json.dumps({'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'rows':rows,
 'available_bytes':{m:os.statvfs(m).f_bavail*os.statvfs(m).f_frsize for m in ('/data1','/data')},
 'scope':'Read-only own registered checkout allocation/path inventories; no file bodies, cleanup, original source/record/Store/protocol/scientific/auth contents read'}))
