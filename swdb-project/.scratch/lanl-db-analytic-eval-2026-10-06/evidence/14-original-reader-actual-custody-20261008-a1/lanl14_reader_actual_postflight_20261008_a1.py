"""Parent read-only original compact custody transfer and separate postflight."""
import base64,datetime,hashlib,json,os,pathlib,stat,subprocess,time,types
P=pathlib.Path
UID=114316761
PRIMARY=P('/data1/yanruj/ArchEvolve')
C=P('/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1')
E=P('/data1/yanruj/ArchEvolve-lanl-generality-final-export-20261007-a1')
EV=P('swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence')
H=PRIMARY/EV/'14-completed-report-transfer-mode-controls-20261008-a1/lanl14_correct_completed_report_transfer_modes_20261008_a1.py'
ADMIN=P('/data/yanruj/EvolveSWDB_runs/lanl14-export-reader-administration-20261007-a1')
CTL=ADMIN/'lanl14-export-reader-control-reader-a1'
def require(v,s):
 if not v:raise RuntimeError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
require(os.getuid()==os.geteuid()==UID and os.uname().machine=='x86_64','account')
hb=H.read_bytes();require(len(hb)==29985 and sha(hb)=='ee12a535ea2c3e6976c920f483c72e8367cd36ec311bf26585137023a2d29ec7','original read-only source pin')
h=types.ModuleType('parent_read_only_postflight');h.__file__=str(H)
exec(compile(hb,str(H),'exec'),h.__dict__)
require(h.__name__!='__main__','no selected main')
b=h.Budget(600)
def original(p):
 p=h.checked(p);s=p.lstat()
 if s.st_size:
  pin,raw=h.read_file(p,1024*1024,b,retain=True)
 else:
  fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
  try:
   raw=os.read(fd,1)
   require(raw==b'' and h.stamp(os.fstat(fd))==h.stamp(s)==h.stamp(p.lstat()),'stable empty original')
  finally:os.close(fd)
  pin={'path':str(p),'bytes':0,'sha256':sha(raw),'stat':h.stamp(s)}
 return {'pin':pin,'base64':base64.b64encode(raw).decode(),'unmodified_original':True}
originals={n:original(p) for n,p in {'remote-reader-preregistration.json':ADMIN/'reader-invocation-preregistration-a1.json','remote-reader-receipt.json':CTL/'receipt.json','remote-reader-cleanup.json':CTL/'cleanup.json','remote-reader-stdout.json':CTL/'stdout','remote-reader-stderr':CTL/'stderr'}.items()}
parsed={k:json.loads(base64.b64decode(v['base64'])) for k,v in originals.items() if k.endswith('.json')}
pr=parsed['remote-reader-preregistration.json'];rc=parsed['remote-reader-receipt.json'];cu=parsed['remote-reader-cleanup.json'];ad=parsed['remote-reader-stdout.json']
require(pr['expected_primary']=='a9c02e918374070ff2654e3f9696bd550230cbbb','primary prereg')
current_source_pins={path:h.read_file(path,8*1024*1024,b,pin['sha256'])[0] for path,pin in pr['source_pins'].items()}
require(current_source_pins==pr['source_pins'],'sources unchanged')
native=h.native(b)
native['/usr/bin/timeout']=h.read_file('/usr/bin/timeout',128*1024*1024,b,'12690a043dfd555a6c14ccc1564f5649c18f1762c0d6ff66729948130898ec52',False,0)[0]
require(native==pr['native'],'native unchanged')
def git(root,*args):
 b.check();r=subprocess.run(['/usr/bin/git','-C',str(root),*args],capture_output=True,timeout=min(60,max(.001,b.deadline-time.monotonic())),env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0'},check=False)
 require(r.returncode==0 and len(r.stdout)<=4*1024*1024,'read-only git');return r.stdout.decode().strip()
refs={str(root):{'head':git(root,'rev-parse','HEAD'),'branch':git(root,'branch','--show-current'),'status':git(root,'status','--porcelain','--untracked-files=all')} for root in (PRIMARY,C,E)}
require(refs[str(PRIMARY)]=={'head':pr['expected_primary'],'branch':'yanrujhou_main','status':'?? swdb-project/records/.retention.lock'} and git(PRIMARY,'rev-parse','origin/yanrujhou_main')==pr['expected_primary'],'primary unchanged')
require(refs[str(C)]['head']=='f893fed400347ed23d92e917d8bde21b75e5375d' and refs[str(C)]['status']=='','C unchanged')
require(refs[str(E)]['head']==pr['export_commit'] and refs[str(E)]['status']=='' and git(E,'rev-list','--parents','-n','1',pr['export_commit']).split()==[pr['export_commit'],pr['source_commit']],'pure E unchanged')
lock=PRIMARY/'swdb-project/records/.retention.lock'
require(list((getattr(lock.lstat(),n) for n in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns')))==pr['retention_original_stat'],'retention unchanged')
R14=h.source_identity(b);require(R14==pr['R14_source_identity'],'R14 unchanged')
leases=h.released(b);require(leases==pr['released_leases'],'all leases released unchanged')
modules={}
for root in (C,E):
 files=sorted((root/'swdb-project/swdb').rglob('*.py'))
 values={p.relative_to(root/'swdb-project/swdb').as_posix():h.read_file(p,8*1024*1024,b)[0]['sha256'] for p in files}
 require(len(values)==185 and h.true_digest(values)==pr['F6'],'same F6')
 modules[str(root)]={'modules':len(values),'identity_sha256':h.true_digest(values)}
for pin in [pr['actual_export_receipt'],pr['report_transfer_file_pin'],pr['count_receipt_file_pin'],*pr['new_canonical_byte_pins'].values()]:require(h.read_file(pin['path'],100*1024*1024,b,pin['sha256'])[0]==pin,'original selected file unchanged')
active=[];visibility_errors=[]
needles=[b'lanl14_readonly_nine_export_admission_lossless_gzip_20261007_a1.py',b'lanl14_export_reader_administrative_supervisor_20261007_a1_r1.py']
for p in P('/proc').iterdir():
 if not p.name.isdigit() or int(p.name)==os.getpid():continue
 try:
  if p.stat().st_uid!=UID:continue
  cmd=(p/'cmdline').read_bytes()
  if any(n in cmd for n in needles):
   fields=(p/'stat').read_text().rsplit(')',1)[1].split()
   active.append({'pid':int(p.name),'state':fields[0],'start_ticks':int(fields[19])})
 except (FileNotFoundError,ProcessLookupError):pass
 except PermissionError:visibility_errors.append(int(p.name))
require(not active and not visibility_errors,'selected owned processes stopped and visible')
result={'format':'swdb.lanl14-parent-original-reader-postflight-transfer.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originals':originals,'postflight':{'all_checks_passed':True,'refs':refs,'source_pins_unchanged':True,'native_pins_unchanged':True,'all_selected_original_file_pins_unchanged':True,'retention_stat_unchanged':True,'R14_source_identity':R14,'modules':modules,'released_leases':leases,'selected_owned_processes':active,'visibility_errors':visibility_errors,'capacity_bytes':{m:os.statvfs(m).f_bavail*os.statvfs(m).f_frsize for m in ('/data1','/data')},'memory_available_bytes':int(next(x.split()[1] for x in P('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024,'load':os.getloadavg()},'scientific_admission_not_inferred_from_exit':True,'no_raw_scientific_body_transferred':True}
print(json.dumps(result,sort_keys=True))
