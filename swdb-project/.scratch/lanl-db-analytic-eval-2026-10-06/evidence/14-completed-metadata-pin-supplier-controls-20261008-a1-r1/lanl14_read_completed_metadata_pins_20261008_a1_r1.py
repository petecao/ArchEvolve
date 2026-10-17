"""Prospective read-only completed14 pin supplier. SOURCE ONLY; NOT RUN.

Reuse only the exact returned ee12a module bytes with __name__ != __main__.
No correction main/fchmod/output_root/journal, scientific CLI, Store, file output,
report/YAML body parsing/transfer, permission change or source normalization.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import sys
import time
from types import ModuleType, SimpleNamespace

UID = 114316761
PRIMARY = Path('/data1/yanruj/ArchEvolve')
MEMACC = Path('/data1/yanruj/Memacc-repro-20260925')
WRAPPER_REL = 'AgenticRefiner/scripts/host/socket_lane.sh'
RAW = Path('/data/yanruj/EvolveSWDB_runs/lanl-generality-final-20261007-a1')
SOURCE = Path('/data1/yanruj/ArchEvolve-lanl-generality-final-20261007-a1')
RELATIVE_HELPER = 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/14-completed-report-transfer-mode-controls-20261008-a1/lanl14_correct_completed_report_transfer_modes_20261008_a1.py'
HELPER = PRIMARY / RELATIVE_HELPER
HELPER_BYTES = 29985
HELPER_SHA = 'ee12a535ea2c3e6976c920f483c72e8367cd36ec311bf26585137023a2d29ec7'
C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
R14 = 'c4ab2fdbb0b0c57ee9f515522835897f24466d6b'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
NATIVE = {
    '/usr/bin/python3.12': (8020928, 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'),
    '/usr/bin/git': (4019024, '06b2aa74919b1993f9fd7e47060ea98d98c27206f16ccc2d35f51ced7e7877eb'),
}
STABLE = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
MAX_RETURN = 64 * 1024
MAX_SELF = 64 * 1024
MAX_BOOT_READ = 128 * 1024 * 1024


class Refused(RuntimeError):
    pass


def require(value, reason):
    if not value:
        raise Refused(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def stamp(value):
    return {name: getattr(value, name) for name in STABLE}


class BootBudget:
    def __init__(self, seconds):
        require(type(seconds) is int and 60 <= seconds <= 3600, 'explicit metadata deadline outside60..3600')
        self.deadline = time.monotonic() + seconds
        self.bytes_read = 0

    def check(self):
        require(time.monotonic() < self.deadline, 'metadata deadline exhausted')

    def consume(self, count):
        self.check()
        self.bytes_read += count
        require(self.bytes_read <= MAX_BOOT_READ, 'bootstrap read cap exceeded')


def checked(path, *, owner, directory=False):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and len(str(path)) <= 4096,
            'canonical fixed source path required')
    require(not any(p.is_symlink() for p in (path, *path.parents))
            and path.resolve(strict=True) == path, 'symlink or redirected path refused')
    status = path.lstat()
    require(status.st_uid == owner and
            (stat.S_ISDIR(status.st_mode) if directory else stat.S_ISREG(status.st_mode)),
            'source owner/type differs')
    if not directory:
        require(status.st_nlink == 1, 'single-link file required')
    return path, status


def boot_read(path, maximum, budget, *, owner=UID, expected=None, retain=False):
    path, before = checked(path, owner=owner)
    require(0 < before.st_size <= maximum, 'bootstrap file size bound differs')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        require(stamp(os.fstat(fd)) == stamp(before), 'bootstrap FD identity differs')
        blocks, count, digest = [], 0, hashlib.sha256()
        while True:
            budget.check()
            block = os.read(fd, min(1024 * 1024, maximum - count + 1))
            if not block:
                break
            count += len(block)
            budget.consume(len(block))
            require(count <= maximum, 'bootstrap returned bytes exceed cap')
            digest.update(block)
            if retain:
                blocks.append(block)
        require(count == before.st_size and stamp(os.fstat(fd)) == stamp(before) == stamp(path.lstat()),
                'bootstrap source/FD changed')
        pin = {'path': str(path), 'bytes': count, 'sha256': digest.hexdigest(), 'stat': stamp(before)}
        require(expected is None or pin['sha256'] == expected, 'bootstrap returned-byte pin differs')
        return pin, b''.join(blocks) if retain else None
    finally:
        os.close(fd)


def privacy_roots():
    result = {}
    for path in (Path('/data1/yanruj'), Path('/data/yanruj')):
        path, observed = checked(path, owner=UID, directory=True)
        require(stat.S_IMODE(observed.st_mode) == 0o700, 'literal private root differs')
        result[str(path)] = stamp(observed)
    return result


def stable_roots(before):
    after = privacy_roots()
    # No output/removal occurs here, so the complete root observations must stay exact.
    require(after == before, 'private roots changed during metadata read')
    return after


def primary_git(*tail, budget):
    budget.check()
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C',
           'GIT_OPTIONAL_LOCKS': '0', 'GIT_NO_LAZY_FETCH': '1', 'GIT_TERMINAL_PROMPT': '0',
           'GIT_PAGER': 'cat', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'}
    child = subprocess.run(['/usr/bin/git', '-c', 'core.fsmonitor=false', '-C', str(PRIMARY), *tail],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=min(25, budget.deadline - time.monotonic()), env=env)
    require(child.returncode == 0 and not child.stderr and len(child.stdout) <= 8 * 1024 * 1024,
            'fixed readonly primary Git refused; prose omitted')
    return child.stdout


def primary_binding(expected, helper_raw, budget):
    checked(PRIMARY, owner=UID, directory=True)
    head = primary_git('rev-parse', 'HEAD', budget=budget).decode().strip()
    require(head == expected and re.fullmatch('[0-9a-f]{40}', head), 'expected delivered primary HEAD differs')
    upstream = primary_git('rev-parse', 'refs/remotes/origin/yanrujhou_main', budget=budget).decode().strip()
    branch = primary_git('branch', '--show-current', budget=budget).decode().strip()
    require(upstream == expected and branch == 'yanrujhou_main', 'delivered primary YANMAIN/branch differs')
    integration = primary_git('for-each-ref', '--format=%(objectname)',
                              'refs/remotes/origin/codex/lanl-analytic-eval', budget=budget).decode().strip()
    require(not integration or re.fullmatch('[0-9a-f]{40}', integration), 'observed integration ref shape differs')
    entry = primary_git('ls-files', '--stage', '--', RELATIVE_HELPER, budget=budget).decode().strip().split()
    oid = hashlib.sha1(b'blob ' + str(len(helper_raw)).encode() + b'\0' + helper_raw).hexdigest()
    require(entry == ['100644', oid, '0', RELATIVE_HELPER]
            and primary_git('rev-parse', 'HEAD:' + RELATIVE_HELPER, budget=budget).decode().strip() == oid,
            'reviewed helper committed/index Git mode/blob differs')
    return {'HEAD': head, 'branch': branch, 'origin_yanrujhou_main': upstream,
            'observed_origin_integration': integration or None,
            'integration_ref_scope': 'Observation only; primary delivery fetches YANMAIN, not an integration freshness claim.',
            'helper_Git_mode': '100644', 'helper_Git_blob': oid}


def load_reviewed_helper(budget, expected_primary):
    require(sys.platform == 'linux' and socket.gethostname().split('.')[0] == 'mbit10'
            and os.getuid() == os.geteuid() == UID, 'native own Linux mbit10 required before import')
    require(sys.flags.dont_write_bytecode == 1 and sys.flags.optimize == 0
            and Path(sys.executable).resolve(strict=True) == Path('/usr/bin/python3.12'),
            'pinned native Python -B required before import')
    roots = privacy_roots()
    native = {}
    for path, (size, digest) in NATIVE.items():
        pin, raw = boot_read(path, 128 * 1024 * 1024, budget, owner=0, expected=digest, retain=True)
        require(pin['bytes'] == size and raw[:6] == b'\x7fELF\x02\x01'
                and int.from_bytes(raw[18:20], 'little') == 62
                and not pin['stat']['st_mode'] & 0o022 and pin['stat']['st_mode'] & 0o111,
                'fixed native root-owned x86_64 ELF differs')
        native[path] = pin
    helper_pin, returned = boot_read(HELPER, HELPER_BYTES, budget, expected=HELPER_SHA, retain=True)
    require(helper_pin['bytes'] == HELPER_BYTES and stat.S_IMODE(helper_pin['stat']['st_mode']) == 0o644,
            'direct durable helper size/physical0644 differs')
    primary = primary_binding(expected_primary, returned, budget)
    stable_roots(roots)
    module = ModuleType('lanl14_original_ee12a_readonly_supplier_helpers')
    module.__file__ = str(HELPER)
    # Returned bytes above, not a second path loader; __name__ never __main__.
    exec(compile(returned, str(HELPER), 'exec'), module.__dict__)
    require(module.__name__ != '__main__' and module.UID == UID and module.SOURCE == SOURCE
            and module.RAW == RAW and module.C == C and module.R14 == R14 and module.F6 == F6
            and module.MAX_JSON == 8 * 1024 * 1024
            and module.MAX_REPORT == 1024 * 1024 * 1024 and module.MAX_OTHER == 100 * 1024 * 1024
            and module.NATIVE == NATIVE, 'exact original helper contract differs')
    return module, helper_pin, returned, roots, native, primary


def wrapper_git(*tail, budget):
    budget.check()
    checked(MEMACC, owner=UID, directory=True)
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C',
           'GIT_OPTIONAL_LOCKS': '0', 'GIT_NO_LAZY_FETCH': '1', 'GIT_TERMINAL_PROMPT': '0',
           'GIT_PAGER': 'cat', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null'}
    child = subprocess.run(['/usr/bin/git', '-c', 'core.fsmonitor=false', '-C', str(MEMACC), *tail],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=min(25, budget.deadline - time.monotonic()), env=env)
    require(child.returncode == 0 and not child.stderr and len(child.stdout) <= 8 * 1024 * 1024,
            'fixed readonly wrapper Git refused; prose omitted')
    return child.stdout


def wrapper_binding(h, manifest, budget):
    wrapper = MEMACC / WRAPPER_REL
    require(manifest['wrapper']['path'] == str(wrapper), 'original manifest wrapper route differs')
    expected = h.sha_syntax(manifest['wrapper']['sha256'])
    observed = wrapper_git('rev-parse', 'refs/remotes/origin/yanrujhou_main', budget=budget).decode().strip()
    require(re.fullmatch('[0-9a-f]{40}', observed), 'actual wrapper upstream40 required')
    pin, returned = h.read_file(wrapper, h.MAX_JSON, budget, expected, True)
    committed = wrapper_git('show', observed + ':' + WRAPPER_REL, budget=budget)
    require(returned == committed, 'manifest wrapper bytes differ from observed upstream blob')
    entry = wrapper_git('ls-tree', '-z', observed, '--', WRAPPER_REL, budget=budget).split(b'\0')
    require(len(entry) == 2 and not entry[1], 'exact wrapper Git entry required')
    meta, path = entry[0].split(b'\t', 1)
    mode, kind, oid = meta.decode().split()
    actual_oid = hashlib.sha1(b'blob ' + str(len(returned)).encode() + b'\0' + returned).hexdigest()
    require(path.decode() == WRAPPER_REL and kind == 'blob' and mode in ('100644', '100755')
            and oid == actual_oid, 'actual wrapper Git blob/mode differs')
    require(h.stamp(wrapper.lstat()) == pin['stat'], 'actual wrapper stat changed')
    return {'upstream_commit': observed, 'file': pin,
            'mode_octal': oct(stat.S_IMODE(pin['stat']['st_mode'])),
            'Git_mode': mode, 'Git_blob': oid,
            'scope': 'Actual local origin/YANMAIN40 observed and original manifest byte-bound; no fetch or remote/latest freshness claim.'}


def selected_stats(h, rows, budget):
    result = []
    for row in rows:
        budget.check()
        path = h.checked(row['path'])
        value = path.lstat()
        require(0 < value.st_size <= row['maximum'] and not value.st_mode & 0o7000,
                'selected original size/special mode differs')
        record = {'path': str(path), 'kind': row['kind'], 'bytes': value.st_size,
                  'mode_octal': oct(stat.S_IMODE(value.st_mode)), 'stat': h.stamp(value),
                  'declared_original_file_sha256': row['expected_sha256']}
        if 'id' in row:
            record['id'] = row['id']
            record['file_SHA_scope'] = 'Original exact request/acceptance pin inherited; YAML bytes not opened or parsed by supplier.'
        else:
            record['file_SHA_scope'] = 'Independently streamed report/Markdown bytes, or exact original request JSON bytes.'
        result.append(record)
        require(h.stamp(path.lstat()) == record['stat'], 'selected stat changed during observation')
    require(len(result) == 21, 'original21 current-stat set differs')
    return result


def run(args):
    boot = BootBudget(args.deadline_s)
    own = Path(__file__).absolute()
    own_pin, _ = boot_read(own, MAX_SELF, boot)
    require(stat.S_IMODE(own_pin['stat']['st_mode']) == 0o644 and not own.is_relative_to(RAW)
            and not own.is_relative_to(SOURCE), 'own reviewed source0644/outside originals required')
    h, helper_pin, helper_raw, roots, native_before, primary_before = load_reviewed_helper(boot, args.expected_primary)
    budget = h.Budget(args.deadline_s)
    budget.deadline = boot.deadline
    budget.bytes_read = boot.bytes_read
    native_pins = h.native(budget)
    require(native_pins == native_before, 'native original helper/bootstrap facts differ')
    source_before = h.source_identity(budget)
    leases_before = h.released(budget)
    directory_before = {}
    for directory in (RAW, RAW / 'report'):
        h.checked(directory, True)
        directory_before[str(directory)] = h.stamp(directory.lstat())
    manifest, mp = h.read_json(RAW / 'manifest.json', budget, sealed=True)
    accept, ap = h.read_json(RAW / 'control/acceptance.json', budget, sealed=True)
    request, rp = h.read_json(RAW / 'report-request.json', budget, sealed=True)
    protected, pp = h.read_json(RAW / 'protected.json', budget, sealed=True)
    vp, _ = h.read_file(RAW / 'final-validate.stdout', h.MAX_JSON, budget)
    report_pin, _ = h.read_file(RAW / 'report/report.json', h.MAX_REPORT, budget, retain=False)
    md_pin, _ = h.read_file(RAW / 'report/report.md', h.MAX_OTHER, budget, retain=False)
    # This semantic identity is inherited from the original sealed acceptance.
    report_identity = h.sha_syntax(accept['report_sha256'])
    derived = SimpleNamespace(manifest_file_sha256=mp['sha256'], manifest_identity_sha256=manifest['identity_sha256'],
        acceptance_file_sha256=ap['sha256'], acceptance_identity_sha256=accept['identity_sha256'],
        request_file_sha256=rp['sha256'], request_identity_sha256=request['identity_sha256'],
        protected_file_sha256=pp['sha256'], final_validation_file_sha256=vp['sha256'],
        report_file_sha256=report_pin['sha256'], report_identity_sha256=report_identity,
        markdown_file_sha256=md_pin['sha256'], report_bytes=report_pin['bytes'], markdown_bytes=md_pin['bytes'])
    original_manifest, original_accept, original_request, original_protected, inputs = h.completion(derived, budget)
    require((original_manifest, original_accept, original_request, original_protected) ==
            (manifest, accept, request, protected), 'original returned metadata changed')
    wrapper_before = wrapper_binding(h, original_manifest, budget)
    rows = h.subjects(derived, original_accept, original_request, original_protected)
    observed_before = selected_stats(h, rows, budget)
    require(len(rows) == 21 and len([r for r in rows if r['kind'] in ('protocol', 'estimate')]) == 18,
            'actual all9/18 subject set differs')
    # Stream report/Markdown once more to prove unchanged byte identity, no JSON/report parse.
    require(h.read_file(RAW / 'report/report.json', h.MAX_REPORT, budget, report_pin['sha256'])[0] == report_pin
            and h.read_file(RAW / 'report/report.md', h.MAX_OTHER, budget, md_pin['sha256'])[0] == md_pin,
            'original report/Markdown streamed byte identity changed')
    _, _, _, _, final_inputs = h.completion(derived, budget)
    require(final_inputs == inputs and h.source_identity(budget) == source_before
            and h.released(budget) == leases_before, 'final original completion/source/leases differ')
    require(selected_stats(h, rows, budget) == observed_before, 'original21 stat/mode set changed')
    require(h.native(budget) == native_pins, 'native pins changed')
    require(wrapper_binding(h, original_manifest, budget) == wrapper_before,
            'observed wrapper upstream/bytes/stat changed during metadata read')
    final_helper, final_returned = boot_read(HELPER, HELPER_BYTES, budget, expected=HELPER_SHA, retain=True)
    require(final_helper == helper_pin and final_returned == helper_raw
            and primary_binding(args.expected_primary, final_returned, budget) == primary_before,
            'reviewed helper bytes/primary changed')
    require(h.read_file(own, MAX_SELF, budget, own_pin['sha256'])[0] == own_pin, 'own source changed')
    root_after = stable_roots(roots)
    require({str(p): h.stamp(h.checked(p, True).lstat()) for p in (RAW, RAW / 'report')}
            == directory_before, 'actual raw/report directory identity/mode changed')
    actual_raw = {str(p): {'path': str(p), 'mode_octal': oct(stat.S_IMODE(p.lstat().st_mode)),
                           'stat': h.stamp(p.lstat())} for p in (RAW, RAW / 'report')}
    result = {'format': 'swdb.lanl14-completed-readonly-metadata-pins.v1', 'sealed': False,
        'source_only_preparation': False, 'read_only_actual_metadata': True, 'scientific_admission': False,
        'guard_or_permission_actions': 0, 'report_body_parsed_or_transferred': False,
        'YAML_bodies_opened_parsed_or_transferred': False, 'native_scientific_CLI_Store_creation': False,
        'manifest': {'file': mp, 'original_identity_sha256': manifest['identity_sha256'], 'original_policy': 'True'},
        'acceptance': {'file': ap, 'original_identity_sha256': accept['identity_sha256'], 'original_policy': 'True'},
        'request': {'file': rp, 'original_identity_sha256': request['identity_sha256'], 'original_policy': 'True'},
        'protected': {'file': pp, 'original_identity_sha256': protected['identity_sha256'], 'original_policy': 'True'},
        'validation': vp, 'original_completion_inputs': inputs,
        'report': {'file': report_pin, 'semantic_identity_sha256': report_identity,
                   'semantic_identity_scope': 'EXPLICITLY INHERITED original acceptance.report_sha256; report body never parsed.'},
        'Markdown': {'file': md_pin}, 'exact_derived_args': vars(derived),
        'ordered_nine_pairs': [{'kernel': row['kernel'], 'target': row['target']} for row in request['pairs']],
        'new_canonical_count': 18, 'prior_canonical_count': 686, 'completed_raw_canonical_count': 704,
        'original21_current_modes_and_stats': observed_before, 'raw_report_directories': actual_raw,
        'source': source_before, 'C': C, 'R14': R14, 'F6': F6,
        'native': native_pins, 'released_authoritative_leases': leases_before,
        'primary_fixed_native_Git_observed40': primary_before,
        'wrapper_upstream_commit': wrapper_before['upstream_commit'],
        'wrapper_fixed_native_Git_observation': wrapper_before, 'own_source': own_pin,
        'imported_original_helper': helper_pin, 'import_scope': 'Exact returned ee12a bytes, __main__ false; only readonly native/source/completion/subjects/released/read primitives called.',
        'literal_private_roots_before': roots, 'literal_private_roots_after': root_after,
        'inherited_completion': {'wrapper_runner': '0 verified by unchanged completion',
                                'generation': 510, 'node': 0, 'ended_and_empty_owned_cleanup': 'Verified by unchanged completion; not reconstructed or rewritten'},
        'requested_deadline_s': args.deadline_s, 'streamed_bytes_read': budget.bytes_read,
        'administrative_limit_scope': 'Unchanged ee12a read/file/deadline limits; compact return64KiB. No scientific caps changed.'}
    returned = (json.dumps(result, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False) + '\n').encode()
    require(len(returned) <= MAX_RETURN, 'compact metadata return exceeds64KiB')
    # Final write is one compact stdout metadata object; no disk/body output or retry.
    sys.stdout.buffer.write(returned)
    sys.stdout.buffer.flush()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--deadline-s', required=True, type=int)
    parser.add_argument('--expected-primary', required=True)
    args = parser.parse_args()
    require(re.fullmatch('[0-9a-f]{40}', args.expected_primary), 'explicit actual expected primary40 required')
    run(args)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as failure:
        # Never exception prose, environment, raw source/body or captured native Git streams.
        print(json.dumps({'format': 'swdb.lanl14-completed-readonly-metadata-pins-refusal.v1',
                          'failure_type': type(failure).__name__, 'scientific_admission': False,
                          'guard_or_permission_actions': 0, 'sealed': False}, sort_keys=True))
        raise SystemExit(2)
