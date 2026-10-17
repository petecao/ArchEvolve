"""Pure exact unused-overload metadata branch; no audit or scientific record parse."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
HERE=Path(__file__).resolve().parent
INIT=HERE.parent
OLD=(INIT/'initialized_cold_obligations_v2.py').read_text()
NEW=(HERE/'initialized_cold_obligations_v3.py').read_text()
assert hashlib.sha256(OLD.encode()).hexdigest()=='dfc647552f4a1bbfd33cc4745289257a9aca4e8b587ce45ca9aa757066950dc9'
META=json.loads((INIT/'cold-v7-admission-04af74c1/retained-arity0-property-metadata-20261016.json').read_bytes())
def deny(event,args):
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.','ctypes.dlopen')) or event=='os.system':raise RuntimeError('pure unused-overload control refuses '+event)
sys.addaudithook(deny)
NS={'__name__':'inert_unused_metadata'};exec(compile(NEW,'<exact-closed-obligations-v3>','exec'),NS)
def source_receipt(number):
 text=(INIT/('cold-reference-wp-correct.c' if number==711 else 'cold-reference-wp-wrong.c')).read_text()
 return NS['initialized_wp_source'](text,number,INIT)
def fixture(row):
 props={p['property']:copy.deepcopy(p) for p in row['unused_arity0_all_properties']}
 return copy.deepcopy(row['unused_arity0_CSV']),props,{},source_receipt(row['expected_result']),Path(next(iter(props.values()))['source_file'])
class Controls(unittest.TestCase):
 def test_actual_shapes_are_unused_and_old_extern_predicate_is_red(self):
  old=next(n for n in ast.parse(OLD).body if isinstance(n,ast.FunctionDef) and n.name=='current_goals')
  line=next(n for n in old.body if isinstance(n,ast.Assert) and 'for p in extern' in ast.unparse(n))
  for row in META['records']:
   rows,props,goals,query,path=fixture(row)
   with self.assertRaises(AssertionError):exec(compile(ast.Module(body=[line],type_ignores=[]),'<exact-old-extern-predicate>','exec'),{'extern':[p for p in props.values() if p['extern']],'HELPERS':NS['HELPERS']})
   receipt=NS['unused_arity0_v3'](rows,props,goals,query,path)
   self.assertEqual(receipt['native_goals'],0);self.assertFalse(receipt['active_helper']);self.assertFalse(receipt['implementation_proven']);self.assertFalse(receipt['precondition_proven'])
   self.assertNotIn('get_new_reg_unsigned_int_args0',NS['HELPERS'])
 def test_each_shape_call_support_goal_and_csv_mutation_refuses(self):
  base=fixture(META['records'][0]);fn='get_new_reg_unsigned_int_args0'
  mutations=[lambda r,p,g,q:p[fn+'_requires'].update(description=r'requires \true'),lambda r,p,g,q:p[fn+'_requires'].update(extern=True),lambda r,p,g,q:p[fn+'_assigns'].update(property_variant='IPPredicate'),lambda r,p,g,q:p[fn].update(call_context={'caller':'trust_fixture'}),lambda r,p,g,q:p.pop(fn+'_requires'),lambda r,p,g,q:g.update(bad={'function':fn,'property':fn+'_assigns','targets':[]}),lambda r,p,g,q:g.update(bad={'function':'trust_fixture','property':'other','targets':[fn+'_assigns']}),lambda r,p,g,q:p.update(other={**p[fn],'property':'other','function':'trust_fixture','dependencies':[fn+'_assigns']}),lambda r,p,g,q:r[0].update(status='Valid'),lambda r,p,g,q:r.append(dict(r[0])),lambda r,p,g,q:q.update(unused_arity0_declaration_only=False),lambda r,p,g,q:q.update(reference_sha256='0'*64)]
  for index,mutate in enumerate(mutations):
   rows,props,goals,query,path=copy.deepcopy(base);mutate(rows,props,goals,query)
   with self.subTest(index=index),self.assertRaises((AssertionError,KeyError)):NS['unused_arity0_v3'](rows,props,goals,query,path)
 def test_source_query_binds_exact_false_prototype_and_absence_of_calls(self):
  for number in (711,1107):self.assertTrue(source_receipt(number)['unused_arity0_declaration_only'])
  text=(INIT/'cold-reference-wp-correct.c').read_text()
  for changed in (text+'\nvoid bad(void){get_new_reg_unsigned_int_args0();}\n',text.replace(r'requires \false; assigns \nothing;',r'requires \true; assigns \nothing;')):
   with self.assertRaises(AssertionError):NS['initialized_wp_source'](changed,711,INIT)
 def test_csv_wrapper_removes_only_validated_three_properties_and_two_rows(self):
  rows,props,goals,query,path=fixture(META['records'][0]);active={'function':'trust_fixture','origin':None,'dependencies':[]};rows.append(active);props['active']=active
  captured=[];old=NS['current_csv_active_v2']
  def stand_in(r,p,g,f):
   self.assertEqual(r,[active]);self.assertEqual(p,{'active':active});self.assertEqual(g,goals);self.assertEqual(f,[]);captured.append(True);return {'CSV_rows':1,'ordinary_checks':'inert seam only'}
  NS['current_csv_active_v2']=stand_in
  try:result=NS['current_csv'](rows,props,goals,[],validated_query=query,expected_wp_input=path)
  finally:NS['current_csv_active_v2']=old
  self.assertEqual(captured,[True]);self.assertEqual(result['CSV_rows'],3);self.assertEqual(len(result['unused_requires_false_overload']['CSV_rows']),2)
 def test_all_active_csv_and_goal_check_bodies_preserved_by_inverse(self):
  a,b=ast.parse(OLD),ast.parse(NEW)
  oldcsv=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='current_csv');newcsv=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name=='current_csv_active_v2');newcsv.name='current_csv'
  self.assertEqual(ast.dump(oldcsv),ast.dump(newcsv))
  self.assertEqual(NS['HELPERS'],{'init_MAA','get_new_reg_unsigned_int_args1','get_reg_unsigned_int'})
  oldgoal=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='current_goals');newgoal=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name=='current_goals')
  newgoal.args=oldgoal.args
  newgoal.body=[n for n in newgoal.body if not(isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='unused' for t in n.targets))]
  oldextern=next(n for n in oldgoal.body if isinstance(n,ast.Assert) and 'for p in extern' in ast.unparse(n));idx=next(i for i,n in enumerate(newgoal.body) if isinstance(n,ast.Assert) and 'for p in extern' in ast.unparse(n));newgoal.body[idx]=oldextern
  oldcross=next(n for n in oldgoal.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and getattr(n.value.func,'id',None)=='current_csv');idx=next(i for i,n in enumerate(newgoal.body) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and getattr(n.value.func,'id',None)=='current_csv');newgoal.body[idx]=oldcross
  self.assertEqual(ast.dump(oldgoal),ast.dump(newgoal))
 def test_primary_linux_report_sources_match_prior_pins(self):
  q=json.loads((INIT/'cold-v7-admission-04af74c1/unused-arity0-linux-primary-report-20261016.json').read_bytes());self.assertEqual([r['sha256'] for r in q['files']],['3ac71b35403ac50ed40951bdb974edc59a42ce362e9c75a2b80c2a29788dc21d','b6d14101aa358ee74b64b85db43bd8bb31e9577dc8852629bee2160b3ac8c8b9'])
  primary=q['files'][1]['excerpts'][0]['text'];self.assertIn('Never_tried       -> "Ignored"',primary);self.assertIn('Considered_valid  -> "Considered valid"',primary)
if __name__=='__main__':unittest.main(verbosity=2)
