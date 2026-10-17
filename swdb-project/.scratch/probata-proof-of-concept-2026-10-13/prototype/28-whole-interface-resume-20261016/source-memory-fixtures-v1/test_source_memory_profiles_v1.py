"""No-child controls of exact prospective source requests, not source admission."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest


def deny(event, args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.fork','os.posix_spawn','socket.')) or event in {'os.system','ctypes.dlopen'}:
        raise RuntimeError('source-fixture preparation forbids '+event)


sys.addaudithook(deny)
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[4]
M=types.ModuleType('inert_source_profiles')
exec(compile(ast.parse((HERE/'source_memory_profiles_v1.py').read_bytes()),str(HERE/'source_memory_profiles_v1.py'),'exec'),M.__dict__)


class Controls(unittest.TestCase):
    def test_exact_three_callers_share_one_source_and_original_inventory(self):
        result=M.prepare(PROJECT,HERE/'same_thread_memory_v1.cpp')
        self.assertEqual(len(result['cases']),3)
        self.assertEqual([row['predicted_verdict'] for row in result['cases']],['refuted','refuted','proven'])
        self.assertEqual([row['contract']['ensures'] for row in result['cases']],
            [r'\result == 7',r'\result == 9',r'\result == 7'])
        self.assertEqual(len({row['prospective_mangled_name'] for row in result['cases']}),3)
        for row in result['cases']:
            self.assertEqual(row['thread'],0)
            self.assertEqual(row['contract']['assigns'],r'\everything')
            order=row['source_order_offsets']
            self.assertLess(order['issue'],order['CPU_access']);self.assertLess(order['CPU_access'],order['covering_wait'])
            request=row['ordinary_allocation_request']
            self.assertEqual(request['bytes'],64)
            self.assertTrue(request['requires_separately_owned_mapping'])
            self.assertTrue(request['alignment_is_not_inferred_from_source'])

    def test_read_request_never_grants_observation_or_owned_context(self):
        result=M.prepare(PROJECT,HERE/'same_thread_memory_v1.cpp')
        for key in ('compiler_observed','source_admission_granted','receiver_context_granted',
                    'old_fixed79_80_changed','abstract25_reused_or_relabelled'):
            self.assertIs(result[key],False)
        self.assertNotIn('accepted',result)
        self.assertNotIn('declaration_id',json.dumps(result))
        self.assertNotIn('get_tile_ready',(HERE/'same_thread_memory_v1.cpp').read_text())

    def test_source_mutation_missing_cover_or_alias_refuses_before_capture(self):
        original=(HERE/'same_thread_memory_v1.cpp').read_bytes()
        with tempfile.TemporaryDirectory(prefix='source-profiles-',dir=HERE) as tmp:
            root=Path(tmp).resolve();source=root/'caller.cpp';source.write_bytes(original)
            M.prepare(PROJECT,source)
            for raw in (original+b' ',original.replace(b'wait_ready(result);',b';',1),
                        original.replace(b'data[0] = 9;',b'data[1] = 9;',1)):
                source.write_bytes(raw)
                with self.assertRaises(M.Refused):M.prepare(PROJECT,source)
            source.write_bytes(original);link=root/'alias.cpp';link.symlink_to(source)
            with self.assertRaises(M.Refused):M.prepare(PROJECT,link)
            with self.assertRaises(OSError):M.prepare(root,source)


if __name__=='__main__':unittest.main(verbosity=2)
