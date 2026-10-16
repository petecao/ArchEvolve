"""Public source-to-packet capability controls. Created: 2026-10-15 ET.

These tests execute no compiler, verifier, or prover. Actual imported-heap
capability is a separately admitted experiment, never inferred from this suite.
"""
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import pytest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / '.scratch/probata-proof-of-concept-2026-10-13/prototype/25-heap-capability/packets.py'
EXPERIMENT = CLI.with_name('experiment.py')


def test_original_count_value_and_dtor_emit_source_mapped_isolated_packets(tmp_path):
    output = tmp_path / 'packets'
    result = subprocess.run([sys.executable, str(CLI), 'prepare', '--output', str(output)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads((output / 'manifest.json').read_text())
    assert manifest['capability_only'] is True
    assert manifest['original_members'] == ['std_vector_int_ctor_count_value', 'std_vector_int_dtor']
    goals = {g['id']: g for g in manifest['obligations']}
    assert {'ctor.prefix.establish', 'ctor.prefix.step', 'ctor.prefix.exit',
            'ctor.frame.preexisting', 'dtor.frame.surviving', 'dtor.post.old_invalid',
            'control.zero_size.formation', 'control.reused_address.stale'} <= goals.keys()
    for goal in goals.values():
        packet = (output / goal['path']).read_text()
        if goal['kind'] == 'c_kernel':
            assert 'size_t t25_ctor_numeric(size_t n, size_t k)' in packet
            assert 'allocation_size_exact' in packet
        else:
            assert packet.count('check lemma ') == 1
        assert 'axiom ' not in packet
        assert goal['source_spans']
        assert goal['dependencies'] == []
    assert manifest['original_caller_premises_added'] == []
    assert manifest['verifier_launched'] is False


def test_packet_check_refuses_a_deleted_source_obligation_even_after_manifest_rewrite(tmp_path):
    output = tmp_path / 'packets'
    build = subprocess.run([sys.executable, str(CLI), 'prepare', '--output', str(output)],
                           capture_output=True, text=True, timeout=30)
    assert build.returncode == 0, build.stderr
    command = [sys.executable, str(CLI), 'check', '--input', str(output)]
    clean = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert clean.returncode == 0, clean.stdout + clean.stderr
    path = output / 'manifest.json'
    manifest = json.loads(path.read_text())
    manifest['obligations'] = [g for g in manifest['obligations'] if g['id'] != 'ctor.prefix.step']
    path.write_text(json.dumps(manifest))
    changed = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert changed.returncode != 0
    assert 'inventory' in changed.stdout + changed.stderr


def test_first_pair_capability_covers_original_clause_and_safety_groups(tmp_path):
    output = tmp_path / 'packets'
    result = subprocess.run([sys.executable, str(CLI), 'prepare', '--output', str(output)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    manifest = json.loads((output / 'manifest.json').read_text())
    assert manifest['pending_source_inventory'] == []
    groups = {group for g in manifest['obligations'] for group in g['source_groups']}
    assert groups == {*(f'C{i}' for i in range(1, 10)), *(f'D{i}' for i in range(1, 8))}
    goals = {g['id']: g for g in manifest['obligations']}
    assert goals['ctor.numeric']['kind'] == 'c_kernel'
    for name in ('control.omitted_store', 'control.wrong_release',
                 'control.stale_read', 'control.double_release'):
        assert goals[name]['expected'] == 'not_proven'
    assert manifest['scope'].startswith('Complete first-pair capability inventory')
    assert manifest['verifier_launched'] is False


def test_reviewed_original_source_gate_refuses_an_extra_write_with_old_needles_intact(tmp_path):
    first = tmp_path / 'first'
    built = subprocess.run([sys.executable, str(CLI), 'prepare', '--output', str(first)],
                           capture_output=True, text=True, timeout=30)
    assert built.returncode == 0, built.stderr
    sources = tmp_path / 'sources'
    sources.mkdir()
    for path in first.glob('*.original.c'):
        shutil.copyfile(path, sources / path.name)
    command = [sys.executable, str(CLI), 'prepare', '--sources', str(sources)]
    clean = subprocess.run([*command, '--output', str(tmp_path / 'clean')],
                           capture_output=True, text=True, timeout=30)
    assert clean.returncode == 0, clean.stdout + clean.stderr
    path = sources / 'std_vector_int_ctor_count_value.original.c'
    text = path.read_text()
    text = text.replace('this->size = n;', 'this->size = n; this->capacity = 0;')
    path.write_text(text)
    changed = subprocess.run([*command, '--output', str(tmp_path / 'changed')],
                             capture_output=True, text=True, timeout=30)
    assert changed.returncode != 0
    assert 'reviewed source' in changed.stdout + changed.stderr


def test_allocator_freshness_is_an_explicit_uniform_transition_not_a_caller_premise(tmp_path):
    output = tmp_path / 'packets'
    result = subprocess.run([sys.executable, str(CLI), 'prepare', '--output', str(output)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    manifest = json.loads((output / 'manifest.json').read_text())
    goals = {g['id']: g for g in manifest['obligations']}
    assert 'ctor.alloc.separation' in goals
    assert 'Heap::available(h,n,a)' in goals['ctor.alloc.separation']['statement']
    assert manifest['semantic_relations']['allocator_output'] == 'fresh identity, exact extent, available address, uninitialized cells, prior-object frame'
    assert manifest['semantic_relations']['generic_caller_composition'] == 'unsupported'
    assert manifest['original_caller_premises_added'] == []


def test_receiver_accesses_and_source_mutants_have_explicit_event_to_vc_bindings(tmp_path):
    output = tmp_path / 'packets'
    built = subprocess.run([sys.executable, str(CLI), 'prepare', '--output', str(output)],
                           capture_output=True, text=True, timeout=30)
    assert built.returncode == 0, built.stderr
    manifest = json.loads((output / 'manifest.json').read_text())
    events = {event['id']: event for event in manifest['source_events']}
    assert {'ctor.zero.data', 'ctor.zero.size', 'ctor.zero.capacity',
            'ctor.allocated.data', 'ctor.allocated.capacity', 'ctor.fill',
            'ctor.final.size', 'dtor.load_and_release'} <= events.keys()
    goals = {g['id']: g for g in manifest['obligations']}
    for event in events.values():
        assert event['source_spans']
        assert event['obligations']
        assert all(name in goals for name in event['obligations'])
    for name in ('ctor.zero.data', 'ctor.zero.size', 'ctor.zero.capacity',
                 'ctor.allocated.data', 'ctor.allocated.capacity', 'ctor.final.size'):
        assert any('.rte.' in name for name in events[name]['obligations'])
    missing = goals['control.omitted_store']
    omitted = (output / missing['control_source']['path']).read_text()
    assert '(void)value;' in omitted
    assert 'this->data[k] = value;' not in omitted
    assert missing['source_transition'] == 'h'
    assert 't25_inv(h,r,o,b,n,k+1,v)' in missing['statement']
    wrong = goals['control.wrong_release']
    assert 'swdb_free(NULL);' in (output / wrong['control_source']['path']).read_text()
    assert wrong['source_transition'] == 'Heap::release(h,0)'


@pytest.mark.parametrize('field,value', [
    ('capability_only', False),
    ('pending_validation', []),
    ('semantic_relations', {'generic_caller_composition': 'supported'}),
])
def test_unvalidated_capability_cannot_be_rewritten_as_a_proof_claim(tmp_path, field, value):
    output = tmp_path / 'packets'
    built = subprocess.run([sys.executable, str(CLI), 'prepare', '--output', str(output)],
                           capture_output=True, text=True, timeout=30)
    assert built.returncode == 0, built.stderr
    path = output / 'manifest.json'
    manifest = json.loads(path.read_text())
    manifest[field] = value
    path.write_text(json.dumps(manifest))
    changed = subprocess.run([sys.executable, str(CLI), 'check', '--input', str(output)],
                             capture_output=True, text=True, timeout=30)
    assert changed.returncode != 0
    assert 'declaration' in changed.stdout + changed.stderr


def test_typed_layout_and_reuse_controls_require_a_valid_allocator_transition(tmp_path):
    output = tmp_path / 'packets'
    built = subprocess.run([sys.executable, str(CLI), 'prepare', '--output', str(output)],
                           capture_output=True, text=True, timeout=30)
    assert built.returncode == 0, built.stderr
    manifest = json.loads((output / 'manifest.json').read_text())
    assert manifest['semantic_relations']['typed_layout'] == 'int: size4 align4; receiver: size24 align8, fields0/8/16; original typed validity includes alignment'
    goals = {g['id']: g for g in manifest['obligations']}
    zero = goals['control.zero_size.formation']['statement']
    assert 'Heap::available(h,0,a)' in zero
    assert 'Heap::well_formed(Heap::allocate(h,0,a))' in zero
    reuse = goals['control.reused_address.stale']['statement']
    assert 'Heap::freeable(h,b,0)' in reuse
    assert '4*n <= Heap::bytes(h,b)' in reuse
    assert 'Heap::available(Heap::release(h,b),n,Heap::numerical_address(h,b))' in reuse
    assert 'control.live_zero_base.not_fresh' in goals
    assert manifest['original_caller_premises_added'] == []


def test_formal_plan_keeps_each_target_and_mandatory_flags_without_running_tools(tmp_path):
    packets = tmp_path / 'packets'
    built = subprocess.run([sys.executable, str(CLI), 'prepare', '--output', str(packets)],
                           capture_output=True, text=True, timeout=30)
    assert built.returncode == 0, built.stderr
    output = tmp_path / 'plan'
    planned = subprocess.run([sys.executable, str(EXPERIMENT), '--plan-only', '--input', str(packets),
                              '--output', str(output), '--seconds-per-prover', '7',
                              '--public-timeout-seconds', '123'],
                             capture_output=True, text=True, timeout=30)
    assert planned.returncode == 0, planned.stdout + planned.stderr
    plan = json.loads((output / 'plan.json').read_text())
    source = json.loads((packets / 'manifest.json').read_text())
    assert [r['id'] for r in plan['rows']] == [g['id'] for g in source['obligations']]
    assert plan['verifier_launched'] is False
    for row in plan['rows']:
        command = row['command']
        assert row['public_timeout_seconds'] == 123
        assert command[command.index('-wp-timeout') + 1] == '7'
        assert all(flag in command for flag in ('-wp-rte','-wp-no-filter-init','-wp-smoke-tests'))
        assert command[command.index('-wp-cache') + 1] == 'none'
        assert command[command.index('-rte-initialized') + 1] == '@all'
        if row['kind'] == 'check_lemma':
            assert command[command.index('-wp-prop') + 1] == '+' + row['goal']
        else:
            assert '-wp-fct=t25_ctor_numeric' in command


def test_execution_boundary_checks_source_and_forwards_the_real_leaf_timeout(tmp_path):
    forbidden = tmp_path / 'must-not-run'
    marker = tmp_path / 'formal-tool-was-probed'
    forbidden.write_text('#!/bin/sh\n: > ' + str(marker) + '\nexit 99\n')
    forbidden.chmod(0o755)
    env = {**os.environ, 'SWDB_FRAMA_C': str(forbidden)}
    rejected = subprocess.run([sys.executable, str(EXPERIMENT), '--run-admitted',
                               '--expected-commit', '0'*40, '--output', str(tmp_path / 'actual')],
                              capture_output=True, text=True, timeout=30, env=env)
    assert rejected.returncode != 0
    assert 'source commit' in rejected.stdout + rejected.stderr
    assert not marker.exists()
    output = tmp_path / 'timeout-control'
    controlled = subprocess.run([sys.executable, str(EXPERIMENT), '--process-control',
                                 '--control-sleep-seconds', '4', '--public-timeout-seconds', '1',
                                 '--output', str(output)],
                                capture_output=True, text=True, timeout=15, env=env)
    assert controlled.returncode != 0
    resource = json.loads((output / 'resources.json').read_text())
    assert resource['timed_out'] is True
    assert resource['wall_seconds'] < 3
    assert not marker.exists()


def test_global_targets_include_constructive_source_premise_witnesses(tmp_path):
    output = tmp_path / 'packets'
    built = subprocess.run([sys.executable, str(CLI), 'prepare', '--output', str(output)],
                           capture_output=True, text=True, timeout=30)
    assert built.returncode == 0, built.stderr
    manifest = json.loads((output / 'manifest.json').read_text())
    goals = {g['id']: g for g in manifest['obligations']}
    for name in ('control.ctor.premises_feasible', 'control.dtor.premises_feasible'):
        assert goals[name]['expected'] == 'proven'
        assert '==>' not in goals[name]['statement']
    assert manifest['semantic_relations']['incoming_heap'].startswith('arbitrary')
    assert manifest['semantic_relations']['premise_witnesses'] == 'concrete feasibility controls only; never restrictions on arbitrary incoming heaps'


@pytest.mark.parametrize('case,expected', [
    ('target_unknown', True), ('unclassified', False), ('unrelated_open', False),
    ('numeric_without_smoke', False), ('numeric_smoke', True),
    ('timed_out', False), ('out_of_memory', False),
])
def test_result_policy_requires_exact_semantic_target_and_numeric_nonvacuity(tmp_path, case, expected):
    target = 'lemma_t25_control_stale_read'
    goal = {'goal': 'g1', 'property': target, 'status': 'unknown', 'smoke': False}
    payload = {'row': {'kind': 'check_lemma', 'goal': 't25_control_stale_read', 'expected': 'not_proven'},
               'resources': {'exit_code': 0, 'timed_out': False, 'out_of_memory': False},
               'reading': {'verdict': 'not_proven', 'failure_class': 'unknown', 'goals': [goal]},
               'inventory': {'properties': [{'property': target, 'kind': 'lemma'}]}}
    if case == 'unclassified':
        payload['reading']['failure_class'] = 'unclassified_wp_outcome'
    elif case == 'unrelated_open':
        payload['reading']['goals'] = [{**goal, 'status': 'valid'}, {**goal, 'goal': 'g2', 'property': 'unrelated'}]
    elif case.startswith('numeric_'):
        payload['row'] = {'kind': 'c_kernel', 'goal': 't25_ctor_numeric', 'expected': 'proven'}
        payload['reading'] = {'verdict': 'proven', 'failure_class': None, 'goals': [{**goal, 'status': 'valid'}]}
        if case == 'numeric_smoke':
            payload['reading']['goals'].append({**goal, 'goal': 's1', 'status': 'valid', 'smoke': True})
    elif case in ('timed_out', 'out_of_memory'):
        payload['resources'][case] = True
    source = tmp_path / 'reading.json'
    source.write_text(json.dumps(payload))
    result = subprocess.run([sys.executable, str(EXPERIMENT), '--check-result', '--input', str(source),
                             '--output', str(tmp_path / 'policy')], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    checked = json.loads((tmp_path / 'policy/result-policy.json').read_text())
    assert checked['matches_expected'] is expected
    assert checked['verifier_launched'] is False


def test_actual_output_inside_checkout_is_rejected_before_source_or_tool_probe(tmp_path):
    output = ROOT / '.scratch' / 't25-must-not-create-output'
    assert not output.exists()
    result = subprocess.run([sys.executable, str(EXPERIMENT), '--run-admitted', '--expected-commit', '0'*40,
                             '--output', str(output)], capture_output=True, text=True, timeout=30)
    assert result.returncode != 0
    assert 'outside the source checkout' in result.stdout + result.stderr
    assert not output.exists()


def test_import_search_path_is_available_to_initial_parse_before_then(tmp_path):
    inputs = tmp_path / 'packets'
    made = subprocess.run([sys.executable, str(CLI), 'prepare', '--output', str(inputs)],
                          capture_output=True, text=True, timeout=30)
    assert made.returncode == 0, made.stderr
    output = tmp_path / 'plan'
    planned = subprocess.run([sys.executable, str(EXPERIMENT), '--plan-only', '--input', str(inputs),
                              '--output', str(output)], capture_output=True, text=True, timeout=30)
    assert planned.returncode == 0, planned.stderr
    for row in json.loads((output / 'plan.json').read_text())['rows']:
        command = row['command']
        before_parse = command[:command.index('wp_input.c')]
        assert '-wp-library' in before_parse
        assert before_parse[before_parse.index('-wp-library')+1] == str(inputs / 'theory')
        after_then = command[command.index('-then')+1:]
        assert after_then[after_then.index('-wp-library')+1] == str(inputs / 'theory')


def test_heap_exported_names_avoid_why3_effect_keywords_and_bind_packet_references(tmp_path):
    import re
    inputs = tmp_path / 'packets'
    made = subprocess.run([sys.executable, str(CLI), 'prepare', '--output', str(inputs)],
                          capture_output=True, text=True, timeout=30)
    assert made.returncode == 0, made.stderr
    theory = (inputs / 'theory/heap_bridge.mlw').read_text()
    declared = set(re.findall(r'\b(?:predicate|function|type)\s+([A-Za-z_]\w*)', theory))
    assert not declared & {'reads', 'writes'}  # Why3 1.8.2 effect-clause keywords.
    manifest = json.loads((inputs / 'manifest.json').read_text())
    used = set()
    for goal in manifest['obligations']:
        used.update(re.findall(r'Heap::([A-Za-z_]\w*)', (inputs / goal['path']).read_text()))
    assert used <= declared
