"""2026-10-16 ET. Inert four-phase memory-fixture observation assembly.

No compiler, project import, child, native, solver or network may run here.
The new observation stops before JSON/source/ABI interpretation. Its exact
success boundary is four complete compiler outputs with the inherited physical
source/runtime/dependency/resource checks; public admission remains separate.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys

EVENTS = []
def no_child(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('inert memory-capture assembly refuses ' + event)
sys.addaudithook(no_child)

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
OLD = WHOLE / 'compiler-capture-v10'
OLD_NAME = 'probata-resume-20261016-t28-full-tu-2baf722f-v10'
NEW_NAME = 'probata-resume-20261016-t28-memory-tu-2baf722f-v1'
SOURCE_SHA = '55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'

def pin(path, expected=None):
    path = Path(path).resolve(strict=True)
    data = path.read_bytes()
    result = {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if expected is not None:
        assert result['sha256'] == expected, str(path)
    return result

def write(name, value):
    (HERE / name).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')

def changes(old, new, path=()):
    if type(old) is dict and type(new) is dict:
        result = []
        for key in sorted(set(old) | set(new)):
            if key not in old: result.append({'path': [*path, key], 'new': new[key], 'added': True})
            elif key not in new: result.append({'path': [*path, key], 'old': old[key], 'removed': True})
            else: result.extend(changes(old[key], new[key], (*path, key)))
        return result
    if old != new or type(old) is not type(new):
        return [{'path': list(path), 'old': old, 'new': new}]
    return []

def main():
    old_entry = pin(OLD / 'linux_compiler_capture_v10.py', '095eee7198167f5e89ae3a64deb2c42e8097951d957a91de0a7c8fd6efb60810')
    source = pin(WHOLE / 'source-memory-fixtures-v1/same_thread_memory_v1.cpp', SOURCE_SHA)
    text = Path(old_entry['path']).read_text()
    original = text
    edits = []
    def replace(before, after):
        nonlocal text
        assert text.count(before) == 1, before[:100]
        text = text.replace(before, after, 1)
        edits.append({'old': before, 'new': after})

    replace('RAW_NAME = "' + OLD_NAME + '"', 'RAW_NAME = "' + NEW_NAME + '"')
    replace('MINIFIER_SHA = "b866e14fe3ca210de178aab71f5c8a662e15f818a5ca485095487b005ae51897"\n', '')
    replace('BINDER_SHA = "217cdda6ca8eaea99526010f2c379dad963ca81c18c79322ce02ab8cc9296ed8"\n',
            'MEMORY_SOURCE_SHA = "' + SOURCE_SHA + '"\n')
    start = text.index('def check_prepared(')
    end = text.index('\ndef finalization_payloads(', start)
    replace(text[start:end], '')
    insertion = '''def memory_observation_recipe(adapter, *, compiler, project, raw):
    """Keep the complete original caller TU and independent ABI-literal parse."""
    recipe = lossless_recipe(adapter, compiler=compiler, project=project, raw=raw)
    old_source = str(Path(raw) / "control/source_call_fixture_v2.cpp")
    new_source = str(Path(raw) / "control/same_thread_memory_v1.cpp")
    for item in recipe["commands"][:2]:
        if item["argv"].count(old_source) != 1:
            raise ValueError("exact inherited original-source caller recipe required")
        item["argv"] = [new_source if token == old_source else token for token in item["argv"]]
    recipe["lossless_caller_stdout"] = {"codec": "gzip-single-member", "expanded_limit": 2147483648,
        "retained_file_limit": STAGE_BYTES, "unfiltered_original_frontend_stdout": True,
        "expanded_memory_is_not_retained_disk_bytes": True, "raw_full_DOM_materialized": False,
        "AST_or_ABI_interpreted_in_measurement": False,
        "mandatory_downstream": "strict complete-stream role normalization/inverse, original source/runtime/dependency closure, same-TU/ABI/call/body admission"}
    return recipe


'''
    replace('def stream_caller_ast(', insertion + 'def stream_caller_ast(')
    replace('def main(argv):', '''def complete_observation(commands, groups):
    return (len(groups) == 2 and [row["label"] for row in groups] == ["caller", "abi"]
        and [row["phase"] for row in commands] == ["caller-preprocess", "caller-ast", "abi-preprocess", "abi-ast"]
        and all(type(row.get("returncode")) is int and row["returncode"] == 0 for row in commands))


def main(argv):''')
    replace('    minifier = module("strict_minify_v2.py", MINIFIER_SHA)\n', '')
    replace('    binder = module("whole_interface_v4.py", BINDER_SHA)\n    declarations = binder.inventory(project)\n', '')
    replace('("source_call_fixture_v2.cpp", "compiler_abi_probe_v1.cpp", "m5ops.h")',
            '("same_thread_memory_v1.cpp", "compiler_abi_probe_v1.cpp", "m5ops.h")')
    replace('    original_inputs += [pin(project / row["relative"]) for row in policy["source_inputs"]]',
            '    if original_inputs[0]["sha256"] != MEMORY_SOURCE_SHA or original_inputs[0]["bytes"] != 3258:\n        raise ValueError("exact reviewed three-function memory source required")\n    original_inputs += [pin(project / row["relative"]) for row in policy["source_inputs"]]')
    replace('    recipe = lossless_recipe(adapter, compiler=compiler["command"][0], project=str(project), raw=str(raw))',
            '    recipe = memory_observation_recipe(adapter, compiler=compiler["command"][0], project=str(project), raw=str(raw))')
    replace('    commands, groups, prepared, error, after_errors = [], [], None, None, []',
            '    commands, groups, observation_complete, error, after_errors = [], [], False, None, []')
    replace('source_name = "source_call_fixture_v2.cpp" if label == "caller" else "compiler_abi_probe_v1.cpp"',
            'source_name = "same_thread_memory_v1.cpp" if label == "caller" else "compiler_abi_probe_v1.cpp"')
    begin = text.index('        stream_receipt = json.loads((out / "caller.ast.gzip.json").read_bytes())')
    finish = text.index('    except Exception as failure:', begin)
    replace(text[begin:finish], '        observation_complete = complete_observation(commands, groups)\n')
    replace('accepted = error is None and not after_errors and prepared is not None and len(commands) == 4 and not cache_present and bytes_used() <= TOTAL_BYTES',
            'accepted = error is None and not after_errors and observation_complete and not cache_present and bytes_used() <= TOTAL_BYTES')
    replace('''            "source_names": sorted({row["name"] for row in prepared["calls"]}) if prepared else [],
            "source_call_count": len(prepared["calls"]) if prepared else 0,
            "scope": "Actual Clang source/ABI preparation only; source/CPU/model/public admission remains required",''',
            '''            "compiler_observation_complete": observation_complete,
            "source_names": [], "source_call_count": 0, "source_call_admitted": False, "ABI_interpreted": False,
            "strict_complete_TU_consumer_passed": False,
            "scope": "Actual four-phase Clang observation only; strict complete-stream role normalization and source/runtime/dependency/same-TU/ABI/call/body/public admission remain required",''')
    entry_path = HERE / 'linux_memory_capture_v1.py'
    entry_path.write_text(text)
    # The exact complete predecessor is an opaque review pin, not an executed
    # fallback. Store ordered before/after documents to make removed blocks
    # independently recoverable using the original unique-context edits.
    entry = pin(entry_path)

    old_policy = json.loads((OLD / 'linux_compiler_capture_policy_v10.json').read_bytes())
    old_command = json.loads((OLD / 'linux_compiler_capture_command_v10.json').read_bytes())
    def transform(value):
        if type(value) is str:
            for before, after in [(str(OLD), str(HERE)), (OLD_NAME, NEW_NAME),
                ('linux_compiler_capture_v10.py', 'linux_memory_capture_v1.py'),
                ('linux_compiler_capture_policy_v10.json', 'linux_memory_capture_policy_v1.json'),
                ('source_call_fixture_v2.cpp', 'same_thread_memory_v1.cpp')]:
                value = value.replace(before, after)
            return value
        if type(value) is list: return [transform(item) for item in value]
        if type(value) is dict: return {transform(key): transform(item) for key, item in value.items()}
        return value
    policy = transform(copy.deepcopy(old_policy))
    policy['schema'] = 't28-three-memory-TU-compiler-observation-1'
    policy['entry_sha256'] = entry['sha256']
    namespace = {'__name__': 'inert_recipe', '__file__': str(entry_path)}
    exec(compile(text, str(entry_path), 'exec'), namespace)
    adapter_path = WHOLE / 'streaming-minify-v1/compiler_unit_adapter_v4.py'
    adapter = type('RecipeAdapter', (), {})()
    adapter_ns = {'__name__': 'inert_recipe_adapter', '__file__': str(adapter_path)}
    exec(compile(adapter_path.read_bytes(), str(adapter_path), 'exec'), adapter_ns)
    adapter.capture_recipe = adapter_ns['capture_recipe']
    raw = '/data/yanruj/EvolveSWDB_runs/' + NEW_NAME
    policy['capture_recipe'] = namespace['memory_observation_recipe'](adapter,
        compiler=policy['compiler']['command'][0], project=policy['source_project'], raw=raw)
    staged = []
    for row in old_command['controller_inputs']:
        name = Path(row['path']).name
        if name in {'linux_compiler_capture_policy_v10.json', 'strict_minify_v2.py', 'whole_interface_v4.py'}: continue
        path = Path(transform(row['path']))
        if name == 'source_call_fixture_v2.cpp': path = Path(source['path'])
        staged.append(pin(path))
    policy['controller_files'] = {Path(row['path']).name: {key: row[key] for key in ('bytes', 'sha256')} for row in staged}
    policy['observation_only'] = True
    write('linux_memory_capture_policy_v1.json', policy)
    policy_pin = pin(HERE / 'linux_memory_capture_policy_v1.json')
    command = transform(copy.deepcopy(old_command))
    command['controller_inputs'] = [*staged, policy_pin]
    command['argv'][-1] = policy_pin['sha256']
    command['recipe'] = policy['capture_recipe']
    command['source_call_admission'] = False
    command['root_acceptance'] = ('Four actual commands exit0 with a complete unfiltered lossless original caller stream and independent ABI-literal outputs, '
        'exact source/control/runtime/dependency pre/post closure, bounded healthy guard and finite root settlement. '
        'No AST/ABI interpretation, source/call/body/native/model/public acceptance is granted; separate reviewed strict transport and source consumers remain mandatory.')
    command['status'] = 'INERT: exact compiler-observation-only packet; independent review and root admission required'
    write('linux_memory_capture_command_v1.json', command)
    inverse = {'date': '2026-10-16 ET', 'predecessor': old_entry, 'successor': entry,
        'entry_edits': edits, 'predecessor_policy': pin(OLD / 'linux_compiler_capture_policy_v10.json'),
        'predecessor_command': pin(OLD / 'linux_compiler_capture_command_v10.json'),
        'policy_edits': changes(old_policy, policy), 'command_edits': changes(old_command, command),
        'unchanged_functions': ['_stable_capture_stat', 'pin', 'save', 'recheck', 'original_helpers', 'check_derived_stub',
            'compare_dependencies', 'finalization_payloads', 'finalize_capture', 'bind_zlib', 'lossless_recipe', 'stream_caller_ast'],
        'different_success_boundary': 'Compiler observation only. No strict JSON/source/ABI consumer runs or succeeds here.',
        'resource_source_runtime_dependency_gates_unchanged': True,
        'new_exact_source': source, 'prospective_node': 1, 'actual_execution': False}
    # An independently reproducible edit operation also carries the predecessor
    # offset, avoiding ambiguous insertion positions for removed text.
    state = original
    for edit in edits:
        edit['offset'] = state.index(edit['old'])
        state = state[:edit['offset']] + edit['new'] + state[edit['offset'] + len(edit['old']):]
    assert state == text
    for edit in reversed(edits):
        at = edit['offset']
        assert state[at:at+len(edit['new'])] == edit['new']
        state = state[:at] + edit['old'] + state[at+len(edit['new']):]
    assert state == original and ast.dump(ast.parse(state)) == ast.dump(ast.parse(original))
    write('memory-capture-v1-inverse.json', inverse)
    log = HERE / 'pure-memory-capture-v1-controls.log'
    validation = {'executed': False}
    if log.exists():
        report = json.loads(log.read_text().splitlines()[-1])
        assert report['failures'] == report['errors'] == report['skips'] == 0 and report['child_events'] == []
        assert report['entry_sha256'] == entry['sha256'] and report['controls_sha256'] == pin(HERE / 'test_memory_capture_v1.py')['sha256']
        validation = {'executed': True, 'report': report, 'log': pin(log)}
    packet = {'date': '2026-10-16 ET', 'status': command['status'], 'controller_inputs': command['controller_inputs'],
        'command': pin(HERE / 'linux_memory_capture_command_v1.json'), 'inverse': pin(HERE / 'memory-capture-v1-inverse.json'),
        'preparation': pin(__file__), 'controls': pin(HERE / 'test_memory_capture_v1.py'), 'validation': validation,
        'predecessor_packet': pin(OLD / 'compiler-capture-source-packet-v10.json'),
        'fixture_packet': pin(WHOLE / 'source-memory-fixtures-v1/source-memory-fixture-packet-v1.json'),
        'controls_bytes': sum(row['bytes'] for row in command['controller_inputs']),
        'expanded_original_stream_limit_bytes': 2147483648, 'caller_ast_phase_seconds': 120,
        'other_phase_seconds': 45, 'retained_per_file_bytes': 134217728, 'retained_total_bytes': 268435456,
        'finalization_reserve_bytes': 1048576, 'guard_seconds': 180, 'entry_seconds': 165, 'rss_bytes': 4294967296,
        'native_or_solver_executed': False, 'AST_or_ABI_interpreted': False,
        'source_call_admitted': False, 'public_proof': False, 'current_0_2': False, 'full_ticket28': False}
    assert packet['controls_bytes'] < 1048576 and not EVENTS
    write('memory-capture-source-packet-v1.json', packet)
    print(json.dumps(pin(HERE / 'memory-capture-source-packet-v1.json'), sort_keys=True))

if __name__ == '__main__': main()
