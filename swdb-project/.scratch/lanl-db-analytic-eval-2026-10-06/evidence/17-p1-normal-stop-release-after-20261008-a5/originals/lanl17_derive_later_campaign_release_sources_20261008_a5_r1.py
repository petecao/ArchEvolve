"""Local source derivation for actual p2-p4 attempt1/node0; no execution or admission."""
import argparse,ast,copy,difflib,hashlib,json,os,re,stat,sys
from pathlib import Path
BASE=Path('/private/tmp')
R='5e12a9796432654d88def24ecea617d16ca605b2'
H='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
N='00c269b43275753cbc81983180fb36c365d9275e82e350d7c5c5e039442c08e8'
P='32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
S='/data1/yanruj/ArchEvolve-lanl17-source-20261007-a5'
RAW='/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5'
CID1='extensa-gem5-bfs-20261006-p1'
SOURCES={
 'observer':('lanl17_read_p1_native_release_observation_20261008_a5_r2.py',15125,'df19c76a0a3c667f5d1b901677c72641a0f367e6971b4ee2e37a62871bbc7626'),
 'reader':('lanl17_read_p1_normal_terminal_originals_20261008_a5_r2.py',7926,'6ecee4f1ccd0227527da4cc5831cbc42aeb1120dd1b5f4656660dac92cb08818'),
 'author':('lanl17_finalize_p1_normal_release_request_20261008_a5_r4.py',18684,'5f74373dda97c28ae4e3aa2b74923d31bf747fc967d59b626da9fac836a3ac0f'),
 'draft':('lanl17-p1-release-request-draft-r1-20261008-a5.json',12307,'0c7b8fd601b07c8e61f1e6709aeeefeb11de619a1b1e2d10c5a77086a86eba08'),
 'helper':('lanl17_parent_helpers_cleanup60_a4.py',38195,H),
 'producer':('lanl17_parent_capture_projection_producer_a3_20261007.py',46165,P),
}
FIELDS=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
SEEN=[]
class Refused(ValueError):pass
def need(ok,code):
 if not ok:raise Refused(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def stamp(s):return {k:getattr(s,'st_'+k) for k in FIELDS}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()
def strict(b):
 def pairs(rows):
  d={}
  for k,v in rows:need(k not in d,'duplicate_key');d[k]=v
  return d
 def bad(v):raise Refused('nonfinite_JSON')
 v=json.loads(b,object_pairs_hook=pairs,parse_constant=bad);need(type(v) is dict,'JSON_object');return v

def read(p,cap,digest=None,size=None):
 need(p.is_absolute() and p.resolve(strict=True)==p and not any(x.is_symlink() for x in (p,*p.parents)),'canonical_local_file')
 s=p.lstat();need(stat.S_ISREG(s.st_mode) and s.st_uid==os.geteuid() and s.st_nlink==1 and not s.st_mode&0o7022 and 0<s.st_size<=cap,'owned_bounded_local_file')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
 with os.fdopen(fd,'rb') as f:
  need(stamp(s)==stamp(os.fstat(f.fileno())),'open_changed');b=f.read(cap+1)
  need(len(b)==s.st_size<=cap and stamp(s)==stamp(os.fstat(f.fileno()))==stamp(p.lstat()),'read_race')
 if digest is not None:need(sha(b)==digest,'exact_input_SHA')
 if size is not None:need(len(b)==size,'exact_input_size')
 SEEN.append((p,cap,sha(b),stamp(s)));return b

def sealed(v):
 need(v.get('canonical_ensure_ascii',True) is True,'canonical_True')
 need(type(v.get('identity_sha256')) is str and re.fullmatch('[0-9a-f]{64}',v['identity_sha256']) is not None and sha(canonical({k:x for k,x in v.items() if k!='identity_sha256'}))==v['identity_sha256'],'original_seal')
def one(s,old,new):need(s.count(old)==1,'narrow_source_anchor');return s.replace(old,new)
def output(p,b):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 return {'path':str(p),'bytes':len(b),'sha256':sha(b)}

def main():
 p=argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
 p.add_argument('--campaign',required=True,choices=[f'extensa-gem5-bfs-20261006-p{x}' for x in (2,3,4)])
 for name in ('dispatch-original','lane-original','manifest-original','native-wrapper-source'):p.add_argument('--'+name,required=True,type=Path)
 for name in ('dispatch-sha256','lane-sha256'):p.add_argument('--'+name,required=True)
 p.add_argument('--actual-dispatch-and-native-lane-provenance-reviewed',action='store_true')
 a=p.parse_args();need(sys.platform=='darwin' and os.getuid()==os.geteuid()!=0 and sys.flags.dont_write_bytecode and not sys.flags.optimize,'local_parent_flags');need(a.actual_dispatch_and_native_lane_provenance_reviewed,'actual_parent_provenance_review_required')
 for d in (a.dispatch_sha256,a.lane_sha256):need(re.fullmatch('[0-9a-f]{64}',d) is not None,'explicit_original_SHA')
 originals={k:read(BASE/n,65536,d,z) for k,(n,z,d) in SOURCES.items()}
 read(a.native_wrapper_source,32768,N,10510)
 m=strict(read(a.manifest_original,1048576,'b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1',292401));sealed(m)
 need(m['source_commit']==R and m['source']==S and m['raw']==RAW and m['helper_sha256']==H and m['estimator_sha256']==F6 and m['source_clean'] is True and m['wrapper']['sha256']==N,'exact_frozen_M2_source')
 db=read(a.dispatch_original,65536,a.dispatch_sha256);d=strict(db);sealed(d)
 need(d['format']=='swdb.lanl17-campaign-dispatch.v1' and d['campaign']==a.campaign and type(d['attempt']) is int and d['attempt']==1 and type(d['node']) is int and d['node']==0 and d['resume'] is False and d['baselines_only'] is False and d['source_commit']==R and d['manifest_sha256']==m['identity_sha256'] and d['estimator_sha256']==F6 and d['policy']==m['policy'],'actual_dispatch_scope_source_policy')
 lb=read(a.lane_original,32768,a.lane_sha256);lane=strict(lb)['socket_lane'];tag=a.campaign.rsplit('-',1)[1];job='swdb-lanl17-20261007-a5-'+tag+'-a1'
 need(type(lane) is dict and type(lane['node']) is int and lane['node']==0 and lane['job']==job and lane['lease_name']=='mbit10-evaluation-node0' and type(lane['lease_generation']) is int and lane['lease_generation']>0 and type(lane['exit_code']) is int and 'record_errors' not in lane,'actual_native_lane_generation_binding')
 generation=lane['lease_generation'];need(re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z',lane['started_utc']) is not None,'native_lane_start')
 names={k:n.replace('p1',tag) for k,(n,_,_) in SOURCES.items() if k in ('observer','reader','author','draft')}
 paths={k:BASE/n for k,n in names.items()}
 draft=strict(originals['draft']);draft['generation_basis']='actual native lane original; no counter inference';draft['known_active_generation']=generation
 draft['derived_from']={'path':str(a.dispatch_original),'bytes':len(db),'sha256':sha(db),'identity_sha256':d['identity_sha256']}
 draft['request_template']['context']['campaign']=a.campaign
 def routes(v):
  if isinstance(v,dict):return {k:routes(x) for k,x in v.items()}
  if isinstance(v,list):return [routes(x) for x in v]
  if isinstance(v,str):return v.replace(CID1+'/attempt-1',a.campaign+'/attempt-1').replace('lanl17-p1-',f'lanl17-{tag}-').replace('generation511',f'generation{generation}').replace('match511',f'match{generation}')
  return v
 draft=routes(draft);spec=draft['request_template'];need(spec['context']['policy']==m['policy'],'global_policy_retained')
 spec['observations']['lease_generation']['required_value']=generation
 spec['inputs']['dispatch'].update(path=RAW+'/attempts/'+a.campaign+'/attempt-1/dispatch-preregistration.json',bytes=len(db),sha256=sha(db),identity_sha256=d['identity_sha256'])
 draft_bytes=(json.dumps(draft,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
 def derive(k):
  s=originals[k].decode();s=s.replace(CID1+'/attempt-1',a.campaign+'/attempt-1').replace("'"+CID1+"'","'"+a.campaign+"'").replace('swdb-lanl17-20261007-a5-p1-a1',job)
  s=re.sub(r'\b511\b',str(generation),s);s=s.replace('generation511',f'generation{generation}').replace('released511',f'released{generation}').replace('not511',f'not{generation}')
  s=s.replace('lanl17-p1-',f'lanl17-{tag}-').replace('lanl17_read_p1_',f'lanl17_read_{tag}_').replace('Local p1-only',f'Local {tag}-only')
  s=s.replace('ee2d7bebe5a8003403a136b3fd8f62b1d72b743b6b47c1f8f97c4abb31ac53dd',d['identity_sha256'])
  return s
 observer=derive('observer').encode();reader=derive('reader').encode();author=derive('author')
 author=one(author,"DRAFT='"+SOURCES['draft'][2]+"'","DRAFT='"+sha(draft_bytes)+"'")
 author=one(author,"DSHA='7e63d49398eb8f8e2f0d9332b84c1350276acd5b50b9287b2d0b694ec565a6b4'","DSHA='"+sha(db)+"'")
 author=one(author,',32768,DRAFT,12307)',',32768,DRAFT,'+str(len(draft_bytes))+')')
 author=one(author,',65536,DSHA,44229)',',65536,DSHA,'+str(len(db))+')')
 author=author.replace(SOURCES['observer'][2],sha(observer));author=one(author,',32768,Q,15125)',',32768,Q,'+str(len(observer))+')');author=one(author,"'bytes':15125,'sha256':Q","'bytes':"+str(len(observer))+",'sha256':Q")
 author=one(author,"'"+SOURCES['reader'][2]+"',7926)","'"+sha(reader)+"',"+str(len(reader))+")")
 bodies={'observer':observer,'reader':reader,'author':author.encode(),'draft':draft_bytes}
 for k in ('observer','reader','author'):ast.parse(bodies[k].decode())
 # The shared p1-named M2 policy stays byte-for-byte equal in every applicable source.
 policy_literal=next(line for line in originals['reader'].decode().splitlines() if line.startswith('POLICY='));need(policy_literal in reader.decode(),'reader_global_policy_retained')
 diffs=[]
 for k in bodies:diffs.extend(difflib.unified_diff(originals[k].decode().splitlines(True),bodies[k].decode().splitlines(True),fromfile=str(BASE/SOURCES[k][0]),tofile=str(paths[k])))
 diffpath=BASE/f'lanl17-{tag}-release-source-derivation-20261008-a5.diff';diffbytes=''.join(diffs).encode()
 metapath=BASE/f'lanl17-{tag}-release-source-derivation-20261008-a5.json'
 metadata={'format':'swdb.lanl17-later-release-source-derivation.v1','source_only':True,'scientific_admission':False,'remote_or_controls_executed':False,'campaign':a.campaign,'attempt':1,'node':0,'generation':generation,'lane_exit_at_derivation':lane['exit_code'],'generation_not_inferred_from_dispatch_or_counter':True,'actual_inputs':[{'path':str(p),'bytes':row['size'],'sha256':h,'stat':row} for p,_,h,row in SEEN],'outputs':[{'path':str(paths[k]),'bytes':len(v),'sha256':sha(v)} for k,v in bodies.items()],'diff':{'path':str(diffpath),'bytes':len(diffbytes),'sha256':sha(diffbytes)},'fresh_live_checks_and_review_required_before_any_use':True,'source_staging_and_finalizer_execution_not_performed':True,'native_permissions_unchanged':True,'global_M2_policy_unchanged':True}
 all_outputs=[(paths[k],v) for k,v in bodies.items()]+[(diffpath,diffbytes),(metapath,(json.dumps(metadata,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode())]
 for path,_ in all_outputs:need(path.parent==BASE and not os.path.lexists(path),'fresh_private_outputs_required')
 for path,cap,h,s in list(SEEN):need(stamp(path.lstat())==s and sha(read(path,cap,h))==h,'inputs_changed_before_derivation')
 written=[output(path,v) for path,v in all_outputs];print(json.dumps({'source_only':True,'scientific_admission':False,'outputs':written},sort_keys=True))

if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,TypeError,OSError,IndexError,UnicodeError) as exc:
  print(json.dumps({'source_only_derivation_refused':True,'error_class':type(exc).__name__,'reason_sha256':sha(str(exc).encode()),'scientific_admission':False}),file=sys.stderr);raise SystemExit(2)
