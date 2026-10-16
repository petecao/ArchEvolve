"""2026-10-16 ET. Exact certificate runtime projection successor; source only."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INIT = HERE.parent
V4 = INIT / 'cold-v4-admission-04af74c1'
BASE_SHA = '03cc1de3fe010f0686a8e99729ab831a6cbcdd5f1fa7135a56bf0e6d42271b0d'
BASE_POLICY_SHA = 'b8c75df2cd60e82673bd8e307df2df0ae8fdad698fa9dbc1b16e2b69b571a30b'
OLD_COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-cold-04af74c1-v4'
COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-cold-04af74c1-v5'
HELPER = '''def certificate_runtime_descriptor_v5(compiler, lowerer, physical):
    # A certificate's driver is the producer's _pin(command[0]), the selected
    # wrapper. stdlib runtime.driver independently names the underlying clang.
    assert set(compiler) == {'check', 'command', 'command_executable', 'driver', 'frontend', 'headers', 'parser'}
    selected = compiler['command_executable']
    assert compiler['command'] == [selected['path']] and Path(selected['path']).is_absolute()
    assert selected['sha256'] == '3c053dce26cf5ef22656f1ec9efe0cdf2911a37d5a910261895ac9c42e128fe4'
    assert lowerer['clang'] == {'id': 'clang-22.1.8', 'sha256': selected['sha256']}
    assert compiler['driver']['path'] != selected['path']
    driver = {'path': selected['path'], 'bytes': 145, 'sha256': selected['sha256']}
    physical.pinned(driver)
    return {'command': list(compiler['command']), 'version': lowerer['clang']['id'].removeprefix('clang-'), 'driver': driver}


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
    raw = (V4 / 'initialized_cold_audit_v4.py').read_bytes(); assert sha(raw) == BASE_SHA
    before = raw.decode()
    old = "    runtime = {name: compiler[name] for name in ('command', 'version', 'driver')}\n"
    assert before.count(old) == 1
    after = before.replace('initialized_cold_audit_v4.py POLICY POLICY_SHA256', 'initialized_cold_audit_v5.py POLICY POLICY_SHA256')
    after = after.replace(old, '    runtime = certificate_runtime_descriptor_v5(compiler, lowerer, physical)\n')
    after = after.replace('def audit_record(', HELPER + 'def audit_record(', 1)
    a, b = ast.parse(before), ast.parse(after)
    b.body[0] = a.body[0]
    b.body = [node for node in b.body if not isinstance(node, ast.FunctionDef) or node.name != 'certificate_runtime_descriptor_v5']
    old_record = next(node for node in a.body if isinstance(node, ast.FunctionDef) and node.name == 'audit_record')
    new_record = next(node for node in b.body if isinstance(node, ast.FunctionDef) and node.name == 'audit_record')
    index = next(index for index, node in enumerate(old_record.body) if isinstance(node, ast.Assign) and ast.get_source_segment(before, node) == old.strip())
    new_record.body[index] = old_record.body[index]
    assert ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)
    reader = HERE / 'initialized_cold_audit_v5.py'; reader.write_text(after)
    raw_policy = (V4 / 'initialized-cold-policy-04af74c1-v4.json').read_bytes(); assert sha(raw_policy) == BASE_POLICY_SHA
    policy = rebind(json.loads(raw_policy)); policy['reader_sha256'] = sha(reader.read_bytes())
    policy['provenance']['reader_base_v4_unexecuted'] = pin(V4 / 'initialized_cold_audit_v4.py')
    policy_name = 'initialized-cold-policy-04af74c1-v5.json'; dump(policy_name, policy)
    command = rebind(json.loads((V4 / 'initialized-cold-command-04af74c1-v4.json').read_bytes()))
    command['command'][-3] = COLD + '/control/' + reader.name
    command['command'][-2] = COLD + '/control/' + policy_name
    command['command'][-1] = sha((HERE / policy_name).read_bytes())
    controls = command['control_files']; controls.pop('initialized_cold_audit_v4.py'); controls.pop('initialized-cold-policy-04af74c1-v4.json')
    controls[reader.name] = pin(reader, COLD + '/control/' + reader.name)
    controls[policy_name] = pin(HERE / policy_name, COLD + '/control/' + policy_name)
    command['control_total_bytes'] = sum(row['bytes'] for row in controls.values())
    dump('initialized-cold-command-04af74c1-v5.json', command)
    dump('initialized-cold-v5-inverse.json', {'date': '2026-10-16 ET', 'base': pin(V4 / 'initialized_cold_audit_v4.py'),
        'successor': pin(reader), 'allowed_delta': ['invocation example name', 'one audit_record expected-runtime assignment',
            'new exact selected-wrapper certificate descriptor helper'], 'complete_ast_inverse': True,
        'all_other_record_checks_unchanged': True, 'prior_versions_preserved': True, 'actual_reader_executed': False})


if __name__ == '__main__': build()
