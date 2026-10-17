"""2026-10-16 ET. Remove only the exact merged, idle worktrees and refs in the saved snapshot."""
import datetime
import json
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SNAPSHOT = json.loads((HERE/'recovery-snapshot.json').read_text())
RESULT = {'date_et': '2026-10-16', 'state': 'preflight', 'removed_worktrees': [],
          'preserved_worktrees': [], 'deleted_local_refs': [], 'deleted_remote_refs': []}


def save():
    (HERE/'cleanup-result.json').write_text(json.dumps(RESULT, indent=2)+'\n')


def git(*args, cwd=ROOT, text=True):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(cwd), *args],
                                   text=text, timeout=30).strip()


def worktrees():
    rows = []
    for block in git('worktree', 'list', '--porcelain').split('\n\n'):
        rows.append(dict(line.split(' ', 1) if ' ' in line else (line, True)
                         for line in block.splitlines()))
    return rows


def reader_check():
    targets = [r['path'] for r in SNAPSHOT['worktrees']]
    uid = os.getuid()
    ps = subprocess.run(['/bin/ps', '-axo', 'pid=,uid=,ppid=,command='],
                        check=True, capture_output=True, text=True, timeout=15)
    command_users = []
    count = 0
    for line in ps.stdout.splitlines():
        row = line.strip().split(None, 3)
        if len(row) < 4 or int(row[1]) != uid:
            continue
        count += 1
        found = [p for p in targets if p in row[3]]
        if found:
            command_users.append({'pid': int(row[0]), 'paths': found})
    scan = subprocess.run(['/usr/sbin/lsof', '-n', '-P', '-w', '-u', str(uid), '-F0pcufn'],
                          check=True, capture_output=True, timeout=30)
    assert not scan.stderr, scan.stderr
    pid = descriptor = None
    users = []
    for field in scan.stdout.split(b'\0'):
        field = field.lstrip(b'\n')
        if not field:
            continue
        value = os.fsdecode(field[1:])
        if field[:1] == b'p':
            pid = int(value)
        elif field[:1] == b'f':
            descriptor = value
        elif field[:1] == b'n':
            found = [p for p in targets if value == p or value.startswith(p+'/')]
            if found:
                users.append({'pid': pid, 'descriptor': descriptor, 'paths': found})
    result = {'own_processes': count, 'command_line_users': command_users, 'open_file_or_cwd_users': users}
    assert not command_users and not users, result
    return result


def main():
    assert ROOT == Path('/Users/yanrujhou/CLionProjects/ArchEvolve')
    assert git('branch', '--show-current') == 'yanrujhou_main'
    assert git('merge-base', '--is-ancestor', SNAPSHOT['anchor'], 'HEAD') == ''
    tag = SNAPSHOT['recovery_tag']
    assert git('rev-parse', tag+'^{}') == SNAPSHOT['anchor']
    assert SNAPSHOT['anchor']+'\trefs/tags/'+tag+'^{}' in git('ls-remote', 'origin', 'refs/tags/'+tag+'^{}')
    assert git('stash', 'list', '--format=%H').splitlines() == SNAPSHOT['stash_heads_preserved']
    for ref in SNAPSHOT['remote_branches']:
        assert not git('ls-remote', '--heads', 'origin', ref['ref'])
        RESULT['deleted_remote_refs'].append(ref)
    RESULT['reader_check'] = reader_check()
    RESULT['main_head_before'] = git('rev-parse', 'HEAD')
    RESULT['free_bytes_before'] = shutil.disk_usage(ROOT).free
    RESULT['state'] = 'removing_worktrees'
    save()
    for row in SNAPSHOT['worktrees']:
        path = Path(row['path'])
        current = [w for w in worktrees() if w['worktree'] == str(path)]
        assert len(current) == 1 and current[0]['HEAD'] == row['head']
        assert 'locked' not in current[0] and path.resolve() == path and path != ROOT
        assert git('status', '--porcelain=v1', '--untracked-files=all', cwd=path) == ''
        assert git('merge-base', '--is-ancestor', row['head'], SNAPSHOT['anchor']) == ''
        ignored = git('ls-files', '--others', '--ignored', '--exclude-standard', '-z', cwd=path, text=False)
        names = [os.fsdecode(x) for x in ignored.split(b'\0') if x]
        assert sorted(names) == sorted(r['path'] for r in row['ignored_files'])
        for name in names:
            assert '__pycache__/' in name or name.startswith('.pytest_cache/') or '/.pytest_cache/' in name
            assert (path/name).is_file() and not (path/name).is_symlink()
        result = subprocess.run(['git', '-C', str(ROOT), 'worktree', 'remove', str(path)],
                                capture_output=True, text=True, timeout=60)
        if result.returncode:
            RESULT['preserved_worktrees'].append({'path': str(path), 'reason': result.stderr})
        else:
            assert not os.path.lexists(path)
            RESULT['removed_worktrees'].append(row['path'])
        save()
    attached = {w.get('branch') for w in worktrees()}
    targets = [r for r in SNAPSHOT['local_branches'] if r['ref'] not in attached]
    for row in targets:
        assert git('rev-parse', row['ref']) == row['head']
        assert git('merge-base', '--is-ancestor', row['head'], SNAPSHOT['anchor']) == ''
    transaction = 'start\n'+''.join('delete '+r['ref']+' '+r['head']+'\n' for r in targets)+'prepare\ncommit\n'
    subprocess.run(['git', '-C', str(ROOT), 'update-ref', '--stdin'], input=transaction,
                   check=True, capture_output=True, text=True, timeout=30)
    RESULT['deleted_local_refs'] = targets
    RESULT['worktrees_after'] = worktrees()
    RESULT['local_refs_after'] = git('for-each-ref', '--format=%(refname)', 'refs/heads').splitlines()
    RESULT['main_head_after'] = git('rev-parse', 'HEAD')
    assert RESULT['main_head_after'] == RESULT['main_head_before']
    assert git('stash', 'list', '--format=%H').splitlines() == SNAPSHOT['stash_heads_preserved']
    for row in SNAPSHOT['preserved_local_refs']:
        assert git('rev-parse', row['ref']) == row['head']
    RESULT['free_bytes_after'] = shutil.disk_usage(ROOT).free
    RESULT['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    RESULT['state'] = 'complete' if not RESULT['preserved_worktrees'] else 'complete_with_preserved_worktrees'
    RESULT['recovery_tag'] = tag
    RESULT['stashes_preserved'] = True
    save()
    print(json.dumps({k: RESULT[k] for k in ['state', 'local_refs_after', 'worktrees_after',
                                            'recovery_tag', 'preserved_worktrees']}, indent=2))
    print(json.dumps({'removed_worktrees': len(RESULT['removed_worktrees']),
                      'deleted_local_branches': len(RESULT['deleted_local_refs']),
                      'deleted_remote_branches': len(RESULT['deleted_remote_refs'])}))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        RESULT['state'] = 'stopped_on_error'
        RESULT['error'] = repr(error)
        save()
        raise
