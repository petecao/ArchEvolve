#!/usr/bin/env python3
"""SOURCE ONLY / NOT RUN: private outer capture for unchanged reviewed1ee envelope.

Future parent-reviewed real argv/input pins only. All envelope startup, writer and
GNU diagnostics stay remote, unsealed. No campaign/scientific admission follows.
"""
import argparse
import ctypes
import datetime
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import resource
import signal
import socket
import stat
import subprocess
import sys
import time
sys.dont_write_bytecode = True


C = 'f893fed400347ed23d92e917d8bde21b75e5375d'

F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'

HELPER = '28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'

AUDITOR = '6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da'

COLLECTOR = 'b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'

CIDS = tuple('extensa-gem5-bfs-20261006-p' + str(i) for i in range(1, 5))

MAX_CATALOG_FILE = 128 * 1024 * 1024

MAX_CATALOG_TOTAL = 2 * 1024 * 1024 * 1024

MAX_METADATA = 8 * 1024 * 1024

MAX_RECORDS = 16384

MAX_DEADLINE = 3600

STAMP_KEYS = ('dev', 'ino', 'mode', 'uid', 'size', 'mtime_ns', 'ctime_ns')

INDEX_WRITER = '7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b'

INDEX_WRITER_BYTES = 33445

AUTHOR_SHA256 = 'a2e69aef10deb6186ac49401516ffba9a165b2f3cc94c8001646b6ac9a5b701d'

AUTHOR_BYTES = 38266

CLEANUP_SHA256 = '28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'

CLEANUP_BYTES = 38195

PROCESSES_SHA256 = 'bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'

STAGED_WRITER = Path('/data1/yanruj/lanl17-index-source-20261007-a1/writer.py')

LOG_FILE_CAP = 16 * 1024 * 1024

RECEIPT_CAP = 16384

SIGNALS = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)

FORBIDDEN = {'.codex', '.ssh', '.aws', 'auth.json', 'provider.json', 'prompt.txt', 'feedback.txt'}

class Refused(ValueError):
    pass

def require(condition, code):
    if not condition:
        raise Refused(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def digest(value):
    # Exact public artifacts.digest / selected6a whole-object policy.
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=True, allow_nan=False).encode())

def exact(value, keys, code):
    require(isinstance(value, dict) and set(value) == set(keys), code)
    return value

def full_hash(value, length=64):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value),
            'full_hash_required')
    return value

def strict_json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'duplicate_json_key')
            result[key] = value
        return result
    def nonfinite(_):
        raise Refused('nonfinite_json_constant')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)

def remaining(deadline):
    left = deadline - time.monotonic()
    require(left > 0, 'finite_metadata_deadline_exceeded')
    return left

def checked_path(text, *, directory=False, owned=True):
    require(isinstance(text, (str, Path)), 'explicit_path_required')
    path = Path(text)
    require(path.is_absolute() and '..' not in path.parts and
            all(not part.is_symlink() for part in (path, *path.parents)),
            'absolute_nonsymlink_path_required')
    actual = path.resolve(strict=True)
    status = actual.stat()
    require(stat.S_ISDIR(status.st_mode) if directory else stat.S_ISREG(status.st_mode),
            'original_regular_path_required')
    require(not owned or status.st_uid == os.getuid(), 'original_UID_differs')
    return actual

def stamp(status):
    return {'dev': status.st_dev, 'ino': status.st_ino, 'mode': status.st_mode,
            'uid': status.st_uid, 'size': status.st_size,
            'mtime_ns': status.st_mtime_ns, 'ctime_ns': status.st_ctime_ns}

def file_pin(value):
    exact(value, ('path', 'bytes', 'sha256'), 'exact_original_file_pin_required')
    require(type(value['bytes']) is int and 0 <= value['bytes'] <= MAX_METADATA,
            'bounded_original_metadata_file_required')
    full_hash(value['sha256'])
    return dict(value)

def returned_bytes(pin, maximum, deadline, expected_stamp=None):
    remaining(deadline)
    path = checked_path(pin['path'])
    require(type(pin['bytes']) is int and 0 <= pin['bytes'] <= maximum,
            'bounded_exact_original_size_required')
    full_hash(pin['sha256'])
    if expected_stamp is not None:
        exact(expected_stamp, STAMP_KEYS, 'exact_parent_inventory_stat_required')
        require(all(type(value) is int and value >= 0 for value in expected_stamp.values()),
                'nonnegative_exact_inventory_stat_required')
    with path.open('rb') as stream:
        before = stamp(os.fstat(stream.fileno()))
        require(stat.S_ISREG(before['mode']) and before['uid'] == os.getuid() and
                before['size'] == pin['bytes'], 'original_fd_type_UID_size_differs')
        require(expected_stamp is None or before == expected_stamp, 'parent_inventory_inode_or_stat_differs')
        blocks, size = [], 0
        while True:
            remaining(deadline)
            block = stream.read(min(1024 * 1024, pin['bytes'] + 1 - size))
            if not block:
                break
            blocks.append(block)
            size += len(block)
            require(size <= pin['bytes'], 'returned_original_size_differs')
        after = stamp(os.fstat(stream.fileno()))
    raw = b''.join(blocks)
    require(len(raw) == pin['bytes'] and sha(raw) == pin['sha256'], 'returned_original_bytes_differs')
    require(before == after == stamp(checked_path(pin['path']).stat()), 'original_inode_or_content_changed')
    remaining(deadline)
    return raw, before

def fresh_output(text, forbidden):
    path = Path(text)
    require(path.is_absolute() and '..' not in path.parts and
            re.fullmatch('[A-Za-z0-9_.-]+', path.name), 'fresh_absolute_output_required')
    parent = checked_path(path.parent, directory=True)
    path = parent / path.name
    require(not path.exists() and not path.is_symlink(), 'fresh_output_required')
    require(any(path.is_relative_to(Path(prefix)) for prefix in ('/data/yanruj', '/data1/yanruj')),
            'owned_mbit10_external_output_prefix_required')
    require(all(not path.is_relative_to(root) for root in forbidden), 'output_inside_source_raw_campaign_refused')
    return path

def original_seal(raw, identity):
    full_hash(identity)
    value = strict_json(raw)
    require(isinstance(value, dict) and value.get('identity_sha256') == identity and
            digest({key: child for key, child in value.items() if key != 'identity_sha256'}) == identity,
            'original_true_policy_seal_differs')
    return value

def stop_group(child, *, grace_seconds=20):
    """Reap an owned session leader and kill its remaining same-group children.

    Call only for a Popen started with start_new_session=True. A returned or
    reaped leader does not establish that its process group is empty.
    """
    if child is None:
        return
    try:
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            child.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            pass
    finally:
        # Also finish cleanup if a second interruption unwinds the grace wait.
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait(timeout=5)

def own_processes():
    """Only descendants/adopted orphans of this isolated subreaper, with UID/start-time identity."""
    rows = {}
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if proc.stat().st_uid != os.getuid():
                continue
            rest = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
            rows[int(proc.name)] = {'ppid': int(rest[1]), 'start_time': rest[19]}
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    found, roots = {}, {os.getpid()}
    while True:
        additions = {pid: row for pid, row in rows.items() if pid not in roots and row['ppid'] in roots}
        if not additions:
            return found
        found.update(additions)
        roots.update(additions)

def cleanup_owned():
    terminated = []
    for sig, wait_s in ((signal.SIGTERM, 15), (signal.SIGKILL, 5)):
        remaining = own_processes()
        for pid, row in remaining.items():
            try:
                current = own_processes().get(pid)
                if current and current['start_time'] == row['start_time']:
                    os.kill(pid, sig)
                    terminated.append({'pid': pid, 'start_time': row['start_time'], 'signal': sig.name})
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + wait_s
        while time.monotonic() < deadline:
            while True:
                try:
                    pid, _ = os.waitpid(-1, os.WNOHANG)
                except ChildProcessError:
                    break
                if not pid:
                    break
            if not own_processes():
                break
            time.sleep(0.1)
    return {'subreaper': True, 'terminated_owned_processes': terminated, 'survivors': own_processes()}

def enable_subreaper():
 require(sys.platform=='linux' and os.getuid()!=0,'Linux non-root isolated supervisor required')
 require(ctypes.CDLL(None).prctl(36,1,0,0,0)==0,'Linux child subreaper enable failed')

class Interruption(BaseException):
    def __init__(self, number):
        self.number = number

class PrivateParser(argparse.ArgumentParser):
    def error(self, _message):
        raise Refused('invalid_envelope_argument_vector')

def private_path(text, *, directory=False, owned=True):
    require(isinstance(text, (str, Path)) and len(str(text)) <= 1024, 'bounded_explicit_private_path_required')
    path = checked_path(text, directory=directory, owned=owned)
    require(not FORBIDDEN.intersection(path.parts), 'credential_provider_prompt_path_refused')
    return path

def pinned_control(text, expected_sha, expected_bytes, deadline):
    path = private_path(text)
    pin = file_pin({'path': str(path), 'bytes': expected_bytes, 'sha256': expected_sha})
    returned_bytes(pin, MAX_METADATA, deadline)
    return pin

def executable_pin(text, expected_sha, deadline):
    path = private_path(text, owned=False)
    require(str(path) == text, 'explicit_canonical_executable_path_required')
    before = stamp(path.stat())
    require(before['uid'] in {0, os.getuid()} and before['mode'] & 0o111 and not before['mode'] & 0o022 and
            0 < before['size'] <= MAX_CATALOG_FILE, 'owned_or_system_regular_executable_required')
    hasher, size = hashlib.sha256(), 0
    with path.open('rb') as stream:
        require(stamp(os.fstat(stream.fileno())) == before, 'executable_inode_changed_before_hash')
        while True:
            remaining(deadline)
            block = stream.read(1024 * 1024)
            if not block:
                break
            size += len(block)
            require(size <= before['size'], 'executable_size_changed_during_hash')
            hasher.update(block)
        require(stamp(os.fstat(stream.fileno())) == before, 'executable_inode_changed_after_hash')
    require(size == before['size'] and stamp(private_path(path, owned=False).stat()) == before and
            hasher.hexdigest() == full_hash(expected_sha), 'exact_parent_pinned_executable_differs')
    return {'path': str(path), 'bytes': size, 'sha256': expected_sha, 'stat': before}

def bundle_pins(source, deadline):
    root = private_path(source / 'swdb-project/swdb', directory=True)
    paths = sorted(root.rglob('*.py'))
    require(len(paths) == 185 and all(not p.is_symlink() for p in root.rglob('*')),
            'unchanged_live_185_module_inventory_required')
    pins, hashes = [], {}
    for path in paths:
        remaining(deadline)
        path = private_path(path)
        before = stamp(path.stat())
        require(before['size'] <= MAX_METADATA, 'original_source_module_metadata_bound_exceeded')
        # Hash the exact returned bytes before recording their immutable pin.
        with path.open('rb') as stream:
            require(stamp(os.fstat(stream.fileno())) == before, 'module_inode_changed_before_read')
            raw = stream.read(before['size'] + 1)
            require(stamp(os.fstat(stream.fileno())) == before, 'module_inode_changed_after_read')
        require(len(raw) == before['size'] and stamp(private_path(path).stat()) == before,
                'module_returned_bytes_or_inode_changed')
        hashes[path.relative_to(root).as_posix()] = sha(raw)
        pins.append({'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)})
    require(digest(hashes) == F6, 'unchanged_live_185_module_F6_required')
    return pins

def private_file(path, raw, cap):
    require(len(raw) <= cap, 'bounded_private_metadata_required')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        require(os.fstat(stream.fileno()).st_uid == os.getuid() and
                stat.S_IMODE(os.fstat(stream.fileno()).st_mode) == 0o600, 'exclusive_private_file_required')
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}

def stream_pin(path, cap, deadline):
    path = private_path(path)
    before = stamp(path.stat())
    require(stat.S_IMODE(before['mode']) == 0o600 and before['size'] <= cap,
            'private_bounded_original_capture_required')
    hasher, size = hashlib.sha256(), 0
    with path.open('rb') as stream:
        require(stamp(os.fstat(stream.fileno())) == before, 'private_capture_inode_changed_before_hash')
        while True:
            remaining(deadline)
            block = stream.read(1024 * 1024)
            if not block:
                break
            size += len(block)
            require(size <= cap, 'private_capture_limit_exceeded')
            hasher.update(block)
        require(stamp(os.fstat(stream.fileno())) == before, 'private_capture_inode_changed_after_hash')
    require(size == before['size'] and stamp(private_path(path).stat()) == before, 'private_capture_replaced_or_changed')
    return {'path': str(path), 'bytes': size, 'sha256': hasher.hexdigest(), 'original_sealed': False}

def bounded_print(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False).encode()
    require(len(raw) <= RECEIPT_CAP, 'bounded_returned_receipt_required')
    print(raw.decode('ascii'))


ENVELOPE_SHA256 = '1ee5ffbdf1ef322cfd5bfec4b6e402c29d23c776e855f01d25208ebbece0fcfc'
ENVELOPE_BYTES = 38790
INNER_FORMAT = 'swdb.lanl17-original-index-writer-private-envelope.v1'
FORMAT = 'swdb.lanl17-original-index-writer-private-outer-capture.v1'
INNER_FLAGS = ('request', 'request-sha256', 'request-author-source', 'request-author-source-sha256',
    'parent-review-sha256', 'output-directory', 'log-directory', 'envelope-sha256',
    'cleanup-helper-source', 'python-executable', 'python-executable-sha256',
    'timeout-executable', 'timeout-executable-sha256', 'timeout-family')


def main():
    parser = PrivateParser(description='Private remote outer capture for unchanged1ee envelope', add_help=False)
    for name in (*INNER_FLAGS, 'envelope-source', 'outer-log-directory', 'capture-source-sha256',
                 'parent-reviewed-argv-sha256'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10' and
            os.getuid() == os.geteuid() == 114316761 and pwd.getpwuid(os.getuid()).pw_name == 'yanruj',
            'actual_Linux_mbit10_reviewed_UID_account_required')
    def metadata_alarm(_number, _frame):raise Refused('finite_outer_capture_metadata_deadline_exceeded')
    signal.signal(signal.SIGALRM, metadata_alarm)
    signal.setitimer(signal.ITIMER_REAL, 60)
    deadline = time.monotonic() + 60
    own = private_path(__file__)
    own_pin = file_pin({'path':str(own), 'bytes':own.stat().st_size, 'sha256':full_hash(args.capture_source_sha256)})
    returned_bytes(own_pin, MAX_METADATA, deadline)
    require(args.envelope_sha256 == ENVELOPE_SHA256, 'unchanged_reviewed1ee_envelope_required')
    envelope_pin = pinned_control(args.envelope_source, ENVELOPE_SHA256, ENVELOPE_BYTES, deadline)
    writer_pin = pinned_control(STAGED_WRITER, INDEX_WRITER, INDEX_WRITER_BYTES, deadline)
    require(args.request_author_source_sha256 == AUTHOR_SHA256, 'unchanged_reviewed_a2_author_required')
    author_pin = pinned_control(args.request_author_source, AUTHOR_SHA256, AUTHOR_BYTES, deadline)
    helper_pin = pinned_control(args.cleanup_helper_source, CLEANUP_SHA256, CLEANUP_BYTES, deadline)
    request_path = private_path(args.request)
    require(str(request_path) == args.request, 'canonical_original_request_path_required')
    request_pin = file_pin({'path':str(request_path), 'bytes':request_path.stat().st_size,
                           'sha256':full_hash(args.request_sha256)})
    raw, _ = returned_bytes(request_pin, MAX_METADATA, deadline)
    request = strict_json(raw)
    exact(request, ('format','context','originals','catalog_inventory','summary_binding','limits',
        'parent_review','output_directory'), 'original_request8fields_required')
    require(request['format'] == 'swdb.lanl17-parent-record-index-request.v1', 'original_request_format_required')
    ctx = exact(request['context'], ('source_C','estimator_sha256','final_R','account','campaign',
        'source_path','project','records_directory','manifest_identity_sha256'), 'original_context_required')
    require(ctx['source_C'] == C and ctx['estimator_sha256'] == F6 and ctx['campaign'] in CIDS and
            ctx['account'] == {'host':'mbit10','platform':'linux','uid':os.getuid(),'user':'yanruj'},
            'exact_original_C_F6_campaign_account_required')
    exact(ctx['final_R'], ('commit','tree'), 'original_R_tree_required')
    full_hash(ctx['final_R']['commit'],40); full_hash(ctx['final_R']['tree'],40)
    full_hash(args.parent_review_sha256)
    require(digest(request['parent_review']) == args.parent_review_sha256, 'explicit_original_parent_review_digest_required')
    originals = exact(request['originals'], ('manifest_M2','helper_source','auditor_source','collector_source',
        'validation_argv','validation_exit','validation_stdout','validation_stderr'), 'original_supplier_roles_required')
    m2desc = exact(originals['manifest_M2'], ('path','bytes','sha256','identity_sha256','canonical_ensure_ascii'),
        'exact_original_M2_pin_required')
    require(m2desc['canonical_ensure_ascii'] is True, 'original_M2_True_policy_required')
    m2pin = file_pin({k:m2desc[k] for k in ('path','bytes','sha256')})
    private_path(m2pin['path'])
    m2raw, _ = returned_bytes(m2pin, MAX_METADATA, deadline)
    m2 = original_seal(m2raw,full_hash(m2desc['identity_sha256']))
    source = private_path(ctx['source_path'],directory=True)
    require(str(source) == ctx['source_path'] and source.is_relative_to(Path('/data1/yanruj')) and
            private_path(ctx['project'],directory=True) == source/'swdb-project', 'exact_M2_source_project_required')
    require(m2['format'] == 'swdb.lanl17-parent-population.v1' and m2['source'] == str(source) and
            m2['source_commit'] == ctx['final_R']['commit'] and m2['estimator_sha256'] == F6 and
            m2['helper_sha256'] == HELPER and m2['source_clean'] is True and
            m2['identity_sha256'] == ctx['manifest_identity_sha256'], 'exact_pinned_M2_source_required')
    raw_root = private_path(m2['raw'],directory=True)
    require(str(raw_root) == m2['raw'] and raw_root.is_relative_to(Path('/data/yanruj')) and
            Path(m2pin['path']) == raw_root/'manifest.json', 'exact_M2_raw_manifest_route_required')
    campaigns = tuple(raw_root/'campaign-runs'/'extensa'/cid for cid in CIDS)
    for path in campaigns:
        require(all(not p.is_symlink() for p in (path,*path.parents)), 'M2_campaign_redirect_refused')
        if path.exists():private_path(path,directory=True)
    records = private_path(ctx['records_directory'],directory=True)
    require(str(records) == ctx['records_directory'] and records == campaigns[CIDS.index(ctx['campaign'])]/'records',
            'exact_original_one_catalog_route_required')
    limits = exact(request['limits'], ('catalog_record_count','catalog_total_bytes','max_catalog_file_bytes',
        'max_catalog_total_bytes','max_output_metadata_bytes','metadata_deadline_seconds'), 'original_limits_required')
    require(limits['max_catalog_file_bytes'] == MAX_CATALOG_FILE and limits['max_catalog_total_bytes'] == MAX_CATALOG_TOTAL and
            limits['max_output_metadata_bytes'] == MAX_METADATA and type(limits['metadata_deadline_seconds']) is int and
            60 <= limits['metadata_deadline_seconds'] <= MAX_DEADLINE, 'original_writer_bounds_unchanged_required')
    writer_output = fresh_output(args.output_directory,(source,raw_root,*campaigns))
    require(request['output_directory'] == args.output_directory == str(writer_output), 'original_reviewed_output_required')
    inner_logs = fresh_output(args.log_directory,(source,raw_root,*campaigns,writer_output))
    require(str(inner_logs) == args.log_directory and not writer_output.is_relative_to(inner_logs), 'disjoint_inner_outputs_required')
    forbidden = (source,raw_root,*campaigns,writer_output,inner_logs)
    outer_logs = fresh_output(args.outer_log_directory,forbidden)
    require(str(outer_logs) == args.outer_log_directory and all(not p.is_relative_to(outer_logs) for p in forbidden),
            'outer_logs_disjoint_M2_and_both_inner_outputs_required')
    python_pin = executable_pin(args.python_executable,full_hash(args.python_executable_sha256),deadline)
    require(Path(sys.executable).resolve() == Path(python_pin['path']), 'same_pinned_native_capture_envelope_writer_interpreter_required')
    require(args.timeout_family == 'parent_reviewed_GNU_coreutils_timeout', 'explicit_parent_GNU_timeout_family_required')
    timeout_pin = executable_pin(args.timeout_executable,full_hash(args.timeout_executable_sha256),deadline)
    process_path = source/'swdb-project/swdb/processes.py'
    process_pin = pinned_control(process_path,PROCESSES_SHA256,process_path.stat().st_size,deadline)
    modules = bundle_pins(source,deadline)
    pins = [own_pin,envelope_pin,writer_pin,author_pin,helper_pin,request_pin,m2pin,process_pin,*modules]
    def recheck(cap):
        for pin in pins:returned_bytes(pin,MAX_METADATA,cap)
        require(len(bundle_pins(source,cap)) == 185, 'unchanged_live_F6_inventory_required')
        executable_pin(python_pin['path'],python_pin['sha256'],cap)
        executable_pin(timeout_pin['path'],timeout_pin['sha256'],cap)
    recheck(deadline)
    envelope_argv = [python_pin['path'],'-B',envelope_pin['path']]
    for name in INNER_FLAGS:envelope_argv.extend(('--'+name,getattr(args,name.replace('-','_'))))
    outer_cap = limits['metadata_deadline_seconds'] + 420
    argv = [timeout_pin['path'],'--signal=TERM','--kill-after=60s',str(outer_cap)+'s',*envelope_argv]
    require(digest(argv) == full_hash(args.parent_reviewed_argv_sha256), 'explicit_parent_reviewed_complete_outer_argv_required')
    hard = resource.getrlimit(resource.RLIMIT_FSIZE)[1]
    require(hard == resource.RLIM_INFINITY or hard >= LOG_FILE_CAP, 'private_capture_file_budget_not_available')
    def file_limit():resource.setrlimit(resource.RLIMIT_FSIZE,(LOG_FILE_CAP,LOG_FILE_CAP))
    previous = {sig:signal.getsignal(sig) for sig in SIGNALS}
    def interrupt(number,_frame):raise Interruption(number)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(); start_clock = time.monotonic()
    require(fresh_output(args.outer_log_directory,forbidden) == outer_logs, 'outer_logs_no_longer_fresh')
    outer_logs.mkdir(mode=0o700)
    require(stat.S_IMODE(private_path(outer_logs,directory=True).stat().st_mode) == 0o700, 'exclusive_private_outer_directory_required')
    start = {'format':FORMAT+'.start','started_utc':started,'original_sealed':False,
        'envelope_sha256':ENVELOPE_SHA256,'request_sha256':request_pin['sha256'],
        'argv_sha256':digest(argv),'GNU_timeout_seconds':outer_cap,'GNU_kill_after_seconds':60,
        'administration_basis':'Finite prospective unmeasured writer deadline +420; original inner limits/argv unchanged.'}
    private_file(outer_logs/'start.json',(json.dumps(start,sort_keys=True,ensure_ascii=True)+'\n').encode(),RECEIPT_CAP)
    out_fd = os.open(outer_logs/'stdout',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    err_fd = os.open(outer_logs/'stderr',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    child = None; exit_code = None; enabled = False; state = 'not_launched'; failure = None; received = None
    cleanup_errors = []; cleanup = {'subreaper':False,'terminated_owned_processes':[],'survivors':{}}
    for sig in SIGNALS:signal.signal(sig,interrupt)
    signal.setitimer(signal.ITIMER_REAL,0)
    try:
        enable_subreaper(); enabled = True
        with os.fdopen(out_fd,'wb') as out,os.fdopen(err_fd,'wb') as err:
            # Inherit environment without inspecting, serializing or changing its body/HOME/authentication.
            child = subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                start_new_session=True,close_fds=True,preexec_fn=file_limit)
            exit_code = child.wait(timeout=outer_cap+65)
            state = 'envelope_returned' if exit_code == 0 else 'envelope_or_timeout_failed'
    except Interruption as error:
        state = 'external_signal'; received = signal.Signals(error.number).name
        failure = (type(error).__name__,sha(str(error.number).encode()))
    except BaseException as error:
        state = 'capture_error'; failure = (type(error).__name__,sha(str(error).encode(errors='replace')))
    finally:
        for sig in SIGNALS:signal.signal(sig,signal.SIG_IGN)
        if enabled:
            try:stop_group(child,grace_seconds=15)
            except BaseException as error:cleanup_errors.append(type(error).__name__)
            try:cleanup = cleanup_owned()
            except BaseException as error:cleanup_errors.append(type(error).__name__)
        if child is not None and child.returncode is not None:exit_code = child.returncode
        if cleanup_errors or cleanup.get('survivors') or enabled and cleanup.get('subreaper') is not True:state = 'cleanup_failed'
    postflight = time.monotonic()+60
    signal.setitimer(signal.ITIMER_REAL,60)
    inner_receipt_pin = None; inner_identity = None
    try:
        recheck(postflight)
        require(os.getuid() == os.geteuid() == 114316761 and pwd.getpwuid(os.getuid()).pw_name == 'yanruj', 'final_account_differs')
        private_path(outer_logs,directory=True); private_path(source,directory=True); private_path(raw_root,directory=True)
        for path in campaigns:
            require(all(not p.is_symlink() for p in (path,*path.parents)), 'final_M2_campaign_redirect_refused')
            if path.exists():private_path(path,directory=True)
        for path in (writer_output,inner_logs):
            private_path(path.parent,directory=True)
            if path.exists():private_path(path,directory=True)
        require(all(not outer_logs.is_relative_to(p) and not p.is_relative_to(outer_logs) for p in forbidden), 'final_outer_path_separation_required')
        if state == 'envelope_returned':
            receipt_path = private_path(inner_logs/'receipt.json')
            require(stat.S_IMODE(receipt_path.stat().st_mode) == 0o600, 'private_original_inner_receipt_required')
            inner_receipt_pin = file_pin({'path':str(receipt_path),'bytes':receipt_path.stat().st_size,
                'sha256':stream_pin(receipt_path,RECEIPT_CAP,postflight)['sha256']})
            receipt_raw,_ = returned_bytes(inner_receipt_pin,RECEIPT_CAP,postflight)
            candidate = strict_json(receipt_raw)
            inner_identity = full_hash(candidate['identity_sha256'])
            data = original_seal(receipt_raw,inner_identity)
            cleanup_row = exact(data['cleanup'],('subreaper','terminated_owned_process_count','survivor_count','error_classes'), 'exact_inner_cleanup_row_required')
            inner_writer_argv = [python_pin['path'],'-B',writer_pin['path']]
            for name in INNER_FLAGS[:6]:inner_writer_argv.extend(('--'+name,getattr(args,name.replace('-','_'))))
            inner_gnu_argv = [timeout_pin['path'],'--signal=TERM','--kill-after=60s',str(limits['metadata_deadline_seconds']+120)+'s',*inner_writer_argv]
            require(data['format'] == INNER_FORMAT and data['canonical_ensure_ascii'] is True and
                data['state'] == 'writer_returned' and data['envelope_exit'] == data['captured_timeout_tool_exit'] == 0 and
                data['failure_class'] is None and data['failure_message_sha256'] is None and
                cleanup_row['subreaper'] is True and type(cleanup_row['survivor_count']) is int and cleanup_row['survivor_count'] == 0 and
                cleanup_row['error_classes'] == [] and data['source_C'] == C and data['F6'] == F6 and
                data['module_count'] == 185 and data['final_R'] == ctx['final_R'] and
                data['envelope_source_pin'] == envelope_pin and data['request_pin'] == request_pin and
                data['writer_source_pin'] == writer_pin and data['author_source_pin'] == author_pin and
                data['cleanup_helper_source_pin'] == helper_pin and data['processes_source_pin'] == process_pin and
                data['original_writer_limits'] == limits and data['writer_output_directory'] == str(writer_output) and
                data['log_directory'] == str(inner_logs) and data['argv_sha256'] == digest(inner_gnu_argv) and
                data['GNU_timeout_seconds'] == limits['metadata_deadline_seconds']+120 and data['GNU_kill_after_seconds'] == 60 and
                data['raw_stdout_stderr_or_original_diagnostics_transferred'] is False and
                data['independent_validation_or_campaign_admission'] is False,
                'exact_reviewed_inner_success_custody_required')
    except BaseException as error:
        state = 'final_custody_failed'; failure = (type(error).__name__,sha(str(error).encode(errors='replace')))
    logs = {name:stream_pin(outer_logs/name,LOG_FILE_CAP if name in {'stdout','stderr'} else RECEIPT_CAP,postflight)
            for name in ('start.json','stdout','stderr')}
    if any(logs[name]['bytes'] >= LOG_FILE_CAP for name in ('stdout','stderr')):state = 'private_outer_log_budget_reached'
    code = 0 if state == 'envelope_returned' and exit_code == 0 and inner_receipt_pin and not cleanup_errors and not cleanup.get('survivors') else 1
    receipt = {'format':FORMAT,'canonical_ensure_ascii':True,'started_utc':started,
        'ended_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'elapsed_metadata_s':time.monotonic()-start_clock,
        'state':state,'capture_exit':code,'captured_GNU_envelope_exit':exit_code,'received_signal':received,
        'failure_class':None if failure is None else failure[0],'failure_message_sha256':None if failure is None else failure[1],
        'capture_source_pin':own_pin,'envelope_source_pin':envelope_pin,'writer_source_pin':writer_pin,'author_source_pin':author_pin,
        'request_pin':request_pin,'parent_review_sha256':args.parent_review_sha256,'M2_pin':dict(m2pin,identity_sha256=m2['identity_sha256']),
        'cleanup_source_pin':helper_pin,'processes_source_pin':process_pin,'python_executable_pin':python_pin,'GNU_timeout_executable_pin':timeout_pin,
        'source_C':C,'F6':F6,'module_count':185,'final_R':ctx['final_R'],'original_writer_limits':limits,
        'envelope_argv_sha256':digest(envelope_argv),'parent_reviewed_outer_argv_sha256':digest(argv),'outer_GNU_timeout_seconds':outer_cap,
        'outer_GNU_kill_after_seconds':60,'outer_Popen_wait_seconds':outer_cap+65,'private_log_file_cap_bytes':LOG_FILE_CAP,
        'outer_log_directory':str(outer_logs),'log_pins':logs,'inner_success_receipt_pin':inner_receipt_pin,'inner_success_receipt_identity_sha256':inner_identity,
        'cleanup':{'subreaper':enabled,'terminated_owned_process_count':len(cleanup.get('terminated_owned_processes',[])),
            'survivor_count':len(cleanup.get('survivors',{})),'error_classes':cleanup_errors},
        'raw_startup_GNU_envelope_or_writer_diagnostics_transferred':False,'original_captures_unsealed':True,
        'failed_partial_files_retained':True,'independent_validation_or_campaign_admission':False,
        'scope':'Private original-envelope startup/GNU/child diagnostic capture and metadata custody only; explicit parent input facts are not independently observed. Unmeasured finite outer administration leaves inner argv/source/science limits unchanged.'}
    receipt['identity_sha256'] = digest(receipt)
    raw = (json.dumps(receipt,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
    receipt_pin = private_file(outer_logs/'receipt.json',raw,RECEIPT_CAP)
    returned_bytes(receipt_pin,RECEIPT_CAP,postflight)
    recheck(postflight)
    if inner_receipt_pin:returned_bytes(inner_receipt_pin,RECEIPT_CAP,postflight)
    returned_bytes(own_pin,MAX_METADATA,postflight)
    signal.setitimer(signal.ITIMER_REAL,0)
    for sig,handler in previous.items():signal.signal(sig,handler)
    bounded_print({'format':FORMAT,'receipt_pin':receipt_pin,'receipt_identity_sha256':receipt['identity_sha256'],
        'state':state,'capture_exit':code,'failure_class':receipt['failure_class'],'failure_message_sha256':receipt['failure_message_sha256'],
        'raw_diagnostics_returned':False})
    return code


if __name__ == '__main__':
    try:sys.exit(main())
    except SystemExit:raise
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL,0)
        raw = json.dumps({'format':FORMAT+'.refusal','state':'refused','failure_class':type(error).__name__,
            'failure_message_sha256':sha(str(error).encode(errors='replace')),'raw_diagnostics_returned':False},
            ensure_ascii=True,allow_nan=False).encode()
        if len(raw) <= RECEIPT_CAP:print(raw.decode('ascii'),file=sys.stderr)
        sys.exit(3)

