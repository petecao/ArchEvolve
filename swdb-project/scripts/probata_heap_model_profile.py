"""Coordinator-only first public heap-model profile; created 2026-10-16 ET.

This entry is not an admission or watchdog. Actual mode requires the external
one-worker 8 GiB process-tree watchdog and exact reviewed source/tool admission.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--mode', choices=('controls', 'actual-wp'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=4200)
    parser.add_argument('--public-timeout-seconds', type=int, default=1800)
    parser.add_argument('--member', choices=('std_vector_int_ctor_count',),
                        help='run only the separately reviewed original zero-initializing count model')
    args = parser.parse_args()
    if not 1 <= args.public_timeout_seconds <= 3600 or not 1 <= args.seconds <= 21600:
        parser.error('unsupported profile budget')
    expected_records = 1 if args.member else 2
    if args.mode == 'actual-wp' and args.seconds < expected_records * args.public_timeout_seconds + 120:
        parser.error('whole profile must cover every selected public command plus setup/cleanup margin')
    project = Path(__file__).resolve().parents[1]
    repo = project.parent
    def source_check():
        head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain', '--untracked-files=all'], text=True)
        if head != args.expected_commit or dirty:
            raise SystemExit('the admitted source commit is not exact and clean')
    source_check()
    output = args.output.resolve()
    if output.is_relative_to(repo):
        parser.error('raw output must be outside source checkout')
    output.mkdir(parents=True, exist_ok=False)
    names = ('swdb/heap_model_view.py', 'swdb/heap_model_packets.py', 'swdb/heap_model_vcs.py',
             'swdb/heap_bridge.mlw', 'swdb/heap_model_environment.ml', 'swdb/wp_adapter.py',
             'swdb/proof_setup.py', 'swdb/std_models.py', 'tests/test_heap_model_view.py',
             'scripts/probata_heap_model_profile.py', 'schemas/proof.schema.json', 'pyproject.toml')
    pins = {name: hashlib.sha256((project / name).read_bytes()).hexdigest() for name in names}
    selection = 'tests/test_heap_model_view.py'
    if args.mode == 'actual-wp':
        selection += ('::test_actual_public_original_count_model' if args.member
                      else '::test_actual_public_first_pair_heap_models')
    command = [sys.executable, '-m', 'pytest', '-q', '-x', '-p', 'no:cacheprovider', selection,
               '--basetemp=' + str(output / 'pytest'), '--junitxml=' + str(output / 'junit.xml')]
    profile = {'source_commit': args.expected_commit, 'mode': args.mode, 'source_sha256': pins,
               'command': command, 'public_timeout_seconds': args.public_timeout_seconds,
               'prospective_whole_seconds': args.seconds, 'required_external_rss_cap_bytes': 8589934592,
               'actual_expected_records': expected_records if args.mode == 'actual-wp' else 0,
               'positive_target_counts': ({args.member: 27} if args.member else
                   {'std_vector_int_ctor_count_value': 27, 'std_vector_int_dtor': 11}),
               'scope': 'fresh selected original public c_model proofs only; no generic caller adoption'}
    (output / 'profile.json').write_text(json.dumps(profile, indent=2) + '\n')
    started = time.monotonic()
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'SWDB_VERIFIER_RSS_CAP_BYTES': '8589934592',
           'SWDB_HEAP_MODEL_ACTUAL': '1' if args.mode == 'actual-wp' else '0',
           'SWDB_HEAP_MODEL_PUBLIC_TIMEOUT_SECONDS': str(args.public_timeout_seconds),
           'SWDB_HEAP_MODEL_PROFILE_DEADLINE_MONOTONIC': str(started + args.seconds)}
    if args.mode == 'controls':
        env.update(SWDB_FRAMA_C='none', SWDB_CBMC='none')
    with (output / 'pytest.log').open('w') as log:
        done = subprocess.run(command, cwd=project, env=env, stdout=log, stderr=subprocess.STDOUT)
    source_check()
    elapsed = time.monotonic() - started
    (output / 'result.json').write_text(json.dumps({'pytest_exit_code': done.returncode,
        'source_unchanged': True, 'elapsed_seconds': elapsed,
        'within_whole_budget': elapsed <= args.seconds,
        'actual_proof_claim': 'requires retained records and independent cold audit'}, indent=2) + '\n')
    return 124 if elapsed > args.seconds else done.returncode


if __name__ == '__main__':
    raise SystemExit(main())
