"""2026-10-16 ET. Narrow retained-runtime descriptor successor, source only."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INIT = HERE.parent
V3 = INIT / 'cold-v3-admission-04af74c1'
BASE_SHA = '620e922c24f45c82ce7e7d1888a6acbe6091991702796c71f32dc8d9c86c1e44'
POLICY_SHA = 'c8cd61f44915ea4f24bbc9572469cc7be89776a383af9d7c742f2613342bda7d'
OLD_COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-cold-04af74c1-v3'
COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-cold-04af74c1-v4'
HELPER = '''def validate_compiler_descriptor_v4(name, row, expected):
    # Runtime identity has component bytes, not a version scalar. The two
    # retained producers expose their version through distinct exact metadata.
    assert set(row['runtime']) == {'check', 'command', 'command_executable', 'driver', 'frontend', 'headers', 'parser'}
    wanted = dict(expected['linux_clang_components'])
    assert row['lowering_identity']['clang'] == {'id': 'clang-22.1.8', 'sha256': wanted['command_executable']['sha256']}
    if name == 'runtime-provenance.json':
        assert set(row) == {'runtime', 'lowering_identity', 'tool'}
        assert row['tool'] == {'command': ['clang++'], 'version': '22.1.8', 'missing': ''}
        # The immutable bootstrap receipt predates the reviewed normalization.
        # Its physical wrapper/driver/parser/header pins must still match.
        wanted['command'] = ['clang++']
    else:
        assert name == 'initialized-project-runtime-provenance.json'
        assert set(row) == {'accepted_linux_components', 'admission_basis', 'cold_audit_requirement', 'cwd',
                            'lowering_identity', 'reporter', 'retained_basis', 'runtime', 'scope'}
        assert row['accepted_linux_components'] == wanted
    assert all(row['runtime'][key] == value for key, value in wanted.items())
    return wanted


'''


def sha(data): return hashlib.sha256(data).hexdigest()


def pin(path, remote=None):
    data = path.read_bytes()
    return {'path': remote or str(path.resolve()), 'bytes': len(data), 'sha256': sha(data)}


def dump(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def rebind(value):
    if isinstance(value, dict): return {key: rebind(item) for key, item in value.items()}
    if isinstance(value, list): return [rebind(item) for item in value]
    if isinstance(value, str): return value.replace(OLD_COLD, COLD)
    return value


def build():
    before = (V3 / 'initialized_cold_audit_v3.py').read_bytes()
    assert sha(before) == BASE_SHA
    old = before.decode()
    previous = "        assert runtime['version'] == '22.1.8'\n"
    assert old.count(previous) == 1
    new = old.replace('initialized_cold_audit_v3.py POLICY POLICY_SHA256', 'initialized_cold_audit_v4.py POLICY POLICY_SHA256')
    new = new.replace(previous, '        runtime_components = validate_compiler_descriptor_v4(name, row, expected)\n')
    old_components = "        assert all(runtime[key] == value for key, value in expected['linux_clang_components'].items())\n"
    assert new.count(old_components) == 1
    new = new.replace(old_components, '        assert all(runtime[key] == value for key, value in runtime_components.items())\n')
    new = new.replace('def project_contexts(', HELPER + 'def project_contexts(', 1)
    a, b = ast.parse(old), ast.parse(new)
    b.body[0] = a.body[0]
    b.body = [node for node in b.body if not isinstance(node, ast.FunctionDef) or node.name != 'validate_compiler_descriptor_v4']
    old_contexts = next(node for node in a.body if isinstance(node, ast.FunctionDef) and node.name == 'project_contexts')
    new_contexts = next(node for node in b.body if isinstance(node, ast.FunctionDef) and node.name == 'project_contexts')
    assert isinstance(old_contexts.body[1], ast.For) and isinstance(new_contexts.body[1], ast.For)
    position = next(index for index, node in enumerate(old_contexts.body[1].body)
                    if isinstance(node, ast.Assert) and ast.get_source_segment(old, node) == "assert runtime['version'] == '22.1.8'")
    new_contexts.body[1].body[position] = old_contexts.body[1].body[position]
    position = next(index for index, node in enumerate(old_contexts.body[1].body)
                    if isinstance(node, ast.Assert) and ast.get_source_segment(old, node).startswith('assert all(runtime[key]'))
    new_contexts.body[1].body[position] = old_contexts.body[1].body[position]
    assert ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)
    reader = HERE / 'initialized_cold_audit_v4.py'; reader.write_text(new)
    data = (V3 / 'initialized-cold-policy-04af74c1-v3.json').read_bytes(); assert sha(data) == POLICY_SHA
    policy = rebind(json.loads(data))
    policy['reader_sha256'] = sha(reader.read_bytes())
    policy['provenance']['reader_base_v3'] = pin(V3 / 'initialized_cold_audit_v3.py')
    policy['provenance']['retained_runtime_schema'] = pin(HERE / 'retained-runtime-schema-20261016.json')
    policy['provenance']['preserved_actual_v3_refusal'] = pin(V3 / 'initialized-cold-v3-actual-stdout-20261016.json')
    policy['scope'] = policy['scope'].replace('V3', 'V4')
    policy_name = 'initialized-cold-policy-04af74c1-v4.json'; dump(policy_name, policy)
    original_command = json.loads((V3 / 'initialized-cold-command-04af74c1-v3.json').read_bytes())
    command = rebind(original_command)
    command['command'][-3] = COLD + '/control/' + reader.name
    command['command'][-2] = COLD + '/control/' + policy_name
    command['command'][-1] = sha((HERE / policy_name).read_bytes())
    controls = command['control_files']
    controls.pop('initialized_cold_audit_v3.py'); controls.pop('initialized-cold-policy-04af74c1-v3.json')
    controls[reader.name] = pin(reader, COLD + '/control/' + reader.name)
    controls[policy_name] = pin(HERE / policy_name, COLD + '/control/' + policy_name)
    command['control_total_bytes'] = sum(row['bytes'] for row in controls.values())
    dump('initialized-cold-command-04af74c1-v4.json', command)
    dump('initialized-cold-v4-inverse.json', {'date': '2026-10-16 ET', 'base': pin(V3 / 'initialized_cold_audit_v3.py'),
        'successor': pin(reader), 'allowed_delta': ['invocation example name', 'project_contexts version predicate and context-specific component comparison',
            'new exact observed compiler descriptor validator with literal bootstrap alias and unchanged project absolute selector'], 'complete_ast_inverse': True,
        'scientific_functions_byte_unchanged': True, 'original_v3_refusal_preserved': True,
        'policy_delta': ['fresh cold namespace and derived reader/policy pins', 'local provenance for schema and preserved refusal'],
        'actual_reader_executed': False})


if __name__ == '__main__': build()
