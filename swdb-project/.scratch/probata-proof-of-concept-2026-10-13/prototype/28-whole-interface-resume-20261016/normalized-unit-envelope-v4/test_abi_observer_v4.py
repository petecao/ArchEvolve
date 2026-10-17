"""2026-10-16 ET. Exact fixed-source ABI inlet/staging controls; no actual TU."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
OBSERVER = HERE / 'observer'
OLD = WHOLE / 'normalized-unit-observation-v1'
ABI = WHOLE / 'abi-role-transport-v2'
ENVELOPE = runpy.run_path(str(HERE / 'test_envelope_v4.py'), run_name='exact_no_child_envelope_controls')


def sha(raw): return hashlib.sha256(raw).hexdigest()


class ABIObserverControls(unittest.TestCase):
    def test_all_source_inverses_and_nine_old_module_bytes_exact(self):
        inverse = json.loads((HERE / 'exact-inverses-v4.json').read_bytes())
        for relative, row in inverse['files'].items():
            text = (HERE / relative).read_text()
            for replacement in reversed(row['replacements']):
                self.assertEqual(text.count(replacement['new']), replacement['count'])
                text = text.replace(replacement['new'], replacement['old'])
            original = Path(row['basis']['path']).read_bytes()
            self.assertEqual(sha(original), row['basis']['sha256'])
            self.assertEqual(text.encode(), original)
        current = json.loads((OBSERVER / 'fixed-modules-v2.json').read_bytes())['modules']
        prior = json.loads((OLD / 'fixed-modules-v1.json').read_bytes())['modules']
        actual = {row['module']: (OBSERVER / 'modules' / row['file']).read_bytes() for row in current}
        old = {row['module']: (OLD / 'modules' / row['file']).read_bytes() for row in prior}
        changed = {key for key in old if actual[key] != old[key]}
        self.assertEqual(changed, {'swdb._dx100_whole.normalized_capture_ingress_v2', 'swdb._dx100_whole.normalized_compiler_adapter_v1'})
        self.assertEqual(sum(actual[key] == value for key, value in old.items()), 9)
        self.assertEqual(set(actual) - set(old), {'swdb._dx100_whole.abi_role_transport_v1', 'swdb._dx100_whole.strict_minify_v2'})
        self.assertEqual(actual['swdb._dx100_whole.compiler_unit_adapter_v3'], old['swdb._dx100_whole.compiler_unit_adapter_v3'])
        self.assertEqual(actual['swdb._dx100_whole.normalized_compiler_adapter_v1'], (ABI / 'normalized_compiler_adapter_v2.py').read_bytes())
        self.assertEqual(actual['swdb._dx100_whole.abi_role_transport_v1'], (ABI / 'abi_role_transport_v1.py').read_bytes())

    def test_real_ingress_physical_adapter_gate_V3_RED_V4_GREEN(self):
        path = OBSERVER / 'modules/normalized_capture_ingress_v2.py'
        tree = ast.parse(path.read_bytes())
        loop = next(node for node in ast.walk(tree) if isinstance(node, ast.For) and
            isinstance(node.target, ast.Tuple) and ast.unparse(node.target) == '(module, expected)')
        expected = {'normalizer': 'role_normalized_gzip_v2.py', 'codec': 'lossless_gzip_v2.py',
            'closed': 'closed_python_surface.py', 'normalized_compiler': 'normalized_compiler_adapter_v2.py'}
        def need(value, message):
            if not value: raise ValueError(message)
        def absolute(row):
            raw = Path(row['path']).read_bytes()
            need(len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'real physical primitive gate')
        ns = {'Path': Path, 'hashlib': hashlib, 'need': need, 'reads': SimpleNamespace(absolute=absolute)}
        for name, file in expected.items(): ns[name] = SimpleNamespace(__file__=str(OBSERVER / 'modules' / file))
        ns['normalized_compiler'].LEGACY_SHA = '775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c'
        ns['source'] = SimpleNamespace(compiler=SimpleNamespace(__file__=str(OBSERVER / 'modules/compiler_unit_adapter_v3.py')))
        constants = [node for node in tree.body if isinstance(node, ast.Assign)]
        exec(compile(ast.Module(body=constants, type_ignores=[]), '<exact-ingress-constant-bindings>', 'exec'), ns)
        code = compile(ast.Module(body=[loop], type_ignores=[]), '<exact-promoted-primitive-gate>', 'exec')
        self.assertEqual(ns['NORMALIZED_COMPILER_SHA'], '8acf26651a1e682bb6857128f1a0d5e184b52f489cccd32ea60eb471c1a65ff3')
        exec(code, ns)
        ns['NORMALIZED_COMPILER_SHA'] = '0bbf572196677dbc926bb5d331022c2766e44c287bd1ea3cce0ef077153a8a01'
        with self.assertRaises(ValueError): exec(code, ns)

    def test_real_fifteen_controls_are_copied_and_physically_rechecked(self):
        ns = ENVELOPE['namespace']()
        command = json.loads((HERE / 'command-v4.json').read_bytes())
        policy = json.loads((HERE / 'envelope-policy-v4.json').read_bytes())
        observer = runpy.run_path(str(OBSERVER / 'observe_entry_v2.py'), run_name='private_observer_control_functions_only')
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory).resolve() / ns['RAW_NAME']
            (raw / 'control').mkdir(parents=True)
            old_raw = command['raw']
            selected = json.loads(json.dumps(policy).replace(old_raw, str(raw)))
            for name, origin in command['stage_sources'].items():
                target = raw / 'control' / name
                data = Path(origin['path']).read_bytes()
                target.write_bytes(data)
                selected['controls'][name] = ns['pin'](target)
            observer_policy = json.loads((HERE / 'observation-policy-v1.json').read_bytes())
            observer_policy = json.loads(json.dumps(observer_policy).replace(old_raw, str(raw)))
            for name in observer_policy['controls']:
                observer_policy['controls'][name] = {**selected['controls'][name], 'path': str(raw / 'observer/control' / name)}
            target = raw / 'control/observation-policy-v1.json'
            target.write_bytes(json.dumps(observer_policy, sort_keys=True, separators=(',', ':')).encode())
            selected['controls'][target.name] = ns['pin'](target)
            selected['observer_policy'] = {**ns['pin'](target), 'path': str(raw / 'observer/control' / target.name)}
            ns['stage_layout'](raw, selected)
            values, modules = observer['controls'](observer_policy, raw / 'observer/control')
            self.assertEqual(len(values), 15)
            self.assertEqual(len(modules), 13)
            self.assertEqual(set(values), set(ns['OBSERVER_CONTROLS']))
            self.assertIsNone(observer_policy['capture']['prepared'])
            for name in ('abi_role_transport_v1.py', 'strict_minify_v2.py'):
                (raw / 'observer/control' / name).write_bytes(values[name] + b'\n')
                with self.assertRaises(ValueError): observer['controls'](observer_policy, raw / 'observer/control')
                (raw / 'observer/control' / name).write_bytes(values[name])

    def test_fixed_dependency_order_and_compatibility_role_are_closed(self):
        manifest = json.loads((OBSERVER / 'fixed-modules-v2.json').read_bytes())
        modules = manifest['modules']; order = {row['module']: index for index, row in enumerate(modules)}
        for suffix in ('role_normalized_gzip_v2', 'strict_minify_v2'):
            self.assertLess(order['swdb._dx100_whole.' + suffix], order['swdb._dx100_whole.abi_role_transport_v1'])
        self.assertLess(order['swdb._dx100_whole.abi_role_transport_v1'], order['swdb._dx100_whole.normalized_compiler_adapter_v1'])
        self.assertLess(order['swdb._dx100_whole.normalized_compiler_adapter_v1'], order['swdb._dx100_whole.normalized_capture_ingress_v2'])
        self.assertEqual(manifest['compatibility_module_alias'], {'swdb._dx100_whole.normalized_compiler_adapter_v1': 'normalized_compiler_adapter_v2.py'})
        self.assertNotIn('normalized_compiler_adapter_v1.py', {row['file'] for row in modules})
        self.assertEqual(ENVELOPE['namespace']()['OBSERVER_SHA'], sha((OBSERVER / 'observe_entry_v2.py').read_bytes()))

    def test_original_derived_ABI_receipt_and_prepared_unknown_are_required(self):
        text = (OBSERVER / 'modules/normalized_compiler_adapter_v2.py').read_text()
        self.assertIn("'original_raw_probe_sha256':abi_receipt['original_sha256']", text)
        self.assertIn("prepared['abi_observation']['raw_probe_sha256']==abi_receipt['derived_strict_sha256']", text)
        self.assertIn("'paired_type_role_transport':abi_receipt", text)
        helper = (OBSERVER / 'modules/abi_role_transport_v1.py').read_text()
        self.assertIn("('paired-type-normalizer','strict-token-grammar')", helper)
        self.assertIn("[primitive(normalizer, NORMALIZER_SHA), primitive(tokens, TOKENS_SHA)] == before", helper)
        policy = json.loads((HERE / 'observation-policy-v1.json').read_bytes())
        prior = json.loads((WHOLE / 'normalized-unit-envelope-v3/observation-policy-v1.json').read_bytes())
        old_raw = prior['output_root'].removesuffix('/observer')
        new_raw = policy['output_root'].removesuffix('/observer')
        self.assertEqual(policy['capture'], json.loads(json.dumps(prior['capture']).replace(old_raw, new_raw)))
        self.assertIsNone(policy['capture']['prepared'])
        self.assertEqual(policy['capture']['original']['abi']['sha256'], '0416fecb76bfec1cd375b8d0940de7b1306e9d9b3d591fd0683f544c080ddf15')
        command = json.loads((HERE / 'command-v4.json').read_bytes())
        self.assertEqual(command['guard'], {'whole_seconds': 1200, 'rss_bytes': 4294967296, 'workers': 1, 'retained_bytes': 268435456})
        self.assertEqual(command['root_launch_requirements']['run_environment_unset'], ['LIBRARY_PATH', 'LD_LIBRARY_PATH'])
        self.assertEqual(command['root_launcher']['sha256'], 'b4a2664da950070e5e37ffb88eb260e90d8cdb2d5a591504a7e9723c4891272b')


if __name__ == '__main__': unittest.main(verbosity=2)
