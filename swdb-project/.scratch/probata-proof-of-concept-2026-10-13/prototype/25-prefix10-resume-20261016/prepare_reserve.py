"""2026-10-16 ET. Isolated pure reserve67 preparation, no external tool children."""
import ast
import json
import signal
import sys
import types
from pathlib import Path

from author import SOURCE, blob, digest, encoded, git, pin

ROOT = Path('/private/tmp/probata-resume-20261016-t25-pure-reserve67-c978393b')
MEMBER = 'std_vector_int_realloc_v3_reserve'
MODULES = ['__init__.py', 'std_models.py', 'heap_model_vcs.py',
           'vector_reallocation_model.py', 'vector_reallocation_inventory.py',
           'vector_reallocation_vcs.py', 'heap_reallocation.mlw']
MAX_BYTES = 32 * 1024 * 1024


def main():
    signal.alarm(60)
    ROOT.mkdir(exist_ok=False)
    (ROOT / 'swdb').mkdir()
    rows = []
    for name in MODULES:
        data = blob('swdb/' + name)
        if name.endswith('.py'):
            imports = {alias.name for node in ast.walk(ast.parse(data))
                       if isinstance(node, ast.Import) for alias in node.names}
            imports |= {node.module for node in ast.walk(ast.parse(data))
                        if isinstance(node, ast.ImportFrom)}
            assert not imports - {'hashlib', 'json', 're', 'pathlib', 'ast', 'swdb',
                                  'swdb.heap_model_vcs', 'swdb.vector_reallocation_inventory'}
        path = ROOT / 'swdb' / name
        path.write_bytes(data)
        rows.append({'relative': 'swdb/' + name, 'bytes': len(data), 'sha256': digest(data),
                     'git_blob': git('rev-parse', SOURCE + ':swdb-project/swdb/' + name).decode().strip()})
    lowerer = blob('swdb/c_lowering.py')
    nodes = [node for node in ast.parse(lowerer).body
             if isinstance(node, ast.Assign) and len(node.targets) == 1
             and isinstance(node.targets[0], ast.Name)
             and node.targets[0].id in {'INTEGER_TYPES', 'FLOAT_TYPES', 'INTERNAL_TYPES'}]
    assert len(nodes) == 3
    stub = types.ModuleType('swdb.c_lowering')
    for node in nodes:
        setattr(stub, node.targets[0].id, ast.literal_eval(node.value))
    sys.modules['swdb.c_lowering'] = stub
    attempts = []

    def audit(event, arguments):
        if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn',
                     'os.exec', 'os.fork', 'ctypes.dlopen'}:
            attempts.append(event)
            raise RuntimeError('external/native execution forbidden in pure canonical preparation')

    sys.addaudithook(audit)
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT))
    from swdb import vector_reallocation_vcs as packets
    assert Path(packets.__file__).resolve().parent == ROOT / 'swdb'
    manifest = packets.prepare(MEMBER, ROOT / 'canonical')
    assert packets.check(MEMBER, ROOT / 'canonical') == manifest
    assert len(manifest['obligations']) == 67
    assert all(row['status'] == 'pending' and not row['dependencies']
               for row in manifest['obligations'])
    canonical_files = []
    total = 0
    for path in sorted((ROOT / 'canonical').rglob('*')):
        assert not path.is_symlink()
        if path.is_file():
            total += path.stat().st_size
            assert total <= MAX_BYTES
            canonical_files.append({'path': str(path.relative_to(ROOT / 'canonical')),
                                    'bytes': path.stat().st_size,
                                    'sha256': digest(path.read_bytes())})
    assert not attempts
    receipt = {
        'created': '2026-10-16 ET', 'source_commit': SOURCE, 'member': MEMBER,
        'scope': 'Exact seven Git modules and literal-only lowerer type infrastructure; compiler-free canonical preparation only. Actual project/runtime remains unchanged.',
        'author': pin(Path(__file__)), 'files': rows,
        'lowerer_literal_source_sha256': digest(lowerer),
        'canonical_files': canonical_files,
        'manifest_sha256': digest((ROOT / 'canonical/manifest.json').read_bytes()),
        'target_count': 67, 'physical_reference_files': sum(
            row['path'].startswith('references/') for row in canonical_files),
        'raw_bytes': total, 'raw_budget_bytes': MAX_BYTES, 'whole_alarm_seconds': 60,
        'external_native_attempts': attempts, 'old_records_imported': 0,
        'actual_runtime_overlay': False, 'proof_acceptance': False,
        'caller_acceptance': False, 'ticket_closure': False,
    }
    (ROOT / 'preparer-receipt.json').write_bytes(encoded(receipt))
    signal.alarm(0)
    print(json.dumps({'receipt': pin(ROOT / 'preparer-receipt.json'),
                      'targets': 67, 'canonical_files': len(canonical_files),
                      'raw_bytes': total, 'external_native_attempts': attempts}, indent=2))


if __name__ == '__main__':
    main()
