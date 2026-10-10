"""Parent source/pin review only; no selected module or test execution."""
import ast, collections, datetime, difflib, hashlib, json, pathlib, platform, subprocess, sys
P=pathlib.Path
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(d):return sha(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
prep=P('/private/tmp/lanl14-lossless-gzip-source-preparation-20261007-a1.json')
raw=prep.read_bytes();assert len(raw)==12690 and sha(raw)=='f69ae7e30951885df805cd24ba90dcbb9ac741ad13d59ad0306d7299b18538a2'
d=json.loads(raw);assert d['canonical_ensure_ascii'] is True and digest({k:v for k,v in d.items() if k!='identity_sha256'})==d['identity_sha256']=='febc849346ccd751dea9aeecf49c6605864f748725946c82a67d8f6736df47ef'
allpins={**d['selected_packet_pins'],**d['preserved_originals_and_drafts']}
for pin in allpins.values():
 p=P(pin['path']);b=p.read_bytes();assert not p.is_symlink() and len(b)==pin['bytes'] and sha(b)==pin['sha256']
def data(role):return P(allpins[role]['path']).read_bytes()
def tree(role):return ast.parse(data(role))
def dump(node):return ast.dump(node,include_attributes=False)
def named(t,name):return next(n for n in t.body if getattr(n,'name',None)==name)
for old,new,diff in [('original_bf5_exporter','selected_exporter','exporter_complete_unsealed_diff'),('original_3a_reader','selected_reader','reader_complete_unsealed_diff'),('initial0488_harness_NOT_RUN','selected_R1_harness','harness_complete_unsealed_R1_diff')]:
 a,b=data(old).decode().splitlines(keepends=True),data(new).decode().splitlines(keepends=True)
 actual=''.join(difflib.unified_diff(a,b,fromfile=P(allpins[old]['path']).name,tofile=P(allpins[new]['path']).name)).encode()
 assert actual==data(diff)
 assert actual.count(b'\n@@ ')==(1 if new=='selected_R1_harness' else 5)
e,r=tree('selected_exporter'),tree('selected_reader');oldr=tree('original_3a_reader');olde=tree('original_bf5_exporter')
codec=d['isolated_harness_preparation']['only_lifted_exact_codec_defs'];assigns=d['isolated_harness_preparation']['only_lifted_closed_assignments']
assert len(codec)==12 and len(assigns)==5
for name in codec:assert dump(named(e,name))==dump(named(r,name))
def const(t,name):return next(n for n in t.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id==name)
for name in assigns:assert dump(const(e,name))==dump(const(r,name))
fixed=data('actual_fixed_embedded_codec_source')
assert fixed in data('selected_exporter') and fixed in data('selected_reader')
for name in ('require','sha','relative','missing','same_regions'):assert dump(named(oldr,name))==dump(named(r,name))
for name in ('F6','C','HELPER','REPORTER','CHARS','OLD_FILES','THREADS','TARGETS','ALLOWED','MISSING','JACOBI'):assert dump(const(oldr,name))==dump(const(r,name))
oldmain,newmain=named(oldr,'main'),named(r,'main')
def pairloop(fn):return next(n for n in fn.body if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and [v.id for v in n.target.elts]==['pair','row'])
assert dump(pairloop(oldmain))==dump(pairloop(newmain))
def calls(fn):return [n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='require']
original=[n for n in calls(oldmain) if n.lineno!=92]
assert len(original)==80
current=collections.Counter(map(dump,calls(newmain)));assert not (collections.Counter(map(dump,original))-current)
assert dump(next(n for n in oldmain.body if isinstance(n,ast.ClassDef) and n.name=='SelectedRecords'))==dump(next(n for n in newmain.body if isinstance(n,ast.ClassDef) and n.name=='SelectedRecords'))
assert dump(next(n for n in named(olde,'main').body if isinstance(n,ast.Try)))==dump(next(n for n in named(e,'main').body if isinstance(n,ast.Try)))
oh,nh=tree('initial0488_harness_NOT_RUN'),tree('selected_R1_harness')
oc,nc=named(oh,'CodecTests'),named(nh,'CodecTests');changed='test_concatenated_second_gzip_member_is_refused'
for n in oc.body:
 if isinstance(n,ast.FunctionDef) and n.name!=changed:assert dump(n)==dump(named(nc,n.name))
assert dump(named(oh,'source_lift'))==dump(named(nh,'source_lift'))
cases=[n.name for n in nc.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')];assert len(cases)==13
assert cases==[v['name'] for v in d['isolated_harness_preparation']['methods']]
argv=d['isolated_harness_preparation']['prospective_exact_argv_NOT_RUN'];assert argv==['/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3','-B',allpins['selected_R1_harness']['path']]
assert sys.version_info[:3]==(3,12,6) and platform.system()=='Darwin' and platform.machine()=='arm64'
binary=P(argv[0]).resolve(strict=True);binary_pin={'path':str(binary),'bytes':binary.stat().st_size,'sha256':sha(binary.read_bytes())}
note=P('/private/tmp/lanl14-lossless-gzip-parent-source-review-20261007-a1.md');out=P('/private/tmp/lanl14-lossless-gzip-parent-source-review-20261007-a1.json')
assert not note.exists() and not out.exists()
text='''# Ticket14 lossless-report source review\n\nReviewed 2026-10-07 ET. Parent and independent04 FULL source, finalized handoff/preparation/static comparison, initial harness and exact R1 derivation review found no concrete blocker. Source-only; no test/main/actual report/export/admission ran. Originalbf5/3a/history and C185/F6/e79/reporter/science remain exact.\n\nThe selected928 exporter and690 reader retain the byte-exact original report, conditionally encode only if original >100MiB, preserve22 pure-E additions, and check encoded/original size/SHA/semantic custody. Original ninepair45trial loop,80 reader require calls except honest exporter-lineage pin, original validation3600/owned-cleanup block and null/scope/observer contracts are preserved. Original report remains remote; no field is reduced or JSON reserialized.\n\nSelected3725 R1 harness is a single future13-body synthetic batch at the authorized codec seam; exact12 codec AST definitions and5 closed assignments only, synthetic256/4096 byte bounds, stdlib oracle, corruption/overflow/inode/replay cases. Initial0488 remains NOTRUN. Parent selects the explicit native3.12.6 -B argv below; a bounded60s private runner must bind these exact sources and preserve original start/stdout/stderr/result. Execute once only after the scheduled17:09 checkpoint is fully delivered. This is regression preparation, with no invented RED/GREEN claim.\n\nActual report completion/lane cleanup/full validation, actual report-size-based choice, delivered archived exporter, pure-E receipt and exact actual reader arguments remain separate parent gates under existing user authorization; no additional human permission is required. Neither scientific acceptance nor copied17-control execution is inferred.\n'''+ '\nProspective exact argv: '+json.dumps(argv)+'\n'
with note.open('x') as f:f.write(text)
result={'format':'swdb.lanl14-lossless-gzip-parent-source-review.v1','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonical_ensure_ascii':True,'state':'FULL_SOURCE_AND_SYNTHETIC_ARGV_REVIEWED_NOT_RUN','packet_preparation':{'path':str(prep),'bytes':len(raw),'sha256':sha(raw),'identity_sha256':d['identity_sha256'],'canonical_ensure_ascii':True},'selected_and_preserved_pins':allpins,'review_note':{'path':str(note),'bytes':note.stat().st_size,'sha256':sha(note.read_bytes())},'independent04_full_review_utc':'2026-10-07T21:01:00Z','codec_AST_count':12,'codec_Assign_AST_count':5,'original_reader_require_ASTs_preserved':80,'scientific_pairloop_AST_unchanged':True,'original_public_validation_cleanup_Try_AST_unchanged':True,'harness_methods':cases,'prospective_exact_test_argv':argv,'actual_native_interpreter':binary_pin,'bounded_test_seconds':60,'test_runs':0,'scientific_actions':0,'target_main_import_or_Store_actions':0,'no_actual_report_size_or_results_inferred':True}
result['identity_sha256']=digest(result)
with out.open('x') as f:f.write(json.dumps(result,indent=2,ensure_ascii=True,allow_nan=False)+'\n')
print(json.dumps({'path':str(out),'bytes':out.stat().st_size,'sha256':sha(out.read_bytes()),'identity_sha256':result['identity_sha256'],'test_runs':0,'original_checks':80,'codec_ASTs':12}))
