"""2026-10-16 ET. Pure canonical materialization of the public 59-target binding.

No compiler, solver, network or historical record mutation is permitted.
"""
import ctypes
import hashlib
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
ATTEMPTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'os.exec', 'os.spawn',
                         'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        ATTEMPTS.append(event)
        raise AssertionError('pure binding materialization rejects '+event)


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


sys.dont_write_bytecode = True
sys.addaudithook(audit)
sys.path.insert(0, str(PROJECT))
from swdb import vector_owned_move_binding as binding

base = PROJECT/'tests/fixtures/proof/vector_closed_scientific_bundle'
move = PROJECT/'tests/fixtures/proof/vector_owned_move_scientific_bundle'
result, files = binding.mathematical_dependencies(base, move)
destination = HERE/'canonical-v1'
destination.mkdir(exist_ok=False)
for name, raw in files.items():
    path = destination/name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
result_path = HERE/'bound-mathematical-dependencies-v1.json'
result_path.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
canonical = {'files': [pin(destination/name) for name in sorted(files)],
             'file_count': len(files), 'bytes': sum(map(len, files.values()))}
canonical_path = HERE/'canonical-manifest-v1.json'
canonical_path.write_text(json.dumps(canonical, sort_keys=True, indent=2)+'\n')
assert not ATTEMPTS
print(json.dumps({'created': '2026-10-16 ET', 'result': pin(result_path),
                  'canonical': pin(canonical_path),
                  'target_count': result['complete_source_target_count'],
                  'external_attempts_after_audit': ATTEMPTS,
                  'source_or_caller_admission': False}, sort_keys=True, indent=2))
