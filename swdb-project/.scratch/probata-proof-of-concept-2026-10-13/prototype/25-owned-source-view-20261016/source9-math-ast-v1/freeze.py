"""2026-10-16 ET. Inert stdlib packet assembly; never runs the observer main."""
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
        stream.write((json.dumps(value, indent=2, sort_keys=True)+'\n').encode())


def main():
    context_text = (HERE/'context.json').read_text()
    context = json.loads(context_text)
    prior = Path(context['prior_capture']['path'])
    assert pin(prior) == context['prior_capture']
    assert pin(prior)['sha256'] == '2ec440bcc9c282c3dfeec44f98c79a6861c6882c19ad8b2cb8913b8880dc1e9c'
    old = json.loads(prior.read_bytes())
    assert len(context['tasks']) == 26 and len(context['theories']) == 3
    assert context['tasks'] == [{'id': x['id'], 'artifact': x['artifact'], 'complete_command_census': x['complete_command_census']}
                                for x in old['materialized_tasks']]
    assert [x['normal_verdict'] for x in context['retained_outcomes']] == ['proven']*8+['not_proven']
    lineage = json.loads((HERE/'syntax-lineage.json').read_bytes())
    assert pin(Path(lineage['parent_syntax_file']['path'])) == lineage['parent_syntax_file']
    before = ast.parse(Path(lineage['parent_syntax_file']['path']).read_bytes())
    after = ast.parse((HERE/'syntax.py').read_bytes())
    for name in ('need', 'digest', 'forms'):
        original = next(n for n in before.body if isinstance(n, ast.FunctionDef) and n.name == name)
        selected = next(n for n in after.body if isinstance(n, ast.FunctionDef) and n.name == name)
        assert ast.dump(original, include_attributes=False) == ast.dump(selected, include_attributes=False)
    entry = (HERE/'syntax.py').read_text()+'\n\nCONTEXT = json.loads('+repr(context_text)+')\n\n'+(HERE/'observer.py').read_text()
    compile(ast.parse(entry), '<inert-complete26-math-AST-capture>', 'exec')
    with (HERE/'entry.py').open('xb') as stream:
        stream.write(entry.encode())
    command = {'date': '2026-10-16 ET', 'status': 'INERT_REVIEW_AND_FRESH_ROOT_ADMISSION_REQUIRED',
        'host': 'mbit10', 'stdin': pin(HERE/'entry.py'),
        'argv_after_fresh_scoped_root_preflight': ['/usr/bin/timeout', '--signal=TERM', '--kill-after=5s', '120s',
            '/usr/bin/env', '-i', 'HOME=/nonexistent', 'LANG=C', 'LC_ALL=C', 'PATH=/usr/bin:/bin',
            'PYTHONDONTWRITEBYTECODE=1', '/usr/bin/python3', '-I', '-B', '-'],
        'internal_alarm_seconds': 110, 'outer_timeout_seconds': 120, 'local_timeout_seconds': 130,
        'address_space_bytes': 512*1024**2, 'CPU_limit_set': False,
        'stdout_cap_bytes': 2*1024*1024, 'stderr_cap_bytes': 32768, 'max_input_bytes': 1024*1024,
        'max_atom_bytes': 2048, 'max_term_depth': 160,
        'expected_complete_metadata_exit_code': 2,
        'scope': 'Complete parsed mathematical command metadata only. No actual query, proof/scientific/source admission, project imports or tools. Root must separately admit exact stdin bytes and retain finite pre/postflight.'}
    write(HERE/'command.json', command)
    packet = {'date': '2026-10-16 ET', 'classification': 'FROZEN_INERT_SOURCE9_COMPLETE26_MATH_AST_METADATA',
        'inputs': [pin(prior), lineage['parent_syntax_file']],
        'outputs': [pin(HERE/name) for name in ('syntax.py', 'syntax-lineage.json', 'observer.py', 'context.json',
                    'pure_controls.py', 'pure-controls-v1.log', 'pure-controls-final.log', 'README.md', 'freeze.py', 'entry.py', 'command.json')],
        'exact_helpers_only': ['need', 'digest', 'forms'], 'semantic_helpers_or_normalization_reused': False,
        'retained_task_count': 26, 'physical_input_count': 29,
        'complete_ordered_command_census_required': True,
        'complete_deduplicated_math_trees': ['declare-sort', 'declare-fun', 'declare-const', 'declare-datatype', 'declare-datatypes', 'define-fun', 'assert'],
        'administrative_payload_exported': False, 'original_C_Cpp_TU_theory_contents_or_raw_files_exported': False,
        'pure_controls': {'passed': 18, 'child_native_network_attempts': [], 'actual_reader_main_executed': False},
        'actual_SSH_compiler_native_verifier_solver_or_scientific_execution': False,
        'all_scientific_math_source_Heap_Typed_caller_default_admission_false': True,
        'independent_parent_Spec_and_root_complementary_review_required': True,
        'fresh_root_once_only_admission_required': True}
    write(HERE/'source-packet.json', packet)
    preparation = {'date': '2026-10-16 ET', 'classification': 'INERT_AUTHOR_PREPARATION_ONLY',
        'packet': pin(HERE/'source-packet.json'), 'entry': pin(HERE/'entry.py'), 'command': pin(HERE/'command.json'),
        'observer': pin(HERE/'observer.py'), 'syntax': pin(HERE/'syntax.py'),
        'exact_prior_capture': context['prior_capture'], 'source_commit': context['source_commit'], 'raw_root': context['raw_root'],
        'producer': context['producer'], 'task_count': 26, 'physical_input_count': 29,
        'pure_controls': packet['pure_controls'], 'closed_move_files_changed': False,
        'no_actual_reader_or_project_tool_or_remote_execution': True,
        'acceptance': 'All semantic/scientific/source/Heap/Typed/caller/default/record flags remain false; expected completed metadata exit2.'}
    target = POC/'evidence/t25-owned-source9-math-ast-capture-preparation-v1-20261016.json'
    write(target, preparation)
    print(json.dumps({'preparation': pin(target), 'packet': pin(HERE/'source-packet.json'),
                      'entry': pin(HERE/'entry.py'), 'command': pin(HERE/'command.json')}, indent=2))


if __name__ == '__main__':
    main()
