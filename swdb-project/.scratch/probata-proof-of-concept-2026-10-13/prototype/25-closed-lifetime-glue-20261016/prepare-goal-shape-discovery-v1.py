"""Author symbol/count-only metadata for the two still-unmatched full goals."""
import ast
from pathlib import Path

here=Path(__file__).resolve().parent
tree=ast.parse((here/'cold-auditor-v4.py').read_text())
functions={'require','digest','pin','forms','expand','canon','source_goal'}
assignments={'CHECKS','SOURCE_DEFINITIONS','POSITIVE_PREMISE','POSITIVE_STATE'}
nodes=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom)) or
       isinstance(n,ast.FunctionDef) and n.name in functions or
       isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in assignments for t in n.targets)]
code=ast.unparse(ast.Module(body=nodes,type_ignores=[]))+'\n'
code+='''
signal.alarm(30)
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
root=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-fb197c5d-t25-closed-lifetime6-public-v1/closed-lifetime6-public-v1-profile')
def counts(value):
    result=Counter()
    if isinstance(value,str):
        if not value.startswith('@'):result[value]+=1
    else:
        for child in value:result.update(counts(child))
    return result
rows=[]
for ident in ('positive.exit_image','positive.cleanup'):
    path=next((root/('leaf-'+ident)).rglob('*.psmt2'))
    goal=[x[1] for x in forms(path.read_text()) if x[0]=='assert'][-1]
    actual=counts(canon(goal)); expected=counts(canon(source_goal(ident)))
    rows.append({'id':ident,'task':pin(path),'actual_goal_sha256':digest(goal),
                 'only_actual_symbol_counts':dict(actual-expected),'only_source_symbol_counts':dict(expected-actual),
                 'same_symbol_count_inventory':actual==expected})
print(json.dumps({'classification':'PASSIVE_GOAL_SYMBOL_COUNT_METADATA','rows':rows,
                  'raw_terms_transferred':False,'scientific_execution':False,'acceptance':False},sort_keys=True,indent=2))
'''
path=here/'goal-shape-discovery-v1.py'
assert not path.exists()
path.write_text(code)
print(path)
