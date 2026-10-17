"""Pure real-metadata/parser/root/signature controls; no project or child run.

Small TU nodes and ABI meanings are explicit synthetic protocol fixtures. No
large original TU, original ABI payload, body or native program is interpreted.
"""
import ast
import copy
import hashlib
import inspect
import io
import json
import math
import os
from pathlib import Path
import re
import runpy
import stat
import sys
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
PROPOSED=HERE/'proposed'
EVENTS=[]
def audit(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('pure memory source controls forbid child/native/network')
    if event=='import' and str(args[0]).split('.')[0]=='swdb':raise RuntimeError('pure controls forbid project import')
sys.addaudithook(audit)


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def need(value,message):
    if not value:raise ValueError(message)


def projected(path, values=None, names=None):
    nodes=[n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.Assign) or
           isinstance(n,(ast.FunctionDef,ast.ClassDef)) and (names is None or n.name in names)]
    ns={'Path':Path,'hashlib':hashlib,'json':json,'copy':copy,'re':re,'math':math,'os':os,'stat':stat,'io':io}
    if values:ns.update(values)
    exec(compile(ast.Module(nodes,type_ignores=[]),str(path),'exec'),ns)
    return ns


FACTS=json.loads((PROPOSED/'memory_capture_facts_v1.json').read_bytes())
POST=json.loads((WHOLE/'memory-role-gzip-v1-actual/postflight-stdout-v2.json').read_bytes())
ORIGINAL=json.loads((WHOLE/'compiler-memory-capture-v1-actual/closure-stdout-v1.json').read_bytes())
POLICY=json.loads((WHOLE/'memory-role-gzip-v1/source_policy_v1.json').read_bytes())
OBSERVER_POLICY=json.loads((HERE/'observer/observation-policy-template-v1.json').read_bytes())
SOURCE=SimpleNamespace(need=need,digest=digest,contracts=SimpleNamespace(document=json.loads))
INGRESS=projected(PROPOSED/'memory_normalized_capture_ingress_v1.py',{'source':SOURCE})
LEGACY=WHOLE/'normalized-unit-observation-v1/modules/compiler_unit_adapter_v3.py'
ROOT_SUPPORT=runpy.run_path(str(WHOLE/'source-memory-selection-v1/test_source_memory_selection_v1.py'),run_name='closed_root_fixture_support')
ROOT_API=ROOT_SUPPORT['M']


def adapter_fixture():
    api,kwargs=ROOT_SUPPORT['fixture'](ROOT_API['CASES'][0][0]);tu=kwargs['normalized_tu'];calls=kwargs['preparation']['calls'];calls[:]=[]
    actual_counts=(12,14,14)
    for index,root in enumerate(tu['inner']):
        body=root['inner'][0];start=root['range']['begin']['offset']+45
        local,ref=body['inner'][0],body['inner'][-1];nodes=[]
        for ordinal in range(actual_counts[index]):
            at=start+ordinal*2
            call={'kind':'CallExpr','range':{'begin':{'offset':at},'end':{'offset':at,'tokLen':1}},
                'inner':[{'kind':'DeclRefExpr','referencedDecl':{'kind':'FunctionDecl','name':'alloc_MAA'}}]}
            nodes.append(call);calls.append({'name':'alloc_MAA','caller_mangled':root['mangledName'],'call_range':[at,at+1]})
        body['inner']=[local,*nodes,ref]
    raw=canonical(tu);source_path=ROOT_SUPPORT['SOURCE'];source_bytes=source_path.read_bytes()
    class OriginalPath:
        def __init__(self,path):self.path=str(path)
        def __str__(self):return self.path
        def resolve(self):return self
        def read_bytes(self):
            if self.path==str(source_path):return source_bytes
            if self.path=='/explicit-inert-probe.cpp':return b'ABI source stand-in'
            raise ValueError('unknown small fixture path')
    def abi(raw,**kwargs):return {'abi':{'fixture':'ABI'},'raw_probe_sha256':hashlib.sha256(raw).hexdigest()}
    legacy=projected(LEGACY,{'Path':OriginalPath,'observed_abi':abi},names={'Refused','need','sha','strict_decoder','parse_json_roots','resolve_locations','prepare_unit'})
    def bind_call(tree,**values):
        return next(row for row in calls if row['caller_mangled']==values['caller'] and row['call_range']==list(values['call_range']))
    api['bind_call']=bind_call
    delegated=[]
    def delegate(*args,**values):delegated.append(values);return legacy['prepare_unit'](*args,**values)
    derived=b'explicit derived strict ABI protocol fixture'
    receipt={'selected_family':'three-memory-g642','original_sha256':hashlib.sha256(b'explicit ABI value double').hexdigest(),
        'derived_strict_sha256':hashlib.sha256(derived).hexdigest()}
    adapter=projected(PROPOSED/'memory_normalized_compiler_adapter_v1.py',{'legacy':SimpleNamespace(__file__=str(LEGACY),prepare_unit=delegate),
        'abi_transport':SimpleNamespace(normalize_abi=lambda raw:(derived,receipt))})
    adapter.update(EXPANDED_BYTES=len(raw),EXPANDED_SHA=hashlib.sha256(raw).hexdigest(),COMPRESSED_BYTES=13,SOURCE_PATH=str(source_path))
    values={'transport_kind':adapter['KIND'],'full_tu_raw':raw,'abi_raw':b'explicit ABI value double',
        'source_path':source_path,'source_bytes':source_bytes,'probe_path':'/explicit-inert-probe.cpp','probe_bytes':b'ABI source stand-in',
        'declarations':kwargs['declarations'],'compiler_capture_pin':adapter['CAPTURE_SHA'],
        'full_tu_compressed_bytes':13,'full_tu_expanded_limit':201326592}
    return adapter,legacy,api,values,delegated,kwargs


class Controls(unittest.TestCase):
    def test_exact_actual_memory_facts_and_first_stream_disjoint(self):
        for name,row in FACTS['original'].items():
            original=next(r for r in ORIGINAL['rows']if r['path']==row['path'])
            self.assertEqual({k:original[k]for k in ('path','bytes','sha256')},row)
        self.assertEqual(FACTS['codec'],POST['transport']['normalized_gzip_codec'])
        self.assertEqual(FACTS['normalization'],POST['census'])
        self.assertEqual(FACTS['codec']['expanded_bytes'],177082275)
        self.assertEqual(FACTS['codec']['compressed_bytes'],12666345)
        self.assertNotEqual(FACTS['kind'],'complete-original-tu-paired-type-gzip-2')
        self.assertEqual(hashlib.sha256((PROPOSED/'memory_capture_facts_v1.json').read_bytes()).hexdigest(),
            '9862edaf233ebb7d6146dfdb7e825864e1c4314bd5e034a9a8800c97b20a3f3a')

    def test_actual_original_and_transform_boundaries_refuse_false_promotions(self):
        result=ORIGINAL['metadata']['component/result.json'];INGRESS['original_gate'](result)
        INGRESS['transform_gate'](POST['transform_result'],FACTS)
        for key,value in (('accepted',False),('source_call_admitted',True),('ABI_interpreted',True),
                          ('strict_complete_TU_consumer_passed',True),('public_proof',True),('error',{}),('source_call_count',1)):
            changed={**result,key:value}
            with self.subTest(key=key),self.assertRaises(ValueError):INGRESS['original_gate'](changed)
        for key,value in (('normalization_complete',False),('source_fixture_sha256','0'*64),('original_AST_ABI_source_call_admitted',True),
                          ('compiler_or_native_or_solver_executed',True),('wall_seconds',float('nan'))):
            with self.subTest(key=key),self.assertRaises(ValueError):INGRESS['transform_gate']({**POST['transform_result'],key:value},FACTS)

    def test_actual_root_execution_publication_and_complete911_input14_output_closure(self):
        transform=OBSERVER_POLICY['capture']['transform']
        load=lambda key:json.loads(Path(FACTS[key]['path']).read_bytes())
        args=(load('root_adoption'),load('reconciliation'),load('invocation'),load('stdout'),transform,FACTS)
        INGRESS['execution_gate'](*args)
        rows=INGRESS['input_output_closure'](POST['transform_result'],POLICY,transform,FACTS)
        self.assertEqual(len(rows),911+13)
        for key in ('input_pins','outputs'):
            changed=copy.deepcopy(POST['transform_result']);changed[key].pop()
            with self.assertRaises(ValueError):INGRESS['input_output_closure'](changed,POLICY,transform,FACTS)
        changed=copy.deepcopy(args);changed[2]['returncode']=False
        with self.assertRaises(ValueError):INGRESS['execution_gate'](*changed)

    def test_reused_physical_dependency_utilities_are_byte_exact(self):
        old=(WHOLE/'normalized-ingress-v2/proposed/normalized_capture_ingress_v2.py').read_text()
        new=(PROPOSED/'memory_normalized_capture_ingress_v1.py').read_text()
        functions=lambda text:{n.name:ast.get_source_segment(text,n)for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
        before,after=functions(old),functions(new)
        for name in ('need','exact','same_bytes','stream_stable','make_dependencies','physical_runtime'):
            self.assertEqual(before[name],after[name])

    def test_public_prepared_equality_and_private_unknown_preparation_are_separate(self):
        calls=[];result=('/original',b'source',{'kind':'TranslationUnitDecl'},[],{'actual':'fixture'}, {})
        ns=projected(PROPOSED/'memory_normalized_capture_ingress_v1.py',{'source':SOURCE})
        ns['_derive']=lambda *a:(calls.append(a)or result)
        reads=SimpleNamespace(document=lambda pin:pin,recheck=lambda:None)
        selected={'capture':{'prepared':None}}
        with self.assertRaises(ValueError):ns['complete_capture'](selected,reads,'/original-project')
        self.assertEqual(calls,[]);self.assertEqual(ns['observe_capture'](selected,reads,'/original-project'),result)
        selected['capture']['prepared']={'actual':'fixture'}
        self.assertEqual(ns['complete_capture'](selected,reads,'/original-project'),result)
        selected['capture']['prepared']={'invented':'fixture'}
        with self.assertRaises(ValueError):ns['complete_capture'](selected,reads,'/original-project')
        with self.assertRaises(ValueError):ns['observe_capture'](selected,reads,'/original-project')

    def test_real_legacy_strict_parser_and40_call_wrapper_keep_full_tu(self):
        adapter,legacy,api,kwargs,delegated,root=adapter_fixture()
        result=adapter['prepare_unit'](api,**kwargs)
        self.assertEqual(result['schema'],'whole-interface-original-tu-preparation-1')
        self.assertEqual(len(result['calls']),40)
        self.assertEqual(result['normalized_transport']['kind'],FACTS['kind'])
        self.assertFalse(result['public_admission'])
        self.assertIs(delegated[0]['full_tu_raw'],kwargs['full_tu_raw'])
        self.assertEqual(delegated[0]['full_tu_expanded_limit'],536870912)
        with self.assertRaises(ValueError):legacy['parse_json_roots'](b'{"kind":"UsingType","type":{},"type":{}}')

    def test_wrong_memory_source_transport_extents_receipts_and_call_censuses_refuse(self):
        for key,value in (('transport_kind','complete-original-tu-paired-type-gzip-2'),('full_tu_expanded_limit',536870912),
                          ('full_tu_compressed_bytes',True),('compiler_capture_pin','0'*64),('source_bytes',b'other-source')):
            adapter,legacy,api,kwargs,delegated,root=adapter_fixture();kwargs[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):adapter['prepare_unit'](api,**kwargs)
            self.assertEqual(delegated,[])
        adapter,legacy,api,kwargs,delegated,root=adapter_fixture();result=adapter['prepare_unit'](api,**kwargs)
        for mutation in ('deleted','extra-caller','duplicate-range'):
            changed=copy.deepcopy(result)
            if mutation=='deleted':changed['calls'].pop()
            elif mutation=='extra-caller':changed['calls'][0]['caller_mangled']='_Zunknownv'
            else:changed['calls'][1]['call_range']=changed['calls'][0]['call_range']
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):adapter['check_cases'](changed)

    def test_three_real_root_helper_certificates_preserve_graph_and_private_tokens(self):
        adapter,legacy,api,kwargs,delegated,root=adapter_fixture();prepared=adapter['prepare_unit'](api,**kwargs)
        source=SimpleNamespace(binder=SimpleNamespace(**api))
        module=projected(PROPOSED/'memory_source_preparation_v1.py',{'source':source,
            'selection':SimpleNamespace(**ROOT_API),'compiler':SimpleNamespace(**adapter)})
        tu=legacy['resolve_locations'](legacy['parse_json_roots'](kwargs['full_tu_raw'],full_tu=True,expanded_limit=201326592)[0],kwargs['source_path'])
        before=copy.deepcopy(tu)
        cert=module['prepare_roots'](normalized_tu=tu,source_path=kwargs['source_path'],preparation=prepared,
            declarations=kwargs['declarations'],abi=prepared['abi_observation']['abi'])
        self.assertEqual(len(cert['units']),3);self.assertEqual(tu,before)
        self.assertEqual(len({row['selected_root']['selected_declaration_id']for row in cert['units']}),3)
        self.assertFalse(cert['actual_body_CPU_lifetime_or_public_acceptance'])
        self.assertTrue(all(row['body_CPU_lifetime_mapping_receiver_checks_required']for row in cert['units']))
        changed=copy.deepcopy(tu);changed['inner'].pop();bad=copy.deepcopy(prepared);bad['normalized_full_tu_sha256']=digest(changed)
        with self.assertRaises(ValueError):module['prepare_roots'](normalized_tu=changed,source_path=kwargs['source_path'],preparation=bad,
            declarations=kwargs['declarations'],abi=prepared['abi_observation']['abi'])

    def test_closed_dispatch_preserves_old_branches_and_refuses_unprepared_memory(self):
        calls=[];first=SimpleNamespace(KIND='complete-original-tu-paired-type-gzip-2',complete_capture=lambda *a:calls.append('first'))
        memory=SimpleNamespace(KIND=FACTS['kind'],SOURCE_SHA=FACTS['original']['source']['sha256'],complete_capture=lambda *a:calls.append('memory'))
        ns=projected(PROPOSED/'capture_family_dispatch_v1.py',{'source':SimpleNamespace(need=need,CAPTURE_KIND='lossless-complete-original-tu-v1'),
            'first':first,'memory':memory})
        for kind in ('lossless-complete-original-tu-v1',first.KIND,FACTS['kind']):
            ns['complete_capture']({'capture':{'kind':kind},'proof_source':{'sha256':memory.SOURCE_SHA}},None,None)
        self.assertEqual(calls,['first','first','memory'])
        for kind in ('unsupported-unprepared-memory-profile-1','unknown',None):
            with self.assertRaises(ValueError):ns['complete_capture']({'capture':{'kind':kind}},None,None)
        with self.assertRaises(ValueError):ns['complete_capture']({'capture':{'kind':memory.KIND},'proof_source':{'sha256':'0'*64}},None,None)

    def test_observer_closed_module_manifest_source_roles_and_exact_inverse(self):
        observer=HERE/'observer';manifest=json.loads((observer/'fixed-memory-modules-v1.json').read_bytes())
        self.assertEqual(len(manifest['modules']),14);self.assertEqual(len(OBSERVER_POLICY['controls']),17)
        for row in manifest['modules']:
            raw=(observer/'modules'/row['file']).read_bytes()
            self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(row['bytes'],row['sha256']))
        self.assertIsNone(OBSERVER_POLICY['capture']['prepared']);self.assertIsNone(OBSERVER_POLICY['root_admission_receipt'])
        self.assertEqual(OBSERVER_POLICY['capture']['kind'],FACTS['kind'])
        self.assertTrue(all('/control/'in row['path']and'/observer/control/'not in row['path']
            for role,row in OBSERVER_POLICY['capture']['transform'].items()if role in ('root_adoption','reconciliation','postflight','invocation','stdout','stderr')))
        text=(observer/'observe_memory_entry_v1.py').read_text();inverse=json.loads((HERE/'observer-entry-inverse-v2.json').read_bytes())
        for new,old in inverse['result_schema_inverse'].items():text=text.replace(new,old)
        for row in reversed(inverse['replacements']):
            self.assertEqual(text.count(row['new']),1);text=text.replace(row['new'],row['old'],1)
        self.assertEqual(text,Path(inverse['predecessor']['path']).read_text())

    def test_body_preparation_binds_real_consumer_signatures_and_no_callback_api(self):
        text=(PROPOSED/'memory_source_preparation_v1.py').read_text();tree=ast.parse(text)
        root=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='prepare_roots')
        self.assertEqual(root.args.args,[])
        specs={
            'prepare_atlas':(WHOLE/'source_dispatch_v3.py','prepare_atlas'),
            'check_allocations':(WHOLE/'receiver-memory-v1/receiver_memory_v1.py','check_allocations'),
            'memory_object':(WHOLE/'runtime-projection-v4/runtime_projection_v4.py','memory_object')}
        for attr,(path,name)in specs.items():
            function=next(n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name==name)
            stub=copy.deepcopy(function);stub.body=[ast.Pass()];namespace={}
            exec(compile(ast.fix_missing_locations(ast.Module([stub],type_ignores=[])),'real-body-consumer-signature','exec'),namespace)
            signature=inspect.signature(namespace[name])
            for call in (n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr==attr):
                signature.bind(*[None for _ in call.args],**{k.arg:None for k in call.keywords})
        self.assertIn('root-selected-memory-source-object-mapping-1',text)
        self.assertIn('owned_runtime_context_receiver_preparation_still_required',text)
        self.assertEqual(EVENTS,[])

    def test_source_hook_exact_inverse_and_only_closed_metadata_roles_extend(self):
        import builtins
        source_path=HERE/'integration-source/dx100_checked_source.py'
        text=source_path.read_text();inverse=json.loads((HERE/'source-family-hook-inverse-v2.json').read_bytes())
        restored=text
        for row in reversed(inverse['replacements']):
            self.assertEqual(restored.count(row['new']),row['count'])
            restored=restored.replace(row['new'],row['old'])
        self.assertEqual(restored,Path(inverse['base']['path']).read_text())
        dispatcher=SimpleNamespace(NORMALIZED_KINDS=('complete-original-tu-paired-type-gzip-2',FACTS['kind']))
        def import_protocol(name,globals=None,locals=None,fromlist=(),level=0):
            if name=='swdb._dx100_whole':return SimpleNamespace(capture_family_dispatch_v1=dispatcher)
            raise AssertionError('unadmitted metadata role import')
        node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and n.name=='capture_inputs')
        ns={'need':need,'CAPTURE_KIND':'lossless-complete-original-tu-v1',
            '__builtins__':{**vars(builtins),'__import__':import_protocol}}
        exec(compile(ast.Module([node],type_ignores=[]),'real-metadata-role-projection','exec'),ns)
        selected=OBSERVER_POLICY['capture']
        self.assertEqual(ns['capture_inputs'](selected),(selected['transform']['normalized_gzip'],selected['original']['observation']))
        self.assertNotEqual(selected['transform']['normalized_gzip'],selected['original']['compressed_tu'])
        with self.assertRaises(ValueError):ns['capture_inputs']({'kind':'unsupported-unprepared-memory-profile-1'})

    def test_genuine_original_ABI_role_stays_separate_and_generic_decoder_is_unchanged(self):
        self.assertEqual(FACTS['original']['abi'],{'path':FACTS['original_root']+'/component/abi.ast.json',
            'bytes':127541,'sha256':'493764cb6cbb2783db0cdfbbaf1bfd7d3b6efc73ff27df77eb9e5d6e8603b55c'})
        tree=ast.parse((PROPOSED/'memory_normalized_capture_ingress_v1.py').read_bytes())
        call=next(n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)
            and n.func.attr=='prepare_unit')
        abi=next(k.value for k in call.keywords if k.arg=='abi_raw')
        self.assertEqual(ast.unparse(abi),"reads.selected(original['abi'])")
        self.assertEqual(hashlib.sha256(LEGACY.read_bytes()).hexdigest(),
            '775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c')
        self.assertIn('must not be dispatched', (HERE/'PLAN.md').read_text())


    def test_successor_exact_inverses_and_unchanged_body_consumers(self):
        inverse=json.loads((HERE/'successor-inverse-v2.json').read_bytes())
        old=HERE.parent/'memory-normalized-ingress-v1'
        for relative,rows in inverse['changed_source_replacements'].items():
            text=(HERE/relative).read_text()
            for row in reversed(rows):
                self.assertEqual(text.count(row['new']),1);text=text.replace(row['new'],row['old'],1)
            self.assertEqual(text,(old/relative).read_text())
        for relative in inverse['unchanged_semantic_sources']:
            self.assertEqual((HERE/relative).read_bytes(),(old/relative).read_bytes())
        def functions(path):
            text=path.read_text()
            return {n.name:ast.get_source_segment(text,n)for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
        self.assertEqual(functions(PROPOSED/'memory_normalized_capture_ingress_v1.py'),
            functions(old/'proposed/memory_normalized_capture_ingress_v1.py'))

    def test_adapter_consumes_derived_ABI_and_retains_original_identity(self):
        adapter,legacy,api,kwargs,delegated,_root=adapter_fixture()
        observed=[];normalizer=adapter['abi_transport'].normalize_abi
        adapter['abi_transport'].normalize_abi=lambda raw:(observed.append(raw)or normalizer(raw))
        result=adapter['prepare_unit'](api,**kwargs)
        self.assertEqual(observed,[kwargs['abi_raw']])
        self.assertNotEqual(delegated[0]['abi_raw'],kwargs['abi_raw'])
        abi=result['abi_observation'];receipt=abi['paired_type_role_transport']
        self.assertEqual(abi['raw_probe_sha256'],hashlib.sha256(delegated[0]['abi_raw']).hexdigest())
        self.assertEqual(abi['raw_probe_sha256'],receipt['derived_strict_sha256'])
        self.assertEqual(abi['original_raw_probe_sha256'],hashlib.sha256(kwargs['abi_raw']).hexdigest())
        self.assertEqual(receipt['selected_family'],'three-memory-g642')
        self.assertIs(delegated[0]['full_tu_raw'],kwargs['full_tu_raw'])
        self.assertEqual(len(result['calls']),40)

    def test_first_ABI_family_or_false_derived_consumer_identity_refuses(self):
        adapter,legacy,api,kwargs,delegated,_root=adapter_fixture()
        derived,receipt=adapter['abi_transport'].normalize_abi(kwargs['abi_raw'])
        adapter['abi_transport'].normalize_abi=lambda raw:(derived,{**receipt,'selected_family':'first-source-v10'})
        with self.assertRaises(ValueError):adapter['prepare_unit'](api,**kwargs)
        self.assertEqual(delegated,[])
        adapter['abi_transport'].normalize_abi=lambda raw:(derived,receipt)
        legacy['observed_abi']=lambda *a,**kw:{'abi':{'fixture':'ABI'},'raw_probe_sha256':receipt['original_sha256']}
        with self.assertRaises(ValueError):adapter['prepare_unit'](api,**kwargs)

    def test_exact_reviewed_helper_primitive_and_closed_observer_paths(self):
        expected=WHOLE/'abi-role-transport-v2/abi_role_transport_v1.py'
        self.assertEqual((PROPOSED/'abi_role_transport_v1.py').read_bytes(),expected.read_bytes())
        self.assertEqual(hashlib.sha256(expected.read_bytes()).hexdigest(),'ea2e7e26ae154ccb9bd40204f75571ddca8fe50591a862d36abb140ec0893f8e')
        self.assertEqual((PROPOSED/'strict_minify_v2.py').read_bytes(),(WHOLE/'streaming-minify-v1/strict_minify_v2.py').read_bytes())
        modules=json.loads((HERE/'observer/fixed-memory-modules-v1.json').read_bytes())['modules']
        order={row['module']:i for i,row in enumerate(modules)}
        for name in ('role_normalized_gzip_v2','strict_minify_v2'):
            self.assertLess(order['swdb._dx100_whole.'+name],order['swdb._dx100_whole.abi_role_transport_v1'])
        self.assertLess(order['swdb._dx100_whole.abi_role_transport_v1'],order['swdb._dx100_whole.memory_normalized_compiler_adapter_v1'])
        for name in ('abi_role_transport_v1.py','strict_minify_v2.py'):
            row=OBSERVER_POLICY['controls'][name]
            self.assertEqual(row['path'],OBSERVER_POLICY['output_root']+'/control/'+name)
            raw=(HERE/'observer/modules'/name).read_bytes()
            self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(row['bytes'],row['sha256']))
        source=(HERE/'integration-source/dx100_checked_source.py').read_text()
        producer=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name=='producer_paths')
        self.assertIn('abi_role_transport_v1, strict_minify_v2',ast.get_source_segment(source,producer))
        self.assertIsNone(OBSERVER_POLICY['capture']['prepared'])
        self.assertIsNone(OBSERVER_POLICY['root_admission_receipt'])

    def test_real_ingress_adapter_physical_pin_old_RED_new_GREEN(self):
        tree=ast.parse((PROPOSED/'memory_normalized_capture_ingress_v1.py').read_bytes())
        loop=next(n for n in ast.walk(tree)if isinstance(n,ast.For)and isinstance(n.target,ast.Tuple)
            and ast.unparse(n.target)=='(module, expected)')
        paths={'codec':WHOLE/'normalized-unit-observation-v1/modules/lossless_gzip_v2.py',
            'normalizer':WHOLE/'role-normalized-gzip-v2/role_normalized_gzip_v2.py',
            'closed':WHOLE/'normalized-unit-observation-v1/modules/closed_python_surface.py',
            'memory_compiler':PROPOSED/'memory_normalized_compiler_adapter_v1.py'}
        def absolute(row,**_kw):
            raw=Path(row['path']).read_bytes()
            need((len(raw),hashlib.sha256(raw).hexdigest())==(row['bytes'],row['sha256']),'exact physical memory primitive required')
        ns={'Path':Path,'reads':SimpleNamespace(absolute=absolute)}
        ns.update({name:SimpleNamespace(__file__=str(path))for name,path in paths.items()})
        ns['memory_compiler'].LEGACY_SHA='775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c'
        ns['source']=SimpleNamespace(compiler=SimpleNamespace(__file__=str(LEGACY)))
        assignments=[n for n in tree.body if isinstance(n,ast.Assign)]
        exec(compile(ast.Module(assignments,type_ignores=[]),'actual-memory-pins','exec'),ns)
        code=compile(ast.Module([loop],type_ignores=[]),'actual-memory-primitive-gate','exec')
        exec(code,ns)
        ns['MEMORY_COMPILER_SHA']='1315ebef75dc4219bcb012aa2a5f85cbcaeb82c54bb625fdad6f18ea397a6e62'
        with self.assertRaises(ValueError):exec(code,ns)


if __name__=='__main__':unittest.main(verbosity=2)
