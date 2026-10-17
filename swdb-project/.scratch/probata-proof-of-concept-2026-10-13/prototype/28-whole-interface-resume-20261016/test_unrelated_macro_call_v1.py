"""2026-10-16 ET. Narrow unrelated-macro location regression; synthetic metadata."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest


def deny(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        raise RuntimeError('macro location controls refuse '+event)


sys.addaudithook(deny)
HERE=Path(__file__).resolve().parent


def own(name):
    path=HERE/name;ns={'__file__':str(path),'__name__':'inert_macro_location_fixture'}
    exec(compile(ast.parse(path.read_bytes()),str(path),'exec'),ns)
    return ns


API=own('whole_interface_v4.py');OLD=own('whole_interface_v3.py');DISPATCH=own('source_dispatch_v3.py')
BASE=own('test_whole_interface.py');BASE['API']=API


class Controls(BASE['Controls']):
    def test_07_unrelated_indirect_call_no_longer_blocks_the_selected_direct_api(self):
        row=next(r for r in self.declarations if r['name']=='get_new_tile')
        tu,kw=self.fixture(row)
        macro={'kind':'CallExpr','range':{'begin':{'spellingLoc':{'offset':123},'expansionLoc':{'offset':0}},
                                        'end':{'spellingLoc':{'offset':124},'expansionLoc':{'offset':0,'tokLen':6}}},
               'inner':[{'kind':'DeclRefExpr','referencedDecl':{'kind':'FunctionDecl','name':'__assert_fail','id':'ordinary-assert-failure'}}]}
        tu['inner'][1]['inner'][0]['inner'].append(macro)
        with self.assertRaises(OLD['Refused']):OLD['bind_call'](tu,**kw)
        binding=API['bind_call'](tu,**kw)
        result=DISPATCH['bind_dispatch'](API,tu,binding=binding,staged_arguments=[],thread='owned_thread',**kw)
        self.assertEqual(result['model_expression'],'dws_get_new_tile_unsigned_int(owned_thread)')
        self.assertFalse(result['public_admission'])

    def test_08_selected_macro_site_and_ambiguous_direct_sites_still_refuse(self):
        row=next(r for r in self.declarations if r['name']=='get_new_tile')
        for mutation in ('macro','duplicate'):
            tu,kw=self.fixture(row);call=tu['inner'][1]['inner'][0]['inner'][0]
            if mutation=='macro':call['range']['begin']={'spellingLoc':{'offset':0},'expansionLoc':{'offset':kw['call_range'][0]}}
            else:tu['inner'][1]['inner'][0]['inner'].append(copy.deepcopy(call))
            with self.assertRaises(API['Refused']):API['bind_call'](tu,**kw)

    def test_09_all_three_inverse_deltas_restore_physical_predecessors(self):
        receipt=json.loads((HERE/'unrelated-macro-call-v1-inverse-delta.json').read_bytes())
        self.assertEqual(len(receipt['versions']),3)
        for row in receipt['versions']:
            original=Path(row['old_path']).read_bytes();raw=Path(row['new_path']).read_bytes();inverse=raw.decode()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),row['new_sha256'])
            self.assertEqual(hashlib.sha256(original).hexdigest(),row['old_sha256'])
            for edit in reversed(row['edits']):
                self.assertEqual(inverse.count(edit['new']),1);inverse=inverse.replace(edit['new'],edit['old'],1)
            self.assertEqual(inverse.encode(),original)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'skips':len(result.skipped),'actual_compiler_or_project_child':False},sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
