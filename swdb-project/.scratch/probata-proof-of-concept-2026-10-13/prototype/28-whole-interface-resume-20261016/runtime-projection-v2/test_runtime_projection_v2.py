"""2026-10-16 ET. Source preparation/strings only, no native or actual TU."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('runtime source controls refuse '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;PROJECT=WHOLE.parents[3]
def load(path):
    ns={'__name__':'inert_projection_controls','__file__':str(path)};exec(compile(path.read_bytes(),str(path),'exec'),ns);return ns
R=load(HERE/'runtime_projection_v2.py');BASE=load(WHOLE/'test_whole_interface.py')
API,_=R['component'](WHOLE,'whole_interface_v4.py');DISPATCH,_=R['component'](WHOLE,'source_dispatch_v3.py')
ABI=BASE['ABI'];DECLS=API['inventory'](PROJECT);SOURCE=(WHOLE/'source_call_fixture_v2.cpp').read_text()
ALLOCATIONS=[{'object_index':0},{'object_index':1}]
HEADER,INVENTORY,INSTANCES=R['render_header'](API,DISPATCH,PROJECT,DECLS,ABI,ALLOCATIONS,0)
def edits():
    result=[]
    for before,after,kind in [('#include "MAA_gem5.hpp"','#include "dws_original_runtime.hpp"','api-include'),
        ('std::uint32_t data[2]','dws_cxx_array<std::uint32_t,2,0> data','ordinary-array-declarator'),
        ('std::int32_t limits[2]','dws_cxx_array<std::int32_t,2,1> limits','ordinary-array-declarator')]+[
        (typ+' *'+name,'dws_cxx_pointer<'+typ+'> '+name,'cacheable-pointer-declarator') for typ,name in
        [('std::uint32_t','index_data'),('std::uint32_t','source_data'),('std::uint32_t','result_data'),('std::int32_t','min_data'),('std::int32_t','max_data')]]+[
        ('volatile std::uint32_t *address_only','dws_cxx_address<std::uint32_t> address_only','noncacheable-address-declarator')]:
        at=SOURCE.index(before);result.append({'begin':at,'end':at+len(before),'before':before,'after':after,'kind':kind,'declaration_id':None if kind=='api-include' else 'synthetic-'+str(at)})
    return result
class Controls(unittest.TestCase):
    def test_actual_26_names_27_declarations_132_routes_render(self):
        self.assertEqual((len(INVENTORY),len({r['name'] for r in INVENTORY}),len(INSTANCES)),(27,26,132))
        self.assertEqual({r['formal_arity'] for r in INVENTORY if r['name']=='get_new_reg'},{0,1})
        for row in INSTANCES:self.assertIn(row['c_name']+'(',HEADER)
        self.assertIn('get_data_type_other',HEADER);self.assertIn('DataType',HEADER);self.assertIn('else {static_assert(!std::is_same_v<T,T>',HEADER)
    def test_fixed_thread_and_exact_fresh_source_inventory(self):
        for thread in (True,-1,2,'0'):
            with self.assertRaises(R['Refused']):R['render_header'](API,DISPATCH,PROJECT,DECLS,ABI,ALLOCATIONS,thread)
        changed=copy.deepcopy(DECLS);changed[0]['line']+=1
        with self.assertRaises(R['Refused']):R['render_header'](API,DISPATCH,PROJECT,changed,ABI,ALLOCATIONS,0)
    def test_nine_declarator_only_edits_preserve_original_function(self):
        changed=R['check_edits'](SOURCE,edits());self.assertEqual(changed.count('\n'),SOURCE.count('\n'));self.assertEqual(len(edits()),9)
        # Removing the allowed prefixes leaves exactly the same remaining text.
        old=SOURCE;new=changed
        for row in edits():old=old.replace(row['before'],'@'+row['kind']+'@',1);new=new.replace(row['after'],'@'+row['kind']+'@',1)
        self.assertEqual(new,old)
        for line in SOURCE.splitlines():
            if any(token in line for token in ('assert(','maa_','wait_ready(','return data[0]','get_new_','get_reg<')):self.assertIn(line,changed)
    def test_edit_mutation_overlap_source_range_kind_newline_refuse(self):
        for field,value in [('begin',-1),('end',1),('before','other'),('after','bad\ntext'),('kind','expression'),('declaration_id','x')]:
            changed=edits();changed[0][field]=value
            if field=='declaration_id':continue # generic edit shape binds declaration IDs at projection, not here.
            with self.subTest(field=field),self.assertRaises(R['Refused']):R['check_edits'](SOURCE,changed)
        with self.assertRaises(R['Refused']):R['check_edits'](SOURCE,edits()+[edits()[0]])
    def test_Cxx17_scalar_assignment_and_proxy_RHS_refusal(self):
        self.assertIn('operator=(T v)',HEADER);self.assertIn('operator=(const dws_cxx_reference&)=delete',HEADER)
        self.assertNotIn('static_cast<T>(other)',HEADER)
        self.assertNotIn('operator=(',HEADER[HEADER.index('struct dws_cxx_pointer'):HEADER.index('struct dws_cxx_address')])
        # The closed original fixture has only literal RHS at pointer stores.
        import re
        writes=re.findall(r'\b(?:index_data|source_data|min_data|max_data)\[[01]\]\s*=\s*([^;]+);',SOURCE)
        self.assertEqual(len(writes),8);self.assertTrue(all(re.fullmatch(r'[0-9]+',v) for v in writes))
    def test_only_explicit_array_list_initialization_and_original_values(self):
        self.assertIn('dws_cxx_array()=delete;',HEADER);self.assertIn('dws_cxx_array(std::initializer_list<T> values)',HEADER)
        self.assertIn('for(T item:values)',HEADER);self.assertIn('for(;i<N;++i)',HEADER)
        source=R['check_edits'](SOURCE,edits());self.assertIn('data = {1, 2};',source);self.assertIn('limits = {0, 1};',source)
        self.assertNotIn('dws_prepare_receiver_v1();',source);self.assertNotIn('dxm_reset(',HEADER)
    def test_pointer_copies_have_no_allocation_lifetime_and_use_rechecks(self):
        proxy=HEADER[HEADER.index('struct dws_cxx_pointer'):HEADER.index('struct dws_cxx_address')]
        self.assertNotIn('dws_cxx_enter(',proxy);self.assertNotIn('dws_cxx_leave(',proxy);self.assertNotIn('~dws_cxx_pointer',proxy)
        self.assertIn('dws_local_require_v1(p.object,dws_cxx_thread)',HEADER)
        self.assertIn('dws_pointer_offset(dws_cxx_live(value),n)',proxy)
        self.assertIn('~dws_cxx_array() {dws_cxx_leave(Object);}',HEADER)
        self.assertIn('case 0:dws_local_leave_0_v1();break;',HEADER);self.assertIn('case 1:dws_local_leave_1_v1();break;',HEADER)
    def test_source_and_every_component_exact_physical_pins(self):
        self.assertEqual(hashlib.sha256(SOURCE.encode()).hexdigest(),R['SOURCE_SHA'])
        for name in R['PINS']:R['component'](WHOLE,name)
        wrong=R['SOURCE_SHA'][:-1]+'0'
        with self.assertRaises(R['Refused']):R['file_pin'](WHOLE/'source_call_fixture_v2.cpp',wrong)
    def test_no_lowered_C_replacement_or_runtime_claim(self):
        source=(HERE/'runtime_projection_v2.py').read_text();tree=ast.parse(source)
        projection=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='projection')
        self.assertNotIn('checked[',ast.unparse(projection));self.assertIn('generated_lowered_C_body_used',source)
        self.assertNotIn('subprocess',source);self.assertNotIn('ctypes',source);self.assertEqual(EVENTS,[])
    def test_missing_inputs_and_missing_receiver_policy_refuse(self):
        with self.assertRaises(R['Refused']):R['projection'](WHOLE,PROJECT)
        receiver_api,_=R['component'](WHOLE,'receiver-state-draws-v2/receiver_state_draws_v2.py')
        with self.assertRaises((R['Refused'],receiver_api['Refused'])):R['recheck_receiver'](receiver_api,{'binding':{},'c_text':'','draw_plan':{},'integration':{}},{'path':'/nonexistent-projection-policy','bytes':0,'sha256':'0'*64})
    def test_receiver_policy_is_reprepared_and_all_outputs_compared(self):
        # Isolated protocol double only: production _projection obtains its
        # receiver API solely from the exact physically pinned component.
        class Pin:
            @classmethod
            def parse(cls,row):return row
        class Prepared:
            c_text='fixed';binding_json=b'{"x":1}';draw_plan_json=b'{"count":2}';integration_plan_json=b'{"one":true}'
        calls=[]
        api={'Pin':Pin,'OwnedSelection':lambda value:value,'prepare':lambda value:(calls.append(value) or Prepared()),'document':lambda value:{'policy':'fixed'}}
        receiver={'binding':{'x':1},'c_text':'fixed','draw_plan':{'count':2},'integration':{'one':True}}
        self.assertEqual(R['recheck_receiver'](api,receiver,{'pin':'selected'}),{'policy':'fixed'});self.assertEqual(calls,[{'pin':'selected'}])
        for name in receiver:
            changed=copy.deepcopy(receiver);changed[name]='tampered'
            with self.assertRaises(R['Refused']):R['recheck_receiver'](api,changed,{'pin':'selected'})
    def test_header_hashes_match_owned_API_and_enum_reread_is_pinned(self):
        self.assertEqual(R['HEADER_PINS'],API['HEADER_PINS'])
        for name,expected in R['HEADER_PINS'].items():
            raw,pin=R['file_pin'](PROJECT/'apps/dx100/benchmarks/API'/name,expected);self.assertEqual(pin['sha256'],expected)
        tree=ast.parse((HERE/'runtime_projection_v2.py').read_bytes());enum=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='enum_text')
        self.assertIn('file_pin(Path(project)',ast.unparse(enum));self.assertIn('expected)',ast.unparse(enum))
        source=(HERE/'runtime_projection_v2.py').read_text();self.assertIn('for pin in [*pins,*header_pins]',source);self.assertIn("'source_headers':header_pins",source)
    def test_exact_V1_source_inverse(self):
        delta=json.loads((HERE/'runtime-projection-v2-inverse.json').read_bytes());text=(HERE/'runtime_projection_v2.py').read_text()
        for edit in reversed(delta['edits']):self.assertEqual(text.count(edit['new']),1);text=text.replace(edit['new'],edit['old'],1)
        self.assertEqual(text,Path(delta['predecessor']['path']).read_text())
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS,
        'scope':'synthetic edit/string/header preparation; full projection/actual TU/compiler/native/public admission remain absent','projection_sha256':hashlib.sha256((HERE/'runtime_projection_v2.py').read_bytes()).hexdigest(),'header_sha256':hashlib.sha256(HEADER.encode()).hexdigest()}))
    sys.exit(not result.wasSuccessful())
