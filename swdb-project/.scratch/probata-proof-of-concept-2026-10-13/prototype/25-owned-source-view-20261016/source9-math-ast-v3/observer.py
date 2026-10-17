"""2026-10-16 ET. Inert complete26 parsed mathematical metadata capture.

No semantic normalization, support adoption, proof, project import or tool call.
Only the exact reviewed stdin entry may be separately admitted by the root.
"""
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import time

MATH = frozenset({'declare-sort', 'declare-fun', 'declare-const', 'declare-datatype',
                  'declare-datatypes', 'define-fun', 'assert'})
OPAQUE = frozenset({'set-info', 'set-option', 'set-logic', 'check-sat', 'get-info'})
MAX_FILE = 1024*1024
MAX_OUTPUT = 2*1024*1024


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def identity(st):
    return [st.st_dev, st.st_ino, st.st_mode, st.st_nlink, st.st_uid, st.st_gid,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns]


def read_input(path, expected):
    """Full no-follow read and complete nine-field file/parent identity check."""
    need(path in ALLOWED, 'closed selected input path')
    value = Path(path)
    need(value.is_absolute() and '..' not in value.parts, 'canonical absolute input')
    parents = [(parent, identity(parent.lstat())) for parent in reversed(value.parents)]
    need(all(stat.S_ISDIR(row[2]) for _, row in parents), 'no symlink or special input ancestor')
    for parent, row in parents:
        key = str(parent)
        need(key not in PARENTS or PARENTS[key] == row, 'original physical parent identity unchanged')
        PARENTS[key] = row
    before = value.lstat()
    need(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= MAX_FILE, 'bounded regular mathematical input')
    descriptor = os.open(value, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        stamp = identity(before)
        need(identity(os.fstat(descriptor)) == stamp, 'no-follow original descriptor')
        pieces, remaining = [], MAX_FILE+1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            pieces.append(chunk); remaining -= len(chunk)
        raw = b''.join(pieces)
        need(len(raw) == before.st_size and len(raw) <= MAX_FILE, 'full bounded input extent')
        need(stamp == identity(os.fstat(descriptor)) == identity(value.lstat()), 'stable complete input read')
        need(all(row == identity(parent.lstat()) for parent, row in parents), 'stable physical input ancestors')
        need(len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256'],
             'exact retained mathematical input content')
        need(path not in FILES or FILES[path] == stamp, 'original nine-field input identity unchanged')
        FILES[path] = stamp
        return raw
    finally:
        os.close(descriptor)


def audit(event, args):
    if event == 'open':
        filename, mode, flags = args
        allowed_flags = os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, 'O_CLOEXEC', 0)
        need(isinstance(filename, str) and filename in ALLOWED and
             not (isinstance(mode, str) and any(c in mode for c in 'wax+')) and
             isinstance(flags, int) and flags >= 0 and flags & ~allowed_flags == 0,
             'only exact selected read-only physical file opens are allowed')
    forbidden = {'subprocess.Popen', 'ctypes.dlopen', 'os.system', 'os.posix_spawn', 'os.exec', 'os.fork',
                 'os.remove', 'os.rmdir', 'os.rename', 'os.link', 'os.symlink', 'os.mkdir',
                 'os.chmod', 'os.chown', 'os.truncate', 'os.utime', 'os.chdir', 'os.kill', 'os.killpg',
                 'os.listdir', 'os.scandir', 'resource.setrlimit', 'resource.prlimit'}
    if event in forbidden or event.startswith('socket.'):
        raise RuntimeError('read-only capture forbids mutation, execution, network or resource changes')


def atom_bounds(commands):
    pending = [(commands, 0)]
    while pending:
        value, depth = pending.pop()
        need(depth <= 160, 'mathematical term depth cap')
        if isinstance(value, str):
            need(len(value.encode()) <= 2048, 'complete mathematical atom byte cap')
        else:
            need(isinstance(value, list), 'complete S-expression node kind')
            pending.extend((child, depth+1) for child in value)


def command_shape(command):
    head = command[0]
    if head == 'assert':
        need(len(command) == 2, 'complete assertion command shape')
    elif head == 'define-fun':
        need(len(command) == 5 and isinstance(command[1], str) and isinstance(command[2], list),
             'complete definition command shape')
    elif head == 'declare-fun':
        need(len(command) == 4 and isinstance(command[1], str) and isinstance(command[2], list),
             'complete function declaration shape')
    elif head in {'declare-const', 'declare-sort', 'declare-datatype'}:
        need(len(command) == 3 and isinstance(command[1], str), 'complete named declaration shape')
    elif head == 'declare-datatypes':
        need(len(command) == 3 and all(isinstance(value, list) for value in command[1:]),
             'complete datatype declaration shape')


def capture_task(text, row, trees):
    commands = forms(text)
    atom_bounds(commands)
    need(all(isinstance(command, list) and command and isinstance(command[0], str) and
             command[0] in MATH | OPAQUE for command in commands), 'complete closed command-head census')
    census = [{'index': index, 'kind': command[0], 'sha256': digest(command)}
              for index, command in enumerate(commands)]
    need(compact(census) == compact(row['complete_command_census']), 'exact prior full ordered command census')
    queries = [index for index, command in enumerate(commands) if command[0] == 'check-sat']
    need(len(queries) == 1 and commands[queries[0]] == ['check-sat'] and
         all(command == ['get-info', ':reason-unknown'] for command in commands[queries[0]+1:]) and
         not any(command[0] == 'get-info' for command in commands[:queries[0]]),
         'one closed query and exact metadata epilogue; never executed')
    assertions = [index for index, command in enumerate(commands) if command[0] == 'assert']
    need(assertions and assertions[-1] < queries[0], 'one sole last-assert goal role is required')
    goal = assertions[-1]
    refs = []
    for index, command in enumerate(commands):
        key, head = census[index]['sha256'], command[0]
        if head in MATH:
            need(key not in trees or trees[key] == command, 'full-command digest collision refused')
            trees[key] = command
        refs.append({**census[index], 'tree_ref': key if head in MATH else None,
                     'role': 'goal' if index == goal else 'support' if head == 'assert' else
                             'definition' if head == 'define-fun' else 'declaration' if head in MATH else 'administrative'})
    need(sum(ref['role'] == 'goal' for ref in refs) == 1, 'exactly one goal reference retained')
    return {'id': row['id'], 'artifact': row['artifact'], 'commands': refs,
            'complete_command_census_sha256': digest(census),
            'goal_command_index': goal, 'goal_command_sha256': census[goal]['sha256'],
            'support_assertions': len(assertions)-1, 'all_commands_retained': True,
            'semantic_equivalence_or_support_admission': False}


def publication(result):
    payload = compact(result)+b'\n'
    need(len(payload) <= MAX_OUTPUT, 'complete parsed metadata output cap; no truncation')
    return payload


def main():
    need(sys.flags.isolated and sys.flags.dont_write_bytecode and not sys.flags.optimize,
         'isolated bytecode-free nonoptimized capture')
    resource.setrlimit(resource.RLIMIT_AS, (512*1024**2, 512*1024**2))
    signal.alarm(110)
    started = time.monotonic()
    need(len(CONTEXT['tasks']) == 26 and len(CONTEXT['theories']) == 3, 'complete26 task and three-theory input set')
    root = Path(CONTEXT['raw_root'])
    inputs = []
    for row in CONTEXT['tasks']:
        relative = Path(row['artifact']['relative'])
        need(not relative.is_absolute() and '..' not in relative.parts and relative.suffix in {'.smt2', '.psmt2'},
             'canonical retained mathematical task path')
        inputs.append((str(root/relative), row['artifact']))
    for row in CONTEXT['theories']:
        path = Path(row['path'])
        need(path.is_absolute() and '..' not in path.parts and root in path.parents and path.suffix == '.mlw',
             'canonical retained theory path')
        inputs.append((str(path), row))
    need(len({path for path, _ in inputs}) == 29, 'exact distinct29 physical inputs')
    global ALLOWED, FILES, PARENTS
    ALLOWED = frozenset(path for path, _ in inputs)
    FILES, PARENTS = {}, {}
    sys.addaudithook(audit)
    trees, tasks, observed = {}, [], []
    for (path, expected), row in zip(inputs[:26], CONTEXT['tasks']):
        raw = read_input(path, expected)
        tasks.append(capture_task(raw.decode('utf-8'), row, trees))
        observed.append({'path': path, 'bytes': len(raw), 'sha256': expected['sha256'], 'nine_stat': FILES[path]})
    for path, expected in inputs[26:]:
        raw = read_input(path, expected)
        observed.append({'path': path, 'bytes': len(raw), 'sha256': expected['sha256'], 'nine_stat': FILES[path]})
    for path, expected in inputs:
        read_input(path, expected)
    need(len(FILES) == 29, 'every selected input checked before and after')
    result = {'date': '2026-10-16 ET', 'classification': 'COMPLETE26_PARSED_MATHEMATICAL_METADATA_ONLY',
        'prior_capture': CONTEXT['prior_capture'], 'raw_root': CONTEXT['raw_root'],
        'source_commit': CONTEXT['source_commit'], 'producer': CONTEXT['producer'],
        'tasks': tasks, 'deduplicated_complete_math_commands': trees,
        'unique_math_commands': len(trees), 'task_count': 26, 'physical_inputs': observed,
        'theory_pins': CONTEXT['theories'], 'retained_outcomes': CONTEXT['retained_outcomes'],
        'all29_content_and_nine_stat_pre_post_equal': True,
        'complete_command_order_and_sole_last_assert_goals_retained': True,
        'administrative_payloads_exported': False, 'original_C_Cpp_TU_or_raw_files_exported': False,
        'scientific_acceptance': False, 'mathematical_acceptance': False,
        'source_Heap_Typed_caller_default_admission': False, 'public_proof_record_created': False,
        'actual_solver_submission_or_continuous_runtime_identity_attested': False,
        'runtime_scope': 'Finite selected-input syntax observation under system Python only; no current or historical complete runtime/loader/source-to-binary closure.',
        'address_space_bytes': 512*1024**2, 'CPU_limit_set': False, 'internal_alarm_seconds': 110,
        'elapsed_seconds': time.monotonic()-started}
    payload = publication(result)
    sys.stdout.buffer.write(payload); sys.stdout.buffer.flush()
    need(time.monotonic()-started < 110, 'settled parsed metadata publication deadline')
    return 2


if __name__ == '__main__':
    try:
        exit_code = main()
    except Exception as error:
        sys.stdout.buffer.write(compact({'classification': 'REFUSED_COMPLETE26_MATH_METADATA_CAPTURE',
            'scientific_acceptance': False, 'error_type': type(error).__name__, 'reason': str(error)[:1024]})+b'\n')
        exit_code = 1
    raise SystemExit(exit_code)
