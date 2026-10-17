"""2026-10-16 ET. Pure twelve-global source observation controls, not actual TU."""
import ast
import copy
import json
from pathlib import Path
import re
import sys
import unittest


def deny(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        raise RuntimeError('source global controls refuse '+event)


sys.addaudithook(deny)
HERE=Path(__file__).resolve().parent


def own(name):
    p=HERE/name;ns={'__file__':str(p),'__name__':'inert_source_global_fixture'}
    exec(compile(ast.parse(p.read_bytes()),str(p),'exec'),ns)
    return ns


API=own('whole_interface_v3.py');GLOBALS=own('source_program_globals_v1.py')


class Controls(unittest.TestCase):
    def setUp(self):
        self.declarations=API['inventory'](HERE.parents[3]);headers={Path(row['header_path']).name:row for row in self.declarations}
        self.nodes=[]
        for index,(name,(header,typ,_)) in enumerate(GLOBALS['GLOBALS'].items()):
            path=Path(headers[header]['header_path']);text=path.read_text()
            match=re.search(r'^'+re.escape(typ).replace(r'\ ',r'\s*')+r'\s*'+re.escape(name)+r'\s*;',text,re.M)
            end=match.end()-1
            while text[end-1].isspace():end-=1
            self.nodes.append({'kind':'VarDecl','id':'global'+str(index),'name':name,'type':{'qualType':typ},
                'loc':{'_file':str(path)},'range':{'begin':{'offset':match.start()},'end':{'offset':end-1,'tokLen':1}}})
        self.tu={'kind':'TranslationUnitDecl','inner':self.nodes}
        self.kw={'execution_mode':'fresh-cxx-program-globals','program_context_receipt_sha256':'a'*64}

    def test_01_all_twelve_globals_are_source_zeros_without_device_reset(self):
        out=GLOBALS['observe_globals'](API,self.tu,self.declarations,**self.kw)
        self.assertEqual(len(out['globals']),12)
        pointers=[row for row in out['globals'] if row['CXX_static_initialization']=='null pointer']
        self.assertEqual(len(pointers),8)
        self.assertTrue(all(row['source_initial_value'] is None for row in pointers))
        self.assertTrue(all(row['source_initial_value']==0 for row in out['globals'] if row not in pointers))
        for key in ('model_reset_called','alloc_MAA_called','init_MAA_called','device_payload_initializedness_granted',
                    'device_ownership_granted','preexisting_command_history_cleared','device_receiver_state_bound','public_admission'):
            self.assertFalse(out[key])
        for row in pointers:
            if row['name'] in {'INSTR_tsrc1_tsrc2_rdst1_rdst2_rsrc1_rsrc2_rsrc3_csrc','INSTR_baseaddr'}:
                self.assertEqual(row['model_host_receiver_relation']['kind'],'instruction-pointer-derived-only-after-allocation')
                self.assertEqual(row['model_host_receiver_relation']['unallocated_source_value'],'null pointer')

    def test_02_malformed_global_definition_and_census_refuse(self):
        for key,value in (('init','c'),('storageClass','extern'),('tls','dynamic'),('inner',[{'kind':'ImplicitValueInitExpr'}]),
                          ('id',''),('loc',{'_file':'/wrong/MAA.hpp'}),('type',{'qualType':'unsigned int'})):
            mutated=copy.deepcopy(self.tu);mutated['inner'][0][key]=value
            with self.assertRaises(GLOBALS['Refused']):GLOBALS['observe_globals'](API,mutated,self.declarations,**self.kw)
        for nodes in (self.nodes[:-1],self.nodes+[copy.deepcopy(self.nodes[0])],
                      [{'kind':'NamespaceDecl','name':'wrong','inner':self.nodes}]):
            with self.assertRaises(GLOBALS['Refused']):GLOBALS['observe_globals'](API,dict(self.tu,inner=nodes),self.declarations,**self.kw)
        mutated=copy.deepcopy(self.tu);mutated['inner'][0]['range']['end']['offset']-=1
        with self.assertRaises(GLOBALS['Refused']):GLOBALS['observe_globals'](API,mutated,self.declarations,**self.kw)

    def test_03_execution_context_does_not_follow_from_source_hash(self):
        for key,value in (('execution_mode','reused-device'),('execution_mode','fresh-device'),('program_context_receipt_sha256','unbound')):
            kw=dict(self.kw);kw[key]=value
            with self.assertRaises(GLOBALS['Refused']):GLOBALS['observe_globals'](API,self.tu,self.declarations,**kw)
        out=GLOBALS['observe_globals'](API,self.tu,self.declarations,**self.kw)
        self.assertTrue(out['fresh_program_interpretation_requires_root_admission'])
        self.assertTrue(out['pointer_null_is_source_semantic_value_not_raw_bit_claim'])


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'skips':len(result.skipped),'actual_compiler_or_project_child':False},sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
