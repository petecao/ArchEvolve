from pathlib import Path
import ast,hashlib,json,re,subprocess
repo=Path('/private/tmp/probata-resume-t07-private-array');tip='b9b96fb85573c0292d2f7171b984cd2ee4076443';base='swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/';ep='swdb-project/.scratch/probata-proof-of-concept-2026-10-13/evidence/t07-canonical-generation-preparation-20261016.json';H=lambda b:hashlib.sha256(b).hexdigest()
def blob(p,c=tip):return subprocess.check_output(['git','show',c+':'+p],cwd=repo)
e=json.loads(blob(ep));manifest=Path(e['raw_manifest']['path']);assert H(manifest.read_bytes())==e['raw_manifest']['sha256'];m=json.loads(manifest.read_bytes());counts={}
for x in m['artifacts']:
 p=Path(x['path']);assert H(p.read_bytes())==x['sha256'] and p.stat().st_size==x['bytes'],str(p)
counts['artifacts']=len(m['artifacts'])
for x in e['sources']:assert H(blob(x['path']))==x['sha256']
files=subprocess.check_output(['git','ls-tree','-r','--name-only',tip],cwd=repo).decode().splitlines();out=[];historical=[]
for prefix in ['standin_outslot','standin_private_array']:
 for p in files:
  if p.startswith(base+prefix+'/'):
   assert blob(p)==blob(p,'e97fb191');historical.append(p)
 for p in files:
  if p.startswith(base+prefix+'_canonical/') and p.endswith(('.c','.h')):
   old=p.replace(prefix+'_canonical/',prefix+'/');data=blob(old);new=blob(p);expected=b'\n'.join(x.rstrip(b' \t') for x in data.split(b'\n'));assert expected==new and new.count(b'\n')==data.count(b'\n') and not re.search(rb'[ \t]+\n',new);out.append({'path':p,'old_sha256':H(data),'sha256':H(new),'lines':new.count(b'\n')})
assert len(out)==18
packetpath=Path('/private/tmp/probata-t07-private-array-generation-packet-v2-20261016.json');packet=json.loads(packetpath.read_bytes());assert H(packetpath.read_bytes())=='880b57fc296e464a8b52699e299234abe5ec78d035b96d2d874c0919bb595724'
for x in packet['files']:assert H(Path(x['path']).read_bytes())==x['sha256'] and Path(x['path']).stat().st_size==x['bytes']
expectedpath=Path('/private/tmp/probata-t07-private-array-generation-expected-v2-20261016.json');ex=json.loads(expectedpath.read_bytes());entry=Path('/private/tmp/probata-t07-private-array-generation-entry-v2-20261016.py');ast.parse(entry.read_bytes());assert ex['source_commit']==tip and len(ex['source_blobs'])==31
for x in ex['source_blobs']:
 b=blob(x['relative']);assert H(b)==x['sha256'] and len(b)==x['bytes'];bid=subprocess.check_output(['git','rev-parse',tip+':'+x['relative']],cwd=repo).decode().strip();assert bid==x['git_blob']
# Runtime physical surface/absence checks as data, no selected tool execution.
physical=0
for x in [*ex['tools'].values(),ex['python'],*ex['toolchain_artifacts'],*ex['configuration_files'],*ex['external_pins']]:
 p=Path(x['path'])
 if x.get('absent'):assert not p.exists()
 else:assert str(p.resolve())==x['resolved'] and H(p.read_bytes())==x['sha256'];physical+=1
for t in [ex['standard_headers'],ex['psutil_surface'],*ex['package_surfaces']]:
 root=Path(t['path']);wanted={x['relative'] for x in t['files']}
 if 'frama-c/share/libc' in str(root):found={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
 elif root.name=='psutil':found={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.suffix in ['.py','.so']}
 else:found={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and (p.suffix in ['.cmi','.cmx','.cmxa','.cmxs','.a'] or p.name=='META')}
 assert found==wanted
 for x in t['files']:p=Path(x['path']);assert str(p.resolve())==x['resolved'] and H(p.read_bytes())==x['sha256'];physical+=1
header=blob(ex['header_relative']).decode();strip=lambda s:re.sub(r'/\*.*?\*/|//[^\n]*','',s,flags=re.S)
def defs(s):return [x for x in re.findall(r'\b(\w+)\s*\([^;{}]*\)\s*\{',strip(s)) if x not in ['if','for','while','switch']]
assert sorted(defs(header))==sorted(ex['header_helpers']) and len(ex['header_helpers'])==20
for c in ex['cases']:
 s=blob(c['site_relative']).decode();assert sorted(defs(s))==sorted(c['root_functions']) and len(c['helpers'])==20+len(c['root_functions']);assert set(c['helpers'])==set(ex['header_helpers'])|set(c['root_functions'])
 for x in c['intended_read_anchors']:assert s.splitlines()[x['line']-1].strip()==x['text'] and H(s.splitlines()[x['line']-1].encode())==x['line_sha256']
 assert len(c['direct_bodyless_call_contexts'])==3
 for x in c['all_direct_call_contexts']:
  text=header if x['source_file']=='gapbs_models.h' else s;assert H(text.splitlines()[x['line']-1].encode())==x['line_sha256']
assert len(ex['cases'])==10
staticdir=Path('/private/tmp/probata-t07-private-array-generation-static-controls-final-20261016');controls=json.loads((staticdir/'controls.json').read_bytes());assert len(controls['records'])==31 and all(x['passed'] for x in controls['records'])
v={'source':tip,'canonical_evidence_sha256':H(blob(ep)),'canonical_raw_manifest_sha256':H(manifest.read_bytes()),'canonical_manifest_groups':counts,'canonical_source_payloads':out,'historical_files_unchanged':len(historical),'canonical_checks_reported':e['controls']['passed'],'generation_packet_sha256':H(packetpath.read_bytes()),'generation_packet_files':packet['files'],'git_blobs_checked':31,'runtime_physical_reference_instances_checked':physical,'cases':[{k:c[k] for k in ['name','root_functions','helpers','intended_read_anchors']} for c in ex['cases']],'static_control_records':31,'hash_errors':[],'actual_tools_or_entry_executed_by_reviewer':False}
p=Path('/private/tmp/probata-t07-canonical-generation-passive-data-v2-b9b96fb8-20261016.json');p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps({k:x for k,x in v.items() if k not in ['cases','canonical_source_payloads','generation_packet_files']},indent=2))
