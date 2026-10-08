from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

from archevolve.__main__ import reference_context
from archevolve.hardware_catalog import load_catalog, query_catalog, inspect_design
from archevolve.normalize import load_normalized
from archevolve.select import select_candidates
from archevolve.comparison import compare_designs
from archevolve.intrinsic_handoff import draft_intrinsics

ROOT = Path(__file__).resolve().parents[1]
DID = 'axi-pack-date2024-sell-required-l2-gather'
SUBTYPE = 'sell_required_l2_staging'


class AXIPackAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, _ = load_catalog(ROOT / 'catalog/hardware-v0.1.yaml')
        cls.design = inspect_design(cls.catalog, DID)

    def query(self, **kw):
        args = dict(design_id=DID, operation='read', subtype=SUBTYPE, address_pattern='indirect')
        args.update(kw)
        return query_catalog(self.catalog, **args)

    def test_explicit_scoped_mapping_retains_unknowns(self):
        result = self.query(payload_type='float64', index_width_bits=32)
        self.assertEqual(len(result['matches']), 1)
        self.assertEqual(result['matches'][0]['status'], 'needs_evidence')
        self.assertTrue(result['matches'][0]['requirements'])
        self.assertEqual(result['matches'][0]['operation']['subtype'], SUBTYPE)
        self.assertIsInstance(self.design['operations'][0]['datatype_notes'], str)

    def test_generic_read_subtypes_do_not_match(self):
        for subtype in ['gather', 'stream_load', 'totally_nonexistent']:
            with self.subTest(subtype=subtype):self.assertFalse(self.query(subtype=subtype)['matches'])

    def test_no_update_or_old_value_inheritance(self):
        for operation in ['write', 'read_modify_write', 'reduce']:
            with self.subTest(operation=operation):self.assertFalse(self.query(operation=operation)['matches'])
        self.assertFalse(self.query(require_old_value=True)['matches'])

    def test_sparse_and_dense_bfs_selection_unchanged(self):
        base = deepcopy(self.catalog)
        base['designs'] = [d for d in base['designs'] if d['id'] != DID]
        for name in ['bfs-sparse.features.v1.2.yaml', 'bfs-fully-connected.features.v1.2.yaml']:
            case = load_normalized(ROOT / 'examples/received' / name, reference_context(ROOT))
            with self.subTest(case=name):
                self.assertEqual(select_candidates(case, base, 'bound-catalog', 'fixed-digest', 12),
                                 select_candidates(case, self.catalog, 'bound-catalog', 'fixed-digest', 12))

    def test_explicit_intent_projections_keep_full_contract(self):
        case = load_normalized(ROOT / 'examples/received/bfs-sparse.features.v1.2.yaml', reference_context(ROOT))
        request, _ = select_candidates(case, self.catalog, 'bound-catalog', 'fixed-digest', 12)
        intent = deepcopy(request['capability_requests'][0])
        intent.update(operation='read', subtype=SUBTYPE, purpose='read', array='sell_indexed_vector_tile',
                      address_pattern='indirect', payload_type='float64', index_width_bits=32,
                      require_old_value=False, mutable_target=False, statement_ids=[], source_locations=[],
                      statement_binding_status='unbound', missing_workload_evidence=[],
                      mapping_basis='Synthetic explicit SELL intent; no actual kernel binding.')
        with patch('archevolve.evidence_select.capability_requests', return_value=([intent], [])):
            exact, _ = select_candidates(case, self.catalog, 'bound-catalog', 'fixed-digest', 2, [DID])
        candidate = exact['candidates'][1]
        draft = draft_intrinsics(exact, candidate)
        comparison = compare_designs(exact, self.catalog, [DID])['designs'][0]
        self.assertEqual(candidate['requirements'], self.design['requirements'])
        self.assertEqual(comparison['requirements'], self.design['requirements'])
        self.assertEqual(draft['requirements'], self.design['requirements'])
        self.assertEqual(draft['operations'][0]['postconditions']['catalog_result'], self.design['operations'][0]['result'])
        self.assertIsNone(draft['operations'][0]['concrete_signature'])
        self.assertIsNone(draft['operations'][0]['implementation_ref'])
        self.assertFalse(any(v for k, v in draft['readiness'].items() if k != 'description_generated'))

    def test_paper_mechanisms_and_units_do_not_certify_runtime(self):
        kinds = {m['kind'] for m in self.design['internal_mechanisms'] if m['status'] == 'described'}
        self.assertTrue({'coalescing', 'reordering', 'buffering', 'completion'}.issubset(kinds))
        l2 = next(p for p in self.design['parameters'] if p['id'] == 'l2_size')
        self.assertEqual(l2['unit'], 'KB (paper notation)')
        self.assertEqual(l2['state'], 'fixed_reference')
        self.assertTrue(any(m['status'] == 'unknown' for m in self.design['internal_mechanisms']))


if __name__ == '__main__':unittest.main()
