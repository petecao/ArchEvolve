"""Local byte-custody archiver; SOURCE PREPARATION ONLY until parent invokes main.

Copies fixed original files and optional explicitly reviewed correction originals.
Never imports or calls selected controls, SSH, guard, observer, Store or tests.
No commit/push, issue edit, mode change to existing files, cleanup or admission.
"""
import argparse, datetime, hashlib, json, os, pathlib, re, stat, subprocess, time
P = pathlib.Path
DEFAULT_W = P('/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve')
REL = 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-detached-E-inspection-failure-and-source-custody-20261008-a1'
MAX_FILE = 2 * 1024 * 1024
MAX_TOTAL = 8 * 1024 * 1024
MAX_EXTRA = 32
SECONDS = 180
# Fixed originals were read/hash-pinned during preparation. No future pin is guessed.
FIXED = [{'bytes': 5251, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-detached-E-default-originals-20261008-a1/status.json', 'original_policy': 'original_unsealed_json', 'relative_path': 'failed-originals/status.json', 'sha256': 'e723a2ea379155b89c47502658602c6ca0becc84e2d1771cfe090cb4639eedf8'}, {'bytes': 4687, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-detached-E-default-originals-20261008-a1/configuration.json', 'original_policy': 'original_unsealed_json', 'relative_path': 'failed-originals/configuration.json', 'sha256': '51ebd75c968c7fe6fd9a8b530009837cea508ec486071c208e4eb11131c20a1d'}, {'bytes': 106, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-detached-E-default-originals-20261008-a1/tmux.conf', 'original_policy': 'opaque_original_bytes', 'relative_path': 'failed-originals/tmux.conf', 'sha256': 'a6b69cdfa58f10a0f62697e88a619fffa06b5956bb515ba5200fa2e77c7c31df'}, {'bytes': 2097, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-detached-E-default-originals-20261008-a1/launch-status.json', 'original_policy': 'original_unsealed_json', 'relative_path': 'failed-originals/launch-status.json', 'sha256': '7379eb89d1c18a3b8b7b0a1aa7dee9e1aa79bca3db4cb7afa9d730946c71e9f2'}, {'bytes': 0, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-detached-E-default-originals-20261008-a1/launch.stdout', 'original_policy': 'opaque_original_bytes', 'relative_path': 'failed-originals/launch.stdout', 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, {'bytes': 0, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-detached-E-default-originals-20261008-a1/launch.stderr', 'original_policy': 'opaque_original_bytes', 'relative_path': 'failed-originals/launch.stderr', 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, {'bytes': 0, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-detached-E-default-originals-20261008-a1/guard.stdout', 'original_policy': 'opaque_original_bytes', 'relative_path': 'failed-originals/guard.stdout', 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, {'bytes': 727, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-detached-E-default-originals-20261008-a1/guard.stderr', 'original_policy': 'opaque_original_bytes', 'relative_path': 'failed-originals/guard.stderr', 'sha256': '318551da812cabda621fb6fa5f3600826195a8e389da3663e7d1443560f27a1f'}, {'bytes': 5083, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-detached-E-default-originals-20261008-a1/local-custody.json', 'original_policy': 'original_unsealed_json', 'relative_path': 'failed-originals/local-custody.json', 'sha256': '804fd01dee30e2b2bd275aa29f0ca405d9ac58ef65774d050eb76df67583d5d4'}, {'bytes': 2849, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl_read_detached_E_administration_originals_20261008_a1_r1.py', 'original_policy': 'opaque_original_bytes', 'relative_path': 'original-custody/lanl_read_detached_E_administration_originals_20261008_a1_r1.py', 'sha256': '70aea2815b329c160ba3aaa7c48d1ad48448a03bec1d7ab63707d1ddc1b2a853'}, {'bytes': 2977, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl_decode_detached_E_original_custody_20261008_a1.py', 'original_policy': 'opaque_original_bytes', 'relative_path': 'original-custody/lanl_decode_detached_E_original_custody_20261008_a1.py', 'sha256': '5ad38e9d0c40446daafbfda5323567c8fdf40029953cf7fb3ae3a566c3d7db8a'}, {'bytes': 29403, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-RAW-top-LANL-namespace-original-20261008-a1.json', 'original_policy': 'original_unsealed_json', 'relative_path': 'original-custody/lanl-RAW-top-LANL-namespace-original-20261008-a1.json', 'sha256': '48c02d1a1332e213077d19f7268ffd59f63334fe6657a1931c2dff26638c9b28'}, {'bytes': 0, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-RAW-top-LANL-namespace-original-20261008-a1.stderr', 'original_policy': 'opaque_original_bytes', 'relative_path': 'original-custody/lanl-RAW-top-LANL-namespace-original-20261008-a1.stderr', 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, {'bytes': 1506, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-original-top-lane-sidecar-readonly-custody-20261008-a1.json', 'original_policy': 'original_unsealed_json', 'relative_path': 'original-custody/lanl-original-top-lane-sidecar-readonly-custody-20261008-a1.json', 'sha256': '1697dc07d42fb8239aaea2ddd6de9d2048d4a0e4891606ea48d129d039e2515a'}, {'bytes': 0, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-original-top-lane-sidecar-readonly-custody-20261008-a1.stderr', 'original_policy': 'opaque_original_bytes', 'relative_path': 'original-custody/lanl-original-top-lane-sidecar-readonly-custody-20261008-a1.stderr', 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, {'bytes': 1058, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl_read_original_top_lane_sidecar_20261008_a1.py', 'original_policy': 'opaque_original_bytes', 'relative_path': 'original-custody/lanl_read_original_top_lane_sidecar_20261008_a1.py', 'sha256': '61687eb49f2441436b38c1f04a603c0cf25cab7c4a95d18dd8c8cde852635181'}, {'bytes': 400, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-detached-E-default-launch-original-20261008-a1.json', 'original_policy': 'original_unsealed_json', 'relative_path': 'original-custody/lanl-detached-E-default-launch-original-20261008-a1.json', 'sha256': '4267f114bb9891dfb6a7e62052629cbe5f59fe70cbd090a51bc94edbea4f3d72'}, {'bytes': 0, 'group': 'failed_inspection_and_original_custody', 'original_path': '/private/tmp/lanl-detached-E-default-launch-original-20261008-a1.stderr', 'original_policy': 'opaque_original_bytes', 'relative_path': 'original-custody/lanl-detached-E-default-launch-original-20261008-a1.stderr', 'sha256': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}, {'bytes': 15359, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17_detach_passive_observer_administration_20261008_a1_r2.py', 'original_policy': 'opaque_original_bytes', 'relative_path': 'reviewed-source-history/lanl17_detach_passive_observer_administration_20261008_a1_r2.py', 'sha256': 'f303c3b6a3ef909224d6c693b846b47f5755f587bc105acea0dfac3c9e504405'}, {'bytes': 828, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17-detached-passive-observer-administration-r2-complete-r1-derivation-20261008.diff', 'original_policy': 'opaque_original_bytes', 'relative_path': 'reviewed-source-history/lanl17-detached-passive-observer-administration-r2-complete-r1-derivation-20261008.diff', 'sha256': '08b20a02716432ed941a895e528d6a37da11adff37cc28f9d1d6a3e4e1b8893e'}, {'bytes': 3633, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17-detached-passive-observer-administration-r2-source-handoff-20261008.md', 'original_policy': 'opaque_original_bytes', 'relative_path': 'reviewed-source-history/lanl17-detached-passive-observer-administration-r2-source-handoff-20261008.md', 'sha256': 'cad2049b33f65608bea5032c5afe2d57f0957c1337bd801733dd63d0f7db5a32'}, {'bytes': 1440, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17-detached-passive-observer-administration-r2-source-comparison-20261008.json', 'original_policy': 'original_unsealed_json', 'relative_path': 'reviewed-source-history/lanl17-detached-passive-observer-administration-r2-source-comparison-20261008.json', 'sha256': 'b06ab8559762d9f4a31377128d5086f7fdbbc6cf94c4da184a6112db86b8cad5'}, {'bytes': 3260, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17-detached-passive-observer-r2-independent-source-review-20261008.md', 'original_policy': 'opaque_original_bytes', 'relative_path': 'reviewed-source-history/lanl17-detached-passive-observer-r2-independent-source-review-20261008.md', 'sha256': '6202ae5d737adf896d33533e800d66e29512a888b190a9709e4433636e4341eb'}, {'bytes': 23849, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17_detach_exact_R4_storage_administration_20261008_a1_r1.py', 'original_policy': 'opaque_original_bytes', 'relative_path': 'reviewed-source-history/lanl17_detach_exact_R4_storage_administration_20261008_a1_r1.py', 'sha256': 'af93b23d2cbee7caaa8dd0199b3cb6f425fe91a2df840444c6f09641232a87eb'}, {'bytes': 20322, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17-detached-R4-administration-r1-complete-EwrapperR2-derivation-20261008.diff', 'original_policy': 'opaque_original_bytes', 'relative_path': 'reviewed-source-history/lanl17-detached-R4-administration-r1-complete-EwrapperR2-derivation-20261008.diff', 'sha256': '8dc857a2e93ce440bcd2b0d626995e3a9dc136940f239c1a19065a8ad6615e1f'}, {'bytes': 8656, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17-detached-R4-administration-r1-source-handoff-20261008.md', 'original_policy': 'opaque_original_bytes', 'relative_path': 'reviewed-source-history/lanl17-detached-R4-administration-r1-source-handoff-20261008.md', 'sha256': '67dd75f611c88b39463782f6ca6c077dad85959a5c4583f09676fa4afcde6daa'}, {'bytes': 2782, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17-detached-R4-administration-r1-source-comparison-20261008.json', 'original_policy': 'original_unsealed_json', 'relative_path': 'reviewed-source-history/lanl17-detached-R4-administration-r1-source-comparison-20261008.json', 'sha256': 'aadde1a3d9701e699ffe84e9df0ba0d4e415f6b8e574d7f9405c126d788a612b'}, {'bytes': 7426, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17-detached-R4-administration-r1-independent-source-review-20261008.md', 'original_policy': 'opaque_original_bytes', 'relative_path': 'reviewed-source-history/lanl17-detached-R4-administration-r1-independent-source-review-20261008.md', 'sha256': 'd3b3d619cb37d0405018a29b25f167b5cbf4f14c5794086a6a36b798edd2f368'}, {'bytes': 24000, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17_detach_exact_R4_storage_administration_20261008_a1_r2.py', 'original_policy': 'opaque_original_bytes', 'relative_path': 'reviewed-source-history/lanl17_detach_exact_R4_storage_administration_20261008_a1_r2.py', 'sha256': 'deb59a340c92892336282f85697158b7b1181a33a288201fe6e2746c15c9a9be'}, {'bytes': 816, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17-detached-R4-administration-r2-complete-r1-derivation-20261008.diff', 'original_policy': 'opaque_original_bytes', 'relative_path': 'reviewed-source-history/lanl17-detached-R4-administration-r2-complete-r1-derivation-20261008.diff', 'sha256': 'e0bd89a2fb0dcd8d575b05ea0b5ebff2d3ee94bcc04ee34b7da95eca60f12aba'}, {'bytes': 3706, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17-detached-R4-administration-r2-source-handoff-20261008.md', 'original_policy': 'opaque_original_bytes', 'relative_path': 'reviewed-source-history/lanl17-detached-R4-administration-r2-source-handoff-20261008.md', 'sha256': '68526f64844d0e0b2a71c110e98e5c094fa9a91b93e58814f27d6e5209f11e56'}, {'bytes': 1334, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17-detached-R4-administration-r2-source-comparison-20261008.json', 'original_policy': 'original_unsealed_json', 'relative_path': 'reviewed-source-history/lanl17-detached-R4-administration-r2-source-comparison-20261008.json', 'sha256': '6227828e2e5a47adcc01eb51f89d34ff394034f1168674500f87713c36838707'}, {'bytes': 2967, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17-detached-R4-administration-r2-independent-source-review-20261008.md', 'original_policy': 'opaque_original_bytes', 'relative_path': 'reviewed-source-history/lanl17-detached-R4-administration-r2-independent-source-review-20261008.md', 'sha256': '73817a23522645e6593748c9d79f6d47b1971e7b4b9cb0047dc662c9c9a77b6f'}, {'bytes': 3385, 'group': 'reviewed_source_history', 'original_path': '/private/tmp/lanl17-passive-raw-hash-scope-and-plan-seam-source-note-20261008-a1.md', 'original_policy': 'opaque_original_bytes', 'relative_path': 'reviewed-source-history/lanl17-passive-raw-hash-scope-and-plan-seam-source-note-20261008-a1.md', 'sha256': '9326f483faa66cadd2717710356b02268268f760c17d4c5b68085de9d11efde3'}]

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
    return json.loads(raw, object_pairs_hook=pairs,
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

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-head', required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--worktree', default=str(DEFAULT_W))
    parser.add_argument('--extension-inventory')
    parser.add_argument('--extension-inventory-sha256')
    args = parser.parse_args()
    deadline = time.monotonic() + SECONDS
    os.umask(0o077)
    require(re.fullmatch('[0-9a-f]{40}', args.expected_head), 'exact_parent_supplied_HEAD40')
    require(re.fullmatch('[0-9a-f]{64}', args.source_sha256), 'own_source_SHA64')
    require(bool(args.extension_inventory) == bool(args.extension_inventory_sha256), 'paired_extension_arguments')
    own = P(__file__).absolute()
    own_raw, own_stat = read(own, MAX_FILE, deadline)
    require(sha(own_raw) == args.source_sha256, 'own_source_pin')
    w = route(P(args.worktree))
    require(w == DEFAULT_W and w.is_dir(), 'fixed_owned_archive_worktree')
    require(git(w, deadline, 'rev-parse', 'HEAD').decode().strip() == args.expected_head
            and git(w, deadline, 'branch', '--show-current').decode().strip() == 'codex/lanl-analytic-eval'
            and not git(w, deadline, 'status', '--porcelain'), 'expected_clean_parent_worktree')
    before_tree = git(w, deadline, 'ls-tree', '-r', '-z', 'HEAD')
    originals = [dict(row) for row in FIXED]
    extension_pin = None
    if args.extension_inventory:
        require(re.fullmatch('[0-9a-f]{64}', args.extension_inventory_sha256), 'extension_SHA64')
        ext_path = route(P(args.extension_inventory))
        require(ext_path.parent == P('/private/tmp'), 'private_explicit_extension_metadata')
        raw, s = read(ext_path, 256 * 1024, deadline)
        require(sha(raw) == args.extension_inventory_sha256, 'extension_metadata_pin')
        extra = strict(raw)
        # This is only an archival list, not a receipt, plan, admission or review.
        require(isinstance(extra, list) and 1 <= len(extra) <= MAX_EXTRA, 'explicit_extension_list')
        for row in extra:
            allowed = {'original_path', 'relative_path', 'bytes', 'sha256', 'original_policy',
                       'original_canonical_ensure_ascii'}
            require(isinstance(row, dict) and set(row) <= allowed
                    and {'original_path', 'relative_path', 'bytes', 'sha256', 'original_policy'} <= set(row),
                    'extension_row_fields')
            require(row['relative_path'].startswith('corrected-source-package/'), 'separate_correction_package')
            originals.append(dict(row, group='explicit_parent_reviewed_correction_originals'))
        extension_pin = {'path': str(ext_path), 'bytes': len(raw), 'sha256': sha(raw),
                         'original_policy': 'original_unsealed_archival_list', 'stat': list(s)}
    seen_paths, seen_names = set(), set()
    materialized = []
    total = 0
    for row in originals:
        rel = P(row['relative_path'])
        require(not rel.is_absolute() and '..' not in rel.parts and str(rel) == row['relative_path']
                and re.fullmatch('[A-Za-z0-9_./-]+', str(rel)), 'closed_relative_archive_path')
        p = route(P(row['original_path']))
        require(p.is_relative_to(P('/private/tmp')) and str(p) not in seen_paths
                and str(rel) not in seen_names, 'original_path_scope_or_duplicate')
        require(type(row['bytes']) is int and 0 <= row['bytes'] <= MAX_FILE
                and re.fullmatch('[0-9a-f]{64}', row['sha256']), 'explicit_original_size_SHA')
        seen_paths.add(str(p)); seen_names.add(str(rel))
        total += row['bytes']; require(total <= MAX_TOTAL, 'cumulative_archive_original_bound')
        raw, s = read(p, MAX_FILE, deadline)
        validate_pin(row, raw)
        materialized.append((row, raw, s))
    status = strict(next(raw for row, raw, _ in materialized if row['relative_path'] == 'failed-originals/status.json'))
    require(status['state'] == 'guard_refused_or_failed' and status['guard_exit_code'] == 1
            and status['remove_requested'] is False and status['scientific_admission'] is False,
            'original_failed_default_inspection_boundary')
    dest = w / REL
    route(dest.parent)
    require(dest.parent.is_dir() and not os.path.lexists(dest), 'fresh_archive_destination')
    dest.mkdir(mode=0o700)
    pins = []
    try:
        for row, raw, s in materialized:
            out = dest / row['relative_path']
            out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            write_original(out, raw)
            pins.append(dict(row, archive_path=REL + '/' + row['relative_path']))
        # Recheck original returned bytes and source after copying, not only hashes of metadata.
        for row, old_raw, old_stat in materialized:
            later, s = read(P(row['original_path']), MAX_FILE, deadline)
            require(later == old_raw and s == old_stat, 'original_changed_during_archive')
        later, s = read(own, MAX_FILE, deadline)
        require(later == own_raw and s == own_stat, 'archiver_source_changed')
        if extension_pin:
            later, s = read(P(extension_pin['path']), 256 * 1024, deadline)
            require(sha(later) == extension_pin['sha256'] and list(s) == extension_pin['stat'], 'extension_changed')
        require(git(w, deadline, 'rev-parse', 'HEAD').decode().strip() == args.expected_head
                and git(w, deadline, 'ls-tree', '-r', '-z', 'HEAD') == before_tree
                and not git(w, deadline, 'diff', '--name-only', 'HEAD'), 'prior_tracked_tree_or_HEAD_changed')
        manifest = {'format': 'swdb.detached-E-failure-and-reviewed-source-byte-custody.v1',
                    'canonical_ensure_ascii': True,
                    'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'parent_commit': args.expected_head, 'archive': REL,
                    'archiver_source_pin': {'path': str(own), 'bytes': len(own_raw), 'sha256': sha(own_raw)},
                    'fixed_original_count': len(FIXED), 'extension_inventory_pin': extension_pin,
                    'originals': pins, 'original_count': len(pins), 'original_bytes': total,
                    'original_failed_inspection': {'guard_exit_code': 1, 'remove_requested': False,
                                                  'started_utc': status['started_utc'], 'ended_utc': status['ended_utc']},
                    'source_extension_pending': extension_pin is None,
                    'archival_invokes_selected_control_mains': False,
                    'archive_supplies_cleanup_capacity_plan_or_scientific_admission': False,
                    'prior_tracked_tree_SHA256': sha(before_tree),
                    'scope': 'Byte custody only; original policies and creation-time NOTRUN labels preserved. Actual failed default custody is separate from prospective corrected sources.'}
        manifest['identity_sha256'] = sha(canonical(manifest))
        manifest_raw = (json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()
        write_original(dest/'manifest.json', manifest_raw)
        readme = ('# Failed detached E inspection and reviewed source custody\n\n'
                  'The original detached default inspection ran on 2026-10-07 at 23:11 ET (original machine custody 03:11:16–17 UTC on 2026-10-08) and returned guard exit 1 with removal not requested. Its stdout was empty; original stderr reports `original raw root`. This archive supplies neither removal nor plan/capacity/scientific admission. Later events remain separate.\n\n'
                  'The eight remote originals, exact local decoding custody, original launch/namespace/sidecar observations, and their reader/collector/decoder sources are copied unchanged. The base64 transfer packet is not duplicated; original local-custody retains its exact packet pin. Namespace top-level size/allocation metadata is not recursive RAW volume or source clearance. The sidecar observation is original unsealed metadata, not a rewritten lane receipt.\n\n'
                  'Reviewed passive R2 and detached R4 R1/R2 source/diff/handoff/static-review originals retain their immutable creation-time SOURCE ONLY / NOT RUN statements. Their presence proves byte custody and source review only. The corrected-source-package, if explicitly supplied by the parent after review, is separately listed; its absent extension remains pending. No selected source was imported or invoked by this archiver.\n\n'
                  'Only this manifest uses a new explicit canonical True whole-object-minus-identity custody seal. Original unsealed JSON, opaque streams and any explicitly supplied original seal policy are preserved byte for byte. This source archiver does not commit, push, edit an issue, modify an existing file or conduct a remote action. Parent owns archive execution, subsequent issue history, review and delivery.\n')
        write_original(dest/'README.md', readme.encode())
        require(git(w, deadline, 'status', '--porcelain').decode().splitlines() == ['?? ' + REL + '/'],
                'archive_only_untracked_scope')
        require(git(w, deadline, 'rev-parse', 'HEAD').decode().strip() == args.expected_head
                and git(w, deadline, 'ls-tree', '-r', '-z', 'HEAD') == before_tree
                and not git(w, deadline, 'diff', '--name-only', 'HEAD'), 'final_parent_tree_changed')
        print(json.dumps({'archive': REL, 'expected_head': args.expected_head, 'originals': len(pins),
                          'original_bytes': total, 'new_files': len(pins) + 2,
                          'manifest_identity_sha256': manifest['identity_sha256'],
                          'manifest_bytes': len(manifest_raw), 'manifest_sha256': sha(manifest_raw),
                          'README_bytes': len(readme.encode()), 'README_sha256': sha(readme.encode()),
                          'corrected_source_extension_pending': extension_pin is None,
                          'no_selected_main_or_remote_action': True}, sort_keys=True))
    except BaseException:
        # Retain original copied partials for parent inspection; never remove/retry them.
        raise

if __name__ == '__main__':
    main()
