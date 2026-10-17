#!/usr/bin/env python3
"""PROSPECTIVE passive ONE-catalog inventory/present-summary reader; NOT RUN.

Source-only preparation, 2026-10-07 ET. Future execution reads current public
record bytes and exactly ONE selected summary identity. It never invokes Store,
public validation, an index writer, campaign, provider, native/compiler work,
collector, auditor, SSH or Git mutation. Historical validation continuity,
quiescence/exclusivity and normal/substantive completion are NOT observed here.
Original7a128MiB/file,2GiB unique ONE inventory,16k records,8MiB metadata bounds
remain unchanged. One new UNSEALED metadata file is neither a request nor an
admission. Present-summary mode requires its explicit path. The other explicit
mode leaves summary binding unresolved; no parent absence flag is invented.
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

def require_inventory_equal(expected, actual):
    require(set(expected) == set(actual), 'full_catalog_inventory_path_set_changed')
    require(all(expected[rel]['stat'] == actual[rel] for rel in expected),
            'full_catalog_inventory_inode_or_stat_changed')

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
                                   timeout=min(60, remaining(deadline)), env=environment, stderr=subprocess.DEVNULL)

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

sys.dont_write_bytecode = True
INDEX_WRITER = '7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b'
INDEX_WRITER_BYTES = 33445
OUTPUT_FORMAT = 'swdb.lanl17-passive-one-catalog-inventory.v1'
FORBIDDEN_NAMES = {'.codex', '.ssh', '.aws', 'auth.json', 'provider.json', 'prompt.txt', 'feedback.txt'}


def privacy_path(text, directory=False):
    path = checked_path(text, directory=directory)
    require(not FORBIDDEN_NAMES.intersection(path.parts), 'private_credential_provider_prompt_path_refused')
    return path


def observe_inventory_row(root, rel, expected_stamp, deadline):
    """Derive current file SHA/stat only; parse no original record body."""
    record_relative(rel)
    exact(expected_stamp, STAMP_KEYS, 'exact_observed_stat7_required')
    require(all(type(v) is int and v >= 0 for v in expected_stamp.values()), 'nonnegative_observed_stat7_required')
    size = expected_stamp['size']
    require(0 <= size <= MAX_CATALOG_FILE, 'unchanged_128MiB_per_catalog_body_bound_exceeded')
    path = privacy_path(root / rel)
    require(path.is_relative_to(root), 'observed_record_leaves_exact_one_catalog')
    remaining(deadline)
    with path.open('rb') as stream:
        before = stamp(os.fstat(stream.fileno()))
        require(before == expected_stamp and stat.S_ISREG(before['mode']) and before['uid'] == os.getuid(),
                'observed_catalog_fd_inode_stat_UID_differs')
        hasher, returned = hashlib.sha256(), 0
        while True:
            remaining(deadline)
            block = stream.read(min(1024 * 1024, size + 1 - returned))
            if not block:
                break
            returned += len(block)
            require(returned <= size, 'observed_catalog_returned_size_differs')
            hasher.update(block)
        after = stamp(os.fstat(stream.fileno()))
    require(returned == size and before == after == stamp(privacy_path(path).stat()),
            'observed_catalog_replaced_or_changed_during_hash')
    remaining(deadline)
    return {'path': rel, 'bytes': returned, 'sha256': hasher.hexdigest(), 'stat': dict(before)}


def observe_one_inventory(root, deadline):
    scanned = scan_catalog(root, deadline)
    require(0 < len(scanned) <= MAX_RECORDS, 'bounded_nonempty_one_catalog_inventory_required')
    total = 0
    for current in scanned.values():
        require(type(current['size']) is int and 0 <= current['size'] <= MAX_CATALOG_FILE,
                'unchanged_128MiB_per_catalog_body_bound_exceeded')
        total += current['size']
        require(total <= MAX_CATALOG_TOTAL, 'unchanged_2GiB_unique_one_catalog_bound_exceeded')
    inventory = {rel: observe_inventory_row(root, rel, current, deadline)
                 for rel, current in scanned.items()}
    require_inventory_equal(inventory, scan_catalog(root, deadline))
    return inventory, total


def observe_present_summary(root, rel, inventory, campaign, revision, deadline):
    """Only explicit selected summary YAML is parsed, under original7a policy."""
    record_relative(rel)
    require(rel in inventory, 'explicit_present_summary_path_missing_from_inventory')
    row = inventory[rel]
    raw, _ = returned_bytes({'path': str(root / rel), 'bytes': row['bytes'], 'sha256': row['sha256']},
                            MAX_CATALOG_FILE, deadline, row['stat'])
    data = yaml.load(raw, Loader=RecordLoader)
    require(isinstance(data, dict), 'selected_original_summary_must_be_mapping')
    plain_record(data)
    rid = campaign + '.summary'
    require(data['id'] == rid and data['kind'] == 'campaign_summary' and data['campaign'] == campaign and
            data['mode'] == 'extensa' and data['swdb_commit'] == revision,
            'explicit_original_present_summary_identity_source_differs')
    remaining(deadline)
    binding = {'state': 'present', 'path': rel, 'id': rid, 'record_sha256': digest(data)}
    pin = {'path': str(root / rel), 'bytes': len(raw), 'sha256': sha(raw),
           'id': rid, 'kind': 'campaign_summary', 'record_sha256': binding['record_sha256']}
    return binding, pin


def write_metadata(path, raw, deadline):
    remaining(deadline)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        require(os.fstat(stream.fileno()).st_uid == os.getuid() and
                stat.S_IMODE(os.fstat(stream.fileno()).st_mode) == 0o600, 'private_exclusive_metadata_file_required')
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    pin = {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}
    returned_bytes(pin, MAX_METADATA, deadline)
    return pin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('manifest', 'manifest-sha256', 'manifest-identity-sha256', 'source-sha', 'source-tree',
                 'campaign', 'index-writer-source', 'index-writer-source-sha256',
                 'reader-sha256', 'account-user', 'output-directory'):
        parser.add_argument('--' + name, required=True)
    for name in ('manifest-bytes', 'account-uid', 'metadata-deadline-seconds', 'writer-metadata-deadline-seconds'):
        parser.add_argument('--' + name, required=True, type=int)
    parser.add_argument('--summary-selection', required=True, choices=('present', 'parent-binding-required'))
    parser.add_argument('--summary-relative-path')
    args = parser.parse_args()
    require((args.summary_selection == 'present' and isinstance(args.summary_relative_path, str) and
             bool(args.summary_relative_path)) or
            (args.summary_selection == 'parent-binding-required' and args.summary_relative_path is None),
            'explicit_present_summary_path_or_unresolved_parent_binding_required')
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10' and
            args.account_uid == os.getuid() == os.geteuid() == 114316761 and
            args.account_user == pwd.getpwuid(os.getuid()).pw_name == 'yanruj',
            'explicit_reviewed_actual_Linux_mbit10_account_required')
    require(args.campaign in CIDS, 'exact_one_original_campaign_required')
    require(60 <= args.metadata_deadline_seconds <= MAX_DEADLINE and
            60 <= args.writer_metadata_deadline_seconds <= MAX_DEADLINE, 'explicit_finite_metadata_allowances_required')
    deadline = time.monotonic() + args.metadata_deadline_seconds
    def expired(_signum, _frame):
        raise Refused('finite_passive_inventory_metadata_deadline_exceeded')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, remaining(deadline))
    started_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    own = privacy_path(__file__)
    own_pin = file_pin({'path': str(own), 'bytes': own.stat().st_size, 'sha256': full_hash(args.reader_sha256)})
    returned_bytes(own_pin, MAX_METADATA, deadline)
    writer = privacy_path(args.index_writer_source)
    writer_pin = file_pin({'path': str(writer), 'bytes': writer.stat().st_size,
                           'sha256': full_hash(args.index_writer_source_sha256)})
    require(writer_pin['sha256'] == INDEX_WRITER and writer_pin['bytes'] == INDEX_WRITER_BYTES,
            'unchanged_reviewed_original7a_source_pin_required')
    returned_bytes(writer_pin, MAX_METADATA, deadline)
    manifest_path = privacy_path(args.manifest)
    require(manifest_path.name == 'manifest.json' and manifest_path.is_relative_to(Path('/data/yanruj')),
            'original_public_M2_manifest_path_required_before_read')
    m2pin = file_pin({'path': str(manifest_path), 'bytes': args.manifest_bytes,
                     'sha256': full_hash(args.manifest_sha256)})
    m2raw, _ = returned_bytes(m2pin, MAX_METADATA, deadline)
    m2 = original_seal(m2raw, full_hash(args.manifest_identity_sha256))
    plain_record(m2)
    source = privacy_path(m2['source'], directory=True)
    full_hash(args.source_sha, 40); full_hash(args.source_tree, 40)
    require(source.is_relative_to(Path('/data1/yanruj')) and m2['format'] == 'swdb.lanl17-parent-population.v1' and
            m2['source'] == str(source) and m2['source_commit'] == args.source_sha and
            m2['helper_sha256'] == HELPER and m2['estimator_sha256'] == F6 and m2['source_clean'] is True,
            'exact_original_M2_R_C_F6_source_binding_required')
    raw_root = privacy_path(m2['raw'], directory=True)
    require(raw_root.is_relative_to(Path('/data/yanruj')) and manifest_path == raw_root / 'manifest.json',
            'original_M2_raw_manifest_binding_required')
    campaigns = tuple(raw_root / 'campaign-runs' / 'extensa' / cid for cid in CIDS)
    for folder in campaigns:
        require(all(not p.is_symlink() for p in (folder, *folder.parents)), 'original_campaign_path_redirect_refused')
        if folder.exists():
            privacy_path(folder, directory=True)
    records = privacy_path(campaigns[CIDS.index(args.campaign)] / 'records', directory=True)
    require(records == campaigns[CIDS.index(args.campaign)] / 'records', 'exact_original_one_catalog_path_required')
    project = privacy_path(source / 'swdb-project', directory=True)
    source_identity = scientific_source(source, args.source_sha, args.source_tree, deadline)
    forbidden = (source, raw_root, *campaigns)
    output = fresh_output(args.output_directory, forbidden)
    privacy_path(output.parent, directory=True)
    context = {'source_C': C, 'estimator_sha256': F6,
        'final_R': {'commit': args.source_sha, 'tree': args.source_tree},
        'account': {'host': 'mbit10', 'platform': 'linux', 'uid': args.account_uid, 'user': args.account_user},
        'campaign': args.campaign, 'source_path': str(source), 'project': str(project),
        'records_directory': str(records), 'manifest_identity_sha256': m2['identity_sha256']}
    inventory, total = observe_one_inventory(records, deadline)
    if args.summary_selection == 'present':
        summary_binding, summary_pin = observe_present_summary(records, args.summary_relative_path, inventory,
                                                               args.campaign, args.source_sha, deadline)
    else:
        summary_binding, summary_pin = None, None
    pins = [own_pin, writer_pin, m2pin]
    metadata = {'format': OUTPUT_FORMAT, 'metadata_is_unsealed': True,
        'read_started_utc': started_utc, 'current_facts_prepared_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'reader_source_pin': own_pin, 'original_index_writer_source_pin': writer_pin,
        'manifest_M2_pin': dict(m2pin, identity_sha256=m2['identity_sha256'], canonical_ensure_ascii=True),
        'context': context, 'source_identity': source_identity,
        'catalog_inventory': list(inventory.values()), 'catalog_inventory_sha256': digest(list(inventory.values())),
        'summary_binding': summary_binding, 'summary_original_pin': summary_pin,
        'summary_selection': args.summary_selection,
        'summary_descriptor': {'id': args.campaign + '.summary', 'binding_requires_parent_observation': summary_binding is None,
            'index_wide_ID_absence_checked': False, 'parent_observed_absence_attestation_generated': False},
        'limits': {'catalog_record_count': len(inventory), 'catalog_total_bytes': total,
            'max_catalog_file_bytes': MAX_CATALOG_FILE, 'max_catalog_total_bytes': MAX_CATALOG_TOTAL,
            'max_output_metadata_bytes': MAX_METADATA, 'metadata_deadline_seconds': args.writer_metadata_deadline_seconds},
        'passive_reader_metadata_deadline_seconds': args.metadata_deadline_seconds,
        'metadata_digest_policy': {'ensure_ascii': True, 'sort_keys': True, 'separators': [',', ':'], 'allow_nan': False},
        'summary_digest_policy': 'Exact original7a timestamp-as-string, duplicate-key refusal, finite plain values and full-record canonical-true digest',
        'output_exclusion_roots': [str(root) for root in forbidden],
        'not_observed_or_admitted': ['prior_full_catalogue_validation', 'unchanged_since_original_validation',
            'all_campaign_processes_stopped', 'exclusive_snapshot_ownership', 'all_record_ID_uniqueness',
            'summary_ID_absence', 'normal_or_substantive_campaign_completion', 'trajectory_or_D30_admission'],
        'reader_actions': {'public_validation': 0, 'Store': 0, 'index_writer': 0, 'collector': 0,
            'auditor': 0, 'campaign': 0, 'native_or_compiler': 0, 'provider': 0, 'remote_or_SSH': 0, 'Git_mutation': 0},
        'scope': 'Current passive file/stat/hash inventory for exactly ONE original M2-routed catalog, plus one explicitly selected present summary identity. No global snapshot continuity, process state, prior validation or scientific admission is inferred; original7a/author parent reviews remain required. Only an explicitly selected present summary YAML is parsed; parent-binding-required mode leaves its binding null and does not search body IDs or assert absence. Other bodies are hashed, never serialized.'}
    encoded = (json.dumps(metadata, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()
    require(len(encoded) <= MAX_METADATA and 'identity_sha256' not in metadata,
            'bounded_unsealed_inventory_metadata_required')
    def final_checks():
        recheck_catalog(records, inventory, deadline)
        recheck_originals(pins, deadline)
        require(scientific_source(source, args.source_sha, args.source_tree, deadline) == source_identity,
                'actual_R_C_F6_source_changed_during_passive_read')
        require_inventory_equal(inventory, scan_catalog(records, deadline))
        recheck_originals(pins, deadline)
        returned_bytes(own_pin, MAX_METADATA, deadline)
        remaining(deadline)
    final_checks()
    require(fresh_output(args.output_directory, forbidden) == output, 'passive_output_no_longer_fresh')
    privacy_path(output.parent, directory=True)
    output.mkdir(mode=0o700)
    require(privacy_path(output, directory=True) == output and stat.S_IMODE(output.stat().st_mode) == 0o700,
            'fresh_private_inventory_metadata_directory_required')
    metadata_pin = write_metadata(output / 'catalog-inventory.json', encoded, deadline)
    final_checks()
    returned_bytes(metadata_pin, MAX_METADATA, deadline)
    recheck_originals(pins, deadline)
    returned_bytes(own_pin, MAX_METADATA, deadline)
    remaining(deadline)
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps({'format': OUTPUT_FORMAT, 'unsealed_metadata_file_pin': metadata_pin,
        'metadata_payload_sha256': digest(metadata), 'reader_source_pin': own_pin,
        'catalog_record_count': len(inventory), 'summary_state': args.summary_selection,
        'index_writer_or_scientific_admission_executed': False}, ensure_ascii=True, allow_nan=False))


if __name__ == '__main__':
    try:
        main()
    except (Refused, KeyError, TypeError, ValueError, RecursionError, OSError, yaml.YAMLError,
            subprocess.SubprocessError) as error:
        print(json.dumps({'format': 'swdb.lanl17-passive-inventory-refusal.v1',
            'exception_class': type(error).__name__,
            'exception_message_sha256': sha(str(error).encode(errors='replace')),
            'original_parser_or_command_or_environment_text_transferred': False}, ensure_ascii=True), file=sys.stderr)
        sys.exit(3)

