"""2026-10-16 ET. Four original default-constructor contracts; preserve every normal native task.

Uses the committed adapter and ordinary shared verifier lock/RSS watchdog.
No native replay or caller adoption. Original generated evidence stays in /tmp.
"""
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def completion_gate(results, members, *, wall_seconds, retained_bytes):
    expected = ('std_vector_int_ctor', 'std_vector_float_ctor',
                'std_vector_double_ctor', 'std_vector_int_ptr_ctor')
    return (tuple(members) == expected and len(results) == 4
        and tuple(row['member'] for row in results) == expected
        and all(row['verdict'] == 'proven'
            and type(row['resources'].get('exit_code')) is int
            and row['resources']['exit_code'] == 0
            and row['resources'].get('out_of_memory') is False
            and row['resources'].get('timed_out') is False for row in results)
        and type(wall_seconds) in (int, float) and 0 <= wall_seconds <= 900
        and type(retained_bytes) is int and 0 <= retained_bytes <= 128 * 1024**2)


def main():
    project = Path(__file__).resolve().parents[4]
    output = Path('/private/tmp/probata-vector-default4-public-20261016-v2')
    assert not output.exists() and shutil.disk_usage(output.parent).free > 20 * 1024**3
    commit = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
    assert commit == 'a102e275cd23352aea8c268be3761d8a330b9be0'
    relatives = ('swdb/standard_vector_member_view.py', 'swdb/wp_adapter.py',
        'swdb/wp_pointer_bounds.py', 'swdb/proof_setup.py', 'schemas/proof.schema.json',
        'tests/testkit/standard_library.py', 'swdb/std_models.py', 'swdb/c_lowering.py', 'swdb/proof.py')
    pins = []
    for relative in relatives:
        raw = (project / relative).read_bytes()
        original = subprocess.check_output(['git', '-C', str(project), 'show', commit + ':swdb-project/' + relative])
        assert raw == original
        pins.append({'relative': relative, 'sha256': hashlib.sha256(raw).hexdigest()})
    sys.path[:0] = [str(project), str(project / 'tests')]
    import yaml
    from swdb import c_lowering, rss_watchdog, std_models
    from testkit.standard_library import method_version
    output.mkdir()
    records = output / 'records'
    records.mkdir()
    methods = output / 'library/methods'
    methods.mkdir(parents=True)
    shutil.copyfile(project / 'tests/fixtures/proof/methods/contract-fixture-1.yaml',
                    methods / 'contract-fixture-1.yaml')
    method = method_version(c_lowering.identity())
    method.update(id='method.wp-vector-default-constructors-v1', sequence=4)
    method['models']['std_vector'] = std_models.identity()
    wp = next(row for row in method['lineup'] if row['tool'] == 'frama-c-wp')
    wp['flags'] += ['-wp-out', str(output / 'native-working'), '-wp-print', '-wp-proof-trace']
    (methods / 'wp-vector-default-constructors-v1.yaml').write_text(yaml.safe_dump(method, sort_keys=False))
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
        SWDB_VERIFIER_RSS_CAP_BYTES=str(8 * 1024**3))
    selectors = [key for key in environment if key.startswith(('FRAMAC_WP', 'WP_'))
                 or key in ('SWDB_FRAMA_C', 'SWDB_VERIFIER_LOCK', 'SWDB_PROOF_REPORT_OUT')]
    assert not selectors, selectors
    plan = {'date': '2026-10-16 ET', 'source_commit': commit, 'source_pins': pins,
        'cwd': str(project), 'RSS_cap_bytes': 8 * 1024**3,
        'whole_seconds': 900, 'leaf_outer_seconds': 240, 'job_seconds': 180, 'workers': 1,
        'members': ['std_vector_int_ctor', 'std_vector_float_ctor', 'std_vector_double_ctor', 'std_vector_int_ptr_ctor'],
        'method_sha256': hashlib.sha256((methods / 'wp-vector-default-constructors-v1.yaml').read_bytes()).hexdigest(),
        'expected': 'four complete original default-constructor contracts proven; no caller or general allocation-domain admission',
        'preflight': {'disk_free_bytes': shutil.disk_usage(output).free, 'fresh_Mac_memory_and_shared_lock_admission': 'root-required before dispatch'},
        'output_budget_bytes': 128 * 1024**2, 'raw_destination': str(output)}
    (output / 'plan.json').write_text(json.dumps(plan, sort_keys=True, indent=2) + '\n')
    started = time.monotonic()
    results = []
    for member in plan['members']:
        remaining = 900 - (time.monotonic() - started)
        assert remaining > 15
        command = [sys.executable, '-B', '-m', 'swdb', 'prove', '--records', str(records),
            '--adapter', 'wp', '--model', member, '--method-version', 'method.wp-vector-default-constructors-v1',
            '--budget-minutes', '3', '--runs-dir', str(output / 'runs'), '--format', 'json']
        leaf = output / member
        leaf.mkdir()
        original = std_models.model_text(member)
        assert original and 'swdb_alloc_' not in original and 'swdb_free(' not in original
        (leaf / 'original-model.c').write_text(original)
        (leaf / 'command.json').write_text(json.dumps(command, indent=2) + '\n')
        result = rss_watchdog.run(command, log=leaf / 'public.log', cwd=project,
            env=environment, cap_bytes=8 * 1024**3, timeout=min(240, remaining))
        (leaf / 'resources.json').write_text(json.dumps(dataclasses.asdict(result), sort_keys=True, indent=2) + '\n')
        row = {'member': member, 'resources': dataclasses.asdict(result), 'verdict': None}
        if result.exit_code == 0:
            record = json.loads((leaf / 'public.log').read_bytes())['record']
            row.update(verdict=record['verdict'], record_id=record['id'],
                failure_class=record.get('failure_class'),
                ordinary_goals=sum(not goal.get('smoke') for goal in record.get('goals', [])),
                smokes=sum(bool(goal.get('smoke')) for goal in record.get('goals', [])))
        native = output / 'native-working'
        if native.exists():
            assert native.is_dir() and not native.is_symlink()
            before_native = []
            for artifact in sorted(native.rglob('*')):
                assert not artifact.is_symlink() and (artifact.is_file() or artifact.is_dir())
                if artifact.is_file():
                    data = artifact.read_bytes()
                    before_native.append({'relative': str(artifact.relative_to(native)),
                        'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
            archive = leaf / 'retained-native'
            assert not archive.exists()
            shutil.move(str(native), str(archive))
            for artifact in before_native:
                data = (archive / artifact['relative']).read_bytes()
                assert len(data) == artifact['bytes'] and hashlib.sha256(data).hexdigest() == artifact['sha256']
            relocation = {'date': '2026-10-16 ET', 'actual_original_WP_output': str(native),
                'retained_archive': str(archive), 'exact_bytes_before_after_move': True,
                'files': before_native, 'source_or_caller_admission': False}
            (leaf / 'native-relocation.json').write_text(json.dumps(relocation, sort_keys=True, indent=2) + '\n')
            row['native_files_preserved'] = len(before_native)
        else:
            row['native_files_preserved'] = 0
        results.append(row)
        total = sum(path.stat().st_size for path in output.rglob('*') if path.is_file())
        assert total <= 128 * 1024**2
        (output / 'incremental.json').write_text(json.dumps({'results': results, 'retained_bytes': total}, sort_keys=True, indent=2) + '\n')
        if row['verdict'] != 'proven' or result.out_of_memory or result.timed_out:
            break
    for row in pins:
        assert hashlib.sha256((project / row['relative']).read_bytes()).hexdigest() == row['sha256']
    final_total = sum(path.stat().st_size for path in output.rglob('*') if path.is_file())
    settled_elapsed = time.monotonic() - started
    complete = completion_gate(results, plan['members'],
        wall_seconds=settled_elapsed, retained_bytes=final_total)
    print(json.dumps({'output': str(output), 'results': results, 'all_four_proven': complete,
        'wall_seconds': settled_elapsed, 'retained_bytes': final_total,
        'caller_admission': False}, sort_keys=True), flush=True)
    return 0 if complete and time.monotonic() - started <= 900 else 1



if __name__ == '__main__':
    raise SystemExit(main())
