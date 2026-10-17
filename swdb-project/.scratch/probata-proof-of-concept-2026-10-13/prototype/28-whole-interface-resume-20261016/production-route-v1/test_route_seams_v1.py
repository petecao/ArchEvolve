"""No-child stdlib controls of the actual proposed harness/source seams.

Project code is parsed, not imported. Only closed named nodes are compiled
into inert namespaces; imported project collaborators are explicit stand-ins.
No source program, compiler, solver, native binary, or verifier is executed.
"""
import ast
import copy
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent


def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'os.exec', 'os.spawn', 'os.system')):
        raise AssertionError('forbidden child/network: ' + event)


sys.addaudithook(audit)


def extracted(path, names, namespace):
    tree = ast.parse(path.read_text())
    selected = [node for node in tree.body if getattr(node, 'name', None) in names]
    assert {node.name for node in selected} == set(names)
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def source_namespace():
    ns = {'dataclass':dataclass, 'Path':Path, 'hashlib':hashlib, 'json':json, 're':re,
          'FUNCTION':'whole_interface_source_fixture', 'SOURCE_SHA':'3'*64,
          'KIND':'dx100-whole-interface-source-v1', 'SourceSelection':object}
    return extracted(HERE/'proposed/swdb/dx100_checked_source.py',
        {'Refused','need','sha','canonical','digest','SourceUnit','harness_profile',
         'unit_contract','lowering_fields','model_fields'},ns)


def namespace(path, source):
    def inert_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == 'swdb' and fromlist == ('dx100_checked_source',):
            return SimpleNamespace(dx100_checked_source=SimpleNamespace(**source))
        raise AssertionError('unexpected import in extracted node: ' + name)
    ns = {'dataclass':dataclass,'field':field,'re':re,
          'TOOL_ID':'controlled-translator','TOOL_VERSION':'controlled-v1','HAVOC_BUDGET':1024,
          'REACH_END':'swdb_reach.end','REAL_WORDS':('float','double','real'),
          'std_models':SimpleNamespace(OUT_OF_RANGE='controlled.range'),
          '_array_domain_plan':lambda *args:{},
          'expression':lambda text,*args,**kwargs:'(swdb_result == 80)',
          '_frame':lambda *args:'1',
          '__builtins__':dict(vars(__import__('builtins')),__import__=inert_import)}
    return extracted(path,{'Untranslatable','Clause','Interface','Plan','harness','is_real_type','_print','_draw'},ns)


def unit(source,budget=4):
    rows = [{'name':'whole_choice_'+str(i),'role':'whole-model-choice','ctype':'uint32_t',
             'c_lvalue':'dws_choice_table['+str(i)+']'} for i in range(budget)]
    return source['SourceUnit'](function=source['FUNCTION'],returns='unsigned int',
        source_text='unsigned int whole_interface_source_fixture(void) { return 80u; }\n',
        model_text='static void helper(void) {}\n', anchors=(), summaries=(),
        certificate_json=b'{}', draw_rows_json=json.dumps(rows).encode(), input_pins=(),
        policy_json=json.dumps({'choice_budget':budget,'defines':['NUM_CORES=4','TILE_SIZE=16384'],
                               'unit_contract':{'id':'unit.first','sha256':'a'*64}}).encode(),
        normalized_tu={},unit_preparation={},statement_preparation={},atlas={},allocations=(),abi={},selection=None,
        receiver_policy_pin_json=b'{}',receiver_preparation=None)


class RouteSeams(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = source_namespace()
        cls.new = namespace(HERE/'proposed/swdb/cbmc_translator.py',cls.source)
        cls.old = namespace(HERE/'base-source/cbmc_translator.py',cls.source)

    def interface(self): return self.new['Interface'](self.source['FUNCTION'],'unsigned int',())
    def rows(self): return [self.new['Clause']('ensures',r'\result == 80','first#value'),
                            self.new['Clause']('assigns',r'\everything','first#frame')]

    def build(self,value,**kwargs):
        return self.new['harness'](self.interface(),self.rows(),sizes={},cap=0,whole_source=value,**kwargs)

    def test_old_default_is_byte_identical(self):
        interface=self.interface();rows=[self.new['Clause']('ensures',r'\result == 80','first#value')]
        args={'sizes':{},'cap':0,'setup':('legacy_init();',),'state':('old_state',)}
        old,op=self.old['harness'](interface,rows,**args)
        new,np=self.new['harness'](interface,rows,**args)
        self.assertEqual(old,new)
        self.assertEqual(op.draws,np.draws)
        self.assertEqual(op.capacity,np.capacity)

    def test_actual_harness_registers_receiver_draws_once(self):
        text,plan=self.build(unit(self.source,4))
        self.assertEqual(plan.inputs,4)
        self.assertEqual(plan.capacity,1028)
        self.assertEqual(text.count('dws_prepare_receiver_v1();'),1)
        self.assertNotIn('swdb_next()',text)
        self.assertNotIn('swdb_dx_init',text)
        for i in range(4):
            self.assertIn('dws_choice_table['+str(i)+']',text)
            self.assertNotIn('(long long) whole_choice_'+str(i),text)

    def test_full_uint32_choice_slot_domain_is_not_restricted(self):
        text,plan=self.build(unit(self.source,256))
        self.assertEqual(plan.inputs,256)
        self.assertEqual(plan.capacity,1280)
        self.assertTrue(all(set(row)=={'name','role','ctype','c_lvalue'} for row in plan.draws))
        self.assertNotIn('SWDB_ASSUME(',text)

    def test_budget_zero_and_excess_refuse(self):
        for budget in (0,257):
            with self.assertRaises(self.new['Untranslatable']):
                self.build(unit(self.source,budget))

    def test_replay_lvalue_and_draw_order_mutations_refuse(self):
        original=unit(self.source)
        for mutation in ('lvalue','name','role','ctype','delete','reverse'):
            altered=copy.deepcopy(original); rows=json.loads(altered.draw_rows_json)
            if mutation=='lvalue':rows[0]['c_lvalue']='injected()'
            elif mutation=='name':rows[0]['name']='other'
            elif mutation=='role':rows[0]['role']='state'
            elif mutation=='ctype':rows[0]['ctype']='int'
            elif mutation=='delete':rows.pop()
            else:rows.reverse()
            object.__setattr__(altered,'draw_rows_json',json.dumps(rows).encode())
            with self.assertRaises(self.new['Untranslatable']):self.build(altered)

    def test_generic_reset_havoc_and_callbacks_refuse(self):
        for options in ({'setup':('swdb_dx_init();',)}, {'state':('x',)}, {'finish':('ignore();',)},
                        {'knobs':(('x','x>=0',(0,1)),)}, {'call':'substitute'}, {'check':True},
                        {'array_domains':{'p':{'bound':4}}}):
            with self.assertRaises(self.new['Untranslatable']): self.build(unit(self.source),**options)

    def test_only_broad_explicit_frame_is_supported(self):
        for text in (r'\nothing','x',r'\everything, x'):
            rows=self.rows();rows[1]=self.new['Clause']('assigns',text,'first#frame')
            with self.assertRaises(self.new['Untranslatable']):
                self.new['harness'](self.interface(),rows,sizes={},cap=0,whole_source=unit(self.source))
        text,_=self.build(unit(self.source))
        self.assertIn('SWDB_PROP(1, "first#frame")',text)
        self.assertIn('SWDB_PROP((swdb_result == 80), "first#value")',text)

    def test_native_mode_rejects_second_line_in_same_program(self):
        text,_=self.build(unit(self.source))
        self.assertIn('if (fgets(swdb_line, sizeof swdb_line, stdin)) return 3;',text)
        self.assertLess(text.index('if (fgets(swdb_line'),text.index('  return 0;\n}',text.index('if (fgets(swdb_line')))
        # The adapter must launch each oracle row separately; no reset can make
        # the receiver reusable. This control covers generated harness source.

    def test_scalar_bound_is_still_rejected_by_real_harness(self):
        with self.assertRaises(self.new['Untranslatable']):
            self.new['harness'](self.interface(),self.rows(),sizes={'input_size':1},cap=0,
                               whole_source=unit(self.source))

    def test_exact_selected_unit_contract_identity(self):
        library=SimpleNamespace(content_sha256=lambda name:'a'*64)
        check=self.source['unit_contract'];value=unit(self.source)
        check(library,value,'unit.first','a'*64,self.rows())
        for ident,digest in (('other','a'*64),('unit.first','b'*64)):
            with self.assertRaises(ValueError):check(library,value,ident,digest,self.rows())
        for row in (self.new['Clause']('requires','1','x'),self.new['Clause']('ensures',r'\result == 81','x')):
            with self.assertRaises(ValueError):check(library,value,'unit.first','a'*64,self.rows()+[row])

    def test_helpers_and_source_loop_functions_are_disjoint(self):
        value=unit(self.source)
        object.__setattr__(value,'selection',SimpleNamespace(entry_id='new.entry',library=SimpleNamespace(content_sha256=lambda _:'a'*64)))
        data=self.source['model_fields'](value)
        self.assertEqual(data['functions'],('helper',))
        self.assertEqual(data['unwind'],513)
        for name in (self.source['FUNCTION'],'dws_source_program'):
            altered=copy.deepcopy(value);object.__setattr__(altered,'model_text','static void '+name+'(void) {}\n')
            with self.assertRaises(ValueError):self.source['model_fields'](altered)

    def test_hook_exact_source_inverse(self):
        inverse=json.loads((HERE/'hook-inverse-v1.json').read_text())
        for name,edits in inverse.items():
            restored=(HERE/'proposed/swdb'/name).read_text()
            for row in reversed(edits):
                self.assertEqual(restored.count(row['new']),row['count'])
                restored=restored.replace(row['new'],row['old'])
            self.assertEqual(restored,(HERE/'base-source'/name).read_text())

    def test_cache_bypass_precedes_generic_options_and_tool_probe(self):
        tree=ast.parse((HERE/'proposed/swdb/formal_frame.py').read_text())
        f=next(node for node in tree.body if getattr(node,'name',None)=='lowered')
        branch=next(node for node in f.body if isinstance(node,ast.If) and ast.unparse(node.test)=='selection is not None')
        self.assertIn('whole_source_selection=selection',ast.unparse(branch))
        self.assertNotIn('_LOWERED',ast.unparse(branch))
        cached=next(node for node in f.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='key' for t in node.targets))
        self.assertLess(branch.lineno,cached.lineno)

    def test_actual_v8_capture_refusal_cannot_be_promoted(self):
        source=HERE/'proposed/swdb/dx100_checked_source.py'
        receipt=HERE.parents[2]/'evidence/t28-capture-v8-root-observation-20261016t2130z.json'
        actual=json.loads(receipt.read_bytes())['actual']['component/result.json']
        self.assertEqual(actual['accepted'],False)
        self.assertEqual(actual['error']['message'],'expanded compiler stream limit exceeded')
        ns=extracted(source,{'complete_capture'},dict(self.source,CAPTURE_KIND='lossless-complete-original-tu-v1'))
        keys={'kind','policy','result','observation','prepared','runtime_before','runtime_after','zlib_before',
              'zlib_after','zlib_runtime','gzip_receipt','compressed_tu','abi','probe','source'}
        selected={name:name for name in keys};selected['kind']=ns['CAPTURE_KIND']
        read=SimpleNamespace(document=lambda name:actual if name=='result' else {})
        with self.assertRaises(self.source['Refused']):ns['complete_capture']({'capture':selected},read,None)


if __name__=='__main__': unittest.main(verbosity=2)
