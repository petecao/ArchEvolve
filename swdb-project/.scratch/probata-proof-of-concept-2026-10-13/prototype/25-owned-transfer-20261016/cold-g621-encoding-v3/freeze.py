"""2026-10-16 ET. Inert metadata-only packet assembly, never observer execution."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(path, value):
    with path.open('xb') as stream:
        stream.write((json.dumps(value, indent=2, sort_keys=True) + '\n').encode())


def main():
    previous = HERE.parent / 'cold-g621-encoding-v2'
    context_text = (HERE / 'context.json').read_text()
    context = json.loads(context_text)
    original_context = json.loads((previous / 'context.json').read_bytes())
    assert {k: v for k, v in context.items() if k != 'standard_abs_source'} == original_context
    assert len(context['tasks']) == 20
    capture = POC / 'evidence/t25-owned-transfer10-encoding-v2-actual-stdout-20261016.json'
    assert pin(capture)['sha256'] == 'b04c4ae7f0497edeaaca697c58b7310eb1c1bdc70a0190cf90d1a5bf5af9691c'
    primary = Path('/Users/yanrujhou/.opam/framac-33/share/why3/stdlib/int.mlw')
    raw = primary.read_bytes()
    assert pin(primary)['sha256'] == context['standard_abs_source']['sha256']
    begin, end = context['standard_abs_source']['module_byte_range']
    assert hashlib.sha256(raw[begin:end]).hexdigest() == context['standard_abs_source']['module_body_sha256']
    inverse = json.loads((HERE / 'full-source-inverses.json').read_bytes())
    for row in inverse['files']:
        restored = (HERE / row['filename']).read_text()
        assert hashlib.sha256(restored.encode()).hexdigest() == row['successor_sha256']
        for edit in reversed(row['edits']):
            assert restored[edit['new_start']:edit['new_end']] == edit['after']
            restored = restored[:edit['new_start']] + edit['before'] + restored[edit['new_end']:]
        assert restored == (previous / row['filename']).read_text()
    entry = '\n\n'.join([(HERE / 'semantic_terms.py').read_text(),
                           (HERE / 'encoding_probe.py').read_text(),
                           'CONTEXT = json.loads(' + repr(context_text) + ')',
                           (HERE / 'observer.py').read_text()])
    compile(ast.parse(entry), '<inert-frozen-encoding-v3>', 'exec')
    with (HERE / 'entry.py').open('xb') as stream:
        stream.write(entry.encode())
    command = json.loads((previous / 'command.json').read_bytes())
    command.update(schema='ownership10-g621-bounded-encoding-probe-v3', stdin=pin(HERE / 'entry.py'))
    write(HERE / 'command.json', command)
    packet = {
        'date': '2026-10-16 ET', 'classification': 'FROZEN_INERT_COMPLETE20_ENCODING_COMPARISON_V3',
        'inputs': [pin(previous / name) for name in
                   ('source-packet.json', 'semantic_terms.py', 'encoding_probe.py', 'observer.py', 'context.json', 'command.json')]
                  + [pin(capture), pin(POC / 'evidence/t25-owned-transfer10-cold-v3-root-stdout-20261016.json'),
                     pin(primary)],
        'outputs': [pin(HERE / name) for name in
                    ('semantic_terms.py', 'encoding_probe.py', 'observer.py', 'context.json',
                     'inverse.json', 'full-source-inverses.json', 'authoring-history.json',
                     'pure_controls.py', 'pure-controls-initial.log', 'pure-controls-final.log',
                     'README.md', 'freeze.py', 'entry.py', 'command.json')],
        'pure_controls': {'passed': 21, 'child_native_network_attempts': [],
                          'scope': 'Synthetic and retained-metadata source controls only; no actual task query or scientific run.'},
        'canonical_identities_added': ['complete_right_associated_implication_chain', 'complete_mathematical_SMT_plus_operand_commutation'],
        'source_definition_attribution': context['standard_abs_source'],
        'complete_predecessor_source_inverses': True,
        'same20task_complete_command_censuses': True,
        'selected_files': 22,
        'full_body_or_type_encoding_adoption': False,
        'unknown_definitions_and_support_remain_pending': True,
        'actual_query_executed': False, 'actual_tools_executed': False,
        'mathematical_acceptance': False, 'scientific_acceptance': False,
        'source_body_Typed_caller_default_or_public_record_acceptance': False,
        'root_exact_admission_required': True}
    write(HERE / 'source-packet.json', packet)
    receipt = {
        'date': '2026-10-16 ET', 'classification': 'PREPARATION_ONLY; INDEPENDENT_REVIEW_AND_ROOT_ADMISSION_REQUIRED',
        'packet': pin(HERE / 'source-packet.json'), 'entry': pin(HERE / 'entry.py'),
        'command': pin(HERE / 'command.json'), 'source_inverse': pin(HERE / 'full-source-inverses.json'),
        'pure_controls': packet['pure_controls'], 'source_definition_attribution': context['standard_abs_source'],
        'unchanged20task_source_and_support_context': True,
        'changed_existing_functions': ['canon', 'inspect_task', 'main'],
        'added_function': 'absolute_definition',
        'no_actual_compiler_native_solver_project_or_remote_execution': True,
        'all_acceptance_false': True}
    target = POC / 'evidence/t25-owned-transfer10-encoding-v3-preparation-20261016.json'
    write(target, receipt)
    print(json.dumps({'preparation': pin(target), 'packet': pin(HERE / 'source-packet.json'),
                      'entry': pin(HERE / 'entry.py'), 'command': pin(HERE / 'command.json')}, indent=2))


if __name__ == '__main__':
    main()
