"""2026-10-16 ET. Restore one archived local worktree or branch from the cleanup manifest."""
import argparse
import json
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--worktree', help='Exact historical worktree path in the manifest')
    group.add_argument('--branch', help='Original branch name, without refs/heads/')
    parser.add_argument('--execute', action='store_true', help='Apply the displayed Git command')
    args = parser.parse_args()
    manifest = Path(__file__).with_name('recovery-snapshot.json')
    snapshot = json.loads(manifest.read_text())
    root = manifest.resolve().parents[3]
    if args.worktree:
        rows = [r for r in snapshot['worktrees'] if r['path'] == args.worktree]
        if len(rows) != 1:
            parser.error('Choose one exact worktree path from recovery-snapshot.json')
        row = rows[0]
        if Path(row['path']).exists() or Path(row['path']).is_symlink():
            parser.error('The historical destination already exists; nothing was changed')
        command = ['git', '-C', str(root), 'worktree', 'add', '--detach', row['path'], row['head']]
    else:
        rows = [r for r in snapshot['local_branches'] if r['ref'] == 'refs/heads/'+args.branch]
        if len(rows) != 1:
            parser.error('Choose one original local branch from recovery-snapshot.json')
        command = ['git', '-C', str(root), 'branch', args.branch, rows[0]['head']]
    print(subprocess.list2cmdline(command))
    if args.execute:
        subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
