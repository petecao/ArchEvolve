"""2026-10-16 ET. Compiler-free closed initialized-register policy controls.

Run through the separately reviewed standalone unittest entry, not pytest's
compiler-aware repository fixtures. No C parser, compiler or verifier is used.
"""
import hashlib
import ast
import copy
import json
import re
import tempfile
import types
import unittest
from pathlib import Path


def real_resolution_library(project,root=None):
    """Project unchanged public reference methods; no permissive fake resolver."""
    from swdb import paths
    file=project/'swdb/library.py';tree=ast.parse(file.read_bytes(),filename=str(file))
    original=next(node for node in tree.body if isinstance(node,ast.ClassDef)and node.name=='Library')
    methods=[node for node in original.body if isinstance(node,ast.FunctionDef)and node.name in {'resolve','_pin'}]
    assert len(methods)==2
    shell=ast.ClassDef(name='Library',bases=[],keywords=[],body=methods,decorator_list=[],type_params=[])
    context={'Path':Path,'paths':paths,'re':re,'artifacts':types.SimpleNamespace(file_hash=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest())}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[shell],type_ignores=[])),str(file),'exec'),context)
    library=context['Library']();library.root=root or project/'library'
    return library


class InitializedPolicy(unittest.TestCase):
    def fixture(self):
        from swdb.dx100_initialized_register_model import ENTRY
        from swdb.dx100_size_source import SOURCE_PINS
        project=Path(__file__).parents[1]
        pins=[{'root':'project','path':('apps/dx100/benchmarks/API/'+name if name in {'MAA.hpp','MAA_gem5.hpp'}
               else 'tests/fixtures/proof/dx100/gem5-e4fc4af/'+name),'sha256':digest}for name,digest in SOURCE_PINS.items()]
        return real_resolution_library(project),{'kind':'dx100-initialized-u32-register-v1','call':'get_new_reg','entry':dict(ENTRY),'sources':pins}

    def test_source_policy_requires_the_distinct_original_u32_entry_and_all_sources(self):
        from swdb import dx100_initialized_register_source as source
        from swdb.dx100_initialized_register_model import ENTRY
        from swdb.dx100_size_source import SOURCE_PINS
        project=Path(__file__).parents[1]
        pins=[]
        for name,digest in SOURCE_PINS.items():
            relative=('apps/dx100/benchmarks/API/'+name if name in {'MAA.hpp','MAA_gem5.hpp'}
                      else 'tests/fixtures/proof/dx100/gem5-e4fc4af/'+name)
            pins.append({'root':'project','path':relative,'sha256':digest})
        definition={'kind':'dx100-initialized-u32-register-v1','call':'get_new_reg',
                    'entry':dict(ENTRY),'sources':pins}
        admitted=source.policy(real_resolution_library(project),definition)
        self.assertNotIn('refused',admitted)
        self.assertEqual(admitted['kind'],'dx100-initialized-u32-register-v1')
        self.assertEqual(admitted['call'],'get_new_reg')
        self.assertEqual(admitted['entry']['host_counter_objects'],
                         'REG_count, SPD_count and region_count are disjoint from the configured scalar MMIO range')
        self.assertEqual(len(admitted['sources']),7)
        self.assertEqual(admitted['termination_policy'],'conditional normal return; no hardware liveness')

    def test_closed_semantics_keep_prewrite_capacity_and_refuse_type_overload_or_model_changes(self):
        from swdb import dx100_initialized_register_source as source
        from swdb.dx100_initialized_register_model import OWNER,STATEMENT,PROTOTYPES,CONTRACTS,STATE,MODEL
        library,definition=self.fixture()
        rows=[]
        for name in ('init_MAA','get_new_reg','get_reg'):
            selected={**copy.deepcopy(definition),'call':name}
            v={'prototype':PROTOTYPES[name],'contract':CONTRACTS[name],'definition':selected}
            row={'call':name,'supported':True,'rules':['register_scope','register_source']}
            if name=='init_MAA':row.update(v)
            else:
                v.update(arguments=['unsigned int'],arity=1)
                if name=='get_new_reg':v['declaration']='inline int get_new_reg(T1 data)'
                row['instances']=[v]
                if name=='get_new_reg':row['instances'].append({'arguments':['unsigned int'],'arity':0,'declaration':'inline int get_new_reg()','prototype':'int get_new_reg_unsigned_int_args0(void)','contract':r'requires \false; assigns \nothing;'})
            rows.append(row)
        data={'id':source.SEMANTICS_ID,'model':{'layout':'dx100-initialized-u32-register-partial-v1'},'calls':rows,
              'rules':[{'id':'register_scope','statement':STATEMENT,'assumed':{'owner':OWNER},'record_assumption':True}]}
        texts={'model.state':STATE,'model.c':MODEL,'model.logic':'/* No added axioms. */\n','ghost.acsl':'/* Ordinary register-word projection. */\n'}
        errors=[]
        self.assertTrue(source.check(library,data,texts,lambda *e:errors.append(e)),errors)
        self.assertEqual(CONTRACTS['get_new_reg'].split(';')[0],'requires 0 <= REG_count <= 31')
        for change in ('u64','args0','model','new_premise','unknown_entry','counter_alias','cloned_semantics'):
            with self.subTest(change=change):
                d=copy.deepcopy(data);t=dict(texts);variant=d['calls'][1]['instances'][0]
                if change=='u64':variant['arguments']=['unsigned long long']
                elif change=='args0':variant['arity']=0
                elif change=='model':t['model.c']=t['model.c'].replace('__swdb_dx_reg_words[old]=data','__swdb_dx_reg_words[0]=data')
                elif change=='new_premise':variant['contract']=variant['contract'].replace('requires 0 <= REG_count <= 31;','requires REG_count == 0;')
                elif change=='unknown_entry':variant['definition']['entry']['core']=True
                elif change=='counter_alias':variant['definition']['entry']['host_counter_objects']='counter may alias MMIO'
                else:d['id']='semantics.dx100_initialized_register_current_clone_0_2'
                refused=[]
                self.assertFalse(source.check(library,d,t,lambda *e:refused.append(e)))
                self.assertTrue(refused)

    def test_partial_unit_requires_its_distinct_policy_and_physical_semantics_pin(self):
        from swdb import dx100_initialized_register_source as source
        with tempfile.TemporaryDirectory(prefix='initialized-policy-')as folder:
            path=Path(folder)/'semantics.json';data={'id':source.SEMANTICS_ID,'model':{'layout':'dx100-initialized-u32-register-partial-v1'}}
            path.write_text(json.dumps(data));ident='semantics.dx100_initialized_register_fixture_0_2'
            class Library:
                files={ident:path}
                def get(self,name):return data if name==ident else None
            policy={'kind':'partial-normal-return-v1','source_policy':'dx100-initialized-u32-register-v1',
                    'semantics':{'id':ident,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}
            entry={'id':'contract.dx100_initialized_register_partial_fixture.v1','version':'0.1',
                   'proof_unit':{'function':'trust_fixture','correctness_policy':policy}}
            self.assertEqual(source.unit_policy(Library(),entry),policy)
            for changed in (None,[],True,dict(policy,kind='total'),dict(policy,source_policy='dx100-u32-register-v1'),
                            dict(policy,semantics={'id':ident,'sha256':'0'*64})):
                with self.subTest(policy=changed):
                    wrong=copy.deepcopy(entry);wrong['proof_unit']['correctness_policy']=changed
                    with self.assertRaises(source.Refused):source.unit_policy(Library(),wrong)

    def test_source_policy_refuses_linked_source_even_when_the_target_bytes_match(self):
        from swdb import dx100_initialized_register_source as source
        library,definition=self.fixture()
        with tempfile.TemporaryDirectory(prefix='initialized-linked-source-')as folder:
            target=library.resolve(definition['sources'][0]).resolve()
            root=Path(folder).resolve();physical=root/'physical';physical.mkdir()
            (physical/target.name).write_bytes(target.read_bytes());library.root=root
            direct=copy.deepcopy(definition)
            direct['sources'][0].update(root='library',path='physical/'+target.name)
            self.assertNotIn('refused',source.policy(library,direct))
            (root/'file-alias').mkdir();(root/'file-alias'/target.name).symlink_to(physical/target.name)
            (root/'directory-alias').symlink_to(physical,target_is_directory=True)
            for alias in ['file-alias','directory-alias']:
                with self.subTest(alias=alias):
                    changed=copy.deepcopy(direct);changed['sources'][0]['path']=alias+'/'+target.name
                    self.assertEqual(library.resolve(changed['sources'][0]),physical/target.name)
                    self.assertIn('refused',source.policy(library,changed))


if __name__=='__main__':unittest.main()
