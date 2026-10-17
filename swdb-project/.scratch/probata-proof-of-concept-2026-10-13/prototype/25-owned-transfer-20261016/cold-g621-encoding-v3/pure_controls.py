"""2026-10-16 ET. No-child synthetic encoding and exact-delta controls."""
import ast
import copy
import json
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
        records=json.loads((HERE/'full-source-inverses.json').read_bytes())['files']
        row=next(r for r in records if r['filename']=='encoding_probe.py')
        value=(HERE/'encoding_probe.py').read_text()
        for edit in reversed(row['edits']):
            self.assertEqual(value[edit['new_start']:edit['new_end']],edit['after'])
            value=value[:edit['new_start']]+edit['before']+value[edit['new_end']:]
        self.assertEqual(value,(HERE.parent/'cold-g621-encoding-v2/encoding_probe.py').read_text())

    def test_exact_canonicalizer_inverse(self):
        records=json.loads((HERE/'full-source-inverses.json').read_bytes())['files']
        row=next(r for r in records if r['filename']=='semantic_terms.py')
        value=(HERE/'semantic_terms.py').read_text()
        for edit in reversed(row['edits']):
            self.assertEqual(value[edit['new_start']:edit['new_end']],edit['after'])
            value=value[:edit['new_start']]+edit['before']+value[edit['new_end']:]
        self.assertEqual(value,(HERE.parent/'cold-g621-encoding-v2/semantic_terms.py').read_text())


    def test_complete_curried_and_nary_implications(self):
        for left,right in [('(=> a (=> b c))','(=> (and a b) c)'),
            ('(=> a b c d)','(=> (and a b c) d)'),
            ('(forall ((x Int)) (=> (= x 0) (=> (< x 2) (=> (< x 3) (= x 0)))))','(forall ((y Int)) (=> (and (< y 3) (= y 0) (< y 2)) (= y 0)))')]:
            self.assertEqual(canonical(left),canonical(right))

    def test_implication_barriers_missing_premises_and_polarity(self):
        for left,right in [('(=> a (forall ((x Int)) (=> (p x) (q x))))','(forall ((x Int)) (=> (and a (p x)) (q x)))'),
            ('(=> (=> a b) c)','(=> (and a b) c)'),
            ('(=> a (=> b c))','(=> a c)'),
            ('(=> a (=> b c))','(=> (and a (not b)) c)')]:
            self.assertNotEqual(canonical(left),canonical(right))

    def test_mathematical_plus_orders_complete_operands_only(self):
        self.assertEqual(canonical('(forall ((frontier Int)) (= (+ 1 frontier) 4))'),canonical('(forall ((f Int)) (= (+ f 1) 4))'))
        self.assertEqual(canonical('(+ (f x) 3 (g y))'),canonical('(+ (g y) (f x) 3)'))
        for left,right in [('(+ x y)','(+ x z)'),('(+ x y y)','(+ x y)'),('(+ x (+ y z))','(+ (+ x y) z)')]:
            self.assertNotEqual(canonical(left),canonical(right))

    def test_fp_bv_custom_and_quoted_operators_are_unchanged(self):
        for op in ('fp.add','bvadd','custom_add','|+|'):
            self.assertNotEqual(canonical('('+op+' x y)'),canonical('('+op+' y x)'))
        with self.assertRaises(ValueError):
            ns['inspect_task']([term('(declare-fun + (Bool Bool) Bool)')],'empty.valid',HASHES,{})

    def test_selected_abs_requires_exact_typed_complete_body(self):
        expected=term('(define-fun abs1 ((x Int)) Int (ite (<= 0 x) x (- x)))')
        self.assertTrue(ns['absolute_definition'](expected)['complete_typed_body_matches'])
        for changed in [term('(define-fun abs1 ((x Int)) Int 0)'),term('(define-fun abs1 ((x Real)) Real (ite (<= 0 x) x (- x)))'),
            term('(define-fun abs1 ((x Int)) Int (ite (< 0 x) x (- x)))'),term('(define-fun other ((x Int)) Int (ite (<= 0 x) x (- x)))')]:
            self.assertFalse(ns['absolute_definition'](changed)['complete_typed_body_matches'])

    def test_context_addition_and_observer_delta_preserve_complete20(self):
        before=json.loads((HERE.parent/'cold-g621-encoding-v2/context.json').read_bytes())
        after=json.loads((HERE/'context.json').read_bytes())
        self.assertEqual({k:v for k,v in after.items()if k!='standard_abs_source'},before)
        self.assertEqual(len(after['tasks']),20)
        self.assertEqual(after['standard_abs_source']['sha256'],'eb5bc9d4a46e1b6a298d24fd36dcf9dfb8f35cbc75b2f44007cfe1a24550ce8d')
        primary=Path('/Users/yanrujhou/.opam/framac-33/share/why3/stdlib/int.mlw').read_bytes()
        begin,end=after['standard_abs_source']['module_byte_range']
        self.assertEqual(ns['hashlib'].sha256(primary).hexdigest(),after['standard_abs_source']['sha256'])
        self.assertEqual(ns['hashlib'].sha256(primary[begin:end]).hexdigest(),after['standard_abs_source']['module_body_sha256'])
        row=next(r for r in json.loads((HERE/'full-source-inverses.json').read_bytes())['files']if r['filename']=='observer.py')
        value=(HERE/'observer.py').read_text()
        for edit in reversed(row['edits']):value=value[:edit['new_start']]+edit['before']+value[edit['new_end']:]
        self.assertEqual(value,(HERE.parent/'cold-g621-encoding-v2/observer.py').read_text())
        self.assertEqual(ATTEMPTS,[])

    def test_complete20_projected_publication_extent(self):
        prior=HERE.parents[2]/'evidence/t25-owned-transfer10-encoding-v2-actual-stdout-20261016.json'
        raw=prior.read_bytes()
        self.assertEqual(ns['hashlib'].sha256(raw).hexdigest(),'b04c4ae7f0497edeaaca697c58b7310eb1c1bdc70a0190cf90d1a5bf5af9691c')
        value=json.loads(raw)
        standard=ns['absolute_definition'](term('(define-fun abs1 ((x Int)) Int (ite (<= 0 x) x (- x)))'))
        for task in value['tasks']:
            for row in task['definitions']:
                row['selected_standard_definition']=standard if row['name']=='abs1' else None
            # Deliberately retain every mismatch with a maximum supported path.
            task['first_canonical_goal_difference']={
                'path':[100000]*120,
                'actual_shape':{'kind':'list','items':100000,'operator':None,'unknown_head_sha256':'a'*64},
                'expected_shape':{'kind':'list','items':100000,'operator':None,'unknown_head_sha256':'b'*64},
                'actual_node_sha256':'c'*64,'expected_node_sha256':'d'*64}
        value['standard_abs_source']=json.loads((HERE/'context.json').read_bytes())['standard_abs_source']
        value['all22_selected_inputs_pre_post_equal']=True
        self.assertEqual(len(value['tasks']),20)
        self.assertLessEqual(len(ns['compact'](value))+1,256*1024)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print('child_native_network_attempts='+repr(ATTEMPTS))
    raise SystemExit(0 if result.wasSuccessful() and not ATTEMPTS else 1)
