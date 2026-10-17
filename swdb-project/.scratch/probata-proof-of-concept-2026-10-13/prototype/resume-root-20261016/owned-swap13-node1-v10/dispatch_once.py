"""2026-10-16 ET. Local exact root-once-admitted public13 sparse/node1 dispatch.

No cleanup or deletion. Preflight is read-only; the exact reviewed V10 creates
one fresh isolated sparse clone and dispatches the bounded job via socket lane.
"""
from pathlib import Path
import datetime,hashlib,json,subprocess,time

HERE=Path(__file__).resolve().parent
POC=HERE.parents[2]
EV=POC/'evidence'
PREFIX='t25-owned-swap13-sparse-v10-node1-'
SSH=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10','mbit10']


def pin(path):
    b=path.read_bytes();return {'path':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}


def save(name,value):
    p=EV/(PREFIX+name+'-20261016.json')
    with p.open('xb')as stream:stream.write((json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode())
    return p


def invoke(name,argv,stdin=None,timeout=60,cap=2*1024**2):
    clock=time.monotonic();started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        p=subprocess.run(argv,input=stdin,capture_output=True,timeout=timeout)
        code=p.returncode;out=p.stdout;err=p.stderr;uncertain=False
    except subprocess.TimeoutExpired as exc:
        code=None;out=exc.stdout or b'';err=exc.stderr or b'';uncertain=True
    op=EV/(PREFIX+name+'-stdout-20261016.json');ep=EV/(PREFIX+name+'-stderr-20261016.txt')
    for path,raw in [(op,out),(ep,err)]:
        with path.open('xb')as stream:stream.write(raw)
    receipt={'started_utc':started,'elapsed_seconds':time.monotonic()-clock,'argv':argv,
             'stdin_sha256':hashlib.sha256(stdin).hexdigest()if stdin is not None else None,
             'exit_code':code,'uncertain_transport_result':uncertain,'stdout':pin(op),'stderr':pin(ep),
             'within_output_cap':len(out)<=cap and len(err)<=262144}
    save(name+'-invocation',receipt)
    if not receipt['within_output_cap']:raise ValueError('bounded dispatch metadata cap exceeded')
    return receipt,out


def main():
    admission=EV/'t25-owned-swap13-sparse-v10-node1-root-once-admission-20261016.json'
    assert pin(admission)['sha256']=='a39075896fdd70b8862bc1abf674c5863cfd39927c0e782b35c545ce45593340'
    adm=json.loads(admission.read_bytes())
    for key in ('argv','launcher','node1_compatibility','prior_science_admission','source_review',
                'sparse_independent_spec','sparse_packet','sparse_root_standards','unchanged_entry',
                'unchanged_expected','unchanged_inner_command'):
        row=adm[key];assert pin(Path(row['path']))==row
    packet=json.loads(Path(adm['sparse_packet']['path']).read_bytes())
    for row in packet['inputs']+packet['files']:assert pin(Path(row['path']))==row
    argv=json.loads((HERE/'node1-argv.json').read_bytes())['argv']
    assert argv[6]=='1' and argv[5]=='2800' and len(argv)==9
    check=b'''import json,os,subprocess,datetime
from pathlib import Path
env={'HOME':'/nonexistent','PATH':'/usr/bin:/bin','LC_ALL':'C','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
def call(argv):return subprocess.check_output(argv,text=True,timeout=15,env=env).strip()
r={'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'uptime':call(['/usr/bin/uptime']),'disk':call(['/usr/bin/df','-B1','/data1','/data']),'memory':{},'leases':{},'sources':{},'new_source_path_exists':os.path.lexists('/data1/yanruj/probata-resume-20261016-a102e275'),'retained1433_source_exists':Path('/data1/yanruj/probata-resume-20261016-1433b8f5').is_dir()}
for line in Path('/proc/meminfo').read_text().splitlines():
 key,_,tail=line.partition(':')
 if key in ('MemTotal','MemAvailable'):r['memory'][key+'_bytes']=int(tail.split()[0])*1024
for name in ('mbit10-evaluation','mbit10-evaluation-node0','mbit10-evaluation-node1'):
 p=Path('/data1/yanruj/lact-host-lease')/(name+'.meta.json');v=json.loads(p.read_bytes());r['leases'][name]={'state':v['state'],'lease':v.get('lease')}
for name in ('ArchEvolve','probata-resume-20261016-1433b8f5','probata-resume-20261016-2baf722f'):
 root=Path('/data1/yanruj')/name;a=['/usr/bin/git','--no-optional-locks','--no-replace-objects','-c','core.fsmonitor=false','-c','core.preloadIndex=false','-c','index.threads=1','-C',str(root)];r['sources'][str(root)]={'branch':call(a+['rev-parse','--abbrev-ref','HEAD']),'commit':call(a+['rev-parse','HEAD'])}
print(json.dumps(r,sort_keys=True))
'''
    pre,out=invoke('fresh-preflight',[*SSH,'/usr/bin/timeout','--signal=TERM','--kill-after=5s','60s','/usr/bin/env','-i','HOME=/nonexistent','PATH=/usr/bin:/bin','LANG=C','LC_ALL=C','/usr/bin/python3','-I','-B','-'],check,75,65536)
    assert pre['exit_code']==0
    fresh=json.loads(out)
    assert fresh['leases']['mbit10-evaluation-node1']['state']=='released'
    assert fresh['leases']['mbit10-evaluation']['state']=='released'
    assert fresh['memory']['MemAvailable_bytes']>=9*1024**3
    assert not fresh['new_source_path_exists']and fresh['retained1433_source_exists']
    save('actual-dispatch-attempt',{'date':'2026-10-16 ET','admission':pin(admission),
        'argv':adm['argv'],'fresh_preflight':pre,'once_only':True,
        'protected_startup_window_coordinated_with_ticket25_and_ticket28':True})
    dispatched,out=invoke('launcher-dispatch',argv,timeout=240,cap=2*1024**2)
    observed=json.loads(out)if dispatched['exit_code']==0 and out else {}
    report={'date':'2026-10-16 ET','classification':'DISPATCHED_PENDING_ACTUAL_SETTLEMENT'if dispatched['exit_code']==0 else 'REFUSED_OR_UNCERTAIN_NO_AUTOMATIC_RETRY',
            'admission':pin(admission),'fresh_preflight':pre,'launcher_dispatch':dispatched,
            'reported_session':observed.get('session'),'reported_raw_root':observed.get('output'),
            'lane':1,'source_commit':adm['source_commit'],'actual_complete':False,
            'proof_scientific_source_Heap_Typed_caller_or_ticket_admission':False,
            'cleanup_or_deletion_attempted':False,'original1433_preserved_by_protocol':True}
    path=save('dispatch-execution',report);print(json.dumps(pin(path)))
    return 0 if dispatched['exit_code']==0 else 1


if __name__=='__main__':raise SystemExit(main())
