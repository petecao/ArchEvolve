"""2026-10-16 ET. Draft standalone ownership10 runtime and output guards.

Only the active exact leaf may contain Why3's one zero-byte Unix IPC node.
This is metadata classification, never permission to open or connect to IPC.
All ordinary output links and other specials refuse, and settlement is strict.
"""
ACTIVE_LEAF = {}
WHY3_ROOT = '/data1/yanruj/probata-verifiers/opam/framac-33/lib/why3'
IPC_BASENAME = r'why3server[0-9a-f]{6}sock'
ENTRY_LIMIT = 30000


def need(condition, message):
    if not condition:
        raise ValueError(message)


def physical_ancestors(root, target):
    need(root.is_absolute() and root.resolve(strict=True) == root
         and stat.S_ISDIR(root.lstat().st_mode), 'physical output root required')
    relative = target.relative_to(root)
    path = root
    for part in relative.parts:
        path = path/part
        need(stat.S_ISDIR(path.lstat().st_mode) and path.resolve(strict=True) == path,
             'physical output ancestor required')


def active_ipc_path(root, path):
    if not ACTIVE_LEAF:
        return False
    leaf = ACTIVE_LEAF['directory']
    if path.parent != leaf/'tmp' or re.fullmatch(IPC_BASENAME, path.name) is None:
        return False
    physical_ancestors(root, path.parent)
    need(leaf.parent == root and leaf.name == 'leaf-'+ACTIVE_LEAF['target'],
         'active leaf producer identity differs')
    command = json.loads((leaf/'command.json').read_bytes())
    need(command['selected_id'] == ACTIVE_LEAF['target']
         and command['cwd'] == str(leaf)
         and command['input']['sha256'] == ACTIVE_LEAF['input_sha256']
         and sha(leaf/'wp_input.c') == ACTIVE_LEAF['input_sha256'],
         'active IPC is not owned by the exact canonical invocation')
    return True


def raw_bytes(root):
    """Strict physical accounting; narrow live IPC disappearance only."""
    physical_ancestors(root, root)
    total, entries_seen, sockets = 0, 0, []
    pending = [root]
    while pending:
        parent = pending.pop()
        physical_ancestors(root, parent)
        with os.scandir(parent) as entries:
            for item in entries:
                entries_seen += 1
                need(entries_seen <= ENTRY_LIMIT, 'ownership10 raw entry census cap exceeded')
                path = Path(item.path)
                try:
                    observed = item.stat(follow_symlinks=False)
                except FileNotFoundError:
                    if active_ipc_path(root, path):
                        continue
                    raise
                if stat.S_ISDIR(observed.st_mode):
                    pending.append(path)
                elif stat.S_ISREG(observed.st_mode):
                    need(observed.st_size <= 134217728, 'raw per-file128MiB allowance exceeded')
                    total += observed.st_size
                elif stat.S_ISSOCK(observed.st_mode):
                    need(active_ipc_path(root, path)
                         and observed.st_uid == os.geteuid()
                         and observed.st_dev == root.lstat().st_dev and observed.st_size == 0,
                         'unlisted runtime IPC or owner/device/size differs')
                    sockets.append(str(path.relative_to(root)))
                    need(len(sockets) <= 1, 'one worker admits at most one Why3 runtime socket')
                else:
                    raise ValueError('raw output links and special entries refused')
    return total


def bounded_bytes(path, data, output_root, policy, *, reserve=True):
    """Projected aggregate check, physical regular output and fsync/postcheck."""
    physical_ancestors(output_root, path.parent)
    if os.path.lexists(path):
        old = path.lstat()
        need(stat.S_ISREG(old.st_mode), 'derived output may replace only its regular file')
        previous = old.st_size
    else:
        previous = 0
    reserved = policy['metadata_reserve_bytes'] if reserve else 0
    need(len(data) <= policy['per_file_bytes'], 'derived metadata per-file allowance exceeded')
    before = raw_bytes(output_root)
    need(before-previous+len(data)+reserved <= policy['output_budget_bytes']-policy['root_headroom_bytes'],
         'projected aggregate raw-output allowance exceeded before writing '+path.name)
    with path.open('wb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    need(raw_bytes(output_root)+reserved <= policy['output_budget_bytes']-policy['root_headroom_bytes'],
         'aggregate raw-output allowance exceeded after metadata fsync')


def bounded_json(path, value, output_root, policy, *, reserve=True):
    bounded_bytes(path, (json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n').encode(),
                  output_root, policy, reserve=reserve)


def why3_dependency_check(expected):
    """Exact declared ELF candidates and alias bindings; no loader observation."""
    result = []
    for row in expected['why3_elf_candidate_files']:
        path = Path(row['path'])
        observed = path.lstat()
        need(stat.S_ISREG(observed.st_mode) and path.resolve(strict=True) == path
             and observed.st_size == row['bytes'] and sha(path) == row['sha256'],
             'selected Why3 package/ELF dependency physical bytes differ')
        result.append(pin(path))
    for row in expected['why3_elf_candidate_aliases']:
        path = Path(row['path'])
        need(stat.S_ISLNK(path.lstat().st_mode) and os.readlink(path) == row['target']
             and str(path.resolve(strict=True)) == row['resolved'],
             'declared Why3 ELF candidate alias differs')
    return {'files': result, 'aliases': expected['why3_elf_candidate_aliases'],
            'scope': 'Prospective physical candidate checks. OS loader/dlopen and source-to-binary/between-check identity remain explicit TCB.'}


def preserve_primary_error(root, error, policy):
    """Bounded first-failure metadata; diagnostic accounting is never admission."""
    physical_ancestors(root, root)
    target = root/'primary-error.json'
    if os.path.lexists(target):
        observed = target.lstat()
        need(stat.S_ISREG(observed.st_mode) and observed.st_size <= 16384,
             'existing primary error must be bounded regular output')
        return pin(target)
    total, count, pending, specials = 0, 0, [root], []
    while pending:
        parent = pending.pop()
        with os.scandir(parent) as entries:
            for item in entries:
                count += 1
                need(count <= ENTRY_LIMIT, 'diagnostic entry census cap exceeded')
                path = Path(item.path); observed = item.stat(follow_symlinks=False)
                if stat.S_ISDIR(observed.st_mode):
                    pending.append(path)
                elif stat.S_ISREG(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
                    total += observed.st_size
                else:
                    if len(specials) < 16:
                        specials.append({'relative':str(path.relative_to(root)), 'mode':observed.st_mode})
    value = {'error_type':type(error).__name__, 'error':str(error)[:4096],
             'producer_complete':False, 'proof_acceptance':False,
             'diagnostic_only_unadmitted_specials':specials,
             'scope':'First failure retained before strict settlement; no scientific or resource acceptance.'}
    data = (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    need(len(data) <= 16384 < policy['metadata_reserve_bytes']
         and total+policy['metadata_reserve_bytes'] <= policy['output_budget_bytes']-policy['root_headroom_bytes'],
         'first failure diagnostic exceeds fixed metadata reserve')
    with target.open('xb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    return pin(target)


def root_sibling_census(profile, policy):
    """All physical staged/root siblings, with fixed space for post-exit metadata."""
    root=profile.parent
    physical_ancestors(root, profile)
    total, count, files, pending = 0, 0, 0, [root]
    while pending:
        parent=pending.pop()
        physical_ancestors(root,parent)
        with os.scandir(parent) as entries:
            for item in entries:
                path=Path(item.path)
                count += 1
                need(count <= ENTRY_LIMIT, 'root sibling census entry cap exceeded')
                observed=item.stat(follow_symlinks=False)
                if path==profile:
                    need(stat.S_ISDIR(observed.st_mode), 'exact physical profile sibling required')
                    continue
                if stat.S_ISDIR(observed.st_mode):pending.append(path)
                else:
                    need(stat.S_ISREG(observed.st_mode) and observed.st_size <= policy['per_file_bytes'],
                         'root sibling must be a bounded regular physical file')
                    total += observed.st_size;files += 1
    need(total+policy['root_post_exit_reserve_bytes'] <= policy['root_headroom_bytes'],
         'root staged/metadata siblings exceed fixed headroom and post-exit reserve')
    return {'bytes':total,'regular_files':files,'root_headroom_bytes':policy['root_headroom_bytes'],
            'post_exit_reserve_bytes':policy['root_post_exit_reserve_bytes'],
            'scope':'Physical siblings at this observation; final root collector must bound the entire raw after its own metadata settles.'}
