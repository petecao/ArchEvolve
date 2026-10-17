"""2026-10-16 Eastern. Pure metadata/real rule-render controls; no Library construction."""
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
FINITE=HERE.parent/'finite-trace-public-v2'
def audit(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:raise AssertionError('no child/native/network in entry metadata controls')
sys.addaudithook(audit)
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
P=load('_finite_invariant_rules',HERE/'entry_rules_v1.py')
def extract(path,names,ns):
    nodes=[n for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    assert {n.name for n in nodes}==set(names);exec(compile(ast.Module(nodes,type_ignores=[]),str(path),'exec'),ns);return ns
def base_entry():
    rows=[dict(id=name,statement=text,assumed=dict(owner='Eric' if name in P.TRUST else 'Existing compiler/numeric owner'),record_assumption=True) for name,text in {**P.TRUST,**P.OWNED}.items()]
    rows += [dict(id='whole_context_'+name.replace('-','_'),statement=text+' Owner: Existing source harness.',assumed=dict(owner='Existing source harness'),record_assumption=True) for name,text in sorted(P.SOURCE_CONTEXT.items())]
    return dict(id='semantics.finite_selected',kind='proof_semantics',target='dx100-mmio',version='0.2',sequence=2,formal_frame=1,contract_form='dx100-whole-interface-checked-body-1',rules=rows,
        checked_body={'fixture_only':'unchanged'},calls=['unchanged fixture marker'],not_a_Library_or_authority=True)

class Controls(unittest.TestCase):
    def test_append_seven_exact_invariants_preserves_all_existing_metadata(self):
        base=base_entry();raw=json.dumps(base,indent=2).encode();out=P.prepare(raw);entry=json.loads(out.entry_json);cert=json.loads(out.certificate_json)
        self.assertEqual(entry['rules'][:-7],base['rules']);self.assertEqual(entry['rules'][-7:],P.appended_rules())
        self.assertEqual({k:v for k,v in entry.items() if k!='rules'},{k:v for k,v in base.items() if k!='rules'})
        self.assertEqual(cert['original']['sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual(cert['appended_rule_count'],7)
        self.assertEqual(cert['finite_generic_owner'],'ticket28 synthetic fixture harness')
        self.assertTrue(cert['source_and_finite_scopes_must_not_be_read_as_unqualified_same_prestate'])
        self.assertFalse(cert['receiver_truth_or_ownership_grant']);self.assertFalse(cert['actual_Library_or_public_acceptance'])

    def test_append_inverse_and_all_origins_exact(self):
        base=base_entry();entry=json.loads(P.prepare(P.canonical(base)).entry_json);entry['rules']=entry['rules'][:-7]
        self.assertEqual(P.canonical(entry),P.canonical(base))
        for row in P.SOURCE_PINS.values():
            raw=Path(row['path']).read_bytes();self.assertEqual(len(raw),row['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
        ns={'need':P.need}
        finite=P.SOURCE_PINS['finite_receiver'];tree=ast.parse(Path(finite['path']).read_bytes())
        for n in tree.body:
            if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RULE_STATEMENTS' for t in n.targets):exec(compile(ast.Module([n],type_ignores=[]),finite['path'],'exec'),ns)
        extract(Path(finite['path']),{'rule_rows'},ns)
        self.assertEqual(P.appended_rules()[:-1],ns['rule_rows'](P.OWNER))
        core=P.SOURCE_PINS['finite_core'];ns.update(LOGICAL_RULE=P.LOGICAL_RULE,LOGICAL_STATEMENT=P.LOGICAL_STATEMENT)
        extract(Path(core['path']),{'logical_rule'},ns);self.assertEqual(P.appended_rules()[-1],ns['logical_rule'](P.OWNER))

    def test_duplicate_reserved_missing_or_changed_rules_refuse(self):
        mutations=[]
        for change in ('duplicate','missing_trust','missing_context','wrong_Eric','changed_statement','already_appended','unknown_finite','float_frame','bool_sequence'):
            base=base_entry()
            if change=='duplicate':base['rules'].append(copy.deepcopy(base['rules'][0]))
            elif change=='missing_trust':base['rules'].pop(0)
            elif change=='missing_context':base['rules'].pop()
            elif change=='wrong_Eric':base['rules'][0]['assumed']['owner']='Unselected owner'
            elif change=='changed_statement':base['rules'][-1]['statement']='Unreviewed replacement'
            elif change=='already_appended':base['rules']+=P.appended_rules()
            elif change=='unknown_finite':base['rules'].append(dict(id='finite_context_unreviewed'))
            elif change=='float_frame':base['formal_frame']=1.0
            else:base['sequence']=True
            with self.assertRaises(P.Refused,msg=change):P.prepare(P.canonical(base))
        with self.assertRaises(P.Refused):P.prepare(b'{"rules":[],"rules":[]}')

    def test_generic_rules_do_not_embed_selected_context_or_fact_hashes(self):
        rows=P.appended_rules();self.assertEqual(len({x['id'] for x in rows}),7)
        for row in rows:
            self.assertEqual(set(row),{'id','statement','assumed','record_assumption'})
            self.assertEqual(row['assumed'],{'owner':P.OWNER});self.assertIs(row['record_assumption'],True)
            self.assertIsNone(re.search(r'[0-9a-f]{64}',row['statement']))
        altered=base_entry();altered['synthetic_distinct_context_marker']='second unrelated fixture metadata'
        self.assertEqual(json.loads(P.prepare(P.canonical(altered)).entry_json)['rules'][-7:],rows)

    def test_real_record_level_and_handoff_keep_all_twenty_uncapped_rules(self):
        # Reuse the reviewed control's actual extracted production functions.
        # Only its synthetic entry and expected rule count change; temp files
        # stay in this owned directory. No actual swdb import or Library runs.
        source=FINITE/'test_finite_public.py';tree=ast.parse(source.read_bytes())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Controls')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='test_normal_entry_rule_assumptions_do_not_cap_real_level_or_render')
        class Adapt(ast.NodeTransformer):
            def visit_Assign(self,node):
                if any(isinstance(t,ast.Name) and t.id=='data' for t in node.targets):
                    return ast.copy_location(ast.parse('data=json.loads(P.prepare(P.canonical(base_entry())).entry_json)').body[0],node)
                return self.generic_visit(node)
            def visit_Constant(self,node):
                return ast.copy_location(ast.Constant(20),node) if node.value==14 else node
            def visit_Call(self,node):
                self.generic_visit(node)
                if isinstance(node.func,ast.Attribute) and node.func.attr=='TemporaryDirectory':
                    for keyword in node.keywords:
                        if keyword.arg=='dir':keyword.value=ast.Name(id='OWN_HERE',ctx=ast.Load())
                return node
        method=ast.fix_missing_locations(Adapt().visit(copy.deepcopy(method)))
        E=load('_finite_rule_level_events',FINITE/'proposed/swdb/_dx100_finite/event_plan_v2.py')
        ns=dict(globals(),HERE=FINITE,PACKAGE=FINITE/'proposed/swdb/_dx100_finite',OWN_HERE=HERE,E=E)
        exec(compile(ast.Module([method],type_ignores=[]),str(source),'exec'),ns)
        ns[method.name](self)

if __name__=='__main__':unittest.main(verbosity=2)
