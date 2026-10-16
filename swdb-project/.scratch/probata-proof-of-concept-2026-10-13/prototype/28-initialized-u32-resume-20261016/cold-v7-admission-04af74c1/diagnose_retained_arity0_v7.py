from pathlib import Path
import hashlib,json,sys,csv,io
BASE=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-cold-04af74c1-v7/control')
p=BASE/'initialized-cold-policy-04af74c1-v7.json';b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=='c1661a048f446d1bc62d468d364b25641b27c2f29a9613b838b630a62c0b90fb';policy=json.loads(b)
def deny(event,args):
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.','ctypes.dlopen')) or event in {'os.system','os.remove','os.rename','os.mkdir','os.rmdir'}:raise RuntimeError('passive inventory diagnostic refuses '+event)
 if event=='open':
  path,mode,flags=args
  if mode is not None and any(c in mode for c in 'wax+') or flags&(1|2|64|512|1024):raise RuntimeError('no writes')
sys.addaudithook(deny)
rows=[];raw=Path(policy['raw']);helpers={'init_MAA','get_new_reg_unsigned_int_args1','get_reg_unsigned_int'}
for record in policy['records']:
 matches=[(name,row) for name,row in policy['raw_manifest']['files'].items() if name.endswith('/wp/wp-inventory.json') and record['id'] in Path(name).parts]
 assert len(matches)==1
 name,pin=matches[0];f=raw/name;b=f.read_bytes();assert len(b)==pin['bytes'] and hashlib.sha256(b).hexdigest()==pin['sha256'];inv=json.loads(b)
 extern=[row for row in inv['properties'] if row['extern']]
 selected=[{key:row[key] for key in ('property','kind','function','description','source_file','line','emitter','origin','dependencies','status_registered','property_export_origin')} for row in extern]
 unexpected=[row for row in selected if row['kind']!='contract' or row['function'] not in helpers]
 unused=[p for p in inv['properties'] if p['function']=='get_new_reg_unsigned_int_args0']
 affected_goals=[g for g in inv['goals'] if g['function']=='get_new_reg_unsigned_int_args0' or g['property'] in {p['property'] for p in unused} or any(target in {p['property'] for p in unused} for target in g['targets'])]
 csvname=name[:-len('wp-inventory.json')]+'wp-properties.csv';csvpin=policy['raw_manifest']['files'][csvname];csvbytes=(raw/csvname).read_bytes();assert len(csvbytes)==csvpin['bytes'] and hashlib.sha256(csvbytes).hexdigest()==csvpin['sha256'];csvrows=list(csv.DictReader(io.StringIO(csvbytes.decode()),delimiter='\t'));unused_csv=[r for r in csvrows if r['function']=='get_new_reg_unsigned_int_args0']
 rows.append({'expected_result':record['expected_result'],'inventory_sha256':pin['sha256'],'properties':len(inv['properties']),'goals':len(inv['goals']),'Extern_properties':selected,'unexpected_Extern':unexpected,'unused_arity0_all_properties':unused,'unused_arity0_attached_goals':affected_goals,'unused_arity0_CSV':unused_csv,'property_kind_census':{kind:sum(row['kind']==kind for row in inv['properties']) for kind in sorted({row['kind'] for row in inv['properties']})}})
print(json.dumps({'classification':'PASSIVE_EXTERN_CLASSIFICATION_METADATA_ONLY','records':rows,'reader_audit_executed':False,'scientific_reexecution':False},indent=2,sort_keys=True))
