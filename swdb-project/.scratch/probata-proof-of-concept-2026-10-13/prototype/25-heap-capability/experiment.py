"""First-pair heap capability command plan. Created: 2026-10-15 ET.

Plan mode performs no tool discovery or compiler/verifier execution. Actual
execution requires a separate coordinator-admitted source/command freeze.
"""
from __future__ import annotations
import argparse
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import packets

CAP = 8589934592


def pin(path):
    return {'path': str(path), 'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def source_check(expected):
    repo = packets.ROOT.parent
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if not expected or head != expected:
        raise ValueError('source commit does not match coordinator-admitted exact SHA')
    dirty = subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain', '--untracked-files=all'], text=True)
    if dirty.strip():
        raise ValueError('coordinator-admitted source commit is not clean')
    return head


def run_leaf(row, directory, env):
    """The same real timeout boundary used by actual WP and the sleep control."""
    from swdb.rss_watchdog import run
    directory.mkdir(parents=True, exist_ok=True)
    result = run(row['command'], log=directory / 'frama-c.log', cwd=directory, env=env,
                 cap_bytes=CAP, timeout=row['public_timeout_seconds'])
    (directory / 'resources.json').write_text(json.dumps(dataclasses.asdict(result), indent=2) + '\n')
    return result


def plan(manifest, inputs, output, seconds, public_timeout, command=('frama-c',),
         report_module='@fresh-report-module@'):
    rows = []
    for goal in manifest['obligations']:
        flags = [
            '-wp', '-wp-rte', '-rte-initialized', '@all', '-wp-no-filter-init',
            '-wp-cache', 'none', '-wp-smoke-tests', '-wp-par', '1',
            '-wp-timeout', str(seconds), '-wp-prover', 'qed,alt-ergo,z3,cvc5',
            '-wp-status-all', '-wp-library', str(inputs / 'theory'),
            '-wp-out', 'prover-files', '-wp-print',
            '-wp-dkey', 'print-generated,why3:compile,prover:pp_task',
        ]
        if goal['kind'] == 'check_lemma':
            flags += ['-wp-prop', '+' + goal['goal']]
        else:
            flags += ['-wp-fct=t25_ctor_numeric']
        invocation = [
            *command, '-machdep', 'x86_64', '-kernel-warn-key', 'annot-error=abort',
            '-wp-library', str(inputs / 'theory'),
            'wp_input.c', '-print', '-ocode', 'wp-normalized.c', '-then',
            '-machdep', 'x86_64', *flags, '-wp-report-json', 'wp-goals.json',
            '-then', '-load-module', str(report_module), '-report', '-report-untried',
            '-report-csv', 'wp-properties.csv',
        ]
        rows.append({'id': goal['id'], 'goal': goal['goal'], 'kind': goal['kind'],
                     'expected': goal['expected'], 'input': goal['path'],
                     'input_sha256': goal['sha256'],
                     'cwd': str(output / 'jobs' / goal['id']), 'command': invocation,
                     'public_timeout_seconds': public_timeout})
    return {'created': '2026-10-15 ET', 'capability_only': True,
            'verifier_launched': False, 'input_manifest_sha256':
                hashlib.sha256((inputs / 'manifest.json').read_bytes()).hexdigest(),
            'input_root': str(inputs), 'rows': rows,
            'scope': 'Prospective exact commands; no tool/version or proof success claim.',
            'mandatory_followup': 'Inspect imported proposition closure and emitted task hypotheses; no result accepted from command exit alone.'}


def matches_result(row, resources, reading, inventory):
    """Additional experiment policy after the normal complete-report reader.

    An unknown/timeout is an open negative control, never a solver refutation.
    Synthetic policy checks are not proof records or tool observations.
    """
    if resources.get('exit_code') != 0 or resources.get('timed_out') is not False or resources.get('out_of_memory') is not False:
        return False
    goals = reading.get('goals', [])
    ordinary = [g for g in goals if not g.get('smoke')]
    smoke = [g for g in goals if g.get('smoke')]
    if not ordinary or any(g.get('status') != 'valid' for g in smoke):
        return False
    if row['kind'] == 'check_lemma':
        targets = [p for p in inventory.get('properties', []) if p.get('kind') == 'lemma']
        if len(targets) != 1:
            return False
        target = targets[0].get('property', '')
        if target != row['goal'] and not target.endswith('_' + row['goal']):
            return False
        selected = [g for g in ordinary if g.get('property') == target]
        if not selected or len(selected) != len(ordinary):
            return False
    elif row['kind'] == 'c_kernel':
        selected = ordinary
        if not smoke:
            return False
    else:
        return False
    if row['expected'] == 'proven':
        return (reading.get('verdict') == 'proven' and reading.get('failure_class') is None
                and all(g.get('status') == 'valid' for g in selected))
    return (row['expected'] == 'not_proven' and reading.get('verdict') == 'not_proven'
            and reading.get('failure_class') in {'unknown', 'timeout'}
            and any(g.get('status') != 'valid' for g in selected))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--plan-only', action='store_true')
    mode.add_argument('--run-admitted', action='store_true')
    mode.add_argument('--process-control', action='store_true')
    mode.add_argument('--check-result', action='store_true')
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-commit')
    parser.add_argument('--why3-stdlib', type=Path)
    parser.add_argument('--control-sleep-seconds', type=float, default=4)
    parser.add_argument('--seconds-per-prover', type=int, default=10)
    parser.add_argument('--public-timeout-seconds', type=int, default=180)
    args = parser.parse_args()
    if not 1 <= args.seconds_per_prover <= 120 or not 1 <= args.public_timeout_seconds <= 3600:
        parser.error('budgets outside supported capability limits')
    output = args.output.resolve()
    if args.check_result:
        if args.input is None:
            parser.error('result policy control needs a reading/inventory JSON input')
        payload = json.loads(args.input.read_text())
        matched = matches_result(payload['row'], payload['resources'], payload['reading'], payload['inventory'])
        output.mkdir(parents=True, exist_ok=False)
        (output / 'result-policy.json').write_text(json.dumps({
            'mode': 'synthetic_result_policy_only', 'matches_expected': matched,
            'verifier_launched': False, 'model_body_proof_records_created': 0}, indent=2) + '\n')
        return 0
    if args.process_control:
        output.mkdir(parents=True, exist_ok=False)
        row = {'command': [sys.executable, '-c', f'import time; time.sleep({args.control_sleep_seconds!r})'],
               'public_timeout_seconds': args.public_timeout_seconds}
        result = run_leaf(row, output, dict(os.environ))
        print(json.dumps({'mode': 'process_control_only', 'verifier_launched': False,
                          'resources': dataclasses.asdict(result)}))
        return result.exit_code
    if args.run_admitted:
        if output.is_relative_to(packets.ROOT.parent.resolve()):
            parser.error('actual output must be outside the source checkout')
        source_check(args.expected_commit)  # Before even probing a formal tool.
        if args.why3_stdlib is None:
            parser.error('actual admission requires the declared pinned Why3 standard-library directory')
    elif args.input is None:
        parser.error('plan mode needs prepared input packets')
    inputs = args.input.resolve() if args.input else output / 'inputs'
    if args.input and output.is_relative_to(inputs):
        parser.error('reports must not mutate the immutable input packet tree')
    output.mkdir(parents=True, exist_ok=False)
    if not args.input:
        packets.prepare(inputs)
    packets.check(inputs)
    manifest = json.loads((inputs / 'manifest.json').read_text())
    commands = plan(manifest, inputs, output, args.seconds_per_prover, args.public_timeout_seconds)
    (output / 'plan.json').write_text(json.dumps(commands, sort_keys=True, indent=2) + '\n')
    if args.run_admitted:
        return actual(args, manifest, commands, inputs, output)
    print(json.dumps({'output': str(output), 'rows': len(commands['rows']), 'verifier_launched': False}))
    return 0


def actual(args, manifest, commands, inputs, output):
    """Only the coordinator invokes this path, inside an outer RSS/time guard.

    Normal generated-goal reading is reused; source/VC mapping and imported
    task hypotheses additionally need independent review. No c_model record
    or certification level is created by this experiment.
    """
    from swdb import framac, proof_setup, verifier_lock
    state = {'created': '2026-10-15 ET', 'source_commit': args.expected_commit,
             'scope': 'Original int count/value+dtor mapped capability experiment, not a model-body record.',
             'capability_only': True, 'model_body_proof_records_created': 0,
             'input_manifest': pin(inputs / 'manifest.json'), 'rows': [],
             'complete': False, 'all_result_expectations_matched': False,
             'import_task_audit_pending': True, 'errors': []}
    profile = output / 'profile.json'
    def save():
        profile.write_text(json.dumps(state, sort_keys=True, indent=2) + '\n')
    save()
    try:
        stdlib = args.why3_stdlib.resolve()
        std_files = sorted(stdlib.rglob('*.mlw'))
        if not (stdlib / 'int.mlw').is_file() or not (stdlib / 'map.mlw').is_file() or not std_files:
            raise ValueError('declared Why3 standard library is missing required imports')
        state['declared_why3_stdlib'] = [pin(path) for path in std_files]
        state['import_resolution_boundary'] = ('Declared physical sources are pinned; actual resolved imported '
            'propositions/definitions and emitted task hypotheses require independent comparison before acceptance.')
        state['runtime_source_pins'] = [pin(packets.ROOT / 'swdb' / name) for name in (
            'std_models.py','c_lowering.py','proof_setup.py','proof_report.ml',
            'rss_watchdog.py','framac.py','verifier_lock.py')]
        state['prototype_pins'] = [pin(packets.HERE / name) for name in (
            'heap_bridge.mlw','source_vcs.py','packets.py','experiment.py')]
        state['checks'] = proof_setup.identity()
        with verifier_lock.hold('ticket25 admitted heap capability') as lease:
            state['verifier_lease'] = lease
            tool = framac.locate()
            if tool.missing:
                raise ValueError(tool.missing)
            state['formal_tool'] = {'command': list(tool.command), 'version': tool.version}
            reader = output / 'reader'
            reader.mkdir()
            report_module = proof_setup.compile_report_module(reader)
            state['fresh_report_module'] = pin(report_module)
            commands = plan(manifest, inputs, output, args.seconds_per_prover,
                            args.public_timeout_seconds, tool.command, report_module)
            (output / 'executed-plan.json').write_text(json.dumps(commands, sort_keys=True, indent=2) + '\n')
            for row in commands['rows']:
                source_check(args.expected_commit)
                packets.check(inputs)
                directory = Path(row['cwd'])
                directory.mkdir(parents=True, exist_ok=False)
                shutil.copyfile(inputs / row['input'], directory / 'wp_input.c')
                (directory / 'tmp').mkdir()
                env = {**os.environ, 'TMPDIR': str(directory / 'tmp'),
                       'SWDB_PROOF_REPORT_OUT': str(directory / 'wp-inventory.json')}
                run = run_leaf(row, directory, env)
                result = {**row, 'verifier_launched': True, 'resources': dataclasses.asdict(run)}
                report_paths = [directory / name for name in (
                    'wp-goals.json','wp-properties.csv','wp-inventory.json','wp-normalized.c')]
                if (run.exit_code == 0 and not run.timed_out and not run.out_of_memory
                        and all(path.is_file() for path in report_paths)):
                    reading = proof_setup.read_wp_reports(*report_paths[:3])
                    result['reading'] = reading
                    inventory = json.loads(report_paths[2].read_text())
                    result['matches_expected'] = matches_result(row, dataclasses.asdict(run), reading, inventory)
                else:
                    result['matches_expected'] = False
                    result['report_error'] = 'nonzero exit, timeout/OOM, or incomplete fresh report set'
                result['reports'] = [pin(path) for path in directory.rglob('*') if path.is_file()]
                state['rows'].append(result)
                save()
                print(json.dumps({'id': row['id'], 'matches_expected': result['matches_expected'],
                                  'wall_seconds': run.wall_seconds}), flush=True)
                if not result['matches_expected']:
                    break
        state['complete'] = len(state['rows']) == len(commands['rows'])
        state['all_result_expectations_matched'] = state['complete'] and all(
            row['matches_expected'] for row in state['rows'])
    except Exception as error:
        state['errors'].append(f'{type(error).__name__}: {error}')
    finally:
        try:
            source_check(args.expected_commit)
            state['source_after'] = {'commit': args.expected_commit, 'clean': True}
        except Exception as error:
            state['errors'].append('source-after: ' + str(error))
        save()
    return 0 if state['all_result_expectations_matched'] and not state['errors'] else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError) as error:
        print(json.dumps({'status': 'refused', 'error': str(error)}), file=sys.stderr)
        raise SystemExit(2)
