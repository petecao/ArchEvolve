"""Author V3 mutation-flag closure with compiler-free scripted controls."""
import ast
import hashlib
import json
import os
import stat
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
previous = (HERE / 'cold-auditor-v2.py').read_text()
assert hashlib.sha256(previous.encode()).hexdigest() == '348033757aeb332b50f3efcf0b65d58364206eae76e5c56aa20a1aa660cbdeb5'
old = "writable = (isinstance(mode, str) and any(x in mode for x in 'wax+')) or (flags & os.O_ACCMODE) != os.O_RDONLY"
new = old + ' or bool(flags & (os.O_CREAT | os.O_TRUNC | os.O_APPEND))'
assert previous.count(old) == 1
current = previous.replace(old, new)
assert current.replace(new, old) == previous
tree = ast.parse(current)
git_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'git')
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
audit_node = next(n for n in main.body if isinstance(n, ast.FunctionDef) and n.name == 'audit')

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def fstat(descriptor):
    if descriptor == 4:
        return types.SimpleNamespace(st_mode=stat.S_IFIFO)
    if descriptor == 5:
        return types.SimpleNamespace(st_mode=stat.S_IFREG)
    raise OSError('scripted descriptor disappearance')

fake_os = types.SimpleNamespace(O_ACCMODE=os.O_ACCMODE, O_RDONLY=os.O_RDONLY,
    O_CREAT=os.O_CREAT, O_TRUNC=os.O_TRUNC, O_APPEND=os.O_APPEND, fstat=fstat)
namespace = {'READ_ONLY_GIT_ACTIVE': False, 'os': fake_os, 'stat': stat,
             'json': json, 'require': require, 'SOURCE': Path('/inert/source')}
exec(compile(ast.fix_missing_locations(ast.Module(body=[audit_node, git_node], type_ignores=[])), '<extracted-guard-controls>', 'exec'), namespace)
controls = []
for name, active, values, refused in [
    ('inactive_fifo_write_refused', False, (4, 'w', os.O_WRONLY), True),
    ('active_git_fifo_write_allowed', True, (4, 'w', os.O_WRONLY), False),
    ('active_git_regular_fd_write_refused', True, (5, 'w', os.O_WRONLY), True),
    ('active_git_path_write_refused', True, ('/inert/file', 'w', os.O_WRONLY), True),
    ('outside_path_write_refused', False, ('/inert/file', 'w', os.O_WRONLY), True),
    ('integer_flags_write_refused', False, ('/inert/file', None, os.O_WRONLY), True),
    ('ordinary_read_allowed', False, ('/inert/file', 'r', os.O_RDONLY), False),
    ('descriptor_failure_preserved', True, (6, 'w', os.O_WRONLY), True),
    ('readonly_create_refused', False, ('/inert/file', None, os.O_RDONLY | os.O_CREAT), True),
    ('readonly_truncate_refused', False, ('/inert/file', None, os.O_RDONLY | os.O_TRUNC), True),
    ('readonly_append_refused', False, ('/inert/file', None, os.O_RDONLY | os.O_APPEND), True),
]:
    namespace['READ_ONLY_GIT_ACTIVE'] = active
    try:
        namespace['audit']('open', values)
    except (RuntimeError, OSError):
        assert refused, name
    else:
        assert not refused, name
    controls.append(name)

calls = []
def check_output(argv, **kwargs):
    assert namespace['READ_ONLY_GIT_ACTIVE']
    calls.append((argv, kwargs))
    if kwargs.get('input') == b'raise':
        raise RuntimeError('scripted Git boundary failure')
    return b'output'
namespace['subprocess'] = types.SimpleNamespace(check_output=check_output)
namespace['READ_ONLY_GIT_ACTIVE'] = False
assert namespace['git']('rev-parse', 'HEAD') == b'output'
assert calls[-1][1] == {'timeout': 45} and not namespace['READ_ONLY_GIT_ACTIVE']
controls.append('unused_git_stdin_not_opened')
assert namespace['git']('hash-object', '--no-filters', '--stdin-paths', input=b'/inert/file\n') == b'output'
assert calls[-1][1] == {'timeout': 45, 'input': b'/inert/file\n'} and not namespace['READ_ONLY_GIT_ACTIVE']
controls.append('required_git_stdin_only_scoped')
try:
    namespace['git']('hash-object', '--no-filters', '--stdin-paths', input=b'raise')
except RuntimeError as error:
    assert str(error) == 'scripted Git boundary failure' and not namespace['READ_ONLY_GIT_ACTIVE']
else:
    raise AssertionError('scripted boundary failure missing')
controls.append('git_scope_reset_preserves_exception')

output = HERE / 'cold-auditor-v3.py'
assert not output.exists()
output.write_text(current)
receipt = {
    'created': '2026-10-16 ET',
    'classification': 'INERT_PASSIVE_OPEN_MUTATION_FLAG_CLOSURE',
    'previous_auditor_sha256': hashlib.sha256(previous.encode()).hexdigest(),
    'previous_version_executed': False,
    'auditor': {'path': str(output.relative_to(BASE)), 'sha256': hashlib.sha256(current.encode()).hexdigest(), 'bytes': len(current.encode())},
    'exact_inverse_to_v2': True,
    'scripted_boundary_controls': controls,
    'controls_external_processes_executed': 0,
    'author_remote_execution': False,
    'acceptance': False,
    'scope': 'Only add O_CREAT/O_TRUNC/O_APPEND mutation flags to the open refusal; no scientific accounting changes. V1 refusal and V2 unexecuted preserved.',
}
receipt_path = BASE / 'evidence/t25-closed-lifetime6-cold-auditor-preparation-v3-20261016.json'
assert not receipt_path.exists()
receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
print(json.dumps({'auditor': receipt['auditor'], 'receipt_sha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest(), 'controls': len(controls)}))
