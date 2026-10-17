"""2026-10-16 ET. Synthetic memory projection protocol, never actual preparation.

The real root selector, receiver allocation checker and projection guards run.
Upstream compiler binding/body/receiver preparation are explicit inert protocol
doubles. No complete observed TU, owned context or scientific result is claimed.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import runpy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;PROJECT=WHOLE.parents[3]
V3=WHOLE/'runtime-projection-v3';SOURCE_PATH=WHOLE/'source-memory-fixtures-v1/same_thread_memory_v1.cpp'


def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        raise AssertionError('child/native/network event forbidden')
    if event=='import' and str(args[0]).split('.')[0]=='swdb':
        raise AssertionError('project import forbidden')


sys.addaudithook(no_child)
R=runpy.run_path(str(HERE/'runtime_projection_v4.py'))
S=runpy.run_path(str(WHOLE/'source-memory-selection-v1/source_memory_selection_v1.py'))
RECEIVER=runpy.run_path(str(WHOLE/'receiver-memory-v1/receiver_memory_v1.py'))
CONTROL=runpy.run_path(str(WHOLE/'source-memory-selection-v1/test_source_memory_selection_v1.py'))
SOURCE=SOURCE_PATH.read_text()


def span(begin,end):
    return {'begin':{'offset':begin},'end':{'offset':end-1,'tokLen':1}}


def pin(path,raw):
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def protocol(function):
    api,base=CONTROL['fixture'](function)
    base['declarations'][2]['name']='get_cacheable_tile_pointer'
    tu,preparation=base['normalized_tu'],base['preparation']
    source_calls=preparation['calls']
    for number,owner in enumerate(tu['inner']):
        begin,end=api['_span'](owner);body=owner['inner'][0]
        body['range']=span(SOURCE.index('{',begin),end)
        array=body['inner'][0];start=SOURCE.index('std::uint32_t data[16]',begin)
        stop=SOURCE.index(';',start)+1
        array.update(type={'qualType':'std::uint32_t[16]'},range=span(start,stop))
        if owner['name'].endswith('during_store'):continue
        start=SOURCE.index('std::uint32_t *index_data',begin);stop=SOURCE.index(';',start)+1
        call_start=SOURCE.index('get_cacheable_tile_pointer',start);call_stop=SOURCE.index(')',call_start)+1
        call={'kind':'CallExpr','range':span(call_start,call_stop),'inner':[]}
        pointer={'kind':'VarDecl','id':'0x'+str(300+number),'name':'index_data',
            'loc':{'_file':str(SOURCE_PATH)},'type':{'qualType':'std::uint32_t *'},
            'range':span(start,stop),'inner':[call]}
        body['inner'].append(pointer)
        source_calls.append({'name':'get_cacheable_tile_pointer','caller_mangled':owner['mangledName'],
            'call_range':[call_start,call_stop],'dtype':0})
    profile=S['profile'](function);caller=profile['caller_mangled']
    owner=next(node for node in tu['inner'] if node['name']==function)
    array=owner['inner'][0]['inner'][0]
    allocation={'object_index':0,'object_id':'selected_data','caller':caller,'local_id':array['id'],
        'declaration_sha256':R['digest'](array),'declaration_range':api['_span'](array),
        'scope_end_offset':api['_span'](owner['inner'][0])[1],'allocation_thread':0,
        'allocation_origin':'checked-original-automatic-declaration'}
    object_pin=R['digest']({'source_sha256':R['MEMORY_SOURCE_SHA'],'caller':caller,'local_id':array['id'],
        'declaration_sha256':R['digest'](array)})
    atlas={'schema':'source-ordinary-cell-atlas-1','objects':[{'object_id':'selected_data','source_pin':object_pin,
        'guest_base':4096,'physical_base':4096,'extent':16,'dtype':0,'base_cell':0,'cell_ids':list(range(16))}],
        'cells':[{'cell':i,'physical_begin':4096+i*4,'physical_end':4100+i*4,'dtype':0} for i in range(16)],
        'mmio_excluded_span':[17179869184,17179869184+8*32*16384+4*32+4*32+24],
        'initialization_granted':False,'history_events_added':0,'public_admission':False,
        'owned_premises':['source object identity/lifetime','guest→physical projection','complete CPU-access instrumentation']}
    preparation.update(normalized_full_tu_sha256=R['digest'](tu),compiler_capture_receipt_sha256='c'*64,
                       abi_observation={'abi':base['abi']})
    statements={'schema':'synthetic-statement-protocol-only','assertions':[],'synthetic_selected_body':function}
    documents={}
    def docpin(name,value):
        raw=R['canonical'](value);row=pin(Path('/synthetic-only')/name,raw)
        documents[row['path']]=copy.deepcopy(value)
        return row
    inputs={'source':pin(SOURCE_PATH,SOURCE.encode()),'assertion_header':{'path':'/synthetic-only/assert.h','bytes':1,'sha256':'a'*64},
        'capture_receipt':{'path':'/synthetic-only/capture.json','bytes':1,'sha256':'c'*64},
        'source_atlas':docpin('atlas.json',atlas),'statement_preparation':docpin('statements.json',statements),
        'abi_observation':docpin('abi.json',preparation['abi_observation'])}
    policy={'schema':'synthetic-receiver-protocol-only','full_tu_canonical_sha256':R['digest'](tu),'inputs':inputs}
    policy_pin=docpin('policy.json',policy)
    draw={'count':256,'scope':'synthetic protocol only'}
    integration={'allocation_hooks':[allocation]}
    binding={'input_pins':inputs,'receiver_c_sha256':R['sha'](b'fixed-receiver-protocol-only'),
        'harness_draw_plan_sha256':R['digest'](draw),'integration_plan_sha256':R['digest'](integration)}
    receiver={'binding':binding,'c_text':'fixed-receiver-protocol-only','draw_plan':draw,'integration':integration}
    events=[]
    expected_receiver=copy.deepcopy(receiver);expected_statements=copy.deepcopy(statements)
    def prepare(selected):
        events.append('receiver-prepare')
        if selected.policy.row()!=policy_pin:raise AssertionError('wrong receiver protocol selection')
        return SimpleNamespace(c_text=expected_receiver['c_text'],binding_json=R['canonical'](expected_receiver['binding']),
            draw_plan_json=R['canonical'](expected_receiver['draw_plan']),integration_plan_json=R['canonical'](expected_receiver['integration']))
    receiver_api={**RECEIVER,'prepare':prepare,'document':lambda selected:copy.deepcopy(documents[selected.path])}
    api.update(HEADER_PINS=R['HEADER_PINS'],inventory=lambda _project:base['declarations'])
    class Stager:
        def __init__(self,_api,_dispatch,_tu,**kwargs):
            events.append('selected-body-stage')
            if _tu is not tu or kwargs['source_text']!=SOURCE or kwargs['caller']!=caller or kwargs['live_local_ids']!=set():
                raise AssertionError('original complete source/TU selection differs')
    class Lowerer:
        def __init__(self,*args,**kwargs):events.append('selected-body-check')
        def lower(self):return copy.deepcopy(expected_statements)
    modules={'whole_interface_v4.py':api,'source_dispatch_v3.py':{},'source_argument_staging_v2.py':{'Stager':Stager},
        'source_statements_v2.py':{'Lowerer':Lowerer},'source-memory-selection-v1/source_memory_selection_v1.py':S,
        'receiver-memory-v1/receiver_memory_v1.py':receiver_api}
    def component(_whole,name):
        path=WHOLE/name
        return modules[name],R['file_pin'](path,R['MEMORY_PINS'][name])[1]
    def header(*args):
        events.append('header-render')
        return 'fixed-runtime-header-protocol-only',base['declarations'],[{'synthetic_route':i} for i in range(132)]
    kwargs={'source_path':SOURCE_PATH,'normalized_tu':tu,'function':function,'caller':caller,'declarations':base['declarations'],
        'abi':base['abi'],'atlas':atlas,'allocations':[allocation],'thread':0,'unit_preparation':preparation,
        'statement_preparation':statements,'assertion_header_pin':inputs['assertion_header'],
        'receiver':receiver,'receiver_policy_pin':policy_pin}
    namespace=R['_memory_projection'].__globals__
    return kwargs,events,namespace,component,header


def project(function,mutate=None):
    kwargs,events,namespace,component,header=protocol(function)
    if mutate:mutate(kwargs)
    with patch.dict(namespace,{'memory_component':component,'render_header':header}):
        result=R['memory_projection'](WHOLE,PROJECT,**kwargs)
    return result,events,kwargs


class MemoryControls(unittest.TestCase):
    def test_entire_v3_prefix_and_all_functions_unchanged(self):
        before=(V3/'runtime_projection_v3.py').read_bytes();after=(HERE/'runtime_projection_v4.py').read_bytes()
        self.assertTrue(after.startswith(before))
        old=ast.parse(before);new=ast.parse(after)
        functions={node.name:node for node in new.body if isinstance(node,ast.FunctionDef)}
        for node in old.body:
            if isinstance(node,ast.FunctionDef):
                self.assertEqual(ast.dump(node,include_attributes=False),ast.dump(functions[node.name],include_attributes=False))
        self.assertEqual(R['SOURCE_SHA'],'3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd')

    def test_fixed_components_physical_hashes_and_no_external_loader(self):
        self.assertEqual(len(R['MEMORY_PINS']),6)
        for name,expected in R['MEMORY_PINS'].items():
            self.assertEqual(hashlib.sha256((WHOLE/name).read_bytes()).hexdigest(),expected)
        with self.assertRaises(R['Refused']):R['memory_component'](WHOLE,'arbitrary.py')
        with self.assertRaises(R['Refused']):R['memory_projection'](WHOLE,PROJECT,renderer=lambda:None)

    def test_all_three_selected_roots_and_exact_edit_census(self):
        for function,_,_,_ in S['CASES']:
            with self.subTest(function=function):
                result,events,kwargs=project(function)
                cut=result['edit_manifest']['selected_original_root'];edits=result['edit_manifest']['edits']
                count=2 if function.endswith('during_store') else 3
                self.assertEqual(len(edits),count)
                self.assertEqual({row['kind'] for row in edits},{'api-include','ordinary-array-declarator'} |
                    (set() if count==2 else {'cacheable-pointer-declarator'}))
                self.assertIn('dws_cxx_array<std::uint32_t,16,0> data = {7, 11};',result['cxx_text'])
                self.assertEqual(result['cxx_text'].count('std::uint32_t whole_same_thread_'),1)
                self.assertEqual(result['runtime_identity']['source_route_instances'],[{'synthetic_route':i} for i in range(132)])
                self.assertEqual(len(cut['omitted_unreferenced_definitions']),2)
                self.assertEqual(events,['receiver-prepare','selected-body-stage','selected-body-check','header-render','receiver-prepare'])
                self.assertFalse(result['runtime_identity']['same_TU_graph_modified_or_filtered'])
                self.assertEqual(R['digest'](kwargs['normalized_tu']),kwargs['unit_preparation']['normalized_full_tu_sha256'])

    def test_source_body_and_receiver_changed_certificates_refuse(self):
        function=S['CASES'][1][0]
        mutations=(lambda k:k['statement_preparation'].update(changed=True),
            lambda k:k['receiver'].update(c_text='untrusted replacement'),
            lambda k:k['receiver']['draw_plan'].update(count=1),
            lambda k:k['receiver']['integration'].update(allocation_hooks=[]),
            lambda k:k['unit_preparation'].update(compiler_capture_receipt_sha256='b'*64),
            lambda k:k.update(caller='_Z5wrongv'))
        for change in mutations:
            with self.assertRaises(R['Refused']):project(function,change)

    def test_physical_line_alignment_and_exact_single_object_refuse(self):
        function=S['CASES'][0][0]
        mutations=(lambda k:k['atlas']['objects'][0].update(physical_base=4100),
            lambda k:k['atlas']['objects'][0].update(dtype=1),lambda k:k['atlas']['objects'][0].update(extent=15),
            lambda k:k['atlas']['objects'].append(copy.deepcopy(k['atlas']['objects'][0])),
            lambda k:k.update(allocations=[]),lambda k:k.update(thread=1),lambda k:k.update(thread=True))
        for change in mutations:
            with self.assertRaises(R['Refused']):project(function,change)

    def test_real_allocation_checker_cannot_replace_profile_line_alignment(self):
        kwargs,_,_,component,_=protocol(S['CASES'][0][0])
        api,_=component(WHOLE,'whole_interface_v4.py')
        owner=next(node for node in kwargs['normalized_tu']['inner'] if node['mangledName']==kwargs['caller'])
        atlas=copy.deepcopy(kwargs['atlas']);atlas['objects'][0]['physical_base']+=4
        for cell in atlas['cells']:
            cell['physical_begin']+=4;cell['physical_end']+=4
        # A valid natural-u32 mapping can cross a64-byte line. The memory
        # profile must reject it after the unchanged receiver check passes.
        RECEIVER['check_allocations'](kwargs['allocations'],atlas,R['MEMORY_SOURCE_SHA'],1)
        with self.assertRaisesRegex(R['Refused'],'owned64-byte physical alignment'):
            R['memory_object'](atlas,kwargs['allocations'],S['profile'](kwargs['function']),kwargs['caller'],0,api,owner)
        for mutation in (lambda value:value['objects'].append(copy.deepcopy(value['objects'][0])),
                         lambda value:value['objects'][0].update(dtype=1),
                         lambda value:value['objects'][0].update(extent=15)):
            changed=copy.deepcopy(kwargs['atlas']);mutation(changed)
            with self.assertRaises(R['Refused']):
                R['memory_object'](changed,kwargs['allocations'],S['profile'](kwargs['function']),kwargs['caller'],0,api,owner)

    def test_unchanged_real_header_renderer_one_object_27_declarations_132_routes(self):
        api,_=R['component'](WHOLE,'whole_interface_v4.py')
        dispatch,_=R['component'](WHOLE,'source_dispatch_v3.py')
        abi={'byte_order':'little','int_bits':32,'pointer_bits':64,
            'canonical_types':dict(zip(R['TYPE_KEYS'],('unsigned int','int','float','unsigned long','long','double'))),
            'alignments':[4,4,4,8,8,8],'sizes':[4,4,4,8,8,8]}
        declarations=api['inventory'](PROJECT)
        header,inventory,instances=R['render_header'](api,dispatch,PROJECT,declarations,abi,[{'object_index':0}],0)
        self.assertEqual((len(inventory),len({row['name'] for row in inventory}),len(instances)),(27,26,132))
        self.assertIn('case 0:dws_local_enter_0_v1();break;',header)
        self.assertIn('case 0:dws_local_leave_0_v1();break;',header)
        self.assertNotIn('case 1:dws_local_enter_1_v1();break;',header)
        self.assertNotIn('case 1:dws_local_leave_1_v1();break;',header)
        self.assertIn('for(;i<N;++i)',header)

    def test_exact_origin_and_scope_refuse(self):
        function=S['CASES'][2][0]
        for field,value in (('caller','wrong'),('object_index',1),('allocation_origin','self-authorized'),
                            ('scope_end_offset',3259),('declaration_sha256','0'*64),('allocation_thread',1)):
            def change(kwargs,field=field,value=value):kwargs['allocations'][0][field]=value
            with self.assertRaises(R['Refused']):project(function,change)

    def test_original_selected_API_and_scalar_lines_remain(self):
        for function,_,_,_ in S['CASES']:
            result,_,_=project(function)
            begin,end=S['spelling_span'](SOURCE,function)
            selected=SOURCE[begin:end]
            for line in selected.splitlines():
                if any(token in line for token in ('maa_','wait_ready(','get_new_','return ','data[0] =','index_data[0] =')):
                    self.assertIn(line,result['cxx_text'])
            self.assertFalse(result['edit_manifest']['generated_lowered_C_body_used'])
            self.assertFalse(result['edit_manifest']['source_function_result_or_prediction_used_by_runtime'])

    def test_selected_root_is_rechecked_after_header_render(self):
        kwargs,events,namespace,component,header=protocol(S['CASES'][0][0])
        def mutating_header(*args):
            result=header(*args);kwargs['normalized_tu']['after_change']=True;return result
        with patch.dict(namespace,{'memory_component':component,'render_header':mutating_header}):
            with self.assertRaisesRegex(R['Refused'],'TU changed'):
                R['memory_projection'](WHOLE,PROJECT,**kwargs)

    def test_receiver_is_reprepared_after_render(self):
        kwargs,events,namespace,component,header=protocol(S['CASES'][1][0])
        def mutating_header(*args):
            result=header(*args);kwargs['receiver']['c_text']='changed after precheck';return result
        with patch.dict(namespace,{'memory_component':component,'render_header':mutating_header}):
            with self.assertRaises(R['Refused']):R['memory_projection'](WHOLE,PROJECT,**kwargs)

    def test_first_profile_no_memory_hash_allowlist(self):
        with self.assertRaises(R['Refused']):R['file_pin'](SOURCE_PATH,R['SOURCE_SHA'])
        with self.assertRaises(R['Refused']):R['memory_projection'](WHOLE,PROJECT)
        self.assertEqual(R['PINS']['receiver-state-draws-v2/receiver_state_draws_v2.py'],
            'f6c19464a6587b4fbd4a6278dc66be97f1c4ab16d46b2db8cd6b804d41608a5f')


if __name__=='__main__':unittest.main(verbosity=2)
