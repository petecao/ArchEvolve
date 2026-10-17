"""2026-10-16 ET. Passive exact Python roots/link/startup metadata; no package import."""
from pathlib import Path
import datetime,hashlib,json,os,stat,time
H=lambda b:hashlib.sha256(b).hexdigest()
D=lambda v:H(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def pin(p):
 p=Path(p);a=p.stat()
 with p.open('rb')as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
 b=p.stat()
 if(a.st_ino,a.st_mtime_ns,a.st_size)!=(b.st_ino,b.st_mtime_ns,b.st_size):raise ValueError('unstable physical file')
 return {'path':str(p),'bytes':a.st_size,'sha256':sha}
def inventory(root):
 root=Path(root)
 if root.is_symlink()or not root.is_dir():raise ValueError('nonregular root')
 entries=[]
 for p in sorted(root.rglob('*')):
  row={'relative':str(p.relative_to(root))};mode=p.lstat().st_mode
  if stat.S_ISLNK(mode):row.update(kind='symlink',target=os.readlink(p),resolved=str(p.resolve(strict=True)))
  elif stat.S_ISREG(mode):row.update(kind='file',**{k:v for k,v in pin(p).items()if k!='path'})
  elif stat.S_ISDIR(mode):row.update(kind='directory')
  else:raise ValueError('special input')
  entries.append(row)
 return entries

def summary(root,entries):
 return {'path':str(root),'counts':{'entries':len(entries),'files':sum(r['kind']=='file'for r in entries),'directories':sum(r['kind']=='directory'for r in entries),'symlinks':sum(r['kind']=='symlink'for r in entries)},'total_bytes':sum(r.get('bytes',0)for r in entries),'inventory_sha256':D(entries)}
def chain(p):
 p=Path(p);seen=set();rows=[]
 while p.is_symlink():
  normalized=os.path.normpath(str(p))
  if normalized in seen:raise ValueError('cycle')
  seen.add(normalized);target=os.readlink(p);rows.append({'path':normalized,'target':target});p=Path(os.path.normpath(str(p.parent/target)))if not Path(target).is_absolute()else Path(target)
 return rows

def main():
 started=time.monotonic();root_paths=['/usr/lib/python3.12','/data1/yanruj/venvs/swdb-test/lib/python3.12/site-packages','/usr/local/lib/python3.12/dist-packages','/usr/lib/python3/dist-packages'];surfaces={};full={};target_inventories={}
 for root in root_paths:
  entries=inventory(root);row=summary(root,entries);links={}
  for entry in entries:
   if entry['kind']!='symlink':continue
   p=Path(root)/entry['relative'];target=p.resolve(strict=True);metadata={'target':entry['target'],'resolved':str(target),'target_kind':'directory'if target.is_dir()else'file','chain':chain(p)}
   if target.is_file():metadata.update({k:v for k,v in pin(target).items()if k!='path'})
   else:
    target_entries=inventory(target)
    if any(r['kind']=='symlink'for r in target_entries):raise ValueError('new nested target symlink requires explicit separate review')
    target_inventories[str(target)]=target_entries;target_summary=summary(target,target_entries);metadata.update(target_inventory_sha256=target_summary['inventory_sha256'],target_counts=target_summary['counts'],target_total_bytes=target_summary['total_bytes'])
   links[entry['relative']]=metadata
  row['symlinks']=links;surfaces[root]=row;full[root]=entries
 startup_paths=['/usr/lib/python3.12/site.py','/etc/python3.12/sitecustomize.py','/data1/yanruj/venvs/swdb-test/pyvenv.cfg','/usr/lib/python3/dist-packages/distutils-precedence.pth','/usr/lib/python3/dist-packages/_distutils_hack/__init__.py','/usr/lib/python3/dist-packages/_distutils_hack/override.py','/usr/lib/python3/dist-packages/apport_python_hook.py']
 startup=[pin(p)for p in startup_paths]
 interpreter='/data1/yanruj/venvs/swdb-test/bin/python';interpreter_binding={'path':interpreter,'chain':chain(interpreter),'resolved':str(Path(interpreter).resolve(strict=True)),'target_pin':pin(Path(interpreter).resolve(strict=True))}
 pth=[]
 for root in root_paths:
  for p in sorted(Path(root).glob('*.pth')):pth.append({**pin(p),'lines_sha256':D(p.read_text().splitlines())})
 # A complete second membership pass detects concurrent addition/deletion/type/link changes.
 for root in root_paths:
  rows=inventory(root)
  if rows!=full[root]:raise ValueError('root changed during passive capture: '+root)
 for root,expected in target_inventories.items():
  if inventory(root)!=expected:raise ValueError('target changed during passive capture')
 return {'created':'2026-10-16 ET','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'schema':'closed-python-surface-metadata-1','canonical_json':{'sort_keys':True,'separators':[',',':'],'allow_nan':False,'encoding':'UTF-8'},'scope':'Fresh passive physical hashes and exact complete membership, no interpreter/package/native/version/compiler/solver execution; guarded actual sys.path/startup semantics remain pending.','surfaces':surfaces,'startup_pins':startup,'pth':pth,'interpreter':interpreter_binding,'root_inventories':full,'target_inventories':target_inventories,'before_after_full_inventory_equal':True,'actual_sys_path_observed':False,'candidate_expected_sys_path':['/usr/lib/python312.zip','/usr/lib/python3.12','/usr/lib/python3.12/lib-dynload','/data1/yanruj/venvs/swdb-test/lib/python3.12/site-packages','/usr/local/lib/python3.12/dist-packages','/usr/lib/python3/dist-packages'],'absence':{p:not Path(p).exists()for p in ['/usr/lib/python312.zip','/usr/local/lib/python312.zip','/data1/yanruj/venvs/swdb-test/lib/python312.zip']},'wall_seconds':time.monotonic()-started}
if __name__=='__main__':print(json.dumps(main(),sort_keys=True,indent=2))
