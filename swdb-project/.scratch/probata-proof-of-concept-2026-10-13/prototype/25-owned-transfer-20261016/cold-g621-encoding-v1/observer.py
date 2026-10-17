"""2026-10-16 ET. INERT bounded G621 encoding metadata probe.

No compiler, native helper, verifier, solver, subprocess, project import, socket,
filesystem mutation or proof re-execution. Root must review/admit the frozen
stdin entry. This captures shapes/hashes/booleans and always keeps proof pending.
"""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def file_identity(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_nlink, st.st_uid, st.st_gid,
            st.st_size, st.st_mtime_ns, st.st_ctime_ns)


def physical_read(path, wanted, cap=1024*1024):
    path = Path(path)
    need(path.is_absolute() and '..' not in path.parts, 'absolute canonical read path')
    parents = [(p, p.lstat()) for p in reversed(path.parents)]
    need(all(stat.S_ISDIR(st.st_mode) for p, st in parents), 'physical directory ancestors')
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_size <= cap, 'bounded regular input')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        need(file_identity(before) == file_identity(os.fstat(descriptor)), 'original open descriptor')
        chunks = []; remaining = cap+1
        while remaining:
            data = os.read(descriptor, min(remaining, 65536))
            if not data:
                break
            chunks.append(data); remaining -= len(data)
        raw = b''.join(chunks)
        need(len(raw) == before.st_size and len(raw) <= cap, 'bounded full read')
        need(file_identity(before) == file_identity(os.fstat(descriptor)) == file_identity(path.lstat()), 'stable input read')
        need(all(file_identity(st) == file_identity(p.lstat()) for p, st in parents), 'stable physical ancestors')
        need(hashlib.sha256(raw).hexdigest() == wanted['sha256'], 'exact retained physical content')
        if 'bytes' in wanted:
            need(len(raw) == wanted['bytes'], 'exact retained size')
        return raw
    finally:
        os.close(descriptor)


def audit(event, args):
    if event == 'subprocess.Popen' or event.startswith('socket.') or event in {
            'os.system', 'os.posix_spawn', 'os.exec', 'os.fork', 'ctypes.dlopen'}:
        raise RuntimeError('process/native/network execution forbidden')
    if event == 'open':
        filename, mode, flags = args
        need(not (isinstance(mode, str) and any(c in mode for c in 'wax+'))
             and flags & os.O_ACCMODE == os.O_RDONLY
             and not flags & (os.O_CREAT | os.O_TRUNC | os.O_APPEND), 'read-only opens')
        if not isinstance(filename, int):
            need(os.fspath(filename) in ALLOWED_PATHS, 'closed selected read set')


def main():
    need(sys.flags.isolated and sys.flags.dont_write_bytecode and not sys.flags.optimize,
         'isolated bytecode-free nonoptimized observer')
    resource.setrlimit(resource.RLIMIT_AS, (512*1024**2, 512*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    signal.alarm(60)
    need(len(CONTEXT['tasks']) == 20 and len({r['artifact']['relative'] for r in CONTEXT['tasks']}) == 20,
         'exact twenty retained artifacts')
    global ALLOWED_PATHS
    root = Path(CONTEXT['raw_root'])
    selected = []
    for row in CONTEXT['tasks']:
        relative = Path(row['artifact']['relative'])
        need(not relative.is_absolute() and '..' not in relative.parts and relative.suffix == '.psmt2',
             'closed canonical task path')
        selected.append(str(root/relative))
    ALLOWED_PATHS = set(selected+[CONTEXT['source_theory']['path']])
    sys.addaudithook(audit)
    theory = physical_read(CONTEXT['source_theory']['path'], CONTEXT['source_theory'])
    need(b'type state = { active : map int bool; backing : map int int }' in theory and
         b'function empty (dummy:int) : state =' in theory,
         'pinned source product and integer dummy signature')
    result = {'date': '2026-10-16 ET', 'classification': 'BOUNDED_ENCODING_METADATA_CAPTURE_ONLY',
              'prior_capture_sha256': CONTEXT['capture_sha256'], 'source_commit': CONTEXT['source_commit'],
              'source_theory_sha256': CONTEXT['source_theory']['sha256'],
              'source_fields': [{'name':'active','index':'Int','value':'Bool'},
                                {'name':'backing','index':'Int','value':'Int'}],
              'tasks': [], 'scientific_acceptance': False, 'mathematical_acceptance': False,
              'source_body_Typed_caller_default_acceptance': False,
              'actual_submission_attested': False,
              'runtime_boundary': 'This passive system-Python metadata observation does not retroactively pin original dynamic helpers, loaders, solver submissions or continuous runtime identity.'}
    total = 0
    allowed = {'set-logic','set-info','set-option','declare-sort','declare-fun',
               'declare-const','declare-datatypes','declare-datatype','define-fun',
               'assert','check-sat','get-info'}
    for row, path in zip(CONTEXT['tasks'], selected):
        raw = physical_read(path, row['artifact']); total += len(raw)
        need(total <= 2*1024**2, 'aggregate selected task byte cap')
        commands = forms(raw.decode('utf-8'))
        need(all(isinstance(c,list) and c and c[0] in allowed for c in commands), 'complete closed SMT command census')
        need(not any(s.startswith('@') for s in symbols(commands)), 'no source collision with reserved alpha identifiers')
        census = [{'index':i,'kind':c[0],'sha256':digest(c)} for i,c in enumerate(commands)]
        need(census == row['commands'], 'exact prior complete command census')
        checks = [i for i,c in enumerate(commands) if c[0]=='check-sat']
        need(len(checks)==1 and commands[checks[0]]==['check-sat'] and
             all(c==['get-info',':reason-unknown'] for c in commands[checks[0]+1:]),
             'single query metadata; never executed')
        inspected = inspect_task(commands, row['id'], CONTEXT['constant_map_support_hashes'],
                                 CONTEXT['primary_standard_support'])
        inspected.update(id=row['id'],artifact=row['artifact'],
                         prior_goal_equivalent=row['prior_goal_equivalent'],
                         prior_definition_decisions=row['prior_definitions'],
                         prior_unknown_support=row['prior_unknown_support'],
                         complete_command_census_sha256=digest(census),
                         declaration_census=[{'kind':c[0], 'sha256':digest(c),
                            'name':c[1] if len(c)>1 and isinstance(c[1],str) else None}
                            for c in commands if c[0] in {'declare-sort','declare-fun','declare-const','declare-datatypes','declare-datatype'}])
        result['tasks'].append(inspected)
    # Read every selected input once more against the same physical pins. No new
    # whole-raw/runtime or historical uninterrupted-identity claim is made.
    for row,path in zip(CONTEXT['tasks'],selected):
        physical_read(path,row['artifact'])
    physical_read(CONTEXT['source_theory']['path'],CONTEXT['source_theory'])
    result.update(tasks_observed=20, selected_bytes=total, selected_pre_post_equal=True,
                  full_semantic_adoption=False, unrecognized_terms_pending=True)
    payload=compact(result)+b'\n'
    need(len(payload)<=256*1024,'compact metadata stdout cap')
    sys.stdout.buffer.write(payload)
    return 2


if __name__ == '__main__':
    try:
        exit_code=main()
    except Exception as exc:
        payload=compact({'classification':'REFUSED_ENCODING_METADATA_PROBE',
                         'scientific_acceptance':False,'error_type':type(exc).__name__,
                         'reason':str(exc)[:1024]})+b'\n'
        sys.stdout.buffer.write(payload)
        exit_code=1
    raise SystemExit(exit_code)
