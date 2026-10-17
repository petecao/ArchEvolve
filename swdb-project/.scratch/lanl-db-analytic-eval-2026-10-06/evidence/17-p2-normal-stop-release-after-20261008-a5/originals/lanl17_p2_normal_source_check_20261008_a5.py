import datetime,json,os,subprocess,socket
from pathlib import Path
assert socket.gethostname().split('.')[0]=='mbit10' and os.getuid()==os.geteuid()==114316761
R='5e12a9796432654d88def24ecea617d16ca605b2'
def run(argv):
 p=subprocess.run(argv,capture_output=True,timeout=15,env={'PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_OPTIONAL_LOCKS':'0'});assert p.returncode==0 and len(p.stdout)<=65536;return p.stdout.decode()
S='/data1/yanruj/ArchEvolve-lanl17-source-20261007-a5';PRIMARY='/data1/yanruj/ArchEvolve'
source={p:{'head':run(['/usr/bin/git','-C',p,'rev-parse','HEAD']).strip(),'status':run(['/usr/bin/git','-C',p,'status','--porcelain'])} for p in (S,PRIMARY)}
assert all(v['head']==R for v in source.values()) and source[S]['status']==''
origin=run(['/usr/bin/git','-C',PRIMARY,'rev-parse','origin/yanrujhou_main']).strip();assert origin==R
print(json.dumps({'format':'swdb.lanl17-p2-normal-source-readonly.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':source,'primary_origin':origin,'scientific_admission':False},sort_keys=True))
