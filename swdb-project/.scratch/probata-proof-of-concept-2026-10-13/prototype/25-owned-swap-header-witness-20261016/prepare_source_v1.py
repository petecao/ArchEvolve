"""2026-10-16 ET. Materialize the inert public packet from retained pure sources."""
import hashlib
import json
from pathlib import Path
import signal
import sys


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
PURE = Path('/private/tmp/probata-resume-20261016-t25-owned-swap-witness-green-v4')
ELEMENTS = ('int', 'float', 'double', 'int *')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    with path.open('xb') as handle:
        handle.write(raw)


def main():
    signal.alarm(30)
    control = json.loads((PURE/'result.json').read_bytes())
    if (control['passed'], control['failed'], control['external_native_attempts']) != (4, 0, []):
        raise ValueError('the exact final four pure controls are required')
    for row in control['source_pins']:
        current = PROJECT/'swdb'/row['path']
        copied = PURE/'swdb'/row['path']
        raw = current.read_bytes()
        if current.is_symlink() or copied.is_symlink() or raw != copied.read_bytes() or \
                len(raw) != row['bytes'] or sha(raw) != row['sha256']:
            raise ValueError('final pure source identity changed: '+row['path'])
    test = (PROJECT/'tests/test_vector_owned_swap_header_witness.py').read_bytes()
    if sha(test) != control['test_sha256']:
        raise ValueError('final public test identity changed')
    attempts = []

    def audit(event, args):
        if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec',
                     'os.fork', 'ctypes.dlopen', 'socket.connect'}:
            attempts.append(event)
            raise RuntimeError('inert source materialization rejected '+event)

    sys.addaudithook(audit)
    sys.path.insert(0, str(PURE))
    sys.dont_write_bytecode = True
    from swdb import vector_owned_swap_header_cases as previous
    from swdb import vector_owned_swap_header_witness as packets

    old, old_files = previous.declaration(elements=ELEMENTS)
    directory = HERE/'inert-all-types-v1'
    plan = packets.prepare(directory, elements=ELEMENTS)
    if packets.check(directory, elements=ELEMENTS) != plan:
        raise ValueError('public canonical check disagrees')
    inverses = []
    for row, original in zip(plan['obligations'], old['obligations'], strict=True):
        restored = row['statement'].replace(row['explicit_header'],
                    row['existential_introduction']['original_existential'])
        if restored != original['statement'] or \
                (directory/row['existential_reference']['path']).read_bytes() != old_files[original['path']]:
            raise ValueError('the entire original case and reference inverse changed')
        inverses.append({'case': row['case'], 'original_path': original['path'],
            'original_sha256': original['sha256'], 'target_path': row['path'],
            'target_sha256': row['sha256'], 'entire_statement_inverse_equal': True,
            'original_case_reference_equal': True,
            'existential_introduction': row['existential_introduction']})
    shared = []
    for name, raw in old_files.items():
        if name.startswith('obligations/') or name == 'manifest.json':
            continue
        if (directory/name).read_bytes() != raw:
            raise ValueError('an inherited source/theory/reference changed: '+name)
        shared.append({'path': name, 'bytes': len(raw), 'sha256': sha(raw)})
    try:
        packets.check_launch(directory, elements=ELEMENTS)
    except ValueError as error:
        refusal = str(error)
    else:
        raise ValueError('unproved constructive targets must remain unlaunchable')
    files = [{'path': str(path.relative_to(directory)), 'bytes': path.stat().st_size,
              'sha256': sha(path.read_bytes())}
             for path in sorted(directory.rglob('*')) if path.is_file()]
    if attempts or any(path.is_symlink() for path in directory.rglob('*')) or \
            sum(row['bytes'] for row in files) > 2*1024**2:
        raise ValueError('bounded regular-only inert materialization required')
    write(HERE/'original-header3-manifest-v1.json', old)
    write(HERE/'derivation-v1.json', {
        'date': '2026-10-16 ET', 'elements': ELEMENTS,
        'original_statement': old['original_statement'],
        'complete_source_antecedent': old['complete_source_antecedent'],
        'original_reconstruction': old['reconstruction'],
        'new_reconstruction': plan['reconstruction'], 'case_inverses': inverses,
        'inherited_files': shared, 'physical_context': plan['physical_context'],
        'kernel_bindings': plan['kernel_bindings'],
        'all_three_stronger_obligations_pending': True,
        'sibling_theorem_premises': [], 'added_caller_requires': [],
        'launch_refusal': refusal, 'external_native_attempts': attempts,
        'actual_formal_run': False, 'mathematical_admission': False,
        'source_admission': False, 'caller_admission': False})
    write(HERE/'canonical-files-v1.json', {'date': '2026-10-16 ET',
        'count': len(files), 'total_bytes': sum(row['bytes'] for row in files),
        'files': files, 'external_native_attempts': attempts})
    signal.alarm(0)
    print(json.dumps({'files': len(files), 'bytes': sum(row['bytes'] for row in files),
        'old_files_unchanged': len(shared), 'stronger_targets': len(inverses),
        'launch_refused': True, 'external_native_attempts': attempts}))


if __name__ == '__main__':
    main()
