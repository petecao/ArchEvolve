#!/usr/bin/env python3
"""2026-10-15 ET. Plan a source archive; mutate only with explicit closeout gates.

No deletion is implemented. Emitted cleanup commands require root review and fresh
expected-tip/use checks. Historical tips become archive parents, not main merges.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess

PREFIX = 'codex/probata-'
DIRTY_ALLOWED = {'/private/tmp/probata-standard-at-view',
                 '/private/tmp/probata-vector-ownership'}


def run(repo, *args, data=None):
    return subprocess.check_output(['git', '-C', str(repo), *args], input=data)


def git(repo, *args):
    return run(repo, *args).decode().strip()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def worktrees(repo):
    out = []
    for block in git(repo, 'worktree', 'list', '--porcelain').split('\n\n'):
        row = dict(line.split(' ', 1) if ' ' in line else (line, '')
                   for line in block.splitlines())
        if row:
            out.append(row)
    return out


def refs(repo):
    local = {}
    for line in git(repo, 'for-each-ref', '--format=%(refname) %(objectname)',
                    'refs/heads').splitlines():
        ref, oid = line.split()
        if ref.startswith('refs/heads/' + PREFIX):
            local[ref] = oid
    remote = {}
    for line in git(repo, 'ls-remote', '--heads', 'origin',
                    'refs/heads/' + PREFIX + '*').splitlines():
        oid, ref = line.split()
        remote[ref] = oid
    return local, remote


def status(repo):
    return git(repo, 'status', '--porcelain=v1', '--untracked-files=all')


def untracked(repo):
    paths = run(repo, 'ls-files', '--others', '--exclude-standard', '-z',
                '--', 'swdb-project').split(b'\0')
    out = {}
    for raw in paths:
        if not raw:
            continue
        name = os.fsdecode(raw)
        path = Path(repo) / name
        data = os.fsencode(os.readlink(path)) if path.is_symlink() else path.read_bytes()
        mode = '120000' if path.is_symlink() else ('100755' if path.stat().st_mode & 0o111 else '100644')
        out[name] = {'oid': run(repo, 'hash-object', '--stdin', data=data).decode().strip(),
                     'mode': mode}
    return out


def snapshot(repo):
    # Refuse outside-scope edits before Git's index snapshot can capture them.
    outside = git(repo, 'status', '--porcelain=v1', '--untracked-files=all',
                  '--', '.', ':(exclude)swdb-project')
    if outside:
        raise RuntimeError('Outside-SWDB edits require a separate recovery disposition: ' + str(repo))
    before = {'head': git(repo, 'rev-parse', 'HEAD'),
              'index_tree': git(repo, 'write-tree'),
              'cached_patch_sha256': digest(run(repo, 'diff', '--cached', '--binary', '--full-index')),
              'unstaged_patch_sha256': digest(run(repo, 'diff', '--binary', '--full-index')),
              'untracked': untracked(repo)}
    old = git(repo, 'rev-parse', '--verify', 'refs/stash') if subprocess.run(
        ['git', '-C', str(repo), 'show-ref', '--verify', '--quiet', 'refs/stash']).returncode == 0 else None
    subprocess.run(['git', '-C', str(repo), 'stash', 'push', '--include-untracked',
                    '-m', 'Probata source recovery 2026-10-15', '--', 'swdb-project'], check=True)
    oid = git(repo, 'rev-parse', 'refs/stash')
    assert oid != old, 'No new recovery stash created'
    assert git(repo, 'rev-parse', oid + '^2^{tree}') == before['index_tree']
    assert digest(run(repo, 'diff', '--binary', '--full-index', oid+'^1', oid+'^2')) == before['cached_patch_sha256']
    assert digest(run(repo, 'diff', '--binary', '--full-index', oid+'^2', oid)) == before['unstaged_patch_sha256']
    parents = git(repo, 'rev-list', '--parents', '-n', '1', oid).split()[1:]
    saved = {}
    if len(parents) == 3:
        for raw in run(repo, 'ls-tree', '-r', '-z', oid+'^3').split(b'\0'):
            if raw:
                header, name = raw.split(b'\t', 1)
                mode, _kind, blob = header.decode().split()
                saved[os.fsdecode(name)] = {'oid': blob, 'mode': mode}
    assert saved == before['untracked'], 'Untracked recovery tree differs'
    assert not status(repo), 'Worktree still dirty after scoped recovery stash'
    return {'worktree': str(repo), 'stash': oid, 'before': before,
            'restore': ['git', 'stash', 'apply', '--index', oid],
            'boundary': 'Stash and archive ancestry retained; original index/untracked verified.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--final-main', required=True, help='Exact final pushed yanrujhou_main commit')
    parser.add_argument('--tag', default='probata-source-recovery-20261015')
    parser.add_argument('--execute', action='store_true', help='Create stashes/archive/tag/bundle only; no cleanup')
    parser.add_argument('--workers-stopped', action='store_true', help='Root confirmed agents and all evaluations stopped')
    args = parser.parse_args()
    repo = args.repo.resolve()
    feature = repo/'swdb-project/.scratch/probata-proof-of-concept-2026-10-13'
    recovery = feature/'recovery'
    assert git(repo, 'rev-parse', 'yanrujhou_main') == args.final_main
    assert git(repo, 'ls-remote', '--heads', 'origin', 'refs/heads/yanrujhou_main').split()[0] == args.final_main
    local, remote = refs(repo)
    wts = [w for w in worktrees(repo) if w.get('branch', '').startswith('refs/heads/'+PREFIX)]
    dirty = [w for w in wts if status(w['worktree'])]
    manifest = {'date': '2026-10-15 ET', 'final_main': args.final_main,
                'local_refs': local, 'remote_refs': remote, 'worktrees': wts,
                'dirty_worktrees': [w['worktree'] for w in dirty], 'snapshots': [],
                'boundary': 'Unmerged historical tips are archived, never described as merged into main.'}
    if not args.execute:
        print(json.dumps(manifest, indent=2))
        return
    assert args.workers_stopped, 'Root must confirm no running agent/evaluation before snapshots'
    assert shutil.disk_usage(repo).free >= 1024**3, 'Recovery needs at least 1 GiB free'
    git(repo, 'check-ref-format', 'refs/tags/'+args.tag)
    assert git(repo, 'symbolic-ref', '--short', 'HEAD') == 'yanrujhou_main'
    assert not status(repo), 'Primary final-main checkout must be clean'
    assert not (recovery/'source-recovery.bundle').exists(), 'Never overwrite existing recovery bundle'
    assert subprocess.run(['git', '-C', str(repo), 'show-ref', '--verify', '--quiet',
                           'refs/tags/'+args.tag]).returncode != 0, 'Never replace an existing archive tag'
    assert not git(repo, 'ls-remote', '--tags', 'origin', 'refs/tags/'+args.tag), 'Remote tag already exists'
    assert {w['worktree'] for w in dirty} <= DIRTY_ALLOWED, 'Unknown dirty worktree requires root review'
    for w in dirty:
        manifest['snapshots'].append(snapshot(Path(w['worktree'])))
    parents = list(dict.fromkeys([args.final_main, *local.values(), *remote.values(),
                                  *(s['stash'] for s in manifest['snapshots'])]))
    for oid in parents:
        git(repo, 'cat-file', '-e', oid+'^{commit}')
    tree = git(repo, 'rev-parse', args.final_main+'^{tree}')
    command = ['git', '-C', str(repo), 'commit-tree', tree]
    for oid in parents:
        command += ['-p', oid]
    archive = subprocess.check_output(command, input=b'Probata source recovery 2026-10-15; historical parent archive, not main integration.\n').decode().strip()
    # The remote annotated tag retains branch names and exact snapshot reconstruction metadata.
    # Its commit tree is still exactly final main; historical tips are archive parents only.
    manifest['archive_commit'] = archive
    manifest['archive_tag'] = args.tag
    subprocess.run(['git', '-C', str(repo), 'tag', '-a', args.tag, archive, '--file=-'],
                   input=('Probata source recovery 2026-10-15\n\n'+json.dumps(manifest, indent=2)+'\n').encode(), check=True)
    subprocess.run(['git', '-C', str(repo), 'push', 'origin', 'refs/tags/'+args.tag], check=True)
    peeled = git(repo, 'ls-remote', '--tags', 'origin', 'refs/tags/'+args.tag+'^{}')
    assert peeled.split()[0] == archive, 'Remote archive tag verification failed'
    recovery.mkdir(exist_ok=True)
    assert subprocess.run(['git', '-C', str(repo), 'check-ignore', '-q', str(recovery/'source-recovery.bundle')]).returncode == 0
    subprocess.run(['git', '-C', str(repo), 'bundle', 'create', str(recovery/'source-recovery.bundle'),
                    'refs/tags/'+args.tag], check=True)
    subprocess.run(['git', '-C', str(repo), 'bundle', 'verify', str(recovery/'source-recovery.bundle')], check=True)
    assert (recovery/'source-recovery.bundle').stat().st_size <= 256*1024**2, 'Bundle exceeded 256 MiB budget; retained for inspection'
    manifest.update({'archive_commit': archive, 'archive_tag': args.tag,
                     'bundle_sha256': digest((recovery/'source-recovery.bundle').read_bytes()),
                     'bundle_bytes': (recovery/'source-recovery.bundle').stat().st_size,
                     'restore_tip': 'git switch -c codex/probata-recovered-<name> <expected_tip>',
                     'restore_bundle': 'git fetch <bundle-path> refs/tags/'+args.tag+':refs/tags/'+args.tag})
    # Commands only. Root rechecks current-use, expected tips and archive ancestry.
    commands = []
    for ref, tip in remote.items():
        commands.append(['git', 'push', '--force-with-lease='+ref+':'+tip, 'origin', ':'+ref])
    for w in wts:
        path = Path(w['worktree'])
        if path != repo and str(path).startswith('/private/tmp/probata-'):
            commands.append(['git', 'worktree', 'remove', str(path)])
    for ref in local:
        commands.append(['git', 'branch', '-D', ref.removeprefix('refs/heads/')])
    manifest['cleanup_commands_review_only'] = [shlex.join(c) for c in commands]
    (recovery/'source-recovery-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps({'archive': archive, 'tag': args.tag, 'bundle': str(recovery/'source-recovery.bundle'),
                      'snapshots': len(manifest['snapshots']), 'cleanup': 'Not executed; commands in local manifest.'}))


if __name__ == '__main__':
    main()
