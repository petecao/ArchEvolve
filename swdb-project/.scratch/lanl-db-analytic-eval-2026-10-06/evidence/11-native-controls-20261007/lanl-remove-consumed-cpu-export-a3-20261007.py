"""Remove one integrated CPU export checkout. Updated 2026-10-07 ET.

Read-only by default. Raw evidence and immutable execution source are retained.
"""
from pathlib import Path
import argparse, datetime, json, os, re, socket, subprocess, sys

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('model', 'development', 'holdout', 'band-report'))
    parser.add_argument('commit')
    parser.add_argument('--remove', action='store_true')
    args = parser.parse_args()
    assert re.fullmatch('[0-9a-f]{40}', args.commit)
    assert socket.gethostname().split('.')[0] == 'mbit10'
    root = Path('/data1/yanruj')
    repo = root / 'ArchEvolve'
    source = root / 'ArchEvolve-lanl-cpu-model-validation-20261006-a1'
    path = root / ('ArchEvolve-lanl-cpu-' + args.phase + '-evidence-20261006-a3')
    branch = 'codex/lanl-cpu-' + args.phase + '-evidence-a3'
    def git(folder, *arguments):
        return subprocess.check_output(['git', '-C', str(folder), *arguments], text=True, timeout=60).strip()
    def points_inside(target):
        return target == str(path) or target.startswith(str(path) + '/')
    def free_bytes():
        st = os.statvfs('/data1')
        return st.f_bavail * st.f_frsize
    for lane in ('mbit10-evaluation-node0', 'mbit10-evaluation-node1', 'mbit10-evaluation'):
        assert json.loads((root / 'lact-host-lease' / (lane + '.meta.json')).read_text())['state'] == 'released'
    assert path.is_dir() and not path.is_symlink()
    assert git(path, 'rev-parse', 'HEAD') == args.commit
    assert git(path, 'branch', '--show-current') == branch
    assert not git(path, 'status', '--porcelain')
    assert git(path, 'rev-parse', 'origin/' + branch) == args.commit
    subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', args.commit,
                    'origin/yanrujhou_main'], check=True, timeout=60)
    receipt = path / 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence' / (
        '11-cpu-' + args.phase + '-mbit10-20261006-a3.json')
    data = json.loads(receipt.read_text())
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(source / 'swdb-project'))
    from swdb import artifacts
    assert data['identity_sha256'] == artifacts.digest({k: v for k, v in data.items() if k != 'identity_sha256'})
    assert data['source_commit'] == 'f893fed400347ed23d92e917d8bde21b75e5375d'
    assert data['raw_transferred'] is False and data['lane']['exit_code'] == 0 and data['lane']['ended_utc']
    assert data['lane']['node'] == 0
    references = 0
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        refs = [process / 'cwd']
        try:
            refs += list((process / 'fd').iterdir())
        except (PermissionError, FileNotFoundError):
            pass
        for ref in refs:
            try:
                target = os.readlink(ref)
            except OSError:
                continue
            assert not points_inside(target), 'An active process uses the export checkout'
            references += 1
    links = 0
    for run in Path('/data/yanruj/EvolveSWDB_runs').iterdir():
        if not run.name.startswith('lanl-'):
            continue
        for folder, directories, files in os.walk(run, followlinks=False):
            for name in directories + files:
                ref = Path(folder) / name
                if not ref.is_symlink():
                    continue
                assert not points_inside(str(ref.resolve())), 'Raw evidence refers to the export checkout'
                links += 1
    before = free_bytes()
    if args.remove:
        git(repo, 'worktree', 'remove', str(path))
        assert not path.exists()
    assert git(repo, 'rev-parse', 'refs/heads/' + branch) == args.commit
    assert git(repo, 'rev-parse', 'origin/' + branch) == args.commit
    assert git(source, 'rev-parse', 'HEAD') == data['source_commit']
    assert Path(data['raw_directory']).is_dir()
    print(json.dumps({'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'phase': args.phase, 'path': str(path), 'commit': args.commit, 'branch': branch,
        'removed': args.remove, 'process_references_checked': references, 'raw_symlinks_checked': links,
        'raw_and_execution_source_preserved': True, 'git_and_origin_preserved': True,
        'free_before_bytes': before, 'free_after_bytes': free_bytes(),
        'recovered_bytes': free_bytes() - before}))

if __name__ == '__main__':
    main()
