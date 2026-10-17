"""2026-10-16 ET. Promote exact source bytes into an inert production proposal.

No import or execution of project/prototype code. Runtime imports use the normal
private swdb package. Historical source is data only, never a .scratch import.
"""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
PROJECT = WHOLE.parents[3]
DEST = HERE / 'proposed/swdb/_dx100_whole'
SOURCES = {
    'whole_interface_v4.py': ('whole_interface_v4.py', '217cdda6ca8eaea99526010f2c379dad963ca81c18c79322ce02ab8cc9296ed8'),
    'source_dispatch_v3.py': ('source_dispatch_v3.py', 'd05d3ba716af2d88703636ffbf57bf0834acd5e59ee7ce3aebe0a72648a8b703'),
    'source_argument_staging_v2.py': ('source_argument_staging_v2.py', '79bdae72fd7b4de05771776684b5c6af275afb736313ece1df8790ae57ae6178'),
    'source_statements_v2.py': ('source_statements_v2.py', '49832255fef43afa51078479770d62f01e7e539e4f71f4034e3f2648cb867738'),
    'source_program_globals_v1.py': ('source_program_globals_v1.py', '17bc9b0aefc7cadd5762f630b28c3ab97496f3cac17eb40bbd89deda1fe8cc77'),
    'receiver_state_draws_v2.py': ('receiver-state-draws-v2/receiver_state_draws_v2.py', 'f6c19464a6587b4fbd4a6278dc66be97f1c4ab16d46b2db8cd6b804d41608a5f'),
    'compiler_unit_adapter_v3.py': ('lossless-capture-v1/compiler_unit_adapter_v3.py', '775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c'),
    'lossless_gzip_v1.py': ('lossless-capture-v1/lossless_gzip_v1.py', 'f93850883bdab523e59122812fa46877728127e8ba5997c567621347de739193'),
}


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def build():
    rows = []
    for name, (relative, expected) in SOURCES.items():
        source = WHOLE / relative
        raw = source.read_bytes(); origin = pin(source)
        assert len(expected) == 64 and origin['sha256'] == expected
        target = DEST / name; target.write_bytes(raw)
        rows.append({'module': name, 'source_origin': origin, 'promoted': pin(target), 'byte_exact': True})
    model = WHOLE / 'model-entry-v3/whole_model_v3.py'
    assert pin(model)['sha256'] == '2de83f722c439c5a834f9b17549b979e24b3716d79170377bf8cbeafd7b07b50'
    text = model.read_text(); tree = ast.parse(text)
    selected = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef))
        and node.name in {'Refused', 'need', 'check_contract_inventory', 'hook_text'}]
    assert len(selected) == 4
    body = '"""2026-10-16 ET. Exact pure checked-model primitives; portable composition owns I/O."""\n\n'
    body += '\n\n\n'.join(ast.get_source_segment(text, node) for node in selected) + '\n'
    target = DEST / 'model_primitives.py'; target.write_text(body)
    rows.append({'module': target.name, 'source_origin': pin(model), 'promoted': pin(target),
        'exact_function_nodes': {node.name: hashlib.sha256(ast.get_source_segment(text, node).encode()).hexdigest() for node in selected}})
    (DEST / '__init__.py').write_text('"""2026-10-16 ET. Private checked-source implementation; public entry is dx100_checked_source."""\n')
    (HERE / 'promotion-manifest-v1.json').write_text(json.dumps({'date': '2026-10-16 ET', 'modules': rows,
        'runtime_import_policy': 'normal private swdb package only; no .scratch imports or arbitrary callback modules',
        'scope': 'inert proposed production tree, no shared production writes'}, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__': build()
