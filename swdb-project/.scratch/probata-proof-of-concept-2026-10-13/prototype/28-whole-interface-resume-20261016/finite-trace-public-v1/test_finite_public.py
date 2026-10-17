"""2026-10-16 ET. No-child source controls; no actual swdb imports or C execution."""
import ast
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import re
import tempfile
import builtins
import datetime
from zoneinfo import ZoneInfo
from types import SimpleNamespace
from dataclasses import dataclass,field
import unittest

HERE=Path(__file__).resolve().parent
PACKAGE=HERE/'proposed/swdb/_dx100_finite'
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module

def audit(event,args):
    if event in ('subprocess.Popen','os.system','os.exec','os.posix_spawn','ctypes.dlopen') or event.startswith('socket.'):
        raise AssertionError('no child/native/network control: '+event)
sys.addaudithook(audit)
E=load('_finite_closed_events',PACKAGE/'event_plan_v2.py')
C=load('_finite_closed_corpus',HERE/'corpus_public_v1.py')
K=load('_finite_closed_checks',PACKAGE/'finite_checks_v1.py')

def extract(path,names,ns):
    tree=ast.parse(path.read_bytes())
    found=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert {n.name for n in found}==set(names)
    exec(compile(ast.Module(found,type_ignores=[]),str(path),'exec'),ns)
    return ns

def result_rows(extra=()):
    rows=[dict(property='dwe_finite_trace.assertion.1',description=K.REACH,status='FAILURE',sourceLocation=dict(function=K.FUNCTION)),
          dict(property='swdb_run.assertion.1',description=K.NORMAL,status='SUCCESS',sourceLocation=dict(function='swdb_run')),
          dict(property='dxm_cpu_write.assertion.1',description='node-capacity',status='SUCCESS',sourceLocation=dict(function='dxm_cpu_write'))]
    return rows+list(extra)

def witness(value='0'):
    return [dict(stepType='assignment',lhs='goto_symex$$return_value$$swdb_next',value=dict(data=value))]

class Controls(unittest.TestCase):
    def test_complete_literal_corpus_and_old_digest_identity(self):
        rows=C.cases();self.assertEqual(len(rows),30)
        old=json.loads((HERE/'closed-plan-digests.json').read_bytes())
        for row in rows:
            text,profile,anchors=E.render(row['plan'],row['context'])
            self.assertIn('return UINT64_C(0)',text)
            self.assertEqual(len(anchors),len(row['plan']['events']))
            nodes=profile['nodes_required'];self.assertGreater(profile['node_limit'],nodes)
            self.assertEqual(profile['node_limit']&(profile['node_limit']-1),0)
            if row['plan']['id'] in old:
                self.assertEqual(hashlib.sha256(E.canonical(row['plan'])+b'\n').hexdigest(),old[row['plan']['id']])
    def test_query_grammar_and_independent_draw_budget(self):
        row=next(x for x in C.cases() if x['plan']['id']=='ready_relation_positive')
        text,profile,_=E.render(row['plan'],row['context'])
        self.assertEqual(profile['logical_query_count'],1);self.assertEqual(profile['draw_count'],2)
        self.assertIn('dxc_get_tile_ready(0u)',text);self.assertNotIn('get_tile_ready(',text.replace('dxc_get_tile_ready(',''))
        bad=copy.deepcopy(row['plan']);bad['schema']='owned-finite-dx100-event-plan-1'
        with self.assertRaises(E.Refused):E.render(bad,row['context'])
        bad=copy.deepcopy(row['plan']);bad['events'][5]=dict(kind='tile_read',thread=0,tile='t0',lane=0,out='ready')
        with self.assertRaisesRegex(E.Refused,'preceding logical query'):E.render(bad,row['context'])
    def test_source_capacity_is_not_4096_default(self):
        row=C.cases()[0];_,profile,_=E.render(row['plan'],row['context'])
        self.assertEqual(profile['nodes_required'],129);self.assertEqual(profile['node_limit'],256)
    def test_no_hidden_grant_wait_or_assume(self):
        for row in C.cases():
            text,_,_=E.render(row['plan'],row['context'])
            self.assertNotIn('SWDB_ASSUME',text);self.assertNotIn('dxm_claim',text);self.assertNotIn('dxm_reset',text)
            self.assertEqual(text.count('dwi_wait_ready('),sum(x['kind']=='wait_tile' for x in row['plan']['events']))

    def test_complete_result_reader_and_reachability(self):
        result=SimpleNamespace(exit_code=10,out_of_memory=False,timed_out=False)
        def read(rows):return K.read_outcome(result,json.dumps([dict(result=rows)]),1,('dwe_trace_program','dxm_cover','dxm_cpu_write','dxm_device_write'))
        self.assertEqual(read(result_rows())['verdict'],'proven')
        failed=dict(property='dwe_trace_program.assertion.2',description='finite-event-property',status='FAILURE',sourceLocation=dict(function='dwe_trace_program'),trace=witness())
        self.assertEqual(read(result_rows([failed]))['verdict'],'failed')
        for field,value in [('status','UNKNOWN'),('property','swdb_run.assertion.1')]:
            bad=copy.deepcopy(failed);bad[field]=value
            with self.assertRaises(K.Refused):read(result_rows([bad]))
        for change in ('absent_entry','held_entry','wrong_entry_owner','absent_normal','no_model'):
            rows=result_rows()
            if change=='absent_entry':rows.pop(0)
            elif change=='held_entry':rows[0]['status']='SUCCESS'
            elif change=='wrong_entry_owner':rows[0]['sourceLocation']['function']='unrelated'
            elif change=='absent_normal':rows.pop(1)
            else:rows.pop()
            with self.assertRaises(K.Refused):read(rows)
        rows=result_rows([failed]);rows[2]['status']='FAILURE'
        self.assertEqual(read(rows)['failure_class'],'ghost_capacity')
        rows=result_rows([dict(failed,description='finite-owned-quiescence')])
        self.assertEqual(read(rows)['failure_class'],'unsupported_construct')
        rows=result_rows([dict(failed,property='dxm_cover.unwind.0')])
        self.assertEqual(read(rows)['failure_class'],'unwinding_bound_too_small')
        result.timed_out=True;self.assertEqual(read(result_rows())['failure_class'],'timeout')

    def test_oracle_and_native_protocol_refuse_partial_or_invented_values(self):
        self.assertEqual(K.oracle(witness('4294967295'),1),[4294967295])
        for raw in ('','0junk','1.0','true',str(2**63)):
            with self.assertRaises(K.Refused):K.oracle(witness(raw),1)
        with self.assertRaises(K.Refused):K.oracle(witness(),2)
        exact='run 0: input finite_choice_0=7 reach='+K.REACH+' fail=finite-event-property end=check\n'
        self.assertEqual(K.native_row(exact,1)['failed'],['finite-event-property'])
        for raw in (exact.replace('finite_choice_0','finite_choice_1'),exact.replace('reach=','extra=reach='),exact.replace('finite-event-property','node-capacity'),exact+'extra\n',exact.replace(' end=check',' end=infeasible')):
            with self.assertRaises(K.Refused):K.native_row(raw,1)

    def test_exact_actual_loop_selector_closure(self):
        profile=dict(node_limit=256,nodes_required=129)
        rows=K.loop_bounds(profile,['dxm_cover.7','dxm_cpu_write.8','dxm_device_write.9','dwe_trace_program.0'],['dxm_cover','dxm_cpu_write','dxm_device_write','dwe_trace_program'])
        self.assertEqual([row['unwind'] for row in rows],[5121,257,257,513])
        for loops in ([],['dxm_cover.7'],['dxm_cover.7','dxm_cpu_write.8','dxm_device_write.9','unknown.0']):
            with self.assertRaises(K.Refused):K.loop_bounds(profile,loops,['dxm_cover','dxm_cpu_write','dxm_device_write'])
        with self.assertRaises(K.Refused):K.loop_bounds(dict(node_limit=128,nodes_required=129),[x['loop'] for x in rows],['dxm_cover','dxm_cpu_write','dxm_device_write','dwe_trace_program'])

    def test_real_plan_and_checked_native_macro_insertion(self):
        trfile=HERE.parent/'production-route-v4/proposed/swdb/cbmc_translator.py'
        tree=ast.parse(trfile.read_bytes());ns=dict(dataclass=dataclass,field=field)
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'PRELUDE','TOOL_ID','TOOL_VERSION','ORACLE_CAPACITY'} for t in node.targets):exec(compile(ast.Module([node],type_ignores=[]),str(trfile),'exec'),ns)
        extract(trfile,{'Plan'},ns)
        # The unchanged PRELUDE is the actual selected renderer; finite override precedes next().
        prelude=ns['PRELUDE'];tr=SimpleNamespace(Plan=ns['Plan'],prelude=lambda:prelude)
        source=SimpleNamespace(need=E.need,strict=json.loads)
        adapter=dict(tr=tr,source=source,checks=K)
        extract(HERE/'proposed/swdb/dx100_finite_trace_adapter.py',{'plan','texts'},adapter)
        unit=SimpleNamespace(draw_rows_json=json.dumps([dict(name='finite_choice_0',role='finite-model-choice',ctype='uint32_t',c_lvalue='dws_choice_table[0]')]),profile_json=b'{}',model_text='/* exact model */',source_text='/* source wrapper */')
        self.assertEqual(adapter['plan'](unit).inputs,1)
        unit.profile_json=b'{"draw_count":1}';text=adapter['texts'](unit)
        self.assertLess(text.index('static void dwe_fatal'),text.index('static long long swdb_next(void) {\n  SWDB_CHECK'))
        self.assertIn('_Exit(0)',text);self.assertNotIn('longjmp',K.native_override())
        self.assertIn('swdb_oracle_next==1',text)

    def test_typed_discriminator_preserves_source_fallback_and_refuses_confusion(self):
        ns=dict(need=E.need,FUNCTION=K.FUNCTION)
        extract(HERE/'proposed/swdb/dx100_finite_trace.py',{'select_baseline','checked_unit_format'},ns)
        for data in (None,{},dict(proof_unit='malformed normal source metadata'),dict(proof_unit=dict(function='ordinary_cpp'))):
            self.assertIsNone(ns['checked_unit_format'](None,'contract.x',data))
        for data in (dict(finite_trace_selection={},proof_unit=dict(function='ordinary_cpp')),dict(finite_trace_selection={},proof_unit=dict(function=K.FUNCTION,source={},unexpected=True))):
            errors=ns['checked_unit_format'](None,'contract.x',data)
            self.assertIsInstance(errors,list);self.assertTrue(errors)

    def test_public_record_gate_requires_execution_goals_samples_and_replay(self):
        row=dict(case_id='owned_tile_positive',contract=dict(id='contract.finite',sha256='1'*64),conditional_predicted_verdict='proven')
        assumption=dict(kind='proof_semantics',reference=dict(id='semantics.finite#one_instance',sha256='2'*64),sentence='One instance.')
        profile=dict(entry=dict(sha256='2'*64),record_assumptions=[assumption])
        goals=[dict(goal=x['property'],property=x['description'],function=x['sourceLocation']['function'],status=x['status'].lower()) for x in result_rows()]
        record=dict(kind='proof',evidence_kind='execution',verdict='proven',bounds={'threads':1},pins=dict(contract=row['contract'],proof_semantics=dict(sha256='2'*64)),
            assumptions=[assumption],goals=goals,settings=dict(verifier_launched=True,finite_trace=dict(kind='dx100-whole-interface-finite-trace-1',case_id=row['case_id']),
            forms=dict(finite_concrete_model='proven'),finite_native_samples=[dict(output_sha256='3'*64,failed=[],end='done') for _ in range(4)],finite_actual_loop_bounds=[dict(loop='dxm_cover.0',unwind=5121)]))
        self.assertEqual(K.public_record(record,row,profile)['skip_count'],0)
        for mutation in ('fixture','skip','assumption','goals','samples','launch'):
            bad=copy.deepcopy(record)
            if mutation=='fixture':bad['evidence_kind']='contract_fixture'
            elif mutation=='skip':bad['skip_reason']='missing_tool'
            elif mutation=='assumption':bad['assumptions']=[]
            elif mutation=='goals':bad['goals'][2]['status']='unknown'
            elif mutation=='samples':bad['settings']['finite_native_samples']=[]
            else:bad['settings']['verifier_launched']=False
            with self.assertRaises(K.Refused):K.public_record(bad,row,profile)
        row=dict(row,conditional_predicted_verdict='refuted');record['verdict']='refuted';record['settings']['forms']['finite_concrete_model']='refuted'
        record['goals'].append(dict(goal='dwe_trace_program.assertion.9',property='finite-event-property',function='dwe_trace_program',status='failure'))
        record['counterexample']=dict(property='finite-event-property',replay=dict(form='finite_concrete_model_c',replayed=True,failed=['finite-event-property'],end='check',original_cpp_equivalence=False))
        K.public_record(record,row,profile)
        record['counterexample']['replay']['replayed']=False
        with self.assertRaises(K.Refused):K.public_record(record,row,profile)

    def test_hook_exact_inverse_and_ast_parse(self):
        rows=json.loads((HERE/'hook-inverse.json').read_bytes())['files']
        for name,row in rows.items():
            path=HERE/'proposed/swdb'/name;raw=path.read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),row['proposed_sha256']);ast.parse(raw)
            text=raw.decode()
            for edit in reversed(row['edits']):self.assertEqual(text.count(edit['after']),1);text=text.replace(edit['after'],edit['before'])
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),row['base_sha256'])
        for path in (HERE/'proposed').rglob('*.py'):ast.parse(path.read_bytes())

    def test_thirty_exact_owned_compositions_are_source_only(self):
        bridge=load('_finite_owned_complete_source',PACKAGE/'finite_owned_receiver_v4.py')
        def pin(path):
            raw=path.read_bytes();return dict(path=str(path.resolve()),bytes=len(raw),sha256=E.digest(raw))
        def save(path,value,raw=False):
            path.write_bytes(value if raw else E.canonical(value)+b'\n');return pin(path)
        with tempfile.TemporaryDirectory(dir=HERE,prefix='owned30-') as temporary:
            root=Path(temporary).resolve();entry_id='semantics.source_control_0_2';owner='Synthetic test premise owner'
            entry=save(root/'entry.json',dict(id=entry_id,version='0.2',kind='proof_semantics',target='dx100-mmio',contract_form=bridge.MODEL_KIND,
                rules=bridge.rule_rows(owner),public_authority=False))
            identity=dict(id=entry_id,sha256=entry['sha256'])
            for literal in C.cases():
                directory=root/literal['plan']['id'];directory.mkdir();plan=save(directory/'plan.json',literal['plan'])
                context=dict(literal['context'],source_plan_sha256=plan['sha256'],entry_identity=identity,
                    owned_premises=[dict(role=role,owner=identity,rule='finite_context_'+role.replace('-','_')) for role in E.PREMISES])
                context_pin=save(directory/'context.json',context)
                receiver=save(directory/'receiver.json',dict(schema='owned-finite-model-receiver-1',source_plan_sha256=plan['sha256'],context_sha256=context_pin['sha256'],
                    entry_identity=identity,owned_premises_sha256=E.digest(E.canonical(context['owned_premises']))))
                policy=dict(schema='finite-trace-source-policy-1',source_plan=plan,context=context_pin,receiver=receiver,entry=entry,entry_id=entry_id,
                    headers={name:pin(HERE.parent/name) for name,_ in E.HEADERS},hook_producer=pin(PACKAGE/'whole_model_v3.py'),producer=pin(PACKAGE/'event_plan_v2.py'))
                source_policy=save(directory/'source-policy.json',policy);trace=E.prepare(E.OwnedSelection(E.Pin.parse(source_policy)))
                artifacts={name:save(directory/(name+'.txt'),raw,True) for name,raw in dict(c_text=trace.c_text.encode(),certificate=trace.certificate_json,
                    draws=trace.draw_plan_json,profile=trace.resource_profile_json,anchors=trace.anchors_json).items()}
                prepared=dict(policy=source_policy,**artifacts);profile=json.loads(trace.resource_profile_json);draws=json.loads(trace.draw_plan_json)
                facts=bridge.facts_for(literal['plan'],context,profile,draws,entry_id)
                owned=save(directory/'owned.json',bridge.owned_selection_metadata(policy,prepared,identity,facts,owner))
                composition=dict(schema='finite-owned-receiver-selection-2',composer=pin(PACKAGE/'finite_owned_receiver_v4.py'),producer=pin(PACKAGE/'event_plan_v2.py'),
                    receiver_basis=pin(PACKAGE/'receiver_state_draws_basis_v2.py'),prepared=prepared,entry_id=entry_id,premise_owner=owner,owned_selection=owned)
                selected=save(directory/'composition.json',composition);out=bridge.prepare(bridge.OwnedSelection(bridge.Pin.parse(selected)))
                self.assertTrue(out.c_text.startswith(trace.c_text));self.assertIn('dws_choice_table[i]=(uint32_t)swdb_next()',out.receiver_c_text)
                self.assertEqual(json.loads(out.certificate_json)['owned_facts_sha256'],E.digest(E.canonical(facts)))
                self.assertFalse(json.loads(out.certificate_json)['actual_compiler_solver_public_admission'])
                if literal['plan']['id']=='history_latest_positive':
                    altered=json.loads(Path(owned['path']).read_bytes());altered['source_plan']['bytes']=float(altered['source_plan']['bytes'])
                    Path(owned['path']).write_bytes(E.canonical(altered)+b'\n');composition['owned_selection']=pin(Path(owned['path']))
                    bad=save(directory/'wrong-owned.json',composition)
                    with self.assertRaisesRegex(bridge.Refused,'exact externally owned'):bridge.prepare(bridge.OwnedSelection(bridge.Pin.parse(bad)))

    def test_normal_entry_rule_assumptions_do_not_cap_real_level_or_render(self):
        bridge=load('_finite_owned_rule_source',PACKAGE/'finite_owned_receiver_v4.py')
        core=dict(json=json,hashlib=hashlib,re=re,Refused=E.Refused,need=E.need)
        tree=ast.parse((HERE/'proposed/swdb/dx100_finite_trace.py').read_bytes())
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'LOGICAL_RULE','LOGICAL_STATEMENT'} for t in node.targets):exec(compile(ast.Module([node],type_ignores=[]),'actual_finite_constants','exec'),core)
        extract(HERE/'proposed/swdb/dx100_finite_trace.py',{'logical_rule'},core)
        validator=ast.parse((HERE.parent/'production-route-v4/proposed/swdb/dx100_whole_checked.py').read_bytes())
        required={}
        for node in validator.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'TRUST','OWNED'} for t in node.targets):required.update(ast.literal_eval(node.value))
        base=[dict(id=ident,statement=statement,assumed=dict(owner='Eric' if ident in {'mmio_ordering','cross_core_filter','cross_core_write_buffer','no_stale_cpu_copy','one_instance'} else 'Selected compiler owner'),record_assumption=True) for ident,statement in required.items()]
        data=dict(id='semantics.finite_selected',version='0.2',rules=base+bridge.rule_rows('Selected context owner')+[core['logical_rule']('Selected context owner')])
        class Failure(ValueError):pass
        def imported(name,globals=None,locals=None,fromlist=(),level=0):
            if name=='swdb.proof':return SimpleNamespace(AdapterError=Failure)
            raise AssertionError('no project imports in source control: '+name)
        producer=HERE/'proposed/swdb/proof_semantics.py'
        record=dict(artifacts=SimpleNamespace(file_hash=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()),yamlio=SimpleNamespace(load=lambda p:json.loads(Path(p).read_bytes())),
            yaml=SimpleNamespace(YAMLError=ValueError),__builtins__=dict(vars(builtins),__import__=imported))
        extract(producer,{'record_assumptions'},record)
        with tempfile.TemporaryDirectory(dir=HERE,prefix='normal-level-') as temporary:
            path=Path(temporary)/'entry.json';path.write_text(json.dumps(data));digest=hashlib.sha256(path.read_bytes()).hexdigest()
            library=SimpleNamespace(get=lambda _:data,files={data['id']:path})
            assumptions=record['record_assumptions'](library,data['id'],digest)
            self.assertEqual(len(assumptions),14)
            self.assertTrue(all(row['reference']['id'].startswith(data['id']+'#') and row['reference']['sha256']==digest and row['kind']=='proof_semantics' for row in assumptions))
            level_file=HERE.parents[4]/'swdb/level_rule.py';level_tree=ast.parse(level_file.read_bytes());ns=dict(datetime=datetime,ZoneInfo=ZoneInfo)
            for node in level_tree.body:
                if isinstance(node,ast.Assign):exec(compile(ast.Module([node],type_ignores=[]),str(level_file),'exec'),ns)
            extract(level_file,{'rank','bounds_level','smallest','is_baseline_measurement','snapshot'},ns)
            cls=next(n for n in level_tree.body if isinstance(n,ast.ClassDef) and n.name=='Rule')
            selected=[n for n in cls.body if getattr(n,'name',None) in {'level','_assumptions','_checked_method_part','_refuted'}]
            projected=ast.ClassDef(name='Rule',bases=[],keywords=[],body=selected,decorator_list=[])
            exec(compile(ast.fix_missing_locations(ast.Module([projected],type_ignores=[])),str(level_file),'exec'),ns)
            rule=ns['Rule']();rule.library=library
            rule.proofs={'proof.finite':dict(id='proof.finite',subject=dict(kind='candidate_proof_unit',candidate='candidate.finite'),pins=dict(contract=dict(id='unit.finite')),route='cbmc',verdict='proven',assumptions=assumptions)}
            rule.status=lambda _:dict(counts=True,bounds={'threads':1},caps=[],uses=[],stale=[],below_minimum=[])
            result=rule.level('candidate.finite','certified',{'unit.finite'})
            self.assertEqual(result['level'],'proven_within_bounds_threads_1');self.assertEqual(len(result['assumptions']),14)
            rule.candidate=lambda _:result
            handoff_file=HERE.parents[4]/'swdb/handoff_level.py';h=dict(re=re,Failure=Failure)
            for node in ast.parse(handoff_file.read_bytes()).body:
                if isinstance(node,ast.Assign):exec(compile(ast.Module([node],type_ignores=[]),str(handoff_file),'exec'),h)
            def imports(name,globals=None,locals=None,fromlist=(),level=0):
                if name=='swdb':return SimpleNamespace(level_rule=SimpleNamespace(Rule=lambda _:rule,WORDS=ns['WORDS'],snapshot=ns['snapshot']))
                raise AssertionError('no project import: '+name)
            h['__builtins__']=dict(vars(builtins),__import__=imports)
            extract(handoff_file,{'render','block','check','_keys','_bounds','_assumptions','_sentence'},h)
            store=SimpleNamespace(get=lambda ident,kind:rule.proofs.get(ident) if kind=='proof' else {'id':ident})
            rendered=h['render'](store,'candidate.finite',now=datetime.datetime(2026,10,16,12,tzinfo=ZoneInfo('America/New_York')))
            self.assertEqual(rendered['level'],'proven_within_bounds_threads_1');self.assertEqual(len(rendered['assumptions']),14)
            self.assertTrue(rendered['text'].endswith('Says nothing about speed.'))
            bad=[dict(row,kind='assumed_clause') for row in assumptions]
            with self.assertRaises(Failure):h['_assumptions'](bad,library)

if __name__=='__main__':unittest.main(verbosity=2)
