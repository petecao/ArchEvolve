"""2026-10-16 ET. Pure source9 metadata controls, no observer main or tools."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
POC=HERE.parents[2]
EVENTS=[]
def audit(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('source9 pure controls forbid children/native/network')
    if event=='import' and str(args[0]).split('.')[0]=='swdb':
        EVENTS.append(event)
        raise RuntimeError('source9 controls forbid project imports')
sys.addaudithook(audit)
S={}
exec(compile((HERE/'semantic_terms.py').read_bytes(),'<inert-source9-terms>','exec'),S)
CONTEXT=json.loads((HERE/'context.json').read_bytes())
EXPECTED=json.loads((HERE/'expected.frozen.json').read_bytes())

class Controls(unittest.TestCase):
    def test_all_nine_independent_complete_source_statements(self):
        rows=EXPECTED['canonical_manifest']['obligations']
        self.assertEqual([r['id'] for r in rows],list(S['CONCLUSIONS']))
        self.assertEqual(len(rows),9)
        for row in rows:
            self.assertEqual(S['source_statement'](row['id']),row['statement'])
            self.assertEqual(row['dependencies'],[])
            term=S['source_goal'](row['id'])
            binders=term[1][1]
            self.assertEqual(len(binders),8 if row['id'].startswith('move.') else 12)
            self.assertEqual(len(term[1][2][1])-1,6 if row['id'].startswith('move.') else 8)
            self.assertEqual(len({r[0]for r in binders}),len(binders))
            self.assertTrue(S['required_definitions'](row['id']))

    def test_complete_independent_definition_terms_parse(self):
        self.assertEqual(len(S['DEFINITIONS']),24)
        for name,(bindings,body) in S['DEFINITIONS'].items():
            S['one']('(forall ('+bindings+') '+body+')')
        self.assertEqual(sum(k.startswith('E_')for k in S['DEFINITIONS']),14)
        self.assertEqual(sum(k.startswith('O_')for k in S['DEFINITIONS']),10)

    def test_alpha_and_let_keep_binding_scope(self):
        for left,right in [('(forall ((x Int)) (= x x))','(forall ((renamed Int)) (= renamed renamed))'),
            ('(let ((t 4)) (forall ((x Int)) (= x t)))','(forall ((q Int)) (= q 4))')]:
            self.assertEqual(S['ordered_alpha'](S['one'](left)),S['ordered_alpha'](S['one'](right)))
        left=S['one']('(forall ((x Int)) (forall ((y Int)) (forall ((x Int)) (forall ((z Int)) (= x z)))))')
        right=S['one']('(forall ((x Int)) (forall ((y Int)) (forall ((x Int)) (forall ((z Int)) (= x x)))))')
        self.assertNotEqual(S['ordered_alpha'](left),S['ordered_alpha'](right))

    def test_mutated_or_dropped_full_premise_never_matches(self):
        for ident in S['CONCLUSIONS']:
            original=S['source_goal'](ident)
            changed=json.loads(json.dumps(original));changed[1][2][1].pop()
            self.assertFalse(S['compare'](changed,original)[0])
            changed=json.loads(json.dumps(original));changed[1][2][2]='true'
            self.assertFalse(S['compare'](changed,original)[0])

    def test_task_never_adopts_unknown_encoding_or_sibling_premise(self):
        goal=S['source_goal']('move.source_empty')
        def wire(value):return value if isinstance(value,str)else '('+' '.join(wire(v)for v in value)+')'
        text='(set-logic ALL)\n(assert '+wire(goal)+')\n(check-sat)\n(get-info :reason-unknown)\n'
        result=S['task_semantics'](text,'move.source_empty',{})
        self.assertTrue(result['goal_equivalent'])
        self.assertFalse(result['scientific_acceptance'])
        self.assertFalse(result['source_type_semantics_established'])
        self.assertTrue(result['unresolved'])
        with self.assertRaises(ValueError):S['task_semantics']('(assert P_t25_old)\n'+text,'move.source_empty',{})
        with self.assertRaises(ValueError):S['task_semantics'](text+'(check-sat)','move.source_empty',{})
        with self.assertRaises(ValueError):S['task_semantics'](text+'(get-model)','move.source_empty',{})

    def test_all_26_physical_tasks_and_original_timeout_retained(self):
        self.assertEqual(len(CONTEXT['task_artifacts']),26)
        counts={ident:0 for ident in S['CONCLUSIONS']}
        for row in CONTEXT['task_artifacts']:
            matched=[ident for ident in counts if '/leaf-'+ident+'/'in row['relative']]
            self.assertEqual(len(matched),1);counts[matched[0]]+=1
        self.assertEqual(counts,{ident:6 if ident.endswith('owner_correspondence')else 2 for ident in counts})
        self.assertFalse(CONTEXT['all_nine_producer_proven'])
        self.assertEqual(CONTEXT['settlement']['lease_generation'],623)
        self.assertEqual(CONTEXT['settlement']['ended_utc'],'2026-10-16T22:45:42Z')

    def test_full_source_and_canonical_pins(self):
        self.assertEqual(len(EXPECTED['canonical_files']),29)
        self.assertEqual(CONTEXT['canonical_manifest'],EXPECTED['canonical_manifest'])
        for name,row in CONTEXT['source_theories'].items():
            self.assertEqual(hashlib.sha256((HERE/name).read_bytes()).hexdigest(),row['sha256'])
        self.assertEqual(sum(row['kind']=='regular'for row in CONTEXT['raw_manifest']),188)
        self.assertEqual(sum(row.get('bytes',0)for row in CONTEXT['raw_manifest']),21450336)

    def test_original_read_source_runtime_helpers_exact(self):
        old=ast.parse((POC/'prototype/25-owned-transfer-20261016/cold-g621-v3/observer.py').read_bytes())
        current=ast.parse((HERE/'observer.py').read_bytes())
        for name in ('need','sha','compact','digest','identity','physical','read_bytes','pin','read','walk','git','audit','runtime','source_closure','strip_comments','normal_flags','resolved_command'):
            a=next(n for n in old.body if isinstance(n,ast.FunctionDef)and n.name==name)
            b=next(n for n in current.body if isinstance(n,ast.FunctionDef)and n.name==name)
            self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))
        prior=ast.parse((POC/'prototype/25-owned-transfer-20261016/cold-g621-encoding-v1/semantic_terms.py').read_bytes())
        tree=ast.parse((HERE/'semantic_terms.py').read_bytes())
        for name in ('need','digest','forms','substitute','symbols','canon','one'):
            a=next(n for n in prior.body if isinstance(n,ast.FunctionDef)and n.name==name)
            b=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name==name)
            self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))
        self.assertEqual(EVENTS,[])

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_native_network_or_project_events':EVENTS,'observer_main_or_remote_or_scientific_execution':False},sort_keys=True))
    raise SystemExit(not result.wasSuccessful()or bool(EVENTS))
