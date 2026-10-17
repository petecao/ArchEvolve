"""Compiler-free source/profile/loop-selection controls; no scientific run."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
EVENTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event); raise RuntimeError('no child/native/network in resource controls')


sys.addaudithook(audit)


def namespace():
    result = {'__name__': 'pure_first_source_resources'}
    exec(compile((HERE / 'resource_profile_v1.py').read_bytes(), str(HERE / 'resource_profile_v1.py'), 'exec'), result)
    return result


class Controls(unittest.TestCase):
    def test_source_and_all_four_bodies_are_exact_physical_reviewed_bytes(self):
        ns = namespace()
        self.assertEqual(hashlib.sha256((WHOLE / 'source_call_fixture_v2.cpp').read_bytes()).hexdigest(), ns['SOURCE_SHA'])
        for name, digest in ns['COMPONENTS'].items():
            self.assertEqual(hashlib.sha256((WHOLE / name).read_bytes()).hexdigest(), digest)

    def test_first_source_structural_calls_and_conservative_accounting(self):
        ns = namespace(); source = (WHOLE / 'source_call_fixture_v2.cpp').read_text()
        counts = {'maa_stream_load': 4, 'maa_stream_store': 1, 'maa_alu_scalar': 1, 'maa_alu_vector': 1,
            'maa_alu_reduce': 1, 'maa_indirect_load': 1, 'maa_indirect_store_vector': 1,
            'maa_indirect_store_scalar': 1, 'maa_indirect_rmw_vector': 1, 'maa_indirect_rmw_scalar': 1, 'maa_range_loop': 1}
        for name, count in counts.items(): self.assertEqual(len(re.findall(r'\b' + name + r'\s*<', source)), count)
        selected = ns['select'](ns['SOURCE_SHA'], ns['FUNCTION'], dict(ns['COMPONENTS']))
        self.assertEqual(selected['structural_node_budget'], 828)
        self.assertGreater(selected['DXM_NODES'], selected['structural_node_budget'])
        # Even the four loads' conservative structural slice exceeds default128.
        self.assertGreater(4 * 58, selected['backend_default_DXM_NODES'])

    def test_unknown_source_function_component_or_changed_profile_refuse(self):
        ns = namespace(); selected = ns['select'](ns['SOURCE_SHA'], ns['FUNCTION'], dict(ns['COMPONENTS']))
        for sha, function, components in [('0' * 64, ns['FUNCTION'], ns['COMPONENTS']),
            (ns['SOURCE_SHA'], 'whole_same_thread_read_during_gather', ns['COMPONENTS']),
            (ns['SOURCE_SHA'], ns['FUNCTION'], {})]:
            with self.assertRaises(ns['Refused']): ns['select'](sha, function, components)
        for key, value in [('DXM_NODES', 2048), ('structural_node_budget', 128), ('default_helper_unwind', 1),
                           ('helper_owner_unwind', {}), ('capacity_evaluation_and_unwinding_assertions_retained', False)]:
            bad = {**selected, key: value}
            with self.assertRaises(ns['Refused']): ns['prefix'](bad)

    def test_prefix_is_explicit_and_backend_defaults_and_guards_are_unchanged(self):
        ns = namespace(); selected = ns['select'](ns['SOURCE_SHA'], ns['FUNCTION'], ns['COMPONENTS'])
        prefix = ns['prefix'](selected); backend = (WHOLE / 'whole_value_backend_v1.h').read_text()
        self.assertIn('#ifdef DXM_NODES\n#error', prefix); self.assertIn('#define DXM_NODES 1024', prefix)
        self.assertIn('#ifndef DXM_NODES\n#define DXM_NODES 128\n#endif', backend)
        for literal in ('steps++ < 20*DXM_NODES', 'depth < DXM_NODES', 'dxm_count < DXM_NODES', 'DXM_NODES <= UINT_MAX/20'):
            self.assertTrue(literal in backend, literal)
        self.assertNotIn('assume', prefix)

    def test_actual_opaque_selector_order_only_cover_owner_gets_larger_bound(self):
        ns = namespace(); profile = ns['select'](ns['SOURCE_SHA'], ns['FUNCTION'], ns['COMPONENTS'])
        loops = ['dxp_find.0', 'dxm_cover.7', 'dws_prepare_receiver_v1.3', 'dxm_cover.0']
        rows = ns['helper_loop_bounds'](profile, loops, ['dxp_find', 'dxm_cover', 'dws_prepare_receiver_v1'])
        self.assertEqual([row['loop'] for row in rows], loops)
        self.assertEqual([row['unwind'] for row in rows], [513, 20481, 513, 20481])
        for bad in (['unknown.0'], ['dxm_cover.0', 'dxm_cover.0'], ['dxm_cover.bad'], [{}], 'dxm_cover.0'):
            with self.assertRaises(ns['Refused']): ns['helper_loop_bounds'](profile, bad, ['dxm_cover'])

    def test_source_profile_performs_no_imported_project_or_native_execution(self):
        imports = [node for node in ast.parse((HERE / 'resource_profile_v1.py').read_bytes()).body if isinstance(node, (ast.Import, ast.ImportFrom))]
        self.assertEqual({alias.name for node in imports for alias in node.names}, {'json', 're'})
        self.assertEqual(EVENTS, [])


if __name__ == '__main__': unittest.main(verbosity=2)
