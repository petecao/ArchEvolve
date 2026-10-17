"""2026-10-16 ET. Source-only controls; never launch compiler or verifier."""
import hashlib
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import concrete_ready_v1 as ready


class Controls(unittest.TestCase):
    def setUp(self):
        self.backend = (HERE.parent / '28-whole-interface-resume-20261016/whole_value_backend_v1.h').read_bytes()

    def test_complete_backend_and_identical_polling_caller(self):
        unit = ready.prepare(self.backend)
        self.assertEqual(unit['backend_sha256'], hashlib.sha256(self.backend).hexdigest())
        self.assertIn(self.backend.decode(), unit['concrete_c'])
        self.assertEqual(unit['concrete_c'].count(self.backend.decode()), 1)
        self.assertIn(ready.CALLER, unit['concrete_c'])
        self.assertEqual(ready.remove_loop_annotation(unit['wp_c']), ready.wp_without_loop_annotation())
        self.assertIn(ready.CALLER, ready.remove_loop_annotation(unit['wp_c']))
        for source in (unit['concrete_c'], unit['wp_c']):
            self.assertIn('while (dxc_get_tile_ready(0) == 0)', source)
        with self.assertRaises(ValueError): ready.prepare(self.backend + b'\n')

    def test_one_step_relation_covers_stutter_and_completion(self):
        unit = ready.prepare(self.backend)
        text = unit['concrete_c']
        for marker in ('ready.refinement.answer', 'ready.refinement.pending',
                       'ready.refinement.value', 'ready.refinement.frame',
                       'ready.refinement.event_count', 'ready.refinement.choice_count'):
            self.assertIn(marker, text)
        self.assertIn('before = pending ? before : issued;', text)
        self.assertIn('dxb_step(pending, before, issued, answer)', text)
        self.assertFalse(unit['refinement_accepted'])
        self.assertFalse(unit['public_adoption'])

    def test_partial_loop_has_no_fairness_or_resource_counter(self):
        unit = ready.prepare(self.backend)
        wp = unit['wp_c']
        self.assertIn(r'terminates \false;', wp)
        self.assertNotIn('loop variant', wp)
        self.assertNotIn('assume(', wp)
        self.assertIn('loop invariant dxb_pending == 0 ==> dxb_visible == issued;', wp)
        self.assertIn('loop assigns dxb_pending, dxb_visible;', wp)
        self.assertEqual(ready.CALLER.count('dxc_get_tile_ready(0)'), 1)
        self.assertNotIn('prefix', ready.CALLER)
        self.assertEqual(unit['correctness'], 'partial correctness; infinite zero observations remain permitted')

    def test_exact_backend_closure_and_no_source_header_invention(self):
        unit = ready.prepare(self.backend)
        self.assertEqual(set(unit['concrete_functions']), {'dxc_get_tile_ready', 'dxc_wait_tile',
            'dxc_cover', 'dxm_cover', 'dxa_complete', 'dxm_device_write', 'dxm_value', 'dxc_cpu_memory_access'})
        for name, row in unit['concrete_functions'].items():
            self.assertEqual(hashlib.sha256(row['body'].encode()).hexdigest(), row['sha256'], name)
        self.assertIsNone(unit['original_header_query'])
        self.assertEqual(unit['same_entry_logical_rule'], 'finite_logical_ready')
        self.assertIn('actual complete one-step CBMC result', unit['required_acceptance'][0])

    def test_mutated_query_or_completion_body_refuses(self):
        for old, new in [(b'if (ready) dxc_wait_tile(tile);', b'if (!ready) dxc_wait_tile(tile);'),
                         (b'dxc_commands[i].pending=0;', b'dxc_commands[i].pending=1;'),
                         (b'dxm_memory[cell]=value;', b'dxm_memory[cell]=0;')]:
            changed = self.backend.replace(old, new)
            self.assertNotEqual(changed, self.backend)
            with self.assertRaises(ValueError): ready.prepare(changed)


if __name__ == '__main__': unittest.main(verbosity=2)
