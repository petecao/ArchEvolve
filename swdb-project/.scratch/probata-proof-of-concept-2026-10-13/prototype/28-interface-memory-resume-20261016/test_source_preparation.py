"""2026-10-16 ET. Pure literal source/role controls; no C/backend execution."""
import ast
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


def no_children(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        raise RuntimeError('source-only preparation refuses ' + event)


sys.addaudithook(no_children)
SOURCE = Path(__file__).with_name('interface_memory.py')
PROJECT = SOURCE.parents[4]
spec = importlib.util.spec_from_file_location('interface_memory_source_only', SOURCE)
memory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(memory)

# Literal expectations are independent of the parser and rendering algorithms.
# Entries: opcode, src1, src2, dst1, register sources, expected u64 masks
# (explicit read, explicit write, physical read, physical write, counted ready).
EXPECTED = {
    'maa_stream_load': ('STREAM_LD', None, None, 'dst_tile', ['min_reg', 'max_reg', 'stride_reg'],
                        {'dst_tile': 6, 'cond_tile': 4}, (16, 64, 16, 192, 192)),
    'maa_stream_store': ('STREAM_ST', 'src_tile', None, None, ['min_reg', 'max_reg', 'stride_reg'],
                         {'src_tile': 5, 'cond_tile': 4}, (48, 0, 112, 0, 96)),
    'maa_indirect_load': ('INDIR_LD', 'idx_tile', None, 'dst_tile', [],
                          {'idx_tile': 1, 'dst_tile': 5, 'cond_tile': 3}, (10, 32, 10, 96, 98)),
    'maa_indirect_store_scalar': ('INDIR_ST_SCALAR', 'idx_tile', None, 'dst_tile', ['src_reg'],
                                  {'idx_tile': 1, 'dst_tile': 5, 'cond_tile': 3}, (10, 32, 10, 96, 98)),
    'maa_indirect_store_vector': ('INDIR_ST_VECTOR', 'idx_tile', 'src_tile', 'dst_tile', [],
                                  {'idx_tile': 1, 'src_tile': 5, 'dst_tile': 9, 'cond_tile': 3}, (42, 512, 106, 1536, 1634)),
    'maa_indirect_rmw_scalar': ('INDIR_RMW_SCALAR', 'idx_tile', None, 'dst_tile', ['src_reg'],
                                {'idx_tile': 1, 'dst_tile': 5, 'cond_tile': 3}, (10, 32, 10, 96, 98)),
    'maa_indirect_rmw_vector': ('INDIR_RMW_VECTOR', 'idx_tile', 'src_tile', 'dst_tile', [],
                                {'idx_tile': 1, 'src_tile': 5, 'dst_tile': 9, 'cond_tile': 3}, (42, 512, 106, 1536, 1634)),
}


class SourcePreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binding = memory.inventory(PROJECT)
        cls.calls = {call['name']: call for call in cls.binding['calls']}
        cls.header = memory.render_header(cls.binding)

    def masks(self, name, arguments, dtype=3, tiles=32):
        return memory.project_roles(self.calls[name], dtype, arguments, tiles)

    def test_exact_seven_pinned_source_call_mappings(self):
        self.assertEqual(set(self.calls), set(EXPECTED))
        for name, (opcode, src1, src2, dst1, registers, _, _) in EXPECTED.items():
            with self.subTest(name=name):
                call = self.calls[name]
                self.assertEqual(call['opcode'], opcode)
                for role, expected in [('src1', src1), ('src2', src2), ('dst1', dst1)]:
                    value = call['roles'][role]
                    self.assertEqual(None if value is None else value['parameter'], expected)
                self.assertEqual(call['register_parameters_not_yet_bound'], registers)
                self.assertIsNone(call['roles']['dst2'])
                self.assertEqual(call['roles']['condition'], {'parameter': 'cond_tile', 'optional': True})

    def test_all_seven_u64_masks_match_independent_literals(self):
        for name, row in EXPECTED.items():
            with self.subTest(name=name):
                result = self.masks(name, row[5])
                self.assertEqual(tuple(result[key] for key in ['explicit_read', 'explicit_write', 'physical_read', 'physical_write', 'ready_roles']), row[6])

    def test_all_six_dtypes_keep_index_and_condition_four_byte_roles(self):
        for dtype in range(6):
            with self.subTest(dtype=dtype):
                masks = self.masks('maa_indirect_load', {'idx_tile': 1, 'dst_tile': 5, 'cond_tile': 3}, dtype=dtype)
                self.assertEqual(masks['physical_read'], 10)
                self.assertEqual(masks['physical_write'], 32 if dtype < 3 else 96)
                self.assertEqual(masks['ready_roles'], 34 if dtype < 3 else 98)

    def test_condition_only_role_is_not_counted(self):
        masks = self.masks('maa_stream_load', {'dst_tile': 6, 'cond_tile': 4})
        self.assertEqual(masks['physical_read'], 16)
        self.assertEqual(masks['ready_roles'], 192)
        self.assertEqual(masks['ready_roles'] & 16, 0)

    def test_counted_second_half_is_present_without_even_id_rule(self):
        masks = self.masks('maa_stream_store', {'src_tile': 5, 'cond_tile': -1})
        self.assertEqual(masks['explicit_read'], 32)
        self.assertEqual(masks['physical_read'], 96)
        self.assertEqual(masks['ready_roles'], 96)

    def test_optional_old_result_and_condition_can_be_absent(self):
        masks = self.masks('maa_indirect_rmw_scalar', {'idx_tile': 1, 'dst_tile': -1, 'cond_tile': -1})
        self.assertEqual(masks, {'explicit_read': 2, 'explicit_write': 0, 'physical_read': 2, 'physical_write': 0, 'ready_roles': 2})

    def test_same_id_condition_source_alias_is_counted_when_widths_agree(self):
        masks = self.masks('maa_stream_store', {'src_tile': 5, 'cond_tile': 5}, dtype=0)
        self.assertEqual(masks['ready_roles'], 32)

    def test_condition_source_width_disagreement_refuses(self):
        with self.assertRaisesRegex(memory.Refused, 'getWordSize'):
            self.masks('maa_stream_store', {'src_tile': 5, 'cond_tile': 5})

    def test_index_data_width_disagreement_refuses(self):
        with self.assertRaisesRegex(memory.Refused, 'getWordSize'):
            self.masks('maa_indirect_store_vector', {'idx_tile': 5, 'src_tile': 5, 'dst_tile': -1, 'cond_tile': -1})

    def test_physical_input_output_alias_refuses_even_with_distinct_starts(self):
        with self.assertRaisesRegex(memory.Refused, 'disjointness'):
            self.masks('maa_indirect_store_vector', {'idx_tile': 1, 'src_tile': 5, 'dst_tile': 6, 'cond_tile': -1})

    def test_last_u64_pair_and_non_sentinel_negative_ids_refuse(self):
        for values in [{'src_tile': 31, 'cond_tile': -1}, {'src_tile': 5, 'cond_tile': -2}]:
            with self.subTest(values=values), self.assertRaises(memory.Refused):
                self.masks('maa_stream_store', values)

    def test_exact_arguments_and_integer_type_domain_are_required(self):
        for dtype, values in [(True, {'src_tile': 5, 'cond_tile': -1}), (6, {'src_tile': 5, 'cond_tile': -1}), (0, {'src_tile': 5}), (0, {'src_tile': True, 'cond_tile': -1})]:
            with self.subTest(dtype=dtype, values=values), self.assertRaises(memory.Refused):
                self.masks('maa_stream_store', values, dtype=dtype)

    def test_modified_pinned_header_refuses_before_inventory(self):
        read_bytes = Path.read_bytes
        def changed(path):
            data = read_bytes(path)
            return data + b'\n' if path.name == 'MAA_gem5.hpp' else data
        with patch.object(Path, 'read_bytes', changed), self.assertRaisesRegex(memory.Refused, 'immutable source'):
            memory.inventory(PROJECT)

    def test_generated_all_seven_wrappers_have_literal_role_entries(self):
        for name, row in EXPECTED.items():
            with self.subTest(name=name):
                body = self.header.split('static unsigned dxi_prepare_' + name + '(', 1)[1].split('\n}\n', 1)[0]
                self.assertIn('dxi_add_role(&masks,widths,cond_tile,4,1,0,0);', body)
                if row[1]:
                    width = '4' if row[0].startswith('INDIR') else '(dtype < 3 ? 4 : 8)'
                    self.assertIn('dxi_add_role(&masks,widths,' + row[1] + ',' + width + ',0,0,1);', body)
                if row[2]:
                    self.assertIn('dxi_add_role(&masks,widths,' + row[2] + ',(dtype < 3 ? 4 : 8),0,0,1);', body)
                if row[3]:
                    optional = 0 if row[0] in {'STREAM_LD', 'INDIR_LD'} else 1
                    self.assertIn('dxi_add_role(&masks,widths,' + row[3] + ',(dtype < 3 ? 4 : 8),' + str(optional) + ',1,1);', body)
                access = 1 if row[0] in {'STREAM_LD', 'INDIR_LD'} else 2
                self.assertIn('return dxi_prepare_memory(thread,' + str(access) + ',source_base,domain,masks);', body)

    def test_generated_region_and_line_checks_precede_counted_prepare(self):
        self.assertLess(self.header.index('dxr_assign(source_base)'), self.header.index('dxr_check_span(assigned'))
        self.assertLess(self.header.index('dxr_check_span(assigned'), self.header.index('dxc_store_span(begin,end-begin,domain.line_bytes)'))
        self.assertLess(self.header.index('dxc_store_span(begin,end-begin,domain.line_bytes)'), self.header.index('return dxc_prepare_counted('))
        self.assertNotIn('return dxc_prepare(', self.header)
        self.assertNotIn('dxc_get_tile_ready(', self.header)

    def test_source_preparation_does_not_promote_public_or_current_version(self):
        self.assertFalse(self.binding['public_support'])
        self.assertFalse(self.binding['current_0_2'])
        tree = ast.parse(SOURCE.read_text())
        imports = {node.names[0].name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import)}
        self.assertTrue(imports <= {'hashlib', 'json', 're'})
        self.assertNotIn('subprocess', SOURCE.read_text())


if __name__ == '__main__':
    unittest.main()
