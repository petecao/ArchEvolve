"""2026-10-16 ET. Explicit entry-I and child startup policies; no child execution.

The older physical and entry-I receipt helpers remain unchanged. Root observation
V2 supplies post-package paths only; initial-path equality is a prospective gate,
not a claim about the timing of the old observation or frozen site source.
"""
import hashlib
import json
import os
from pathlib import Path

ENV_KEYS = ('SETUPTOOLS_USE_DISTUTILS', 'PYTHONPATH', 'PYTHONPYCACHEPREFIX',
            'PYTHONDONTWRITEBYTECODE', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD',
            'PROBATA_OUTPUT', 'SWDB_VERIFIER_LOCK', 'SWDB_VERIFIER_RSS_CAP_BYTES',
            'PYTHONNOUSERSITE', 'PYTHONSAFEPATH')
PYTHON_ENV_KEYS = {'PYTHONPATH', 'PYTHONPYCACHEPREFIX', 'PYTHONDONTWRITEBYTECODE',
                   'PYTHONNOUSERSITE', 'PYTHONSAFEPATH'}
PACKAGES = ['pytest', 'yaml', 'jsonschema', 'psutil']
ORIGINS = ['site', 'sitecustomize', '_distutils_hack', *PACKAGES]
PHYSICAL_KEYS = ('schema', 'surfaces', 'startup_pins', 'pth', 'interpreter', 'absence')


def digest_v2(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def child_environment_v2(base, *, project, raw, cache):
    """Explicit environment used by both child observer and real pytest child."""
    environment = dict(base)
    for name in list(environment):
        if (name.startswith('PYTHON') and name not in PYTHON_ENV_KEYS) or name == '__PYVENV_LAUNCHER__':
            del environment[name]
    environment.update(PYTHONPATH=str(project), PYTHONNOUSERSITE='1', PYTHONSAFEPATH='1',
                       PYTHONDONTWRITEBYTECODE='1', PYTHONPYCACHEPREFIX=str(cache),
                       PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', SETUPTOOLS_USE_DISTUTILS='local',
                       PROBATA_OUTPUT=str(raw), SWDB_VERIFIER_LOCK=str(Path(raw) / 'verifier.lock'),
                       SWDB_VERIFIER_RSS_CAP_BYTES='8589934592')
    return environment


def startup_projection_v2(environment):
    return {name: environment.get(name) for name in ENV_KEYS}


def validate_role_plan_v2(plan, *, metadata, source_project, root_observer_bytes, closed):
    """Bind the literal root observation and explicitly covered path selection."""
    keys = {'schema', 'admitted', 'root_observer_sha256', 'root_observer_selection',
            'physical_metadata_sha256', 'package_sys_path', 'covered_descendants',
            'packages', 'module_origins', 'executable', 'prefix', 'base_prefix', 'source_project'}
    closed._keys(plan, keys, 'startup roles V2 plan')
    if plan['schema'] != 'python-startup-roles-plan-2' or plan['admitted'] is not True:
        raise ValueError('explicit root-admitted role plan required')
    if plan['root_observer_selection'] != 'observation':
        raise ValueError('exact root observer selection required')
    closed._sha(plan['root_observer_sha256'])
    if type(root_observer_bytes) is not bytes or hashlib.sha256(root_observer_bytes).hexdigest() != plan['root_observer_sha256']:
        raise ValueError('separate raw root observer provenance pin differs')
    observed = json.loads(root_observer_bytes)['observation']
    if (observed['schema'] != 'guarded-linux-python-observation-1' or
            observed['selected_packages'] != PACKAGES or plan['packages'] != PACKAGES or
            plan['package_sys_path'] != observed['sys_path'] or len(plan['package_sys_path']) != 7 or
            len(set(plan['package_sys_path'])) != 7):
        raise ValueError('literal seven observed paths/four packages differ')
    physical = {name: metadata[name] for name in PHYSICAL_KEYS}
    if digest_v2(physical) != plan['physical_metadata_sha256']:
        raise ValueError('closed physical metadata digest differs')
    source = closed._absolute(str(source_project))
    if plan['source_project'] != str(source) or closed._resolution(source, []) != source or not source.is_dir():
        raise ValueError('policy-bound canonical selected source project differs')
    if any(str(source) == path for path in plan['package_sys_path']):
        raise ValueError('source project collides with package path')
    if plan['executable'] != metadata['interpreter']['path']:
        raise ValueError('selected role interpreter differs from closed chain')
    for name in ('executable', 'prefix', 'base_prefix'):
        if plan[name] != observed[name]:
            raise ValueError('root-observed role interpreter/prefix differs')
    if str(Path(plan['prefix']) / 'pyvenv.cfg') not in {row['path'] for row in metadata['startup_pins']}:
        raise ValueError('role venv prefix configuration is not pinned')
    roots = set(metadata['surfaces'])
    covered = []
    for name in plan['package_sys_path']:
        path = closed._absolute(name)
        if metadata['absence'].get(name) is True:
            if os.path.lexists(path):
                raise ValueError('explicit absent role path appeared')
        else:
            if closed._resolution(path, []) != path or not path.is_dir():
                raise ValueError('canonical real role directory required')
            parents = [root for root in roots if Path(root) == path or Path(root) in path.parents]
            if len(parents) != 1:
                raise ValueError('role path lacks one exact closed physical root')
            if name not in roots:
                covered.append({'path': name, 'root': parents[0]})
    if plan['covered_descendants'] != covered:
        raise ValueError('narrow literal covered descendant list differs')
    if not isinstance(plan['module_origins'], dict) or set(plan['module_origins']) != set(ORIGINS):
        raise ValueError('exact selected package/startup module origin pins required')
    for name, pin in plan['module_origins'].items():
        if pin != observed['loaded_module_origins'][name]:
            raise ValueError('raw root module origin provenance differs')
        physical_path = closed._absolute(pin['path'])
        if not any(Path(root) == physical_path or Path(root) in physical_path.parents for root in roots) and pin not in metadata['startup_pins']:
            # sitecustomize has a closed external physical target, also pinned as
            # startup input. Raw observer adds descriptive fields to its pin.
            if not any(row['path'] == pin['path'] and row['sha256'] == pin['sha256'] for row in metadata['startup_pins']):
                raise ValueError('module physical origin lacks closed coverage')
    return {'root_observer_sha256': plan['root_observer_sha256'],
            'root_observer_selection': plan['root_observer_selection'],
            'physical_metadata_sha256': plan['physical_metadata_sha256'],
            'plan_sha256': digest_v2(plan),
            'boundary': 'old paths observed after package imports; future initial/post-import role states are checked separately; frozen code remains interpreter TCB'}


def role_request_v2(plan, *, role, environment, cache):
    if role not in ('entry-isolated', 'pytest-child'):
        raise ValueError('exact explicit startup role required')
    if role == 'pytest-child' and (environment.get('PYTHONPATH') != plan['source_project'] or
            any(environment.get(name) != '1' for name in ('PYTHONNOUSERSITE', 'PYTHONSAFEPATH', 'PYTHONDONTWRITEBYTECODE'))):
        raise ValueError('child environment policy is not enforced')
    leaks = sorted(name for name in environment if name.startswith('PYTHON') and name not in PYTHON_ENV_KEYS)
    if leaks or '__PYVENV_LAUNCHER__' in environment:
        raise ValueError('unbound Python startup environment selector')
    paths = ([plan['source_project']] if role == 'pytest-child' else []) + plan['package_sys_path']
    return {'role': role, 'initial_sys_path': paths, 'post_package_sys_path': paths,
            'flags': {'isolated': 1 if role == 'entry-isolated' else 0, 'no_user_site': 1,
                      'safe_path': True, 'dont_write_bytecode': True, 'optimize': 0},
            'user_site_enabled': False, 'executable': plan['executable'], 'prefix': plan['prefix'],
            'base_prefix': plan['base_prefix'], 'pycache_prefix': str(cache),
            'startup_environment': startup_projection_v2(environment), 'packages': PACKAGES,
            'module_origins': plan['module_origins']}


def check_role_observation_v2(request, observed):
    if not isinstance(observed, dict) or set(observed) != set(request) | {'schema', 'scope'}:
        raise ValueError('complete exact role observation fields required')
    if observed['schema'] != 'guarded-python-role-observation-2':
        raise ValueError('exact actual role observation schema required')
    projection = {name: observed[name] for name in request}
    if projection != request:
        raise ValueError('actual role initial/post-package path, flags, environment or origin differs')
    for name in ('isolated', 'no_user_site', 'optimize'):
        if type(observed['flags'][name]) is not int:
            raise ValueError('exact integer flag required')
    for name in ('safe_path', 'dont_write_bytecode'):
        if type(observed['flags'][name]) is not bool:
            raise ValueError('exact Boolean flag required')
    if observed['user_site_enabled'] is not False:
        raise ValueError('user site must be explicitly disabled')
    return {'role': request['role'], 'actual_observation_sha256': digest_v2(observed),
            'initial_sys_path': observed['initial_sys_path'], 'post_package_sys_path': observed['post_package_sys_path'],
            'scope': 'actual role startup/package imports only; no project import or proof acceptance'}
