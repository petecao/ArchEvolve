"""2026-10-16 ET. Source-only exact metadata/two-consumer successor builder."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
V1 = WHOLE / 'receiver-state-draws-v1'
CHANGES = {
    'model-entry-v2/whole_model_v2.py': 'model-entry-v3/whole_model_v3.py',
    '7ddff742ec78573dec9ee53c071f57d88ed8fd4d4f819a05118456f72acafe61': '2de83f722c439c5a834f9b17549b979e24b3716d79170377bf8cbeafd7b07b50',
    'source_statements_v1.py': 'source_statements_v2.py',
    '333148951b8e1c634600a7a0deb2abf312c4d708b1ca69fdd04429959518c0d1': '49832255fef43afa51078479770d62f01e7e539e4f71f4034e3f2648cb867738',
}


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def build():
    original = V1 / 'receiver_state_draws_v1.py'
    assert pin(original)['sha256'] == '07b8f687987a90423179e13b42fa312e4678fe5d929e932c9ac0374f0ca54e7b'
    model = WHOLE / 'model-entry-v3/whole_model_v3.py'
    statements = WHOLE / 'source_statements_v2.py'
    assert pin(model)['sha256'] == CHANGES['7ddff742ec78573dec9ee53c071f57d88ed8fd4d4f819a05118456f72acafe61']
    assert pin(statements)['sha256'] == CHANGES['333148951b8e1c634600a7a0deb2abf312c4d708b1ca69fdd04429959518c0d1']
    text = model.read_text()
    helper_node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == 'stable_metadata')
    helper = ast.get_source_segment(text, helper_node)
    old = original.read_text(); new = old
    for before, after in CHANGES.items():
        assert new.count(before) == 1
        new = new.replace(before, after, 1)
    expression = 'path.lstat() == before and hasher.hexdigest() == pin.sha256'
    replacement = 'stable_metadata(path.lstat()) == stable_metadata(before) and hasher.hexdigest() == pin.sha256'
    assert new.count(expression) == 1
    new = new.replace(expression, replacement, 1)
    new = new.replace('def check_file(', helper + '\n\n\ndef check_file(', 1)
    inverse = new.replace(helper + '\n\n\n', '', 1).replace(replacement, expression, 1)
    for before, after in CHANGES.items(): inverse = inverse.replace(after, before, 1)
    assert inverse == old
    (HERE / 'receiver_state_draws_v2.py').write_text(new)
    old_template = json.loads((V1 / 'selection-policy-template-v1.json').read_bytes())
    template = json.loads((V1 / 'selection-policy-template-v1.json').read_bytes())
    for before, after in [('model-entry-v2/whole_model_v2.py', 'model-entry-v3/whole_model_v3.py'),
                          ('source_statements_v1.py', 'source_statements_v2.py')]:
        template['frozen_inputs'].pop(before)
        template['frozen_inputs'][after] = pin(WHOLE / after)
    undo = json.loads(json.dumps(template))
    for before, after in [('model-entry-v2/whole_model_v2.py', 'model-entry-v3/whole_model_v3.py'),
                          ('source_statements_v1.py', 'source_statements_v2.py')]:
        undo['frozen_inputs'].pop(after)
        undo['frozen_inputs'][before] = old_template['frozen_inputs'][before]
    assert undo == old_template
    dump('selection-policy-template-v2.json', template)
    for name in ('context-receipt-template', 'runtime-selection-template'):
        (HERE / (name + '-v2.json')).write_bytes((V1 / (name + '-v1.json')).read_bytes())
    basis = json.loads((V1 / 'frozen-basis-pins-v1.json').read_bytes())
    basis['frozen_inputs'] = template['frozen_inputs']
    basis['historical_assembly_basis'] = {name: pin(WHOLE / name) for name in (
        'model-entry-v1/whole_model_v1.py', 'model-entry-v2/whole_model_v2.py', 'source_statements_v1.py')}
    basis['active_consumer_successors'] = {'model': pin(model), 'statements': pin(statements)}
    dump('frozen-basis-pins-v2.json', basis)
    dump('receiver-state-draws-inverse-v2.json', {'date': '2026-10-16 ET', 'base_receiver': pin(original),
        'successor_receiver': pin(HERE / 'receiver_state_draws_v2.py'), 'stable_metadata_origin': pin(model),
        'stable_metadata_helper_sha256': hashlib.sha256(helper.encode()).hexdigest(),
        'allowed_basis_changes': {'model-entry-v2/whole_model_v2.py': pin(model), 'source_statements_v1.py': pin(statements)},
        'source_text_inverse': True, 'selection_template_inverse': True, 'receiver_draw_semantics_unchanged': True,
        'active_basis_broadening': False, 'actual_preparation_or_scientific_execution': False})


if __name__ == '__main__': build()
