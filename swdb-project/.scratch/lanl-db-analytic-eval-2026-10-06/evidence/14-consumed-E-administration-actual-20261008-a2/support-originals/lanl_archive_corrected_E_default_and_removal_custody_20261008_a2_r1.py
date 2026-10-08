"""Local BYTE-CUSTODY archiver preparation; main has NOT RUN at source creation.

Archives exact corrected E default/removal originals only after parent supplies
reviewed final inventory and executed worktree HEAD. Never imports/calls selected
controls, executes remote actions, removes files, commits or grants admission.
"""
import argparse, datetime, hashlib, json, os, pathlib, re, stat, subprocess, time
P = pathlib.Path
DEFAULT_W = P('/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve')
REL = 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-consumed-E-administration-actual-20261008-a2'
DEFAULT_ROOT = P('/private/tmp/lanl-detached-E-default-originals-20261008-a2')
REMOVAL_ROOT = P('/private/tmp/lanl-detached-E-removal-originals-20261008-a2')
EXPECTED_PRIMARY = '0a2d41ceff5d7a9a6c0732f692ae3c679539289d'
E = '/data1/yanruj/ArchEvolve-lanl-generality-final-export-20261007-a1'
PURE_E = '43256ee0300a59a03919833075fbb13fb3ba9ab3'
GUARD_SHA = '7f92b6f85f4e0c574f3ade7a806c2d6de02108fb8f32579f2e37343e9dc566f9'
WRAPPER_SHA = 'a04486d04c8f3a5f0ceee1d6ff58aeeacdb5aa2f4a9dec9e6befa8f40056cfaf'
REVIEW_PATH = '/data1/yanruj/lanl-account-pam-service-identification-20261008-a1/parent-review.json'
REVIEW_SHA = 'fcf92eee1c4b8bdfaed979dc8bedab004c6c4b7e2b1410c7614bc92d60349f4a'
MAX_FILE = 2 * 1024 * 1024
MAX_TOTAL = 8 * 1024 * 1024
MAX_ORIGINALS = 32
SECONDS = 180
NAMES = ('status.json', 'configuration.json', 'tmux.conf', 'launch-status.json',
         'launch.stdout', 'launch.stderr', 'guard.stdout', 'guard.stderr', 'local-custody.json')
# Only default originals are known at preparation time. No later removal pin is guessed.
DEFAULT_PINS = [
  {
    "original_path": "/private/tmp/lanl-detached-E-default-originals-20261008-a2/status.json",
    "relative_path": "default-originals/status.json",
    "bytes": 5309,
    "sha256": "0d5c2652ca982d053cffe44294490d6eda8a59ee4ebcd4d989e2407e0a0ac081",
    "original_policy": "original_unsealed_json"
  },
  {
    "original_path": "/private/tmp/lanl-detached-E-default-originals-20261008-a2/configuration.json",
    "relative_path": "default-originals/configuration.json",
    "bytes": 4684,
    "sha256": "46c5b18e0c71d3fc7886335989f904688974d1586d78e49ae974f77af27e5f7c",
    "original_policy": "original_unsealed_json"
  },
  {
    "original_path": "/private/tmp/lanl-detached-E-default-originals-20261008-a2/tmux.conf",
    "relative_path": "default-originals/tmux.conf",
    "bytes": 106,
    "sha256": "a6b69cdfa58f10a0f62697e88a619fffa06b5956bb515ba5200fa2e77c7c31df",
    "original_policy": "opaque_original_bytes"
  },
  {
    "original_path": "/private/tmp/lanl-detached-E-default-originals-20261008-a2/launch-status.json",
    "relative_path": "default-originals/launch-status.json",
    "bytes": 2097,
    "sha256": "b920ac82935add2d9fe1592a683bd0754cc97a699236488a7df9c2140476f8db",
    "original_policy": "original_unsealed_json"
  },
  {
    "original_path": "/private/tmp/lanl-detached-E-default-originals-20261008-a2/launch.stdout",
    "relative_path": "default-originals/launch.stdout",
    "bytes": 0,
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "original_policy": "opaque_original_bytes"
  },
  {
    "original_path": "/private/tmp/lanl-detached-E-default-originals-20261008-a2/launch.stderr",
    "relative_path": "default-originals/launch.stderr",
    "bytes": 0,
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "original_policy": "opaque_original_bytes"
  },
  {
    "original_path": "/private/tmp/lanl-detached-E-default-originals-20261008-a2/guard.stdout",
    "relative_path": "default-originals/guard.stdout",
    "bytes": 10434,
    "sha256": "5f17f45a303dcb7475800f136e0c8b70c558f6e9ea846869eb5e85a685d29e9e",
    "original_policy": "original_unsealed_json"
  },
  {
    "original_path": "/private/tmp/lanl-detached-E-default-originals-20261008-a2/guard.stderr",
    "relative_path": "default-originals/guard.stderr",
    "bytes": 0,
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "original_policy": "opaque_original_bytes"
  },
  {
    "original_path": "/private/tmp/lanl-detached-E-default-originals-20261008-a2/local-custody.json",
    "relative_path": "default-originals/local-custody.json",
    "bytes": 5087,
    "sha256": "94aeeaebb8397a92f86e8c441654179ad66b53299442c2236e52c14f7ca0f8ee",
    "original_policy": "original_unsealed_json"
  }
]

def require(value, code):
    if not value:
        raise ValueError(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value, ensure_ascii=True):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=ensure_ascii, allow_nan=False).encode()

def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate_JSON_key')
            result[key] = value
        return result
    def finite_float(value):
        number = float(value)
        require(number == number and abs(number) != float('inf'), 'nonfinite_JSON')
        return number
    return json.loads(raw, object_pairs_hook=pairs, parse_float=finite_float,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite_JSON')))

def stamp(s):
    # Reading may change atime; every content/identity field is retained.
    return (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_uid,
            s.st_gid, s.st_size, s.st_mtime_ns, s.st_ctime_ns)

def route(p):
    p = P(p)
    require(p.is_absolute() and str(p) == os.path.normpath(str(p)), 'canonical_absolute_path')
    for q in (p, *p.parents):
        require(not q.is_symlink(), 'path_symlink')
    return p

def read(p, cap, deadline):
    require(time.monotonic() < deadline, 'archive_deadline')
    p = route(p)
    s = p.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid() and s.st_nlink == 1
            and s.st_size <= cap, 'original_file_identity_or_bound')
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as f:
        require(stamp(os.fstat(f.fileno())) == stamp(s), 'original_open_identity')
        raw = f.read(cap + 1)
        require(len(raw) <= cap and len(raw) == s.st_size
                and stamp(os.fstat(f.fileno())) == stamp(s), 'original_returned_bytes_or_identity')
    require(stamp(p.lstat()) == stamp(s), 'original_final_identity')
    return raw, stamp(s)

def validate_pin(row, raw):
    require(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'original_byte_pin')
    policy = row['original_policy']
    require(policy in ('opaque_original_bytes', 'original_unsealed_json', 'original_sealed_json'),
            'original_policy')
    if policy != 'opaque_original_bytes':
        value = strict(raw)
        require(isinstance(value, dict), 'original_JSON_object')
        if policy == 'original_unsealed_json':
            require('identity_sha256' not in value, 'unsealed_original_has_identity')
        else:
            ensure_ascii = row['original_canonical_ensure_ascii']
            require(type(ensure_ascii) is bool, 'explicit_original_canonical_policy')
            identity = value.get('identity_sha256')
            require(isinstance(identity, str) and re.fullmatch('[0-9a-f]{64}', identity), 'original_identity')
            if 'canonical_ensure_ascii' in value:
                require(value['canonical_ensure_ascii'] is ensure_ascii, 'original_policy_mismatch')
            body = {key: item for key, item in value.items() if key != 'identity_sha256'}
            require(sha(canonical(body, ensure_ascii)) == identity, 'original_seal')
    return raw

def git(w, deadline, *argv):
    remain = deadline - time.monotonic()
    require(remain > 0, 'archive_deadline')
    result = subprocess.run(['git', '-C', str(w), *argv], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=min(60, remain), check=False)
    require(result.returncode == 0, 'read_only_Git_failure_' + sha(result.stderr))
    return result.stdout

def write_original(p, raw):
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    with p.open('rb') as f:
        require(f.read(len(raw) + 1) == raw, 'archive_readback')

def utc(value):
    require(isinstance(value, str), 'original_time_string')
    parsed = datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(parsed.utcoffset() == datetime.timedelta(0), 'original_UTC_time')
    return parsed


def receipt_pin(pin, raw, expected_path):
    require(isinstance(pin, dict) and pin['path'] == expected_path
            and type(pin['bytes']) is int and pin['bytes'] == len(raw)
            and pin['sha256'] == sha(raw), 'original_remote_pin_byte_link')
    return pin


def observation(phase, materialized):
    is_remove = phase == 'removal'
    body = {P(row['relative_path']).name: raw for row, raw, _ in materialized
            if row['relative_path'].startswith(phase + '-originals/')}
    require(set(body) == set(NAMES), 'nine_originals_per_observation')
    status, cfg, result, launch, custody = (strict(body[name]) for name in
        ('status.json', 'configuration.json', 'guard.stdout', 'launch-status.json', 'local-custody.json'))
    for value in (status, cfg, result, launch, custody):
        require(isinstance(value, dict) and value.get('sealed') is False
                and 'identity_sha256' not in value, 'original_unsealed_policy')
    require(status['format'] == 'swdb.lanl14-detached-exact-E-administration-status.v1'
            and status['state'] == 'guard_completed' and status['guard_exit_code'] == 0
            and 'error_class' not in status and 'error_sha256' not in status
            and status['scientific_admission'] is False and status['capacity_admission'] is False
            and status['SSH_role_exemption'] is False
            and status['global_consumer_clearance_claimed'] is False
            and status['expected_primary'] == EXPECTED_PRIMARY
            and status['remove_requested'] is is_remove, 'original_successful_administrative_status')
    require(cfg['format'] == 'swdb.lanl14-detached-exact-E-administration-configuration.v1'
            and cfg['expected_primary'] == EXPECTED_PRIMARY and cfg['remove_requested'] is is_remove
            and cfg['scientific_action'] is False and cfg['inputs'] == status['inputs']
            and cfg['transport_wait_seconds'] == 60 and cfg['guard_timeout_seconds'] == 660
            and cfg['guard_KILL_after_seconds'] == 60 and cfg['worker_wait_seconds'] == 735,
            'original_configuration_scope')
    folder = P(cfg['control_directory'])
    require(folder.is_absolute() and str(folder) == os.path.normpath(str(folder))
            and folder.parent == P('/data1/yanruj')
            and folder.name.startswith('lanl14-detached-e-'), 'original_remote_control_route')
    inputs = cfg['inputs']
    require(inputs['guard']['bytes'] == 26370 and inputs['guard']['sha256'] == GUARD_SHA
            and inputs['wrapper']['bytes'] == 18369 and inputs['wrapper']['sha256'] == WRAPPER_SHA
            and inputs['service_review']['path'] == REVIEW_PATH
            and inputs['service_review']['bytes'] == 3258
            and inputs['service_review']['sha256'] == REVIEW_SHA, 'original_selected_input_pins')
    receipt_pin(status['configuration'], body['configuration.json'], str(folder / 'configuration.json'))
    receipt_pin(status['guard_stdout'], body['guard.stdout'], str(folder / 'guard.stdout'))
    receipt_pin(status['guard_stderr'], body['guard.stderr'], str(folder / 'guard.stderr'))
    argv = ['/usr/bin/timeout', '--signal=TERM', '--kill-after=60s', '660s',
            '/usr/bin/python3.12', '-B', inputs['guard']['path'], '--expected-primary', EXPECTED_PRIMARY,
            '--account-service-review', REVIEW_PATH, '--account-service-review-sha256', REVIEW_SHA]
    if is_remove:
        argv.append('--remove')
    require(status['guard_argv'] == argv, 'original_closed_administrative_argv')
    require(result['format'] == 'swdb.lanl14-consumed-pure-E-checkout-removal.v1'
            and result['expected_primary'] == EXPECTED_PRIMARY and result['path'] == E
            and result['commit'] == PURE_E
            and result['branch'] == 'codex/lanl-generality-estimate-evidence-20261007-a1'
            and result['removed'] is is_remove
            and result['scientific_admission'] is False and result['capacity_admission'] is False
            and result['raw_and_original_controls_and_execution_sources_and_Git_refs_retained'] is True
            and result['account_service_review']['sha256'] == REVIEW_SHA,
            'original_result_scope_and_preservation_flag')
    require(type(result['recovered_bytes']) is int
            and (is_remove or result['recovered_bytes'] == 0), 'original_recovered_bytes')
    require(launch['format'] == 'swdb.lanl14-detached-exact-E-launch.v1'
            and launch['tmux_client_exit_code'] == 0 and launch['scientific_action'] is False
            and launch['transport_termination_or_guard_completion_claimed'] is False,
            'original_launch_boundary')
    require(launch['configuration'] == status['configuration'], 'launch_configuration_pin')
    receipt_pin(launch['tmux_configuration'], body['tmux.conf'], str(folder / 'tmux.conf'))
    require(custody['format'] == 'swdb.detached-E-original-local-byte-custody.v1'
            and custody['semantic_or_success_or_capacity_admission'] is False,
            'original_local_transport_custody_boundary')
    local_root = REMOVAL_ROOT if is_remove else DEFAULT_ROOT
    original_rows = custody['originals']
    require(isinstance(original_rows, list) and len(original_rows) == 8, 'eight_remote_original_custody_rows')
    seen = set()
    for item in original_rows:
        local = P(item['local_path'])
        require(local.parent == local_root and local.name in NAMES[:-1]
                and local.name not in seen, 'original_remote_custody_route_or_duplicate')
        seen.add(local.name)
        require(item['remote_original_path'] == str(folder / local.name)
                and item['bytes'] == len(body[local.name])
                and item['sha256'] == sha(body[local.name]), 'original_remote_local_byte_reconciliation')
    require(seen == set(NAMES[:-1]), 'complete_eight_original_custody_names')
    require(utc(status['started_utc']) <= utc(status['guard_started_utc'])
            <= utc(result['checked_utc']) <= utc(status['ended_utc']), 'original_observation_chronology')
    return {'status': status, 'configuration': cfg, 'result': result, 'body': body, 'custody': custody}


def reconcile_pair(materialized):
    default = observation('default', materialized)
    removal = observation('removal', materialized)
    require(default['configuration']['prior_reviewed_inspection'] is None,
            'original_default_has_no_prior_request')
    prior = removal['configuration']['prior_reviewed_inspection']
    require(isinstance(prior, dict) and set(prior) ==
            {'status', 'stdout', 'parent_review_is_inherited_explicit_invocation_authority'}
            and prior['parent_review_is_inherited_explicit_invocation_authority'] is True,
            'original_removal_explicit_prior_inspection')
    folder = default['configuration']['control_directory']
    receipt_pin(prior['status'], default['body']['status.json'], folder + '/status.json')
    receipt_pin(prior['stdout'], default['body']['guard.stdout'], folder + '/guard.stdout')
    default_status_custody = next(item for item in default['custody']['originals']
                                 if P(item['local_path']).name == 'status.json')
    require(prior['status']['stat'] == default_status_custody['remote_original_stat']
            and prior['stdout'] == default['status']['guard_stdout'], 'original_default_full_stat_pins')
    require(default['configuration']['control_directory'] != removal['configuration']['control_directory']
            and utc(default['status']['ended_utc']) <= utc(removal['status']['started_utc']),
            'separate_later_removal_observation')
    for name in ('original_reader', 'original_receipt'):
        require(default['result'][name] == removal['result'][name], 'same_original_E_reader_and_export_receipt')
    return {'default': {'started_utc': default['status']['started_utc'],
                        'ended_utc': default['status']['ended_utc'], 'guard_exit_code': 0, 'removed': False,
                        'status_sha256': sha(default['body']['status.json']),
                        'stdout_sha256': sha(default['body']['guard.stdout'])},
            'removal': {'started_utc': removal['status']['started_utc'],
                        'ended_utc': removal['status']['ended_utc'], 'guard_exit_code': 0, 'removed': True,
                        'status_sha256': sha(removal['body']['status.json']),
                        'stdout_sha256': sha(removal['body']['guard.stdout']),
                        'original_reported_recovered_bytes': removal['result']['recovered_bytes']},
            'interpretation': 'Original administrative result metadata reconciled locally; original consumer visibility and preservation facts are inherited from those exact originals, not newly observed by archival.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--worktree', default=str(DEFAULT_W))
    parser.add_argument('--inventory', required=True)
    parser.add_argument('--inventory-sha256', required=True)
    args = parser.parse_args()
    deadline = time.monotonic() + SECONDS
    os.umask(0o077)
    # Avoid Git's optional index refresh; no Git mutation command is present.
    os.environ['GIT_OPTIONAL_LOCKS'] = '0'
    require(re.fullmatch('[0-9a-f]{40}', args.expected_head), 'exact_parent_supplied_HEAD40')
    require(re.fullmatch('[0-9a-f]{64}', args.source_sha256)
            and re.fullmatch('[0-9a-f]{64}', args.inventory_sha256), 'explicit_source_and_inventory_SHA64')
    own = P(__file__).absolute()
    own_raw, own_stat = read(own, MAX_FILE, deadline)
    require(sha(own_raw) == args.source_sha256, 'own_source_pin')
    w = route(P(args.worktree))
    require(w == DEFAULT_W and w.is_dir(), 'fixed_owned_archive_worktree')
    require(git(w, deadline, 'rev-parse', 'HEAD').decode().strip() == args.expected_head
            and git(w, deadline, 'branch', '--show-current').decode().strip() == 'codex/lanl-analytic-eval'
            and not git(w, deadline, 'status', '--porcelain'), 'expected_clean_parent_worktree')
    before_tree = git(w, deadline, 'ls-tree', '-r', '-z', 'HEAD')
    inventory = route(P(args.inventory))
    require(inventory.parent == P('/private/tmp'), 'private_explicit_archival_inventory')
    inventory_raw, inventory_stat = read(inventory, 256 * 1024, deadline)
    require(sha(inventory_raw) == args.inventory_sha256, 'explicit_inventory_byte_pin')
    originals = strict(inventory_raw)
    require(isinstance(originals, list) and 18 <= len(originals) <= MAX_ORIGINALS,
            'explicit_18_to_32_original_inventory')
    allowed = {'original_path', 'relative_path', 'bytes', 'sha256', 'original_policy',
               'original_canonical_ensure_ascii'}
    required = {'original_path', 'relative_path', 'bytes', 'sha256', 'original_policy'}
    seen_paths, seen_names = set(), set()
    materialized = []
    total = 0
    for row in originals:
        require(isinstance(row, dict) and required <= set(row) <= allowed, 'explicit_inventory_row_fields')
        rel = P(row['relative_path'])
        require(not rel.is_absolute() and '..' not in rel.parts and str(rel) == row['relative_path']
                and len(rel.parts) == 2 and rel.parts[0] in
                ('default-originals', 'removal-originals', 'support-originals')
                and re.fullmatch('[A-Za-z0-9_./-]+', str(rel)), 'closed_relative_archive_path')
        p = route(P(row['original_path']))
        require(p.is_relative_to(P('/private/tmp')) and str(p) not in seen_paths
                and str(rel) not in seen_names, 'original_path_scope_or_duplicate')
        require(type(row['bytes']) is int and 0 <= row['bytes'] <= MAX_FILE
                and re.fullmatch('[0-9a-f]{64}', row['sha256']), 'explicit_original_size_SHA')
        if rel.parts[0] in ('default-originals', 'removal-originals'):
            root = DEFAULT_ROOT if rel.parts[0] == 'default-originals' else REMOVAL_ROOT
            require(p == root / rel.name and rel.name in NAMES, 'exact_original_observation_path')
            policy = 'original_unsealed_json' if rel.name.endswith('.json') or rel.name == 'guard.stdout' else 'opaque_original_bytes'
            require(row['original_policy'] == policy and 'original_canonical_ensure_ascii' not in row,
                    'original_observation_policy_unchanged')
        seen_paths.add(str(p)); seen_names.add(str(rel))
        total += row['bytes']; require(total <= MAX_TOTAL, 'cumulative_archive_original_bound')
        raw, s = read(p, MAX_FILE, deadline)
        validate_pin(row, raw)
        materialized.append((row, raw, s))
    actual_default = {row['relative_path']: row for row, _, _ in materialized
                      if row['relative_path'].startswith('default-originals/')}
    require(actual_default == {row['relative_path']: row for row in DEFAULT_PINS},
            'known_default_original_pins_unchanged')
    observations = reconcile_pair(materialized)
    dest = w / REL
    route(dest.parent)
    require(dest.parent.is_dir() and not os.path.lexists(dest), 'fresh_archive_destination')
    dest.mkdir(mode=0o700)
    pins = []
    try:
        for row, raw, _ in materialized:
            out = dest / row['relative_path']
            out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            write_original(out, raw)
            pins.append(dict(row, archive_path=REL + '/' + row['relative_path']))
        for row, old_raw, old_stat in materialized:
            later, s = read(P(row['original_path']), MAX_FILE, deadline)
            require(later == old_raw and s == old_stat, 'original_changed_during_archive')
        later, s = read(own, MAX_FILE, deadline)
        require(later == own_raw and s == own_stat, 'archiver_source_changed')
        later, s = read(inventory, 256 * 1024, deadline)
        require(later == inventory_raw and s == inventory_stat, 'explicit_inventory_changed')
        require(git(w, deadline, 'rev-parse', 'HEAD').decode().strip() == args.expected_head
                and git(w, deadline, 'ls-tree', '-r', '-z', 'HEAD') == before_tree
                and not git(w, deadline, 'diff', '--name-only', 'HEAD'), 'prior_tracked_tree_or_HEAD_changed')
        manifest = {'format': 'swdb.consumed-E-administration-original-byte-custody.v1',
                    'canonical_ensure_ascii': True,
                    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'parent_commit': args.expected_head, 'archive': REL,
                    'archiver_source_pin': {'path': str(own), 'bytes': len(own_raw), 'sha256': sha(own_raw)},
                    'explicit_inventory_pin': {'path': str(inventory), 'bytes': len(inventory_raw),
                                               'sha256': sha(inventory_raw)},
                    'originals': pins, 'original_count': len(pins), 'original_bytes': total,
                    'original_observation_reconciliation': observations,
                    'archival_invokes_selected_control_mains': False,
                    'archive_supplies_cleanup_capacity_plan_or_scientific_admission': False,
                    'prior_tracked_tree_SHA256': sha(before_tree),
                    'scope': 'BYTE-CUSTODY ONLY. Original default/removal observations and unsealed policies are preserved; no fresh consumer visibility, capacity, plan or scientific admission.'}
        manifest['identity_sha256'] = sha(canonical(manifest))
        manifest_raw = (json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()
        write_original(dest / 'manifest.json', manifest_raw)
        readme = ('# Corrected consumed E default and removal original custody\n\nDate: 2026-10-08 (ET)\n\n'
                  'This archive retains two separately observed administrative steps: the successful default inspection with removed=false, followed by a separately captured successful explicit removal with removed=true. The exact original times, status/stdout pins, original recovered-byte report, and the removal configuration prior-inspection links are recorded in the manifest. Archival reconciles original metadata locally and does not reacquire host visibility or perform cleanup.\n\n'
                  'All nine originals per observation are copied byte for byte, including their original UNSEALED status/configuration/result/launch/local-decoding custody and opaque streams. Explicit support originals, if supplied by the parent, retain their declared original policies and creation-time source-only/NOTRUN labels. The old failed inspection and earlier 66-original archive are untouched. No base64 transport envelope is manufactured or original seal field invented.\n\n'
                  'The manifest alone has a new explicit canonical True whole-object-minus-identity BYTE-CUSTODY seal. It is not a source of fresh capacity, parent completeness, plan, cleanup eligibility or scientific admission. Original retention/reference claims remain inherited from the exact original administrative receipts; they are not independent archival observations. The selected guard, wrapper, observers and scientific sources are never imported or called here.\n\n'
                  'Only this fresh evidence folder is written. Prior tracked blobs/modes and HEAD are checked; no issue, map, progress, record, source, existing file, commit, push or remote action is changed by this archiver. Any copied partials on failure remain for parent review without cleanup or retry.\n')
        write_original(dest / 'README.md', readme.encode())
        require(git(w, deadline, 'status', '--porcelain').decode().splitlines() == ['?? ' + REL + '/'],
                'archive_only_untracked_scope')
        require(git(w, deadline, 'rev-parse', 'HEAD').decode().strip() == args.expected_head
                and git(w, deadline, 'ls-tree', '-r', '-z', 'HEAD') == before_tree
                and not git(w, deadline, 'diff', '--name-only', 'HEAD'), 'final_parent_tree_changed')
        # Close source/request/input stability after publication too.
        for row, old_raw, old_stat in materialized:
            later, s = read(P(row['original_path']), MAX_FILE, deadline)
            require(later == old_raw and s == old_stat, 'original_changed_before_success')
        require(read(own, MAX_FILE, deadline) == (own_raw, own_stat), 'final_archiver_source_changed')
        require(read(inventory, 256 * 1024, deadline) == (inventory_raw, inventory_stat),
                'final_inventory_changed')
        print(json.dumps({'archive': REL, 'expected_head': args.expected_head, 'originals': len(pins),
                          'original_bytes': total, 'new_files': len(pins) + 2,
                          'manifest_identity_sha256': manifest['identity_sha256'],
                          'manifest_bytes': len(manifest_raw), 'manifest_sha256': sha(manifest_raw),
                          'README_bytes': len(readme.encode()), 'README_sha256': sha(readme.encode()),
                          'selected_mains_or_remote_actions_invoked': False,
                          'fresh_capacity_plan_or_scientific_admission': False}, sort_keys=True))
    except BaseException:
        # Retain copied partials; no deletion, repair, retry or original rewrite.
        raise


if __name__ == '__main__':
    main()
