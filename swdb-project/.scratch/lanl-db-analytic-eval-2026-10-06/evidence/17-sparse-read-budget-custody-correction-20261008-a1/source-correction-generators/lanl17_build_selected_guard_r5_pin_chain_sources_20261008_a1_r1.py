import ast,difflib,hashlib,json,os,pathlib
T=pathlib.Path('/private/tmp'); ledger=[]
G0='4956a7453ae569d7ccf6e1a9ed98a1a933bee2e35cca1774932afbfba819bd26';G='d75baaf9dbe7192b02812cab525ccd6c50c81fd312d67cbfae7b9c8fdf955301'
W0='1127d1fba8e004153cf086cace7d19ccd901e85902f9ad91924407922c85c6ca';W='e16f1afa5a427d452504e7a759a7562dcc05a98014e2b4ece1663db6755d39ec'
E0='swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-library-preserving-sparse-retirement-custody-20261008-a1';E='swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-sparse-read-budget-custody-correction-20261008-a1'
def publish(a,b,oldsha,edit):
 p=T/a;q=T/b;v=p.read_bytes();assert hashlib.sha256(v).hexdigest()==oldsha,(a,hashlib.sha256(v).hexdigest());s=edit(v.decode());out=s.encode();ast.parse(out)
 d=''.join(difflib.unified_diff(v.decode().splitlines(True),s.splitlines(True),fromfile=a,tofile=b)).encode();dp=T/(b+'.complete-adjacent.diff')
 for route,raw in ((q,out),(dp,d)):
  if route.exists():
   assert route.read_bytes()==raw,(route,"partial_initial_source_changed");continue
  fd=os.open(route,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 row={'old':{'path':str(p),'bytes':len(v),'sha256':oldsha},'new':{'path':str(q),'bytes':len(out),'sha256':hashlib.sha256(out).hexdigest()},'diff':{'path':str(dp),'bytes':len(d),'sha256':hashlib.sha256(d).hexdigest()}}
 ledger.append(row);return row

def pins(s):
 return s.replace(G0,G).replace(W0,W).replace('166145','180887').replace('24115','24114')
builder=publish('lanl17_build_sparse_parent_plan_review_materials_20261008_a1.py','lanl17_build_sparse_parent_plan_review_materials_20261008_a2.py','9f1ec05188231de988872a8adbd74a92e49952cee613710107bca7f74ebf204c',pins)
pub=publish('lanl_publish_parent_sparse_plan_review_originals_20261008_a1_r1.py','lanl_publish_parent_sparse_plan_review_originals_20261008_a2.py','72527faeabe146304ac647f8edef90d5de49bcbf9aae768515e588e025cb71d9',pins)
collector=publish('lanl_read_detached_sparse_administration_originals_20261008_a1.py','lanl_read_detached_sparse_administration_originals_20261008_a2.py','af667835394c5b2adced9c66313382de4a948347fc99594692f45253b29fe957',pins)
decoder=publish('lanl_decode_detached_sparse_original_custody_20261008_a1.py','lanl_decode_detached_sparse_original_custody_20261008_a2.py','03cbe508a449f3a2a713bb2f1f5cd8bb59e4031a6f46643155bca4718d05bd1c',pins)
def launch_edit(s):
 return pins(s).replace('lanl17_detach_library_preserving_sparse_administration_20261008_a1_r1.py','lanl17_detach_library_preserving_sparse_administration_20261008_a1_r2.py').replace('lanl_sparse_retire_consumed_source_guard_20261008_a1_r2.py','lanl_sparse_retire_consumed_source_guard_20261008_a1_r5.py').replace('selected_R2_basenames','selected_G5_W2_basenames')
launch=publish('lanl17_capture_reviewed_sparse_default_launch_20261008_a1_r1.py','lanl17_capture_reviewed_sparse_default_launch_20261008_a2.py','7c5f9500bbb364a0caf87b31e7bc5b99cf569ffa4ab0b98f4094a10eaa97461a',launch_edit)
def copy_edit(s):
 s=s.replace(E0,E)
 a="ADMIN_REF='refs/remotes/origin/codex/lanl17-storage-guard-cost'\n";assert s.count(a)==1;s=s.replace(a,a+"ADMIN_PARENT='28446e8682b0a55ef4bb2050de9c46e072c39ce6'\n")
 a="    git('merge-base','--is-ancestor',FROZEN,args.administrative40)\n    diff=git('diff','--name-status','--no-renames','-z',FROZEN,args.administrative40).split(b'\\0')\n";assert s.count(a)==1
 return s.replace(a,"    git('merge-base','--is-ancestor',FROZEN,ADMIN_PARENT)\n    git('merge-base','--is-ancestor',ADMIN_PARENT,args.administrative40)\n    # Earlier additive custody remains immutable; only this new prefix is added.\n    diff=git('diff','--name-status','--no-renames','-z',ADMIN_PARENT,args.administrative40).split(b'\\0')\n")
copier=publish('lanl17_copy_sparse_retirement_sources_from_administrative_git_20261008_a1_r1.py','lanl17_copy_sparse_retirement_sources_from_administrative_git_20261008_a2.py','94f5f33bda82c7d64a9c4644c6630aa5fde598fc7d950d94e7ab74e3e60a37a9',copy_edit)
def boot_edit(s):return s.replace(E0,E).replace('lanl17_copy_sparse_retirement_sources_from_administrative_git_20261008_a1_r1.py','lanl17_copy_sparse_retirement_sources_from_administrative_git_20261008_a2.py')
boot=publish('lanl17_sparse_retirement_copy_native_stdin_bootstrap_20261008_a1_r1.py','lanl17_sparse_retirement_copy_native_stdin_bootstrap_20261008_a2.py','fd3c44fdcb7c69e6b6bfbe27221a8508547657b94e7af4b94bec47fc2cd09d8b',boot_edit)
def capture_edit(s):
 s=launch_edit(s).replace(E0,E)
 s=s.replace('fd3c44fdcb7c69e6b6bfbe27221a8508547657b94e7af4b94bec47fc2cd09d8b',boot['new']['sha256'])
 s=s.replace('94f5f33bda82c7d64a9c4644c6630aa5fde598fc7d950d94e7ab74e3e60a37a9',copier['new']['sha256'])
 s=s.replace("'11828'",repr(str(copier['new']['bytes'])))
 return s
capture=publish('lanl17_capture_exact_administrative_fetch_two_source_copy_20261008_a1_r1.py','lanl17_capture_exact_administrative_fetch_two_source_copy_20261008_a2.py','8899a532aa90b55fccd2fa00c5dba7cdd8c0fcdad513882ba794a6f0e11bff66',capture_edit)
def publication_edit(s):
 return s.replace('lanl_publish_parent_sparse_plan_review_originals_20261008_a1_r1.py','lanl_publish_parent_sparse_plan_review_originals_20261008_a2.py').replace('72527faeabe146304ac647f8edef90d5de49bcbf9aae768515e588e025cb71d9',pub['new']['sha256']).replace('lanl17-publish-sparse-parent-originals-20261008-a2.py','lanl17-publish-sparse-parent-originals-20261008-a3.py')
publication=publish('lanl17-publish-pinned-sparse-originals-parent-capture-20261008-a1-r1.py','lanl17-publish-pinned-sparse-originals-parent-capture-20261008-a3.py','4f4be3b1609cb69858e12501b667b0c7c9629e7aad5f0425af065050306a30cf',publication_edit)
def readonly_edit(s):
 module=ast.parse(s);node=next(n for n in module.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='BOOT' for t in n.targets));oldboot=ast.literal_eval(node.value)
 m=ast.parse(oldboot);inner=next(n for n in m.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='COLLECTOR' for t in n.targets));payload=ast.literal_eval(inner.value);assert hashlib.sha256(payload).hexdigest()==collector['old']['sha256']
 rows=oldboot.splitlines(True);rows[inner.lineno-1:inner.end_lineno]=['COLLECTOR='+repr((T/pathlib.Path(collector['new']['path']).name).read_bytes())+'\n'];newboot=''.join(rows)
 newboot=newboot.replace('af667835394c5b2adced9c66313382de4a948347fc99594692f45253b29fe957',collector['new']['sha256']).replace('11504',str(collector['new']['bytes'])).replace('exact-readonly-sparse-collector-af667835','exact-readonly-sparse-collector-'+collector['new']['sha256'][:8]).replace('lanl17-detached-sparse-default-a1','lanl17-detached-sparse-default-a3').replace('lanl17-detached-sparse-retire-a2','lanl17-detached-sparse-retire-a4')
 ast.parse(newboot);rows=s.splitlines(True);rows[node.lineno-1:node.end_lineno]=['BOOT='+repr(newboot)+'\n'];s=''.join(rows)
 s=s.replace('af667835394c5b2adced9c66313382de4a948347fc99594692f45253b29fe957',collector['new']['sha256']).replace('11504',str(collector['new']['bytes'])).replace('lanl17-detached-sparse-default-a1','lanl17-detached-sparse-default-a3').replace('lanl17-detached-sparse-retire-a2','lanl17-detached-sparse-retire-a4')
 return s
readonly=publish('lanl17_capture_readonly_sparse_collector_originals_20261008_a1.py','lanl17_capture_readonly_sparse_collector_originals_20261008_a2.py','354303d16cd5e7fcb8d1665c0593cc3fe4f0734acfe5098fab1603fff6dbf5ff',readonly_edit)
raw=(json.dumps({'format':'swdb.selected-sparse-R5-W2-source-only-pin-chain.v1','sealed':False,'target_mains_or_tests_run':False,'new_evidence_prefix':E,'rows':ledger},sort_keys=True,indent=2)+'\n').encode();p=T/'lanl17-selected-sparse-R5-W2-source-only-pin-chain-20261008-a1.json';fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
print(json.dumps({'manifest':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'created_sources':len(ledger),'source_pins':[r['new'] for r in ledger]}))
