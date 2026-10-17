"""No-child regression of exact retained shell and extracted launch/role seams.

This is a closed source interpreter for the retained export vocabulary, not a
shell execution or an assertion about a future loader/interpreter observation.
The account object is an explicit stand-in; all science-relevant exports come
from the retained exact shell files and the selected launcher adaptation.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shlex
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
POC = WHOLE.parent.parent
ROOT = WHOLE / 'normalized-unit-envelope-v2-actual'
LOADER = WHOLE / 'root-launcher-loader-v11/launch_observer_loader_v11.py'
RUNTIME = WHOLE / 'compiler-capture-v10/linux_compiler_capture_policy_v10.json'
TRACE = WHOLE.parent / '28-public-memory-trace-resume-20261016'
OLD = WHOLE / 'normalized-unit-envelope-v2'
PURE = runpy.run_path(str(HERE / 'test_envelope_v4.py'), run_name='exact_v3_envelope_controls')
COMMAND = json.loads((HERE / 'command-v4.json').read_bytes())


def projected(path):
    tree = ast.parse(path.read_bytes())
    ns = {'Path': Path, 'json': json, 'hashlib': hashlib, 'os': os}
    nodes = [n for n in tree.body if isinstance(n, (ast.Assign, ast.FunctionDef))]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<exact-startup-role-source>', 'exec'), ns)
    return ns


def remote_ast():
    tree = ast.parse(LOADER.read_bytes())
    expression = next(n.value for n in tree.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'script' for t in n.targets))
    return ast.parse(expression.right.value)


def adapted(unsets, raw):
    tree = remote_ast()
    assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'adapted_run' for t in n.targets))
    condition = next(n for n in tree.body if isinstance(n, ast.If)
        and ast.unparse(n.test) == "cfg['run_environment_unset']")
    ns = {'run': (ROOT / 'retained-legacy-v2.sh').read_text(),
        'old': Path('/data/yanruj/EvolveSWDB_runs/probata-composed-0e7f2327-t27-negative'),
        'out': Path(raw), 'source': Path(COMMAND['source_project']).parent,
        'cfg': {'rss_cap_bytes': 4294967296, 'run_environment_unset': unsets}}
    exec(compile(ast.Module(body=[assignment, condition], type_ignores=[]), '<exact-run-adaptation>', 'exec'), ns)
    return ns['adapted_run']


def sanitized():
    assignment = next(n for n in remote_ast().body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'sanitized' for t in n.targets))
    ns = {'account': SimpleNamespace(pw_dir='/root-account-home-standin', pw_name='root-account-name-standin')}
    exec(compile(ast.Module(body=[assignment], type_ignores=[]), '<exact-env-i-source>', 'exec'), ns)
    assert not any(k in ns['sanitized'] for k in ('LD_LIBRARY_PATH', 'LIBRARY_PATH', 'PYTHONPATH'))
    return ns['sanitized']


def shell_projection(source, environment):
    env = dict(environment); commands = []
    def expand(value):
        if any(token in value for token in ('`', '$(', ';', '\\')):
            raise ValueError('unsupported shell vocabulary')
        pattern = r'\$\{([A-Za-z_][A-Za-z_0-9]*):-([^}]*)\}|\$([A-Za-z_][A-Za-z_0-9]*)'
        def replace(match):
            if match[1]: return env.get(match[1]) or expand(match[2])
            if match[3] not in env: raise ValueError('unset strict shell variable')
            return env[match[3]]
        return re.sub(pattern, replace, value)
    for line in source.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line == 'set -euo pipefail': continue
        if line.startswith('source '):
            if line != 'source /data1/yanruj/probata-verifiers/env.sh': raise ValueError('unknown source')
            env, nested = shell_projection((ROOT / 'retained-environment-v2.sh').read_text(), env)
            commands += nested
        elif line.startswith('export '):
            for item in shlex.split(line[7:]):
                name, value = item.split('=', 1)
                if re.fullmatch('[A-Za-z_][A-Za-z_0-9]*', name) is None: raise ValueError('unknown export')
                env[name] = expand(value)
        elif line.startswith('unset '):
            for name in shlex.split(line[6:]): env.pop(name, None)
        elif line.startswith(('mkdir -p ', 'cd ')):
            commands.append([expand(token) for token in shlex.split(line)])
        elif line == '"$PROBATA_PYTHON" "$PROBATA_OUTPUT/watch.py"':
            commands.append([expand(token) for token in shlex.split(line)])
        else: raise ValueError('unrecognized retained shell line')
    return env, commands


def wrapper_projection(environment):
    snapshot = json.loads((POC / 'evidence/resume-20261016-lane-coordination/mbit10-preflight-and-wrapper-snapshots.json').read_bytes())
    rows = snapshot['wrapper_snapshots']
    if isinstance(rows, dict): rows = list(rows.values())
    calls = []
    def run(argv, **kwargs):
        calls.append({'argv': argv, **kwargs})
        return SimpleNamespace(exit_code=0)
    for filename in ('watch.py', 'execute.py'):
        row = next(row for row in rows if row['path'].endswith('/' + filename))
        original = row['content']
        expected = {'watch.py': '4485ae66', 'execute.py': 'ea774376'}[filename]
        assert hashlib.sha256(original.encode()).hexdigest().startswith(expected)
        code = original.replace('8589934592', '4294967296')
        node = next(n for n in ast.parse(code).body if isinstance(n, ast.Assign)
            and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) and n.value.func.id == 'run')
        ns = {'out': Path(COMMAND['raw']), 'cfg': {'command': COMMAND['argv'], 'log_name': 'acceptance.log',
            'source': str(Path(COMMAND['source_project']).parent), 'timeout_seconds': 1200},
            'source': Path(COMMAND['source_project']).parent, 'sys': SimpleNamespace(executable=COMMAND['argv'][0]),
            'os': SimpleNamespace(environ=environment), 'run': run}
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<exact-watch-execute-run-seam>', 'exec'), ns)
        environment = calls[-1]['env']
    return calls


class RootEnvironmentControls(unittest.TestCase):
    def test_namespace_inventory_inverse_and_stable_functions_exact(self):
        selected = HERE / 'linux_observation_envelope_v4.py'
        new = selected.read_text()
        inverse = json.loads((HERE / 'exact-inverses-v4.json').read_bytes())['files']['linux_observation_envelope_v4.py']
        for row in reversed(inverse['replacements']):
            self.assertEqual(new.count(row['new']), row['count']); new = new.replace(row['new'], row['old'])
        before = HERE.parent / 'normalized-unit-envelope-v3/linux_observation_envelope_v3.py'
        self.assertEqual(new, before.read_text())
        for name in ('bind_environment', 'publish_final_result', 'read', 'runtime_helpers', 'check_outputs'):
            def function(path):
                return ast.dump(next(n for n in ast.parse(path.read_bytes()).body if isinstance(n, ast.FunctionDef) and n.name == name))
            self.assertEqual(function(selected), function(before))

    def test_retained_source_pins_and_actual_v2_red(self):
        receipt = json.loads((ROOT / 'passive-shell-source-stdout-v2.json').read_bytes())
        for role, file in (('actual', 'retained-actual-v2.sh'), ('legacy', 'retained-legacy-v2.sh'), ('environment', 'retained-environment-v2.sh')):
            raw = (ROOT / file).read_bytes(); row = receipt['rows'][role]
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (row['bytes'], row['sha256']))
        old_raw = json.loads((OLD / 'command-v2.json').read_bytes())['raw']
        source = adapted(['LIBRARY_PATH'], old_raw)
        self.assertEqual(source, (ROOT / 'retained-actual-v2.sh').read_text())
        env, _ = shell_projection(source, sanitized())
        runtime = json.loads(RUNTIME.read_bytes())
        self.assertEqual(env['LD_LIBRARY_PATH'], runtime['native_runtime']['loader_environment']['LD_LIBRARY_PATH'] + ':')
        with self.assertRaisesRegex(ValueError, 'unadmitted loader search'):
            PURE['namespace']()['bind_environment'](Path(old_raw), runtime, env)

    def test_full_real_shell_exports_launcher_unset_argv_bind_and_role_green(self):
        source = adapted(['LIBRARY_PATH', 'LD_LIBRARY_PATH'], COMMAND['raw'])
        env, shell_calls = shell_projection(source, sanitized())
        self.assertNotIn('LD_LIBRARY_PATH', env); self.assertNotIn('LIBRARY_PATH', env)
        self.assertEqual(shell_calls[-1], [COMMAND['argv'][0], COMMAND['raw'] + '/watch.py'])
        self.assertEqual(env['SWDB_VERIFIER_RSS_CAP_BYTES'], '4294967296')
        self.assertEqual(env['PROBATA_OUTPUT'], COMMAND['raw'])
        self.assertEqual(env['SWDB_VERIFIER_LOCK'], COMMAND['raw'] + '/verifier.lock')
        calls = wrapper_projection(env)
        self.assertEqual(calls[0]['argv'], [COMMAND['argv'][0], COMMAND['raw'] + '/execute.py'])
        self.assertEqual(calls[1]['argv'], COMMAND['argv'])
        for call in calls:
            self.assertEqual((call['cap_bytes'], call['timeout']), (4294967296, 1200))
            self.assertNotIn('LD_LIBRARY_PATH', call['env']); self.assertNotIn('LIBRARY_PATH', call['env'])
        runtime = json.loads(RUNTIME.read_bytes()); received = calls[1]['env']
        ns = PURE['namespace'](); binding = ns['bind_environment'](Path(COMMAND['raw']), runtime, received)
        self.assertIsNone(binding['known_root_environment_before']['LD_LIBRARY_PATH'])
        role = projected(TRACE / 'python_startup_roles_v2.py')['role_request_v2'](runtime['startup_roles'],
            role='entry-isolated', environment=received, cache=Path(COMMAND['raw']) / 'entry-source-cache')
        self.assertEqual(COMMAND['argv'][1:5], ['-I', '-B', '-X', 'pycache_prefix=' + role['pycache_prefix']])
        self.assertEqual(role['flags'], {'isolated': 1, 'no_user_site': 1, 'safe_path': True, 'dont_write_bytecode': True, 'optimize': 0})
        self.assertIsNone(role['startup_environment']['PYTHONPATH'])
        self.assertEqual(role['initial_sys_path'], runtime['startup_roles']['package_sys_path'])
        self.assertEqual(role['post_package_sys_path'], role['initial_sys_path'])
        self.assertEqual(len(role['initial_sys_path']), 7)

    def test_unknown_loader_values_and_python_selectors_still_refuse(self):
        env, _ = shell_projection(adapted(['LIBRARY_PATH', 'LD_LIBRARY_PATH'], COMMAND['raw']), sanitized())
        ns = PURE['namespace'](); runtime = json.loads(RUNTIME.read_bytes())
        known = runtime['native_runtime']['loader_environment']['LD_LIBRARY_PATH']
        for name, value in (('LD_LIBRARY_PATH', known + ':'), ('LD_LIBRARY_PATH', ':' + known),
            ('LD_LIBRARY_PATH', known + ':/extra'), ('LD_LIBRARY_PATH', '/extra'),
            ('LD_PRELOAD', '/extra.so'), ('LIBRARY_PATH', known), ('PYTHONPATH', '/wrong-source'),
            ('PYTHONHOME', '/wrong-prefix')):
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                ns['bind_environment'](Path(COMMAND['raw']), runtime, {**env, name: value})

    def test_root_command_and_explicit_observer_successor_closure(self):
        self.assertEqual(COMMAND['root_launcher']['sha256'], hashlib.sha256(LOADER.read_bytes()).hexdigest())
        self.assertEqual(COMMAND['root_launch_requirements']['run_environment_unset'], ['LIBRARY_PATH', 'LD_LIBRARY_PATH'])
        self.assertEqual(COMMAND['root_created_directories'], [COMMAND['raw'] + '/control'])
        self.assertLessEqual(COMMAND['root_controls_bytes_including_policy'], 1048576)
        old = json.loads((WHOLE / 'normalized-unit-envelope-v3/command-v3.json').read_bytes())
        replaced = {'linux_observation_envelope_v3.py', 'observe_entry_v1.py',
            'fixed-modules-v1.json', 'normalized_compiler_adapter_v1.py'}
        added = {'linux_observation_envelope_v4.py', 'observe_entry_v2.py',
            'fixed-modules-v2.json', 'normalized_compiler_adapter_v2.py',
            'abi_role_transport_v1.py', 'strict_minify_v2.py'}
        self.assertEqual(set(COMMAND['stage_sources']), (set(old['stage_sources']) - replaced) | added)
        changed = replaced | {'observation-policy-v1.json', 'normalized_capture_ingress_v2.py'}
        observer_files = {row['file'] for row in json.loads((HERE / 'observer/fixed-modules-v2.json').read_bytes())['modules']}
        for name, row in old['stage_sources'].items():
            if name in changed: continue
            self.assertEqual({k: v for k, v in COMMAND['stage_sources'][name].items() if k != 'path'},
                             {k: v for k, v in row.items() if k != 'path'})
            if name not in observer_files | {'selected-zlib-runtime.json'}:
                self.assertEqual(COMMAND['stage_sources'][name]['path'], row['path'])
        self.assertEqual(COMMAND['guard'], old['guard'])


if __name__ == '__main__': unittest.main(verbosity=2)
