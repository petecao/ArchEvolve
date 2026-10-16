"""Author the exact SMT census after checked positive-definition unfolding."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent.parent
previous=(HERE/'cold-auditor-v5.py').read_text()
assert hashlib.sha256(previous.encode()).hexdigest()=='121761cf8e8298417a38271662262e2ab1fc155152c5ddc4d23e1805d8dfd17d'
old='''def check_source_definitions(definitions, ident):
    selected = [d for d in definitions if d[1].startswith(('P_t25', 'L_t25'))]
    require({d[1] for d in selected} == required_definitions(ident),
            'complete source definition closure '+ident)
'''
new='''def check_source_definitions(definitions, ident, actual_goal):
    selected = [d for d in definitions if d[1].startswith(('P_t25', 'L_t25'))]
    wanted = required_definitions(ident)
    if ident in {'positive.exit_image', 'positive.cleanup'} and 'L_t25_closed_positive' not in symbols(actual_goal):
        # The complete goal has already matched its independently expanded source variant.
        # The SMT driver then removes this one unused definition; common exports retain it.
        wanted = wanted - {'L_t25_closed_positive'}
    require({d[1] for d in selected} == wanted,
            'complete source definition closure '+ident)
'''
old_call="defs=check_source_definitions([x for x in tree if x[0]=='define-fun'],ident)"
new_call="defs=check_source_definitions([x for x in tree if x[0]=='define-fun'],ident,assertions[-1])"
assert previous.count(old)==previous.count(old_call)==1
current=previous.replace(old,new,1).replace(old_call,new_call,1)
assert current.replace(new,old,1).replace(new_call,old_call,1)==previous
tree=ast.parse(current)
functions={'require','digest','forms','expand','canon','source_goal','positive_source_reduction','symbols','required_definitions','check_source_definitions','frame_order_nnf'}
assignments={'CHECKS','SOURCE_DEFINITIONS','POSITIVE_PREMISE','POSITIVE_STATE'}
nodes=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom)) or
       isinstance(n,ast.FunctionDef) and n.name in functions or
       isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in assignments for t in n.targets)]
namespace={}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<extracted-pure-source-census-controls>','exec'),namespace)
forms=namespace['forms'];definitions=namespace['SOURCE_DEFINITIONS'];controls=[]
for ident in ('positive.exit_image','positive.cleanup'):
    source=namespace['source_goal'](ident)
    goal=namespace['positive_source_reduction'](ident,source)
    wanted=namespace['required_definitions'](ident)-{'L_t25_closed_positive'}
    rows=[forms('(define-fun '+name+' ('+definitions[name][0]+') Bool '+definitions[name][1]+')')[0] for name in sorted(wanted)]
    assert set(namespace['check_source_definitions'](rows,ident,goal))==wanted
    controls.append(ident+': exact expanded-goal source closure accepted')
    for missing in wanted:
        try:namespace['check_source_definitions']([r for r in rows if r[1]!=missing],ident,goal)
        except ValueError:pass
        else:raise AssertionError('missing '+missing+' accepted')
    controls.append(ident+': each other missing definition refused')
    try:namespace['check_source_definitions'](rows,ident,source)
    except ValueError:pass
    else:raise AssertionError('definition omitted while original goal still references it')
    controls.append(ident+': referenced positive definition cannot be omitted')
    extra=forms('(define-fun P_t25_unrelated () Bool true)')[0]
    try:namespace['check_source_definitions']([*rows,extra],ident,goal)
    except ValueError:pass
    else:raise AssertionError('extra source definition accepted')
    controls.append(ident+': extra source definition refused')

output=HERE/'cold-auditor-v6.py';assert not output.exists();output.write_text(current)
receipt={
    'created':'2026-10-16 ET','classification':'INERT_PASSIVE_EXPANDED_POSITIVE_DEFINITION_CENSUS',
    'previous_auditor_sha256':hashlib.sha256(previous.encode()).hexdigest(),
    'previous_actual_refusal':{'sha256':'93bb0e0f23314bacb0cf940cce5e0f897545fe659877da2487ed21e690df524a','bytes':195,'checks_before_refusal':95625},
    'auditor':{'path':str(output.relative_to(BASE)),'bytes':len(current.encode()),'sha256':hashlib.sha256(current.encode()).hexdigest()},
    'exact_inverse_to_v5':True,'pure_controls':controls,'controls_external_processes_executed':0,
    'common_export_full_definition_census_unchanged':True,
    'SMT_only_unused_definition_omitted_after_complete_goal_match':'L_t25_closed_positive',
    'source_definitions_kept':{'positive.exit_image':7,'positive.cleanup':6},
    'author_remote_execution':False,'acceptance':False,
    'scope':'Only exact SMT definition census after the previously checked source definition is fully expanded in the matched goal. Every remaining source definition is still required and body checked.',
}
path=BASE/'evidence/t25-closed-lifetime6-cold-auditor-preparation-v6-20261016.json';assert not path.exists()
path.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(json.dumps({'auditor':receipt['auditor'],'receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'controls':len(controls)}))
