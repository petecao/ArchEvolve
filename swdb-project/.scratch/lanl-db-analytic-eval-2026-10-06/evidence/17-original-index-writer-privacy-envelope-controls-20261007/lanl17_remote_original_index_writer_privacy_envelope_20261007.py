#!/usr/bin/env python3
"""NOT RUN: remote privacy/infrastructure envelope for immutable original7a writer.

2026-10-07 ET. Future parent-reviewed actual argv only. Original six writer flags,
request/review, source and scientific bounds remain unchanged. All child stdout/
stderr stay private ON MBIT10; only bounded receipt/status/pins are returned.
This envelope is not a validator, request author, catalog admission or repair.
"""
import argparse
import ctypes
import datetime
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
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

def plain_record(value, depth=0, active=None):
    # Refuse unsupported values/alias cycles rather than normalize their identity.
    require(depth <= 100, 'record_metadata_depth_exceeded')
    active = set() if active is None else active
    if isinstance(value, (dict, list)):
        require(id(value) not in active, 'cyclic_record_alias_refused')
        active.add(id(value))
        if isinstance(value, dict):
            require(all(isinstance(key, str) for key in value), 'nonstring_record_key_refused')
            children = value.values()
        else:
            children = value
        for child in children:
            plain_record(child, depth + 1, active)
        active.remove(id(value))
    else:
        require(value is None or type(value) in (str, int, bool) or
                type(value) is float and math.isfinite(value), 'unsupported_record_value_refused')

def utc(value):
    require(isinstance(value, str), 'explicit_UTC_observation_required')
    parsed = datetime.datetime.fromisoformat(value)
    require(parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0,
            'explicit_UTC_observation_required')
    return parsed

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

def record_relative(value):
    require(isinstance(value, str), 'explicit_record_relative_path_required')
    path = PurePosixPath(value)
    require(not path.is_absolute() and '..' not in path.parts and '\\' not in value and
            path.as_posix() == value and path.suffix in {'.yaml', '.yml'} and
            not any(part.startswith('.') for part in path.parts), 'exact_public_record_path_required')
    return value

def approved_inventory(value, limits):
    require(isinstance(value, list) and 0 < len(value) <= MAX_RECORDS, 'explicit_full_real_inventory_required')
    result = {}
    total = 0
    for row in value:
        exact(row, ('path', 'bytes', 'sha256', 'stat'), 'exact_original_catalog_inventory_row_required')
        rel = record_relative(row['path'])
        require(rel not in result, 'duplicate_inventory_path')
        require(type(row['bytes']) is int and 0 <= row['bytes'] <= MAX_CATALOG_FILE,
                'distinct_128MiB_catalog_source_read_bound_exceeded')
        full_hash(row['sha256'])
        exact(row['stat'], STAMP_KEYS, 'exact_parent_inventory_stat_required')
        require(row['stat']['size'] == row['bytes'], 'approved_inventory_size_and_stat_differ')
        total += row['bytes']
        require(total <= MAX_CATALOG_TOTAL, 'distinct_2GiB_catalog_source_read_bound_exceeded')
        result[rel] = dict(row)
    require([row['path'] for row in value] == sorted(result), 'sorted_complete_inventory_required')
    require(type(limits['catalog_record_count']) is int and limits['catalog_record_count'] == len(result) and
            type(limits['catalog_total_bytes']) is int and limits['catalog_total_bytes'] == total,
            'explicit_exact_inventory_count_or_total_differs')
    return result

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

def check_writer_review(request):
    review = exact(request['parent_review'], ('basis', 'writer_sha256',
        'reviewed_request_payload_sha256', 'actual_inputs_parent_approved',
        'fixtures_or_replays_allowed', 'validated_snapshot'), 'exact_original7a_parent_review_required')
    require(review['basis'] == 'explicit_parent_review_of_real_quiescent_catalog_and_original_prior_full_validation' and
            review['writer_sha256'] == INDEX_WRITER and review['actual_inputs_parent_approved'] is True and
            review['fixtures_or_replays_allowed'] is False and
            review['reviewed_request_payload_sha256'] == digest({k:v for k,v in request.items() if k != 'parent_review'}),
            'original7a_explicit_request_review_boundary_differs')
    observations = exact(review['validated_snapshot'], ('campaign', 'records_directory',
        'catalog_inventory_sha256', 'validation_files_sha256', 'prior_validation_full_catalogue',
        'catalog_unchanged_since_original_validation', 'all_campaign_processes_stopped',
        'exclusive_snapshot_ownership_confirmed', 'observed_utc'), 'exact_original7a_parent_snapshot_observations_required')
    require(observations['campaign'] == request['context']['campaign'] and
            observations['records_directory'] == request['context']['records_directory'] and
            observations['catalog_inventory_sha256'] == digest(request['catalog_inventory']) and
            observations['validation_files_sha256'] == {role:request['originals'][role]['sha256'] for role in VALIDATION_ROLES} and
            all(observations[k] is True for k in ('prior_validation_full_catalogue',
                'catalog_unchanged_since_original_validation', 'all_campaign_processes_stopped',
                'exclusive_snapshot_ownership_confirmed')), 'original7a_inherited_snapshot_observation_binding_differs')
    observed = utc(observations['observed_utc'])
    require(observed <= datetime.datetime.now(datetime.timezone.utc), 'snapshot_observation_cannot_be_future')
    return review, observations

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

INDEX_WRITER = '7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b'
INDEX_WRITER_BYTES = 33445
AUTHOR_SHA256 = 'a2e69aef10deb6186ac49401516ffba9a165b2f3cc94c8001646b6ac9a5b701d'
AUTHOR_BYTES = 38266
CLEANUP_SHA256 = '28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
CLEANUP_BYTES = 38195
PROCESSES_SHA256 = 'bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
VALIDATION_ROLES = ('validation_argv', 'validation_exit', 'validation_stdout', 'validation_stderr')
STAGED_WRITER = Path('/data1/yanruj/lanl17-index-source-20261007-a1/writer.py')
LOG_FILE_CAP = 16 * 1024 * 1024  # Infrastructure only; original outputs already have8MiB cap.
RECEIPT_CAP = 16384
SIGNALS = (signal.SIGTERM, signal.SIGINT, signal.SIGHUP)
FORBIDDEN = {'.codex', '.ssh', '.aws', 'auth.json', 'provider.json', 'prompt.txt', 'feedback.txt'}
FORMAT = 'swdb.lanl17-original-index-writer-private-envelope.v1'

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


def main():
    parser = PrivateParser(description='Remote original7a private-capture envelope; explicit reviewed input pins only', add_help=False)
    for name in ('request', 'request-sha256', 'request-author-source', 'request-author-source-sha256',
                 'parent-review-sha256', 'output-directory', 'log-directory', 'envelope-sha256',
                 'cleanup-helper-source', 'python-executable', 'python-executable-sha256',
                 'timeout-executable', 'timeout-executable-sha256', 'timeout-family'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10' and
            os.getuid() == os.geteuid() == 114316761 and pwd.getpwuid(os.getuid()).pw_name == 'yanruj',
            'actual_Linux_mbit10_reviewed_UID_account_required')
    require(args.timeout_family == 'parent_reviewed_GNU_coreutils_timeout', 'explicit_parent_GNU_timeout_family_required')
    def metadata_alarm(_number, _frame):raise Refused('finite_private_envelope_metadata_deadline_exceeded')
    signal.signal(signal.SIGALRM, metadata_alarm)
    preflight = time.monotonic() + 60
    signal.setitimer(signal.ITIMER_REAL, 60)
    own = private_path(__file__)
    own_pin = file_pin({'path': str(own), 'bytes': own.stat().st_size, 'sha256': full_hash(args.envelope_sha256)})
    returned_bytes(own_pin, MAX_METADATA, preflight)
    writer_pin = pinned_control(STAGED_WRITER, INDEX_WRITER, INDEX_WRITER_BYTES, preflight)
    require(full_hash(args.request_author_source_sha256) == AUTHOR_SHA256, 'unchanged_reviewed_a2_author_required')
    author_pin = pinned_control(args.request_author_source, AUTHOR_SHA256, AUTHOR_BYTES, preflight)
    cleanup_pin = pinned_control(args.cleanup_helper_source, CLEANUP_SHA256, CLEANUP_BYTES, preflight)
    request_path = private_path(args.request)
    require(str(request_path) == args.request, 'canonical_original_request_path_required')
    request_pin = file_pin({'path': str(request_path), 'bytes': request_path.stat().st_size,
                            'sha256': full_hash(args.request_sha256)})
    request_raw, _ = returned_bytes(request_pin, MAX_METADATA, preflight)
    request = strict_json(request_raw)  # Exact returned bytes are verified before parse.
    plain_record(request)
    exact(request, ('format', 'context', 'originals', 'catalog_inventory', 'summary_binding', 'limits',
                    'parent_review', 'output_directory'), 'unchanged_original_request8fields_required')
    require(request['format'] == 'swdb.lanl17-parent-record-index-request.v1', 'original_request_format_required')
    ctx = exact(request['context'], ('source_C', 'estimator_sha256', 'final_R', 'account', 'campaign',
        'source_path', 'project', 'records_directory', 'manifest_identity_sha256'), 'exact_original_context_required')
    require(ctx['source_C'] == C and ctx['estimator_sha256'] == F6 and ctx['campaign'] in CIDS,
            'original_C_F6_campaign_context_required')
    exact(ctx['final_R'], ('commit', 'tree'), 'original_R_tree_context_required')
    full_hash(ctx['final_R']['commit'], 40); full_hash(ctx['final_R']['tree'], 40)
    require(ctx['account'] == {'host': 'mbit10', 'platform': 'linux', 'uid': os.getuid(), 'user': 'yanruj'},
            'original_context_actual_account_differs')
    originals = exact(request['originals'], ('manifest_M2', 'helper_source', 'auditor_source', 'collector_source',
        'validation_argv', 'validation_exit', 'validation_stdout', 'validation_stderr'), 'exact_original_supplier_pins_required')
    m2desc = exact(originals['manifest_M2'], ('path', 'bytes', 'sha256', 'identity_sha256', 'canonical_ensure_ascii'),
                   'exact_original_M2_pin_required')
    require(m2desc['canonical_ensure_ascii'] is True, 'original_M2_true_policy_required')
    m2pin = file_pin({k:m2desc[k] for k in ('path', 'bytes', 'sha256')})
    private_path(m2pin['path'])
    m2raw, _ = returned_bytes(m2pin, MAX_METADATA, preflight)
    m2 = original_seal(m2raw, full_hash(m2desc['identity_sha256']))
    source = private_path(ctx['source_path'], directory=True)
    require(str(source) == ctx['source_path'] and source.is_relative_to(Path('/data1/yanruj')) and
            private_path(ctx['project'], directory=True) == source / 'swdb-project', 'exact_original_source_project_required')
    require(m2['format'] == 'swdb.lanl17-parent-population.v1' and m2['source'] == str(source) and
            m2['source_commit'] == ctx['final_R']['commit'] and m2['helper_sha256'] == HELPER and
            m2['estimator_sha256'] == F6 and m2['source_clean'] is True and
            m2['identity_sha256'] == ctx['manifest_identity_sha256'], 'original_M2_source_identity_required')
    raw_root = private_path(m2['raw'], directory=True)
    require(str(raw_root) == m2['raw'] and raw_root.is_relative_to(Path('/data/yanruj')) and
            Path(m2pin['path']) == raw_root / 'manifest.json', 'original_M2_raw_manifest_route_required')
    campaigns = tuple(raw_root / 'campaign-runs' / 'extensa' / cid for cid in CIDS)
    for path in campaigns:
        require(all(not part.is_symlink() for part in (path, *path.parents)), 'M2_campaign_path_redirect_refused')
        if path.exists():private_path(path, directory=True)
    records = private_path(ctx['records_directory'], directory=True)
    require(str(records) == ctx['records_directory'] and records == campaigns[CIDS.index(ctx['campaign'])] / 'records',
            'exact_original_one_catalog_route_required')
    limits = exact(request['limits'], ('catalog_record_count', 'catalog_total_bytes', 'max_catalog_file_bytes',
        'max_catalog_total_bytes', 'max_output_metadata_bytes', 'metadata_deadline_seconds'), 'original_limits_exact_required')
    require(limits['max_catalog_file_bytes'] == MAX_CATALOG_FILE and limits['max_catalog_total_bytes'] == MAX_CATALOG_TOTAL and
            limits['max_output_metadata_bytes'] == MAX_METADATA and type(limits['metadata_deadline_seconds']) is int and
            60 <= limits['metadata_deadline_seconds'] <= MAX_DEADLINE, 'original_writer_bounds_unchanged_required')
    approved_inventory(request['catalog_inventory'], limits)  # Metadata shape only; no body parsing/hash or admission here.
    review, observed = check_writer_review(request)
    require(digest(review) == full_hash(args.parent_review_sha256), 'exact_explicit_original_parent_review_sha_required')
    require(observed['records_directory'] == str(records), 'canonical_review_catalog_route_required')
    writer_output = fresh_output(args.output_directory, (source, raw_root, *campaigns))
    require(request['output_directory'] == args.output_directory == str(writer_output), 'exact_original_reviewed_writer_output_required')
    log_directory = fresh_output(args.log_directory, (source, raw_root, *campaigns, writer_output))
    require(str(log_directory) == args.log_directory and not writer_output.is_relative_to(log_directory),
            'disjoint_log_and_writer_output_in_both_directions_required')
    private_path(log_directory.parent, directory=True); private_path(writer_output.parent, directory=True)
    python_pin = executable_pin(args.python_executable, full_hash(args.python_executable_sha256), preflight)
    require(Path(sys.executable).resolve() == Path(python_pin['path']), 'exact_envelope_and_writer_interpreter_required')
    timeout_pin = executable_pin(args.timeout_executable, full_hash(args.timeout_executable_sha256), preflight)
    process_pin = pinned_control(source / 'swdb-project/swdb/processes.py', PROCESSES_SHA256,
                                 (source / 'swdb-project/swdb/processes.py').stat().st_size, preflight)
    module_pins = bundle_pins(source, preflight)
    pins = [own_pin, writer_pin, author_pin, cleanup_pin, request_pin, m2pin, process_pin, *module_pins]
    recheck_originals = lambda deadline: [returned_bytes(p, MAX_METADATA, deadline) for p in pins]
    recheck_originals(preflight)
    outer_cap = limits['metadata_deadline_seconds'] + 120
    child_argv = [python_pin['path'], '-B', writer_pin['path'], '--request', args.request,
        '--request-sha256', args.request_sha256, '--request-author-source', args.request_author_source,
        '--request-author-source-sha256', args.request_author_source_sha256,
        '--parent-review-sha256', args.parent_review_sha256, '--output-directory', args.output_directory]
    argv = [timeout_pin['path'], '--signal=TERM', '--kill-after=60s', str(outer_cap) + 's', *child_argv]
    previous = {sig:signal.getsignal(sig) for sig in SIGNALS}
    child = None; child_exit = None; state = 'not_launched'; received = None; failure = None
    cleanup_errors = []; cleanup = {'subreaper': False, 'terminated_owned_processes': [], 'survivors': {}}
    enabled = False; started = datetime.datetime.now(datetime.timezone.utc).isoformat(); clock_start = time.monotonic()
    def interrupt(number, _frame):raise Interruption(number)
    def child_log_limits():resource.setrlimit(resource.RLIMIT_FSIZE, (LOG_FILE_CAP, LOG_FILE_CAP))
    soft, hard = resource.getrlimit(resource.RLIMIT_FSIZE)
    require(hard == resource.RLIM_INFINITY or hard >= LOG_FILE_CAP, 'existing_hard_file_limit_cannot_cover_private_log_budget')
    # Original outputs are capped8MiB; the16MiB per-file infrastructure ceiling
    # only prevents runaway inherited diagnostics. Exceeding it is a failed run.
    start = {'format': FORMAT + '.start', 'started_utc': started, 'original_sealed': False,
        'writer_sha256': INDEX_WRITER, 'author_sha256': AUTHOR_SHA256, 'request_sha256': request_pin['sha256'],
        'parent_review_sha256': args.parent_review_sha256, 'argv_sha256': digest(argv),
        'original_six_writer_flags_preserved': True, 'writer_deadline_seconds': limits['metadata_deadline_seconds'],
        'GNU_timeout_seconds': outer_cap, 'GNU_kill_after_seconds': 60, 'private_log_file_cap_bytes': LOG_FILE_CAP,
        'capture_scope': 'All inherited stdout/stderr stay remote, unsealed and unmodified; overflow is failure, partial files retained.'}
    start_raw = (json.dumps(start, sort_keys=True, ensure_ascii=True, allow_nan=False) + '\n').encode()
    require(fresh_output(args.log_directory, (source, raw_root, *campaigns, writer_output)) == log_directory,
            'log_directory_no_longer_fresh')
    log_directory.mkdir(mode=0o700)
    require(private_path(log_directory, directory=True) == log_directory and stat.S_IMODE(log_directory.stat().st_mode) == 0o700,
            'exclusive_private_log_directory_required')
    start_pin = private_file(log_directory / 'start.json', start_raw, RECEIPT_CAP)
    out_fd = os.open(log_directory / 'stdout', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    err_fd = os.open(log_directory / 'stderr', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    for sig in SIGNALS:signal.signal(sig, interrupt)
    signal.setitimer(signal.ITIMER_REAL, 0)  # Child has its own exact GNU timeout; preflight timer cannot truncate it.
    try:
        enable_subreaper(); enabled = True
        environment = dict(os.environ)
        for name in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONINSPECT'):
            environment.pop(name, None)
        environment['PYTHONDONTWRITEBYTECODE'] = '1'
        with os.fdopen(out_fd, 'wb') as out, os.fdopen(err_fd, 'wb') as err:
            child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                start_new_session=True, close_fds=True, preexec_fn=child_log_limits, env=environment)
            state = 'running'
            try:
                child_exit = child.wait(timeout=outer_cap + 65)
                state = 'writer_returned' if child_exit == 0 else 'writer_or_timeout_failed'
            except subprocess.TimeoutExpired as error:
                state = 'supervisor_wait_expired'; failure = (type(error).__name__, sha(str(error).encode()))
    except Interruption as error:
        received = signal.Signals(error.number).name; state = 'external_signal'
        failure = (type(error).__name__, sha(str(error.number).encode()))
    except BaseException as error:
        state = 'envelope_error'; failure = (type(error).__name__, sha(str(error).encode(errors='replace')))
    finally:
        for sig in SIGNALS:signal.signal(sig, signal.SIG_IGN)
        if enabled:
            try:stop_group(child, grace_seconds=15)
            except BaseException as error:cleanup_errors.append(type(error).__name__)
            try:cleanup = cleanup_owned()
            except BaseException as error:cleanup_errors.append(type(error).__name__)
        if child is not None and child.returncode is not None:child_exit = child.returncode
        if cleanup_errors or cleanup.get('survivors') or enabled and cleanup.get('subreaper') is not True:
            state = 'cleanup_failed'
    postflight = time.monotonic() + 60
    signal.setitimer(signal.ITIMER_REAL, 60)
    try:
        recheck_originals(postflight)
        require(len(bundle_pins(source, postflight)) == 185, 'source_F6_after_child_required')
        executable_pin(python_pin['path'], python_pin['sha256'], postflight)
        executable_pin(timeout_pin['path'], timeout_pin['sha256'], postflight)
        private_path(log_directory, directory=True)
        private_path(source, directory=True); private_path(raw_root, directory=True)
        for path in campaigns:
            require(all(not part.is_symlink() for part in (path, *path.parents)), 'final_campaign_redirect_refused')
            if path.exists():private_path(path, directory=True)
        private_path(writer_output.parent, directory=True)
        if writer_output.exists():
            require(private_path(writer_output, directory=True) == writer_output, 'final_writer_output_redirect_refused')
        require(all(not log_directory.is_relative_to(p) for p in (source, raw_root, *campaigns, writer_output)) and
                not writer_output.is_relative_to(log_directory), 'final_log_writer_output_separation_required')
    except BaseException as error:
        state = 'immutable_or_path_recheck_failed'; failure = (type(error).__name__, sha(str(error).encode(errors='replace')))
    output_pins = {name:stream_pin(log_directory / name, LOG_FILE_CAP if name in {'stdout', 'stderr'} else RECEIPT_CAP,
                                 postflight) for name in ('start.json', 'stdout', 'stderr')}
    if any(output_pins[n]['bytes'] >= LOG_FILE_CAP for n in ('stdout', 'stderr')):state = 'private_log_budget_reached'
    code = 0 if state == 'writer_returned' and child_exit == 0 and not cleanup_errors and not cleanup.get('survivors') else 1
    receipt = {'format': FORMAT, 'canonical_ensure_ascii': True, 'started_utc': started,
        'ended_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'elapsed_envelope_seconds': time.monotonic()-clock_start,
        'state': state, 'envelope_exit': code, 'captured_timeout_tool_exit': child_exit, 'signal_received': received,
        'failure_class': None if failure is None else failure[0], 'failure_message_sha256': None if failure is None else failure[1],
        'writer_source_pin': writer_pin, 'author_source_pin': author_pin, 'request_pin': request_pin,
        'manifest_M2_pin': dict(m2pin, identity_sha256=m2['identity_sha256']), 'envelope_source_pin': own_pin,
        'cleanup_helper_source_pin': cleanup_pin, 'processes_source_pin': process_pin,
        'python_executable_pin': python_pin, 'GNU_timeout_executable_pin': timeout_pin,
        'GNU_timeout_family_basis': 'Explicit actual parent review plus exact executable hash, not guessed version',
        'argv_sha256': digest(argv), 'writer_six_flag_argv_sha256': digest(child_argv[3:]),
        'source_C': C, 'F6': F6, 'module_count':185, 'final_R':ctx['final_R'],
        'original_writer_limits':limits, 'writer_output_directory':str(writer_output), 'log_directory':str(log_directory),
        'GNU_timeout_seconds':outer_cap, 'GNU_kill_after_seconds':60, 'supervisor_wait_seconds':outer_cap+65,
        'private_log_file_cap_bytes':LOG_FILE_CAP, 'log_pins':output_pins,
        'cleanup':{'subreaper':enabled, 'terminated_owned_process_count':len(cleanup.get('terminated_owned_processes', [])),
            'survivor_count':len(cleanup.get('survivors', {})), 'error_classes':cleanup_errors},
        'raw_stdout_stderr_or_original_diagnostics_transferred':False, 'partial_failure_data_preserved':True,
        'independent_validation_or_campaign_admission':False,
        'scope':'Original writer execution/metadata infrastructure and privacy only. Parent-reviewed snapshot facts are unchanged request inputs, not independently observed by this envelope. All actual original stdout/stderr remain private remote unsealed originals.'}
    receipt['identity_sha256'] = digest(receipt)
    receipt_raw = (json.dumps(receipt, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()
    receipt_pin = private_file(log_directory / 'receipt.json', receipt_raw, RECEIPT_CAP)
    returned_bytes(receipt_pin, RECEIPT_CAP, postflight)
    recheck_originals(postflight)
    executable_pin(python_pin['path'], python_pin['sha256'], postflight)
    executable_pin(timeout_pin['path'], timeout_pin['sha256'], postflight)
    require(len(bundle_pins(source, postflight)) == 185, 'final_source_F6_inventory_required')
    returned_bytes(own_pin, MAX_METADATA, postflight)
    signal.setitimer(signal.ITIMER_REAL, 0)
    for sig, handler in previous.items():signal.signal(sig, handler)
    bounded_print({'format':FORMAT, 'receipt_pin':receipt_pin, 'receipt_identity_sha256':receipt['identity_sha256'],
        'state':state, 'envelope_exit':code, 'failure_class':receipt['failure_class'],
        'failure_message_sha256':receipt['failure_message_sha256'], 'raw_diagnostics_returned':False})
    return code


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL, 0)
        # Includes parser/context/source/OS failures; never expose original text.
        raw = json.dumps({'format':FORMAT+'.refusal', 'state':'refused',
            'failure_class':type(error).__name__, 'failure_message_sha256':sha(str(error).encode(errors='replace')),
            'raw_diagnostics_returned':False}, ensure_ascii=True, allow_nan=False).encode()
        if len(raw) <= RECEIPT_CAP:print(raw.decode('ascii'), file=sys.stderr)
        sys.exit(3)

