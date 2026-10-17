#!/usr/bin/env python3
"""PROSPECTIVE parent-generated full record-index metadata writer; NOT RUN.

This distinct writer fills a metadata supplier gap. It does not impersonate an
original 28d output and never invokes Store, validate, SWDB, SQLite, a campaign,
provider, native experiment, collector, auditor, SSH or a selected reader.
Prior full validation and quiescence are inherited from explicit parent review
of original files and an exact real catalog inventory, not independently rerun.
The bare index is UNSEALED. Its rows contain exact source-byte SHA and the C/6a
whole-record canonical-true digest. A separate new custody receipt is sealed.
128 MiB/file and 2 GiB unique inventory bound ONLY this new catalog source read;
existing selected inputs and all scientific/selected controls remain unchanged.
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
REQUEST_FORMAT = 'swdb.lanl17-parent-record-index-request.v1'
CUSTODY_FORMAT = 'swdb.lanl17-parent-record-index-writer-custody.v1'
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
                                   timeout=min(60, remaining(deadline)), env=environment)


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


def publish(destination, index_raw, custody_raw, before_publication, after_publication):
    # Callbacks are exact original/catalog/source rechecks, not admission hooks.
    before_publication()
    require(not destination.exists() and not destination.is_symlink(), 'publication_output_no_longer_fresh')
    checked_path(destination.parent, directory=True)
    destination.mkdir(mode=0o700)
    require(checked_path(destination, directory=True) == destination, 'published_directory_redirect_refused')
    for name, raw in (('record-index.json', index_raw), ('writer-custody.json', custody_raw)):
        with (destination / name).open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        (destination / name).chmod(0o600)
        require(checked_path(destination / name).read_bytes() == raw, 'published_metadata_bytes_differ')
    after_publication()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('request', 'request-sha256', 'request-author-source', 'request-author-source-sha256',
                 'parent-review-sha256', 'output-directory'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    initial_deadline = time.monotonic() + 60
    request_path = checked_path(args.request)
    require(request_path.stat().st_size <= MAX_METADATA, 'original_request_metadata_bound_exceeded')
    request_pin = {'path': str(request_path), 'bytes': request_path.stat().st_size,
                   'sha256': full_hash(args.request_sha256)}
    request_raw, _ = returned_bytes(request_pin, MAX_METADATA, initial_deadline)
    request = strict_json(request_raw)
    exact(request, ('format', 'context', 'originals', 'catalog_inventory', 'summary_binding', 'limits',
                    'parent_review', 'output_directory'), 'exact_parent_index_request_required')
    require(request['format'] == REQUEST_FORMAT, 'parent_index_request_format_differs')
    limits = exact(request['limits'], ('catalog_record_count', 'catalog_total_bytes', 'max_catalog_file_bytes',
        'max_catalog_total_bytes', 'max_output_metadata_bytes', 'metadata_deadline_seconds'), 'explicit_exact_limits_required')
    require(limits['max_catalog_file_bytes'] == MAX_CATALOG_FILE and
            limits['max_catalog_total_bytes'] == MAX_CATALOG_TOTAL and
            limits['max_output_metadata_bytes'] == MAX_METADATA and
            type(limits['metadata_deadline_seconds']) is int and
            60 <= limits['metadata_deadline_seconds'] <= MAX_DEADLINE, 'distinct_explicit_source_and_metadata_bounds_required')
    deadline = time.monotonic() + limits['metadata_deadline_seconds']
    def expired(_signum, _frame):
        raise Refused('finite_metadata_deadline_exceeded')
    require(sys.platform == 'linux', 'actual_mbit10_Linux_required')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, remaining(deadline))
    context = exact(request['context'], ('source_C', 'estimator_sha256', 'final_R', 'account', 'campaign',
        'source_path', 'project', 'records_directory', 'manifest_identity_sha256'), 'exact_actual_context_required')
    require(context['source_C'] == C and context['estimator_sha256'] == F6, 'scientific_C_F6_differs')
    exact(context['final_R'], ('commit', 'tree'), 'explicit_actual_final_R_required')
    account = exact(context['account'], ('host', 'platform', 'uid', 'user'), 'explicit_actual_account_required')
    require(account['host'] == socket.gethostname().split('.')[0] == 'mbit10' and account['platform'] == 'linux' and
            type(account['uid']) is int and account['uid'] == os.getuid() == os.geteuid() and
            account['user'] == pwd.getpwuid(os.getuid()).pw_name == 'yanruj', 'actual_mbit10_UID_account_differs')
    campaign = context['campaign']
    require(campaign in CIDS, 'exact_original_named_campaign_required')
    source = checked_path(context['source_path'], directory=True)
    require(checked_path(context['project'], directory=True) == source / 'swdb-project', 'exact_original_M2_project_required')
    originals = exact(request['originals'], ('manifest_M2', 'helper_source', 'auditor_source', 'collector_source',
        'validation_argv', 'validation_exit', 'validation_stdout', 'validation_stderr'), 'exact_original_supplier_pins_required')
    pinned = []
    for role, expected in (('helper_source', HELPER), ('auditor_source', AUDITOR), ('collector_source', COLLECTOR)):
        pin = file_pin(originals[role])
        require(pin['sha256'] == expected, 'selected_original_control_source_differs')
        returned_bytes(pin, MAX_METADATA, deadline)
        pinned.append(pin)
    m2desc = exact(originals['manifest_M2'], ('path', 'bytes', 'sha256', 'identity_sha256', 'canonical_ensure_ascii'),
                   'explicit_original_M2_true_policy_pin_required')
    require(m2desc['canonical_ensure_ascii'] is True, 'original_helper28d_M2_policy_differs')
    m2pin = file_pin({key: m2desc[key] for key in ('path', 'bytes', 'sha256')})
    m2raw, _ = returned_bytes(m2pin, MAX_METADATA, deadline)
    m2 = original_seal(m2raw, m2desc['identity_sha256'])
    pinned.append(m2pin)
    require(m2['format'] == 'swdb.lanl17-parent-population.v1' and
            m2['identity_sha256'] == context['manifest_identity_sha256'] and m2['source'] == str(source) and
            m2['source_commit'] == context['final_R']['commit'] and m2['estimator_sha256'] == F6 and
            m2['helper_sha256'] == HELPER and m2['source_clean'] is True, 'actual_original_M2_source_differs')
    raw_root = checked_path(m2['raw'], directory=True)
    require(raw_root.is_relative_to(Path('/data/yanruj')), 'original_M2_raw_prefix_differs')
    folders = tuple(raw_root / 'campaign-runs' / 'extensa' / cid for cid in CIDS)
    for folder in folders:
        require(all(not part.is_symlink() for part in (folder, *folder.parents)), 'original_campaign_path_redirect_refused')
    records = checked_path(context['records_directory'], directory=True)
    require(records == folders[CIDS.index(campaign)] / 'records', 'exact_28d_campaign_catalog_routing_required')
    require(request['output_directory'] == args.output_directory, 'parent_reviewed_output_path_differs')
    output = fresh_output(args.output_directory, (source, raw_root, *folders))
    inventory = approved_inventory(request['catalog_inventory'], limits)
    review = exact(request['parent_review'], ('basis', 'writer_sha256', 'reviewed_request_payload_sha256',
        'actual_inputs_parent_approved', 'fixtures_or_replays_allowed', 'validated_snapshot'), 'explicit_parent_review_required')
    require(digest(review) == full_hash(args.parent_review_sha256) and
            review['basis'] == 'explicit_parent_review_of_real_quiescent_catalog_and_original_prior_full_validation' and
            review['actual_inputs_parent_approved'] is True and review['fixtures_or_replays_allowed'] is False and
            review['reviewed_request_payload_sha256'] == digest({key: value for key, value in request.items() if key != 'parent_review'}),
            'exact_parent_review_or_actual_request_boundary_differs')
    observed = exact(review['validated_snapshot'], ('campaign', 'records_directory', 'catalog_inventory_sha256',
        'validation_files_sha256', 'prior_validation_full_catalogue', 'catalog_unchanged_since_original_validation',
        'all_campaign_processes_stopped', 'exclusive_snapshot_ownership_confirmed', 'observed_utc'),
        'explicit_parent_snapshot_observations_required')
    require(observed['campaign'] == campaign and observed['records_directory'] == str(records) and
            observed['catalog_inventory_sha256'] == digest(request['catalog_inventory']) and
            observed['validation_files_sha256'] == {role: originals[role]['sha256'] for role in
                ('validation_argv', 'validation_exit', 'validation_stdout', 'validation_stderr')} and
            all(observed[key] is True for key in ('prior_validation_full_catalogue',
                'catalog_unchanged_since_original_validation', 'all_campaign_processes_stopped',
                'exclusive_snapshot_ownership_confirmed')), 'exact_parent_inherited_validation_snapshot_differs')
    utc(observed['observed_utc'])
    own = checked_path(__file__)
    own_pin = file_pin({'path': str(own), 'bytes': own.stat().st_size, 'sha256': full_hash(review['writer_sha256'])})
    returned_bytes(own_pin, MAX_METADATA, deadline)
    author = checked_path(args.request_author_source)
    author_pin = file_pin({'path': str(author), 'bytes': author.stat().st_size,
                          'sha256': full_hash(args.request_author_source_sha256)})
    returned_bytes(author_pin, MAX_METADATA, deadline)
    pinned.extend((request_pin, own_pin, author_pin))
    source_identity = scientific_source(source, context['final_R']['commit'], context['final_R']['tree'], deadline)
    validated_count, validation_pins = validation_originals(raw_root, campaign, records, originals, deadline)
    pinned.extend(validation_pins)
    require(validated_count == len(inventory), 'original_validation_count_and_current_approved_inventory_differ')
    index = build_index(records, inventory, deadline)
    summary = summary_check(request['summary_binding'], inventory, index, records, campaign,
                            context['final_R']['commit'], deadline)
    index_raw = (json.dumps(index, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False) + '\n').encode()
    require(len(index_raw) <= MAX_METADATA, 'unchanged_8MiB_selected_index_metadata_bound_exceeded')
    custody = {'format': CUSTODY_FORMAT, 'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'canonical_ensure_ascii': True, 'state': 'parent_generated_metadata_with_inherited_prior_validation',
        'actual_campaign_admission': False, 'index_is_original_28d_output': False, 'index_sealed': False,
        'writer_source_pin': own_pin, 'original_unsealed_request_pin': request_pin,
        'request_author_source_pin': author_pin, 'parent_review_sha256': digest(review),
        'source_identity': source_identity, 'account': account, 'campaign': campaign,
        'manifest_M2_pin': dict(m2desc), 'manifest_identity_sha256': m2['identity_sha256'],
        'original_selected_control_source_pins': {role: originals[role] for role in ('helper_source', 'auditor_source', 'collector_source')},
        'records_directory': str(records), 'catalog_record_count': len(index),
        'catalog_source_bytes': limits['catalog_total_bytes'], 'approved_catalog_inventory_sha256': digest(request['catalog_inventory']),
        'source_byte_limit_scope': 'Unique approved catalog bytes, not cumulative I/O; construction and two final custody passes reread the unchanged originals.',
        'original_catalog_inventory': request['catalog_inventory'], 'original_summary_binding': request['summary_binding'],
        'original_summary_pin': summary, 'original_28d_per_campaign_validation_pins': validation_pins,
        'inherited_parent_validated_snapshot': observed,
        'validation_boundary': 'Original public full-validation exit/stdout/stderr and unchanged/exclusive snapshot are parent-reviewed inherited facts. This writer performs byte/index checks, not full schema/rule/reference validation or independent process/lease observation.',
        'limits': limits, 'new_unsealed_index_pin': {'path': str(output / 'record-index.json'), 'bytes': len(index_raw),
            'sha256': sha(index_raw), 'record_index_sha256': digest(index)},
        'whole_record_digest_policy': {'ensure_ascii': True, 'sort_keys': True, 'separators': [',', ':'], 'allow_nan': False,
            'timestamps': 'original_public_string_dates', 'duplicate_mapping_keys': 'refused'},
        'catalog_original_bytes_rewritten': False, 'existing_selected_or_scientific_bounds_changed': False,
        'SWDB_Store_validate_native_provider_campaign_collector_auditor_remote_actions': 0}
    custody['identity_sha256'] = digest(custody)
    custody_raw = (json.dumps(custody, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()
    require(len(custody_raw) <= MAX_METADATA, 'new_metadata_custody_bound_exceeded')
    def final_checks():
        recheck_catalog(records, inventory, deadline)
        recheck_originals(pinned, deadline)
        require(scientific_source(source, context['final_R']['commit'], context['final_R']['tree'], deadline) == source_identity,
                'actual_source_identity_changed_before_success')
        require_inventory_equal(inventory, scan_catalog(records, deadline))
        # Own source and all originals are checked last, before publishing/success.
        recheck_originals(pinned, deadline)
        returned_bytes(own_pin, MAX_METADATA, deadline)
        remaining(deadline)
    publish(output, index_raw, custody_raw, final_checks, final_checks)
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps({'state': custody['state'], 'actual_campaign_admission': False,
                      'new_unsealed_index_pin': custody['new_unsealed_index_pin'],
                      'writer_custody_identity_sha256': custody['identity_sha256']}))


if __name__ == '__main__':
    try:
        main()
    except (Refused, KeyError, TypeError, ValueError, RecursionError, OSError, yaml.YAMLError,
            subprocess.SubprocessError) as error:
        # Never expose raw YAML/parser values, original logs, private state or argv.
        print(json.dumps({'state': 'refused', 'actual_campaign_admission': False,
                          'reason': str(error) if isinstance(error, Refused) else type(error).__name__,
                          'diagnostic_sha256': sha(str(error).encode())}), file=sys.stderr)
        sys.exit(3)
