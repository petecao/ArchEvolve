"""2026-10-16 ET. Source-only native86 cold policy/template preparation.

Never admits or executes the reader. Runtime paths and root observation hashes
come from the exact reviewed V4 packet and already collected compact metadata.
"""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
POC = WHOLE.parent.parent


def no_child(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.', 'ctypes.dlopen')) or event == 'os.system':
        raise RuntimeError('source-only template preparation refuses ' + event)


sys.addaudithook(no_child)


def pin(path, staged=False):
    raw = path.read_bytes()
    return {'path': None if staged else str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    source = HERE / 'native86_cold_audit.py'
    root = POC / 'evidence/t28-native86-v4-root-execution-20261016.json'
    review = POC / 'evidence/resume-20261016-lane-coordination/resume-main-launcher-v9-independent-static-review-20261016.json'
    command = WHOLE / 'linux_native86_command_v4.json'
    assert pin(root)['sha256'] == '67241250320da121d467688a89308db60831e6dea0c324329e7029a62373e26b'
    assert pin(review)['sha256'] == 'ad31177bce794e960107439ac2080f2f1af5eb71fa83007264edc6c1a4274682'
    assert pin(command)['sha256'] == 'fe518dfcdb0f5910f25d6678b5faa5500140d61a775b5c4873a10f8fc9324f70'
    metadata = json.loads((HERE / 'passive-native86-v4-metadata.json').read_text())
    runtime = json.loads((WHOLE / 'linux_native86_policy_v4.json').read_text())
    policy = {'date': '2026-10-16 ET', 'schema': 'native86-passive-cold-policy-1', 'admitted': False,
        'scope': 'Private native86 retained metadata/source/runtime audit only. Root must supply staged canonical paths, exact reader environment and independent runtime/source policy admission before actual invocation.',
        'raw': metadata['raw_root'], 'reader': pin(source, True), 'root_receipt': pin(root, True),
        'guard_review': pin(review, True), 'command': pin(command, True),
        'raw_snapshot': {'files': metadata['files'], 'directories': metadata['directories']},
        'reader_admission': {'admitted': False, 'python': runtime['python'],
            'prefix': runtime['startup_roles']['prefix'], 'base_prefix': runtime['startup_roles']['base_prefix'],
            'initial_sys_path': runtime['startup_roles']['package_sys_path'], 'pycache_prefix': None,
            'environment': {'PYTHONPATH': None, 'PYTHONHOME': None, 'PYTHONDONTWRITEBYTECODE': '1',
                'PYTHONPYCACHEPREFIX': None, 'PYTHONNOUSERSITE': None, 'PYTHONSAFEPATH': None,
                'PYTEST_DISABLE_PLUGIN_AUTOLOAD': None, 'SETUPTOOLS_USE_DISTUTILS': None,
                'PROBATA_OUTPUT': None, 'SWDB_VERIFIER_LOCK': None, 'SWDB_VERIFIER_RSS_CAP_BYTES': None}}}
    (HERE / 'native86-cold-policy-template.json').write_text(json.dumps(policy, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': 'INERT TEMPLATE; actual paths/admission pending', 'reader': pin(source),
        'policy_template': pin(HERE / 'native86-cold-policy-template.json'), 'raw_files': len(metadata['files']),
        'raw_bytes': metadata['total_bytes']}, sort_keys=True, indent=2))


if __name__ == '__main__': main()
