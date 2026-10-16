"""Passive settled native profile cold audit, 2026-10-16 ET; executes no input."""
from pathlib import Path
import hashlib,json,shlex,stat
BASE=Path('/private/tmp/probata-t07-omp-profile-native-v3-20261016');C=BASE/'component'
OUT=Path('/private/tmp/probata-t07-omp-profile-cold-v3-20261016.json')
def H(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
checks=[];pins=[]
def need(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def pin(r):
 p=Path(r['path']);need('physical:'+str(p),p.stat().st_size==r['bytes'] and H(p)==r['sha256'])
 if 'resolved' in r:need('resolved:'+str(p),str(p.resolve())==r['resolved'])
 pins.append({'path':str(p),'bytes':p.stat().st_size,'sha256':H(p)})
rootpath=Path('/private/tmp/probata-root-t07-omp-profile-native-execution-v3-20261016.json');need('root-receipt-identity',H(rootpath)=='b867d8ac9fe19687ee82a5088629e080802e0c12f185447db62d81d6f719089f10');root=load(rootpath)
for r in root['physical_files']:pin(r)
actual=[]
for p in BASE.rglob('*'):
 st=p.lstat()
 if stat.S_ISREG(st.st_mode):actual.append(str(p))
 else:need('only-directory-special:'+str(p),stat.S_ISDIR(st.st_mode))
need('full20-raw-membership',set(actual)=={r['path'] for r in root['physical_files']} and len(actual)==20)
g=load(BASE/'root-native.guard.log.summary.json');need('guard-root-equality',g==root['guard']);need('healthy-guard',g['exit_code']==0 and not any(g[k] for k in ['timed_out','queue_timed_out','killed_by_watchdog','inspection_events','unconfirmed_children']) and all(g[k] is None for k in ['inspection_failure','cleanup_inspection_failure','primary_inspection_failure','error']))
e=load(C/'expected.json');packet=load('/private/tmp/probata-t07-omp-profile-native-v3-20261016-packet.json')
for r in packet['files']:pin(r)
need('exact-admitted-expected',H(C/'expected.json')==H('/private/tmp/probata-t07-omp-profile-native-v3-20261016-expected.json'))
need('exact-admitted-entry',H(C/'entry.py')==H('/private/tmp/probata-t07-omp-profile-native-v3-20261016-entry.py'))
for r in [*e['tools'].values(),e['compiler_load_context'],*e['compiler_implementation_images'],e['source'],e['trace'],e['helper_scope_decision'],e['selected_include_closure_receipt'],*e['compile_input_whitelist'],*e['selected_source_files']]:pin(r)
need('903-compile-inputs-23-source-files-five-compiler-images',len(e['compile_input_whitelist'])==903 and len(e['selected_source_files'])==23 and len(e['compiler_implementation_images'])==5)
obs=load(C/'observations.json');need('root-observations',obs==root['observations'])
for name,n in [('one',1),('two_negative',2)]:
 row=obs[name];need('exact-env-'+name,row['environment']=={'OMP_THREAD_LIMIT':str(n),'OMP_NUM_THREADS':str(n),'OMP_DYNAMIC':'FALSE'})
 values={'outside_threads':1,'thread_limit':n,'max_threads':n,'dynamic':0,'entries':n,'team_min':n,'team_max':n,'id_min':0,'id_max':n-1,'zero_ids':1,'level_min':1,'level_max':1,'int_bytes':4,'size_t_bytes':8,'openmp_macro':202011}
 o=row['observation'];need('exact-observation-'+name,set(o)=={*values,'libomp_path'} and all(type(o[k]) is int and o[k]==v for k,v in values.items()) and str(Path(o['libomp_path']).resolve())==e['tools']['libomp']['resolved'])
 need('raw-observation-'+name,load(C/('profile-'+name+'.stdout'))==o and (C/('profile-'+name+'.stderr')).stat().st_size==0)
need('negative-explicitly-validated-and-refused',obs['two_negative']['exact_two_thread_observation_validated'] is True and obs['two_negative']['selected_profile_refused'] is True)
commands=load(C/'commands.json');need('root-commands',commands==root['commands']);need('exact-three-calls',[r['label'] for r in commands]==['compile','profile-one','profile-two_negative'])
need('exact-compile-flags',commands[0]['argv']==[s.replace('@OUTPUT@',str(C)) for s in e['compiler_argv_template']]);need('remaining-shared-deadline',all(0<r['remaining_seconds']<=50 for r in commands) and all(a['remaining_seconds']>b['remaining_seconds'] for a,b in zip(commands,commands[1:])))
need('no-compile-diagnostics',all((C/('compile.'+suffix)).stat().st_size==0 for suffix in ['stdout','stderr']))
paths={str(Path(s).resolve()) for s in shlex.split((C/'includes.d').read_text().replace('\\\n',' ').split(':',1)[1])};allow={r['resolved']:r for r in e['compile_input_whitelist']};allow[str((C/'profile.cc').resolve())]=e['source'];closure=load(C/'actual-physical-include-closure.json')
need('129-exact-admitted-dependencies',len(paths)==129 and paths=={r['path'] for r in closure} and all(p in allow and H(p)==allow[p]['sha256'] for p in paths))
for r in closure:pin(r)
m=load(C/'manifest.json');need('component-manifest-complete',set(r['path'] for r in m)=={str(p.relative_to(C)) for p in C.rglob('*') if p.is_file()}-{'manifest.json','result.json'})
for r in m:pin({**r,'path':str(C/r['path'])})
result=load(C/'result.json');need('root-result',result==root['result']);need('all-native-gates',all(result[k] is True for k in ['runtime_installation_one_thread_observed','compiler_implementation_load_context_pinned','outside_printf_not_team_evidence_demonstrated','source_runtime_retained_unchanged','within_internal_deadline']) and result['actual_TD_execution_observed'] is False and result['source_allocator_lifetime_TD_count_accepted'] is False and 'error' not in result)
pins.append({'path':str(rootpath),'bytes':rootpath.stat().st_size,'sha256':H(rootpath)})
OUT.write_text(json.dumps({'scope':'PASS settled installation/profile only; no exact TD execution or proof','checks':len(checks),'pins':pins,'raw_files':20,'includes':129,'admitted_input_whitelist':903,'selected_sources':23,'compiler_images':5,'guard':{'wall_s':g['wall_s'],'peak_rss_mb':g['peak_rss_mb'],'exit_code':0,'inspection_events':[]},'profile':obs,'conditional_bridge':'standard typed-private-frame + selected compiler/runtime TCB, no machinechecked whole C++→C simulation or Init-reset fact','TD_or_counted_accepted':False},indent=2)+'\n');print(json.dumps({'pass':True,'checks':len(checks),'output':str(OUT),'sha256':H(OUT)}))
