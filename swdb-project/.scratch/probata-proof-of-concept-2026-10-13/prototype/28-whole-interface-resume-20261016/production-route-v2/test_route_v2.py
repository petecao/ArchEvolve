"""No-child source controls of the V2 public adapter/native seams."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent
BASE=runpy.run_path(str(HERE/'test_route_seams_v1.py'),run_name='route_v1_controls')


def inert_import(selected):
    def imported(name, globals=None, locals=None, fromlist=(), level=0):
        key=(name,tuple(fromlist))
        if key in selected:return selected[key]
        raise AssertionError('unexpected project import: '+str(key))
    return imported


class RouteV2(BASE['RouteSeams']):
    def scanner(self):
        path=HERE.parents[4]/'swdb/acsl_subset.py'
        tree=ast.parse(path.read_text())
        nodes=[n for n in tree.body if isinstance(n,(ast.Assign,ast.ClassDef,ast.FunctionDef))]
        ns={'re':re,'dataclass':BASE['dataclass'],'field':BASE['field']}
        exec(compile(ast.Module(nodes,type_ignores=[]),str(path),'exec'),ns)
        return ns

    def test_wrong79_reaches_real_harness_predicate_without_model_draw_changes(self):
        scanner=self.scanner()
        ns=dict(self.new,acsl_subset=SimpleNamespace(**scanner))
        BASE['extracted'](HERE/'proposed/swdb/cbmc_translator.py',{'_tokens','_Expr','Context','expression','_cast'},ns)
        value=BASE['unit'](self.source)
        wrong=self.rows();wrong[0]=self.new['Clause']('ensures',r'\result == 79','wrong#value')
        library=SimpleNamespace(content_sha256=lambda name:'d'*64 if name=='unit.wrong' else 'a'*64)
        self.source['unit_contract'](library,value,'unit.wrong','d'*64,wrong)
        c79,p79=ns['harness'](self.interface(),wrong,sizes={},cap=0,whole_source=value)
        c80,p80=ns['harness'](self.interface(),self.rows(),sizes={},cap=0,whole_source=value)
        # harness's globals are the namespace in which its actual AST was defined.
        ns['harness'].__globals__['expression']=ns['expression']
        c79,p79=ns['harness'](self.interface(),wrong,sizes={},cap=0,whole_source=value)
        c80,p80=ns['harness'](self.interface(),self.rows(),sizes={},cap=0,whole_source=value)
        self.assertIn('79LL',c79);self.assertIn('80LL',c80)
        self.assertEqual(p79.draws,p80.draws);self.assertEqual(p79.capacity,p80.capacity)
        self.assertEqual(c79.replace('79LL','80LL').replace('wrong#value','first#value'),c80)
        self.assertNotIn('SWDB_ASSUME(',c79)
        self.assertEqual(value.model_text,BASE['unit'](self.source).model_text)
        self.assertEqual(value.draw_rows_json,BASE['unit'](self.source).draw_rows_json)
        ns['harness'].__globals__['expression']=lambda text,*args,**kwargs:'(swdb_result == 80)'

    def test_real_formal_entry_and_acsl_front_door_red_green(self):
        scanner=self.scanner();logic=scanner['LogicLibrary']({})
        self.assertTrue(scanner['check_formal_half'](r'assigns \everything;',[],logic))
        source_path=HERE/'proposed/swdb/dx100_checked_source.py'
        current={}
        policy={'unit_contracts':[{'id':'unit.first','sha256':'a'*64,'expected_result':80},
                                  {'id':'unit.wrong','sha256':'d'*64,'expected_result':79}]}
        source_ns=dict(self.source,select_baseline=lambda *_:object(),Inputs=lambda _:None,
            source_policy=lambda *_:(None,None,policy))
        BASE['extracted'](source_path,{'checked_unit_format','sole_whole_frame'},source_ns)
        module=SimpleNamespace(**source_ns)
        root=HERE.parents[4]
        frame=HERE/'proposed/swdb/formal_frame.py';tree=ast.parse(frame.read_text())
        ns={'re':re,'FRAME_VERSION':1,'acsl_subset':SimpleNamespace(**scanner),
            '__builtins__':dict(vars(__import__('builtins')),__import__=inert_import({('swdb',('dx100_checked_source',)):SimpleNamespace(dx100_checked_source=module)}))}
        BASE['extracted'](frame,{'_entry','_placement'},ns)
        library=SimpleNamespace(get=lambda ident:current.get(ident),content_sha256=lambda ident:'a'*64,
            _pin=lambda row:None)
        data={'kind':'library_operation','formal_frame':1,'version':'1.0',
            'proof_unit':{'function':self.source['FUNCTION'],'source':{'root':'library','path':'first.cpp','sha256':'f'*64}},
            'clauses':[{'id':'value','proof_placement':'per_candidate','acsl':{'text':r'ensures \result == 80;'}},
                       {'id':'frame','proof_placement':'per_candidate','acsl':{'text':r'assigns \everything;'}}]}
        current['unit.first']=data
        # Exact real constants avoid a duplicate formal-frame implementation.
        constants={'VERSION','FRAME_FIELDS','CLAUSE_FIELDS'}
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in constants for t in node.targets):
                exec(compile(ast.Module([node],type_ignores=[]),str(frame),'exec'),ns)
        errors=[];pending=[]
        ns['_entry'](library,'unit.first',data,lambda *row:errors.append(row),{},logic,set(),pending)
        self.assertEqual(errors,[]);self.assertEqual(len(pending),1)
        mutations=[lambda x:x['clauses'].append({'id':'extra','proof_placement':'per_candidate','acsl':{'text':'requires 1;'}}),
            lambda x:x['clauses'][1]['acsl'].update(text=r'assigns \nothing;'),
            lambda x:x['clauses'][1]['acsl'].update(text=r'assigns \everything, x;'),
            lambda x:x['clauses'][0]['acsl'].update(text=r'ensures \unknown;')]
        for mutate in mutations:
            altered=copy.deepcopy(data);mutate(altered);current['unit.first']=altered;errors=[]
            ns['_entry'](library,'unit.first',altered,lambda *row:errors.append(row),{},logic,set(),[])
            self.assertTrue(errors)
        current['unit.first']=data
        library.content_sha256=lambda ident:'b'*64;errors=[]
        ns['_entry'](library,'unit.first',data,lambda *row:errors.append(row),{},logic,set(),[])
        self.assertTrue(errors)

    def test_actual_source_root_red_green(self):
        project=HERE.parents[4]
        paths_file=project/'swdb/paths.py'
        assignment=next(n for n in ast.parse(paths_file.read_text()).body if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='HOME' for t in n.targets))
        default=assignment.value.args[0].args[1]
        actual_home=eval(compile(ast.Expression(default),str(paths_file),'eval'),{'Path':Path,'__file__':str(paths_file)})
        self.assertEqual(actual_home,project)
        self.assertTrue((actual_home/'apps/dx100/benchmarks/API/MAA.hpp').is_file())
        def select(file):
            selected={'root':'library','path':'first.cpp','sha256':'a'*64}
            ns={'Path':Path,'object':object,'dataclass':BASE['dataclass'],'FUNCTION':self.source['FUNCTION'],
                'METHOD':'method.dx100-whole-checked-source-v1','need':self.source['need'],
                'contracts':SimpleNamespace(checked=lambda d:d.get('contract_form')=='checked',policy=lambda *_:{'source_policy':{}}),
                'Inputs':lambda library:SimpleNamespace(document=lambda row:{'proof_source':selected}),
                '__builtins__':dict(vars(__import__('builtins')),__import__=inert_import({('swdb',('paths',)):SimpleNamespace(paths=SimpleNamespace(HOME=actual_home))}))}
            BASE['extracted'](file,{'SourceSelection','select_baseline'},ns)
            library=SimpleNamespace(entries={'new':{'kind':'proof_semantics','target':'dx100-mmio','sequence':2,'contract_form':'checked'}})
            return ns['select_baseline'](library,{'function':self.source['FUNCTION'],'source':selected})
        old=select(HERE.parent/'production-route-v1/proposed/swdb/dx100_checked_source.py')
        new=select(HERE/'proposed/swdb/dx100_checked_source.py')
        self.assertNotEqual(old.project,actual_home)
        self.assertEqual(new.project,actual_home)

    def test_actual_native_prelude_is_fatal_before_oracle(self):
        source_path=HERE/'proposed/swdb/dx100_checked_source.py'
        tree=ast.parse(source_path.read_text())
        fatal=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='WHOLE_NATIVE_FAILURE' for t in n.targets))
        ns=dict(self.source,WHOLE_NATIVE_FAILURE=fatal)
        BASE['extracted'](source_path,{'native_prelude'},ns)
        translator=HERE/'proposed/swdb/cbmc_translator.py'
        ast_translator=ast.parse(translator.read_text())
        prelude=next(ast.literal_eval(n.value) for n in ast_translator.body if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='PRELUDE' for t in n.targets))
        harness={'PRELUDE':prelude,'TOOL_ID':'fixed','TOOL_VERSION':'fixed','ORACLE_CAPACITY':'swdb.oracle_capacity',
            '__builtins__':dict(vars(__import__('builtins')),__import__=inert_import({('swdb',('dx100_checked_source',)):SimpleNamespace(dx100_checked_source=SimpleNamespace(**ns))}))}
        BASE['extracted'](translator,{'prelude'},harness)
        normal=harness['prelude']();checked=harness['prelude'](BASE['unit'](self.source))
        self.assertNotIn('swdb_whole_native_stop',normal)
        self.assertIn('fflush(stdout); _Exit(0);',checked)
        self.assertNotIn('longjmp',fatal)
        self.assertIn('#undef SWDB_CHECK',fatal)
        self.assertIn('#undef SWDB_ASSUME',fatal)
        self.assertLess(checked.index('swdb_whole_native_stop'),checked.index('static long long swdb_next(void)'))
        self.assertIn('"check"',fatal);self.assertIn('"infeasible"',fatal)

    def test_real_native_dispatch_uses_one_stub_child_per_line(self):
        calls=[]
        class Done:
            def __init__(self,code,out,error):self.returncode,self.stdout,self.stderr=code,out,error
        def controlled(argv,**kwargs):
            calls.append((argv,kwargs))
            return SimpleNamespace(returncode=0,stdout='run 0: result=80 end=done\n',stderr='')
        ns={'subprocess':SimpleNamespace(run=controlled),'os':os,'re':re,
            '__builtins__':dict(vars(__import__('builtins')),__import__=inert_import({('swdb.cbmc_adapter',('_Done',)):SimpleNamespace(_Done=Done)}))}
        BASE['extracted'](HERE/'proposed/swdb/dx100_checked_adapter.py',{'run_fresh_domain'},ns)
        result,crashed=ns['run_fresh_domain']('/pinned/binary',[[0,2**32-1],[1,2]])
        self.assertEqual(len(calls),2)
        self.assertEqual([call[1]['input'] for call in calls],['0 4294967295\n','1 2\n'])
        self.assertEqual(result.stdout.count('end=done'),2)
        self.assertIn('run 1:',result.stdout)
        self.assertEqual(crashed,set())
        for rc,out,err in ((1,'','trap'),(0,'run 0: end=done\nrun 1: end=done\n',''),(0,'run 0: end=done\n','runtime error: bad')):
            ns['subprocess']=SimpleNamespace(run=lambda *a,**k:SimpleNamespace(returncode=rc,stdout=out,stderr=err))
            refused,_=ns['run_fresh_domain']('/pinned/binary',[[0]])
            self.assertNotEqual(refused.returncode,0)

    def test_compiler_keeps_absolute_wrapper_command(self):
        calls=[]
        def controlled(argv,**kwargs):calls.append(argv);return SimpleNamespace(returncode=0)
        ns={'subprocess':SimpleNamespace(run=controlled)}
        BASE['extracted'](HERE/'proposed/swdb/dx100_checked_adapter.py',{'compile_native'},ns)
        tool={'clang':SimpleNamespace(command=('/pinned/custom-wrapper',))}
        for side in ('c','cxx'):self.assertIsNone(ns['compile_native'](tool,side,'source','binary',['-fsanitize=undefined']))
        self.assertTrue(all(row[0]=='/pinned/custom-wrapper' for row in calls))
        self.assertIn('c',calls[0]);self.assertIn('c++',calls[1])
        self.assertTrue(all('-fsanitize=undefined' in row for row in calls))

    def test_actual_retained_runtime_descriptor_shape(self):
        retained=HERE.parents[1]/'28-initialized-u32-resume-20261016/cold-v4-admission-04af74c1/retained-runtime-schema-20261016.json'
        # Both projects are siblings under prototype, not nested below WHOLE.
        retained=HERE.parent.parent/'28-initialized-u32-resume-20261016/cold-v4-admission-04af74c1/retained-runtime-schema-20261016.json'
        metadata=json.loads(retained.read_bytes())['files']['initialized-project-runtime-provenance.json']
        scalars=metadata['selected_scalars']
        runtime={name:scalars['runtime.'+name] for name in ('command','command_executable','driver')}
        self.assertNotIn('version',metadata['schema']['runtime'])
        wrapper={**runtime['command_executable'],'bytes':145}
        driver={**runtime['driver'],'bytes':1}
        policy={'producer_manifest':{'sha256':'a'*64},'receiver_selection':{}}
        unit=SimpleNamespace(policy_json=json.dumps(policy).encode(),selection=SimpleNamespace(library=None))
        receiver_policy={'physical_inputs':{'compiler_wrapper':wrapper,'compiler_driver':driver},
            'inputs':{'runtime_receipt':{'sha256':'b'*64}}}
        reads=SimpleNamespace(document=lambda row:receiver_policy,absolute=lambda *a,**k:None,recheck=lambda:None)
        namespace={'json':json,'MANIFEST_ID':'swdb-dx100-whole-checked-producers-1',
            'source':SimpleNamespace(METHOD='method.dx100-whole-checked-source-v1',need=self.source['need'],Inputs=lambda _:reads),
            '__builtins__':dict(vars(__import__('builtins')),__import__=inert_import({('swdb',('stdlib_provenance',)):SimpleNamespace(stdlib_provenance=SimpleNamespace(runtime_identity=lambda _:runtime))}))}
        BASE['extracted'](HERE/'proposed/swdb/dx100_checked_adapter.py',{'method_check'},namespace)
        method=SimpleNamespace(id='method.dx100-whole-checked-source-v1',data={'c_lowering':{'translators':[{'id':namespace['MANIFEST_ID'],'sha256':'a'*64}]}})
        adapter=SimpleNamespace(method=method);tools={'clang':SimpleNamespace(command=runtime['command'],version='22.1.8')}
        namespace['method_check'](adapter,unit,tools)
        for role in ('command_executable','driver'):
            old=runtime[role]
            runtime[role]={**old,'path':'/unadmitted/alias'}
            with self.assertRaises(self.source['Refused']):namespace['method_check'](adapter,unit,tools)
            runtime[role]=old
        tools['clang'].command=['clang++']
        with self.assertRaises(self.source['Refused']):namespace['method_check'](adapter,unit,tools)

    def test_all_three_wp_summary_guards_remain(self):
        tree=ast.parse((HERE/'proposed/swdb/proof_semantics.py').read_text())
        for name in ('acsl_source','wp_prelude','wp_locations'):
            node=next(n for n in tree.body if getattr(n,'name',None)==name)
            calls=[n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_require_summary_form']
            self.assertEqual(len(calls),1)

    def test_current_selection_unchanged_and_generic_checked_calls_refuse(self):
        new=ast.parse((HERE/'proposed/swdb/proof_semantics.py').read_text())
        old=ast.parse((HERE/'base-source/proof_semantics.py').read_text())
        get=lambda tree,name:next(n for n in tree.body if getattr(n,'name',None)==name)
        self.assertEqual(ast.dump(get(new,'current')),ast.dump(get(old,'current')))
        options=ast.unparse(get(new,'lowering_options'))
        self.assertIn('dx100_whole_checked.checked(data)',options)
        self.assertIn("'refused_calls'",options)

    def test_postchecks_exist_for_all_initialized_source_outcomes(self):
        tree=ast.parse((HERE/'proposed/swdb/dx100_checked_adapter.py').read_text())
        run=next(n for n in tree.body if getattr(n,'name',None)=='run')
        guarded=next(n for n in run.body if isinstance(n,ast.Try))
        final=ast.unparse(ast.Module(guarded.finalbody,type_ignores=[]))
        self.assertIn('source.recheck',final)
        self.assertIn('check_launch',final)
        self.assertIn('whole_source_post_input_refusal',final)

    def test_final_input_gate_regenerates_not_metadata_accepts(self):
        tree=ast.parse((HERE/'proposed/swdb/dx100_checked_adapter.py').read_text())
        node=next(n for n in tree.body if getattr(n,'name',None)=='check_launch')
        text=ast.unparse(node)
        for required in ('source.recheck(unit)','method_check(adapter, unit','native.view(unit)',
                         'native.check_generated_header','adapter._build','Path(path).read_bytes()'):
            self.assertIn(required,text)
        self.assertNotIn("get('accepted')",text)


if __name__=='__main__':unittest.main(verbosity=2)
