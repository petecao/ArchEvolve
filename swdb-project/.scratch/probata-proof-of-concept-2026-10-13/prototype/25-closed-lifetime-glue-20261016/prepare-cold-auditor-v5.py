"""Author exact positive source-definition/equality reductions; no remote run."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent.parent
previous=(HERE/'cold-auditor-v4.py').read_text()
assert hashlib.sha256(previous.encode()).hexdigest()=='aed8c5402047f13f4a02aa371eef80499accef8b490ae4feadc1883b2bc1d3dc'
helper='''def positive_source_reduction(ident, value):
    """Expand the source definition and eliminate only forall b's defining equality.

    forall b. (b=t && A(b)) ==> B(b) is equivalent to A(t) ==> B(t)
    when b is absent from t. All other source antecedents remain present.
    """
    require(ident in {'positive.exit_image', 'positive.cleanup'}, 'positive source reduction scope')
    require(value[0] == 'not' and value[1][0] == 'forall', 'complete negated universal source goal')
    bindings, body = value[1][1:]
    require(bindings.count(['b', 'Int']) == 1 and body[0] == '=>' and body[1][0] == 'and',
            'exact source buffer binder and implication')
    equality = ['=', 'b', ['next', 'before']]
    require(body[1][1:].count(equality) == 1, 'exact retained source fresh-buffer equality')
    def reduce(tree):
        if isinstance(tree, str):
            return ['next', 'before'] if tree == 'b' else tree
        if tree and tree[0] == 'L_t25_closed_positive':
            require(len(tree) == 4, 'source positive definition arity')
            return ['put_integer', reduce(tree[1]), reduce(tree[2]), '8', reduce(tree[3])]
        return [reduce(x) for x in tree]
    antecedent = ['and', *[x for x in body[1][1:] if x != equality]]
    return ['not', ['forall', [x for x in bindings if x != ['b', 'Int']],
                    ['=>', reduce(antecedent), reduce(body[2])]]]


'''
old="""            if ident=='positive.cleanup':variants.append(('positive_antecedent_dominates_scalar_branch',source_goal(ident,positive_branch=True)))
            equal=[name for name,value in variants if actual==canon(value)]
"""
new="""            if ident=='positive.cleanup':variants.append(('positive_antecedent_dominates_scalar_branch',source_goal(ident,positive_branch=True)))
            if ident in {'positive.exit_image', 'positive.cleanup'}:
                variants += [(name+'_source_definition_and_fresh_buffer_substitution', positive_source_reduction(ident, value))
                             for name, value in list(variants)]
            equal=[name for name,value in variants if actual==canon(value)]
"""
assert previous.count(old)==previous.count('def main():')==1
current=previous.replace(old,new,1).replace('def main():',helper+'def main():',1)
assert current.replace(helper,'',1).replace(new,old,1)==previous
tree=ast.parse(current)
names={'require','digest','forms','expand','canon','source_goal','positive_source_reduction'}
assignments={'CHECKS','SOURCE_DEFINITIONS','POSITIVE_PREMISE','POSITIVE_STATE'}
nodes=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom)) or
       isinstance(n,ast.FunctionDef) and n.name in names or
       isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in assignments for t in n.targets)]
namespace={}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<extracted-pure-positive-source-controls>','exec'),namespace)
source=namespace['source_goal']; reduction=namespace['positive_source_reduction']; canon=namespace['canon']
controls=[]
for ident in ('positive.exit_image','positive.cleanup'):
    original=source(ident)
    reduced=reduction(ident,original)
    original_ant=original[1][2][1][1:]
    reduced_ant=reduced[1][2][1][1:]
    assert len(original_ant)==10 and len(reduced_ant)==9
    assert ['b','Int'] not in reduced[1][1]
    assert 'L_t25_closed_positive' not in json.dumps(reduced)
    assert '"b"' not in json.dumps(reduced)
    for premise in reduced_ant:
        corrupted=json.loads(json.dumps(reduced))
        corrupted[1][2][1].remove(premise)
        assert canon(corrupted)!=canon(reduced)
    controls.append(ident+': nine retained antecedents individually tamper checked')
    assert canon(reduction(ident,source(ident,positive_branch=True)))==canon(reduced) if ident=='positive.exit_image' else True
    for label, mutate in [
        ('fresh_equality_missing_refused',lambda x:x[1][2][1].remove(['=','b',['next','before']])),
        ('fresh_term_changed_refused',lambda x:x[1][2][1].__setitem__(8,['=','b',['next','entry']])),
        ('buffer_binder_sort_changed_refused',lambda x:x[1][1].__setitem__(4,['b','heap'])),
    ]:
        bad=json.loads(json.dumps(original)); mutate(bad)
        try:reduction(ident,bad)
        except ValueError:pass
        else:raise AssertionError(label)
        controls.append(ident+': '+label)

output=HERE/'cold-auditor-v5.py';assert not output.exists();output.write_text(current)
receipt={
    'created':'2026-10-16 ET','classification':'INERT_PASSIVE_EXACT_POSITIVE_SOURCE_REDUCTION',
    'previous_auditor_sha256':hashlib.sha256(previous.encode()).hexdigest(),
    'previous_actual_refusal':{'sha256':'034e9cb658ed6b51eb64665d7fa644e4cf9dfcbee9b3cf100e08f49b319544be',
        'bytes':334,'checks_before_refusal':93632,'goal':'positive.exit_image'},
    'auditor':{'path':str(output.relative_to(BASE)),'bytes':len(current.encode()),'sha256':hashlib.sha256(current.encode()).hexdigest()},
    'exact_inverse_to_v4':True,'pure_controls':controls,'each_positive_goal_retained_antecedents':9,
    'defining_equality_discharged_only_by_universal_substitution':True,
    'source_function_unfolded':'L_t25_closed_positive(loop,r,n) = put_integer(loop,r,8,n)',
    'all_actual_goal_terms_unchanged':True,'author_remote_execution':False,
    'controls_external_processes_executed':0,'acceptance':False,
    'scope':'Only additional full source-goal variants for the two positive cases. No actual goal rewriting, missing antecedent, sibling theorem, new caller premise or proof-result change.',
}
path=BASE/'evidence/t25-closed-lifetime6-cold-auditor-preparation-v5-20261016.json';assert not path.exists()
path.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
print(json.dumps({'auditor':receipt['auditor'],'receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'controls':len(controls)}))
