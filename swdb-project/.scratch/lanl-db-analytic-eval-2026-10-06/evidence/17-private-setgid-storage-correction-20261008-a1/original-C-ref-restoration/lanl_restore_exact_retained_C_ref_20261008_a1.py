"""Prospective exact absent-C-ref repair only; SOURCE-ONLY / NOT RUN."""
import datetime, hashlib, json, os, pathlib, pwd, socket, stat, subprocess, sys, time
P=pathlib.Path; UID=114316761; BASE=P('/data1/yanruj'); PRIMARY=BASE/'ArchEvolve'
C=BASE/'ArchEvolve-lanl-cpu-model-validation-20261006-a1'
CURRENT='b91756c92a596ef88585b934b4b9a0a06b8767a4'; CHEAD='f893fed400347ed23d92e917d8bde21b75e5375d'
REF='refs/heads/codex/lanl-ticket11-source-c'; F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
NAMESPACE_SHA='43864cde40d28f83331ebafdb247e2bf688e62a351e6b5619cd68bd098413c77'
NATIVE={'/usr/bin/git':(4019024,'06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),
        '/usr/bin/python3.12':(8020928,'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f')}
DEADLINE=time.monotonic()+600; state='preflight'; os.umask(0o077)
def need(value,code):
 if not value:raise ValueError(code)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def stamp(s):return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}
def left():
 r=DEADLINE-time.monotonic();need(r>0,'finite_administrative_deadline');return r
def route(p):
 need(p.resolve(strict=True)==p and not any(x.is_symlink() for x in (p,*p.parents)),'canonical_nonsymlink_route')
def root(p):
 left();route(p);s=p.lstat();need(stat.S_ISDIR(s.st_mode) and s.st_uid==UID,'owned_checkout_root')
 if p==BASE:need(stat.S_IMODE(s.st_mode)==0o700,'BASE_private0700')
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
 try:need(stamp(s)==stamp(os.fstat(fd))==stamp(p.lstat()),'root_open_identity')
 finally:os.close(fd)
 return stamp(s)
def roots():
 for p,s in ROOTS.items():need(root(p)==s,'bound_root_changed')
def read(p,cap,owner=UID,native=False):
 left();roots();route(p);s=p.lstat()
 need(stat.S_ISREG(s.st_mode) and s.st_uid==owner and s.st_nlink==1 and not s.st_mode&0o7000 and s.st_size<=cap,'ordinary_owned_single_link_file')
 if native:need(stat.S_IMODE(s.st_mode)==0o755,'native_mode0755')
 else:need(p.is_relative_to(PRIMARY) or p.is_relative_to(C),'read_scope')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 with os.fdopen(fd,'rb') as f:
  raw=f.read(cap+1);need(len(raw)==s.st_size and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'returned_file_bytes_stat')
 roots();return raw,stamp(s)
def natives():
 return {p:{'bytes':len(b),'sha256':sha(b),'stat':s} for p,(n,h) in NATIVE.items() for b,s in [read(P(p),n,0,True)] if checked_native(b,n,h)}
def checked_native(b,n,h):need(len(b)==n and sha(b)==h,'native_bytes_identity');return True
def stable():
 roots();need(natives()==NATIVE_PINS,'native_changed');need(read(LOCK,0)==RETENTION,'original_empty_retention_changed')
def git(repo,*args,allow_absent=False):
 need(repo in (PRIMARY,C),'exact_Git_repository');stable();left()
 env={'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','GIT_TERMINAL_PROMPT':'0','GIT_NO_LAZY_FETCH':'1',
      'GIT_OPTIONAL_LOCKS':'0','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
 try:
  r=subprocess.run(['/usr/bin/git','-c','protocol.allow=never','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','-C',str(repo),*args],
                   stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=min(120,left()),check=False)
  need(len(r.stdout)+len(r.stderr)<=32*1024*1024,'Git_output32MiB');need(not r.stderr,'Git_stderr_refusal')
  need(r.returncode==0 or (allow_absent and r.returncode==1 and not r.stdout),'Git_exit_refusal')
  return r.stdout,r.returncode
 finally:stable()
def g(repo,*args):return git(repo,*args)[0]
def inventories():
 all_refs={}
 for repo in (PRIMARY,C):
  b=g(repo,'for-each-ref','--format=%(refname) %(objectname)');rows={}
  for line in b.decode('ascii').splitlines():
   name,oid=line.split(' ');need(name.startswith('refs/') and len(oid)==40 and all(x in '0123456789abcdef' for x in oid) and name not in rows,'complete_ref_inventory_shape');rows[name]=oid
  need(list(rows)==sorted(rows),'sorted_ref_inventory');all_refs[str(repo)]=(b,rows)
 return all_refs
def checkout_checks():
 for ref in ('HEAD','refs/heads/yanrujhou_main','refs/remotes/origin/yanrujhou_main','refs/remotes/origin/codex/lanl-analytic-eval'):
  need(g(PRIMARY,'rev-parse',ref).decode().strip()==CURRENT,'PRIMARY_current_four_refs')
 need(g(PRIMARY,'branch','--show-current').decode().strip()=='yanrujhou_main','PRIMARY_branch')
 need(g(PRIMARY,'status','--porcelain').decode().strip()=='?? swdb-project/records/.retention.lock','PRIMARY_retention_only')
 need(g(C,'rev-parse','HEAD').decode().strip()==CHEAD and not g(C,'status','--porcelain').strip() and not g(C,'branch','--show-current').strip(),'protected_C_clean_detached')
 need(not g(PRIMARY,'merge-base','--is-ancestor',CHEAD,CURRENT),'C_ancestor_current')
 need(g(PRIMARY,'rev-parse','--path-format=absolute','--git-common-dir').decode().strip()==str(PRIMARY/'.git')
      and g(C,'rev-parse','--path-format=absolute','--git-common-dir').decode().strip()==str(PRIMARY/'.git'),'exact_shared_common_Git_directory')
 route(PRIMARY/'.git');need(stat.S_ISDIR((PRIMARY/'.git').lstat().st_mode) and (PRIMARY/'.git').lstat().st_uid==UID,'owned_common_Git_directory')
 namespace=g(PRIMARY,'ls-tree','-r','-z',CHEAD,'--','swdb-project/swdb')
 need(len(namespace)==20905 and sha(namespace)==NAMESPACE_SHA and namespace==g(PRIMARY,'ls-tree','-r','-z',CURRENT,'--','swdb-project/swdb')
      and namespace==g(C,'ls-tree','-r','-z',CHEAD,'--','swdb-project/swdb'),'exact_C223_namespace')
 entries=[x for x in namespace.split(b'\0') if x];need(len(entries)==223,'namespace223')
 py_paths=[x.split(b'\t',1)[1].decode() for x in entries if x.split(b'\t',1)[1].endswith(b'.py')]
 need(len(py_paths)==185,'modules185');sources={}
 for repo in (PRIMARY,C):
  module_root=repo/'swdb-project/swdb';need(root(module_root)['uid']==UID,'owned_module_root')
  actual=[]
  for folder,dirs,files in os.walk(module_root,followlinks=False,onerror=lambda error:(_ for _ in ()).throw(ValueError('source_walk_inaccessible'))):
   left()
   for name in dirs:route(P(folder)/name)
   for name in files:
    if name.endswith('.py'):actual.append(str((P(folder)/name).relative_to(repo)))
  need(sorted(actual)==sorted(py_paths),'exact_live185_paths')
  facts={};pins={}
  for name in sorted(py_paths):
   b,s=read(repo/name,8*1024*1024);rel=str(P(name).relative_to('swdb-project/swdb'));facts[rel]=sha(b);pins[name]={'sha256':sha(b),'stat':s}
  need(sha(json.dumps(facts,sort_keys=True,separators=(',',':'),allow_nan=False).encode())==F6,'exact_live_F6')
  sources[str(repo)]=pins
 return sources
try:
 need(sys.platform=='linux' and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==UID
      and pwd.getpwuid(UID).pw_name=='yanruj' and sys.executable=='/usr/bin/python3.12','exact_native_host_account')
 ROOTS={p:root(p) for p in (BASE,PRIMARY,C)};LOCK=PRIMARY/'swdb-project/records/.retention.lock';RETENTION=read(LOCK,0)
 need(RETENTION[0]==b'' and sha(RETENTION[0])=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855','original_empty_retention')
 NATIVE_PINS=natives();before_sources=checkout_checks();before=inventories()
 need(all(REF not in rows for b,rows in before.values()),'C_ref_must_be_absent')
 loose=PRIMARY/'.git'/REF;need(not os.path.lexists(loose) and not any(p.is_symlink() for p in loose.parents),'absent_literal_ref_route')
 need(git(PRIMARY,'show-ref','--verify','--quiet',REF,allow_absent=True)[1]==1,'native_absent_ref')
 state='exact_ref_update_attempt_started';git(PRIMARY,'update-ref','--no-deref',REF,CHEAD,'0'*40);state='exact_ref_update_returned0'
 after=inventories()
 for key,(b,rows) in before.items():
  expected=dict(rows);expected[REF]=CHEAD;need(after[key][1]==expected,'exactly_one_new_ref_all_originals_preserved')
 need(checkout_checks()==before_sources,'source_bytes_stats_identity_changed');stable()
 result={'format':'swdb.exact-retained-C-ref-restoration-original.v1','sealed':False,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'state':state,'expected_primary':CURRENT,'new_ref':REF,'new_ref_oid':CHEAD,'expected_old_oid':'0'*40,
         'native_pins':NATIVE_PINS,'bound_root_stats':{str(p):s for p,s in ROOTS.items()},
         'retention':{'bytes':0,'sha256':sha(RETENTION[0]),'stat':RETENTION[1]},'namespace223_sha256':NAMESPACE_SHA,'Python_modules':185,'F6':F6,
         'ref_inventory':{p:{'before_count':len(before[p][1]),'after_count':len(after[p][1]),'before_file_sha256':sha(before[p][0]),'after_file_sha256':sha(after[p][0]),'only_added_ref':REF} for p in before},
         'one_Git_seconds':120,'finite_administration_seconds':600,'fetch_checkout_or_selected_control_main':False,'scientific_capacity_or_cleanup_admission':False}
 raw=json.dumps(result,sort_keys=True,ensure_ascii=True,allow_nan=False).encode();need(len(raw)+1<=16384,'bounded_original_receipt');print(raw.decode())
except (OSError,ValueError,subprocess.SubprocessError,UnicodeError) as error:
 print(json.dumps({'format':'swdb.exact-retained-C-ref-restoration-refusal.v1','sealed':False,'state':state,'error_class':type(error).__name__,
                   'error_message_sha256':sha(str(error).encode()),'success_or_admission':False},sort_keys=True));sys.exit(1)
