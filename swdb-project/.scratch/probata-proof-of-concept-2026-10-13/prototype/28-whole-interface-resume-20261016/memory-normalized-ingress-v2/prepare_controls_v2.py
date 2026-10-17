"""2026-10-16 ET. Closed no-child controls for the inert memory ABI successor."""
import ast
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'memory-normalized-ingress-v1'
source = (OLD / 'test_memory_family_v1.py').read_text()


def replace(old, new):
    global source
    assert source.count(old) == 1, old[:100]
    source = source.replace(old, new, 1)


replace("    def abi(raw,**kwargs):return {'abi':{'fixture':'ABI'}}",
    "    def abi(raw,**kwargs):return {'abi':{'fixture':'ABI'},'raw_probe_sha256':hashlib.sha256(raw).hexdigest()}")
replace("    adapter=projected(PROPOSED/'memory_normalized_compiler_adapter_v1.py',{'legacy':SimpleNamespace(__file__=str(LEGACY),prepare_unit=delegate)})",
    "    derived=b'explicit derived strict ABI protocol fixture'\n"
    "    receipt={'selected_family':'three-memory-g642','original_sha256':hashlib.sha256(b'explicit ABI value double').hexdigest(),\n"
    "        'derived_strict_sha256':hashlib.sha256(derived).hexdigest()}\n"
    "    adapter=projected(PROPOSED/'memory_normalized_compiler_adapter_v1.py',{'legacy':SimpleNamespace(__file__=str(LEGACY),prepare_unit=delegate),\n"
    "        'abi_transport':SimpleNamespace(normalize_abi=lambda raw:(derived,receipt))})")
replace("        self.assertEqual(len(manifest['modules']),12);self.assertEqual(len(OBSERVER_POLICY['controls']),15)",
    "        self.assertEqual(len(manifest['modules']),14);self.assertEqual(len(OBSERVER_POLICY['controls']),17)")
source = source.replace("HERE/'observer-entry-inverse-v1.json'", "HERE/'observer-entry-inverse-v2.json'")
source = source.replace("HERE/'source-family-hook-inverse-v1.json'", "HERE/'source-family-hook-inverse-v2.json'")
source = source.replace('test_genuine_ABI_role_is_separate_and_no_normalizer_or_last_wins_is_added',
    'test_genuine_original_ABI_role_stays_separate_and_generic_decoder_is_unchanged')
append = '''
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
'''
assert source.count("\n\nif __name__=='__main__':") == 1
source = source.replace("\n\nif __name__=='__main__':", '\n' + append + "\n\nif __name__=='__main__':")
(HERE / 'test_memory_family_v2.py').write_text(source)
