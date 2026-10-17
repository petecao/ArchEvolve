"""Author compact, in-place definition-normalization metadata inspection."""
import ast
from pathlib import Path

here = Path(__file__).resolve().parent
tree = ast.parse((here/'cold-auditor-v3.py').read_text())
functions = {'require', 'digest', 'pin', 'forms', 'expand', 'canon', 'source_goal', 'symbols', 'required_definitions'}
assignments = {'CHECKS', 'SOURCE_DEFINITIONS', 'POSITIVE_PREMISE', 'POSITIVE_STATE'}
selected = []
for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        selected.append(node)
    elif isinstance(node, ast.FunctionDef) and node.name in functions:
        selected.append(node)
    elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in assignments for t in node.targets):
        selected.append(node)
code = ast.unparse(ast.Module(body=selected, type_ignores=[])) + '\n'
code += '''
signal.alarm(60)
resource.setrlimit(resource.RLIMIT_AS, (512*1024**2, 512*1024**2))
root = Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-fb197c5d-t25-closed-lifetime6-public-v1/closed-lifetime6-public-v1-profile')
def nnf(value, comparisons=False, implication=False):
    if isinstance(value, str): return value
    if value and value[0]=='let': return nnf(expand(value), comparisons, implication)
    if value and value[0]=='not' and isinstance(value[1], list):
        child=value[1]
        if child[0]=='not': return nnf(child[1], comparisons, implication)
        if child[0] in {'and','or'}:
            return nnf(['or' if child[0]=='and' else 'and', *[['not',x] for x in child[1:]]], comparisons, implication)
        if comparisons and child[0] in {'<','<='}:
            return nnf(['<=' if child[0]=='<' else '<', child[2], child[1]], comparisons, implication)
    if value and implication and value[0]=='=>':
        return nnf(['or',['not',value[1]],value[2]], comparisons, implication)
    return [nnf(x, comparisons, implication) for x in value]
rows=[]
for ident in ('receiver.entry','constructor.frame','buffer.identity','zero.cleanup','positive.exit_image','positive.cleanup'):
    for path in sorted((root/('leaf-'+ident)).rglob('*.psmt2'))+sorted((root/('leaf-'+ident)).rglob('*.smt2')):
        tree=forms(path.read_text())
        for definition in [d for d in tree if d[0]=='define-fun' and d[1].startswith(('P_t25','L_t25'))]:
            name=definition[1]
            bindings,body=SOURCE_DEFINITIONS[name]
            expected=forms('(forall ('+bindings+') '+body+')')[0]
            actual=['forall', definition[2], definition[-1]]
            variants={}
            for label,options in [('literal',{}),('demorgan',{}),('demorgan_comparisons',{'comparisons':True}),('demorgan_comparisons_implication',{'comparisons':True,'implication':True})]:
                left,right=(actual,expected) if label=='literal' else (nnf(actual,**options),nnf(expected,**options))
                variants[label]=canon(left)==canon(right)
            rows.append({'id':ident,'task':path.name,'task_sha256':pin(path)['sha256'],'definition':name,
                         'actual_definition_sha256':digest(definition),'expected_definition_sha256':digest(expected),
                         'source_equivalence_variants':variants})
print(json.dumps({'classification':'PASSIVE_IN_PLACE_DEFINITION_NORMALIZATION_DISCOVERY','rows':rows,
                  'raw_terms_transferred':False,'scientific_execution':False,'acceptance':False},sort_keys=True,indent=2))
'''
path=here/'definition-discovery-v1.py'
assert not path.exists()
path.write_text(code)
print(path)
