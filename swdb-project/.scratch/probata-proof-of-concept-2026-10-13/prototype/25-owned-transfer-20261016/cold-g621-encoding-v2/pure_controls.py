"""2026-10-16 ET. No-child synthetic encoding and exact-delta controls."""
import ast
import copy
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
ATTEMPTS=[]


def block(event,args):
    if event=='subprocess.Popen' or event.startswith('socket.') or event in {'os.system','os.posix_spawn','os.exec','os.fork','ctypes.dlopen'}:
        ATTEMPTS.append(event)
        raise RuntimeError('pure controls forbid child/native/network')


sys.addaudithook(block)
ns={'__name__':'_pure'}
for name in ('semantic_terms.py','encoding_probe.py','observer.py'):
    exec(compile((HERE/name).read_text(),str(HERE/name),'exec'),ns)
old={'__name__':'_pure_old'}
exec(compile((HERE.parent/'cold-g621-v3/semantic_terms.py').read_text(),'<old>','exec'),old)


def term(value):
    return ns['one'](value)


def canonical(value):
    return ns['canon'](term(value))


SCHEMA=term('(declare-datatypes ((state 0)) (((state_builder (active (Array Int Bool)) (backing (Array Int Int))))))')
FALSE=term('(forall ((i Int)) (= (select fc i) false))')
ZERO=term('(forall ((i Int)) (= (select fc1 i) 0))')
DECLS=[term('(declare-fun fc () (Array Int Bool))'),term('(declare-fun fc1 () (Array Int Int))')]
HASHES={'false':ns['digest'](FALSE),'zero':ns['digest'](ZERO)}


class Controls(unittest.TestCase):
    def test_original_failure_then_corrected_binder_depth(self):
        left='(let ((a 0)) (forall ((x Int)) (= x a)))';right='(forall ((y Int)) (= y 0))'
        self.assertNotEqual(old['canon'](old['one'](left)),old['canon'](old['one'](right)))
        self.assertEqual(canonical(left),canonical(right))

    def test_wrappers_and_nested_binders(self):
        self.assertEqual(canonical('(and p (forall ((x Int)) (exists ((y Int)) (= x y))))'),
                         canonical('(and (let ((c 0)) (forall ((a Int)) (exists ((b Int)) (= b a)))) p)'))

    def test_free_variable_is_not_captured(self):
        self.assertEqual(canonical('(let ((a x)) (forall ((x Int)) (= x a)))'),
                         canonical('(forall ((y Int)) (= y x))'))
        self.assertNotEqual(canonical('(forall ((y Int)) (= y x))'),canonical('(forall ((y Int)) (= y y))'))

    def test_different_scope_and_types_remain_distinct(self):
        self.assertNotEqual(canonical('(forall ((x Int)) (exists ((y Int)) (= x y)))'),
                            canonical('(exists ((x Int)) (forall ((y Int)) (= x y)))'))
        self.assertNotEqual(canonical('(forall ((x Int)) (= x 0))'),canonical('(forall ((x Real)) (= x 0))'))

    def test_schema_exact_product(self):
        row=ns['record_schema']([SCHEMA]);self.assertTrue(row['matching']);self.assertEqual(row['constructor'],'state_builder')
        for value in [SCHEMA+[[]],term('(declare-datatypes ((state 0)) (((state_builder (active (Array Int Int)) (backing (Array Int Int))))))'),
                      term('(declare-datatypes ((state 0)) (((state_builder (backing (Array Int Int)) (active (Array Int Bool))))))')]:
            self.assertFalse(ns['record_schema']([value])['matching'])
        self.assertFalse(ns['record_schema']([SCHEMA,SCHEMA])['matching'])

    def test_constant_map_full_quantified_formula(self):
        commands=DECLS+[['assert',FALSE],['assert',ZERO]]
        self.assertTrue(all(r['full_quantified_formula_matches'] for r in ns['constant_maps'](commands,HASHES)))
        for text in ['(forall ((i Int)) (=> p (= (select fc i) false)))','(forall ((i Real)) (= (select fc i) false))',
                     '(exists ((i Int)) (= (select fc i) false))','(forall ((i Int)) (= (select fc i) true))']:
            bad=term(text);hashes={**HASHES,'false':ns['digest'](bad)}
            self.assertFalse(ns['constant_maps'](DECLS+[['assert',bad],['assert',ZERO]],hashes)[0]['full_quantified_formula_matches'])

    def test_map_type_digest_and_duplicate_refuse(self):
        for commands,hashes in [([term('(declare-fun fc () (Array Int Int))'),DECLS[1],['assert',FALSE],['assert',ZERO]],HASHES),
                               (DECLS+[['assert',FALSE],['assert',FALSE],['assert',ZERO]],HASHES),
                               (DECLS+[['assert',FALSE],['assert',ZERO]],{**HASHES,'false':'0'*64})]:
            self.assertFalse(ns['constant_maps'](commands,hashes)[0]['full_quantified_formula_matches'])

    def test_empty_exact_constructor_and_constant_maps(self):
        schema=ns['record_schema']([SCHEMA]);maps=ns['constant_maps'](DECLS+[['assert',FALSE],['assert',ZERO]],HASHES)
        good=term('(define-fun empty ((dummy Int)) state (state_builder fc fc1))')
        self.assertTrue(ns['empty_shape']([good],schema,maps)['matching'])
        for text in ['(define-fun empty ((dummy Int)) state (state_builder fc1 fc))',
                     '(define-fun empty ((dummy Real)) state (state_builder fc fc1))',
                     '(define-fun empty ((dummy Int)) state (other fc fc1))']:
            self.assertFalse(ns['empty_shape']([term(text)],schema,maps)['matching'])
        self.assertFalse(ns['empty_shape']([good],{'matching':False},maps)['matching'])

    def test_unknown_support_stays_pending(self):
        goal=ns['source_goal']('swap.self')
        result=ns['inspect_task']([SCHEMA,['assert','unrecognized'],['assert',goal]],'swap.self',HASHES,{})
        self.assertIn({'kind':'support_assertion','sha256':ns['digest']('unrecognized')},result['unresolved'])
        self.assertFalse(result['scientific_acceptance'])
        self.assertFalse(result['actual_submission_attested'])

    def test_alias_does_not_precede_schema(self):
        definition=term('(define-fun begin_owner ((s state) (r Int)) state (state_builder (store (active s) r true) (store (backing s) r 0)))')
        goal=ns['source_goal']('swap.self')
        good=ns['inspect_task']([SCHEMA,definition,['assert',goal]],'swap.self',HASHES,{})
        bad=ns['inspect_task']([definition,['assert',goal]],'swap.self',HASHES,{})
        self.assertTrue(good['definitions'][0]['equivalent_after_local_schema_check'])
        self.assertFalse(bad['definitions'][0]['equivalent_after_local_schema_check'])

    def test_observer_audit_closed_no_write_no_child(self):
        ns['ALLOWED_PATHS']={'/exact'}
        for event,args in [('subprocess.Popen',()),('socket.connect',()),('ctypes.dlopen',()),
                           ('open',('/other','r',0)),('open',('/exact','w',1))]:
            with self.assertRaises((RuntimeError,ValueError)):ns['audit'](event,args)
        ns['audit']('open',('/exact','r',0))

    def test_first_difference_is_only_path_shape_digest(self):
        fn=ns['first_difference']
        self.assertIsNone(fn(['not','x'],['not','x']))
        result=fn(['not',['forall',[],['valid','secret_actual',0]]],['not',['exists',[],['valid','secret_expected',1]]])
        self.assertEqual(result['path'],[1])
        self.assertEqual(result['actual_shape']['operator'],'forall')
        self.assertEqual(result['expected_shape']['operator'],'exists')
        self.assertNotIn('secret_',repr(result))
        atom=fn(['=', 'secret_actual', '0'],['=', 'secret_expected', '0'])
        self.assertEqual(atom['path'],[1])
        self.assertNotIn('secret_',repr(atom))

    def test_v2_probe_exact_diagnostic_only_inverse(self):
        value=(HERE/'encoding_probe.py').read_text()
        left=value.index('def first_difference(');right=value.index('def inspect_task(',left)
        value=value[:left]+value[right:]
        value=value.replace("    actual_canonical_goal = canon(goal)\n    expected_canonical_goal = canon(source_goal(ident))\n    goal_equivalent = schema['matching'] and actual_canonical_goal == expected_canonical_goal\n",
                            "    goal_equivalent = schema['matching'] and canon(goal) == canon(source_goal(ident))\n")
        value=value.replace("            'goal_canonical_sha256': digest(actual_canonical_goal),\n            'expected_goal_canonical_sha256': digest(expected_canonical_goal),\n            'first_canonical_goal_difference': first_difference(actual_canonical_goal, expected_canonical_goal),\n",'')
        self.assertEqual(value,(HERE.parent/'cold-g621-encoding-v1/encoding_probe.py').read_text())
        for name in ('semantic_terms.py','observer.py','context.json'):
            self.assertEqual((HERE/name).read_bytes(),(HERE.parent/'cold-g621-encoding-v1'/name).read_bytes())

    def test_exact_canonicalizer_inverse(self):
        value=(HERE/'semantic_terms.py').read_text()
        value=value.replace('def canon(tree, env=None, depth=0, binder_depth=0):','def canon(tree, env=None, depth=0):')
        value=value.replace(', depth + 1, binder_depth + 1)',', depth + 1)').replace(', depth + 1, binder_depth)',', depth + 1)')
        value=value.replace('% (binder_depth, key, index)','% (depth, key, index)')
        value=value.replace('    Binder depth is separate from resource/traversal depth so inert lets and\n    connective wrappers cannot rename otherwise identical bound variables.\n','')
        self.assertEqual(value,(HERE.parent/'cold-g621-v3/semantic_terms.py').read_text())


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print('child_native_network_attempts='+repr(ATTEMPTS))
    raise SystemExit(0 if result.wasSuccessful() and not ATTEMPTS else 1)
