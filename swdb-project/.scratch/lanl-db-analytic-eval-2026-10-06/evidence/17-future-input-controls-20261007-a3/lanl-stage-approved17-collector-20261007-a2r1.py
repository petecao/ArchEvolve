"""Stage one reviewed source atomically; never execute its collector/main."""
import hashlib,json,pathlib,shlex,subprocess
T=pathlib.Path('/private/tmp')
source=T/'lanl17_compact_attempt_custody_a2r1_20261007.py'
approval=T/'lanl17-parent-selected-controls-review-20261007-a2r1s1.json'
output=T/'lanl17-approved-collector-staging-actual-20261007-a2r1.json'
raw=source.read_bytes()
assert len(raw)==24818 and hashlib.sha256(raw).hexdigest()=='b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'
assert hashlib.sha256(approval.read_bytes()).hexdigest()=='8e25b51ea9ded910765af9001f3765e06909609cdf7f2d72551285d142ccc62a'
assert not output.exists() and not output.is_symlink()
remote=r'''
import datetime,hashlib,json,os,pathlib,pwd,socket,sys
P=pathlib.Path
assert sys.platform=='linux' and socket.gethostname()=='mbit10'
assert os.getuid()==os.geteuid()==114316761 and pwd.getpwuid(os.getuid()).pw_name=='yanruj'
parent=P('/data1/yanruj');assert parent.is_dir() and parent.stat().st_uid==os.getuid()
assert all(not p.is_symlink() for p in (parent,*parent.parents))
destination=parent/'lanl17-custody-source-20261007-a2r1'
assert not destination.exists() and not destination.is_symlink()
raw=sys.stdin.buffer.read(24819)
assert len(raw)==24818 and hashlib.sha256(raw).hexdigest()=='b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'
destination.mkdir(mode=0o700)
control=destination/'collector.py'
fd=os.open(control,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as handle:handle.write(raw)
assert control.read_bytes()==raw and control.stat().st_uid==os.getuid() and control.stat().st_mode&0o777==0o600
row={'format':'swdb.lanl17-approved-collector-source-staging.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'host':'mbit10','uid':os.getuid(),'user':'yanruj','collector_path':str(control),'bytes':len(raw),'collector_sha256':hashlib.sha256(raw).hexdigest(),
 'parent_source_review_identity':'3ef7a0d4180c59afc2d10fc69b30745a6a2b3b58657edec47409d5e5e3acf594',
 'parent_source_review_file_sha256':'8e25b51ea9ded910765af9001f3765e06909609cdf7f2d72551285d142ccc62a',
 'collector_imported_or_executed':False,'campaign_or_metadata_dispatched':False,'actual_campaign_inputs_read':False,
 'scientific_source_or_active_controls_modified':False,'authentication_or_environment_contents_read':False,
 'scope':'One fresh own-UID source copy only; actual collector inputs, execution and campaign admission remain separate future gates.'}
row['identity_sha256']=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
encoded=json.dumps(row,indent=2,allow_nan=False)+'\n'
with (destination/'staging.json').open('x') as handle:handle.write(encoded)
sys.stdout.write(encoded)
'''
completed=subprocess.run(['ssh','mbit10','python3 -c '+shlex.quote(remote)],input=raw,capture_output=True,timeout=60)
assert completed.returncode==0,completed.stderr.decode(errors='replace')
row=json.loads(completed.stdout)
assert row['identity_sha256']==hashlib.sha256(json.dumps({k:v for k,v in row.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
assert row['collector_sha256']==hashlib.sha256(raw).hexdigest() and row['collector_imported_or_executed'] is False
with output.open('xb') as handle:handle.write(completed.stdout)
assert source.read_bytes()==raw
print(json.dumps({'actual_staging':str(output),'identity_sha256':row['identity_sha256'],'file_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'collector_path':row['collector_path'],'collector_executed':False}))
