"""2026-10-16 ET. Retire one completed clean detached source with recovery.

No raw evidence or external symlink target is removed. Refuse unknown readers,
ignored/untracked/modified state or any unexpected tracked Git object type.
"""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import subprocess

PRIMARY = Path('/data1/yanruj/ArchEvolve')
SOURCE = Path('/data1/yanruj/probata-resume-20261016-18f04e56')
COMMIT = '18f04e569b949f465d6732db9505e3a264805040'

def git(root, *arguments):
    return subprocess.check_output(['git', '-C', str(root), *arguments])

assert SOURCE.is_dir() and not SOURCE.is_symlink()
assert git(SOURCE, 'rev-parse', 'HEAD').decode().strip() == COMMIT
assert git(SOURCE, 'rev-parse', '--abbrev-ref', 'HEAD').decode().strip() == 'HEAD'
assert not git(SOURCE, 'status', '--porcelain', '--untracked-files=all', '--ignored')
assert not git(SOURCE, 'submodule', 'status')
subprocess.run(['git', '-C', str(PRIMARY), 'merge-base', '--is-ancestor', COMMIT,
                'origin/yanrujhou_main'], check=True)
lock = PRIMARY/'swdb-project/records/.retention.lock'
lock_before = (lock.read_bytes(), lock.stat().st_mode)
readers, unreadable, exclusions, races = [], [], [], []
scanned = 0
for proc in Path('/proc').iterdir():
    if not proc.name.isdecimal():
        continue
    try:
        if proc.stat().st_uid != os.getuid():
            continue
        scanned += 1
        comm = (proc/'comm').read_text().strip()
        command = (proc/'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace').strip()
        if (comm == '(sd-pam)' and command in ('', '(sd-pam)')) or \
                (comm == 'sshd' and command == 'sshd: yanruj@notty'):
            exclusions.append({'pid': int(proc.name), 'comm': comm, 'command': command,
                               'boundary': 'Exact OS session/SSH transport helper; inaccessible private proc details excluded'})
            continue
        environment = (proc/'environ').read_bytes()
        cwd = os.readlink(proc/'cwd')
        descriptors = []
        for descriptor in (proc/'fd').iterdir():
            try:
                descriptors.append(os.readlink(descriptor))
            except FileNotFoundError:
                pass
        selected = str(SOURCE)
        if selected in command or selected.encode() in environment or \
                any(value == selected or value.startswith(selected+'/') for value in [cwd, *descriptors]):
            readers.append({'pid': int(proc.name), 'comm': comm, 'target_reference': True})
    except FileNotFoundError:
        races.append(int(proc.name))
    except PermissionError:
        if proc.exists():
            unreadable.append({'pid': int(proc.name), 'error': 'PermissionError'})
assert not readers and not unreadable, {'readers': readers, 'unreadable': unreadable}
raws = [str(path) for path in Path('/data/yanruj/EvolveSWDB_runs').glob('*18f04e56*') if path.is_dir()]
assert raws
manifest = hashlib.sha256()
tracked_links = []
entries = git(SOURCE, 'ls-files', '--stage', '-z').split(b'\0')
count = 0
for entry in entries:
    if not entry:
        continue
    metadata, relative = entry.decode().split('\t', 1)
    mode, oid, stage = metadata.split()
    assert stage == '0'
    path = SOURCE/relative
    if mode == '120000':
        assert path.is_symlink()
        literal = os.readlink(path)
        payload = literal.encode()
        tracked_links.append({'relative': relative, 'literal_target': literal,
                              'target_traversed': False, 'target_unchanged_by_unlink': True})
    else:
        assert mode in ('100644', '100755') and path.is_file() and not path.is_symlink(), relative
        payload = path.read_bytes()
    manifest.update(mode.encode()+b'\0'+relative.encode()+b'\0'+hashlib.sha256(payload).digest())
    count += 1
before = shutil.disk_usage('/data1').free
tree = git(SOURCE, 'rev-parse', 'HEAD^{tree}').decode().strip()
restore = ['git', '-C', str(PRIMARY), 'worktree', 'add', '--detach', str(SOURCE), COMMIT]
subprocess.run(['git', '-C', str(PRIMARY), 'worktree', 'remove', str(SOURCE)], check=True)
assert not SOURCE.exists() and all(Path(path).is_dir() for path in raws)
assert lock_before == (lock.read_bytes(), lock.stat().st_mode)
print(json.dumps({'created': '2026-10-16 ET', 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'retired_source': str(SOURCE), 'commit': COMMIT, 'tree': tree,
    'retained_remote_main': git(PRIMARY, 'rev-parse', 'origin/yanrujhou_main').decode().strip(),
    'ancestor_verified': True, 'source_clean': True, 'ignored_files': [],
    'tracked_files': count, 'tracked_links': tracked_links, 'physical_tracked_manifest_sha256': manifest.hexdigest(),
    'finite_owned_processes_scanned': scanned, 'active_owned_readers': readers,
    'unreadable_owned_workloads': unreadable, 'excluded_OS_session_helpers': exclusions, 'exited_process_races': races,
    'reader_confirmation': 'ticket25 and ticket28 confirm no active or pending physical18f reader; original source and all raw remain published/recoverable',
    'restore_argv': restore, 'raw_directories_retained': raws,
    'primary_branch': git(PRIMARY, 'rev-parse', '--abbrev-ref', 'HEAD').decode().strip(),
    'primary_commit': git(PRIMARY, 'rev-parse', 'HEAD').decode().strip(),
    'primary_retention_lock_preserved': {'sha256': hashlib.sha256(lock_before[0]).hexdigest(), 'mode': lock_before[1]},
    'disk_before_bytes': before, 'disk_after_bytes': shutil.disk_usage('/data1').free,
    'scope': 'Ordinary git worktree remove of this clean detached completed own source only, no force. Raw, all other sources/toolchains, external link targets and ticket7 preserved. No compiler/native/proof execution.'}, indent=2))
