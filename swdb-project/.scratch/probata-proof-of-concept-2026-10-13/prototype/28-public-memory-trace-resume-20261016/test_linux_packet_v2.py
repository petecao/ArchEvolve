"""2026-10-16 ET. Pure V2 assembly/controller/progress controls; no child/tools."""
import ast
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import pathlib
import re
import shlex
import shutil
import stat
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn')) or event in {'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        raise RuntimeError('pure V2 controls refuse ' + event)


sys.addaudithook(deny)
ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / 'linux_trace_entry_v2.py').read_text()
TREE = ast.parse(SOURCE)
NAMES = {'validate_policy_v2', 'ocaml_membership_v2', 'import_surface', 'pin', 'junit_census', 'header_surface_check_v4', 'check_staged_controllers_v2'}
BODY = [node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name in NAMES or
        isinstance(node, ast.Assign) and all(isinstance(target, ast.Name) for target in node.targets)]
CONTEXT = dict(hashlib=hashlib, json=json, os=os, pathlib=pathlib, Path=Path, re=re, shlex=shlex,
               shutil=shutil, stat=stat, ET=ET)
exec(compile(ast.Module(body=BODY, type_ignores=[]), '<pure-v2-controller>', 'exec'), CONTEXT)


def valid_policy():
    policy = json.loads((ROOT / 'linux_trace_policy_template_v2.json').read_bytes())
    policy.update(admitted=True, source_commit='1' * 40, source_root='/admitted/source/swdb-project',
                  raw_name='probata-resume-20261016-t28-memory-trace-11111111-v2',
                  source_files={'swdb/cbmc_adapter.py': '2' * 64}, runtime_files={'/runtime/pin': '3' * 64})
    policy['source_consumer_trees'] = {name: {'oid': '4' * 40} for name in policy['source_consumer_trees']}
    policy['linux_clang_components'] = {'command': ['/admitted/clang++'],
        'command_executable': {'path': '/admitted/clang++', 'sha256': '5' * 64},
        'driver': {}, 'headers': {}, 'parser': {}}
    policy['tools'] = {name: {'path': '/admitted/' + name, 'sha256': '6' * 64} for name in
                       ('cbmc', 'frama-c', 'opam', 'python', 'ocamlfind', 'ocamlopt', 'why3', 'gcc', 'z3', 'cvc5', 'alt-ergo')}
    policy['tools']['cbmc']['version'] = '6.11.0'
    policy['tools']['frama-c']['version'] = '33.0'
    return policy


class LinuxV2Controls(unittest.TestCase):
    def test_template_inert_exact_v2_census_and_cbmc(self):
        with self.assertRaises(ValueError): CONTEXT['validate_policy_v2'](json.loads((ROOT / 'linux_trace_policy_template_v2.json').read_bytes()))
        policy = valid_policy()
        CONTEXT['validate_policy_v2'](policy)
        mutations = [lambda p: p.update(raw_name=p['raw_name'].replace('-v2', '-v1')),
                     lambda p: p['guard'].update(workers=2), lambda p: p['guard'].update(timeout_seconds=1201),
                     lambda p: p['junit'].update(skipped=1), lambda p: p['selection'].pop(),
                     lambda p: p['tools']['cbmc'].update(version='6.11'),
                     lambda p: p['cbmc_version_output'].update(stdout='6.11.0\n'),
                     lambda p: p['control_files'].pop('python_role_observer_v2.py'),
                     lambda p: p['linux_clang_components'].update(command=['clang++'])]
        for mutation in mutations:
            bad = copy.deepcopy(policy); mutation(bad)
            with self.assertRaises(ValueError): CONTEXT['validate_policy_v2'](bad)

    def test_v1_reviewed_helpers_exact_ast_and_bytes(self):
        old = (ROOT / 'linux_trace_entry_v1.py').read_text()
        oldf = {node.name: node for node in ast.parse(old).body if isinstance(node, ast.FunctionDef)}
        newf = {node.name: node for node in TREE.body if isinstance(node, ast.FunctionDef)}
        from prepare_linux_entry_v2 import HELPERS, BASIS_SHA
        self.assertEqual(hashlib.sha256(old.encode()).hexdigest(), BASIS_SHA)
        for name in HELPERS:
            self.assertEqual(ast.get_source_segment(old, oldf[name]), ast.get_source_segment(SOURCE, newf[name]))

    def test_staged_entry_policy_and_membership_before_after(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory).resolve(); control = raw / 'control'; control.mkdir()
            for name in CONTEXT['CONTROL_NAMES_V2']:
                (control / name).write_bytes(b'inert control')
            entry, policy = control / 'entry.py', control / 'policy.json'
            entry.write_bytes(b'inert entry'); policy.write_bytes(b'inert policy')
            expected = {'linux_launch_binding': {'entry_sha256': hashlib.sha256(entry.read_bytes()).hexdigest()}}
            arguments = dict(entry_file=entry, policy_file=policy, policy_sha256=hashlib.sha256(policy.read_bytes()).hexdigest())
            verify = CONTEXT['check_staged_controllers_v2']
            before = verify(raw, expected, **arguments)
            self.assertEqual(verify(raw, expected, **arguments), before)
            for path in (entry, policy):
                old = path.read_bytes(); path.write_bytes(b'changed')
                with self.assertRaises(ValueError): verify(raw, expected, **arguments)
                path.write_bytes(old)
            extra = control / 'extra'; extra.write_bytes(b'extra')
            with self.assertRaises(ValueError): verify(raw, expected, **arguments)
            extra.unlink(); entry.unlink(); entry.symlink_to('policy.json')
            with self.assertRaises(ValueError): verify(raw, expected, **arguments)
            self.assertIn('check_staged_controllers_v2(raw, expected', SOURCE[SOURCE.rindex('    finally:'):])

    def test_ocaml_membership_exact_component_order_and_no_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / 'dir').mkdir(); (root / 'dir/a').write_bytes(b'a'); (root / 'dir-z').write_bytes(b'z')
            files = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in root.rglob('*') if path.is_file()}
            policy = {'ocaml_packages': {'package': str(root)}, 'runtime_files': files}
            self.assertEqual(CONTEXT['ocaml_membership_v2'](policy)['package']['count'], 2)
            (root / 'new-file').write_bytes(b'new')
            with self.assertRaises(ValueError): CONTEXT['ocaml_membership_v2'](policy)
            (root / 'new-file').unlink(); (root / 'link').symlink_to('dir/a')
            with self.assertRaises(ValueError): CONTEXT['ocaml_membership_v2'](policy)

    def test_exact_reused_header_census_and_aggregate(self):
        import closed_python_surface as closed
        other = (ROOT.parent / '28-initialized-u32-resume-20261016/linux_pair_entry_v4.py').read_text()
        old = next(node for node in ast.parse(other).body if isinstance(node, ast.FunctionDef) and node.name == 'header_surface_check_v4')
        new = next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == 'header_surface_check_v4')
        self.assertEqual(ast.get_source_segment(other, old), ast.get_source_segment(SOURCE, new))
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            aggregate = hashlib.sha256(); surfaces = {}; total = 0
            for label in ('libc++', 'clang-resource'):
                root = base / label; root.mkdir()
                (root / 'dir').mkdir(); (root / 'dir/a').write_bytes(b'a'); (root / 'dir-z').write_bytes(b'z')
                rows = [{'relative': str(path.relative_to(root)), 'bytes': path.stat().st_size,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                        for path in sorted(root.rglob('*')) if path.is_file()]
                for row in rows:
                    aggregate.update(label.encode() + b'\0' + row['relative'].encode() + b'\0' + bytes.fromhex(row['sha256']))
                total += len(rows)
                surfaces[label] = {'path': str(root), 'count': len(rows),
                    'inventory_sha256': hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()}
            wanted = {'id': 'llvm-standard-resource-headers', 'sha256': aggregate.hexdigest(), 'files': total}
            self.assertEqual(CONTEXT['header_surface_check_v4'](surfaces, wanted, closed)['aggregate'], wanted)
            bad = dict(wanted, sha256='0' * 64)
            with self.assertRaises(ValueError): CONTEXT['header_surface_check_v4'](surfaces, bad, closed)
            (base / 'libc++/dir/a').write_bytes(b'mutated')
            with self.assertRaises(ValueError): CONTEXT['header_surface_check_v4'](surfaces, wanted, closed)
            (base / 'libc++/dir/a').write_bytes(b'a'); (base / 'libc++/link').symlink_to('dir/a')
            with self.assertRaises(ValueError): CONTEXT['header_surface_check_v4'](surfaces, wanted, closed)

    def test_control_template_exact_bytes_and_metadata_provenance(self):
        policy = json.loads((ROOT / 'linux_trace_policy_template_v2.json').read_bytes())
        for name, digest in policy['control_files'].items():
            path = ROOT / name
            if not path.exists():
                path = ROOT.parents[1] / 'evidence/resume-20261016-lane-coordination' / name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        import python_startup_roles_v2 as roles
        plan = policy['python_startup_roles_v2']
        self.assertEqual(plan['covered_descendants'], [
            {'path': '/usr/lib/python3.12/lib-dynload', 'root': '/usr/lib/python3.12'},
            {'path': '/usr/lib/python3.12/dist-packages', 'root': '/usr/lib/python3.12'}])
        self.assertEqual(len(plan['package_sys_path']), 7)
        self.assertEqual(plan['packages'], roles.PACKAGES)
        self.assertEqual(policy['linux_launch_binding']['entry_sha256'], hashlib.sha256(SOURCE.encode()).hexdigest())

    def test_progress_each_report_and_exception_is_fsynced(self):
        source = (ROOT / 'trace_pytest_child_v2.py').read_text()
        node = next(item for item in ast.walk(ast.parse(source)) if isinstance(item, ast.ClassDef) and item.name == 'Progress')
        namespace = dict(datetime=datetime, json=json, os=os)
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<pure-progress-hook>', 'exec'), namespace)
        with tempfile.TemporaryFile(mode='w+') as stream:
            plugin = namespace['Progress'](stream)
            with patch.object(os, 'fsync', wraps=os.fsync) as fsync:
                for when, outcome in [('setup', 'passed'), ('call', 'failed'), ('teardown', 'passed')]:
                    plugin.pytest_runtest_logreport(types.SimpleNamespace(nodeid='exact-case', when=when,
                        outcome=outcome, duration=0.1, longrepr='failure' if outcome == 'failed' else None))
                plugin.pytest_internalerror('internal', None)
                plugin.pytest_exception_interact(types.SimpleNamespace(nodeid='exact-case'), types.SimpleNamespace(excinfo='exception'),
                    types.SimpleNamespace(when='call', outcome='failed'))
                self.assertEqual(fsync.call_count, 5)
            stream.seek(0); values = [json.loads(line) for line in stream]
            self.assertEqual([row['outcome'] for row in values[:3]], ['passed', 'failed', 'passed'])
            self.assertTrue(all(row['at_utc'].endswith('+00:00') for row in values))
            self.assertEqual(values[-1]['event'], 'exception')

    def test_guarded_child_source_is_inert_and_startup_precedes_project(self):
        child = (ROOT / 'trace_pytest_child_v2.py').read_text()
        function = next(node for node in ast.parse(child).body if isinstance(node, ast.FunctionDef))
        observer = next(node for node in function.body if isinstance(node, ast.Assign) and ast.unparse(node.value).startswith('observe_role_v2('))
        project = next(node for node in function.body if isinstance(node, ast.ImportFrom) and node.module == 'swdb')
        self.assertLess(observer.lineno, project.lineno)
        comparison = next(node for node in function.body if isinstance(node, ast.If) and
            isinstance(node.test, ast.Compare) and isinstance(node.test.left, ast.DictComp))
        self.assertLess(observer.lineno, comparison.lineno)
        self.assertLess(comparison.lineno, project.lineno)
        # Execute only the three no-import guard statements with an inert observer
        # double to ensure post-package changes cannot reach project imports.
        assignments = [node for node in function.body if observer.lineno - 1 <= node.lineno <= comparison.lineno]
        context = {'arguments': {'startup_request': {'post_package_sys_path': ['/admitted']}}}
        context['observe_role_v2'] = lambda request: dict(request)
        exec(compile(ast.Module(body=assignments, type_ignores=[]), '<pure-child-startup-comparison>', 'exec'), context)
        context['observe_role_v2'] = lambda request: {'post_package_sys_path': ['/unlisted']}
        with self.assertRaises(ValueError):
            exec(compile(ast.Module(body=assignments, type_ignores=[]), '<pure-child-startup-comparison>', 'exec'), context)
        self.assertIn("plugins=[plugin]", child)
        self.assertIn("'tests': 25", SOURCE)
        self.assertIn("finally:", SOURCE)
        self.assertIn("closed.verify_python_metadata(physical) != physical_before", SOURCE)
        self.assertIn("flags = ['-I', '-B', '-X', 'pycache_prefix='", SOURCE)
        self.assertIn("[python, '-B', '-c', child_source", SOURCE)
        self.assertNotIn('skipif', child)


if __name__ == '__main__': unittest.main(verbosity=2)
