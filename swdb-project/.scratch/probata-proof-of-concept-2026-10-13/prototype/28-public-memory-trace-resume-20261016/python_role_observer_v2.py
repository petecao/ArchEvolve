"""2026-10-16 ET. INERT source; invoked only within root-admitted entry/child.

Initial paths/flags/environment are checked before the four package imports.
Physical __file__ pins do not establish frozen-code/source equivalence.
"""

def observe_role_v2(request):
    import hashlib
    import importlib
    import json
    import os
    from pathlib import Path
    import site
    import sys
    flags = {'isolated': sys.flags.isolated, 'no_user_site': sys.flags.no_user_site,
             'safe_path': sys.flags.safe_path, 'dont_write_bytecode': sys.dont_write_bytecode,
             'optimize': sys.flags.optimize}
    initial = {'initial_sys_path': list(sys.path), 'flags': flags,
               'user_site_enabled': site.ENABLE_USER_SITE, 'executable': sys.executable,
               'prefix': sys.prefix, 'base_prefix': sys.base_prefix, 'pycache_prefix': sys.pycache_prefix,
               'startup_environment': {name: os.environ.get(name) for name in request['startup_environment']}}
    for name, value in initial.items():
        if value != request[name]:
            raise ValueError('actual initial role startup differs before package import: ' + name)
    if any(name.startswith('PYTHON') and name not in {'PYTHONPATH', 'PYTHONPYCACHEPREFIX',
            'PYTHONDONTWRITEBYTECODE', 'PYTHONNOUSERSITE', 'PYTHONSAFEPATH'} for name in os.environ):
        raise ValueError('unbound actual Python environment selector')
    for name in request['packages']:
        importlib.import_module(name)
    origins = {}
    for name, wanted in request['module_origins'].items():
        module = sys.modules.get(name)
        if module is None or not getattr(module, '__file__', None):
            raise ValueError('expected actual module origin is unavailable: ' + name)
        path = Path(module.__file__).resolve(strict=True)
        origins[name] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                         'spec_origin': getattr(module.__spec__, 'origin', None),
                         'boundary': '__file__ physical pin; frozen/builtin code remains interpreter TCB'}
        if origins[name] != wanted:
            raise ValueError('actual selected package/startup origin differs: ' + name)
    return dict(initial, schema='guarded-python-role-observation-2', role=request['role'],
                packages=request['packages'], post_package_sys_path=list(sys.path), module_origins=origins,
                scope='Actual role initial and post-package states recorded separately; no project import/compiler/proof')


if __name__ == '__main__':
    import json
    import sys
    print(json.dumps(observe_role_v2(json.loads(sys.argv[1])), sort_keys=True))
