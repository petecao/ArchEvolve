import argparse,pathlib,os,stat,hashlib,json,subprocess,datetime,re
P=pathlib.Path;BASE=P('/data1/yanruj');PRIMARY=BASE/'ArchEvolve';C=BASE/'ArchEvolve-lanl-cpu-model-validation-20261006-a1';UID=114316761
REL=P('swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-detached-E-inspection-failure-and-source-custody-20261008-a1')
DEST=BASE/'lanl-storage-admin-selected-source-20261008-a2'
EXPECTED={
 'lanl14_remove_consumed_export_checkout_20261008_a1_r3.py':(26370,'7f92b6f85f4e0c574f3ade7a806c2d6de02108fb8f32579f2e37343e9dc566f9'),
 'lanl14_detach_exact_E_cleanup_administration_20261008_a1_r3.py':(18369,'a04486d04c8f3a5f0ceee1d6ff58aeeacdb5aa2f4a9dec9e6befa8f40056cfaf'),
 'lanl_consumed_detached_source_guard_r4_20261008_r3.py':(88521,'96e033426d492fab3be2a07757ab1e89665a7a67d0f06d3941f274b1214dd294'),
 'lanl17_acquire_passive_consumed_source_metadata_20261008_a1_r4.py':(58634,'1c5a39575e66bb1deea654a586e11a4f9c7437e06547144bdb0347375e1542cf'),
 'lanl17_detach_exact_R4_storage_administration_20261008_a1_r3.py':(24000,'3f5cc9397c9be47232f0c070ca70def25c55a3c69af404af257da992ad105e01'),
 'lanl17_detach_passive_observer_administration_20261008_a1_r3.py':(15359,'f26a2f7790ccf5df117acf19496e7510be778deb44892b4d54b15245efa317b2')}
def sha(b):return hashlib.sha256(b).hexdigest()
def stamp(s):return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}
def private(p):
 s=p.lstat();assert p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)) and stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700
def checkout_identity(p):
 private(BASE)
 assert p in (PRIMARY,C) and p.parent==BASE and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents))
 s=p.lstat();assert stat.S_ISDIR(s.st_mode) and s.st_uid==UID
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:opened=os.fstat(fd)
 finally:os.close(fd)
 assert stamp(s)==stamp(opened)==stamp(p.lstat())
 return stamp(s)
def bound_checkouts():
 for path,original in CHECKOUT_IDENTITIES.items():assert checkout_identity(path)==original
def read(p,cap):
 private(BASE);bound_checkouts()
 assert p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents))
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_uid==UID and s.st_nlink==1 and not s.st_mode&0o7000 and (p.is_relative_to(PRIMARY) or not s.st_mode&0o0022) and s.st_size<=cap
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 with os.fdopen(fd,'rb') as f:b=f.read(cap+1);assert len(b)==s.st_size and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat())
 bound_checkouts()
 return b,stamp(s)
def git(repo,*argv):
 assert repo in (PRIMARY,C);bound_checkouts()
 try:return subprocess.check_output(['/usr/bin/git','-C',str(repo),*argv],timeout=120)
 finally:bound_checkouts()
a=argparse.ArgumentParser();a.add_argument('--expected-primary',required=True);a.add_argument('--manifest-sha256',required=True);a.add_argument('--manifest-identity-sha256',required=True);args=a.parse_args();os.umask(0o077)
assert os.getuid()==os.geteuid()==UID and re.fullmatch('[a-f0-9]{40}',args.expected_primary)
assert all(re.fullmatch('[a-f0-9]{64}',x) for x in (args.manifest_sha256,args.manifest_identity_sha256))
private(BASE)
CHECKOUT_IDENTITIES={repo:checkout_identity(repo) for repo in (PRIMARY,C)}
retention_path=PRIMARY/'swdb-project/records/.retention.lock';retention_bytes,retention_stat=read(retention_path,0)
assert retention_bytes==b'' and sha(retention_bytes)=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
assert git(PRIMARY,'rev-parse','HEAD').decode().strip()==git(PRIMARY,'rev-parse','origin/yanrujhou_main').decode().strip()==args.expected_primary
assert git(PRIMARY,'branch','--show-current').decode().strip()=='yanrujhou_main' and git(PRIMARY,'status','--porcelain').decode().strip()=='?? swdb-project/records/.retention.lock'
assert git(C,'rev-parse','HEAD').decode().strip()=='f893fed400347ed23d92e917d8bde21b75e5375d' and not git(C,'status','--porcelain').strip()
mb,ms=read(PRIMARY/REL/'manifest.json',256*1024);m=json.loads(mb)
assert sha(mb)==args.manifest_sha256 and m['canonical_ensure_ascii'] is True
assert m['identity_sha256']==args.manifest_identity_sha256==sha(json.dumps({k:v for k,v in m.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
assert m['archive_supplies_cleanup_capacity_plan_or_scientific_admission'] is False and m['archival_invokes_selected_control_mains'] is False
originals={x['archive_path']:x for x in m['originals']};copies={}
for name,(size,digest) in EXPECTED.items():
 rel=REL/'corrected-source-package'/name
 assert originals[str(rel)]['bytes']==size and originals[str(rel)]['sha256']==digest
 b,s=read(PRIMARY/rel,256*1024);assert len(b)==size and sha(b)==digest and git(PRIMARY,'show',args.expected_primary+':'+str(rel))==b
 copies[name]=(b,s,rel)
for repo in (PRIMARY,C):
 git(repo,'fetch','origin','codex/lanl-analytic-eval')
 assert git(repo,'rev-parse','origin/codex/lanl-analytic-eval').decode().strip()==args.expected_primary
bound_checkouts()
assert not os.path.lexists(DEST);os.mkdir(DEST,0o700);private(DEST)
bound_checkouts()
result=[]
for name,(b,s,rel) in copies.items():
 bound_checkouts()
 out=DEST/name;fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 got,target=read(out,256*1024);assert got==b and stat.S_IMODE(target['mode'])==0o600 and read(PRIMARY/rel,256*1024)==(b,s)
 result.append({'archive_path':str(PRIMARY/rel),'private_path':str(out),'bytes':len(got),'sha256':sha(got),'private_stat':target})
assert read(PRIMARY/REL/'manifest.json',256*1024)==(mb,ms)
assert git(PRIMARY,'rev-parse','HEAD').decode().strip()==args.expected_primary and git(PRIMARY,'status','--porcelain').decode().strip()=='?? swdb-project/records/.retention.lock'
assert git(C,'rev-parse','HEAD').decode().strip()=='f893fed400347ed23d92e917d8bde21b75e5375d' and not git(C,'status','--porcelain').strip()
assert read(retention_path,0)==(retention_bytes,retention_stat)
bound_checkouts()
print(json.dumps({'format':'swdb.git-reviewed-sidecar-corrected-storage-source-private-copy.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'expected_primary':args.expected_primary,'source_copies':result,'archive_manifest_file_sha256':sha(mb),'archive_manifest_identity_sha256':m['identity_sha256'],'source_refs_refreshed_at_expected_primary':True,'bound_checkout_root_stats':{str(path):original for path,original in CHECKOUT_IDENTITIES.items()},'original_empty_retention_file':{'path':str(retention_path),'bytes':len(retention_bytes),'sha256':sha(retention_bytes),'stat':retention_stat,'unchanged_before_after':True},'selected_mains_invoked':False,'cleanup_capacity_or_scientific_admission':False},sort_keys=True))
