"""2026-10-16 ET. Pure controls for a prospective partial readiness proof."""
import hashlib
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ready_loop


class ReadyLoopControls(unittest.TestCase):
    def test_both_pending_answers_and_completed_query(self):
        self.assertEqual(ready_loop.step(1, 3, 7, 0), (0, 1, 3))
        self.assertEqual(ready_loop.step(1, 3, 7, 1), (1, 0, 7))
        self.assertEqual(ready_loop.step(0, 7, 7, 0), (1, 0, 7))

    def test_zero_does_not_supply_a_cover_or_progress_bound(self):
        pending, visible = 1, 3
        for _ in range(10000):
            answer, pending, visible = ready_loop.step(pending, visible, 7, 0)
            self.assertEqual((answer, pending, visible), (0, 1, 3))
        self.assertEqual(ready_loop.step(pending, visible, 7, 1), (1, 0, 7))

    def test_invalid_states_and_bool_type_confusion_refuse(self):
        for args in ((True, 3, 7, 0), (2, 3, 7, 0), (0, 3, 7, 0),
                     (1, -1, 7, 0), (1, 3, 2**32, 0), (1, 3, 7, True)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                ready_loop.step(*args)

    def test_exact_model_and_explicit_partial_method(self):
        backend = (HERE.parent / '28-whole-interface-resume-20261016/whole_value_backend_v1.h').read_bytes()
        plan = ready_loop.prepare(backend)
        self.assertEqual(plan['model_sha256'], hashlib.sha256(backend).hexdigest())
        self.assertIn(r'terminates \false;', plan['C_source'])
        self.assertIn('while (ready == 0)', plan['C_source'])
        self.assertIn('loop invariant ready == 1 ==> pending == 0;', plan['C_source'])
        self.assertFalse(plan['concrete_model_refinement_admitted'])
        self.assertFalse(plan['public_source_or_ticket_acceptance'])
        self.assertEqual(plan['correctness'], 'partial; no fairness or eventual-ready premise')
        with self.assertRaises(ValueError): ready_loop.prepare(backend + b'\n')

    def test_closed_fixture_does_not_invent_an_original_header_call(self):
        backend = (HERE.parent / '28-whole-interface-resume-20261016/whole_value_backend_v1.h').read_bytes()
        plan = ready_loop.prepare(backend)
        self.assertEqual(plan['source_interface_call'], None)
        self.assertEqual(plan['logical_query'], 'dxc_get_tile_ready')
        self.assertEqual(plan['topology']['pending_commands'], 1)
        self.assertEqual(plan['topology']['dependencies'], [])
        self.assertNotIn('assume(', plan['C_source'])
        self.assertNotIn('loop variant', plan['C_source'])


if __name__ == '__main__': unittest.main(verbosity=2)
