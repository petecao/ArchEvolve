"""2026-10-16 ET. Inert fresh isolated shared-Git sparse source preparation.

Embedded into root launcher V10. Never touches sparse config in the primary,
registers a worktree, follows a selected source symlink or removes an old path.
"""


def sparse_git(root,*arguments,input=None):
 env={'HOME':'/nonexistent','PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C',
      'GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_TERMINAL_PROMPT':'0'}
 argv=['/usr/bin/git','--no-optional-locks','--no-replace-objects',
       '-c','core.hooksPath=/dev/null','-c','core.fsmonitor=false',
       '-c','core.preloadIndex=false','-c','index.threads=1',
       '-C',str(root),*arguments]
 return subprocess.check_output(argv,input=input,env=env,timeout=120)


def sparse_pin(path,limit=1024**2):
 assert path.resolve(strict=True)==path and stat.S_ISREG(path.lstat().st_mode)
 before=path.stat();assert before.st_size<=limit
 raw=path.read_bytes();after=path.stat()
 fields=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_gid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
 assert fields(before)==fields(after) and len(raw)==before.st_size
 return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'identity':fields(before)}


def sparse_primary_snapshot(repo):
 common=repo/'.git';assert common.resolve(strict=True)==common and common.is_dir()
 configs={}
 for p in [common/'config',common/'config.worktree',*sorted((common/'worktrees').glob('*/config.worktree'))]:
  configs[str(p)]={'absent':True} if not os.path.lexists(p) else sparse_pin(p)
 lock=repo/'swdb-project/records/.retention.lock'
 return {'configs':configs,'retention_lock':sparse_pin(lock),
         'worktree_registration_sha256':hashlib.sha256(sparse_git(repo,'worktree','list','--porcelain','-z')).hexdigest()}


def sparse_inventory(data):
 rows=[]
 for part in data.split(b'\0'):
  if not part:continue
  meta,name=part.split(b'\t',1);mode,kind,oid,size=meta.decode().split();path=name.decode()
  assert mode in ('100644','100755') and kind=='blob' and path.startswith('swdb-project/')
  assert '..' not in P(path).parts and not any(ord(c)<32 for c in path)
  rows.append({'path':path,'mode':mode,'oid':oid,'bytes':int(size)})
 assert len(rows)==len({r['path'] for r in rows})
 return rows


def sparse_materialize(repo,source,sha,spec):
 assert sha==spec['source_commit'] and source==P('/data1/yanruj/probata-resume-20261016-'+sha[:8])
 assert not os.path.lexists(source),'sparse route requires a fresh isolated clone; never replace/reconfigure an old source'
 roots=['swdb-project/'+name for name in spec['roots']]
 rows=sparse_inventory(sparse_git(repo,'ls-tree','-rlz',sha,'--',*roots))
 serialized=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
 assert len(rows)==spec['files'] and sum(r['bytes'] for r in rows)==spec['bytes']
 assert hashlib.sha256(serialized).hexdigest()==spec['inventory_sha256']
 assert {name:sparse_git(repo,'rev-parse',sha+':swdb-project/'+name).decode().strip()
         for name in spec['roots']}==spec['consumer_oids']
 reserve=spec['bytes']+spec['metadata_headroom_bytes']
 assert shutil.disk_usage('/data1').free>=10*1024**3+reserve
 before=sparse_primary_snapshot(repo)
 sparse_git(repo,'clone','--shared','--no-checkout','--no-hardlinks','--no-tags',str(repo),str(source))
 own=source/'.git'
 assert own.resolve(strict=True)==own and own.is_dir() and not own.is_symlink()
 assert P(sparse_git(source,'rev-parse','--absolute-git-dir').decode().strip())==own
 common=P(sparse_git(source,'rev-parse','--git-common-dir').decode().strip())
 assert (common if common.is_absolute() else source/common).resolve(strict=True)==own
 assert (own/'objects/info/alternates').read_text()==str(repo/'.git/objects')+'\n'
 # This is an ordinary isolated clone, never worktree sparse-checkout. Only its
 # own private config and pattern file are written before the first checkout.
 sparse_git(source,'config','--local','core.sparseCheckout','true')
 sparse_git(source,'config','--local','core.sparseCheckoutCone','false')
 sparse_git(source,'config','--local','index.sparse','false')
 patterns=''.join('/'+name+('/' if name in ('swdb-project/swdb','swdb-project/schemas','swdb-project/vocab') else '')+'\n' for name in roots)
 with (own/'info/sparse-checkout').open('xb') as stream:stream.write(patterns.encode())
 sparse_git(source,'checkout','--detach',sha)
 assert sparse_git(source,'rev-parse','HEAD').decode().strip()==sha
 assert sparse_git(source,'rev-parse','--abbrev-ref','HEAD').decode().strip()=='HEAD'
 assert not sparse_git(source,'status','--porcelain','--untracked-files=all','--ignored')
 expected={r['path'] for r in rows};found=set();pending=[source]
 allowed_dirs={str(parent) for name in expected for parent in P(name).parents if str(parent)!='.'}
 while pending:
  parent=pending.pop();assert parent.resolve(strict=True)==parent and stat.S_ISDIR(parent.lstat().st_mode)
  with os.scandir(parent) as stream:children=list(stream)
  for item in children:
   p=P(item.path);relative=str(p.relative_to(source));st=p.lstat()
   if p==own:
    assert stat.S_ISDIR(st.st_mode);continue
   if stat.S_ISDIR(st.st_mode):assert relative in allowed_dirs;pending.append(p)
   else:assert stat.S_ISREG(st.st_mode) and relative in expected;found.add(relative)
 assert found==expected,'sparse checkout physical membership must equal all424 selected Git leaves'
 physical=sparse_git(source,'hash-object','--no-filters','--stdin-paths',input=''.join(str(source/r['path'])+'\n' for r in rows).encode()).decode().splitlines()
 assert physical==[r['oid'] for r in rows]
 for row in rows:
  p=source/row['path'];assert p.stat().st_size==row['bytes']
  assert bool(p.stat().st_mode&0o111)==(row['mode']=='100755')
 assert sparse_primary_snapshot(repo)==before,'primary config/registration/retention-lock changed'
 assert shutil.disk_usage('/data1').free>=10*1024**3,'source mount10GiB floor remains mandatory after sparse materialization'
 return expected,{'mode':spec['mode'],'source_commit':sha,'files':len(rows),'bytes':spec['bytes'],
                  'inventory_sha256':spec['inventory_sha256'],'consumer_oids':spec['consumer_oids'],
                  'private_git_config':sparse_pin(own/'config'),'private_sparse_patterns':patterns,
                  'shared_object_store':str(repo/'.git/objects'),'primary_before_after':before,
                  'scope':'Exact small physical consumer projection of complete retained Git commit. Primary config/worktree registration/retention lock and1433 source/raw unchanged; no historical full physical checkout claim.'}
