"""Author the exact source-frame Boolean/order normalization; no remote run."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
previous = (HERE/'cold-auditor-v3.py').read_text()
assert hashlib.sha256(previous.encode()).hexdigest() == '22694c7e41f64f1cf173b07fdad49b1e20954dda04c52e42df38a304f0e073f3'
old = '''        require(canon(actual) == canon(expected), 'independent source definition '+ident+' '+definition[1])
        result[definition[1]] = {'form_sha256': digest(definition), 'source_equivalent': True}
'''
new = '''        normalizations = ['literal_source'] if canon(actual) == canon(expected) else []
        if definition[1] == 'P_t25_frame' and canon(frame_order_nnf(actual)) == canon(frame_order_nnf(expected)):
            normalizations.append('source_frame_de_morgan_and_exact_order_negation')
        require(normalizations, 'independent source definition '+ident+' '+definition[1])
        result[definition[1]] = {'form_sha256': digest(definition), 'source_equivalent': True,
                                  'normalizations': normalizations}
'''
helper = '''def frame_order_nnf(value):
    """Only propositional De Morgan and total-order negation; P_t25_frame only."""
    if isinstance(value, str):
        return value
    if value and value[0] == 'let':
        return frame_order_nnf(expand(value))
    if value and value[0] == 'not' and isinstance(value[1], list):
        child = value[1]
        if child[0] == 'not':
            return frame_order_nnf(child[1])
        if child[0] in {'and', 'or'}:
            return frame_order_nnf(['or' if child[0] == 'and' else 'and',
                                    *[['not', x] for x in child[1:]]])
        if child[0] in {'<', '<='}:
            return frame_order_nnf(['<=' if child[0] == '<' else '<', child[2], child[1]])
    return [frame_order_nnf(x) for x in value]


'''
assert previous.count(old) == previous.count('def check_source_definitions(') == 1
current = previous.replace(old, new).replace('def check_source_definitions(', helper+'def check_source_definitions(', 1)
assert current.replace(helper, '', 1).replace(new, old, 1) == previous

# Execute only extracted pure parser/normalizer definitions; no main/project/OS boundary.
tree = ast.parse(current)
names = {'require', 'digest', 'forms', 'expand', 'canon', 'frame_order_nnf'}
nodes = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom)) or
         isinstance(n, ast.FunctionDef) and n.name in names]
namespace = {'CHECKS': []}
exec(compile(ast.Module(body=nodes, type_ignores=[]), '<extracted-pure-frame-controls>', 'exec'), namespace)
forms = namespace['forms']; canon = namespace['canon']; nnf = namespace['frame_order_nnf']
literal = forms('(not (and (= b r) (<= o p) (< p (+ o 24))))')[0]
expected = forms('(or (not (= b r)) (< p o) (<= (+ o 24) p))')[0]
assert canon(nnf(literal)) == canon(nnf(expected))
controls = ['full_source_excluded_interval_equivalent']
for label, bad in [
    ('receiver_disjunct_missing_refused', '(or (< p o) (<= (+ o 24) p))'),
    ('lower_bound_disjunct_missing_refused', '(or (not (= b r)) (<= (+ o 24) p))'),
    ('upper_bound_disjunct_missing_refused', '(or (not (= b r)) (< p o))'),
    ('lower_bound_reversed_refused', '(or (not (= b r)) (< o p) (<= (+ o 24) p))'),
    ('upper_extent_changed_refused', '(or (not (= b r)) (< p o) (<= (+ o 23) p))'),
]:
    assert canon(nnf(literal)) != canon(nnf(forms(bad)[0])), label
    controls.append(label)

output = HERE/'cold-auditor-v4.py'
assert not output.exists()
output.write_text(current)
discovery = BASE/'evidence/t25-closed-lifetime6-definition-discovery-v1-20261016.json'
assert hashlib.sha256(discovery.read_bytes()).hexdigest() == 'ab92b741d4bf3d79cd98b9be9373750a812ea912f7e4946f7cf85fe2c4e1bce8'
receipt = {
    'created': '2026-10-16 ET',
    'classification': 'INERT_PASSIVE_EXACT_SOURCE_FRAME_NORMALIZATION',
    'previous_auditor_sha256': hashlib.sha256(previous.encode()).hexdigest(),
    'previous_actual_refusal': {'bytes': 200, 'sha256': 'ab798f4d3303c68c5dcabbc7c048880f16d0547fa2b478c752fd86985e59e51e',
        'checks_before_refusal': 42039, 'error': 'independent source definition constructor.frame P_t25_frame'},
    'auditor': {'path': str(output.relative_to(BASE)), 'sha256': hashlib.sha256(current.encode()).hexdigest(), 'bytes': len(current.encode())},
    'exact_inverse_to_v3': True,
    'source_definition_discovery': {'sha256': hashlib.sha256(discovery.read_bytes()).hexdigest(),
        'instances': 106, 'literal_source_equivalent': 90, 'source_frame_boolean_order_equivalent': 16},
    'pure_controls': controls, 'controls_external_processes_executed': 0,
    'author_remote_execution': False, 'acceptance': False,
    'scope': 'Only P_t25_frame source-definition comparison admits exact De Morgan and order negation; all complete source goal antecedents and other definitions remain unchanged. No theorem is imported.',
}
receipt_path = BASE/'evidence/t25-closed-lifetime6-cold-auditor-preparation-v4-20261016.json'
assert not receipt_path.exists()
receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2)+'\n')
print(json.dumps({'auditor': receipt['auditor'], 'receipt_sha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest(), 'controls': len(controls)}))
