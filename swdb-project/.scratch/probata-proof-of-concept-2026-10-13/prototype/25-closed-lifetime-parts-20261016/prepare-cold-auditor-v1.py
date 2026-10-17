"""Compiler-free author of the independently reviewed 23-leaf cold observer.

Never reads the actual remote raw root. Only local source/metadata and extracted
pure formula controls run here. Root settlement and parent review gate execution.
"""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent.parent
SIX=HERE.parent/'25-closed-lifetime-glue-20261016/cold-auditor-v6.py'
prior=SIX.read_text()
assert hashlib.sha256(prior.encode()).hexdigest()=='9a373fe5a32bd11c36149d65f1470c98def984dec10c35465ac7d198f7f8651b'
packet=HERE/'inert-04af74c1-public-v1'
expected=json.loads((packet/'expected.json').read_bytes())
entry_sha='5fdd14d5c2e281fccdbaeb5af5f71972e6e1ca3b8fd83c8105d5e6a91b8a0658'
expected_sha='703568b4bf4dbcfcf4b15acf202f903a5698c5c0563777d0513a4a66e63223aa'
assert hashlib.sha256((packet/'entry.py').read_bytes()).hexdigest()==entry_sha
assert hashlib.sha256((packet/'expected.json').read_bytes()).hexdigest()==expected_sha
source='/data1/yanruj/probata-resume-20261016-04af74c1'
raw='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-04af74c1-t25-closed-lifetime23-public-v1'
command=json.loads((packet/'root-command.json').read_bytes())
command=[x.replace('{SOURCE}',source).replace('{OUTPUT}',raw) for x in command]
command_sha=hashlib.sha256(json.dumps(command,sort_keys=True,separators=(',',':')).encode()).hexdigest()
current=prior
deltas=[]
def replace(old,new,label,count=1):
    global current
    assert current.count(old)==count,(label,current.count(old))
    current=current.replace(old,new,count)
    deltas.append({'label':label,'old':old,'new':new,'count':count})

replace('independent six-glue cold auditor','independent 23-leaf cold observer','documentation')
replace('fb197c5ddd173065ca781766886c6a797684a838','04af74c121a733589fbe1a2087ad602deaef598b','source commit')
replace('fb197c5d','04af74c1','source namespaces',2)
replace('t25-closed-lifetime6-public-v1','t25-closed-lifetime23-public-v1','raw namespace')
replace("PROFILE = RAW/'closed-lifetime6-public-v1-profile'","PROFILE = RAW/'closed-lifetime23-public-v1-profile'",'profile namespace')
replace("ENTRY_SHA = '76a687229c3d28e504102aad1bdd2c3efc47b1992cf1703c94a2291ec6f7c263'","ENTRY_SHA = '"+entry_sha+"'",'entry pin')
replace("EXPECTED_SHA = 'a10f2ee5864b8c39c22e72b29f34e3195b59839e0fdc9a6ae9e5c6c5f7ecd4b2'","EXPECTED_SHA = '"+expected_sha+"'",'expected pin')
replace("COMMAND_SHA = 'be7379c4e99be42f88ef965517af8bf4e42e778041602ac3a8d288ba2dc573a8'","COMMAND_SHA = '"+command_sha+"'",'actual launch command pin')
replace('def source_goal(ident, *, positive_branch=False):','def six_reference_goal(ident, *, positive_branch=False):','retain original full reference transcription')
parts=(HERE/'cold-goals-v1.py').read_text()
replace('READ_ONLY_GIT_ACTIVE = False\n\n\ndef git',parts+'\n\nREAD_ONLY_GIT_ACTIVE = False\n\n\ndef git','independent 23 source formulas and reference reconstruction')
replace("require(ident in {'positive.exit_image', 'positive.cleanup'}, 'positive source reduction scope')",
        "require(ident in {row['id'] for row in leaf_rows()}, 'positive source reduction scope')",'exact 23-id reduction scope')
replace("if ident in {'positive.exit_image', 'positive.cleanup'} and 'L_t25_closed_positive' not in symbols(actual_goal):",
        "if ident in {row['id'] for row in leaf_rows()} and 'L_t25_closed_positive' not in symbols(actual_goal):",'exact expanded-definition census scope')
replace("RAW/'closed-lifetime6-public-v1-entry.py'","RAW/'closed-lifetime23-public-v1-entry.py'",'frozen outer entry filename')
replace("len(physical)==15","len(physical)==34",'complete 34 nonmanifest files')
replace("manifest=read(PROFILE/'canonical-inputs/manifest.json')","manifest=read(PROFILE/'canonical-inputs/manifest.json')\n    reference_equivalence=source_reference_equivalence(manifest)",'independent complete source/reference formula check')
replace("and len(result['runs'])==6","and len(result['runs'])==23",'complete 23 producer outcomes')
replace("'all six distinct source identities'","'all23 distinct source identities'",'census label')
replace("'all six producer outcomes retained'","'all23 producer outcomes retained'",'producer label')
old="""            actual=canon(assertions[-1]);variants=[('literal_source',source_goal(ident))]
            if ident=='positive.cleanup':variants.append(('positive_antecedent_dominates_scalar_branch',source_goal(ident,positive_branch=True)))
            if ident in {'positive.exit_image', 'positive.cleanup'}:
                variants += [(name+'_source_definition_and_fresh_buffer_substitution', positive_source_reduction(ident, value))
                             for name, value in list(variants)]
"""
replace(old,"            actual=canon(assertions[-1]);variants=goal_variants(ident)\n",'full independent source goal variants')
replace("        require(printed,'actual printed theory retained '+ident)",
        """        census=read(directory/'task-census.json')
        internal_qed = not printed and goal['results']==['valid'] and goal['passed'] and any(
            p['prover']=='qed' and p.get('success')==1 for p in peer.get('provers',[]))
        require(bool(printed) or internal_qed,'actual common task or complete internal Qed evidence '+ident)
        require(census['internal_qed_inventory_only']==([goal['goal']] if internal_qed else []),
                'exact internal Qed inventory-only census '+ident)""",'explicit internal Qed-only closure')
replace("files=sorted(directory.rglob('*.psmt2'))+sorted(directory.rglob('*.smt2'));require(files,'actual materialized tasks retained '+ident)",
        "files=sorted(directory.rglob('*.psmt2'))+sorted(directory.rglob('*.smt2'));require(bool(files) != internal_qed,'actual materialized tasks or sole internal Qed census '+ident)",'no fabricated tasks for internal Qed')
replace("'ordinary':1,'smoke':0,'properties':2,'CSV_rows':0,'input':pin(directory/'wp_input.c')",
        "'ordinary':1,'smoke':0,'properties':2,'CSV_rows':0,'internal_qed_inventory_only':internal_qed,'source_goal_sha256':digest(source_goal(ident)),'input':pin(directory/'wp_input.c')",'retain every source-owned internal goal')
replace("result['all_six_producer_proven']","result['all_23_producer_proven']",'actual producer aggregate field')
replace("'PASS_CONDITIONAL_SIX_SOURCE_MATH_COLD' if all_proven else 'COMPLETE_SIX_SOURCE_COLD_NOT_PROVEN'",
        "'PASS_CONDITIONAL_23_SOURCE_MATH_COLD' if all_proven else 'COMPLETE_23_SOURCE_COLD_NOT_PROVEN'",'conditional partial/proven classification')
replace("'all_six_normal_producer_proven':all_proven","'all_23_normal_producer_proven':all_proven,'source_reference_equivalence':reference_equivalence",'retain full reference reconstruction')
replace('Six independent conditional mathematical source duties only','23 independent conditional mathematical source duties only','scientific scope')
replace('REFUSED_PASSIVE_SIX_COLD','REFUSED_PASSIVE_23_COLD','fail-closed classification')

tree=ast.parse(current)
names={'require','digest','forms','expand','strip_comments','canon','six_reference_goal','source_goal','symbols',
       'required_definitions','source_statement','reference_statement','leaf_rows','source_zero_addition',
       'goal_variants','positive_source_reduction','source_reference_equivalence','frame_order_nnf','check_source_definitions'}
assignments={'CHECKS','SOURCE_DEFINITIONS','POSITIVE_PREMISE','POSITIVE_STATE','PARTS_PREMISE_ACSL','PARTS_QUANTIFIERS',
             'PARTS_BASE_BINDINGS','PARTS_POSITIVE_ACSL','PARTS_FINAL_ACSL','PARTS_FINAL','PARTS_SCALAR_ACSL'}
nodes=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom)) or
       isinstance(n,ast.FunctionDef) and n.name in names or
       isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in assignments for t in n.targets)]
ns={}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<pure-independent23-source-controls>','exec'),ns)
manifest=expected['canonical_manifest_portable']
reference=ns['source_reference_equivalence'](manifest)
controls=['all23 exact independent source/ACSL statements and fresh scopes',
          'complete14+9 reference component order and original statements',
          'exact final/scalar witnesses and reflexive equalities']
assert [r['id'] for r in ns['leaf_rows']()]==expected['target_ids']
canonical_source_goals=[]
for row in ns['leaf_rows']():
    ident=row['id'];goal=ns['source_goal'](ident);variants=ns['goal_variants'](ident)
    assert len(goal[1][2][1][1:])==(11 if row['scope'] else 10)
    reduced=ns['positive_source_reduction'](ident,goal)
    assert len(reduced[1][2][1][1:])==(10 if row['scope'] else 9)
    assert all(x[0]!='b' for x in reduced[1][1])
    assert len({x[0] for x in reduced[1][1]})==len(reduced[1][1])
    assert not ns['symbols'](reduced)&{'b','L_t25_closed_positive'}
    canonical_source_goals.append({'id':ident,'source_goal_sha256':ns['digest'](goal),
        'source_goal_variants':[name for name,_ in variants],
        'definition_closure':sorted(ns['required_definitions'](ident))})
controls.append('each23 preserves every nondefining antecedent and fresh index under buffer substitution')
for index in range(23):
    bad=json.loads(json.dumps(manifest));bad['obligations'][index]['statement']+=' && \\false'
    try:ns['source_reference_equivalence'](bad)
    except ValueError:pass
    else:raise AssertionError('changed leaf accepted '+str(index))
controls.append('each23 changed conclusion/source statement refused')
for label,mutate in [
    ('dropped leaf',lambda x:x['obligations'].pop()),
    ('sibling premise',lambda x:x['obligations'][0]['dependencies'].append('positive.cleanup.scalar')),
    ('changed reference',lambda x:x['conjunctions']['positive.exit_image'].__setitem__('original_statement','true')),
    ('changed final witness',lambda x:x['conjunctions']['positive.cleanup']['witnesses'].__setitem__('final','loop')),
    ('missing original component',lambda x:x['conjunctions']['positive.cleanup']['parts'].pop()),
]:
    bad=json.loads(json.dumps(manifest));mutate(bad)
    try:ns['source_reference_equivalence'](bad)
    except ValueError:pass
    else:raise AssertionError(label+' accepted')
    controls.append(label+' refused')

parser_names=('require','digest','pin','read','snapshot','forms','expand','strip_comments','canon','git','normal_flags','source_false_map')
old_tree=ast.parse(prior)
for name in parser_names:
    old=next(n for n in old_tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    new=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False),name
controls.append('twelve reviewed parser/guard/normal-policy helpers AST-identical')

output=HERE/'cold-observer-v1.py';assert not output.exists();output.write_text(current)
receipt={'created':'2026-10-16 ET','classification':'INERT_INDEPENDENT_23_SOURCE_COLD_OBSERVER',
    'auditor':{'path':str(output.relative_to(BASE)),'bytes':len(current.encode()),'sha256':hashlib.sha256(current.encode()).hexdigest()},
    'predecessor':{'sha256':hashlib.sha256(prior.encode()).hexdigest(),'path':str(SIX.relative_to(BASE))},
    'source_commit':expected['source_commit'],'entry_sha256':entry_sha,'expected_sha256':expected_sha,
    'command_sha256':command_sha,'all23_source_controls':canonical_source_goals,
    'reference_equivalence':reference,'controls':controls,'inherited_helpers_AST_equal':list(parser_names),
    'all_deltas':deltas,'remote_raw_inspected':False,'author_remote_execution':False,
    'project_imports':0,'compiler_native_verifier_solver_runs':0,
    'source_typed_bridge_established':False,'body_acceptance':False,'caller_acceptance':False,
    'all23_proof_acceptance':False,'root_settlement_required':True,'independent_parent_review_required':True,
    'scope':'All actual mathematical outcomes retained, including partial/timeout outcomes; exact full source and current source/runtime/canonical/consumer/import/native/task/hypothesis/guard identity closure required. No source/caller/public admission.'}
receipt_path=BASE/'evidence/t25-closed-lifetime23-cold-observer-preparation-v1-20261016.json';assert not receipt_path.exists()
receipt_path.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(json.dumps({'observer':receipt['auditor'],'receipt_sha256':hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
                  'source_controls':len(canonical_source_goals),'controls':len(controls),'command_sha256':command_sha}))
