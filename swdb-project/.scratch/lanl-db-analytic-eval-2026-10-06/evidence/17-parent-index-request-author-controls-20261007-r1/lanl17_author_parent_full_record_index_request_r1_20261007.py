#!/usr/bin/env python3
"""PROSPECTIVE parent author of ONE exact7a full-record-index request; NOT RUN.

This fills the separately audited request-author seam, not original28d output.
The parent must supply the COMPLETE sorted real one-catalog inventory and exact
original eight pins, plus honest prior-validation continuity/quiescence review.
There is no default actual input, approval, normal trajectory or outcome.
Future main passively rechecks returned original bytes/stats, full source C/F6,
M2 routing and an explicitly approved unsealed request payload. No Store/public
validation/index writer/campaign/provider/native/collector/auditor/SSH runs.
It emits only an original UNSEALED request and separately sealed author custody.
128MiB/file,2GiB unique ONE-catalog,16384 records,8MiB metadata,60..3600 seconds
are original7a bounds; no selected input or scientific budget is enlarged.
R1 deliberately captures Git stderr for privacy; all other copied helpers
retain exact original7a source AST/text and loader policy.
"""
import argparse

import datetime

import hashlib

import json

import math

import os

from pathlib import Path, PurePosixPath

import pwd

import re

import signal

import socket

import stat

import subprocess

import sys

import time

import yaml

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

def token(value):
    require(isinstance(value, str) and len(value) <= 256 and
            re.fullmatch('[A-Za-z0-9_.:/+-]+', value), 'bounded_public_token_required')
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

class RecordLoader(getattr(yaml, 'CSafeLoader', yaml.SafeLoader)):
    pass

RecordLoader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in rows if tag != 'tag:yaml.org,2002:timestamp']
    for first, rows in RecordLoader.yaml_implicit_resolvers.items()
}

def no_duplicates(loader, node, deep=False):
    # Exact C/6a key-duplication and timestamp-as-string policy; no module import.
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise Refused('duplicate_yaml_mapping_key')
        seen.add(key)
    return loader.construct_mapping(node, deep=deep)

RecordLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, no_duplicates)

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

def index_record(index, raw):
    value = yaml.load(raw, Loader=RecordLoader)
    require(isinstance(value, dict), 'record_body_must_be_mapping')
    plain_record(value)
    rid, kind = token(value['id']), token(value['kind'])
    require(rid not in index, 'duplicate_record_id')
    index[rid] = {'kind': kind, 'sha256': sha(raw), 'record_sha256': digest(value)}
    return value

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

def scan_catalog(root, deadline):
    # Exact public access.record_files eligible paths; symlink redirects refuse.
    root = checked_path(root, directory=True)
    result = {}
    for base, directories, filenames in os.walk(root, followlinks=False):
        remaining(deadline)
        base = checked_path(base, directory=True)
        for name in directories:
            require(not (base / name).is_symlink(), 'catalog_symlink_directory_refused')
        directories[:] = sorted(name for name in directories if not name.startswith('.'))
        for name in sorted(filenames):
            path = base / name
            require(not path.is_symlink(), 'catalog_symlink_file_refused')
            rel = path.relative_to(root).as_posix()
            if path.suffix in {'.yaml', '.yml'} and not any(part.startswith('.') for part in PurePosixPath(rel).parts):
                path = checked_path(path)
                result[record_relative(rel)] = stamp(path.stat())
                require(len(result) <= MAX_RECORDS, 'catalog_record_count_limit_exceeded')
    return dict(sorted(result.items()))

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

def require_inventory_equal(expected, actual):
    require(set(expected) == set(actual), 'full_catalog_inventory_path_set_changed')
    require(all(expected[rel]['stat'] == actual[rel] for rel in expected),
            'full_catalog_inventory_inode_or_stat_changed')

def build_index(root, inventory, deadline):
    require_inventory_equal(inventory, scan_catalog(root, deadline))
    index = {}
    for rel, row in inventory.items():
        raw, _ = returned_bytes({'path': str(root / rel), 'bytes': row['bytes'], 'sha256': row['sha256']},
                                MAX_CATALOG_FILE, deadline, row['stat'])
        index_record(index, raw)
        remaining(deadline)
    require_inventory_equal(inventory, scan_catalog(root, deadline))
    return dict(sorted(index.items()))

def recheck_catalog(root, inventory, deadline):
    # Rehash returned bodies as well as re-inventory; a same-size rewrite refuses.
    require_inventory_equal(inventory, scan_catalog(root, deadline))
    for rel, row in inventory.items():
        returned_bytes({'path': str(root / rel), 'bytes': row['bytes'], 'sha256': row['sha256']},
                       MAX_CATALOG_FILE, deadline, row['stat'])
    require_inventory_equal(inventory, scan_catalog(root, deadline))

def recheck_originals(pins, deadline):
    for pin in pins:
        returned_bytes(pin, MAX_METADATA, deadline)

def git(source, deadline, *args):
    # Fixed local read-only commands only. No lazy fetch, credential prompts,
    # filters, source imports, SQLite or scientific/public validator execution.
    environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    environment.update(GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0',
                       GIT_OPTIONAL_LOCKS='0', GIT_PAGER='cat')
    return subprocess.check_output(['git', '-c', 'protocol.allow=never', '-c', 'core.fsmonitor=false',
                                    '-C', str(source), *args],
                                   timeout=min(60, remaining(deadline)), env=environment, stderr=subprocess.PIPE)

def scientific_source(source, revision, tree, deadline):
    source = checked_path(source, directory=True)
    full_hash(revision, 40)
    full_hash(tree, 40)
    require(git(source, deadline, 'rev-parse', '--show-toplevel').decode().strip() == str(source) and
            git(source, deadline, 'rev-parse', 'HEAD').decode().strip() == revision and
            not git(source, deadline, 'status', '--porcelain').strip(), 'exact_clean_actual_R_required')
    require(git(source, deadline, 'rev-parse', revision + '^{tree}').decode().strip() == tree,
            'actual_R_tree_differs')
    git(source, deadline, 'merge-base', '--is-ancestor', C, revision)
    def modules(ref):
        rows = {}
        for line in git(source, deadline, 'ls-tree', '-r', '-z', ref, 'swdb-project/swdb').split(b'\0'):
            if not line:
                continue
            meta, raw_path = line.split(b'\t', 1)
            path = raw_path.decode()
            if path.endswith('.py'):
                require(meta.split()[:2] in ([b'100644', b'blob'], [b'100755', b'blob']),
                        'scientific_module_regular_git_blob_required')
                rows[path] = meta
        return rows
    original, current = modules(C), modules(revision)
    require(len(original) == 185 and current == original, 'actual_R_not_exact_185_C_modules')
    module_root = checked_path(source / 'swdb-project/swdb', directory=True)
    live_paths = set()
    for path in module_root.rglob('*'):
        require(not path.is_symlink(), 'scientific_module_symlink_refused')
        if path.suffix == '.py':
            checked_path(path)
            live_paths.add(path.relative_to(source).as_posix())
    require(live_paths == set(current), 'actual_live_module_inventory_differs_including_ignored_files')
    hashes = {}
    for path in sorted(current):
        original_raw = git(source, deadline, 'cat-file', 'blob', C + ':' + path)
        current_path = checked_path(source / path)
        raw, _ = returned_bytes({'path': str(current_path), 'bytes': len(original_raw), 'sha256': sha(original_raw)},
                                MAX_METADATA, deadline)
        hashes[path[len('swdb-project/swdb/'):]] = sha(raw)
    require(digest(hashes) == F6, 'actual_live_185_module_F6_differs')
    return {'commit': revision, 'tree': tree, 'source_C': C, 'estimator_sha256': F6,
            'module_count': 185, 'source_clean': True}

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

def validation_originals(raw_root, campaign, folder, originals, deadline):
    result, pins = {}, []
    names = {'validation_argv': ('argv.json', 'json'), 'validation_exit': ('exit-code.txt', 'text'),
             'validation_stdout': ('stdout', 'bytes'), 'validation_stderr': ('stderr', 'bytes')}
    for role, (suffix, encoding) in names.items():
        pin = file_pin(originals[role])
        require(Path(pin['path']) == raw_root / ('validate-' + campaign + '.' + suffix),
                'original_28d_per_campaign_validation_path_differs')
        raw, _ = returned_bytes(pin, MAX_METADATA, deadline)
        pins.append(pin)
        result[role] = strict_json(raw) if encoding == 'json' else raw
    require(result['validation_argv'] == ['python3', '-m', 'swdb', 'validate', '--records', str(folder)],
            'original_full_campaign_validation_argv_differs')
    require(result['validation_exit'].strip() == b'0', 'original_prior_full_validation_not_exit_zero')
    match = re.fullmatch(rb'OK: ([0-9]+) record\(s\) valid\s*', result['validation_stdout'])
    require(match is not None and result['validation_stderr'] == b'', 'original_prior_full_validation_success_text_differs')
    return int(match.group(1)), pins

def summary_check(binding, inventory, index, folder, campaign, revision, deadline):
    require(isinstance(binding, dict) and binding.get('state') in {'present', 'absent'},
            'explicit_original_summary_presence_required')
    rid = campaign + '.summary'
    if binding['state'] == 'absent':
        exact(binding, ('state', 'id', 'parent_observed_absence'), 'exact_summary_absence_binding_required')
        require(binding['id'] == rid and binding['parent_observed_absence'] is True and rid not in index,
                'original_summary_absence_differs')
        return None
    exact(binding, ('state', 'path', 'id', 'record_sha256'), 'exact_original_summary_binding_required')
    rel = record_relative(binding['path'])
    require(rel in inventory and binding['id'] == rid and rid in index and
            index[rid]['kind'] == 'campaign_summary' and
            index[rid]['record_sha256'] == full_hash(binding['record_sha256']), 'original_summary_index_binding_differs')
    row = inventory[rel]
    raw, _ = returned_bytes({'path': str(folder / rel), 'bytes': row['bytes'], 'sha256': row['sha256']},
                           MAX_CATALOG_FILE, deadline, row['stat'])
    data = yaml.load(raw, Loader=RecordLoader)
    require(data['id'] == rid and data['kind'] == 'campaign_summary' and data['campaign'] == campaign and
            data['mode'] == 'extensa' and data['swdb_commit'] == revision and
            digest(data) == binding['record_sha256'] and sha(raw) == index[rid]['sha256'],
            'original_campaign_summary_source_or_file_differs')
    return {'path': str(folder / rel), 'bytes': len(raw), 'sha256': sha(raw),
            'id': rid, 'record_sha256': digest(data)}

INDEX_WRITER = '7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b'
INDEX_WRITER_BYTES = 33445
REQUEST_FORMAT = 'swdb.lanl17-parent-record-index-request.v1'
SPEC_FORMAT = 'swdb.lanl17-parent-record-index-request-author-spec.v1'
AUTHOR_CUSTODY_FORMAT = 'swdb.lanl17-parent-record-index-request-author-custody.v1'
VALIDATION_ROLES = ('validation_argv', 'validation_exit', 'validation_stdout', 'validation_stderr')


def author_plain(value, depth=0):
    require(depth <= 100, 'author_metadata_depth_exceeded')
    if isinstance(value, dict):
        require(all(isinstance(k, str) for k in value), 'author_metadata_nonstring_key')
        for child in value.values():
            author_plain(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            author_plain(child, depth + 1)
    else:
        require(value is None or type(value) in (str, int, bool) or
                type(value) is float and math.isfinite(value), 'author_metadata_nonfinite_or_unsupported')


def request_from_specification(spec):
    # Fixed format is schema vocabulary, not an observation/default approval.
    return {'format': REQUEST_FORMAT, 'context': spec['context'],
            'originals': spec['originals'], 'catalog_inventory': spec['catalog_inventory'],
            'summary_binding': spec['summary_binding'], 'limits': spec['limits'],
            'parent_review': spec['writer_parent_review'],
            'output_directory': spec['writer_output_directory']}


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


def write_private(path, raw, deadline):
    remaining(deadline)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        before = stamp(os.fstat(stream.fileno()))
        require(before['uid'] == os.getuid() and stat.S_ISREG(before['mode']) and
                stat.S_IMODE(before['mode']) == 0o600, 'fresh_private_author_file_required')
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    pin = {'path':str(path), 'bytes':len(raw), 'sha256':sha(raw)}
    returned_bytes(pin, MAX_METADATA, deadline)
    return pin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('specification', 'specification-sha256', 'parent-review-sha256',
                 'author-sha256', 'output-directory'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--metadata-deadline-seconds', required=True, type=int)
    args = parser.parse_args()
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10' and
            os.getuid() == os.geteuid() == 114316761 and
            pwd.getpwuid(os.getuid()).pw_name == 'yanruj', 'reviewed_actual_Linux_mbit10_UID_account_required')
    require(60 <= args.metadata_deadline_seconds <= MAX_DEADLINE, 'explicit_finite_author_metadata_deadline_required')
    deadline = time.monotonic() + args.metadata_deadline_seconds
    def expired(_signum, _frame):
        raise Refused('finite_author_metadata_deadline_exceeded')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, remaining(deadline))
    spec_path = checked_path(args.specification)
    spec_pin = file_pin({'path':str(spec_path), 'bytes':spec_path.stat().st_size,
                         'sha256':full_hash(args.specification_sha256)})
    spec_raw, _ = returned_bytes(spec_pin, MAX_METADATA, deadline)
    spec = strict_json(spec_raw)
    author_plain(spec)
    exact(spec, ('format', 'context', 'originals', 'catalog_inventory', 'summary_binding',
        'limits', 'writer_parent_review', 'writer_output_directory', 'controls',
        'author_review', 'output_directory'), 'exact_explicit_index_request_author_specification_required')
    require(spec['format'] == SPEC_FORMAT and spec['output_directory'] == args.output_directory,
            'reviewed_author_specification_format_or_output_differs')
    review = exact(spec['author_review'], ('basis', 'author_sha256',
        'reviewed_specification_payload_sha256', 'actual_inputs_parent_approved',
        'fixtures_or_replays_allowed', 'writer_parent_review_sha256', 'reviewed_utc'),
        'exact_parent_author_review_required')
    require(digest(review) == full_hash(args.parent_review_sha256) and
            review['author_sha256'] == full_hash(args.author_sha256) and
            review['basis'] == 'explicit_parent_review_of_real_one_catalog_index_request_and_original_snapshot_attestations' and
            review['actual_inputs_parent_approved'] is True and review['fixtures_or_replays_allowed'] is False and
            review['reviewed_specification_payload_sha256'] == digest({k:v for k,v in spec.items() if k != 'author_review'}),
            'explicit_parent_author_original_input_review_differs')
    own = checked_path(__file__)
    own_pin = file_pin({'path':str(own), 'bytes':own.stat().st_size, 'sha256':args.author_sha256})
    returned_bytes(own_pin, MAX_METADATA, deadline)
    pins = [spec_pin, own_pin]
    controls = exact(spec['controls'], ('index_writer',), 'only_original7a_index_writer_control_required')
    writer_pin = file_pin(controls['index_writer'])
    require(writer_pin['sha256'] == INDEX_WRITER and writer_pin['bytes'] == INDEX_WRITER_BYTES,
            'selected_original7a_index_writer_source_differs')
    returned_bytes(writer_pin, MAX_METADATA, deadline)
    pins.append(writer_pin)
    request = request_from_specification(spec)
    context = exact(request['context'], ('source_C', 'estimator_sha256', 'final_R', 'account', 'campaign',
        'source_path', 'project', 'records_directory', 'manifest_identity_sha256'), 'exact_original7a_context_required')
    require(context['source_C'] == C and context['estimator_sha256'] == F6, 'scientific_C_F6_differs')
    final_R = exact(context['final_R'], ('commit', 'tree'), 'explicit_parent_actual_R_commit_tree_required')
    full_hash(final_R['commit'],40); full_hash(final_R['tree'],40)
    account = exact(context['account'], ('host','platform','uid','user'), 'explicit_parent_actual_account_required')
    require(account == {'host':'mbit10','platform':'linux','uid':114316761,'user':'yanruj'},
            'explicit_actual_account_differs')
    campaign = context['campaign']
    require(campaign in CIDS, 'exact_one_original_named_campaign_required')
    limits = exact(request['limits'], ('catalog_record_count', 'catalog_total_bytes', 'max_catalog_file_bytes',
        'max_catalog_total_bytes', 'max_output_metadata_bytes', 'metadata_deadline_seconds'), 'exact_original7a_limits_required')
    require(type(limits['max_catalog_file_bytes']) is int and limits['max_catalog_file_bytes'] == MAX_CATALOG_FILE and
            type(limits['max_catalog_total_bytes']) is int and limits['max_catalog_total_bytes'] == MAX_CATALOG_TOTAL and
            type(limits['max_output_metadata_bytes']) is int and limits['max_output_metadata_bytes'] == MAX_METADATA and
            type(limits['metadata_deadline_seconds']) is int and
            60 <= limits['metadata_deadline_seconds'] <= MAX_DEADLINE, 'unchanged_original7a_explicit_limits_required')
    inventory = approved_inventory(request['catalog_inventory'], limits)
    writer_review, observations = check_writer_review(request)
    require(review['writer_parent_review_sha256'] == digest(writer_review), 'author_and_writer_parent_reviews_not_exactly_bound')
    reviewed_at = utc(review['reviewed_utc'])
    require(utc(observations['observed_utc']) <= reviewed_at <= datetime.datetime.now(datetime.timezone.utc),
            'actual_parent_author_review_chronology_differs')
    originals = exact(request['originals'], ('manifest_M2', 'helper_source', 'auditor_source', 'collector_source',
        'validation_argv', 'validation_exit', 'validation_stdout', 'validation_stderr'), 'exact_original7a_eight_original_pins_required')
    for role, expected in (('helper_source',HELPER), ('auditor_source',AUDITOR), ('collector_source',COLLECTOR)):
        pin = file_pin(originals[role])
        require(pin['sha256'] == expected, 'selected_original_control_source_differs')
        returned_bytes(pin, MAX_METADATA, deadline)
        pins.append(pin)
    m2desc = exact(originals['manifest_M2'], ('path','bytes','sha256','identity_sha256','canonical_ensure_ascii'),
                   'exact_original7a_M2_descriptor_required')
    require(m2desc['canonical_ensure_ascii'] is True, 'original28d_M2_canonical_policy_differs')
    m2pin = file_pin({k:m2desc[k] for k in ('path','bytes','sha256')})
    m2raw, _ = returned_bytes(m2pin, MAX_METADATA, deadline)
    m2 = original_seal(m2raw, m2desc['identity_sha256'])
    pins.append(m2pin)
    source = checked_path(context['source_path'], directory=True)
    require(source.is_relative_to(Path('/data1/yanruj')) and
            checked_path(context['project'], directory=True) == source/'swdb-project',
            'exact_owned_actual_M2_source_project_required')
    require(m2['format'] == 'swdb.lanl17-parent-population.v1' and
            m2['identity_sha256'] == context['manifest_identity_sha256'] and m2['source'] == str(source) and
            m2['source_commit'] == final_R['commit'] and m2['estimator_sha256'] == F6 and
            m2['helper_sha256'] == HELPER and m2['source_clean'] is True, 'original_M2_source_C_F6_R_binding_differs')
    raw_root = checked_path(m2['raw'], directory=True)
    require(raw_root.is_relative_to(Path('/data/yanruj')) and Path(m2pin['path']) == raw_root/'manifest.json',
            'canonical_original28d_M2_raw_and_manifest_path_required')
    folders = tuple(raw_root/'campaign-runs'/'extensa'/cid for cid in CIDS)
    for folder in folders:
        require(all(not p.is_symlink() for p in (folder,*folder.parents)), 'original_campaign_path_redirect_refused')
        if folder.exists():
            checked_path(folder,directory=True)
    records = checked_path(context['records_directory'], directory=True)
    require(context['records_directory'] == str(records), 'exact_canonical_records_directory_string_required')
    require(records == folders[CIDS.index(campaign)]/'records', 'exact_original28d_one_catalog_routing_required')
    forbidden=(source,raw_root,*folders)
    output = fresh_output(args.output_directory,forbidden)
    writer_output=fresh_output(request['output_directory'],forbidden)
    require(not output.is_relative_to(writer_output) and not writer_output.is_relative_to(output),
            'fresh_author_and_future_writer_outputs_must_be_disjoint')
    source_identity=scientific_source(source,final_R['commit'],final_R['tree'],deadline)
    validated_count,validation_pins=validation_originals(raw_root,campaign,records,originals,deadline)
    pins.extend(validation_pins)
    require(validated_count == len(inventory), 'original_full_validation_count_and_reviewed_one_catalog_inventory_differ')
    # Full byte/index checks confirm current metadata; unchanged prior validation,
    # process stoppage and exclusive ownership remain explicit inherited review.
    current_index=build_index(records,inventory,deadline)
    summary=summary_check(request['summary_binding'],inventory,current_index,records,campaign,final_R['commit'],deadline)
    require(len(current_index) == len(inventory), 'exact_current_catalog_ID_and_path_counts_differ')
    request_raw=(json.dumps(request,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
    require(len(request_raw) <= MAX_METADATA and 'identity_sha256' not in request,
            'unchanged_original7a_unsealed_request_metadata_bound_exceeded')
    request_pin={'path':str(output/'index-request.json'),'bytes':len(request_raw),'sha256':sha(request_raw)}
    custody={'format':AUTHOR_CUSTODY_FORMAT,'canonical_ensure_ascii':True,
        'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'state':'parent_authored_unsealed_index_request_with_inherited_snapshot_review',
        'actual_campaign_admission':False,'request_sealed':False,'bare_index_file_published_or_index_writer_executed':False,
        'original_unsealed_specification_pin':spec_pin,'author_source_pin':own_pin,
        'author_parent_review_sha256':digest(review),'original_index_writer_source_pin':writer_pin,
        'writer_parent_review_sha256':digest(writer_review),
        'original_context':context,'original_eight_pins':originals,
        'source_identity':source_identity,'catalog_inventory_sha256':digest(request['catalog_inventory']),
        'catalog_record_count':len(inventory),'unique_one_catalog_source_bytes':limits['catalog_total_bytes'],
        'current_index_check_sha256':digest(current_index),'original_summary_binding':request['summary_binding'],
        'original_summary_pin':summary,'inherited_parent_validated_snapshot':observations,
        'validation_boundary':'Original28d full validation and unchanged/exclusive/quiescent continuity are explicit parent review, not independently rerun or observed by this author. Current bytes/inventory/identity checks do not create that history.',
        'limits':limits,'author_metadata_deadline_seconds':args.metadata_deadline_seconds,
        'source_read_bound_scope':'128MiB per body and2GiB unique bytes for exactly ONE catalog; final rechecks reread originals. No cumulative-I/O or runtime promise.',
        'output_exclusion_roots':[str(p) for p in forbidden],
        'request_file_pin':request_pin,'unsealed_request_payload_sha256':digest(request),
        'original_input_or_control_rewritten':False,'old_selected_or_scientific_bounds_changed':False,
        'Store_validate_index_writer_collector_auditor_native_provider_campaign_remote_actions':0}
    custody['identity_sha256']=digest(custody)
    custody_raw=(json.dumps(custody,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
    require(len(custody_raw) <= MAX_METADATA, 'unchanged_bounded_author_custody_metadata_required')
    def final_checks():
        recheck_catalog(records,inventory,deadline)
        recheck_originals(pins,deadline)
        require(scientific_source(source,final_R['commit'],final_R['tree'],deadline) == source_identity,
                'actual_source_C_F6_R_changed_before_author_success')
        require_inventory_equal(inventory,scan_catalog(records,deadline))
        recheck_originals(pins,deadline)
        require(fresh_output(request['output_directory'],forbidden) == writer_output,
                'future_writer_output_no_longer_fresh_or_redirected')
        returned_bytes(own_pin,MAX_METADATA,deadline)
        remaining(deadline)
    final_checks()
    require(fresh_output(args.output_directory,forbidden) == output, 'author_output_no_longer_fresh_or_redirected')
    output.mkdir(mode=0o700)
    require(checked_path(output,directory=True) == output and stat.S_IMODE(output.stat().st_mode) == 0o700,
            'fresh_private_author_output_directory_required')
    write_private(output/'index-request.json',request_raw,deadline)
    custody_pin=write_private(output/'author-custody.json',custody_raw,deadline)
    final_checks()
    returned_bytes(request_pin,MAX_METADATA,deadline)
    returned_bytes(custody_pin,MAX_METADATA,deadline)
    # These are last after output verification; no source/main calls occur next.
    recheck_originals(pins,deadline)
    returned_bytes(own_pin,MAX_METADATA,deadline)
    remaining(deadline)
    signal.setitimer(signal.ITIMER_REAL,0)
    print(json.dumps({'format':AUTHOR_CUSTODY_FORMAT,'request_file_pin':request_pin,
        'writer_parent_review_sha256':digest(writer_review),'request_author_source_pin':own_pin,
        'author_custody':dict(custody_pin,identity_sha256=custody['identity_sha256'],canonical_ensure_ascii=True),
        'request_sealed':False,'index_writer_executed':False,'actual_campaign_admission':False},
        ensure_ascii=True,allow_nan=False))


if __name__ == '__main__':
    try:
        main()
    except (Refused,KeyError,TypeError,ValueError,RecursionError,OSError,yaml.YAMLError,
            subprocess.SubprocessError) as error:
        # Preserve partial output. No parser/log/environment/command text leaks.
        print(json.dumps({'format':'swdb.lanl17-parent-index-request-author-refusal.v1',
            'exception_class':type(error).__name__,
            'exception_message_sha256':sha(str(error).encode(errors='replace')),
            'original_parser_or_command_or_environment_text_transferred':False,
            'actual_campaign_admission':False},ensure_ascii=True,allow_nan=False),file=sys.stderr)
        sys.exit(3)
