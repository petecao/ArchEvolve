"""2026-10-16 ET. Original closed move normal public WP diagnostic, inert until admitted.

The selected ordinary method uses the complete original C++ source and contract.
All reports/tasks and any failed or ignored lifetime facts remain unchanged.
Neither a native Valid result nor a smoke timeout admits source ownership.
"""
import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


COMMIT = 'abb598a485cca67c77798e690382b44beb48c9e3'
METHOD = 'method.wp-vector-owned-move-diagnostic-v1'
CONTRACT = 'contract.fixture_vector_owned_move_capture'
FUNCTION = 'vector_owned_move_capture'
OUTPUT = '/private/tmp/probata-vector-owned-move-normal-public-20261016-v2'
CAP = 8*1024**3
WHOLE = 600
BUDGET = 128*1024**2
SOURCE_SHA = 'a0dc043284f96a5b7c052963b51188318ae4abc6a85ee347fea78b6ab392d3a2'


def completion_gate(row, *, wall_seconds, retained_bytes):
    """A completed diagnostic can be not_proven; resource or record gaps cannot."""
    resources = row.get('resources', {})
    return (row.get('function') == FUNCTION and row.get('contract') == CONTRACT
        and row.get('method') == METHOD
        and row.get('record_subject') == {'kind': 'library_summary', 'id': CONTRACT}
        and row.get('record_method') == METHOD
        and row.get('verdict') in {'proven', 'not_proven'}
        and type(row.get('ordinary_goals')) is int and row['ordinary_goals'] > 0
        and type(row.get('native_files_preserved')) is int and row['native_files_preserved'] > 0
        and type(resources.get('exit_code')) is int and resources['exit_code'] == 0
        and resources.get('out_of_memory') is False and resources.get('timed_out') is False
        and type(wall_seconds) in (int, float) and math.isfinite(wall_seconds)
        and 0 <= wall_seconds <= WHOLE
        and type(retained_bytes) is int and 0 <= retained_bytes <= BUDGET)


def extent(directory):
    total = 0
    for path in directory.rglob('*'):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError('unexpected linked or special diagnostic artifact')
        if path.is_file():
            total += path.stat().st_size
    if total > BUDGET:
        raise ValueError('complete diagnostic output budget exceeded')
    return total


def main():
    started = time.monotonic()
    project = Path(__file__).resolve().parents[5]
    output = Path(OUTPUT)
    if output.exists() or output.is_symlink() or shutil.disk_usage(output.parent).free < 20*1024**3:
        raise ValueError('fresh output and full Mac output headroom required')
    commit = subprocess.check_output(['git', '-C', str(project), 'rev-parse', 'HEAD'], text=True).strip()
    if commit != COMMIT:
        raise ValueError('exact prospectively reviewed source commit required')
    relatives = ('swdb/wp_adapter.py', 'swdb/wp_pointer_bounds.py', 'swdb/proof_setup.py',
        'swdb/proof.py', 'schemas/proof.schema.json', 'swdb/std_models.py', 'swdb/c_lowering.py',
        'swdb/vector_owned_move_source.py', 'tests/testkit/standard_library.py',
        'tests/fixtures/proof/lowering/vector_owned_transfer.cc',
        'tests/fixtures/proof/methods/contract-fixture-1.yaml', 'library/methods/probata-draft-1.yaml')
    pins = []
    for relative in relatives:
        path = project/relative
        original = subprocess.check_output(['git', '-C', str(project), 'show', COMMIT+':swdb-project/'+relative])
        if path.is_symlink() or path.read_bytes() != original:
            raise ValueError('actual source differs from reviewed commit: '+relative)
        pins.append({'relative': relative, 'bytes': len(original), 'sha256': hashlib.sha256(original).hexdigest()})
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', SWDB_VERIFIER_RSS_CAP_BYTES=str(CAP))
    selectors = [key for key in environment if key.startswith(('FRAMAC_WP', 'WP_'))
                 or key in ('SWDB_FRAMA_C', 'SWDB_VERIFIER_LOCK', 'SWDB_PROOF_REPORT_OUT')]
    if selectors:
        raise ValueError('unexpected verifier selector environment: '+str(selectors))
    sys.path[:0] = [str(project), str(project/'tests')]
    import yaml
    from swdb import c_lowering, rss_watchdog, std_models
    from testkit.standard_library import method_version
    output.mkdir()
    records = output/'records'; records.mkdir()
    library = output/'library'; library.mkdir()
    methods = library/'methods'; methods.mkdir()
    shutil.copyfile(project/'tests/fixtures/proof/methods/contract-fixture-1.yaml', methods/'contract-fixture-1.yaml')
    method = method_version(c_lowering.identity())
    method.update(id=METHOD, sequence=4, status='draft', created='2026-10-16',
                  description='Complete original closed move normal WP diagnostic; source interpretation is unadmitted.')
    method['models']['std_vector'] = std_models.identity()
    wp = next(row for row in method['lineup'] if row['tool'] == 'frama-c-wp')
    wp['flags'] += ['-wp-out', str(output/'native-working'), '-wp-print', '-wp-proof-trace']
    method_path = methods/'wp-vector-owned-move-diagnostic-v1.yaml'
    method_path.write_text(yaml.safe_dump(method, sort_keys=False))
    units = library/'proof_units'; units.mkdir()
    source = (project/'tests/fixtures/proof/lowering/vector_owned_transfer.cc').read_bytes()
    if len(source) != 327 or hashlib.sha256(source).hexdigest() != SOURCE_SHA:
        raise ValueError('exact original 327-byte closed move source required')
    unit = units/'vector_owned_transfer.cc'; unit.write_bytes(source)
    clauses = [r'requires 0 <= n;', r'assigns \nothing;', r'ensures \result == (n > 0 ? 7 : 0);']
    entry = {'kind': 'rewrite_contract', 'id': CONTRACT, 'formal_frame': 1, 'version': '1.0',
        'provenance': {'origin': {'intrinsic_specification': 'vector-owned-move-diagnostic-20261016'}},
        'proof_unit': {'function': FUNCTION, 'source': {'root': 'library',
            'path': 'proof_units/'+unit.name, 'sha256': SOURCE_SHA}}, 'concurrency_frame': [],
        'clauses': [{'id': name, 'role': role, 'statement': 'Original closed move '+name,
            'discharge_mode': 'runtime_guard', 'negative_control': {'id': name+'-control', 'check': name},
            'acsl': {'text': text, 'uses': []}, 'proof_placement': {'once': 'self'}}
            for (name, role), text in zip((('pre', 'legality'), ('frame', 'postcondition'),
                                          ('post', 'postcondition')), clauses, strict=True)],
        'pattern_key': [{'roles': ['index', 'target'], 'address_shapes': ['stream', 'single_valued_indirect'],
                         'update_kind': 'read'}], 'strategies': [], 'uses_intrinsics': [],
        'uses_library_operations': [], 'runtime_guards': [], 'knobs': [], 'preservation_obligations': [],
        'correctness_check': {'kernel': 'fixture', 'check': 'fixture'},
        'execution_witness': {'check': 'fixture'},
        'negative_controls': [{'id': kind, 'kind': kind, 'check': 'fixture'}
                             for kind in ('overlapping_pointer', 'double_claim', 'dropped_operand')],
        'requirement_map': []}
    contracts = library/'rewrite_contracts'; contracts.mkdir()
    contract_path = contracts/'fixture_vector_owned_move_capture.yaml'
    contract_path.write_text(yaml.safe_dump(entry, sort_keys=False))
    command = [sys.executable, '-B', '-m', 'swdb', 'prove', '--records', str(records),
        '--adapter', 'wp', '--summary', CONTRACT, '--method-version', METHOD,
        '--budget-minutes', '7', '--runs-dir', str(output/'runs'), '--format', 'json']
    plan = {'date': '2026-10-16 ET', 'source_commit': COMMIT, 'source_pins': pins,
        'source': {'sha256': SOURCE_SHA, 'bytes': 327}, 'function': FUNCTION,
        'formal_clauses': clauses, 'caller_premises_added': [], 'method': METHOD,
        'method_sha256': hashlib.sha256(method_path.read_bytes()).hexdigest(),
        'contract_sha256': hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        'command': command, 'RSS_cap_bytes': CAP, 'whole_seconds': WHOLE,
        'leaf_outer_seconds': 480, 'job_seconds': 420, 'workers': 1,
        'output_budget_bytes': BUDGET, 'raw_destination': str(output),
        'preflight': 'root fresh Mac memory/shared verifier lock/runtime admission required before execution',
        'interpretation': 'complete normal public native diagnostic only; no source/Heap/Typed/body/caller acceptance'}
    (output/'plan.json').write_text(json.dumps(plan, sort_keys=True, indent=2)+'\n')
    remaining = WHOLE-(time.monotonic()-started)
    if remaining <= 30:
        raise ValueError('whole diagnostic setup exhausted its time budget')
    run = rss_watchdog.run(command, log=output/'public.log', cwd=project, env=environment,
                           cap_bytes=CAP, timeout=min(480, remaining))
    resources = dataclasses.asdict(run)
    (output/'resources.json').write_text(json.dumps(resources, sort_keys=True, indent=2)+'\n')
    row = {'function': FUNCTION, 'contract': CONTRACT, 'method': METHOD,
           'resources': resources, 'verdict': None, 'native_files_preserved': 0}
    if run.exit_code == 0:
        report = json.loads((output/'public.log').read_bytes())
        record = report['record']
        row.update(verdict=record['verdict'], record_id=record['id'],
                   record_subject=record.get('subject'),
                   record_method=record.get('pins', {}).get('method_version', {}).get('id'),
                   failure_class=record.get('failure_class'),
                   ordinary_goals=sum(not goal.get('smoke') for goal in record.get('goals', [])),
                   smokes=sum(bool(goal.get('smoke')) for goal in record.get('goals', [])))
    native = output/'native-working'
    if native.exists():
        extent(output)
        before = [{'relative': str(f.relative_to(native)), 'bytes': f.stat().st_size,
                   'sha256': hashlib.sha256(f.read_bytes()).hexdigest()}
                  for f in sorted(native.rglob('*')) if f.is_file()]
        archive = output/'retained-native'
        shutil.move(str(native), str(archive))
        for item in before:
            raw = (archive/item['relative']).read_bytes()
            if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
                raise ValueError('native task relocation changed bytes')
        (output/'native-relocation.json').write_text(json.dumps({
            'actual_original_WP_output': str(native), 'retained_archive': str(archive),
            'exact_bytes_before_after_move': True, 'files': before}, sort_keys=True, indent=2)+'\n')
        row['native_files_preserved'] = len(before)
    (output/'diagnostic.json').write_text(json.dumps({'result': row, 'source_admission': False,
        'native_modular_constructor_post_state_or_freeable_not_admitted': True}, sort_keys=True, indent=2)+'\n')
    for item in pins:
        if hashlib.sha256((project/item['relative']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('selected source changed during diagnostic')
    total, elapsed = extent(output), time.monotonic()-started
    complete = completion_gate(row, wall_seconds=elapsed, retained_bytes=total)
    print(json.dumps({'output': str(output), 'result': row, 'complete_native_diagnostic': complete,
        'wall_seconds': elapsed, 'retained_bytes': total, 'source_Heap_Typed_caller_admission': False},
        sort_keys=True), flush=True)
    return 0 if complete and time.monotonic()-started <= WHOLE else 1


if __name__ == '__main__':
    raise SystemExit(main())
