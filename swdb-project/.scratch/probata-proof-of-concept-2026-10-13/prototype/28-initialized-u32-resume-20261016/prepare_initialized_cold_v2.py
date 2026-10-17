"""2026-10-16 ET. Deterministic SOURCE ONLY cold-reader successor builder.

No project import, Git, compiler, native process, verifier, SSH or actual audit.
Root separately supplies the published commit and runtime-controller version;
pending outputs refuse admission. Every V1 input remains untouched.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
PROJECT = next(parent for parent in HERE.parents if parent.name == 'swdb-project')
PRODUCER = PROJECT / 'swdb/dx100_initialized_register_source.py'
PRODUCER_SHA = '01c043e544e50c30fc3d92b6be5a8b097f4dfef0606f53c29068a2ba008ac145'
OLD_COMMIT = '2baf722fdaa6cba24b859eae3172a6f597417d72'
BASES = {
    'passive_initialized_certificate_rechecker_v1.py': '41edf13d21aae4cd852b0acc4d917012e4718d91a5ceba100e587d003ca6d4ed',
    'initialized_cold_obligations_v1.py': 'dfc647552f4a1bbfd33cc4745289257a9aca4e8b587ce45ca9aa757066950dc9',
    'initialized_cold_identities_v1.py': 'eaef8aeca8a448566ff724e0d7c06fbf89c1f59b985ef7dcbad0fa06009f4049',
    'initialized_cold_audit_v1.py': '9530165f5eec29e6931db739ad52b6ebe86333a69106034f7d009e8644508271',
}
OBSERVER_CHANGED = {'_assertion', '_bodies', '_operations'}
OBSERVER_ADDED = {'_assert_source_location_diagnostics', '_counter_bound_flow'}
TRUST_HELPER_SHA = '4d55a093a7a92eeb57c9878760bc48ae71c6d5683bbdbf50760be15997cb0982'


def no_child(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.', 'ctypes.dlopen')) or event == 'os.system':
        raise RuntimeError('cold V2 source builder refuses ' + event)


sys.addaudithook(no_child)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    raw = path.read_bytes()
    return {'bytes': len(raw), 'sha256': sha(raw)}


def named_nodes(text):
    result = {}
    for node in ast.parse(text).body:
        name = node.name if isinstance(node, (ast.FunctionDef, ast.ClassDef)) else (
            node.targets[0].id if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) else None)
        if name is not None:
            if name in result: raise ValueError('duplicate top-level source node: ' + name)
            result[name] = node
    return result


def literal(text, name):
    return ast.literal_eval(named_nodes(text)[name].value)


def segment(text, node):
    return ast.get_source_segment(text, node)


def changed_definitions(left, right):
    left, right = named_nodes(left), named_nodes(right)
    changed = {name for name in left.keys() & right.keys()
               if ast.dump(left[name]) != ast.dump(right[name])}
    return changed, set(right) - set(left), set(left) - set(right)


def replacements(text, values):
    nodes = named_nodes(text)
    lines = text.splitlines(keepends=True)
    edits = []
    for name, value in values.items():
        node = nodes[name]
        # All replaced top-level nodes begin at column zero and end at their
        # final non-newline character. Preserve all surrounding source bytes.
        assert node.col_offset == 0
        original = segment(text, node)
        start = sum(len(line) for line in lines[:node.lineno - 1])
        assert text[start:start + len(original)] == original
        edits.append((start, start + len(original), value))
    for start, stop, value in sorted(edits, reverse=True): text = text[:start] + value + text[stop:]
    ast.parse(text)
    return text


def build(source_commit=None, runtime_controller_version=None):
    if (source_commit is None) != (runtime_controller_version is None):
        raise ValueError('published commit and controller version must be supplied together')
    if source_commit is not None and (not isinstance(source_commit, str) or not re.fullmatch(r'[0-9a-f]{40}', source_commit)
            or source_commit == OLD_COMMIT or type(runtime_controller_version) is not int or runtime_controller_version != 4):
        raise ValueError('explicit new full published commit and reviewed runtime controller version4 required')
    source_raw = PRODUCER.read_bytes()
    if sha(source_raw) != PRODUCER_SHA: raise ValueError('integrated observer physical bytes changed')
    source = source_raw.decode()
    bases = {}
    for name, expected in BASES.items():
        raw = (HERE / name).read_bytes()
        if sha(raw) != expected: raise ValueError('frozen V1 input changed: ' + name)
        bases[name] = raw.decode()
    base_raw = (HERE / 'source-location-repair-proposal-v1/base-source.py').read_bytes()
    if sha(base_raw) != 'c023a4a6298fab7a34f4213f888b6c0fb4fe5c405e5a53741942e3e2accb81cb':
        raise ValueError('frozen old observer baseline changed')
    base_source = base_raw.decode()
    changes, added, removed = changed_definitions(base_source, source)
    if changes != OBSERVER_CHANGED or added != OBSERVER_ADDED or removed:
        raise ValueError('integrated observer scope is not the reviewed exact five-node delta')
    old = bases['passive_initialized_certificate_rechecker_v1.py']
    old_nodes, current_nodes = named_nodes(old), named_nodes(source)
    copies = literal(old, 'COPIED_SOURCE_NODES')
    for row in copies:
        actual = segment(old, old_nodes[row['name']])
        if sha(actual.encode()) != row['sha256']: raise ValueError('V1 copied node changed: ' + row['name'])
        if row['name'] not in OBSERVER_CHANGED and actual != segment(source, current_nodes[row['name']]):
            raise ValueError('unreviewed producer primitive changed: ' + row['name'])
    origins = literal(old, 'ORIGIN_PINS')
    for row in origins:
        path = PROJECT / row['relative']; actual = pin(path)
        if row['relative'] != 'swdb/dx100_initialized_register_source.py' and actual != {key: row[key] for key in ('bytes', 'sha256')}:
            raise ValueError('unchanged origin changed: ' + row['relative'])
        row.update(path=str(path), **actual)
    names = {row['name'] for row in copies} | OBSERVER_ADDED
    new_copies = [{'name': name, 'line_start': current_nodes[name].lineno, 'line_end': current_nodes[name].end_lineno,
                   'sha256': sha(segment(source, current_nodes[name]).encode())}
                  for name in sorted(names, key=lambda name: current_nodes[name].lineno)]
    substitutions = {name: segment(source, current_nodes[name]) for name in OBSERVER_CHANGED}
    substitutions['_operations'] = segment(source, current_nodes['_counter_bound_flow']) + '\n\n' + substitutions['_operations']
    substitutions['_assertion'] = segment(source, current_nodes['_assert_source_location_diagnostics']) + '\n\n' + substitutions['_assertion']
    substitutions.update(ORIGIN_SOURCE_COMMIT='ORIGIN_SOURCE_COMMIT = ' + repr(source_commit),
        ORIGIN_PINS='ORIGIN_PINS = ' + repr(origins), COPIED_SOURCE_NODES='COPIED_SOURCE_NODES = ' + repr(new_copies))
    origin_guard = "    if not isinstance(ORIGIN_SOURCE_COMMIT, str) or not re.fullmatch(r'[0-9a-f]{40}', ORIGIN_SOURCE_COMMIT):\n        raise Refused('V2 published source commit is pending root binding')\n"
    original_origin = segment(old, old_nodes['verify_origin_freeze'])
    marker = '    project = Path(project).resolve()'
    assert original_origin.count(marker) == 1
    substitutions['verify_origin_freeze'] = original_origin.replace(marker, origin_guard + marker)
    rechecker = replacements(old, substitutions)
    rechecker = rechecker.replace('Exact pure producer primitives are copied from published source2baf722f and\npinned below.',
        'Exact pure producer primitives are copied from the reviewed integrated observer\nand pinned below. The V2 published commit is explicit root input; None is pending.')
    assert 'source2baf722f' not in rechecker
    obligations = bases['initialized_cold_obligations_v1.py']
    identity_old = bases['initialized_cold_identities_v1.py']
    identity_leaf = '''def fixture_job_bounds(project):
 # Preserve the exact approved helper default; no project import or execution.
 path=project/'tests/testkit/dx100_trust.py'
 raw=path.read_bytes()
 assert H(raw)=='4d55a093a7a92eeb57c9878760bc48ae71c6d5683bbdbf50760be15997cb0982','reviewed optional-bounds helper changed'
 tree=ast.parse(raw);functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_semantics_fixture']
 assert len(functions)==1
 function=functions[0];names=[arg.arg for arg in function.args.kwonlyargs]
 assert names.count('bounds')==1 and isinstance(function.args.kw_defaults[names.index('bounds')],ast.Constant) and function.args.kw_defaults[names.index('bounds')].value is None
 values=[]
 expected=ast.parse("json.dumps({'threads':1,'input_size':1} if bounds is None else bounds)",mode='eval').body
 for node in ast.walk(function):
  if isinstance(node,ast.Call)and isinstance(node.func,ast.Name)and node.func.id=='run_swdb':
   for index,arg in enumerate(node.args):
    if isinstance(arg,ast.Constant)and arg.value=='--bounds':
     assert index+1<len(node.args) and ast.dump(node.args[index+1])==ast.dump(expected),'unreviewed optional-bounds expression'
     values.append({'threads':1,'input_size':1})
 assert values==[{'threads':1,'input_size':1}],'public fixture launch bounds changed'
 return values[0]'''
    if pin(PROJECT / 'tests/testkit/dx100_trust.py')['sha256'] != TRUST_HELPER_SHA:
        raise ValueError('approved optional-bounds helper physical bytes changed')
    identities = replacements(identity_old, {'fixture_job_bounds': identity_leaf})
    reader_old = bases['initialized_cold_audit_v1.py']
    module_pins = literal(reader_old, 'MODULE_PINS')
    for name, text in (('passive_initialized_certificate_rechecker', rechecker),
                       ('initialized_cold_obligations', obligations), ('initialized_cold_identities', identities)):
        del module_pins[name + '_v1.py']; module_pins[name + '_v2.py'] = sha(text.encode())
    reader = replacements(reader_old, {'SOURCE_COMMIT': 'SOURCE_COMMIT = ' + repr(source_commit) + '\nRUNTIME_CONTROLLER_VERSION = ' + repr(runtime_controller_version),
                                       'MODULE_PINS': 'MODULE_PINS = ' + repr(module_pins)})
    for name in ('passive_initialized_certificate_rechecker', 'initialized_cold_obligations', 'initialized_cold_identities', 'initialized_cold_audit'):
        reader = reader.replace(name + '_v1.py', name + '_v2.py')
    pending_guard = "    assert isinstance(SOURCE_COMMIT, str) and re.fullmatch(r'[0-9a-f]{40}', SOURCE_COMMIT), 'V2 published source commit pending'\n    assert type(RUNTIME_CONTROLLER_VERSION) is int and RUNTIME_CONTROLLER_VERSION == 4, 'V2 reviewed runtime controller version4 pending'\n"
    needle = '    assert __debug__ and not sys.flags.optimize\n'
    assert reader.count(needle) == 1
    reader = reader.replace(needle, needle + pending_guard)
    needle = "expected['runtime_controller_version'] == 4"
    assert reader.count(needle) == 1
    reader = reader.replace(needle, "expected['runtime_controller_version'] == RUNTIME_CONTROLLER_VERSION")
    files = {'passive_initialized_certificate_rechecker_v2.py': rechecker,
             'initialized_cold_obligations_v2.py': obligations,
             'initialized_cold_identities_v2.py': identities, 'initialized_cold_audit_v2.py': reader}
    for value in files.values(): ast.parse(value)
    # Exact inverse proof: replace the permitted changed nodes/metadata and
    # remove the two new helpers. Every other V1 definition stays byte-identical.
    current = named_nodes(rechecker)
    allowed_changed = OBSERVER_CHANGED | {'ORIGIN_SOURCE_COMMIT', 'ORIGIN_PINS', 'COPIED_SOURCE_NODES', 'verify_origin_freeze'}
    for name in old_nodes:
        if name not in allowed_changed and segment(old, old_nodes[name]) != segment(rechecker, current[name]):
            raise ValueError('unreviewed V1 rechecker strictification changed: ' + name)
    assert set(current) - set(old_nodes) == OBSERVER_ADDED
    for row in new_copies:
        assert sha(segment(rechecker, current[row['name']]).encode()) == row['sha256']
    assert obligations.encode() == (HERE / 'initialized_cold_obligations_v1.py').read_bytes()
    assert changed_definitions(identity_old, identities) == ({'fixture_job_bounds'}, set(), set())
    metadata = {'date': '2026-10-16 ET', 'status': 'SOURCE ONLY; root commit/version pending; admission refused' if source_commit is None else 'SOURCE ONLY; root-provided commit/version bound; independent review/admission required',
        'source_commit': source_commit, 'runtime_controller_version': runtime_controller_version,
        'origin_binding': 'Explicit root claim; builder checks physical source bytes and node provenance, never invokes Git or verifies publication.',
        'integrated_producer': {'relative': str(PRODUCER.relative_to(PROJECT)), **pin(PRODUCER)},
        'preserved_v1': {name: pin(HERE / name) for name in BASES},
        'new_files': {name: {'bytes': len(value.encode()), 'sha256': sha(value.encode())} for name, value in files.items()},
        'copied_node_count': len(new_copies), 'copied_nodes': new_copies, 'origin_pins': origins,
        'strictification': {'obligations_byte_identical': True, 'unchanged_rechecker_nodes_byte_identical': True,
            'identity_delta': 'Only exact approved optional-bounds helper default parsing; default unchanged.',
            'reader_delta': 'V2 module filenames/pins, explicit commit and controller version, pending-binding refusal only.',
            'scope_preserved': 'Original conditional partial 711/1107, contracts/method/frame, ordinary obligations, healthy-prover/goal-owner/line/CSV/DAG, full ACSL/whitespace/comment fidelity and phase-one/two refusal.'},
        'actual_audit_or_certificate_checked': False, 'project_import_or_child': False,
        'required_next_step': 'Independent source/inverse review, then root complete source/runtime/raw/reader policy admission; no actual cold read authorized by this builder.'}
    return files, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit')
    parser.add_argument('--runtime-controller-version', type=int)
    args = parser.parse_args()
    files, metadata = build(args.source_commit, args.runtime_controller_version)
    for name, value in files.items(): (HERE / name).write_text(value)
    (HERE / 'initialized-cold-v2-provenance.json').write_text(json.dumps(metadata, sort_keys=True, indent=2) + '\n')
    print(json.dumps({name: row for name, row in metadata.items() if name in ('status', 'source_commit', 'runtime_controller_version', 'new_files')}, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
