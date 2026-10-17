"""Parent source-only staging from delivered Git; never import/execute controls."""
import hashlib,json,pathlib,shlex,subprocess
P=pathlib.Path
output=P('/private/tmp/lanl17-reviewed-input-controls-staging-actual-20261007-a3.json')
assert not output.exists() and not output.is_symlink()
for path,digest in [('/private/tmp/lanl17-parent-source-preparation-review-20261007-a3.json','3cd7b458c037e3f974e44cf8625c7aed9172ca708c455f724d49e9e384d00989'),('/private/tmp/lanl17-parent-selected-controls-review-20261007-a2r1s1.json','8e25b51ea9ded910765af9001f3765e06909609cdf7f2d72551285d142ccc62a')]:
    assert hashlib.sha256(P(path).read_bytes()).hexdigest()==digest
remote=r'''
import datetime,hashlib,json,os,pathlib,pwd,socket,subprocess,sys
P=pathlib.Path
assert sys.platform=='linux' and socket.gethostname()=='mbit10'
assert os.getuid()==os.geteuid()==114316761 and pwd.getpwuid(os.getuid()).pw_name=='yanruj'
base=P('/data1/yanruj');repo=base/'ArchEvolve';revision='5485322bf1867f31c20714666be6eec763778f6a'
assert base.is_dir() and base.stat().st_uid==os.getuid() and all(not p.is_symlink() for p in (base,*base.parents))
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args],timeout=60)
assert git('rev-parse','HEAD').decode().strip()==revision and git('branch','--show-current').decode().strip()=='yanrujhou_main'
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
folder='swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/'
entries=[
 ('assembler.py',folder+'17-future-input-controls-20261007-a3/lanl17_assemble_selected_actual_input_pins_r1_20261007.py',33584,'de669e4c0928876f9d033f6d9c1fc820ab3a1eb915aba20c5b6755b9866d7e6a'),
 ('spec-writer.py',folder+'17-future-input-controls-20261007-a3/lanl17_write_parent_input_specification_20261007.py',11868,'339ea0dc1abb6778f0f016e9c03f2b29c5f1916154b668f5416747b2768a9231'),
 ('capture-producer.py',folder+'17-future-input-controls-20261007-a3/lanl17_parent_capture_projection_producer_a3_20261007.py',46165,'32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6'),
 ('auditor.py',folder+'17-selected-trajectory-controls-20261007-a2r1s1/lanl17_selected_record_trajectory_auditor_a2r1s1_20261007.py',115130,'6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da')]
sources=[]
for name,path,size,digest in entries:
 raw=git('show',revision+':'+path);assert len(raw)==size and hashlib.sha256(raw).hexdigest()==digest
 sources.append((name,path,raw,digest))
destination=base/'lanl17-custody-source-20261007-a3'
assert not destination.exists() and not destination.is_symlink()
destination.mkdir(mode=0o700);rows=[]
for name,origin,raw,digest in sources:
 target=destination/name;fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as stream:stream.write(raw)
 assert target.read_bytes()==raw and target.stat().st_uid==os.getuid() and target.stat().st_mode&0o777==0o600
 rows.append({'path':str(target),'origin_git_path':origin,'bytes':len(raw),'sha256':digest,'mode':'0600','source_imported_or_executed':False})
assert destination.stat().st_mode&0o777==0o700 and git('rev-parse','HEAD').decode().strip()==revision
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
row={'format':'swdb.lanl17-reviewed-input-controls-source-staging.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonical_ensure_ascii':True,
     'host':'mbit10','uid':os.getuid(),'user':'yanruj','source_git_revision':revision,'source_git_branch':'yanrujhou_main','destination':str(destination),'directory_mode':'0700','controls':rows,
     'parent_preparation_review_identity':'be67a38960c5086d8a8b5534b3a571bbed0f56772e4d64d4fb27a58bc3ab6ccc','parent_auditor_review_identity':'3ef7a0d4180c59afc2d10fc69b30745a6a2b3b58657edec47409d5e5e3acf594',
     'archive_manifest_identity':'b910436fe5e7191889fa43f329d1d4faaafb1173d42f6238b564b278bb25f715','selected_control_execution':False,'actual_inputs_templates_requests_constructed_or_read':False,'Store_campaign_native_provider_execution':False,'scientific_admission':False,'authentication_or_environment_contents_read':False,
     'scope':'Fresh owned source-only copies from delivered exact Git blobs. Existing b08 collector stage, every prior source/receipt and active evaluation source remain untouched. Actual requests and inputs require separate review.'}
row['identity_sha256']=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
encoded=(json.dumps(row,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
fd=os.open(destination/'staging.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as stream:stream.write(encoded)
sys.stdout.buffer.write(encoded)
'''
r=subprocess.run(['ssh','mbit10','python3 -c '+shlex.quote(remote)],capture_output=True,timeout=60,check=False)
assert r.returncode==0,r.stderr.decode(errors='replace')
row=json.loads(r.stdout)
assert row['identity_sha256']==hashlib.sha256(json.dumps({k:v for k,v in row.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()
assert row['selected_control_execution'] is False and len(row['controls'])==4
with output.open('xb') as stream:stream.write(r.stdout)
print(json.dumps({'path':str(output),'bytes':len(r.stdout),'sha256':hashlib.sha256(r.stdout).hexdigest(),'identity_sha256':row['identity_sha256'],'selected_control_execution':False}))
