import json,subprocess,hashlib,stat,os
from pathlib import Path
r=Path('/data1/yanruj/Memacc-evolveswdb-lane')
env={'HOME':'/nonexistent','PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
def git(*a):return subprocess.check_output(['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-C',str(r),*a],env=env,timeout=10)
rows=[]
for rel in ('AgenticRefiner/scripts/host/socket_lane.sh','AgenticRefiner/scripts/host/hostlock.sh'):
 p=r/rel;s=p.lstat();assert stat.S_ISREG(s.st_mode)and s.st_size<=1048576;b=p.read_bytes();f=git('show','FETCH_HEAD:'+rel);h=git('show','HEAD:'+rel)
 rows.append({'relative':rel,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'matches_FETCH_HEAD':b==f,'matches_HEAD':b==h})
print(json.dumps({'head':git('rev-parse','HEAD').decode().strip(),'branch':git('rev-parse','--abbrev-ref','HEAD').decode().strip(),'fetch_head':git('rev-parse','FETCH_HEAD').decode().strip(),'selected_status':git('status','--porcelain','--',*[x['relative']for x in rows]).decode().strip(),'scripts':rows,'target_absent':{str(p):not os.path.lexists(p)for p in [Path('/data1/yanruj/probata-resume-20261016-abb598a4'),Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-abb598a4-t25-owned-swap-header3-public-v1')]}}))
