"""Author the narrow read-only Git-pipe correction; no remote execution."""
import ast
import hashlib
import json
import stat
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent.parent
original = (HERE / 'cold-auditor-v1.py').read_text()
assert hashlib.sha256(original.encode()).hexdigest() == '4a4182d08fc7d72e2aec7f201c0e8ef89219c534eeebe44ed89c0389ac4bd418'

old_git = '''def git(*args, input=None):
    return subprocess.check_output(['/usr/bin/git','--no-optional-locks','--no-replace-objects',
        '-c','core.preloadIndex=false','-c','core.fsmonitor=false','-c','index.threads=1',
        '-C',str(SOURCE),*args], input=input, timeout=45)
'''
new_git = '''READ_ONLY_GIT_ACTIVE = False


def git(*args, input=None):
    global READ_ONLY_GIT_ACTIVE
    require(not READ_ONLY_GIT_ACTIVE, 'no nested read-only Git call')
    READ_ONLY_GIT_ACTIVE = True
    try:
        kwargs = {'timeout': 45}
        if input is not None:
            kwargs['input'] = input
        return subprocess.check_output(['/usr/bin/git','--no-optional-locks','--no-replace-objects',
            '-c','core.preloadIndex=false','-c','core.fsmonitor=false','-c','index.threads=1',
            '-C',str(SOURCE),*args], **kwargs)
    finally:
        READ_ONLY_GIT_ACTIVE = False
'''
old_audit = '''        elif event=='open' and len(values)>1 and isinstance(values[1],str) and any(x in values[1] for x in 'wax+'):
            raise RuntimeError('remote writes forbidden')
'''
new_audit = '''        elif event=='open':
            filename, mode, flags = values
            writable = (isinstance(mode, str) and any(x in mode for x in 'wax+')) or (flags & os.O_ACCMODE) != os.O_RDONLY
            if writable:
                if isinstance(filename, int) and READ_ONLY_GIT_ACTIVE and stat.S_ISFIFO(os.fstat(filename).st_mode):
                    return  # Python's stdin pipe wrapper for fixed read-only Git.
                raise RuntimeError('remote writes forbidden: ' + json.dumps({
                    'filename': filename, 'mode': mode, 'flags': flags,
                    'call_site': 'fixed_read_only_git' if READ_ONLY_GIT_ACTIVE else 'outside_git'}))
'''
assert original.count(old_git) == original.count(old_audit) == 1
current = original.replace('import json\n', 'import json\nimport os\nimport stat\n', 1).replace(old_git, new_git).replace(old_audit, new_audit)
assert current.replace('import json\nimport os\nimport stat\n', 'import json\n', 1).replace(new_git, old_git).replace(new_audit, old_audit) == original
tree = ast.parse(current)
git_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'git')
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
audit_node = next(n for n in main.body if isinstance(n, ast.FunctionDef) and n.name == 'audit')
controls = []

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def fstat(descriptor):
    if descriptor == 4:
        return types.SimpleNamespace(st_mode=stat.S_IFIFO)
    if descriptor == 5:
        return types.SimpleNamespace(st_mode=stat.S_IFREG)
    raise OSError('scripted descriptor disappearance')

fake_os = types.SimpleNamespace(O_ACCMODE=3, O_RDONLY=0, fstat=fstat)
namespace = {'READ_ONLY_GIT_ACTIVE': False, 'os': fake_os, 'stat': stat,
             'json': json, 'require': require, 'SOURCE': Path('/inert/source')}
exec(compile(ast.fix_missing_locations(ast.Module(body=[audit_node, git_node], type_ignores=[])), '<extracted-guard-controls>', 'exec'), namespace)
audit = namespace['audit']
for name, active, values, refused in [
    ('inactive_fifo_write_refused', False, (4, 'w', 1), True),
    ('active_git_fifo_write_allowed', True, (4, 'w', 1), False),
    ('active_git_regular_fd_write_refused', True, (5, 'w', 1), True),
    ('active_git_path_write_refused', True, ('/inert/file', 'w', 1), True),
    ('outside_path_write_refused', False, ('/inert/file', 'w', 1), True),
    ('integer_flags_write_refused', False, ('/inert/file', None, 1), True),
    ('ordinary_read_allowed', False, ('/inert/file', 'r', 0), False),
    ('descriptor_failure_preserved', True, (6, 'w', 1), True),
]:
    namespace['READ_ONLY_GIT_ACTIVE'] = active
    try:
        audit('open', values)
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

output = HERE / 'cold-auditor-v2.py'
assert not output.exists(), 'never overwrite an authored version'
output.write_text(current)
receipt = {
    'created': '2026-10-16 ET',
    'classification': 'INERT_PASSIVE_GIT_PIPE_GUARD_CORRECTION',
    'previous_auditor_sha256': hashlib.sha256(original.encode()).hexdigest(),
    'previous_actual_refusal': {'bytes': 164, 'sha256': '2b45e56f5c661ff0125e2a28a003772c2138c749d3b9968fcd241130d4428ceb',
                                'checks_before_refusal': 814, 'error': 'remote writes forbidden'},
    'local_read_only_reproduction': {'event': 'open', 'filename_type': 'int', 'filename': 4,
                                     'mode': 'w', 'flags': 16778753, 'is_fifo': True,
                                     'classification': 'Python subprocess stdin pipe wrapper; no filesystem write'},
    'auditor': {'path': str(output.relative_to(BASE)), 'sha256': hashlib.sha256(current.encode()).hexdigest(), 'bytes': len(current.encode())},
    'exact_inverse_to_v1': True,
    'scripted_boundary_controls': controls,
    'controls_external_processes_executed': 0,
    'author_remote_execution': False,
    'acceptance': False,
    'scope': 'Only omit unused Git stdin and permit an integer FIFO descriptor during fixed read-only Git; all pathname/regular-file writes remain refused. No scientific/source/formula/proof policy changes.',
}
receipt_path = BASE / 'evidence/t25-closed-lifetime6-cold-auditor-preparation-v2-20261016.json'
assert not receipt_path.exists()
receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
print(json.dumps({'auditor': receipt['auditor'], 'receipt_sha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest(), 'controls': len(controls)}))
