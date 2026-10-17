"""2026-10-16 ET. Build a fixed private observation package, no project import."""
import ast
import builtins
import hashlib
import json
from pathlib import Path
import symtable

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent


def sha(raw): return hashlib.sha256(raw).hexdigest()


def main():
    modules = HERE / 'modules'
    inputs = {
        'swdb._dx100_whole.whole_interface_v4': WHOLE / 'whole_interface_v4.py',
        'swdb._dx100_whole.compiler_unit_adapter_v3': WHOLE / 'lossless-capture-v1/compiler_unit_adapter_v3.py',
        'swdb._dx100_whole.receiver_state_draws_v2': WHOLE / 'receiver-state-draws-v2/receiver_state_draws_v2.py',
        'swdb.dx100_whole_checked': WHOLE / 'checked-contracts-v2/dx100_whole_checked_v2.py'}
    for name in ('lossless_gzip_v2', 'role_normalized_gzip_v2', 'closed_python_surface',
                 'normalized_compiler_adapter_v1', 'normalized_capture_ingress_v2'):
        inputs['swdb._dx100_whole.' + name] = WHOLE / 'normalized-ingress-v2/proposed' / (name + '.py')
    rows = []
    for name, origin in inputs.items():
        raw = origin.read_bytes(); target = modules / origin.name; target.write_bytes(raw)
        rows.append({'module': name, 'file': target.name, 'bytes': len(raw), 'sha256': sha(raw),
                     'origin': str(origin)})
    source_path = WHOLE / 'production-route-v3/proposed/swdb/dx100_checked_source.py'
    source = source_path.read_text(); tree = ast.parse(source)
    names = {'Refused', 'need', 'sha', 'canonical', 'digest', 'Inputs'}
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    assert {node.name for node in nodes} == names
    bridge = '''"""2026-10-16 ET. Fixed private observation bridge, not public SourceUnit admission."""
import hashlib
import json
from pathlib import Path
import stat
from swdb import dx100_whole_checked as contracts
from swdb._dx100_whole import whole_interface_v4 as binder
from swdb._dx100_whole import compiler_unit_adapter_v3 as compiler
from swdb._dx100_whole import receiver_state_draws_v2 as receiver
CAPTURE_KIND = 'lossless-complete-original-tu-v1'

def complete_capture(*args, **kwargs):
    raise ValueError('private normalized observation cannot delegate legacy capture')

'''
    bridge += '\n\n'.join(ast.get_source_segment(source, node) for node in nodes) + '\n'
    path = modules / 'observation_source_bridge_v1.py'; path.write_text(bridge)
    rows.insert(4, {'module': 'swdb.dx100_checked_source', 'file': path.name, 'bytes': path.stat().st_size,
        'sha256': sha(path.read_bytes()), 'origin': str(source_path), 'exact_nodes': sorted(names)})
    ingress_path = WHOLE / 'normalized-ingress-v2/proposed/normalized_capture_ingress_v2.py'
    original = ingress_path.read_text()
    node = next(node for node in ast.parse(original).body if isinstance(node, ast.FunctionDef) and node.name == 'complete_capture')
    old = ast.get_source_segment(original, node)
    new = old.replace('def complete_capture(', 'def observe_capture(', 1)
    new = new.replace("    selected=policy['capture']\n", "    selected=policy['capture']\n"
        "    need(type(selected) is dict and selected.get('kind')==KIND and selected.get('prepared') is None,\n"
        "        'observation requires exact normalized kind and explicit unknown preparation output')\n", 1)
    before = "need(prepared==reads.document(selected['prepared']) and prepared['raw_full_tu_sha256']==NORMALIZED_SHA,\n        'fresh complete actual-TU/ABI/declaration/call preparation differs')"
    after = "need(prepared['raw_full_tu_sha256']==NORMALIZED_SHA,\n        'fresh normalized parser input identity differs during observation')"
    assert new.count(before) == 1; new = new.replace(before, after, 1)
    table = symtable.symtable(old, str(ingress_path), 'exec').lookup('complete_capture').get_namespace()
    def globals_in(scope):
        result = {item.get_name() for item in scope.get_symbols() if item.is_global() and item.is_referenced()}
        for child in scope.get_children(): result.update(globals_in(child))
        return result
    imported = sorted(globals_in(table) - set(vars(builtins)))
    prefix = '"""2026-10-16 ET. Data-only bootstrap; public equality ingress is unchanged."""\n'
    prefix += 'from swdb._dx100_whole.normalized_capture_ingress_v2 import (' + ', '.join(imported) + ')\n\n'
    path = modules / 'normalized_unit_observation_v1.py'; path.write_text(prefix + new + '\n')
    rows.append({'module': 'swdb._dx100_whole.normalized_unit_observation_v1', 'file': path.name,
                 'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes()), 'origin': str(ingress_path)})
    inverse = {'date': '2026-10-16 ET', 'original_complete_capture': old, 'observation_capture': new,
        'restoration_edits': [{'old': 'def observe_capture(', 'new': 'def complete_capture('},
            {'old': "    need(type(selected) is dict and selected.get('kind')==KIND and selected.get('prepared') is None,\n        'observation requires exact normalized kind and explicit unknown preparation output')\n", 'new': ''},
            {'old': after, 'new': before}],
        'semantics': 'Emit computed preparation data instead of reading expected preparation; no source or public admission.'}
    restored = new
    for edit in inverse['restoration_edits']:
        assert restored.count(edit['old']) == 1; restored = restored.replace(edit['old'], edit['new'], 1)
    assert restored == old
    (HERE / 'observer-inverse-v1.json').write_text(json.dumps(inverse, sort_keys=True, indent=2) + '\n')
    (HERE / 'fixed-modules-v1.json').write_text(json.dumps({'date': '2026-10-16 ET', 'modules': rows,
        'scope': 'Fixed private staged namespaces; not an installed production package.'}, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'modules': len(rows), 'total_bytes': sum(row['bytes'] for row in rows), 'actual_observation': False}))


if __name__ == '__main__': main()
