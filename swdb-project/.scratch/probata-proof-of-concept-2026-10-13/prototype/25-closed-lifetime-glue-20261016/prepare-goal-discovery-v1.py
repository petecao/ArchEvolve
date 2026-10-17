"""Author compact in-place exact goal-normalization variant inspection."""
import ast
from pathlib import Path

here=Path(__file__).resolve().parent
tree=ast.parse((here/'cold-auditor-v4.py').read_text())
functions={'require','digest','pin','forms','expand','canon','source_goal','symbols','required_definitions','frame_order_nnf'}
assignments={'CHECKS','SOURCE_DEFINITIONS','POSITIVE_PREMISE','POSITIVE_STATE'}
nodes=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom)) or
       isinstance(n,ast.FunctionDef) and n.name in functions or
       isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in assignments for t in n.targets)]
code=ast.unparse(ast.Module(body=nodes,type_ignores=[]))+'\n'
code+='''
signal.alarm(90)
resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2))
root=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-fb197c5d-t25-closed-lifetime6-public-v1/closed-lifetime6-public-v1-profile')
def nnf(value, implication=False):
    if isinstance(value,str):return value
    if value and value[0]=='let':return nnf(expand(value),implication)
    if value and implication and value[0]=='=>':return nnf(['or',['not',value[1]],value[2]],implication)
    return frame_order_nnf([nnf(x,implication) for x in value])
def strict_literal_order(value):
    if isinstance(value,str):return value
    if value and value[0]=='let':return strict_literal_order(expand(value))
    value=[strict_literal_order(x) for x in value]
    if value and value[0]=='<' and len(value)==3:
        if isinstance(value[1],str) and re.fullmatch(r'[0-9]+',value[1]):
            return ['<=',str(int(value[1])+1),value[2]]
        if isinstance(value[2],str) and re.fullmatch(r'[0-9]+',value[2]):
            return ['<=',value[1],str(int(value[2])-1)]
    return value
rows=[]
for ident in ('receiver.entry','constructor.frame','buffer.identity','zero.cleanup','positive.exit_image','positive.cleanup'):
    for path in sorted((root/('leaf-'+ident)).rglob('*.psmt2'))+sorted((root/('leaf-'+ident)).rglob('*.smt2')):
        assertions=[x[1] for x in forms(path.read_text()) if x[0]=='assert']
        actual=assertions[-1]
        sources=[('literal_source',source_goal(ident))]
        if ident=='positive.cleanup':sources.append(('positive_branch_source',source_goal(ident,positive_branch=True)))
        matches={}
        for label,transform in [('literal',lambda x:x),('boolean_order_nnf',nnf),
             ('implication_boolean_order_nnf',lambda x:nnf(x,True)),
             ('strict_literal_order',strict_literal_order),
             ('nnf_then_strict_literal_order',lambda x:strict_literal_order(nnf(x))),
             ('implication_nnf_then_strict_literal_order',lambda x:strict_literal_order(nnf(x,True)))]:
            actual_canon=canon(transform(actual))
            matches[label]=[name for name,source in sources if actual_canon==canon(transform(source))]
        rows.append({'id':ident,'task':path.name,'task_sha256':pin(path)['sha256'],
                     'goal_sha256':digest(actual),'source_equivalence_variants':matches})
print(json.dumps({'classification':'PASSIVE_IN_PLACE_SOURCE_GOAL_NORMALIZATION_DISCOVERY','rows':rows,
                  'raw_terms_transferred':False,'scientific_execution':False,'acceptance':False},sort_keys=True,indent=2))
'''
path=here/'goal-discovery-v1.py'
assert not path.exists()
path.write_text(code)
print(path)
