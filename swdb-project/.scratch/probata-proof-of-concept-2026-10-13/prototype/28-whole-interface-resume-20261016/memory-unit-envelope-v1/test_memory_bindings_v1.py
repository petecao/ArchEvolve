"""2026-10-16 ET. Actual-source temporary staging only; no ABI/TU execution."""
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
PURE = runpy.run_path(str(HERE / 'test_envelope_v1.py'), run_name='memory_envelope_source_controls')


class MemoryBindingControls(unittest.TestCase):
    def test_real35_control_packet_stages17_memory_inputs_and_source(self):
        ns = PURE['namespace']()
        command = json.loads((HERE / 'command-v1.json').read_bytes())
        outer = json.loads((HERE / 'envelope-policy-v1.json').read_bytes())
        original = json.loads((HERE / 'observation-policy-v1.json').read_bytes())
        observer_path = WHOLE / 'memory-normalized-ingress-v2/observer/observe_memory_entry_v1.py'
        observer = runpy.run_path(str(observer_path), run_name='memory_observer_control_functions_only')
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory).resolve() / ns['RAW_NAME']; (raw / 'control').mkdir(parents=True)
            policy = json.loads(json.dumps(outer).replace(command['raw'], str(raw)))
            selected = json.loads(json.dumps(original).replace(command['raw'], str(raw)))
            for name, row in command['stage_sources'].items():
                path = raw / 'control' / name
                path.write_bytes(Path(row['path']).read_bytes())
                policy['controls'][name] = ns['pin'](path)
            for name in selected['controls']:
                selected['controls'][name] = {**policy['controls'][name], 'path': str(raw / 'observer/control' / name)}
            path = raw / 'control/observation-policy-v1.json'
            path.write_text(json.dumps(selected, sort_keys=True, separators=(',', ':')))
            policy['controls'][path.name] = ns['pin'](path)
            policy['observer_policy'] = {**ns['pin'](path), 'path': str(raw / 'observer/control' / path.name)}
            ns['stage_layout'](raw, policy)
            values, modules = observer['controls'](selected, raw / 'observer/control')
            self.assertEqual((len(values), len(modules)), (17, 14))
            self.assertEqual((raw / 'library_fixture/proof_units/same_thread_memory_v1.cpp').read_bytes(),
                (WHOLE / 'source-memory-fixtures-v1/same_thread_memory_v1.cpp').read_bytes())
            self.assertEqual(hashlib.sha256((raw / 'library_fixture/proof_units/same_thread_memory_v1.cpp').read_bytes()).hexdigest(),
                '55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887')

    def test_memory_runtime_and_original_transform_roles_are_exact(self):
        policy = json.loads((HERE / 'observation-policy-v1.json').read_bytes())
        frozen = json.loads((WHOLE / 'memory-normalized-ingress-v2/observer/observation-policy-template-v1.json').read_bytes())
        self.assertEqual(policy['capture'], frozen['capture'])
        self.assertIsNone(policy['capture']['prepared'])
        self.assertEqual(policy['capture']['original']['abi']['sha256'],
            '493764cb6cbb2783db0cdfbbaf1bfd7d3b6efc73ff27df77eb9e5d6e8603b55c')
        self.assertEqual(policy['capture']['transform']['normalized_gzip']['sha256'],
            '8f19a9369b02fde545e7d979d8c5e7852078cc004d8330e7a54ba0c70a7f2aba')
        outer = json.loads((HERE / 'envelope-policy-v1.json').read_bytes())
        self.assertEqual(outer['runtime_policy']['sha256'],
            'd1bfb65ad9bf85aab9cd7dce14ef3b5002134878d86dbaae432814b3082c7cf6')
        self.assertNotEqual(outer['runtime_policy']['sha256'],
            '8d86faea6d8235c9431acddae4d28e08831afaaca1ebc506e9363d66e8e32517')

    def test_fourth_metadata_output_is_closed_and_checked(self):
        ns = PURE['namespace']()
        self.assertEqual(ns['OBSERVER_OUTPUTS'], ('whole-unit-preparation.json', 'observed-input-pins.json',
            'memory-source-units.json', 'unit-observation-result.json'))
        with tempfile.TemporaryDirectory() as directory:
            raw = Path(directory).resolve(); (raw / 'observer/control').mkdir(parents=True)
            (raw / 'observer/memory-source-units.json').write_bytes(b'{}')
            ns['check_outputs'](raw)
            (raw / 'observer/other-units.json').write_bytes(b'{}')
            with self.assertRaises(ValueError): ns['check_outputs'](raw)

    def test_data_only_proposal_receipt_does_not_claim_review_or_context(self):
        policy = json.loads((HERE / 'observation-policy-v1.json').read_bytes())
        command = json.loads((HERE / 'command-v1.json').read_bytes())
        self.assertEqual(policy['root_admission_receipt']['path'], command['raw'] + '/control/memory-source-proposal.json')
        self.assertEqual(policy['root_admission_receipt']['sha256'],
            '9904def8876809e84e737355c93f6a1c87bfb4751bf1c901a05a3b6629915df9')
        self.assertFalse(command['root_metadata_complete'])
        self.assertFalse(command['actual_executed'])
        self.assertEqual(policy['proof_source'], {'root': 'library', 'path': 'proof_units/same_thread_memory_v1.cpp',
            'sha256': '55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'})


if __name__ == '__main__': unittest.main(verbosity=2)
