"""Offline contract for Eric's pinned launcher; no target code is executed."""
from hashlib import sha256
import json
import math
from pathlib import Path

HANDOFF = 'docs/designs/dx100-reference-validation/eric-handoff'
ARTIFACTS = {
    'launcher': ('launch_16k.sh', 'ca411c0adecc1f6966217df39b02100a55b2c0070756b01328d5572081febe86'),
    'wrapper': ('continue_to_verifier.py', '3cc4fe210c2294974c700d5855ef1038f6ce9587009af45df4fd359f98739bd5'),
    'ramulator_config': ('ramulator.yaml', 'aca6e27b58afdfbfd80b7ec41c3f0e7e574a1fc7355a3512981ead823f68731b'),
}
TOPOLOGY = {'channels': 2, 'ranks': 1, 'bankgroups': 4, 'banks': 4}
COUNTERS = ('system.maa.numInst_INDRD', 'system.maa.numInst_RANGE')
BEGIN = '---------- Begin Simulation Statistics ----------'
END = '---------- End Simulation Statistics   ----------'
TARGET_ARTIFACTS = {'wrapper', 'raw_roi_stats', 'counter_snapshot', 'command_json', 'final_stats'}


def manifest(root):
    result = {}
    for key, (name, expected) in ARTIFACTS.items():
        path = HANDOFF + '/' + name
        if sha256((root/path).read_bytes()).hexdigest() != expected:
            raise ValueError('Reviewed Eric handoff changed; update its contract deliberately: ' + path)
        result[key] = {'repository_path': path, 'sha256': expected}
    return result


def system_args(ramulator, guest_env, checkpoint):
    """Exact restored se.py arguments, excluding workload operands and progress."""
    return ['--cpu-type', 'X86O3CPU', '-r', '1', '--checkpoint-dir', checkpoint, '-n', '4', '--mem-size', '16GB',
        '--sys-clock', '3.2GHz', '--cpu-clock', '3.2GHz',
        '--caches', '--l1d_size=32kB', '--l1d_assoc=8', '--l1d-hwp-type=StridePrefetcher', '--l1d_mshrs=16', '--l1d_write_buffers=8',
        '--l1i_size=32kB', '--l1i_assoc=8', '--l1i-hwp-type=StridePrefetcher', '--l1i_mshrs=16', '--l1i_write_buffers=8',
        '--l2cache', '--l2_size=256kB', '--l2_assoc=4', '--l2-hwp-type=StridePrefetcher', '--l2_mshrs=32', '--l2_write_buffers=16',
        '--l3cache', '--l3_size=8MB', '--l3_assoc=16', '--l3_mshrs=256', '--l3_write_buffers=128', '--l3_ports', '4',
        '--cacheline_size=64', '--mem-type', 'Ramulator2', '--ramulator-config', ramulator,
        '--mem-channels', '2', '--maa_ncbus_width', '32', '--maa', '--maa_num_maas', '1', '--maa_num_tile_elements', '16384',
        '--maa_l2_uncacheable', '--maa_l3_uncacheable', '--maa_num_initial_row_table_slices', '32', '--env', guest_env]


def launch_templates(workloads):
    cases = []
    for workload in workloads:
        for variant in ('baseline', 'dx100'):
            key = workload['id'] + '-' + variant
            checkpoint = '{run_root}/' + key + '-checkpoint'
            output = '{run_root}/' + key + '-restore'
            common = ['{source_root}', '{gem5}', '{build_root}/bfs-gem5-' + variant,
                      '{graph_root}/' + workload['id'] + '.sg']
            cases.append({'id': key, 'workload_id': workload['id'], 'variant': variant,
                'checkpoint_argv': ['bash', '{launcher}', 'checkpoint', *common, checkpoint, checkpoint, '{guest_env_file}'],
                'restore_argv': ['bash', '{launcher}', 'restore', *common, output, checkpoint, '{guest_env_file}'],
                'restore_environment': {'VERIFY_MAX_TICKS': None},
                'checkpoint_policy': 'Fresh checkpoint specific to this binary and graph; never share between variants.',
                'output_directory': output, 'checkpoint_directory': checkpoint})
    return cases


def check_roi_evidence(loaded, evidence, receipt, target):
    """Independently replay zero-only projection and bind it to the exit chain."""
    errors, missing = [], []
    needed = {'raw_roi_stats', 'stats', 'counter_snapshot', 'exit_events', 'wrapper'}
    if not needed <= loaded.keys():
        return [], ['roi_derivation_artifacts_incomplete']
    try:
        snapshot = json.loads(loaded['counter_snapshot'])
        exits = json.loads(loaded['exit_events'])
        if not isinstance(snapshot, dict) or not isinstance(exits, dict):
            raise ValueError('object required')
        raw, projected = loaded['raw_roi_stats'], loaded['stats']
        if snapshot.get('raw_roi_sha256') != evidence['raw_roi_stats']['sha256'] or snapshot.get('projected_roi_sha256') != evidence['stats']['sha256']:
            errors.append('roi_snapshot_hash_binding')
        if raw.count(BEGIN) != 1 or raw.count(END) != 1 or raw.index(BEGIN) > raw.index(END):
            raise ValueError('one complete raw ROI dump required')
        values = snapshot.get('instruction_counters')
        if not isinstance(values, dict) or set(values) != set(COUNTERS):
            raise ValueError('exact registered instruction counters required')
        observed = {}
        for line in raw[raw.index(BEGIN):raw.index(END)].splitlines():
            fields = line.split()
            if fields and fields[0] in COUNTERS:
                if fields[0] in observed:
                    raise ValueError('duplicate counter')
                observed[fields[0]] = float(fields[1])
        additions = []
        for name in COUNTERS:
            value = values[name]
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or int(value) != value:
                raise ValueError('invalid registered counter')
            if name in observed:
                if observed[name] != value:
                    raise ValueError('raw/live counter mismatch')
            elif value == 0:
                additions.append(name + ' 0 # explicit registered zero; stock text output suppresses zero\n')
            else:
                raise ValueError('omitted positive counter')
        if projected != raw.replace(END, ''.join(additions) + END):
            errors.append('roi_projection_not_zero_only')
        if receipt.get('stats_block_index') != 0 or type(receipt.get('stats_block_index')) is not int or exits.get('stats_block_index') != 0 or type(exits.get('stats_block_index')) is not int:
            errors.append('frozen_roi_block_must_be_zero')
        if exits.get('wrapper_sha256') != ARTIFACTS['wrapper'][1] or evidence['wrapper']['sha256'] != ARTIFACTS['wrapper'][1]:
            errors.append('roi_wrapper_binding')
        # The wrapper emits these names relative to its output directory.
        directory = Path(evidence['exit_events']['path']).parent
        for field, artifact in [('roi_stats', 'stats'), ('raw_roi_stats', 'raw_roi_stats'), ('counter_snapshot', 'counter_snapshot')]:
            value = exits.get(field)
            if not isinstance(value, str) or (directory/value).resolve() != Path(evidence[artifact]['path']).resolve():
                errors.append('roi_event_path_binding:' + field)
        tick = snapshot.get('snapshot_tick')
        events = exits.get('events')
        if type(tick) is not int or tick < 0 or not isinstance(events, list) or not events:
            raise ValueError('snapshot tick and event chain required')
        first = events[0]
        if not isinstance(first, dict) or first.get('role') != 'roi_exit' or first.get('cause') != 'm5_exit instruction encountered' or type(first.get('code')) is not int or first['code'] != 0 or type(first.get('tick')) is not int or first.get('tick') != tick:
            errors.append('roi_first_event_binding')
        if exits.get('guest_completed') is not True:
            missing.append('verifier_continuation_incomplete')
        elif len(events) != 2:
            errors.append('roi_completion_event_count')
        else:
            final = events[1]
            if not isinstance(final, dict) or final.get('role') != 'post_roi_guest_exit' or final.get('cause') != 'exiting with last active thread context' or type(final.get('code')) is not int or final['code'] != 0:
                errors.append('roi_final_event_binding')
            elif type(final.get('tick')) is not int or final['tick'] < tick:
                errors.append('roi_event_tick_order')
            elif type(target.get('verify_max_ticks')) is int and final['tick'] - tick > target['verify_max_ticks']:
                errors.append('verification_tick_budget_exceeded')
    except (ValueError, TypeError, KeyError, IndexError, OverflowError):
        errors.append('invalid_roi_derivation')
    return errors, missing


def check_launch_evidence(loaded, evidence, receipt, env):
    required = {'command_json', 'simulator', 'binary', 'graph', 'wrapper', 'ramulator_config', 'guest_env_file', 'exit_events'}
    if not (required | {'launcher'}) <= evidence.keys() or 'command_json' not in loaded:
        return [], ['launch_artifacts_incomplete']
    errors, missing = [], []
    target = env.get('target', {})
    checkpoint = receipt.get('checkpoint_directory')
    if not isinstance(checkpoint, str) or not Path(checkpoint).is_absolute():
        return [], ['absolute_checkpoint_directory_required']
    for key in ARTIFACTS:
        if evidence[key]['sha256'] != ARTIFACTS[key][1]:
            errors.append(key + '_reviewed_artifact_mismatch')
        if target.get(key) and Path(target[key]).resolve() != Path(evidence[key]['path']).resolve():
            errors.append(key + '_environment_path_mismatch')
    if env.get('tools', {}).get('gem5') and Path(env['tools']['gem5']).resolve() != Path(evidence['simulator']['path']).resolve():
        errors.append('simulator_environment_path_mismatch')
    source = env.get('source_root')
    budget = target.get('verify_max_ticks')
    if not source or type(budget) is not int or budget <= 0:
        return errors, ['launch_source_or_verification_budget_unbound']
    paths = {k: evidence[k]['path'] for k in required}
    # se.py splits --options on whitespace; do not silently misparse a graph path.
    if any(c.isspace() for c in paths['graph']):
        errors.append('launcher_graph_path_contains_whitespace')
    expected = [paths['simulator'], '--outdir=' + str(Path(paths['exit_events']).parent), paths['wrapper'],
                '--dx100-source-root', str(Path(source).resolve()), '--verify-max-ticks', str(budget), '--',
                *system_args(paths['ramulator_config'], paths['guest_env_file'], checkpoint),
                '--cmd', paths['binary'], '--options', '-f ' + paths['graph'] + ' -r 0 -n 1 -v -l -a', '--prog-interval=1000']
    try:
        recorded = json.loads(loaded['command_json'])
        if recorded != expected or receipt.get('command_argv') != recorded:
            errors.append('recorded_restore_command_mismatch')
    except (ValueError, TypeError):
        errors.append('command_json_invalid')
    folder = Path(evidence['launcher']['path']).parent
    for key, (name, _) in ARTIFACTS.items():
        if Path(evidence[key]['path']) != folder/name:
            errors.append('handoff_sibling_layout_required:' + key)
    output = Path(paths['exit_events']).parent
    if Path(checkpoint).resolve() == output.resolve():
        errors.append('checkpoint_and_restore_directories_must_differ')
    for key, name in [('command_json', 'command.json'), ('exit_events', 'exit-events.json'), ('final_stats', 'stats.txt')]:
        if key in evidence and Path(evidence[key]['path']) != output/name:
            errors.append('launcher_output_path_mismatch:' + key)
    return errors, missing
