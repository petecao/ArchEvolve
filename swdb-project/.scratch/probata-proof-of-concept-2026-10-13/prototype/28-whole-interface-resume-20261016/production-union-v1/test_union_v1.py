"""2026-10-16 ET. Complete source union and producer-closure controls, no child."""
import ast
import copy
import difflib
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;PROJECT=WHOLE.parents[3];OUT=HERE/'proposed';FINITE=WHOLE/'finite-trace-public-v4'
def audit(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:raise RuntimeError('union controls forbid native/child/network')
    if event=='import' and str(args[0]).split('.')[0]=='swdb':raise RuntimeError('union controls forbid installed project imports')
sys.addaudithook(audit)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':sha(raw)}
def need(ok,message):
    if not ok:raise ValueError(message)
def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def projected(path,source_paths=None):
    function=next(n for n in ast.parse((HERE/'build_union_v1.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='projected_producer_paths')
    ns={'ast':ast,'copy':copy,'Path':Path,'types':types,'need':need}
    exec(compile(ast.Module(body=[function],type_ignores=[]),'<real-producer-leaf-projection>','exec'),ns)
    return ns['projected_producer_paths'](path,source_paths=source_paths)

class Controls(unittest.TestCase):
    def test_all_69_selected_paths_exact_and_shared_bases_untouched(self):
        rows=json.loads((HERE/'production-paths-and-bases-v1.json').read_bytes())['paths']
        self.assertEqual(len(rows),69)
        for row in rows:
            self.assertEqual(pin(Path(row['proposal']['path'])),row['proposal'])
            self.assertEqual(pin(Path(row['selected_frozen_source']['path'])),row['selected_frozen_source'])
            self.assertEqual(row['proposal']['sha256'],row['selected_frozen_source']['sha256'])
            current=PROJECT/row['relative']
            if row['current_shared_base'] is None:self.assertFalse(current.exists())
            else:self.assertEqual(pin(current),row['current_shared_base'])
        for name in ('cbmc_adapter.py','formal_frame.py','proof_semantics.py','proof_setup.py'):
            self.assertEqual((OUT/'swdb'/name).read_bytes(),(FINITE/'proposed/swdb'/name).read_bytes())

    def test_semantic_dependency_exact_inverses_and_typed_scope_preserved(self):
        inverses=json.loads((WHOLE/'abi-semantic-dependents-v1/exact-inverses-v1.json').read_bytes())['files']
        for relative,row in inverses.items():
            text=(OUT/relative).read_text()
            for change in reversed(row['replacements']):
                self.assertEqual(text.count(change['new']),change['count']);text=text.replace(change['new'],change['old'])
            self.assertEqual(text.encode(),Path(row['basis']['path']).read_bytes())
        typed=functions(FINITE/'proposed/swdb/dx100_checked_source.py');union=functions(OUT/'swdb/dx100_checked_source.py')
        for name in typed:
            if name!='producer_paths':self.assertEqual(typed[name],union[name],name)
        self.assertEqual((OUT/'swdb/_dx100_finite/context_rule_scope_v1.py').read_bytes(),(FINITE/'proposed/swdb/_dx100_finite/context_rule_scope_v1.py').read_bytes())
        for name in ('complete_capture','record_assumptions'):
            self.assertEqual(typed[name],union[name])

    def test_actual_v3_and_separately_pinned_v4_remain_distinct(self):
        v3=PROJECT/'swdb/_dx100_whole/compiler_unit_adapter_v3.py';v4=OUT/'swdb/_dx100_whole/compiler_unit_adapter_v4.py'
        self.assertEqual(sha(v3.read_bytes()),'775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c')
        self.assertEqual(sha(v4.read_bytes()),'b5bd7293259f69ffe4e5d6094cb6bd46c2d5527ef95cd28d0aaa95d88529e6c6')
        source=(OUT/'swdb/dx100_checked_source.py').read_text()
        self.assertIn('compiler_unit_adapter_v3 as compiler',source);self.assertIn('compiler_unit_adapter_v4 as semantic_compiler',source)
        for name in ('normalized_compiler_adapter_v1.py','memory_normalized_compiler_adapter_v1.py'):
            text=(OUT/'swdb/_dx100_whole'/name).read_text()
            self.assertIn('compiler_unit_adapter_v4 as consumer',text);self.assertIn("CONSUMER_SHA",text)
            self.assertNotIn('compiler_unit_adapter_v3 as',text)
        self.assertEqual(functions(v3)['prepare_unit'],functions(v4)['prepare_unit'])

    def test_real_source_and_finite_producer_role_maps_complete(self):
        source,virtual=projected(OUT/'swdb/dx100_checked_source.py')
        finite,_=projected(OUT/'swdb/dx100_finite_trace.py',source_paths=source)
        recipe=json.loads((HERE/'producer-member-recipe-v1.json').read_bytes())
        source={k:v.relative_to(virtual).as_posix() for k,v in source.items()};finite={k:v.relative_to(virtual).as_posix() for k,v in finite.items()}
        self.assertEqual(source,recipe['SourceUnit_roles']);self.assertEqual(finite,recipe['TraceUnit_roles'])
        self.assertEqual((len(source),len(finite)),(47,70))
        self.assertEqual({key.removeprefix('checked-package/'):value for key,value in finite.items() if key.startswith('checked-package/')},source)
        self.assertEqual(source['compiler_unit_adapter_v3.py'],'swdb/_dx100_whole/compiler_unit_adapter_v3.py')
        self.assertEqual(source['compiler_unit_adapter_v4.py'],'swdb/_dx100_whole/compiler_unit_adapter_v4.py')
        self.assertIn('context_rule_scope_v1.py',source);self.assertIn('_dx100_finite/__init__.py',source)
        self.assertIn('finite/__init__.py',finite)

    def test_real_producer_closure_rejects_missing_v4_wrong_role_or_hash(self):
        source,_=projected(OUT/'swdb/dx100_checked_source.py')
        paths={name:(OUT/path.relative_to('/prospective-selected-producer') if (OUT/path.relative_to('/prospective-selected-producer')).is_file()
            else PROJECT/path.relative_to('/prospective-selected-producer')) for name,path in source.items()}
        manifest={'schema':'swdb-dx100-whole-producers-1','files':{name:pin(path) for name,path in paths.items()}}
        function=next(n for n in ast.parse((OUT/'swdb/dx100_checked_source.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='producer_closure')
        ns={'need':need,'producer_paths':lambda:paths}
        exec(compile(ast.Module(body=[function],type_ignores=[]),'<real-producer-closure>','exec'),ns)
        class Reads:
            def __init__(self,selected):self.selected=selected
            def document(self,row):return self.selected
            def absolute(self,row):
                actual=pin(Path(row['path']));need(actual==row,'physical producer differs')
        ns['producer_closure']({'producer_manifest':{}},Reads(manifest))
        for mutation in ('missing','path','hash','extra'):
            bad=copy.deepcopy(manifest)
            if mutation=='missing':bad['files'].pop('compiler_unit_adapter_v4.py')
            elif mutation=='path':bad['files']['compiler_unit_adapter_v4.py']['path']=str(paths['compiler_unit_adapter_v3.py'])
            elif mutation=='hash':bad['files']['compiler_unit_adapter_v4.py']['sha256']='0'*64
            else:bad['files']['arbitrary.py']=next(iter(bad['files'].values()))
            with self.assertRaises(ValueError):ns['producer_closure']({'producer_manifest':{}},Reads(bad))

    def test_79_member_basis_and_builder_two_edit_inverse(self):
        basis=json.loads((HERE/'profile/normal-producer-basis-union-v1.json').read_bytes())
        rows=basis['files'];self.assertEqual(len(rows),79);self.assertEqual(rows,sorted(rows,key=lambda row:row['relative']))
        self.assertEqual(len({row['relative'] for row in rows}),79)
        self.assertIsNone(basis['final_published_producer_commit'])
        self.assertEqual(basis['root_base_commit'],'001df353dc4aa46ab43c395997b760fb2b203ab2')
        for row in rows:
            path=OUT/row['relative'] if (OUT/row['relative']).is_file() else PROJECT/row['relative']
            actual=pin(path);self.assertEqual((actual['bytes'],actual['sha256']),(row['bytes'],row['sha256']))
        inverse=json.loads((HERE/'builder-inverse-v1.json').read_bytes());text=(HERE/'profile/profile_builder_union_v1.py').read_text()
        for change in reversed(inverse['replacements']):
            self.assertEqual(text.count(change['new']),change['count']);text=text.replace(change['new'],change['old'])
        self.assertEqual(text.encode(),Path(inverse['basis']['path']).read_bytes())

    def test_wp_and_other_live_source_hunks_remain_exact(self):
        for name in ('standard_vector_member_view.py','wp_adapter.py','wp_pointer_bounds.py'):
            final=OUT/'swdb'/name if (OUT/'swdb'/name).exists() else PROJECT/'swdb'/name
            self.assertEqual(final.read_bytes(),(PROJECT/'swdb'/name).read_bytes())
        final=functions(OUT/'swdb/proof_semantics.py');live=functions(PROJECT/'swdb/proof_semantics.py')
        self.assertEqual(final['record_assumptions'],live['record_assumptions'])
        source=(OUT/'swdb/proof_setup.py').read_text()
        self.assertIn('standard_vector_member_view.py',source)
        self.assertIn('dx100_finite_trace',source)

    def test_patch_is_exact_and_inert_metadata_remains_explicit(self):
        table=json.loads((HERE/'production-paths-and-bases-v1.json').read_bytes());patch=[]
        for row in table['paths']:
            new=Path(row['proposal']['path']).read_text();base=row['current_shared_base'];relative=row['relative']
            if base is not None and base['sha256']==sha(new.encode()):continue
            old='' if base is None else (PROJECT/relative).read_text()
            patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='/dev/null' if base is None else 'a/swdb-project/'+relative,tofile='b/swdb-project/'+relative))
        self.assertEqual(''.join(patch),(HERE/'production-union-v1.patch').read_text())
        self.assertIs(table['Git_readback_or_shared_apply_performed'],False)
        recipe=json.loads((HERE/'producer-member-recipe-v1.json').read_bytes())
        self.assertIsNone(recipe['final_root_selected_producer_commit'])
        self.assertIs(recipe['imported_origin_or_published_commit_attested'],False)

if __name__=='__main__':unittest.main(verbosity=2)
