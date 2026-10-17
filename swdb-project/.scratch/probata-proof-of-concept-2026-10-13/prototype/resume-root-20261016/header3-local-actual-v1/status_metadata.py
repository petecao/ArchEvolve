"""2026-10-16 ET. Bounded read-only actual13 status; no raw source/SMT export."""
import datetime,hashlib,json,os,stat,subprocess
from pathlib import Path

RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-abb598a4-t25-owned-swap-header3-public-v1')
PROFILE=RAW/'owned-swap-header3-public-v1-profile'
SOURCE=Path('/data1/yanruj/probata-resume-20261016-abb598a4')


def metadata(path,cap=2*1024**2):
    if not os.path.lexists(path):return None
    st=path.lstat()
    if not stat.S_ISREG(st.st_mode)or st.st_size>cap:raise ValueError('bounded regular status metadata required')
    raw=path.read_bytes();after=path.lstat()
    if (st.st_ino,st.st_size,st.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):
        return {'status_read_in_progress':True}
    try:return json.loads(raw)
    except ValueError:return {'status_JSON_not_settled':True,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


env={'HOME':'/nonexistent','PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
def command(args):return subprocess.check_output(args,text=True,timeout=15,env=env).strip()
r={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw_root':str(RAW),
   'uptime':command(['/usr/bin/uptime']),'disks':command(['/usr/bin/df','-B1','/data1','/data']),
   'leases':{},'source':{},'raw_exists':RAW.is_dir(),'profile_exists':PROFILE.is_dir()}
for name in ('mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1'):
    value=metadata(Path('/data1/yanruj/lact-host-lease')/(name+'.meta.json'))
    r['leases'][name]={key:value.get(key)for key in ('state','lease')}
if SOURCE.is_dir():
    git=['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-c','core.preloadIndex=false','-c','index.threads=1','-C',str(SOURCE)]
    r['source']={'branch':command(git+['rev-parse','--abbrev-ref','HEAD']),
                 'commit':command(git+['rev-parse','HEAD']),
                 'clean':not command(git+['status','--porcelain','--untracked-files=all','--ignored']),
                 'private_git_directory':(SOURCE/'.git').is_dir(),
                 'retained1433_source_exists':Path('/data1/yanruj/probata-resume-20261016-1433b8f5').is_dir()}
for name in ('lane.json','resources.json','outer-resources.json','source-after.json'):
    r[name]=metadata(RAW/name)
launch=metadata(RAW/'launch.json')
if isinstance(launch,dict):r['launch']={k:launch.get(k)for k in ('node','source','source_commit','rss_cap_bytes','workers','timeout_seconds','planned_raw_budget_bytes')}
pre=metadata(RAW/'preflight.json')
if isinstance(pre,dict):r['source_checkout']=pre.get('source_checkout');r['wrapper']=pre.get('wrapper')
method=metadata(PROFILE/'method.json')
if isinstance(method,dict):r['method_flags']=method.get('flags')
result=metadata(PROFILE/'result.json')
if isinstance(result,dict):
    r['result']={k:result.get(k)for k in ('producer_complete','all_three_producer_proven','error_type','error','primary_error','unexecuted','elapsed_seconds','within_profile_budget','classification')}
    r['result']['runs']=[{'id':q['id'],'verdict':q['outcome'].get('verdict'),'failure_class':q['outcome'].get('failure_class'),
                         'ordinary_goals':q['ordinary_goals'],'smoke_goals':q['smoke_goals'],
                         'resources':q['resources']}for q in result.get('runs',[])]
r['profile_entry_directories']=sorted(p.name for p in PROFILE.glob('leaf-*')if p.is_dir())if PROFILE.is_dir()else[]
print(json.dumps(r,sort_keys=True))
