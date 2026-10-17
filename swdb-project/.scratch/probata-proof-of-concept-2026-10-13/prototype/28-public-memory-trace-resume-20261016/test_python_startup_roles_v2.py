"""2026-10-16 ET. No-child controls for explicit role/environment admission."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import unittest

import closed_python_surface as closed
import python_startup_roles_v2 as roles
from test_closed_python_surface import PythonSurfaceControls


class RoleControls(PythonSurfaceControls):
    # Reuse only tiny inert fixture construction, not inherited control selection.
    def setUp(self):
        super().setUp()
        self.project = self.base / 'source-project'
        self.project.mkdir()
        for name in ('lib-dynload', 'dist-packages'):
            (self.roots[0] / name).mkdir()
        self.paths = [str(self.absent), str(self.roots[0]), str(self.roots[0] / 'lib-dynload'),
                      *map(str, self.roots[1:]), str(self.roots[0] / 'dist-packages')]
        from test_closed_python_surface import summary
        oldlinks = self.policy['surfaces'][str(self.roots[0])]['symlinks']
        self.policy['surfaces'][str(self.roots[0])] = dict(summary(self.roots[0]), symlinks=oldlinks)
        physical = {name: self.policy[name] for name in roles.PHYSICAL_KEYS}
        pin = {'path': str(self.site), 'sha256': hashlib.sha256(self.site.read_bytes()).hexdigest(),
               'spec_origin': 'frozen', 'boundary': '__file__ physical pin; frozen/builtin code remains interpreter TCB'}
        self.origins = {name: dict(pin) for name in roles.ORIGINS}
        self.raw = {'observation': {'schema': 'guarded-linux-python-observation-1',
                    'selected_packages': roles.PACKAGES, 'sys_path': self.paths,
                    'executable': str(self.alias), 'prefix': str(self.external), 'base_prefix': str(self.external),
                    'loaded_module_origins': self.origins}}
        self.rawbytes = json.dumps(self.raw).encode()
        self.plan = {'schema': 'python-startup-roles-plan-2', 'admitted': True,
                     'root_observer_sha256': hashlib.sha256(self.rawbytes).hexdigest(),
                     'root_observer_selection': 'observation', 'physical_metadata_sha256': roles.digest_v2(physical),
                     'package_sys_path': self.paths,
                     'covered_descendants': [{'path': str(self.roots[0] / name), 'root': str(self.roots[0])}
                                             for name in ('lib-dynload', 'dist-packages')],
                     'packages': roles.PACKAGES, 'module_origins': self.origins,
                     'executable': str(self.alias), 'prefix': str(self.external), 'base_prefix': str(self.external),
                     'source_project': str(self.project)}
        self.env = roles.child_environment_v2({'PYTHONHOME': '/escape', 'PYTHONUSERBASE': '/escape',
                    'PYTHONINSPECT': '1', '__PYVENV_LAUNCHER__': '/escape', 'PATH': '/preserved'},
                    project=self.project, raw=self.base / 'future-raw', cache=self.base / 'future-cache')

    def validate(self, plan=None, raw=None):
        return roles.validate_role_plan_v2(plan or self.plan, metadata=self.policy,
               source_project=self.project, root_observer_bytes=self.rawbytes if raw is None else raw, closed=closed)

    def observation(self, role='pytest-child'):
        request = roles.role_request_v2(self.plan, role=role, environment=self.env, cache=self.base / 'future-cache')
        return request, dict(copy.deepcopy(request), schema='guarded-python-role-observation-2', scope='actual fixture')

    def test_bootstrap_final_child_environment_and_actual_roles(self):
        self.validate()
        closed.verify_python_metadata(self.policy)
        self.assertEqual(self.env['PATH'], '/preserved')
        self.assertFalse({'PYTHONHOME', 'PYTHONUSERBASE', 'PYTHONINSPECT', '__PYVENV_LAUNCHER__'} & self.env.keys())
        for role in ('entry-isolated', 'pytest-child'):
            request, observed = self.observation(role)
            self.assertEqual(request['flags']['isolated'], int(role == 'entry-isolated'))
            self.assertEqual(request['initial_sys_path'], ([str(self.project)] if role == 'pytest-child' else []) + self.paths)
            roles.check_role_observation_v2(request, observed)
        self.assertFalse((self.base / 'future-raw').exists())
        self.assertFalse((self.base / 'future-cache').exists())

    def test_namespace_exact_no_old_probe_wildcards(self):
        request, observed = self.observation()
        for field in ('PROBATA_OUTPUT', 'SWDB_VERIFIER_LOCK', 'PYTHONPYCACHEPREFIX', 'PYTHONPATH'):
            bad = copy.deepcopy(observed)
            bad['startup_environment'][field] = '/previous-probe'
            with self.assertRaises(ValueError): roles.check_role_observation_v2(request, bad)

    def test_exact_initial_and_post_paths_independently(self):
        request, observed = self.observation()
        for field in ('initial_sys_path', 'post_package_sys_path'):
            for paths in (self.paths, request[field] + ['/usr/unlisted'], list(reversed(request[field]))):
                bad = copy.deepcopy(observed); bad[field] = paths
                with self.assertRaises(ValueError): roles.check_role_observation_v2(request, bad)

    def test_role_flags_cannot_equate_entry_and_child(self):
        request, observed = self.observation()
        for field, value in [('isolated', 1), ('isolated', False), ('no_user_site', 0), ('no_user_site', True),
                             ('safe_path', False), ('safe_path', 1), ('optimize', 1), ('dont_write_bytecode', False)]:
            bad = copy.deepcopy(observed); bad['flags'][field] = value
            with self.assertRaises(ValueError): roles.check_role_observation_v2(request, bad)
        bad = copy.deepcopy(observed); bad['user_site_enabled'] = True
        with self.assertRaises(ValueError): roles.check_role_observation_v2(request, bad)

    def test_provenance_closed_paths_and_origins(self):
        for field, value in [('root_observer_sha256', '0' * 64), ('physical_metadata_sha256', '0' * 64),
                             ('root_observer_selection', 'resources'), ('covered_descendants', []),
                             ('source_project', str(self.base)), ('executable', '/unlisted/python')]:
            bad = copy.deepcopy(self.plan); bad[field] = value
            with self.assertRaises(ValueError): self.validate(bad)
        bad = copy.deepcopy(self.plan); bad['package_sys_path'][-1] = '/usr/unlisted'
        with self.assertRaises(ValueError): self.validate(bad)
        request, observed = self.observation()
        bad = copy.deepcopy(observed); bad['module_origins']['pytest']['sha256'] = '0' * 64
        with self.assertRaises(ValueError): roles.check_role_observation_v2(request, bad)

    def test_child_request_rejects_unsanitized_environment(self):
        for key, value in [('PYTHONNOUSERSITE', '0'), ('PYTHONSAFEPATH', '0'), ('PYTHONPATH', '/unlisted'),
                           ('PYTHONOPTIMIZE', '1'), ('PYTHONHOME', '/unlisted'), ('__PYVENV_LAUNCHER__', '/unlisted')]:
            bad = dict(self.env); bad[key] = value
            with self.assertRaises(ValueError):
                roles.role_request_v2(self.plan, role='pytest-child', environment=bad, cache=self.base / 'future-cache')

    def test_observer_guards_before_selected_package_imports(self):
        source = (Path(__file__).parent / 'python_role_observer_v2.py').read_text()
        tree = ast.parse(source)
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef))
        package_loop = next(node for node in function.body if isinstance(node, ast.For) and ast.unparse(node.iter) == "request['packages']")
        guard = next(node for node in function.body if isinstance(node, ast.For) and ast.unparse(node.iter) == 'initial.items()')
        self.assertLess(guard.lineno, package_loop.lineno)
        self.assertIn("'post_package_sys_path'", source.replace('post_package_sys_path=', "'post_package_sys_path'"))


if __name__ == '__main__':
    # Explicit seven new controls; do not repeat inherited physical controls.
    names = [name for name in RoleControls.__dict__ if name.startswith('test_')]
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(RoleControls(name) for name in names))
    raise SystemExit(not result.wasSuccessful())
