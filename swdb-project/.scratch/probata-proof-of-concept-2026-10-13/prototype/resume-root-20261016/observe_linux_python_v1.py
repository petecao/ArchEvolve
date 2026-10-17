"""2026-10-16 ET. Guarded runtime observation only; no SWDB/compiler/solver import."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import site
import sys

assert sys.flags.isolated and sys.flags.dont_write_bytecode and not sys.flags.optimize
raw = Path(os.environ['PROBATA_OUTPUT']).resolve()
assert raw.is_dir() and sys.pycache_prefix == str(raw / 'python-source-cache')
assert not Path(sys.pycache_prefix).exists()
assert os.environ['SWDB_VERIFIER_RSS_CAP_BYTES'] == '8589934592'
assert sys.executable == '/data1/yanruj/venvs/swdb-test/bin/python'
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == 'e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f'
assert site.ENABLE_USER_SITE is False
names = ('pytest', 'yaml', 'jsonschema', 'psutil')
for name in names:
    importlib.import_module(name)
origins = {}
for name, module in sorted(sys.modules.items()):
    origin = getattr(module, '__file__', None)
    if origin is None:
        continue
    path = Path(origin).resolve()
    if not path.is_file():
        raise ValueError('loaded module origin is not a regular file: ' + name)
    origins[name] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                     'spec_origin': getattr(getattr(module, '__spec__', None), 'origin', None),
                     'boundary': '__file__ physical pin; frozen/builtin code remains interpreter TCB'}
assert not Path(sys.pycache_prefix).exists()
result = {'schema': 'guarded-linux-python-observation-1', 'sys_path': list(sys.path),
          'executable': sys.executable, 'prefix': sys.prefix, 'base_prefix': sys.base_prefix,
          'python_version': sys.version, 'isolated': bool(sys.flags.isolated),
          'dont_write_bytecode': bool(sys.flags.dont_write_bytecode),
          'user_site_enabled': site.ENABLE_USER_SITE, 'pycache_prefix': sys.pycache_prefix,
          'cache_absent_before_after': True, 'selected_packages': list(names),
          'loaded_module_origins': origins, 'source_or_proof_acceptance': False,
          'scope': 'Actual selected interpreter startup/import paths only; no project test/compiler/solver, no proof or hardware result'}
out = raw / 'python-runtime-observation.json'
with out.open('x') as stream:
    stream.write(json.dumps(result, sort_keys=True, indent=2) + '\n')
print(json.dumps({'path': str(out), 'sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
                  'sys_path': result['sys_path'], 'loaded_modules': len(origins),
                  'source_or_proof_acceptance': False}))
