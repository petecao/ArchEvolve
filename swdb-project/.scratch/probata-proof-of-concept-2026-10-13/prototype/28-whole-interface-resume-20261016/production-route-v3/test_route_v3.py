"""Exact V2 role-confusion RED / V3 role-bound bytes GREEN, without children."""
import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import runpy
import stat
import tempfile
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent
PREVIOUS=runpy.run_path(str(HERE/'test_route_v2.py'),run_name='route_v2_controls')
BASE=PREVIOUS['BASE']


class RouteV3(PREVIOUS['RouteV2']):
    def test_library_backed_context_real_level_and_handoff_red_green(self):
        extract=BASE['extracted'];producer=HERE/'proposed/swdb/proof_semantics.py'
        receiver_tree=ast.parse((HERE/'proposed/swdb/_dx100_whole/receiver_state_draws_v2.py').read_text())
        premises=next(ast.literal_eval(n.value) for n in receiver_tree.body if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='PREMISES' for t in n.targets))
        context=[{'rule':name,'statement':statement,'owner':'Trace context owner','record_assumption':True}
                 for name,statement in sorted(premises.items())]
        rules=[{'id':'whole_context_'+row['rule'].replace('-','_'),'statement':row['statement']+' Owner: '+row['owner']+'.',
                'assumed':{'owner':row['owner']},'record_assumption':True}for row in context]
        data={'id':'semantics.checked','rules':rules}
        class Failure(ValueError):pass
        imports={('swdb.proof',('AdapterError',)):SimpleNamespace(AdapterError=Failure)}
        record_ns={'artifacts':SimpleNamespace(file_hash=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()),
            'yamlio':SimpleNamespace(load=lambda p:json.loads(Path(p).read_bytes())),
            'yaml':SimpleNamespace(YAMLError=ValueError),
            '__builtins__':dict(vars(__import__('builtins')),__import__=PREVIOUS['inert_import'](imports))}
        extract(producer,{'record_assumptions'},record_ns)
        with tempfile.TemporaryDirectory(dir=HERE,prefix='assumption-control-') as temporary:
            entry=Path(temporary).resolve()/'semantics.json';entry.write_text(json.dumps(data))
            physical=hashlib.sha256(entry.read_bytes()).hexdigest()
            library=SimpleNamespace(get=lambda ident:data,files={'semantics.checked':entry},content_sha256=lambda _:'a'*64)
            unit=BASE['unit'](self.source)
            object.__setattr__(unit,'selection',SimpleNamespace(library=library,entry_id='semantics.checked'))
            object.__setattr__(unit,'certificate_json',json.dumps({'semantics_entry_file':{'sha256':physical},
                'recorded_context_assumptions':context}).encode())
            source_ns=dict(self.source,receiver=SimpleNamespace(PREMISES=premises))
            source_ns['__builtins__']=dict(vars(__import__('builtins')),__import__=PREVIOUS['inert_import']({
                    ('swdb',('proof_semantics',)):SimpleNamespace(proof_semantics=SimpleNamespace(**record_ns))}))
            extract(HERE/'proposed/swdb/dx100_checked_source.py',{'bind_context_rules','record_assumptions'},source_ns)
            rows=source_ns['record_assumptions'](unit)
            self.assertEqual(len(rows),6)
            self.assertTrue(all(row['sentence'].endswith(' Owner: Trace context owner.') for row in rows))
            self.assertTrue(all(r['kind']=='proof_semantics' and '#whole_context_' in r['reference']['id']
                and r['reference']['sha256']==physical for r in rows))
            handoff_file=HERE.parents[4]/'swdb/handoff_level.py';tree=ast.parse(handoff_file.read_text())
            handoff={'re':re,'Failure':Failure}
            for node in tree.body:
                if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'TEMPLATES','REFERENCE_ID'} for t in node.targets):
                    exec(compile(ast.Module([node],type_ignores=[]),str(handoff_file),'exec'),handoff)
            extract(handoff_file,{'_sentence','_assumptions'},handoff)
            old=dict(self.source)
            extract(HERE.parent/'production-route-v2/proposed/swdb/dx100_checked_source.py',{'record_assumptions'},old)
            with self.assertRaises(Failure):handoff['_assumptions'](old['record_assumptions'](unit),library)
            # Actual candidate-level aggregation, with an inert counting record/status.
            level_file=HERE.parents[4]/'swdb/level_rule.py';level_tree=ast.parse(level_file.read_text())
            level={'snapshot':lambda level,records:{'level':level,'records':records}}
            for node in level_tree.body:
                if isinstance(node,ast.Assign):exec(compile(ast.Module([node],type_ignores=[]),str(level_file),'exec'),level)
            extract(level_file,{'rank','bounds_level','smallest','is_baseline_measurement'},level)
            original=next(n for n in level_tree.body if isinstance(n,ast.ClassDef) and n.name=='Rule')
            methods=[n for n in original.body if getattr(n,'name',None) in {'level','_assumptions','_checked_method_part','_refuted'}]
            cls=ast.ClassDef(name='Rule',bases=[],keywords=[],body=methods,decorator_list=[])
            exec(compile(ast.fix_missing_locations(ast.Module([cls],type_ignores=[])),str(level_file),'exec'),level)
            rule=level['Rule']();rule.proofs={'proof.1':{'id':'proof.1','subject':{'kind':'candidate_proof_unit','candidate':'candidate.1'},
                'pins':{'contract':{'id':'unit.first'}},'route':'cbmc','verdict':'proven','assumptions':rows}}
            rule.status=lambda _:{'counts':True,'bounds':{'threads':1},'caps':[],'uses':[],'stale':[],'below_minimum':[]}
            result=rule.level('candidate.1','certified',{'unit.first'})
            self.assertEqual(result['level'],'proven_within_bounds_threads_1')
            self.assertEqual(result['proven']['bounds'],{'threads':1})
            rendered=handoff['_assumptions'](result['assumptions'],library)
            self.assertEqual(len(rendered),6)
            for row in rendered:
                fragment=row['reference']['id'].split('#')[1]
                owned=next(rule for rule in data['rules'] if rule['id']==fragment)
                self.assertEqual(owned['assumed']['owner'],'Trace context owner')
                self.assertTrue(owned['statement'].endswith(' Owner: Trace context owner.'))
            for change in ('missing','owner','statement','record'):
                altered=json.loads(json.dumps(data))
                if change=='missing':altered['rules'].pop()
                elif change=='owner':altered['rules'][0]['assumed']['owner']='Other owner'
                elif change=='statement':altered['rules'][0]['statement']='Different premise'
                else:altered['rules'][0]['record_assumption']=False
                with self.assertRaises(self.source['Refused']):source_ns['bind_context_rules'](altered,context)

    def test_role_confusion_red_green_and_physical_input_shape(self):
        tree=ast.parse((HERE.parent/'production-route-v2/proposed/swdb/dx100_checked_adapter.py').read_text())
        old=next(n for n in tree.body if getattr(n,'name',None)=='check_launch')
        at=next(i for i,n in enumerate(old.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='allowed' for t in n.targets))
        body=old.body[at:at+2]
        self.assertIsInstance(body[1],ast.For)
        signature=ast.arguments(posonlyargs=[],args=[ast.arg(arg='context'),ast.arg(arg='inputs')],kwonlyargs=[],kw_defaults=[],defaults=[])
        fn=ast.FunctionDef(name='old_gate',args=signature,body=body,decorator_list=[])
        expected={'c':'/* checked generated C */\n','cxx':'/* source-preserving C++ */\n'}
        ns={'Path':Path,'source':SimpleNamespace(need=self.source['need']),'texts':lambda _:expected}
        exec(compile(ast.fix_missing_locations(ast.Module([fn],type_ignores=[])),'actual_v2_gate','exec'),ns)
        receiver={'Path':Path,'stat':stat,'hashlib':hashlib,'re':re,'dataclass':dataclass}
        BASE['extracted'](HERE/'proposed/swdb/_dx100_whole/receiver_state_draws_v2.py',
            {'Refused','need','digest','Pin','stable_metadata','check_file'},receiver)
        green={'Path':Path,'hashlib':hashlib,'source':SimpleNamespace(need=self.source['need'],receiver=SimpleNamespace(**receiver))}
        BASE['extracted'](HERE/'proposed/swdb/dx100_checked_adapter.py',{'check_role_inputs'},green)
        with tempfile.TemporaryDirectory(dir=HERE,prefix='role-control-') as temporary:
            root=Path(temporary).resolve(); c=root/'job.c'; cpp=root/'replay.cc'
            c.write_text(expected['c']);cpp.write_text(expected['cxx'])
            green['check_role_inputs'](expected,[('c',c),('cxx',cpp)])
            cpp.write_text(expected['c'])
            ns['old_gate']({},[(cpp,cpp.read_text())])  # reproduced exact V2 self-claim acceptance
            with self.assertRaises(receiver['Refused']):green['check_role_inputs'](expected,[('cxx',cpp)])
            cpp.write_text(expected['cxx'])
            with self.assertRaises(receiver['Refused']):green['check_role_inputs'](expected,[('c',cpp)])
            with self.assertRaises(self.source['Refused']):green['check_role_inputs'](expected,[('cpp',cpp)])
            linked=root/'alias.c';linked.symlink_to(c)
            with self.assertRaises(receiver['Refused']):green['check_role_inputs'](expected,[('c',linked)])


if __name__=='__main__':unittest.main(verbosity=2)
