from pathlib import Path
import json,hashlib
root=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-36266e10-owned-source9-layout8-public-v2/owned-source9-layout-public-v2-profile/leaf-move.destination_header')
r={'files':{}}
for p in sorted(root.iterdir()):
 if p.is_file():
  raw=p.read_bytes(); row={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
  if p.name in ('frama-c.log','command.json','resources.json','outcome.json') and len(raw)<65536:row['text']=raw.decode()
  r['files'][p.name]=row
print(json.dumps(r,sort_keys=True))
