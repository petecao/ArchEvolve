"""2026-10-16 ET. Root-authorized public pure splitter RED/GREEN60s1GiB8MiB."""
from pathlib import Path
import dataclasses,hashlib,importlib.util,json,sys
import psutil
P=Path;phase=sys.argv[1];assert phase in {'red','green'}
PY=P('/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3.12');CONTROL=P('/private/tmp/probata-t07-device-index-controls-v3-20261016.py');WATCH=P('/private/tmp/probata-resume-t25-pair/swdb-project/swdb/rss_watchdog.py');OUT=P('/private/tmp/probata-t07-device-index-'+phase+'-v4-20261016')
def pin(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert not OUT.exists();OUT.mkdir();memory=psutil.virtual_memory();assert memory.available>=8*1024**3
pre={'date_ET':'2026-10-16','scope':__doc__,'phase':phase,'child':pin(CONTROL),'python':pin(PY),'watchdog':pin(WATCH),'available_bytes':memory.available,'B':False,'c6':False}
(OUT/'preflight.json').write_text(json.dumps(pre,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('ticket07_splitter_selected_rss',WATCH);watch=importlib.util.module_from_spec(spec);sys.modules[spec.name]=watch;spec.loader.exec_module(watch)
cmd=[str(PY),'-I','-B',str(CONTROL),phase,str(OUT/'control')]
r=watch.run(cmd,log=OUT/'control.log',cap_bytes=1024**3,timeout=60,cwd=P('/private/tmp'),env={'PATH':'/usr/bin:/bin','HOME':'/Users/yanrujhou','LANG':'C','LC_ALL':'C','PYTHONDONTWRITEBYTECODE':'1'})
res=dataclasses.asdict(r);res.update(command=cmd,child_unchanged=pin(CONTROL)==pre['child'],raw_bytes=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),B_used=False,c6_used=False)
(OUT/'resources.json').write_text(json.dumps(res,indent=2)+'\n')
assert r.exit_code==(1 if phase=='red' else 0) and not r.out_of_memory and not r.timed_out and res['child_unchanged'] and res['raw_bytes']<=8*1024**2
print(json.dumps({'resources':pin(OUT/'resources.json'),'receipt':pin(OUT/'control/receipt.json')}))
