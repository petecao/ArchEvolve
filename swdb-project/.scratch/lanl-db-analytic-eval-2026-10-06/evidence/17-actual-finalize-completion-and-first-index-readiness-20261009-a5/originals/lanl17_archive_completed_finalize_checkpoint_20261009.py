"""2026-10-09 ET: exact local compact-evidence archive; no remote activity."""
from pathlib import Path
import os,json,hashlib,stat,datetime
from zoneinfo import ZoneInfo
ROOT=Path('/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-actual-finalize-completion-and-first-index-readiness-20261009-a5')
F=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
def exact(p):
 s=p.lstat();assert p.resolve(strict=True)==p and not any(x.is_symlink() for x in (p,*p.parents)) and stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid() and s.st_nlink==1
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  assert os.fstat(f.fileno())==s;b=f.read();assert os.fstat(f.fileno())==p.lstat()==s
 return b,{k:getattr(s,'st_'+k) for k in F}
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b;return
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
files=[]
for name,names in [('lanl17-scientific-finalize-capture-20261008-a5-a1',['start.json','stdin.py','stdout','stderr','transport.json']),('lanl17-finalize-terminal-prerequisite-capture-20261008-2359-a5',['start.json','stdin.py','stdout','stderr','transport.json','preregistration.json','supervisor-receipt.json']),('lanl17-finalize-progress-capture-r3-20261009-0000-a5',['start.json','stdin.py','stdout','stderr','transport.json','progress-original.json']),('lanl17-finalize-completion-capture-20261009-0000-a5-a1',['start.json','stdin.py','stdout','stderr','transport.json','completion-original.json'])]:
 files.extend(Path('/private/tmp')/name/x for x in names)
decoded=Path('/private/tmp/lanl17-finalize-completion-decoded-originals-20261009-0001-a5-a1');files.extend(p for p in decoded.rglob('*') if p.is_file())
for name in ['lanl17-finalize-terminal-prerequisite-collect-config-20261008-2359-a5.json','lanl17-finalize-completion-action-20261009-0000-a5-a1.json','lanl17-finalize-completion-root-semantic-review-20261009-0003-a5.json','lanl17-finalize-parent-terminal-and-prerequisite-independent-actual-review-20261009-a5-r1.json','lanl17-finalize-completion-originals-independent-semantic-review-20261009-a5-r1.json','lanl17-actual-pre-full-index-seven-key-authoring-parent-plan-20261009-a5.md','lanl17-historical-catalog-continuity-evidence-basis-20261009-a5.md','lanl17-historical-catalog-continuity-evidence-basis-20261009-a5.json','lanl17_build_actual_p1_pre_index_input_20261009.py','lanl17_build_actual_p1_pre_index_input_20261009_r2.py','lanl17-p1-pre-full-index-host-input-actual-20261009-a5-a1.json','lanl17-p1-pre-full-index-host-action-actual-20261009-a5-a1.json','lanl17-p1-pre-full-index-host-input-actual-20261009-a5-a2.json','lanl17-p1-pre-full-index-host-action-actual-20261009-a5-a2.json']:
 files.append(Path('/private/tmp')/name)
ROOT.mkdir(parents=True,exist_ok=True);rows=[]
for p in sorted(set(files)):
 b,s=exact(p);out=ROOT/'originals'/p.relative_to('/private/tmp');save(out,b);assert exact(p)==(b,s)
 rows.append({'archive':str(out.relative_to(ROOT)),'original':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'original_stat':s})
inv={'date_ET':datetime.datetime.now(datetime.timezone.utc).astimezone(ZoneInfo('America/New_York')).strftime('%Y-%m-%d %H:%M ET'),'originals':rows,'scientific_admission':False};b=(json.dumps(inv,sort_keys=True,indent=2)+'\n').encode();save(ROOT/'completed-finalize-original-inventory.json',b)
print(json.dumps({'files':len(rows),'bytes':sum(x['bytes'] for x in rows),'inventory':str(ROOT/'completed-finalize-original-inventory.json')}))
