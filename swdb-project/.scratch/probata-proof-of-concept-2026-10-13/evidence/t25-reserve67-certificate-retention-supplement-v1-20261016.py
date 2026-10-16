"""2026-10-16 ET. Passive certificate/report-reference supplement; no project import."""
from pathlib import Path
import ast,datetime,hashlib,json,subprocess,time


def main():
 started=time.monotonic();source=Path('/data1/yanruj/probata-resume-20261016-c978393b');project=source/'swdb-project'
 raw=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-c978393b-t25-qualified-reserve67-public-v1');profile=raw/'qualified-reserve67-profile'
 J=lambda p:json.loads(Path(p).read_bytes());H=lambda b:hashlib.sha256(b).hexdigest()
 D=lambda v:H(json.dumps(v,sort_keys=True,separators=(',',':')).encode())
 checks=0
 def require(value,label):
  nonlocal checks
  if not value:raise ValueError(label)
  checks+=1
 def pin(p):
  p=Path(p);before=p.stat()
  with p.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
  after=p.stat();require((before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino),'stable input')
  return {'path':str(p),'bytes':before.st_size,'sha256':h}
 record=J(profile/'public.stdout')['record'];settings=record['settings'];runs=settings['heap_model_runs'];wp=Path(runs[0]['cwd']).parent
 view_path=wp/'heap-model-view.json';view=J(view_path);viewpin=pin(view_path)
 require(view==settings['heap_model_view'],'retained/public complete certificate equality')
 require(record['pins']['heap_model_view_certificate']=={'id':'qualified-vector-heap-certificate-1','sha256':D(view)},'reconstructed certificate digest')
 text=(project/'swdb/vector_reallocation_view.py').read_text();tree=ast.parse(text);identity=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='identity')
 names=ast.literal_eval(next(n.value for n in identity.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='names'for t in n.targets)))
 rows=[{'path':n,'sha256':pin(project/'swdb'/n)['sha256']}for n in names]
 require(record['pins']['heap_model_view_check']=={'id':'qualified-vector-heap-view-1','sha256':D(rows)},'independently reconstructed qualified view checker')
 for r in record['proof_setup_check']['runs']:
  require(r['hashes']['heap-model-view.json']==viewpin['sha256']and r['hashes']['heap_model_view']==D(view),'each actual setup certificate physical/semantic pin')
 e=J(profile/'expected.json');canonical=J(profile/'canonical-inputs/manifest.json')
 groups={g for r in canonical['obligations']for g in r['source_groups']};require(groups=={f'G{i}'for i in range(1,10)}|{'R1','R2','R3'},'complete G1-G9/R1-R3 reserve source groups')
 ids={r['id']for r in canonical['obligations']};require(all(r['obligations']and set(r['obligations'])<=ids for r in canonical['source_inventory']['events']),'every actual source event has current target owners')
 require(view['source_groups']==view['required_source_groups']==sorted(groups),'source certificate coverage groups')
 require(view['original_caller_premises_added']==[]and view['generic_caller_composition']=='unsupported','no caller premise or composition promotion')
 model_source=(project/'swdb/vector_reallocation_model.py').read_text();modeltree=ast.parse(model_source)
 domain=ast.literal_eval(next(n.value for n in modeltree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='DOMAIN'for t in n.targets)))
 qualified=(profile/'canonical-inputs/qualified.c').read_text();original=(profile/'canonical-inputs/original.c').read_text();restored=qualified.replace('\n'+domain,'',1)
 for member in ('ctor_count_value','grow','reserve','dtor'):restored=restored.replace('std_vector_int_realloc_v3_'+member+'(','std_vector_int_'+member+'(')
 restored=restored.replace('requires std_vector_int_reallocatable_v3(this)','requires std_vector_int_valid(this)').replace('ensures std_vector_int_reallocatable_v3(this)','ensures std_vector_int_valid(this)')
 require(restored==original,'entire inverse-qualified original source restored')
 q=view['qualification'];require(q['original_contract_proved']is False and q['qualified_source_sha256']==H(qualified.encode())and q['original_source_sha256']==q['inverse_qualified_source_sha256']==H(original.encode()),'qualification source boundaries')
 old_body=original.split('static void std_vector_int_reserve(',1)[1].split('{',1)[1];new_body=qualified.split('static void std_vector_int_realloc_v3_reserve(',1)[1].split('{',1)[1]
 for member in ('ctor_count_value','grow','reserve','dtor'):new_body=new_body.replace('std_vector_int_realloc_v3_'+member+'(','std_vector_int_'+member+'(')
 require(old_body==new_body and q['body_sha256']==H(old_body.encode()),'exact executable reserve body unchanged by qualification')
 reports=[record['evidence']['adapter_log'],*record['evidence']['reports']];references=[]
 for row in reports:
  p=Path(row['path']);require(p.is_relative_to(raw)and not p.is_symlink()and p.is_file(),'contained regular evidence reference');actual=pin(p);require(actual['sha256']==row['sha256'],'physical persisted report reference');references.append(actual)
 require(len(references)==10*len(runs)+41,'all retained record evidence references')
 foundation=settings['heap_model_foundations'];require(record['pins']['heap_model_foundations']=={'id':'heap-model-standard-foundations-1','sha256':D(foundation['sources'])},'foundation semantic pin')
 require(pin(wp/'heap-environment/heap_model_environment.ml')['sha256']==foundation['metadata_source_sha256'],'retained environment-helper source pin')
 require(pin(foundation['metadata_executable'])['sha256']==foundation['metadata_executable_sha256'],'retained environment-helper executable pin')
 reader=pin(wp/'heap-reader/proof_report.ml');require(reader['sha256']==pin(project/'swdb/proof_report.ml')['sha256'],'retained/current reader source equality')
 require(any('-load-module'in r['command']and r['command'][r['command'].index('-load-module')+1]==str(wp/'heap-reader/proof_report.cmxs')for r in runs),'actual selected compiled reporter command')
 reporter_binaries=[pin(wp/'heap-reader'/name)for name in ['proof_report.cmi','proof_report.cmx','proof_report.o','proof_report.cmxs']]
 require(len({r['command'][r['command'].index('-load-module')+1]for r in runs})==1,'all runs use same retained native reporter')
 known_refs={D(r)for r in [record['pins']['heap_model_view_check'],record['pins']['heap_model_foundations'],record['pins']['vector_reallocation_model']]}
 runtime=J(profile/'heap-project-runtime-provenance.json');known_refs.add(D(runtime['lowering_identity']['c_lowering']))
 for r in e['tools'].values():known_refs.add(D({'id':r.get('id'),'sha256':r['sha256']}))
 # IDs for the selected native tools are declared in the persisted source method;
 # their hashes must come from the independently checked exact runtime pins.
 permitted_hashes={r['sha256']for r in e['tools'].values()}|{e['linux_clang_components']['command_executable']['sha256']}|{r['sha256']for r in [record['pins']['heap_model_view_check'],record['pins']['heap_model_foundations'],record['pins']['vector_reallocation_model'],runtime['lowering_identity']['c_lowering']]}
 require(len(record['assumptions'])==9 and all(r['kind']=='trusted_tool'and r['reference']['sha256']in permitted_hashes for r in record['assumptions']),'all9 TCB assumptions bind selected tool/view/model/foundation hashes')
 require(not(source/'swdb-project/records/.retention.lock').exists(),'no unexpected source retention writer')
 leases={p.name:J(p)for p in Path('/data1/yanruj/lact-host-lease').glob('mbit10-evaluation*.meta.json')}
 require(subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(source),'rev-parse','HEAD'],text=True).strip()=='c978393b119a3614229a37f0f2c8ca2a097c750b','source retained at exact producer SHA')
 require(not subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(source),'status','--porcelain','--untracked-files=all'],text=True),'source still clean')
 return {'created':'2026-10-16 ET','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':checks,'wall_seconds':time.monotonic()-started,'complete_certificate_reconstructed':True,'certificate':viewpin,'qualified_view_checker':record['pins']['heap_model_view_check'],'source_groups':sorted(groups),'source_events':len(canonical['source_inventory']['events']),'entire_original_source_inverse_equal':True,'qualification_keeps_executable_reserve_body_equal':True,'record_evidence_references':len(references),'record_reference_pin_digest':D(references),'retained_reader_source':reader,'retained_reporter_binaries':reporter_binaries,'all9_explicit_TCB_assumptions_selected_hash_bound':True,'lease_snapshot':leases,'actual_typed_AST_correspondence_or_submitted_bytes_proved':False,'scope':'Additional certificate/reference retention binding only; no compiler, helper/native reporter, project reader, test or solver executed.'}


if __name__=='__main__':
 try:print(json.dumps(main(),sort_keys=True,indent=2))
 except Exception as error:
  print(json.dumps({'classification':'REFUSED_CERTIFICATE_SUPPLEMENT','error':str(error),'acceptance':False}));raise SystemExit(1)
