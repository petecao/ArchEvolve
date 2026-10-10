"""SOURCE ONLY / NOT RUN. Fixed private byte copies; no selected main or admission."""
import argparse,datetime,hashlib,json,os,pathlib,pwd,re,socket,stat,subprocess,sys,time,zlib,selectors,signal
P=pathlib.Path;BASE=P('/data1/yanruj');PRIMARY=BASE/'ArchEvolve';C=BASE/'ArchEvolve-lanl-cpu-model-validation-20261006-a1';UID=114316761
CORE='f893fed400347ed23d92e917d8bde21b75e5375d'
PREFIX=P('swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-reference-birth-dependency-observation-custody-20261008-a1')
SOURCES=BASE/'lanl-storage-admin-selected-source-20261008-a5'
ROLE=BASE/'lanl-portal-helper-inode-review-20261008-a1'
INPUTS=BASE/'lanl17-reviewed-deployment-inputs-20261008-a1'
HELPER='c195eccf8f728f7752dd89e0588af4fe6f0c05f50c7aa6cb47e5bd95f9ecb46b'
# Every destination and original byte pin is fixed; only future role-review bytes are explicit inputs.
FIXED=[
 ('/private/tmp/lanl_consumed_detached_source_guard_r7_20261008_a1.py',SOURCES/'lanl_consumed_detached_source_guard_r7_20261008_a1.py',117232,'97219cdb326edf76e6d341aab4a2a8d58a4750e3da8d2e24a5f9e1097f4a69be'),
 ('/private/tmp/lanl17_acquire_passive_consumed_source_metadata_20261008_a1_r8.py',SOURCES/'lanl17_acquire_passive_consumed_source_metadata_20261008_a1_r8.py',88535,'1188ea21138260a11c1b016b5080f509ece225338d98af1689e053306305ce1c'),
 ('/private/tmp/lanl17_detach_exact_R4_storage_administration_20261008_a1_r6.py',SOURCES/'lanl17_detach_exact_R4_storage_administration_20261008_a1_r6.py',24002,'2b9b2200b002693fa79930822dee530ab9ecda17d3bd04be9f2a726e355ff5df'),
 ('/private/tmp/lanl17_detach_passive_observer_administration_20261008_a1_r8.py',SOURCES/'lanl17_detach_passive_observer_administration_20261008_a1_r8.py',16091,'0dd699118fd456afe3b0b2b6159fc807a3d4bd05940f0f8b304f3e2657179b82'),
 ('/private/tmp/lanl17-fuse-service-public-identity-original-20261008-a1.json',ROLE/'public-identity.json',4103,'1ea76b7519827bae6f81902c2bebd6b16e22c303fcada24257bf1bab73174489'),
 ('/private/tmp/lanl17-exact-checkout-inode-birth-query-original-20261008-a1.json',ROLE/'checkout-inode-birth.json',14762700,'e228811f4b119a7e0c97b666b7da249374f3637cef8b17c0b10b54c4ff422fb7'),
 ('/private/tmp/lanl17-exact-worktree-administration-inode-birth-original-actual-20261008-a1.json',ROLE/'git-admin-inode-birth.json',139083,'a62b53bd4c9f89c3a212690750905c6cf13203fca8fceee560a9ad9ee25a1dd5'),
 ('/private/tmp/lanl17_publish_checked_dx100_deployment_inputs_20261008_a1_r3.py',BASE/'lanl17_publish_checked_dx100_deployment_inputs_20261008_a1_r3.py',27901,'55558276d912c924df9a6701d1848829f42a758233c20ad6da1e06bc6b176f29'),
 ('/private/tmp/lanl17-original-dx100-deployment-prerequisites-query-actual-20261008-a1-r3.json',INPUTS/'original-dx100-deployment-facts.json',60682,'0252f42cde88946aadc6866af53b867b55b782bc9883eae3bb8b85a5ee56823e'),
 ('/private/tmp/lanl17-dx100-live-source-facts-parent-review-20261008-a1.json',INPUTS/'dx100-parent-review.json',1132,'5072c3025b0c372d6d4455d213d1e57d8ba6dda3f0b087883b447026828c4d07'),
 ('/private/tmp/lanl17-native-pyyaml-package-facts-original-actual-20261008-a1.json',INPUTS/'original-pyyaml-facts.json',14870,'bf5f733f184049264ba1ee45a7db09c64c2096a37216f4a153fa64a91b0be6b1'),
 ('/private/tmp/lanl17-native-pyyaml-original-parent-semantic-review-20261008-a1.json',INPUTS/'pyyaml-parent-review.json',1164,'c53e8e57c1118065be79bf1b5efbdfca636c1ed2c6a484c89f55e0b3998c4e9d')]
NATIVES={P('/usr/bin/python3.12'):(8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),P('/usr/bin/git'):(4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb')}
LIMITS={'seconds':300,'Git_seconds':120,'manifest_bytes':2*1024*1024,'one_file_bytes':32*1024*1024,'total_read_bytes':256*1024*1024,'role_review_bytes':256*1024,'stdout_bytes':32*1024,'Git_stderr_bytes':256*1024}
END=None;READ=0;CHECKOUTS={};CREATED=[]
class Refused(Exception):pass
def need(ok,code):
 if not ok:raise Refused(code)
def tick():need(END is not None and time.monotonic()<END,'copy_deadline')
def charge(n):
 global READ
 tick();READ+=n;need(READ<=LIMITS['total_read_bytes'],'cumulative_read_limit')
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def strict(b):
 def pairs(rows):
  d={}
  for k,v in rows:need(k not in d,'duplicate_JSON_key');d[k]=v
  return d
 def bad(v):raise Refused('nonfinite_JSON')
 return json.loads(b,object_pairs_hook=pairs,parse_constant=bad)
def stamp(s):return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}
def route(p):
 tick();need(p.is_absolute() and '..' not in p.parts and not any(q.name in ('auth.json','.ssh','.aws','.codex','.gnupg') for q in (p,*p.parents)),'closed_noncredential_route')
 for q in (p,*p.parents):need(not stat.S_ISLNK(q.lstat().st_mode),'symlink_component')
 need(p.resolve(strict=True)==p,'route_redirect');return p.lstat()
def private(p):
 s=route(p);need(stat.S_ISDIR(s.st_mode) and s.st_uid==UID and stat.S_IMODE(s.st_mode)==0o700,'private_owned_directory');return stamp(s)
def checkout(p):
 need(p in (PRIMARY,C),'fixed_checkout_route');private(BASE);s=route(p)
 need(stat.S_ISDIR(s.st_mode) and s.st_uid==UID,'checkout_owner_type')
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:need(stamp(os.fstat(fd))==stamp(s)==stamp(p.lstat()),'checkout_open_identity')
 finally:os.close(fd)
 return stamp(s)
def bound():
 for p,before in CHECKOUTS.items():need(checkout(p)==before,'checkout_root_changed')
def read(p,cap,owner=UID,mode=None):
 bound();s=route(p)
 need(stat.S_ISREG(s.st_mode) and s.st_uid==owner and s.st_nlink==1 and not s.st_mode&0o7000 and 0<=s.st_size<=cap,'regular_owner_link_size')
 need(p.is_relative_to(PRIMARY) or not s.st_mode&0o22,'private_or_native_file_writable')
 if mode is not None:need(stat.S_IMODE(s.st_mode)==mode,'exact_file_mode')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:
  need(stamp(os.fstat(fd))==stamp(s),'file_open_changed');pieces=[];n=0
  while True:
   tick();b=os.read(fd,min(1024*1024,cap-n+1))
   if not b:break
   charge(len(b));n+=len(b);need(n<=cap,'one_file_read_limit');pieces.append(b)
  need(n==s.st_size and stamp(os.fstat(fd))==stamp(s)==stamp(p.lstat()),'file_changed_during_read')
 finally:os.close(fd)
 bound();return b''.join(pieces),stamp(s)
def git(repo,*argv,cap=8192):
 need(repo in (PRIMARY,C),'Git_fixed_checkout');bound();tick()
 env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
 command=['/usr/bin/git','--no-replace-objects','-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false','-C',str(repo),*argv]
 child=None;selector=selectors.DefaultSelector();parts={'stdout':[],'stderr':[]};counts={'stdout':0,'stderr':0}
 deadline=min(END,time.monotonic()+LIMITS['Git_seconds'])
 try:
  child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,start_new_session=True)
  for key,stream in (('stdout',child.stdout),('stderr',child.stderr)):
   os.set_blocking(stream.fileno(),False);selector.register(stream,selectors.EVENT_READ,key)
  while selector.get_map():
   tick();need(time.monotonic()<deadline,'Git_timeout')
   for selected,event in selector.select(min(.1,max(0,deadline-time.monotonic()))):
    key=selected.data;limit=cap if key=='stdout' else LIMITS['Git_stderr_bytes']
    block=os.read(selected.fileobj.fileno(),min(65536,limit-counts[key]+1))
    if not block:selector.unregister(selected.fileobj);continue
    charge(len(block));counts[key]+=len(block);need(counts[key]<=limit,'Git_output_bound');parts[key].append(block)
  code=child.wait(timeout=max(.1,deadline-time.monotonic()));need(code==0,'Git_nonzero')
  return b''.join(parts['stdout'])
 finally:
  selector.close()
  if child is not None:
   # Only this new-session native Git group; never another source, daemon or lane.
   try:os.killpg(child.pid,signal.SIGTERM)
   except ProcessLookupError:pass
   stop=time.monotonic()+15
   while time.monotonic()<stop:
    try:os.killpg(child.pid,0)
    except ProcessLookupError:break
    time.sleep(.05)
   else:
    try:os.killpg(child.pid,signal.SIGKILL)
    except ProcessLookupError:pass
   child.wait(timeout=5)
   child.stdout.close();child.stderr.close()
  bound()
def source_state(head):
 need(git(PRIMARY,'rev-parse','HEAD').decode().strip()==git(PRIMARY,'rev-parse','origin/yanrujhou_main').decode().strip()==head,'fully_delivered_primary_HEAD')
 need(git(PRIMARY,'branch','--show-current').decode().strip()=='yanrujhou_main','primary_branch')
 need(git(PRIMARY,'status','--porcelain','-z','--untracked-files=all')==b'?? swdb-project/records/.retention.lock\0','only_original_retention_untracked')
 need(git(C,'rev-parse','HEAD').decode().strip()==CORE and not git(C,'status','--porcelain','-z','--untracked-files=all'),'C_identity_or_cleanliness')
def decode(row,stored,size,digest):
 need(row['original_bytes']==size and row['original_sha256']==digest and row['stored_bytes']==len(stored) and row['stored_sha256']==sha(stored),'manifest_selected_byte_pins')
 need(row['decompressed_original_bytes']==size and row['decompressed_original_sha256']==digest and row['decompression_equals_original_byte_pin'] is True,'manifest_lossless_equality')
 codec=row['storage_codec'];tick()
 if codec=='plain':raw=stored
 else:
  need(codec=='gzip_mtime0' and stored[:8]==b'\x1f\x8b\x08\x00\x00\x00\x00\x00','fixed_lossless_gzip_header')
  d=zlib.decompressobj(31);raw=d.decompress(stored,size+1)
  need(len(raw)<=size and d.eof and not d.unused_data and not d.unconsumed_tail,'one_bounded_complete_gzip_member')
  charge(len(raw))
 need(len(raw)==size and sha(raw)==digest,'decompressed_original_bytes_changed');return raw

def main():
 global END,CHECKOUTS
 END=time.monotonic()+LIMITS['seconds'];a=argparse.ArgumentParser(description=__doc__)
 for key in ('expected-primary','manifest-sha256','manifest-identity-sha256','role-review-original-path','role-review-sha256','role-review-identity-sha256','source-sha256'):a.add_argument('--'+key,required=True)
 a.add_argument('--role-review-bytes',required=True,type=int);args=a.parse_args();os.umask(0o077)
 need(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.uname().machine=='x86_64' and os.getuid()==os.geteuid()==UID and pwd.getpwuid(UID).pw_name=='yanruj','native_host_account')
 need(sys.dont_write_bytecode and sys.flags.optimize==0 and re.fullmatch('[a-f0-9]{40}',args.expected_primary),'unoptimized_B_and_exact_revision')
 need(all(re.fullmatch('[a-f0-9]{64}',v) for v in (args.manifest_sha256,args.manifest_identity_sha256,args.role_review_sha256,args.role_review_identity_sha256,args.source_sha256)),'required_SHA_pins')
 need(0<args.role_review_bytes<=LIMITS['role_review_bytes'] and P(args.role_review_original_path).parent==P('/private/tmp') and P(args.role_review_original_path).suffix=='.json','explicit_closed_future_role_original')
 need(P(sys.executable).resolve(strict=True)==P('/usr/bin/python3.12'),'actual_native_python_route')
 private(BASE);CHECKOUTS={p:checkout(p) for p in (PRIMARY,C)}
 own=P(__file__).absolute();need(own.parent==BASE,'source_direct_private_BASE');ownraw,ownstat=read(own,256*1024,mode=0o600);need(sha(ownraw)==args.source_sha256,'own_source_byte_pin')
 native={}
 for p,(size,digest) in NATIVES.items():
  b,s=read(p,16*1024*1024,0,0o755);need(len(b)==size and sha(b)==digest,'native_source_hash');native[str(p)]={'bytes':size,'sha256':digest,'stat':s}
 retention=PRIMARY/'swdb-project/records/.retention.lock';rb,rs=read(retention,0);need(rb==b'' and sha(rb)=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855','original_empty_retention')
 source_state(args.expected_primary)
 manifest_path=PRIMARY/PREFIX/'manifest.json';mb,ms=read(manifest_path,LIMITS['manifest_bytes']);m=strict(mb)
 need(sha(mb)==args.manifest_sha256 and m['format']=='swdb.local-reference-birth-dependency-observation.byte-custody.v1' and m['canonical_ensure_ascii'] is True,'explicit_manifest_source')
 need(m['identity_sha256']==args.manifest_identity_sha256==sha(canonical({k:v for k,v in m.items() if k!='identity_sha256'})),'original_manifest_True_seal')
 need(m['new_plan_process_role_cleanup_capacity_or_scientific_admission'] is False and m['selected_mains_tests_SSH_scientific_or_Git_mutations_performed_by_archiver'] is False,'archive_custody_only_boundary')
 original_rows=m['originals'];need(isinstance(original_rows,list) and len(original_rows)<=256,'finite_manifest_rows')
 by_original={r['original_path']:r for r in original_rows};need(len(by_original)==len(original_rows),'duplicate_original_path')
 jobs=list(FIXED)+[(args.role_review_original_path,ROLE/'parent-review.json',args.role_review_bytes,args.role_review_sha256)]
 need(len(jobs)==13 and len({str(x[1]) for x in jobs})==13,'fixed_thirteen_destinations')
 copies=[]
 for original,dest,size,digest in jobs:
  need(original in by_original,'explicit_archived_original_missing');row=by_original[original];relative=P(row['stored_relative_path'])
  need(not relative.is_absolute() and '..' not in relative.parts and relative.parts and str(relative)==row['stored_relative_path'],'archive_relative_route')
  rel=PREFIX/relative;need(0<=row['stored_bytes']<=LIMITS['one_file_bytes'] and size<=LIMITS['one_file_bytes'],'selected_file_bounds')
  stored,source_stat=read(PRIMARY/rel,LIMITS['one_file_bytes']);need(len(stored)==row['stored_bytes'] and sha(stored)==row['stored_sha256'],'physical_stored_original_pin')
  mode=git(PRIMARY,'ls-tree','-z',args.expected_primary,'--',str(rel));need(mode.startswith(b'100644 blob ') and mode.endswith(b'\t'+str(rel).encode()+b'\0') and mode.count(b'\0')==1,'Git100644_selected_blob')
  need(git(PRIMARY,'cat-file','-s',args.expected_primary+':'+str(rel),cap=64)==(str(len(stored))+'\n').encode(),'Git_stored_blob_size_before_body_read')
  # Exact immutable Git object size is now bounded before Gitshow allocation.
  need(git(PRIMARY,'show',args.expected_primary+':'+str(rel),cap=LIMITS['one_file_bytes'])==stored,'Git_delivered_original_byte_equality')
  raw=decode(row,stored,size,digest);copies.append((original,dest,raw,rel,stored,source_stat))
 role=strict(copies[-1][2]);need(role['format']=='swdb.exact-portal-autounmount-semantic-parent-review.v1' and role['canonical_ensure_ascii'] is True and role['shared_helper_sha256']==HELPER and role['identity_sha256']==args.role_review_identity_sha256==sha(canonical({k:v for k,v in role.items() if k!='identity_sha256'})),'explicit_actual_role_True_seal_and_helper')
 need(role['accepted_exact_role_only'] is True and role['global_reference_free_or_cleanup_capacity_or_scientific_admission'] is False and role['other_consumers_parent_or_descendants_exempted'] is False,'role_scope_not_capacity_or_other_consumers')
 for key,filename,size,digest in (('public_identity','public-identity.json',4103,FIXED[4][3]),('checkout_birth','checkout-inode-birth.json',14762700,FIXED[5][3]),('git_admin_birth','git-admin-inode-birth.json',139083,FIXED[6][3])):
  r=role['original_pins'][key];need(r['path']==str(ROLE/filename) and r['bytes']==size and r['sha256']==digest,'actual_role_original_routes')
 for p in (SOURCES,ROLE,INPUTS,BASE/'lanl17_publish_checked_dx100_deployment_inputs_20261008_a1_r3.py'):need(not os.path.lexists(p),'destination_already_exists_no_repair')
 # Explicit reviewed administrative ref refresh only; C physical HEAD/source stays fixed.
 for repo in (PRIMARY,C):
  git(repo,'fetch','origin','codex/lanl-analytic-eval');need(git(repo,'rev-parse','origin/codex/lanl-analytic-eval').decode().strip()==args.expected_primary,'integration_ref_not_final_delivered')
 source_state(args.expected_primary);bound()
 for p in (SOURCES,ROLE,INPUTS):os.mkdir(p,0o700);CREATED.append(str(p));private(p)
 published=[]
 for original,dest,raw,rel,stored,before in copies:
  bound();private(dest.parent);need(read(PRIMARY/rel,LIMITS['one_file_bytes'])==(stored,before),'archived_original_changed_before_write')
  fd=os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600);CREATED.append(str(dest))
  with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  got,after=read(dest,LIMITS['one_file_bytes'],mode=0o600);need(got==raw,'published_original_bytes')
  published.append({'original_path':original,'stored_git_path':str(rel),'private_path':str(dest),'bytes':len(raw),'sha256':sha(raw),'private_stat':after})
 for original,dest,raw,rel,stored,before in copies:
  need(read(PRIMARY/rel,LIMITS['one_file_bytes'])==(stored,before),'final_archived_original_changed');need(read(dest,LIMITS['one_file_bytes'],mode=0o600)[0]==raw,'final_private_original_changed')
 need(read(manifest_path,LIMITS['manifest_bytes'])==(mb,ms) and read(own,256*1024,mode=0o600)==(ownraw,ownstat),'final_manifest_or_own_source_changed')
 for p,before in native.items():
  b,s=read(P(p),16*1024*1024,0,0o755);need(s==before['stat'] and len(b)==before['bytes'] and sha(b)==before['sha256'],'final_native_changed')
 need(read(retention,0)==(rb,rs),'original_retention_changed');source_state(args.expected_primary);bound()
 return {'format':'swdb.git-reviewed-portal-role-source-input-private-copy.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'expected_primary':args.expected_primary,'manifest_file_sha256':sha(mb),'manifest_identity_sha256':m['identity_sha256'],'actual_role_review_file_sha256':args.role_review_sha256,'actual_role_review_identity_sha256':args.role_review_identity_sha256,'copies':published,'native_pins':native,'read_bytes_charged':READ,'limits':LIMITS,'created_paths':CREATED,'C_physical_HEAD_preserved':CORE,'source_refs_refreshed_at_exact_expected_primary':True,'selected_G_O_publisher_or_other_mains_invoked':False,'new_plan_subset_capacity_or_scientific_admission':False}
if __name__=='__main__':
 try:
  result=main();code=0
 except BaseException as exc:
  result={'format':'swdb.git-reviewed-portal-role-private-copy-failure.v1','sealed':False,'error_class':type(exc).__name__,'reason':str(exc) if isinstance(exc,Refused) else 'original_exception_text_not_transferred','created_paths_preserved':CREATED,'read_bytes_charged':READ,'selected_mains_invoked':False,'capacity_or_scientific_admission':False};code=1
 raw=json.dumps(result,sort_keys=True,ensure_ascii=True,allow_nan=False).encode()+b'\n'
 if len(raw)>LIMITS['stdout_bytes']:raw=b'{"sealed":false,"failure":"compact_copy_status_limit","no_success_inferred":true}\n';code=1
 sys.stdout.buffer.write(raw);raise SystemExit(code)
