"""2026-10-16 ET. Pure small filesystem controls; all runtimes are inert bytes.

No target module/.pth/interpreter, compiler, native code, child or SSH executes.
Expected inventory construction independently reproduces lane's producer source.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

import closed_python_surface as gate
from cbmc_release_gate import check_cbmc_version


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn')) or event in {'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        raise RuntimeError('pure Python-surface control refuses ' + event)


sys.addaudithook(deny)
digest = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def pin(path):
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def inventory(root):
    rows = []
    for path in sorted(root.rglob('*')):
        row = {'relative': str(path.relative_to(root))}
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            row.update(kind='symlink', target=os.readlink(path), resolved=str(path.resolve(strict=True)))
        elif stat.S_ISDIR(mode):
            row.update(kind='directory')
        elif stat.S_ISREG(mode):
            row.update(kind='file', **{key: value for key, value in pin(path).items() if key != 'path'})
        else:
            raise AssertionError('fixture only regular files/directories/known links')
        rows.append(row)
    return rows


def summary(root):
    rows = inventory(root)
    return {'path': str(root), 'counts': {'entries': len(rows), 'files': sum(r['kind'] == 'file' for r in rows),
            'directories': sum(r['kind'] == 'directory' for r in rows), 'symlinks': sum(r['kind'] == 'symlink' for r in rows)},
            'total_bytes': sum(r.get('bytes', 0) for r in rows), 'inventory_sha256': digest(rows), 'symlinks': {}}


def chain(path):
    result = []
    while path.is_symlink():
        target = os.readlink(path)
        result.append({'path': os.path.normpath(str(path)), 'target': target})
        path = Path(os.path.normpath(str(path.parent / target))) if not Path(target).is_absolute() else Path(target)
    return result


class PythonSurfaceControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='t28-python-surface-inert-')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.roots = [self.base / name for name in ('stdlib', 'venv-site', 'local-dist', 'system-dist')]
        for root in self.roots:
            root.mkdir()
        self.external = self.base / 'external'
        self.external.mkdir()
        self.target = self.external / 'shared.txt'
        self.target.write_text('inert known external target\n')
        self.intermediate = self.external / 'intermediate'
        self.intermediate.symlink_to('shared.txt')
        self.link = self.roots[0] / 'known.py'
        self.link.symlink_to('../external/intermediate')
        self.target_dir = self.external / 'locale-data'
        self.target_dir.mkdir()
        (self.target_dir / 'en.dat').write_text('inert locale A')
        (self.target_dir / 'fr.dat').write_text('inert locale B')
        self.directory_link = self.roots[3] / 'locale-data'
        self.directory_link.symlink_to('../external/locale-data')
        (self.roots[0] / 'dir').mkdir()
        (self.roots[0] / 'dir/a.py').write_text('inert A')
        (self.roots[0] / 'dir-z.py').write_text('inert B')
        self.site = self.roots[0] / 'site.py'
        self.site.write_text('inert site startup source; never import\n')
        self.pth = self.roots[3] / 'distutils-precedence.pth'
        self.pth.write_text("import _distutils_hack # inert bytes, never execute\n")
        self.hack = self.roots[3] / '_distutils_hack'
        self.hack.mkdir()
        (self.hack / '__init__.py').write_text('inert startup helper')
        self.cfg = self.external / 'pyvenv.cfg'
        self.cfg.write_text('include-system-site-packages = true\n')
        self.customize = self.external / 'sitecustomize.py'
        self.customize.write_text('inert sitecustomize source')
        self.binary = self.external / 'python-real'
        self.binary.write_text('inert interpreter bytes; never execute')
        self.alias = self.external / 'python'
        self.alias.symlink_to('python3')
        (self.external / 'python3').symlink_to('python-real')
        self.absent = self.external / 'python312.zip'
        surfaces = {str(root): summary(root) for root in self.roots}
        surfaces[str(self.roots[0])]['symlinks']['known.py'] = {
            'target': os.readlink(self.link), 'resolved': str(self.target), 'target_kind': 'file',
            'chain': chain(self.link), 'bytes': self.target.stat().st_size, 'sha256': pin(self.target)['sha256']}
        target_summary = summary(self.target_dir)
        surfaces[str(self.roots[3])]['symlinks']['locale-data'] = {
            'target': os.readlink(self.directory_link), 'resolved': str(self.target_dir), 'target_kind': 'directory',
            'chain': chain(self.directory_link), 'target_counts': target_summary['counts'],
            'target_total_bytes': target_summary['total_bytes'], 'target_inventory_sha256': target_summary['inventory_sha256']}
        self.policy = {'schema': gate.SCHEMA, 'surfaces': surfaces,
            'startup_pins': [pin(path) for path in (self.site, self.cfg, self.customize, self.pth, self.hack / '__init__.py')],
            'pth': [{**pin(self.pth), 'lines_sha256': digest(self.pth.read_text().splitlines())}],
            'interpreter': {'path': str(self.alias), 'chain': chain(self.alias), 'resolved': str(self.binary), 'target_pin': pin(self.binary)},
            'absence': {str(self.absent): True}, 'candidate_expected_sys_path': ['never-admitted-inference'],
            'actual_sys_path_observed': False}

    def test_exact_four_roots_known_file_chain_directory_target_and_empty_root(self):
        receipt = gate.verify_python_metadata(self.policy)
        self.assertTrue(receipt['before_after_equal'])
        self.assertEqual(receipt['before'], receipt['after'])
        self.assertEqual(len(receipt['before']['surfaces']), 4)
        self.assertEqual(receipt['before']['surfaces'][str(self.roots[2])]['counts']['entries'], 0)
        self.assertNotIn('files', receipt['before']['surfaces'][str(self.roots[0])])
        self.assertLess(len(json.dumps(receipt).encode()), 1048576)

    def test_component_order_matches_exact_lane_producer_not_raw_string_order(self):
        rows = inventory(self.roots[0])
        names = [row['relative'] for row in rows]
        self.assertLess(names.index('dir/a.py'), names.index('dir-z.py'))
        self.assertNotEqual(names, sorted(names))
        self.assertEqual(gate.verify_python_metadata(self.policy)['before']['surfaces'][str(self.roots[0])]['inventory_sha256'], digest(rows))

    def test_regular_content_addition_deletion_and_empty_directory_membership_refuse(self):
        path = self.roots[1] / 'added.py'
        path.write_text('new')
        with self.assertRaises(gate.Refused): gate.verify_python_metadata(self.policy)
        path.unlink()
        path.mkdir()
        with self.assertRaises(gate.Refused): gate.verify_python_metadata(self.policy)
        path.rmdir()
        original = self.site.read_bytes()
        self.site.write_bytes(original + b'changed')
        with self.assertRaises(gate.Refused): gate.verify_python_metadata(self.policy)
        self.site.unlink()
        with self.assertRaises(gate.Refused): gate.verify_python_metadata(self.policy)

    def test_unlisted_link_refuses_before_target_follow(self):
        extra = self.roots[1] / 'unlisted'
        extra.symlink_to('/unobserved/nonexistent/target')
        with self.assertRaisesRegex(gate.Refused, 'unlisted Python link'):
            gate.verify_python_metadata(self.policy)

    def test_raw_link_literal_chain_completeness_and_target_bytes_are_pinned(self):
        self.link.unlink()
        self.link.symlink_to('../external/./intermediate')
        with self.assertRaisesRegex(gate.Refused, 'raw link target'):
            gate.verify_python_metadata(self.policy)
        self.link.unlink()
        self.link.symlink_to('../external/intermediate')
        changed = copy.deepcopy(self.policy)
        changed['surfaces'][str(self.roots[0])]['symlinks']['known.py']['chain'].pop()
        with self.assertRaisesRegex(gate.Refused, 'unlisted or changed link chain'):
            gate.verify_python_metadata(changed)
        self.target.write_text('same known path; changed external bytes')
        with self.assertRaisesRegex(gate.Refused, 'physical file bytes differ'):
            gate.verify_python_metadata(self.policy)

    def test_target_directory_complete_membership_and_nested_links_refuse(self):
        new = self.target_dir / 'new.dat'
        new.write_text('new')
        with self.assertRaises(gate.Refused): gate.verify_python_metadata(self.policy)
        new.unlink()
        new.symlink_to('../shared.txt')
        with self.assertRaisesRegex(gate.Refused, 'unlisted Python link'):
            gate.verify_python_metadata(self.policy)

    def test_unknown_ancestor_link_refuses_even_when_final_bytes_are_unchanged(self):
        physical = self.base / 'external-physical'
        self.external.rename(physical)
        self.external.symlink_to(physical)
        with self.assertRaisesRegex(gate.Refused, 'unlisted or changed link chain'):
            gate.verify_python_metadata(self.policy)

    def test_root_replacement_by_symlink_and_special_input_refuse(self):
        root = self.roots[2]
        root.rmdir()
        root.symlink_to(self.roots[1])
        with self.assertRaises(gate.Refused): gate.verify_python_metadata(self.policy)
        root.unlink()
        root.mkdir()
        if hasattr(os, 'mkfifo'):
            os.mkfifo(root / 'special')
            with self.assertRaisesRegex(gate.Refused, 'special Python import input'):
                gate.verify_python_metadata(self.policy)

    def test_executable_pth_census_source_and_line_digest_refuse(self):
        changed = copy.deepcopy(self.policy)
        changed['pth'] = []
        with self.assertRaisesRegex(gate.Refused, '.pth census'):
            gate.verify_python_metadata(changed)
        changed = copy.deepcopy(self.policy)
        changed['pth'][0]['lines_sha256'] = '0' * 64
        with self.assertRaisesRegex(gate.Refused, '.pth bytes/line digest'):
            gate.verify_python_metadata(changed)
        changed = copy.deepcopy(self.policy)
        changed['startup_pins'] = [pin for pin in changed['startup_pins'] if pin['path'] != str(self.pth)]
        with self.assertRaisesRegex(gate.Refused, 'explicitly bound as startup source'):
            gate.verify_python_metadata(changed)

    def test_pyvenv_sitecustomize_and_interpreter_chain_are_not_ambient_exemptions(self):
        original = self.cfg.read_bytes()
        self.cfg.write_bytes(original + b'changed')
        with self.assertRaises(gate.Refused): gate.verify_python_metadata(self.policy)
        self.cfg.write_bytes(original)
        self.customize.write_text('changed hook')
        with self.assertRaises(gate.Refused): gate.verify_python_metadata(self.policy)
        self.customize.write_text('inert sitecustomize source')
        changed = copy.deepcopy(self.policy)
        changed['interpreter']['chain'].pop()
        with self.assertRaisesRegex(gate.Refused, 'unlisted or changed link chain'):
            gate.verify_python_metadata(changed)

    def test_missing_startup_zip_rejects_regular_or_dangling_link_appearance(self):
        self.absent.write_text('new startup zip')
        with self.assertRaisesRegex(gate.Refused, 'missing-path'):
            gate.verify_python_metadata(self.policy)
        self.absent.unlink()
        self.absent.symlink_to('missing-target')
        with self.assertRaisesRegex(gate.Refused, 'missing-path'):
            gate.verify_python_metadata(self.policy)

    def test_second_complete_pass_catches_concurrent_changes(self):
        original = gate._pass
        passes = []
        def mutate_after_first(policy):
            result = original(policy)
            passes.append(True)
            if len(passes) == 1:
                (self.roots[1] / 'late.py').write_text('new after first pass')
            return result
        with patch.object(gate, '_pass', side_effect=mutate_after_first), self.assertRaises(gate.Refused):
            gate.verify_python_metadata(self.policy)
        self.assertEqual(len(passes), 1)

    def test_guarded_sys_path_uses_only_explicit_actual_root_metadata(self):
        observed = {'sys_path': [str(root) for root in self.roots],
                    'flags': {'isolated': 1, 'no_user_site': 1, 'dont_write_bytecode': True, 'optimize': 0},
                    'executable': str(self.alias), 'prefix': str(self.external), 'base_prefix': str(self.base),
                    'pycache_prefix': str(self.base / 'fresh-raw/bootstrap-cache'),
                    'startup_environment': {'SETUPTOOLS_USE_DISTUTILS': None, 'PYTHONPATH': None,
                        'PYTHONPYCACHEPREFIX': str(self.base / 'fresh-raw/bootstrap-cache'), 'PYTHONDONTWRITEBYTECODE': '1',
                        'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'PROBATA_OUTPUT': str(self.base / 'fresh-raw'),
                        'SWDB_VERIFIER_LOCK': str(self.base / 'fresh-raw/verifier.lock'), 'SWDB_VERIFIER_RSS_CAP_BYTES': '8589934592'}}
        physical = digest({key: self.policy[key] for key in ('schema', 'surfaces', 'startup_pins', 'pth', 'interpreter', 'absence')})
        receipt = json.dumps({'schema': 'root-guarded-python-startup-1', 'startup': observed}, sort_keys=True).encode()
        receipt_sha = hashlib.sha256(receipt).hexdigest()
        expected = {'admitted': True, 'root_metadata_sha256': receipt_sha, 'physical_metadata_sha256': physical, **observed}
        def rebind_observation(value):
            raw = json.dumps({'schema': 'root-guarded-python-startup-1', 'startup': value}, sort_keys=True).encode()
            return {**expected, **value, 'root_metadata_sha256': hashlib.sha256(raw).hexdigest()}, raw
        self.assertEqual(gate.check_guarded_startup(expected, observed, metadata=self.policy, root_receipt_bytes=receipt)['root_metadata_sha256'], receipt_sha)
        changed = copy.deepcopy(observed)
        changed['sys_path'].append('/unadmitted/path')
        with self.assertRaises(gate.Refused): gate.check_guarded_startup(expected, changed, metadata=self.policy, root_receipt_bytes=receipt)
        changed = copy.deepcopy(observed)
        changed['startup_environment']['SETUPTOOLS_USE_DISTUTILS'] = 'stdlib'
        with self.assertRaises(gate.Refused): gate.check_guarded_startup(expected, changed, metadata=self.policy, root_receipt_bytes=receipt)
        unpinned = copy.deepcopy(observed)
        unpinned['sys_path'].append(str(self.external))
        changed_policy, changed_receipt = rebind_observation(unpinned)
        with self.assertRaisesRegex(gate.Refused, 'lacks closed physical coverage'):
            gate.check_guarded_startup(changed_policy, unpinned, metadata=self.policy, root_receipt_bytes=changed_receipt)
        for field, value in [('executable', str(self.binary)), ('prefix', str(self.base)),
                             ('pycache_prefix', str(self.base / 'previous-probe/bootstrap-cache'))]:
            changed = copy.deepcopy(observed)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(gate.Refused):
                gate.check_guarded_startup(expected, changed, metadata=self.policy, root_receipt_bytes=receipt)
        zip_observation = copy.deepcopy(observed)
        zip_observation['sys_path'].append(str(self.external / 'unlisted.zip'))
        changed_policy, changed_receipt = rebind_observation(zip_observation)
        with self.assertRaisesRegex(gate.Refused, 'lacks closed physical coverage'):
            gate.check_guarded_startup(changed_policy, zip_observation, metadata=self.policy, root_receipt_bytes=changed_receipt)
        for field, value, reason in [('executable', str(self.binary), 'pinned interpreter'),
                                     ('prefix', str(self.base), 'venv configuration')]:
            changed = copy.deepcopy(observed)
            changed[field] = value
            changed_policy, changed_receipt = rebind_observation(changed)
            with self.subTest(field=field), self.assertRaisesRegex(gate.Refused, reason):
                gate.check_guarded_startup(changed_policy, changed, metadata=self.policy, root_receipt_bytes=changed_receipt)
        with self.assertRaisesRegex(gate.Refused, 'receipt bytes differ'):
            gate.check_guarded_startup(expected, observed, metadata=self.policy, root_receipt_bytes=receipt + b' ')
        for field in ('physical_metadata_sha256', 'root_metadata_sha256'):
            changed = copy.deepcopy(expected)
            changed[field] = 'unknown'
            with self.subTest(field=field), self.assertRaises(gate.Refused):
                gate.check_guarded_startup(changed, observed, metadata=self.policy, root_receipt_bytes=receipt)
        expected['admitted'] = False
        with self.assertRaisesRegex(gate.Refused, 'admission is unknown'):
            gate.check_guarded_startup(expected, observed, metadata=self.policy, root_receipt_bytes=receipt)
        with self.assertRaises(gate.Refused):
            gate.check_guarded_startup(self.policy, observed, metadata=self.policy, root_receipt_bytes=receipt)

    def test_exact_root_observed_cbmc_patch_keeps_unchanged_method_family(self):
        policy = {'accepted_cbmc_release_family': '6.11', 'tools': {'cbmc': {'version': '6.11.0'}}}
        result = check_cbmc_version(policy, 0, '6.11.0\n', '')
        self.assertEqual(result['exact_observed_version'], '6.11.0')
        self.assertEqual(result['stdout_sha256'], hashlib.sha256(b'6.11.0\n').hexdigest())
        for output in ('6.12\n', '6.110\n', '6.11\n', '6.11.1\n', '6.11.0.1\n', '6.11.0bad\n', 'CBMC6.11.0\n', ''):
            with self.subTest(output=output), self.assertRaises(ValueError):
                check_cbmc_version(policy, 0, output, '')
        for version in (None, '6.12', '6.110', '6.11.0.1', 'unknown'):
            with self.subTest(version=version), self.assertRaises(ValueError):
                check_cbmc_version({'accepted_cbmc_release_family': '6.11', 'tools': {'cbmc': {'version': version}}}, 0, '6.11.0\n', '')


if __name__ == '__main__':
    unittest.main(verbosity=2)
