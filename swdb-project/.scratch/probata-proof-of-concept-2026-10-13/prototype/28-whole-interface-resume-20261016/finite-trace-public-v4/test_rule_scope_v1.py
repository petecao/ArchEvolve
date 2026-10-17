"""2026-10-16 Eastern. Fixed scope/actual record and render source controls only."""
import ast
import builtins
import copy
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from zoneinfo import ZoneInfo

HERE=Path(__file__).resolve().parent
PACKAGE=HERE/'proposed/swdb/_dx100_finite'
def audit(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:raise AssertionError('no child/native/network in rule scope controls')
sys.addaudithook(audit)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
def extract(path,names,ns):
    nodes=[n for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert {n.name for n in nodes}==set(names);exec(compile(ast.Module(nodes,type_ignores=[]),str(path),'exec'),ns);return ns
S=load('_fixed_context_scope',PACKAGE/'context_rule_scope_v1.py')
P=load('_scope_invariant_entry',HERE.parent/'finite-entry-rules-v1/entry_rules_v1.py')
E=load('_scope_closed_events',PACKAGE/'event_plan_v2.py')
def make_entry():
    common=[dict(id=name,statement=text,assumed=dict(owner='Eric' if name in S.TRUST else 'Existing compiler/numeric owner'),record_assumption=True) for name,text in {**S.TRUST,**S.OWNED}.items()]
    common += [dict(id='whole_context_'+name.replace('-','_'),statement=text+' Owner: Existing source harness.',assumed=dict(owner='Existing source harness'),record_assumption=True) for name,text in sorted(S.SOURCE_CONTEXT.items())]
    base=dict(id='semantics.finite_selected',kind='proof_semantics',target='dx100-mmio',version='0.2',sequence=2,formal_frame=1,
        contract_form='dx100-whole-interface-checked-body-1',rules=common,fixture_only=True)
    return json.loads(P.prepare(P.canonical(base)).entry_json)
def generic_records(entry,entry_sha):
    return [dict(kind='proof_semantics',reference=dict(id=entry['id']+'#'+row['id'],sha256=entry_sha),sentence=row['statement']) for row in entry['rules'] if row.get('record_assumption') is True]

class Controls(unittest.TestCase):
    def test_one_physical_entry_two_closed_scopes_shared_trust_always_retained(self):
        entry=make_entry();entry_sha=hashlib.sha256(S.canonical(entry)).hexdigest();normal=generic_records(entry,entry_sha)
        before=copy.deepcopy(normal)
        for method,count,own,other in ((S.source,13,S.SOURCE_IDS,S.FINITE_IDS),(S.finite,14,S.FINITE_IDS,S.SOURCE_IDS)):
            selected,receipt=method(entry,normal,entry['id'],entry_sha)
            ids={row['reference']['id'].split('#')[1] for row in selected}
            self.assertEqual(len(selected),count);self.assertTrue(S.COMMON_IDS|own<=ids);self.assertFalse(ids&other)
            self.assertEqual(receipt['entry'],dict(id=entry['id'],sha256=entry_sha));self.assertFalse(receipt['truth_granted'])
            self.assertEqual(receipt['selected_records_sha256'],S.sha(selected));self.assertEqual(normal,before)
            self.assertTrue(all(row['reference']['sha256']==entry_sha for row in selected))
        # Additional unrelated recorded evidence is retained by both branches.
        entry['rules'].append(dict(id='extra_retained_evidence',statement='Synthetic unrelated evidence remains recorded.',assumed={'owner':'Synthetic evidence owner'},record_assumption=True))
        normal=generic_records(entry,entry_sha)
        for method in (S.source,S.finite):self.assertIn('extra_retained_evidence',method(entry,normal,entry['id'],entry_sha)[1]['selected_rule_ids'])

    def test_wrong_hash_partial_owner_unknown_or_caller_filtered_records_refuse(self):
        base=make_entry();digest='1'*64
        for mutation in ('missing_common','wrong_Eric','partial_finite','unknown_source','unknown_finite','unknown_logical','wrong_finite_owner','wrong_source_statement'):
            entry=copy.deepcopy(base)
            if mutation=='missing_common':entry['rules'].pop(0)
            elif mutation=='wrong_Eric':entry['rules'][0]['assumed']['owner']='Changed owner'
            elif mutation=='partial_finite':entry['rules'].pop()
            elif mutation.startswith('unknown_'):
                name={'unknown_source':'whole_context_unreviewed','unknown_finite':'finite_context_unreviewed','unknown_logical':'finite_logical_unreviewed'}[mutation]
                entry['rules'].append(dict(id=name,statement='Unreviewed conflicting context.',assumed={'owner':'Fixture'},record_assumption=True))
            elif mutation=='wrong_finite_owner':entry['rules'][-1]['assumed']['owner']='Changed owner'
            else:next(row for row in entry['rules'] if row['id'] in S.SOURCE_IDS)['statement']='Changed source context'
            for method in (S.source,S.finite):
                with self.assertRaises(S.Refused,msg=mutation):method(entry,generic_records(entry,digest),entry['id'],digest)
        normal=generic_records(base,digest)
        for method in (S.source,S.finite):
            with self.assertRaises(S.Refused):method(base,normal,base['id'],'2'*64)
            with self.assertRaises(S.Refused):method(base,normal[:-1],base['id'],digest)
            changed=copy.deepcopy(normal);changed[0]['reference']['id']='other.entry#'+next(iter(S.COMMON_IDS))
            with self.assertRaises(S.Refused):method(base,changed,base['id'],digest)
            with self.assertRaises(TypeError):method(base,normal,base['id'],digest,excluded_ids=S.COMMON_IDS)
        # The existing SourceUnit-only 0.2 entry remains supported; no finite
        # family is fabricated. Its finite route must still refuse.
        original=dict(base,rules=[row for row in base['rules'] if row['id'] not in S.FINITE_IDS])
        self.assertEqual(len(S.source(original,generic_records(original,digest),original['id'],digest)[0]),13)
        with self.assertRaises(S.Refused):S.finite(original,generic_records(original,digest),original['id'],digest)

    def test_generic_recorder_bytes_unchanged_and_real_physical_reference_checks(self):
        previous=HERE.parent/'finite-trace-public-v2/proposed/swdb/proof_semantics.py'
        current=HERE/'proposed/swdb/proof_semantics.py';self.assertEqual(previous.read_bytes(),current.read_bytes())
        class Failure(ValueError):pass
        def imported(name,globals=None,locals=None,fromlist=(),level=0):
            if name=='swdb.proof':return SimpleNamespace(AdapterError=Failure)
            raise AssertionError('no project import: '+name)
        ns=dict(artifacts=SimpleNamespace(file_hash=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()),yamlio=SimpleNamespace(load=lambda p:json.loads(Path(p).read_bytes())),
            yaml=SimpleNamespace(YAMLError=ValueError),__builtins__=dict(vars(builtins),__import__=imported))
        extract(current,{'record_assumptions'},ns)
        with tempfile.TemporaryDirectory(dir=HERE,prefix='scope-physical-') as directory:
            path=Path(directory)/'entry.json';entry=make_entry();path.write_bytes(S.canonical(entry));digest=hashlib.sha256(path.read_bytes()).hexdigest()
            library=SimpleNamespace(get=lambda _:entry,files={entry['id']:path})
            normal=ns['record_assumptions'](library,entry['id'],digest);self.assertEqual(len(normal),20)
            self.assertEqual(len(S.source(entry,normal,entry['id'],digest)[0]),13)
            self.assertEqual(len(S.finite(entry,normal,entry['id'],digest)[0]),14)
            with self.assertRaises(Failure):ns['record_assumptions'](library,entry['id'],'2'*64)
            path.write_bytes(path.read_bytes()+b' ')
            with self.assertRaises(Failure):ns['record_assumptions'](library,entry['id'],digest)

    def test_real_level_and_handoff_render_both_typed_noncontradictory_scopes(self):
        source=HERE/'test_finite_public.py';tree=ast.parse(source.read_bytes());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Controls')
        original=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='test_normal_entry_rule_assumptions_do_not_cap_real_level_or_render')
        for route,count in (('source',13),('finite',14)):
            class Adapt(ast.NodeTransformer):
                def visit_Assign(self,node):
                    if any(isinstance(t,ast.Name) and t.id=='data' for t in node.targets):return ast.copy_location(ast.parse('data=make_entry()').body[0],node)
                    if any(isinstance(t,ast.Name) and t.id=='assumptions' for t in node.targets):
                        self.generic_visit(node)
                        node.value=ast.Call(func=ast.Attribute(value=ast.Name(id='S',ctx=ast.Load()),attr=route,ctx=ast.Load()),args=[ast.Name(id='data',ctx=ast.Load()),node.value,
                            ast.Subscript(value=ast.Name(id='data',ctx=ast.Load()),slice=ast.Constant('id'),ctx=ast.Load()),ast.Name(id='digest',ctx=ast.Load())],keywords=[])
                        node.value=ast.Subscript(value=node.value,slice=ast.Constant(0),ctx=ast.Load());return node
                    return self.generic_visit(node)
                def visit_Constant(self,node):return ast.copy_location(ast.Constant(count),node) if node.value==14 else node
            method=ast.fix_missing_locations(Adapt().visit(copy.deepcopy(original)))
            ns=dict(globals(),E=E)
            exec(compile(ast.Module([method],type_ignores=[]),str(source),'exec'),ns);ns[method.name](self)

    def test_receiver_scope_source_pin_and_exact_canonical_scope_agree(self):
        bridge=load('_scoped_finite_receiver',PACKAGE/'finite_owned_receiver_v4.py')
        row=bridge.rule_scope_pin();raw=Path(row['path']).read_bytes()
        self.assertEqual(len(raw),row['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
        captured=bridge.captured_rule_scope();entry=make_entry();normal=generic_records(entry,'1'*64)
        self.assertEqual(S.finite(entry,normal,entry['id'],'1'*64),captured.finite(entry,normal,entry['id'],'1'*64))

    def test_exact_SourceUnit_record_boundary_rejects_foreign_type_and_scope(self):
        class Failure(ValueError):pass
        class SourceUnit:pass
        def imported_record(name,globals=None,locals=None,fromlist=(),level=0):
            if name=='swdb.proof':return SimpleNamespace(AdapterError=Failure)
            raise AssertionError('no project import: '+name)
        generic=dict(artifacts=SimpleNamespace(file_hash=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()),yamlio=SimpleNamespace(load=lambda p:json.loads(Path(p).read_bytes())),
            yaml=SimpleNamespace(YAMLError=ValueError),__builtins__=dict(vars(builtins),__import__=imported_record))
        extract(HERE/'proposed/swdb/proof_semantics.py',{'record_assumptions'},generic)
        def imported_source(name,globals=None,locals=None,fromlist=(),level=0):
            if name=='swdb':return SimpleNamespace(proof_semantics=SimpleNamespace(record_assumptions=generic['record_assumptions']))
            raise AssertionError('no project import: '+name)
        ns=dict(SourceUnit=SourceUnit,need=E.need,canonical=S.canonical,context_scope=S,receiver=SimpleNamespace(PREMISES=S.SOURCE_CONTEXT),__builtins__=dict(vars(builtins),__import__=imported_source))
        extract(HERE/'proposed/swdb/dx100_checked_source.py',{'bind_context_rules','record_assumptions'},ns)
        with tempfile.TemporaryDirectory(dir=HERE,prefix='typed-source-record-') as directory:
            entry=make_entry();path=Path(directory)/'entry.json';path.write_bytes(S.canonical(entry));digest=hashlib.sha256(path.read_bytes()).hexdigest()
            library=SimpleNamespace(get=lambda _:entry,files={entry['id']:path});normal=generic['record_assumptions'](library,entry['id'],digest)
            unit=SourceUnit();unit.selection=SimpleNamespace(library=library,entry_id=entry['id'])
            unit.certificate=dict(semantics_entry_file={'sha256':digest},recorded_context_assumptions=[dict(rule=name,statement=text,owner='Existing source harness',record_assumption=True) for name,text in sorted(S.SOURCE_CONTEXT.items())],rule_scope=S.source(entry,normal,entry['id'],digest)[1])
            self.assertEqual(len(ns['record_assumptions'](unit)),13)
            unit.certificate['rule_scope']=S.finite(entry,normal,entry['id'],digest)[1]
            with self.assertRaises(E.Refused):ns['record_assumptions'](unit)
            with self.assertRaises(E.Refused):ns['record_assumptions'](SimpleNamespace(selection=unit.selection,certificate=unit.certificate))

if __name__=='__main__':unittest.main(verbosity=2)
