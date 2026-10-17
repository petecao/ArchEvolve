import pathlib,os,stat,json,hashlib,base64,subprocess,datetime
P=pathlib.Path;control=P('/data/yanruj/EvolveSWDB_runs/lanl17-metadata-prepare-20261007-a4');source=P('/data1/yanruj/ArchEvolve-lanl17-source-20261007-a4');uid=os.getuid()
fields=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
stamp=lambda s:{k:getattr(s,'st_'+k) for k in fields}
rows=[]
for name in ('preregistration.json','supervisor-receipt.json','helper.stdout','helper.stderr'):
 p=control/name;s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==uid and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and s.st_size<=16384
 with p.open('rb') as f:
  assert stamp(os.fstat(f.fileno()))==stamp(s);b=f.read(16385);assert len(b)==s.st_size and stamp(os.fstat(f.fileno()))==stamp(s)==stamp(p.lstat())
 rows.append({'name':name,'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'stat':stamp(s),'body_base64':base64.b64encode(b).decode()})
def git(*args):
 r=subprocess.run(['/usr/bin/git','--no-replace-objects','--no-optional-locks','-c','core.hooksPath=/dev/null','-C',str(source),*args],capture_output=True,timeout=10);assert r.returncode==0;return r.stdout.decode()
refs=[]
for p in P('/proc').iterdir():
 if p.name.isdigit():
  try:
   if p.stat().st_uid!=uid:continue
   b=(p/'cmdline').read_bytes()
   if str(source).encode() in b:refs.append({'pid':int(p.name),'comm':(p/'comm').read_text().strip()})
  except (OSError,PermissionError):pass
out={'format':'swdb.lanl17-failed-prepare-original-capture.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originals':rows,'source_state':{'exists':source.exists(),'identity':stamp(source.lstat()),'HEAD':git('rev-parse','HEAD').strip(),'status':git('status','--porcelain','--untracked-files=all'),'dx100_is_symlink':(source/'swdb-project/apps/dx100').is_symlink(),'dx100_is_directory':(source/'swdb-project/apps/dx100').is_dir()},'source_commandline_references':refs,'raw_exists':P('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a4').exists(),'binding_receipt_exists':P('/data1/yanruj/lanl17-dx100-deployment-20261008-a1/dx100-binding-original.json').exists(),'no_action_or_completion_admission':True}
print(json.dumps(out,sort_keys=True))
