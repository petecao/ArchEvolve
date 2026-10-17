"""2026-10-16 ET. Inert standalone ten-duty ownership-registry normal-WP profile.

Fresh public prepare/check plus unchanged normal command, flag/lineup policies,
native reader and outcome reading. No admitted model/View, public proof record,
universal setup attestation, source correspondence or caller acceptance.
"""
import argparse
import hashlib
import json
import os
import re
import resource
import shutil
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

EXPECTED_SHA256 = '7fb3f40e7ec3eb2c1e2e53a91267738381db7c7f9656ec75fe74722a1c7ea078'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pin(p):return {'path':str(p),'sha256':sha(p),'bytes':Path(p).stat().st_size}


def write(p,obj):p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')


def surface(root,rows):
    root=Path(root)
    if root.is_symlink() or not root.is_dir():raise ValueError('selected import root changed')
    found=[]
    for p in sorted(root.rglob('*')):
        if p.is_symlink() or not(p.is_file() or p.is_dir()):raise ValueError('nonregular import input')
        if p.is_file():found.append({'relative':str(p.relative_to(root)),'sha256':sha(p)})
    if found!=rows:raise ValueError('selected full import-tree membership/hash differs: '+str(root))


def linux_admission(expected,repo,out):
    raw_value=os.environ.get('PROBATA_OUTPUT')
    if not raw_value:raise ValueError('Linux coordinator PROBATA_OUTPUT marker required')
    root=Path(raw_value).resolve()
    if root!=out.parent.resolve():raise ValueError('Linux output marker differs from exact profile root')
    if os.environ.get('SWDB_VERIFIER_LOCK')!=str(root/'verifier.lock') or os.environ.get('SWDB_VERIFIER_RSS_CAP_BYTES')!='8589934592':
        raise ValueError('Linux lock/cap context differs from reviewed wrapper')
    launch_path=root/'launch.json';launch=json.loads(launch_path.read_bytes());policy=expected['resource_policy']
    if Path(launch['source']).resolve()!=repo.resolve() or launch.get('source_commit')!=expected['source_commit']:
        raise ValueError('Linux launch source differs from selected immutable source')
    if launch.get('rss_cap_bytes')!=policy['cap_bytes'] or launch.get('workers')!=1 or launch.get('timeout_seconds')!=policy['root_whole_seconds']:
        raise ValueError('Linux launch whole-worker budget differs')
    command=launch.get('command',[]);binding=expected['linux_launch_binding']
    prefix=[expected['tools']['opam']['path'],'exec','--switch=framac-33','--',binding['python'],'-c']
    if command[:6]!=prefix or len(command)!=9 or command[-2:]!=[str(repo/'swdb-project'),str(root)]:
        raise ValueError('Linux admitted entry command boundary differs')
    # Root's reviewed bootstrap embeds exact entry/expectation bytes and digest
    # literals; it stages them outside source then execs this immutable entry.
    code=command[6]
    if 'ENTRY_SHA256 = '+repr(sha(__file__)) not in code or 'EXPECTED_SHA256 = '+repr(EXPECTED_SHA256) not in code:
        raise ValueError('Linux launch does not bind exact entry/expected byte hashes')
    for name,wanted in binding['wrappers'].items():
        if launch.get('reviewed_wrapper_reuse',{}).get(name)!=wanted or sha(root/name)!=wanted:
            raise ValueError('Linux outer wrapper bytes differ')
    return {'marker_path':str(root),'launch':pin(launch_path),'command_sha256':hashlib.sha256(json.dumps(command,separators=(',',':')).encode()).hexdigest(),
            'source_commit':expected['source_commit'],'rss_cap_bytes':policy['cap_bytes'],'whole_seconds':policy['root_whole_seconds'],
            'lock_path':str(root/'verifier.lock'),'scope':binding['scope'],'Mac_counted_token_required':False}


def consumer_closure(project,repository,expected):
    commit=expected['source_commit'];trees=expected['source_consumer_trees']
    def git(*a,input=None):return subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(repository),*a],input=input,timeout=180)
    for relative,tree in trees.items():
        if git('rev-parse','--verify',commit+':swdb-project/'+relative).decode().strip()!=tree['oid']:
            raise ValueError('source consumer Git tree/blob differs: '+relative)
    packed=git('ls-tree','-r','-z',commit,'--',*['swdb-project/'+x for x in trees])
    wanted=[]
    for entry in packed.split(b'\0'):
        if not entry:continue
        meta,name=entry.decode().split('\t',1);mode,kind,oid=meta.split()
        if mode not in {'100644','100755'}or kind!='blob' or not name.startswith('swdb-project/'):
            raise ValueError('source consumer requires exact regular Git blobs')
        relative=name.removeprefix('swdb-project/');p=project/relative
        if '\n'in str(p)or '\r'in str(p)or str(p).startswith('"'):raise ValueError('unreviewed source path encoding')
        wanted.append({'relative':relative,'git_blob':oid,'path':str(p)})
    found=set()
    for relative in trees:
        root=project/relative
        if root.is_symlink()or not(root.is_file()or root.is_dir()):raise ValueError('source consumer root changed')
        for p in ([root]if root.is_file()else root.rglob('*')):
            if p.is_symlink()or not(p.is_file()or p.is_dir()):raise ValueError('source consumer symlink/special input')
            if p.is_file():found.add(str(p.relative_to(project)))
    if found!={r['relative']for r in wanted}:raise ValueError('source consumer physical membership differs from selected exact source Git tree')
    # hash-object streams physical files and emits only40-byte object names.
    # It never captures the1.33GB catalog body or invokes a content filter.
    physical_oids=git('hash-object','--no-filters','--stdin-paths',input=''.join(r['path']+'\n'for r in wanted).encode()).decode().splitlines()
    if physical_oids!=[r['git_blob']for r in wanted]:raise ValueError('source consumer physical bytes differ from selected immutable source Git blob')
    for row in wanted:
        p=Path(row['path']);h=hashlib.sha256()
        with p.open('rb')as stream:
            for block in iter(lambda:stream.read(1048576),b''):h.update(block)
        row.update(sha256=h.hexdigest(),bytes=p.stat().st_size)
    return {'source_commit':commit,'trees':trees,'files':wanted,'count':len(wanted),
            'total_bytes':sum(r['bytes']for r in wanted),'physical_git_blob_equality':True,
            'scope':'Opaque source-byte identity only. Existing fixture helper selects/parses YAML header/reference closure; no unrelated scientific evidence or held-out source semantics inspected.'}


def guarded_generation(command, directory, environment, policy, timeout, watchdog, output_root):
    """Generation guard whose every post-spawn path kills and reaps its session."""
    file_allowance = policy['output_budget_bytes']-raw_bytes(output_root)-policy['metadata_reserve_bytes']
    if file_allowance <= 0:
        raise ValueError('no raw-output allowance remains before generation')
    def setup():
        resource.setrlimit(resource.RLIMIT_FSIZE, (min(file_allowance, policy['per_file_bytes']), min(file_allowance, policy['per_file_bytes'])))

    started = time.monotonic()
    timed_out = output_limit = False
    watch = None
    descendants = {}
    primary_error = None
    with (directory/'frama-c.log').open('wb') as log:
        process = subprocess.Popen(command, cwd=directory, env=environment, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True, preexec_fn=setup)
        try:
            # Snapshot before entering the watcher: __enter__ may itself fail.
            descendants = watchdog.tree(process.pid)
            watch = watchdog.TreeWatch(process.pid, policy['cap_bytes'])
            with watch:
                while process.poll() is None:
                    descendants = watchdog.tree(process.pid)
                    timed_out = time.monotonic()-started > timeout
                    output_limit = raw_bytes(output_root) > policy['output_budget_bytes']-policy['metadata_reserve_bytes']
                    if timed_out or output_limit:
                        break
                    time.sleep(0.1)
                if not timed_out and not output_limit:
                    process.wait()
            if watch.error:
                raise RuntimeError(watch.error)
        except BaseException as exc:
            primary_error = exc
            raise
        finally:
            # The child owns a new session. A callback/watch/poll/wait exception
            # must never leave it running after the outer worker returns.
            cleanup_errors = []
            try:
                descendants = {**descendants, **watchdog.tree(process.pid)}
            except BaseException as exc:
                cleanup_errors.append('final process-tree snapshot: '+type(exc).__name__+': '+str(exc))
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except BaseException as exc:
                cleanup_errors.append('session kill: '+type(exc).__name__+': '+str(exc))
            for pid in descendants:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except BaseException as exc:
                    cleanup_errors.append('descendant kill: '+type(exc).__name__+': '+str(exc))
            try:
                process.wait(timeout=10)
            except BaseException as exc:
                cleanup_errors.append('reap: '+type(exc).__name__+': '+str(exc))
            if cleanup_errors:
                # Best-effort diagnostics must not replace the original error.
                try:
                    write(directory/'guard-cleanup-errors.json', {
                        'primary_error': None if primary_error is None else
                            type(primary_error).__name__+': '+str(primary_error),
                        'cleanup_errors': cleanup_errors,
                        'scope': 'Guard failure; no complete generation or resource claim'})
                except BaseException:
                    pass
                if primary_error is None:
                    raise RuntimeError('; '.join(cleanup_errors))
    return {'exit_code': process.returncode, 'peak_rss_bytes': watch.peak,
            'out_of_memory': watch.tripped, 'timed_out': timed_out,
            'output_limit': output_limit, 'wall_seconds': time.monotonic()-started}


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
    need(before-previous+len(data)+reserved <= policy['output_budget_bytes'],
         'projected aggregate raw-output allowance exceeded before writing '+path.name)
    with path.open('wb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    need(raw_bytes(output_root)+reserved <= policy['output_budget_bytes'],
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
         and total+policy['metadata_reserve_bytes'] <= policy['output_budget_bytes'],
         'first failure diagnostic exceeds fixed metadata reserve')
    with target.open('xb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    return pin(target)


def why3_runtime_check(expected):
    """Prospective additional closure; never retroactive historical identity."""
    manifests = expected["why3_runtime_extension"]["inventories"]
    result = {}
    for name, wanted in manifests.items():
        root = Path(name)
        need(root.resolve(strict=True) == root and root.is_dir() and not root.is_symlink(),
             "canonical Why3 runtime root required")
        rows, directories = [], []
        for path in sorted(root.rglob("*")):
            observed = path.lstat()
            relative = str(path.relative_to(root))
            if stat.S_ISDIR(observed.st_mode):
                directories.append(relative)
            else:
                need(stat.S_ISREG(observed.st_mode) and path.resolve(strict=True) == path,
                     "Why3 runtime special/link input refused")
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for block in iter(lambda: stream.read(1048576), b""):
                        digest.update(block)
                rows.append({"relative": relative, "bytes": observed.st_size,
                             "sha256": digest.hexdigest(), "mode": stat.S_IMODE(observed.st_mode)})
        need(rows == wanted["files"] and directories == wanted["directories"],
             "Why3 package/dependency physical membership differs")
        need(all(expected["runtime_files"].get(str(root / row["relative"])) == row["sha256"] for row in rows),
             "Why3 additional physical pins must join the existing runtime gate")
        result[name] = {"count": len(rows), "inventory_sha256":
            hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()}
    need(WHY3_ROOT in result and expected["ocaml_packages"].get("why3") == WHY3_ROOT,
         "exact prospective Why3 package binding missing")
    return result




def canonical_check(packets, expected, directory):
    manifest = packets.check(directory, elements=tuple(expected['elements']))
    physical = [{'path': str(p.relative_to(directory)), 'bytes': p.stat().st_size,
                 'sha256': sha(p)} for p in sorted(directory.rglob('*')) if p.is_file()]
    if manifest != expected['canonical_manifest'] or physical != expected['canonical_files']:
        raise ValueError('fresh complete owned-transfer canonical packet differs')
    rows = manifest['obligations']
    if len(rows) != 10 or [r['id'] for r in rows] != expected['target_ids'] or any(
            r['kind'] != 'check_lemma' or r['status'] != 'pending' or r['dependencies'] for r in rows):
        raise ValueError('all ten independent pending check lemmas are required')
    if manifest['source_typed_bridge_established'] is not False or \
            manifest['current_model_records_admitted'] or manifest['caller_premises_added']:
        raise ValueError('owned-transfer packet falsely broadens admission')
    return manifest


def normal_task_census(directory, target, inventory, output_root, policy):
    """Streaming metadata over retained tasks; independent term audit still required."""
    goals = inventory['goals']
    properties = inventory['properties']
    if inventory.get('complete') is not True or not goals or \
            len({g['goal'] for g in goals}) != len(goals) or \
            len({p['property'] for p in properties}) != len(properties):
        raise ValueError('native complete goal/property census missing or duplicated')
    by_property = {p['property']: p for p in properties}
    missing = sorted({d for p in properties for d in p['dependencies'] if d not in by_property})
    origins = sorted({p['origin'] for p in properties if p['origin'] is not None and p['origin'] not in by_property})
    lemmas = [p for p in properties if p.get('kind') == 'lemma']
    ordinary = [g for g in goals if not g['smoke']]
    if missing or origins or len(lemmas) != 1 or not ordinary or any(
            g['property'] != lemmas[0]['property'] for g in ordinary) or \
            not lemmas[0]['property'].endswith('_'+target['goal']) or \
            lemmas[0].get('dependencies') or lemmas[0].get('extern'):
        raise ValueError('sole source-owned independent check lemma or dependency closure differs')
    standard = json.loads((directory/'wp-goals.json').read_bytes())
    if len({g['goal'] for g in standard}) != len(standard) or \
            {g['goal'] for g in standard} != {g['goal'] for g in goals}:
        raise ValueError('complete native/standard goal census differs')
    peers = {g['goal']: g for g in standard}
    for g in goals:
        if any(g.get(k) != peers[g['goal']].get(k) for k in ('property','function','line','smoke','passed')):
            raise ValueError('native/standard goal binding differs: '+g['goal'])
    log_path = directory/'frama-c.log'
    exports = []
    current = None
    offset = line_number = 0
    marker = re.compile(rb'^\s*(?:\[wp(?::[^\]]+)?\]\s*)?EXPORT GOAL\s+(\S+)\s*$')
    declaration = re.compile(rb'^\s*(?:\[wp:print-generated\]\s*)?(use|clone|axiom|goal|constant|function|predicate|type|theory)\s+([^\s:(=]+)')
    with log_path.open('rb') as stream:
        for line in stream:
            line_number += 1
            match = marker.match(line)
            if match:
                if current is not None:
                    current.update(end_byte=offset, sha256=current.pop('_hash').hexdigest())
                    exports.append(current)
                ident = match.group(1).decode()
                owners = [g['goal'] for g in goals if g['goal'].endswith('_'+ident)]
                if len(owners) != 1:
                    raise ValueError('actual common export has no unique native owner: '+ident)
                current = {'export_id': ident, 'goal': owners[0], 'begin_byte': offset,
                           'begin_line': line_number, '_hash': hashlib.sha256(),
                           'declarations': [], 'theory_seen': False, 'goal_seen': False, 'end_seen': False}
            if current is not None:
                current['_hash'].update(line)
                parsed = declaration.match(line)
                if parsed:
                    kind, name = (part.decode(errors='replace') for part in parsed.groups())
                    current['declarations'].append({'kind': kind, 'name': name, 'line': line_number,
                                                   'line_sha256': hashlib.sha256(line).hexdigest()})
                    current['theory_seen'] |= kind == 'theory'
                    current['goal_seen'] |= kind == 'goal'
                current['end_seen'] |= bool(re.match(rb'^\s*end\s*$', line))
            offset += len(line)
    if current is not None:
        current.update(end_byte=offset, sha256=current.pop('_hash').hexdigest())
        exports.append(current)
    if any(not all(row[k] for k in ('theory_seen','goal_seen','end_seen')) for row in exports):
        raise ValueError('retained common task fragment is incomplete')
    exported = {row['goal'] for row in exports}
    inventory_only = [g for g in goals if g['goal'] not in exported]
    missing_tasks = [g['goal'] for g in inventory_only if not (
        g['results'] == ['valid'] and any(p['prover'] == 'qed' and p.get('success') == 1
                                       for p in peers[g['goal']].get('provers', [])))]
    census = {'target': target['id'], 'native_goal_count': len(goals),
              'native_property_count': len(properties), 'ordinary_count': len(ordinary),
              'smoke_count': sum(bool(g['smoke']) for g in goals), 'log': pin(log_path),
              'common_exports': exports, 'internal_qed_inventory_only': [g['goal'] for g in inventory_only],
              'missing_noninternal_tasks': missing_tasks,
              'extern_properties': [p['property'] for p in properties if p['extern']],
              'property_dependencies': [{'property': p['property'], 'variant': p['property_variant'],
                  'origin': p['origin'], 'dependencies': p['dependencies'], 'extern': p['extern']}
                  for p in properties],
              'scope': 'Complete actual census and declaration positions only. Original full log, prover files, native properties and CSV retained. Imported definitions/axioms/hypotheses require independent cold interpretation; no source/caller proof or automatic semantic acceptance.'}
    bounded_json(directory/'task-census.json', census, output_root, policy)
    if missing_tasks:
        raise ValueError('actual required common tasks missing; preserve partial census')
    return census


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected', required=True, type=Path)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if sha(args.expected) != EXPECTED_SHA256:
        raise ValueError('reviewed ten-duty expectation bytes differ')
    expected = json.loads(args.expected.read_bytes()); policy = expected['resource_policy']
    project = args.project.resolve(); repo = project.parent; out = args.output.resolve()
    if str(project) != expected['remote_project'] or out.exists() or out.is_relative_to(repo):
        raise ValueError('exact immutable source and fresh external profile required')
    launch = linux_admission(expected, repo, out)
    out.mkdir(parents=True); os.chdir(project)
    started = time.monotonic(); deadline = started+policy['profile_seconds']
    result = {'created': '2026-10-16 ET', 'scope': expected['scope'],
              'source_commit': expected['source_commit'], 'producer_complete': False,
              'all_ten_producer_proven': False, 'proof_acceptance': False,
              'source_typed_bridge_established': False, 'caller_acceptance': False,
              'body_acceptance': False, 'public_proof_record_created': False,
              'universal_proof_setup_attested': False, 'independent_task_hypothesis_review_pending': True,
              'linux_launch': launch, 'source_receipts': [], 'runs': [],
              'unexecuted': list(expected['target_ids'])}
    def remaining():
        value = deadline-time.monotonic()
        if value <= 0:
            raise TimeoutError('whole standalone profile budget spent')
        return value
    def source_check():
        command = ['/usr/bin/git', '--no-optional-locks', '--no-replace-objects',
                   '-c', 'core.preloadIndex=false', '-c', 'core.fsmonitor=false',
                   '-c', 'index.threads=1', '-C', str(repo)]
        head = subprocess.check_output([*command, 'rev-parse', 'HEAD'], text=True, timeout=30).strip()
        dirty = subprocess.check_output([*command, 'status', '--porcelain', '--untracked-files=all'], text=True, timeout=30)
        if head != expected['source_commit'] or dirty:
            raise ValueError('selected source is not exact and clean')
        for row in expected['source_blobs']+expected['test_helper_pins']:
            if sha(project/row['relative']) != row['sha256']:
                raise ValueError('selected source input changed: '+row['relative'])
        closure = consumer_closure(project, repo, expected)
        path = out/('source-consumers-'+str(len(result['source_receipts']))+'.json')
        bounded_json(path, closure, out, policy); result['source_receipts'].append(pin(path))
    def runtime_check():
        selected = {}
        for name, row in expected['tools'].items():
            path = shutil.which(name)
            if path is None or Path(path).resolve() != Path(row['path']).resolve() or sha(path) != row['sha256']:
                raise ValueError('selected physical tool changed: '+name)
            selected[name] = pin(Path(path).resolve())
        for row in expected['wp_artifacts']:
            if sha(row['path']) != row['sha256']:
                raise ValueError('selected WP artifact changed')
        prefix = Path(expected['linux_prefix'])
        for key, root in [('why3_stdlib', prefix/'share/why3/stdlib'),
                          ('wp_why3_support', prefix/'share/frama-c/share/wp/why3'),
                          ('why3_drivers', prefix/'share/why3/drivers')]:
            surface(root, expected['portable_import_surfaces'][key])
        for row in expected['runtime_sources']:
            if sha(prefix/'lib/frama-c-wp/core'/row['name']) != row['sha256']:
                raise ValueError('selected runtime source changed: '+row['name'])
        if sha(expected['why3_config']['path']) != expected['why3_config']['sha256']:
            raise ValueError('selected Why3 configuration changed')
        selected['why3_packages'] = why3_runtime_check(expected)
        selected['why3_elf_candidates'] = why3_dependency_check(expected)
        return selected
    try:
        source_check(); bounded_json(out/'runtime.json', runtime_check(), out, policy)
        ambient = sorted(k for k in os.environ if k.startswith(('FRAMAC_WP','WP_')) or k == 'SWDB_PROOF_REPORT_OUT')
        if ambient:
            raise ValueError('forbidden ambient WP selectors: '+','.join(ambient))
        shutil.copyfile(__file__, out/'entry.py'); shutil.copyfile(args.expected, out/'expected.json')
        os.environ.update(SWDB_FRAMA_C=expected['tools']['frama-c']['path'], SWDB_CBMC='none',
            SWDB_OCAMLFIND=expected['tools']['ocamlfind']['path'], WHY3CONFIG=expected['why3_config']['path'],
            SWDB_WHY3_CONFIG=expected['why3_config']['path'], PYTHONDONTWRITEBYTECODE='1',
            SWDB_FIXTURE_HOST='swdb-fixture-host', SWDB_VERIFIER_RSS_CAP_BYTES=str(policy['cap_bytes']))
        sys.dont_write_bytecode = True; sys.path[:0] = [str(project), str(project/'tests')]
        from swdb import vector_owned_transfer as packets
        from swdb import heap_model_view as engine, proof_setup, wp_adapter, c_lowering, stdlib_provenance, framac, method_version, rss_watchdog
        from swdb.library import Library
        inputs = out/'canonical-inputs'; manifest = packets.prepare(inputs, elements=tuple(expected['elements']))
        if manifest != canonical_check(packets, expected, inputs):
            raise ValueError('fresh public prepare/check results differ')
        bounded_json(out/'canonical-precheck.json', {'manifest': pin(inputs/'manifest.json'),
            'checker': packets.identity(), 'target_ids': expected['target_ids'],
            'canonical_files': expected['canonical_files'], 'old_proofs_imported': 0}, out, policy)
        compiler = stdlib_provenance.runtime_identity(c_lowering.locate()); lowering = c_lowering.identity()
        if {k: compiler[k] for k in expected['linux_clang_components']} != expected['linux_clang_components'] or \
                compiler != expected['linux_project_identity_derivation']['runtime'] or \
                lowering != expected['linux_project_identity_derivation']['predicted_identity']:
            raise ValueError('fresh source/context compiler composite differs')
        bounded_json(out/'compiler-runtime.json', {'runtime': compiler, 'identity': lowering}, out, policy)
        import yaml
        from swdb import std_models
        seed_root = out/'workspace'; seed_root.mkdir(exist_ok=False)
        records = seed_root/'records'; (records/'proofs').mkdir(parents=True)
        library = seed_root/'library'; methods = library/'methods'; methods.mkdir(parents=True)
        inherited = project/'tests/fixtures/proof/methods/contract-fixture-1.yaml'
        lineup_path = project/'library/methods/probata-draft-1.yaml'
        # Only ordinary fixture method metadata is copied. No test module,
        # test builder, catalog proof, contract or candidate is imported.
        method_data = yaml.safe_load(inherited.read_bytes())
        method_data['lineup'] = yaml.safe_load(lineup_path.read_bytes())['lineup']
        wp_rows = [row for row in method_data['lineup'] if row['tool']=='frama-c-wp']
        if len(wp_rows) != 1:
            raise ValueError('one normal source-pinned WP lineup required')
        wp_rows[0]['flags'] += ['-rte-initialized', '@all', '-wp-no-filter-init']
        method_data['c_lowering']['translators'] = [lowering['c_lowering']]
        method_data['models'].update(std_vector=std_models.identity(), std_pair=std_models.identity())
        method_data.update(id=expected['method_id'], sequence=3,
            description='Standalone conditional ownership-registry ten-duty native mathematical profile. No body/caller/model admission. '+json.dumps(expected['explicit_method_binding'], sort_keys=True))
        method_path = methods/'wp-owned-transfer10-v1.yaml'
        method_path.write_text(yaml.safe_dump(method_data, sort_keys=False))
        seed = SimpleNamespace(root=seed_root, records=records)
        method = method_version.select(seed.root/'library', expected['method_id'])
        adapter = wp_adapter.WpAdapter(Library(seed.root/'library'), 'standalone-owned-transfer', method, records=seed.records)
        tools = adapter._tools(); flags = engine.flags(tools)
        if tools['seconds'] != 30 or tools['provers'] != ['alt-ergo','z3','cvc5'] or \
                any(x.startswith(('-wp-prop','-wp-fct')) or x in {'-wp-gen','-wp-no-why3-detect'} for x in flags):
            raise ValueError('complete unchanged normal proof portfolio required')
        proof_setup._wp_flags(flags, out); proof_setup._lineup(method, adapter, tools, flags)
        bounded_json(out/'method.json', {'pin': method_version.pin(method), 'method': method_data,
            'inherited': pin(inherited), 'lineup_source': pin(lineup_path), 'flags': flags, 'tools': tools,
            'policy': 'Actual ordinary flag/lineup functions only; no universal setup certificate claimed.'}, out, policy)
        reader_dir = out/'reader'; reader_dir.mkdir()
        reader = proof_setup.compile_report_module(reader_dir, timeout=min(120, remaining()))
        foundation = engine.foundations(framac.locate().command, out/'foundation', deadline)
        bounded_json(out/'foundation.json', foundation, out, policy)
        for row in manifest['obligations']:
            remaining(); canonical_check(packets, expected, inputs); runtime_check()
            directory = out/('leaf-'+row['id']); directory.mkdir(); (directory/'tmp').mkdir()
            path = directory/'wp_input.c'; path.write_bytes((inputs/row['path']).read_bytes())
            invocation = engine.command(framac.locate().command, flags, inputs, reader)
            proof_setup._wp_flags(invocation, directory); proof_setup._lineup(method, adapter, tools, flags)
            if sha(path) != row['sha256'] or invocation != engine.command(framac.locate().command, engine.flags(tools), inputs, reader):
                raise ValueError('complete normal command or fresh input changed before launch')
            timeout = min(policy['leaf_timeout_seconds'], remaining())
            bounded_json(directory/'command.json', {'argv': invocation, 'cwd': str(directory),
                'timeout_seconds': timeout, 'input': pin(path), 'selected_id': row['id']}, out, policy)
            environment = {**os.environ, 'TMPDIR': str(directory/'tmp'),
                           'SWDB_PROOF_REPORT_OUT': str(directory/'wp-inventory.json')}
            ACTIVE_LEAF.update(directory=directory, target=row['id'], input_sha256=row['sha256'])
            try:
                resource_result = guarded_generation(invocation, directory, environment, policy, timeout, rss_watchdog, out)
            finally:
                ACTIVE_LEAF.clear()
            raw_bytes(out)  # strict after the guarded process tree has settled

            bounded_json(directory/'resources.json', resource_result, out, policy)
            if resource_result['out_of_memory'] or resource_result['timed_out'] or resource_result['output_limit']:
                raise ValueError('leaf resource boundary hit; preserve all partial artifacts')
            outcome = wp_adapter.read_outcome(SimpleNamespace(**resource_result),
                (directory/'frama-c.log').read_text(errors='replace'),
                directory/'wp-goals.json' if (directory/'wp-goals.json').exists() else None,
                directory/'wp-properties.csv' if (directory/'wp-properties.csv').exists() else None,
                inventory=directory/'wp-inventory.json' if (directory/'wp-inventory.json').exists() else None)
            bounded_json(directory/'outcome.json', outcome, out, policy)
            if not all((directory/name).is_file() for name in ('wp-goals.json','wp-properties.csv','wp-inventory.json','wp-normalized.c')):
                raise ValueError('actual complete native/ordinary/property/normalized reports absent')
            inventory = json.loads((directory/'wp-inventory.json').read_bytes())
            census = normal_task_census(directory, row, inventory, out, policy)
            result['runs'].append({'id': row['id'], 'cwd': str(directory), 'input': pin(path),
                'resources': resource_result, 'outcome': outcome, 'census': pin(directory/'task-census.json'),
                'ordinary_goals': census['ordinary_count'], 'smoke_goals': census['smoke_count']})
            result['unexecuted'].remove(row['id']); bounded_json(out/'result.json', result, out, policy)
        source_check(); runtime_check(); canonical_check(packets, expected, inputs)
        if list((seed.records/'proofs').glob('*.yaml')):
            raise ValueError('standalone profile unexpectedly created a public proof record')
        result.update(producer_complete=True, all_ten_producer_proven=all(r['outcome']['verdict']=='proven' for r in result['runs']),
            source_after_clean=True, raw_bytes=raw_bytes(out),
            classification='Ten fresh producer outcomes retained. Independent complete source/runtime/resource/task/hypothesis review required; no proof/source/Typed/body/caller/public-record acceptance.')
    except Exception as exc:
        result.update(error_type=type(exc).__name__, error=str(exc))
        result['primary_error'] = preserve_primary_error(out, exc, policy)
    finally:
        result['elapsed_seconds'] = time.monotonic()-started
        result['within_profile_budget'] = time.monotonic() < deadline-1
        if not result['within_profile_budget']:
            result['producer_complete'] = False
        # The result and manifest retain independent cold-review requirements.
        # Reserve is checked before each write and exact final size is checked
        # after fsync; profile completion also requires a strict settled walk.
        bounded_json(out/'result.json', result, out, policy, reserve=False)
        bounded_json(out/'artifact-manifest.json', [{'relative': str(p.relative_to(out)), **pin(p)}
            for p in sorted(out.rglob('*')) if p.is_file() and p != out/'artifact-manifest.json'], out, policy, reserve=False)
        settled = raw_bytes(out)
        if settled > policy['output_budget_bytes'] or time.monotonic() >= deadline:
            raise ValueError('final settled raw budget or post-fsync profile deadline exceeded')
    return 0 if result['producer_complete'] and result['within_profile_budget'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
