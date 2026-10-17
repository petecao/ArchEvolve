#!/usr/bin/env python3
"""PROSPECTIVE first-publication request author; NOT RUN, 2026-10-07 ET.

Exactly one reviewed original publication specification becomes one original
32bead parent-capture request and a separate author/file-pin custody receipt.
The author does not run the producer, collector, auditor, Store, validation,
policy freeze, campaign, native/provider experiment, SSH or Git mutation.
Successful preparation and zero opened outcomes require explicit reviewed
original receipts/observations, never path names. Publication observations and
export publication remain parent attestations; this is not study admission.
New request/author-custody hashing explicitly uses canonical ensure_ascii=True.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import pwd
import re
import socket
import stat
import subprocess
import sys
import time
import yaml

sys.dont_write_bytecode = True
C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
PRODUCER = '32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6'
HELPER = '28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
SUPERVISOR = 'fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0'
AUDITOR = '6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da'
COLLECTOR = 'b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'
PROCESSES = 'bcc9ccdc9979a8da416c2c723e80278e17ce8e43e47ebcab29d684da16895289'
PLAN = 'e3420b334ce05f7268699b0079987d1d2afc98fe5cb5503e6069a89038b59170'
CHECKLIST = '45313085d7d010be749f9b9aec7c9aadf0b5b8d1e7c385bfb9f79fd384cc6fe0'
CONTRACT = '192eb5d1c2b461f9d42b3532a934c8dc107bb193f29fabbb5ba2dec94acd2978'
SPEC_FORMAT = 'swdb.lanl17-first-publication-request-author-spec.v1'
REQUEST_FORMAT = 'swdb.lanl17-parent-capture-request.v1'
CUSTODY_FORMAT = 'swdb.lanl17-first-publication-request-author-custody.v1'
CIDS = tuple('extensa-gem5-bfs-20261006-p' + str(i) for i in range(1, 5))
MAX_METADATA = 8 * 1024 * 1024
MAX_ORIGINAL = 32 * 1024 * 1024
MAX_DECLARED_ORIGINALS = 512 * 1024 * 1024
CONTROL_HASHES = {'producer': PRODUCER, 'helper': HELPER, 'supervisor': SUPERVISOR,
    'auditor': AUDITOR, 'collector': COLLECTOR, 'source_plan': PLAN,
    'field_checklist': CHECKLIST, 'accepted_input_contract': CONTRACT}
FORBIDDEN_NAMES = {'.codex', '.ssh', '.aws', 'auth.json', 'provider.json', 'prompt.txt', 'feedback.txt'}
STAMP_KEYS = ('st_dev', 'st_ino', 'st_mode', 'st_uid', 'st_size', 'st_mtime_ns', 'st_ctime_ns')


class Refused(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Refused(code)


def exact(value, keys, code):
    require(isinstance(value, dict) and set(value) == set(keys), code)
    return value


def full_hash(value, length=64):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value), 'full_hash_required')
    return value


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value, ensure_ascii=True):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=ensure_ascii, allow_nan=False).encode())


def strict_json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'duplicate_original_JSON_key')
            result[key] = value
        return result
    def nonfinite(_):
        raise Refused('nonfinite_original_JSON_constant')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


class RecordLoader(getattr(yaml, 'CSafeLoader', yaml.SafeLoader)):
    pass


RecordLoader.yaml_implicit_resolvers = {
    first: [(tag, regexp) for tag, regexp in rows if tag != 'tag:yaml.org,2002:timestamp']
    for first, rows in RecordLoader.yaml_implicit_resolvers.items()
}


def no_duplicates(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        require(key not in seen, 'duplicate_original_YAML_key')
        seen.add(key)
    return loader.construct_mapping(node, deep=deep)


RecordLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, no_duplicates)


def plain(value, depth=0, active=None):
    require(depth <= 100, 'bounded_plain_metadata_required')
    active = set() if active is None else active
    if isinstance(value, (dict, list)):
        require(id(value) not in active, 'cyclic_metadata_refused')
        active.add(id(value))
        if isinstance(value, dict):
            require(all(isinstance(key, str) for key in value), 'string_metadata_keys_required')
            children = value.values()
        else:
            children = value
        for child in children:
            plain(child, depth + 1, active)
        active.remove(id(value))
    else:
        require(value is None or type(value) in (str, int, bool) or
                type(value) is float and math.isfinite(value), 'plain_finite_metadata_required')


def utc(value):
    require(isinstance(value, str), 'explicit_UTC_observation_required')
    parsed = datetime.datetime.fromisoformat(value)
    require(parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0, 'explicit_UTC_observation_required')
    return parsed


def remaining(deadline):
    left = deadline - time.monotonic()
    require(left > 0, 'finite_author_metadata_deadline_exceeded')
    return left


def checked_path(text, directory=False):
    require(isinstance(text, (str, Path)), 'explicit_absolute_path_required')
    path = Path(text)
    require(path.is_absolute() and '..' not in path.parts and
            all(not part.is_symlink() for part in (path, *path.parents)), 'all_path_components_nonsymlink_required')
    require(not FORBIDDEN_NAMES.intersection(path.parts), 'credential_prompt_feedback_source_refused')
    actual = path.resolve(strict=True)
    status = actual.stat()
    require(stat.S_ISDIR(status.st_mode) if directory else stat.S_ISREG(status.st_mode), 'original_regular_type_required')
    require(status.st_uid == os.getuid(), 'original_own_UID_required')
    return actual


def file_pin(value, maximum):
    exact(value, ('path', 'bytes', 'sha256'), 'exact_file_pin_required')
    require(type(value['bytes']) is int and 0 <= value['bytes'] <= maximum, 'bounded_exact_file_size_required')
    full_hash(value['sha256'])
    checked_path(value['path'])
    return dict(value)


def returned_bytes(pin, maximum, deadline):
    remaining(deadline)
    file_pin(pin, maximum)
    path = checked_path(pin['path'])
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid() and before.st_size == pin['bytes'],
                'original_fd_type_UID_size_differs')
        blocks, size = [], 0
        while True:
            remaining(deadline)
            block = stream.read(min(1024 * 1024, pin['bytes'] + 1 - size))
            if not block:
                break
            blocks.append(block)
            size += len(block)
            require(size <= pin['bytes'], 'original_returned_size_differs')
        after = os.fstat(stream.fileno())
    raw = b''.join(blocks)
    final = checked_path(path).stat()
    require(len(raw) == pin['bytes'] and sha(raw) == pin['sha256'], 'returned_bytes_SHA_differs_before_parse')
    require(all(getattr(before, key) == getattr(after, key) == getattr(final, key) for key in STAMP_KEYS),
            'original_replaced_or_changed_while_reading')
    return raw


def read_only_git(source, deadline, *args):
    # Calls below are fixed local read-only metadata/blob operations; no fetch,
    # lazy network, authentication, hooks or optional index locks.
    environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    environment.update(GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0', GIT_PAGER='cat')
    return subprocess.check_output(['git', '-c', 'protocol.allow=never', '-c', 'core.fsmonitor=false',
        '-C', str(source), *args], timeout=min(60, remaining(deadline)), env=environment, stderr=subprocess.DEVNULL)


def source_identity(source, revision, tree, deadline):
    full_hash(revision, 40)
    full_hash(tree, 40)
    require(read_only_git(source, deadline, 'rev-parse', '--show-toplevel').decode().strip() == str(source) and
            read_only_git(source, deadline, 'rev-parse', 'HEAD').decode().strip() == revision and
            read_only_git(source, deadline, 'rev-parse', revision + '^{tree}').decode().strip() == tree and
            not read_only_git(source, deadline, 'status', '--porcelain').strip(), 'exact_clean_actual_R_tree_required')
    read_only_git(source, deadline, 'merge-base', '--is-ancestor', C, revision)
    def modules(ref):
        result = {}
        for row in read_only_git(source, deadline, 'ls-tree', '-r', '-z', ref, 'swdb-project/swdb').split(b'\0'):
            if row:
                meta, name = row.split(b'\t', 1)
                if name.endswith(b'.py'):
                    require(meta.split()[:2] in ([b'100644', b'blob'], [b'100755', b'blob']), 'regular_C_python_blob_required')
                    result[name.decode()] = meta
        return result
    original, current = modules(C), modules(revision)
    require(len(original) == 185 and current == original, 'actual_R_not_exact_185_C_modules')
    root = checked_path(source / 'swdb-project/swdb', directory=True)
    paths = set()
    for path in root.rglob('*'):
        require(not path.is_symlink(), 'live_python_source_symlink_refused')
        if path.suffix == '.py':
            checked_path(path)
            paths.add(path.relative_to(source).as_posix())
    require(paths == set(current), 'live_C_python_inventory_differs_including_ignored_files')
    hashes = {}
    for name in sorted(current):
        raw = read_only_git(source, deadline, 'cat-file', 'blob', C + ':' + name)
        pin = {'path': str(source / name), 'bytes': len(raw), 'sha256': sha(raw)}
        returned_bytes(pin, MAX_METADATA, deadline)
        hashes[name[len('swdb-project/swdb/'):]] = sha(raw)
    require(digest(hashes) == F6, 'live_185_module_F6_differs')
    return {'commit': revision, 'tree': tree, 'source_C': C, 'estimator_sha256': F6, 'modules': 185, 'source_clean': True}


def original_inputs(spec, controls, read_roots, deadline):
    expected = {'manifest_M2': ('json', True, True, 'swdb.lanl17-parent-population.v1', 'helper'),
        'prepare_supervisor': ('json', True, False, 'swdb.lanl17-metadata-supervisor.v1', 'supervisor'),
        'freeze_receipt': ('json', True, True, 'swdb.lanl17-freeze-receipt.v1', 'helper'),
        'policy': ('yaml', False, None, None, None)}
    exact(spec, expected, 'only_four_original_publication_inputs_required')
    data, pins = {}, []
    for name, (encoding, sealed, policy, format_name, writer) in expected.items():
        descriptor = spec[name]
        keys = {'path', 'bytes', 'sha256', 'encoding', 'sealed', 'writer_source'}
        if sealed:
            keys.update(('identity_sha256', 'canonical_ensure_ascii', 'canonical_policy_sources'))
        exact(descriptor, keys, 'exact_original_32bead_input_descriptor_required')
        require(descriptor['encoding'] == encoding and descriptor['sealed'] is sealed, 'original_encoding_sealed_classification_differs')
        pin = {key: descriptor[key] for key in ('path', 'bytes', 'sha256')}
        require(any(checked_path(pin['path']).is_relative_to(root) for root in read_roots), 'original_outside_reviewed_read_roots')
        raw = returned_bytes(pin, MAX_ORIGINAL, deadline)
        value = strict_json(raw) if encoding == 'json' else yaml.load(raw, Loader=RecordLoader)
        plain(value)
        require(isinstance(value, dict), 'original_publication_mapping_required')
        writer_pin = file_pin(descriptor['writer_source'], MAX_ORIGINAL)
        require(any(Path(writer_pin['path']).is_relative_to(root) for root in read_roots), 'original_writer_outside_reviewed_read_roots')
        returned_bytes(writer_pin, MAX_ORIGINAL, deadline)
        pins.extend((pin, writer_pin))
        if sealed:
            require(type(descriptor['canonical_ensure_ascii']) is bool and descriptor['canonical_ensure_ascii'] is policy,
                    'actual_original_writer_canonical_policy_differs')
            require(writer_pin == controls[writer], 'original_sealed_writer_not_exact_reviewed_control')
            full_hash(descriptor['identity_sha256'])
            require(value['format'] == format_name and value['identity_sha256'] == descriptor['identity_sha256'] and
                    digest({key: item for key, item in value.items() if key != 'identity_sha256'}, policy) == value['identity_sha256'],
                    'original_compact_format_or_seal_differs')
            require(descriptor['canonical_policy_sources'] == [controls[writer]], 'explicit_exact_original_canonical_policy_source_required')
            pins.append(dict(controls[writer]))
        data[name] = value
    require(sum(row['bytes'] for row in spec.values()) <= MAX_DECLARED_ORIGINALS, 'original_32bead_declared_total_bound_exceeded')
    return data, pins


def publication(spec, originals):
    ctx, observations = spec['context'], spec['observations']
    exact(ctx, ('source_commit', 'source_C', 'estimator_sha256', 'helper_sha256', 'source_path',
        'manifest_identity_sha256', 'policy', 'account'), 'exact_original_publication_context_required')
    require(ctx['source_C'] == C and ctx['estimator_sha256'] == F6 and ctx['helper_sha256'] == HELPER,
            'explicit_original_C_F6_helper_required')
    full_hash(ctx['source_commit'], 40)
    full_hash(ctx['manifest_identity_sha256'])
    exact(ctx['account'], ('platform', 'host', 'uid', 'user'), 'explicit_original_account_required')
    require(ctx['account'] == {'platform': 'linux', 'host': 'mbit10', 'uid': 114316761, 'user': 'yanruj'}, 'reviewed_parent_account_differs')
    exact(ctx['policy'], ('id', 'identity_sha256', 'frozen_at'), 'exact_original_policy_context_required')
    require(isinstance(ctx['policy']['id'], str) and len(ctx['policy']['id']) <= 256 and
            re.fullmatch('[A-Za-z0-9_.:/+-]+', ctx['policy']['id']), 'original_public_policy_ID_required')
    full_hash(ctx['policy']['identity_sha256'])
    utc(ctx['policy']['frozen_at'])
    exact(observations, ('freeze_export_commit', 'completed_export_exit_code', 'application_outcomes_opened',
        'frozen_live_files_verified', 'checked_utc'), 'all_original_publication_observations_explicit_required')
    full_hash(observations['freeze_export_commit'], 40)
    require(type(observations['completed_export_exit_code']) is int and observations['completed_export_exit_code'] == 0 and
            type(observations['application_outcomes_opened']) is int and observations['application_outcomes_opened'] == 0 and
            observations['frozen_live_files_verified'] is True, 'explicit_successful_publication_and_zero_outcome_observation_required')
    m2, prepare, freeze, policy = (originals[name] for name in ('manifest_M2', 'prepare_supervisor', 'freeze_receipt', 'policy'))
    require(m2['source_commit'] == freeze['manifest']['source_commit'] == ctx['source_commit'] and
            m2['source'] == ctx['source_path'] and m2['identity_sha256'] == ctx['manifest_identity_sha256'] and
            m2['helper_sha256'] == HELPER and m2['estimator_sha256'] == F6 and m2['source_clean'] is True and
            m2['policy'] == ctx['policy'], 'actual_original_M2_source_policy_differs')
    m1 = freeze['manifest']
    require(m1['identity_sha256'] == digest({key: value for key, value in m1.items() if key != 'identity_sha256'}) and
            {key: value for key, value in m2.items() if key not in {'identity_sha256', 'freeze_export'}} ==
            {key: value for key, value in m1.items() if key != 'identity_sha256'}, 'original_M2_not_original_sealed_M1_plus_export')
    require(m2['freeze_export']['commit'] == observations['freeze_export_commit'] and
            freeze['public_policy'] == policy and freeze['population_frozen'] is True and
            type(freeze['application_outcomes_opened']) is int and freeze['application_outcomes_opened'] == 0,
            'actual_original_freeze_export_policy_binding_differs')
    require(policy['kind'] == 'agreement_policy' and policy['mode'] == 'extensa' and policy['format'] == 'swdb.extensa-agreement-policy.v1' and
            {key: policy[key] for key in ('id', 'identity_sha256', 'frozen_at')} == ctx['policy'] and policy['estimator_sha256'] == F6,
            'original_public_policy_identity_differs')
    require(prepare['action'] == 'prepare' and prepare['state'] == 'child_returned' and prepare['fixture'] is False and
            type(prepare['child_exit']) is int and prepare['child_exit'] == 0 and type(prepare['supervisor_exit']) is int and
            prepare['supervisor_exit'] == 0 and prepare['timed_out'] is False and prepare['signal_received'] is None and
            prepare['cleanup_errors'] == [] and prepare['error_type'] is None and prepare['cleanup']['subreaper'] is True and
            prepare['cleanup']['survivors'] == {}, 'original_actual_prepare_did_not_complete_cleanly')
    require(prepare['helper_sha256'] == prepare['cleanup_implementation_sha256'] == HELPER and
            prepare['supervisor_sha256'] == SUPERVISOR and prepare['processes_py_sha256'] == PROCESSES and
            prepare['estimator_sha256'] == F6 and prepare['uid'] == ctx['account']['uid'] and
            type(prepare['provider_calls']) is int and prepare['provider_calls'] == 0 and
            type(prepare['application_outcomes']) is int and prepare['application_outcomes'] == 0,
            'actual_metadata_prepare_source_scope_differs')
    checked = utc(observations['checked_utc'])
    require(checked >= utc(prepare['ended_utc']) and checked >= utc(freeze['checked_utc']) and
            checked >= utc(policy['frozen_at']), 'publication_observation_precedes_original_prepare_freeze')
    return m2


def recheck(pins, deadline):
    for pin in pins:
        returned_bytes(pin, MAX_ORIGINAL, deadline)


def write_exclusive(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
    require(stat.S_IMODE(path.stat().st_mode) == 0o600 and path.stat().st_uid == os.getuid(), 'private_new_file_mode_UID_differs')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('specification', 'specification-sha256', 'parent-review-sha256', 'author-sha256', 'output-directory'):
        parser.add_argument('--' + flag, required=True)
    parser.add_argument('--metadata-deadline-seconds', type=int, required=True)
    args = parser.parse_args()
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10' and
            os.getuid() == os.geteuid() == 114316761 and pwd.getpwuid(os.getuid()).pw_name == 'yanruj', 'actual_reviewed_Linux_mbit10_parent_UID_required')
    require(60 <= args.metadata_deadline_seconds <= 3600, 'explicit_finite_author_metadata_allowance_required')
    deadline = time.monotonic() + args.metadata_deadline_seconds
    specification = checked_path(args.specification)
    spec_pin = {'path': str(specification), 'bytes': specification.stat().st_size, 'sha256': full_hash(args.specification_sha256)}
    raw = returned_bytes(spec_pin, MAX_METADATA, deadline)
    spec = strict_json(raw)
    plain(spec)
    exact(spec, ('format', 'context', 'observations', 'inputs', 'read_roots', 'final_R', 'controls',
        'parent_review', 'output_directory'), 'exact_explicit_publication_author_spec_required')
    require(spec['format'] == SPEC_FORMAT and spec['output_directory'] == args.output_directory, 'original_reviewed_spec_output_differs')
    review = exact(spec['parent_review'], ('basis', 'author_sha256', 'reviewed_spec_payload_sha256',
        'actual_inputs_parent_approved', 'fixtures_or_replays_allowed', 'freeze_export_publication_parent_checked',
        'reviewed_utc'), 'exact_parent_publication_review_required')
    require(digest(review) == full_hash(args.parent_review_sha256) and review['author_sha256'] == full_hash(args.author_sha256) and
            review['reviewed_spec_payload_sha256'] == digest({key: value for key, value in spec.items() if key != 'parent_review'}) and
            review['basis'] == 'explicit_parent_review_of_actual_publication_inputs_and_original_observations' and
            review['actual_inputs_parent_approved'] is True and review['fixtures_or_replays_allowed'] is False and
            review['freeze_export_publication_parent_checked'] is True,
            'explicit_parent_original_input_and_publication_review_differs')
    own = checked_path(__file__)
    own_pin = {'path': str(own), 'bytes': own.stat().st_size, 'sha256': args.author_sha256}
    returned_bytes(own_pin, MAX_METADATA, deadline)
    pins = [spec_pin, own_pin]
    require(isinstance(spec['read_roots'], list) and 0 < len(spec['read_roots']) <= 16, 'bounded_explicit_read_roots_required')
    roots = [checked_path(root, directory=True) for root in spec['read_roots']]
    require(len(set(roots)) == len(roots) and all(root.is_relative_to(Path('/data/yanruj')) or
            root.is_relative_to(Path('/data1/yanruj')) for root in roots), 'explicit_owned_external_read_roots_required')
    exact(spec['controls'], CONTROL_HASHES, 'exact_original_control_plan_pin_set_required')
    controls = {}
    for name, expected in CONTROL_HASHES.items():
        pin = file_pin(spec['controls'][name], MAX_METADATA)
        require(pin['sha256'] == expected and any(Path(pin['path']).is_relative_to(root) for root in roots),
                'selected_control_plan_SHA_or_read_root_differs')
        returned_bytes(pin, MAX_METADATA, deadline)
        controls[name] = pin
        pins.append(pin)
    originals, original_pins = original_inputs(spec['inputs'], controls, roots, deadline)
    pins.extend(original_pins)
    m2 = publication(spec, originals)
    require(utc(review['reviewed_utc']) >= utc(spec['observations']['checked_utc']) and
            utc(review['reviewed_utc']) <= datetime.datetime.now(datetime.timezone.utc), 'actual_parent_review_UTC_differs')
    source = checked_path(m2['source'], directory=True)
    require(str(source) == spec['context']['source_path'] and source.is_relative_to(Path('/data1/yanruj')),
            'exact_original_M2_source_root_required')
    final_R = exact(spec['final_R'], ('commit', 'tree'), 'explicit_reviewed_final_R_tree_required')
    require(final_R['commit'] == m2['source_commit'], 'reviewed_final_R_not_original_M2_source')
    identity = source_identity(source, final_R['commit'], final_R['tree'], deadline)
    policy_writer = checked_path(spec['inputs']['policy']['writer_source']['path'])
    require(policy_writer.is_relative_to(source / 'swdb-project/swdb') and policy_writer.suffix == '.py',
            'original_public_policy_writer_must_be_pinned_live_C_source')
    raw_root = checked_path(m2['raw'], directory=True)
    require(raw_root.is_relative_to(Path('/data/yanruj')) and
            Path(spec['inputs']['manifest_M2']['path']) == raw_root / 'manifest.json', 'canonical_original_M2_path_required')
    campaigns = tuple(raw_root / 'campaign-runs' / 'extensa' / cid for cid in CIDS)
    for path in campaigns:
        require(all(not component.is_symlink() for component in (path, *path.parents)), 'original_campaign_path_redirect_refused')
        if path.exists():
            checked_path(path, directory=True)
    # The original helper/control field checks above do not prove GitHub
    # publication or zero historical outcomes; those observations remain explicit
    # parent review. No scientific/public policy algorithm is invoked here.
    output = Path(args.output_directory)
    require(output.is_absolute() and '..' not in output.parts and re.fullmatch('[A-Za-z0-9_.-]+', output.name) and
            all(not component.is_symlink() for component in (output, *output.parents)) and
            not output.exists(), 'fresh_absolute_nonsymlink_author_output_directory_required')
    parent = checked_path(output.parent, directory=True)
    output = parent / output.name
    require(output.is_relative_to(Path('/data/yanruj')) and not any(output.is_relative_to(root) for root in (source, raw_root, *campaigns)),
            'private_fresh_author_output_outside_original_source_raw_four_campaigns_required')
    request = {'format': REQUEST_FORMAT, 'producer_sha256': PRODUCER, 'source_plan_sha256': PLAN,
        'auditor_sha256': AUDITOR, 'collector_sha256': COLLECTOR, 'capture': 'publication',
        'context': spec['context'], 'observations': spec['observations'], 'inputs': spec['inputs'], 'read_roots': spec['read_roots']}
    request['identity_sha256'] = digest(request)
    encoded = (json.dumps(request, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()
    require(len(encoded) <= MAX_METADATA, 'bounded_original_publication_request_required')
    recheck(pins, deadline)
    require(source_identity(source, final_R['commit'], final_R['tree'], deadline) == identity, 'actual_source_changed_before_author_publication')
    output.mkdir(mode=0o700)
    require(stat.S_IMODE(output.stat().st_mode) == 0o700 and output.stat().st_uid == os.getuid(), 'fresh_private_author_directory_mode_UID_differs')
    request_path = output / 'publication-request.json'
    write_exclusive(request_path, encoded)
    request_pin = {'path': str(request_path), 'bytes': len(encoded), 'sha256': sha(encoded),
        'identity_sha256': request['identity_sha256'], 'canonical_ensure_ascii': True}
    custody = {'format': CUSTODY_FORMAT, 'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'author_source_pin': own_pin, 'specification_file_pin': spec_pin, 'parent_review_sha256': args.parent_review_sha256,
        'original_source_identity': identity, 'original_control_sources': controls,
        'original_publication_inputs': spec['inputs'], 'original_observations_sha256': digest(spec['observations']),
        'request_file_pin': request_pin, 'canonical_ensure_ascii': True,
        'output_exclusion_roots': [str(root) for root in (source, raw_root, *campaigns)],
        'producer_or_collector_or_auditor_or_public_scientific_command_executed': False,
        'scope': 'Publication request author only. Original successful prepare and explicit publication observations are reviewed inputs. Export publication, live-file verification and zero opened outcomes are parent attestations; no trajectory, D30, final dependency or study admission.'}
    custody['identity_sha256'] = digest(custody)
    custody_raw = (json.dumps(custody, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()
    require(len(custody_raw) <= MAX_METADATA, 'bounded_author_file_pin_custody_required')
    custody_path = output / 'author-custody.json'
    write_exclusive(custody_path, custody_raw)
    recheck(pins, deadline)
    require(source_identity(source, final_R['commit'], final_R['tree'], deadline) == identity, 'actual_source_changed_before_author_success')
    returned_bytes({key: request_pin[key] for key in ('path', 'bytes', 'sha256')}, MAX_METADATA, deadline)
    custody_pin = {'path': str(custody_path), 'bytes': len(custody_raw), 'sha256': sha(custody_raw),
        'identity_sha256': custody['identity_sha256'], 'canonical_ensure_ascii': True}
    returned_bytes({key: custody_pin[key] for key in ('path', 'bytes', 'sha256')}, MAX_METADATA, deadline)
    print(json.dumps({'format': CUSTODY_FORMAT, 'request': request_pin, 'author_custody': custody_pin,
        'author_source': own_pin, 'source_identity': identity, 'capture_executed': False}, ensure_ascii=True, allow_nan=False))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, yaml.YAMLError, subprocess.SubprocessError) as exc:
        print(json.dumps({'format': 'swdb.lanl17-first-publication-request-author-refusal.v1',
            'exception_class': type(exc).__name__, 'exception_message_sha256': sha(str(exc).encode(errors='replace')),
            'original_parser_or_command_or_environment_text_transferred': False}), file=sys.stderr)
        raise SystemExit(2)
