"""2026-10-16 ET. Error-frame metadata only; no audit/gate/source change."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INIT = HERE.parent
V5 = INIT / 'cold-v5-admission-04af74c1'
BASE_SHA = '17fbffb48d689a9c6ead2d15fd6968184fd85d0c78ca46f3287e4d9b90abb894'
POLICY_SHA = '394a57ec433e19866c022471597165d7083b2c461ff4f986e579cc0bb04a8ccb'
OLD_COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-cold-04af74c1-v5'
COLD = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-cold-04af74c1-v6'
OLD_FORMAT = '''        print(json.dumps({'classification': 'REFUSED', 'error_type': type(error).__name__,
                          'failure': str(error), 'scientific_acceptance': False}, sort_keys=True))'''
NEW_FORMAT = '        print(json.dumps(refusal_frame_report_v6(error), sort_keys=True))'
HELPER = '''def refusal_frame_report_v6(error):
    """Bounded frame identity only; no exception text, source lines or locals."""
    frames, count = [], 0
    current = error.__traceback__
    while current is not None:
        code = current.tb_frame.f_code
        frames.append({'filename': code.co_filename, 'function': code.co_name, 'line': current.tb_lineno})
        if len(frames) > 16:
            frames.pop(0)
        count += 1
        current = current.tb_next
    return {'classification': 'REFUSED', 'error_type': type(error).__name__,
            'frames': frames, 'frames_omitted': max(0, count - len(frames)), 'scientific_acceptance': False}


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
    data = (V5 / 'initialized_cold_audit_v5.py').read_bytes(); assert sha(data) == BASE_SHA
    before = data.decode(); assert before.count(OLD_FORMAT) == 1
    after = before.replace('initialized_cold_audit_v5.py POLICY POLICY_SHA256', 'initialized_cold_audit_v6.py POLICY POLICY_SHA256')
    after = after.replace(OLD_FORMAT, NEW_FORMAT)
    after = after.replace("if __name__ == '__main__':", HELPER + "if __name__ == '__main__':", 1)
    old, new = ast.parse(before), ast.parse(after)
    new.body[0] = old.body[0]
    new.body = [node for node in new.body if not isinstance(node, ast.FunctionDef) or node.name != 'refusal_frame_report_v6']
    old_main, new_main = old.body[-1], new.body[-1]
    assert isinstance(old_main, ast.If) and isinstance(new_main, ast.If)
    old_try, new_try = old_main.body[-1], new_main.body[-1]
    assert isinstance(old_try, ast.Try) and isinstance(new_try, ast.Try)
    new_try.handlers[0].body[0] = old_try.handlers[0].body[0]
    assert ast.dump(old, include_attributes=False) == ast.dump(new, include_attributes=False)
    reader = HERE / 'initialized_cold_audit_v6.py'; reader.write_text(after)
    source = (V5 / 'initialized-cold-policy-04af74c1-v5.json').read_bytes(); assert sha(source) == POLICY_SHA
    policy = rebind(json.loads(source)); policy['reader_sha256'] = sha(reader.read_bytes())
    policy['provenance']['reader_base_v5'] = pin(V5 / 'initialized_cold_audit_v5.py')
    policy['provenance']['preserved_actual_v5_refusal'] = pin(V5 / 'initialized-cold-v5-actual-refusal-receipt-20261016.json')
    policy['provenance']['preserved_actual_v5_stdout'] = pin(V5 / 'initialized-cold-v5-actual-stdout-20261016.json')
    policy_name = 'initialized-cold-policy-04af74c1-v6.json'; dump(policy_name, policy)
    command = rebind(json.loads((V5 / 'initialized-cold-command-04af74c1-v5.json').read_bytes()))
    command['command'][-3] = COLD + '/control/' + reader.name
    command['command'][-2] = COLD + '/control/' + policy_name
    command['command'][-1] = sha((HERE / policy_name).read_bytes())
    files = command['control_files']; files.pop('initialized_cold_audit_v5.py'); files.pop('initialized-cold-policy-04af74c1-v5.json')
    files[reader.name] = pin(reader, COLD + '/control/' + reader.name)
    files[policy_name] = pin(HERE / policy_name, COLD + '/control/' + policy_name)
    command['control_total_bytes'] = sum(row['bytes'] for row in files.values())
    dump('initialized-cold-command-04af74c1-v6.json', command)
    dump('initialized-cold-v6-inverse.json', {'date': '2026-10-16 ET', 'base': pin(V5 / 'initialized_cold_audit_v5.py'),
        'successor': pin(reader), 'allowed_delta': ['invocation example name', 'refusal formatter call',
            'bounded frame-only refusal formatter'], 'complete_ast_inverse': True,
        'all_prior_functions_byte_unchanged': True, 'error_text_locals_source_payload_omitted': True,
        'prior_versions_and_refusal_preserved': True, 'actual_reader_executed': False})


if __name__ == '__main__': build()
