"""Pure exact producer flag projection/refusal controls; no audit or record parse."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest
HERE=Path(__file__).resolve().parent
INIT=HERE.parent
V6=INIT/'cold-v6-admission-04af74c1'
OLD=(V6/'initialized_cold_audit_v6.py').read_text()
NEW=(HERE/'initialized_cold_audit_v7.py').read_text()
assert hashlib.sha256(OLD.encode()).hexdigest()=='02744c321c9bc60535f374d0b47b4d634b54e02c9786a31351c77859c3d8b598'
META=json.loads((V6/'retained-flags-mismatch-metadata-20261016.json').read_bytes())
def deny(event,args):
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.','ctypes.dlopen')) or event=='os.system':raise RuntimeError('pure selector control refuses '+event)
sys.addaudithook(deny)
def predicate(text):
 nodes=[n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.Assert) and isinstance(n.test,ast.Compare) and ast.unparse(n.test.left)=="settings['flags']"]
 assert len(nodes)==1
 return nodes[0]
def run_predicate(text,row,flags=None):
 exec(compile(ast.Module(body=[predicate(text)],type_ignores=[]),'<exact-flag-predicate>','exec'),{'settings':{'flags':flags if flags is not None else row['actual_settings_flags']},'flags':row['method_flags']})
class Controls(unittest.TestCase):
 def test_old_red_actual_green_both_records(self):
  self.assertEqual(len(META['records']),2)
  for row in META['records']:
   self.assertEqual(row['actual_flag_count'],21);self.assertEqual(row['cold_flag_count'],20)
   with self.assertRaises(AssertionError):run_predicate(OLD,row)
   run_predicate(NEW,row)
 def test_exact_frozen_source_producer_recipe_reproduces_actual_flags(self):
  file=INIT.parent/'28-public-memory-trace-resume-20261016/trace-cold-actual-shape-controls-v2/frozen-source/swdb/wp_adapter.py'
  data=file.read_bytes();self.assertEqual(hashlib.sha256(data).hexdigest(),'dbf887bf8515e6ce59086fdc99ec0b58558d742425311b8e404b5d4437b29ebf')
  tree=ast.parse(data)
  source=[n for n in ast.walk(tree) if isinstance(n,ast.Assign) and n.lineno==487]
  flags=[n for n in ast.walk(tree) if isinstance(n,ast.Assign) and n.lineno==965]
  self.assertEqual(len(source),1);self.assertEqual(len(flags),1)
  self.assertEqual(ast.dump(source[0].value),ast.dump(ast.parse('[f"-wp-fct={job.unit.function}"] + ([f"-inline-calls={\',\'.join(callees)}"] if callees else [])',mode='eval').body))
  for row in META['records']:
   ns={'context':{},'job':types.SimpleNamespace(unit=types.SimpleNamespace(function='trust_fixture')),'callees':[],'tools':{'flags':row['method_flags'],'seconds':30},'MACHDEP':('-machdep','x86_64'),'prover_flags':[]}
   exec(compile(ast.Module(body=[*source,*flags],type_ignores=[]),'<exact04af-producer-assignments>','exec'),ns)
   self.assertEqual(ns['settings_flags'],row['actual_settings_flags'])
 def test_wrong_selector_inline_callee_and_mandatory_flag_mutations_refuse(self):
  row=META['records'][0];good=row['actual_settings_flags']
  alternatives=[good[:-1],good[:-1]+['-wp-fct=other'],good[:-1]+['-wp-fct=trust_fixture,other'],good+['-inline-calls=evil'],[x for x in good if x!='-wp-smoke-tests'],[x for x in good if x!='-rte-initialized']]
  for flags in alternatives:
   with self.subTest(flags=flags),self.assertRaises(AssertionError):run_predicate(NEW,row,flags)
 def test_complete_ast_inverse_and_all_other_science_checks_unchanged(self):
  a,b=ast.parse(OLD),ast.parse(NEW);b.body[0]=a.body[0]
  before=next(n for n in a.body if isinstance(n,ast.FunctionDef) and n.name=='audit_record');after=next(n for n in b.body if isinstance(n,ast.FunctionDef) and n.name=='audit_record')
  index=next(i for i,n in enumerate(before.body) if isinstance(n,ast.Assert) and ast.dump(n)==ast.dump(predicate(OLD)))
  after.body[index]=before.body[index]
  self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))
  self.assertIn("assert unit['function'] == 'trust_fixture'",NEW)
 def test_policy_inverse_and_controls_remain_closed(self):
  old=json.loads((V6/'initialized-cold-policy-04af74c1-v6.json').read_bytes());new=json.loads((HERE/'initialized-cold-policy-04af74c1-v7.json').read_bytes())
  def undo(x):
   if isinstance(x,dict):return {k:undo(v) for k,v in x.items()}
   if isinstance(x,list):return [undo(v) for v in x]
   return x.replace('initialized-cold-04af74c1-v7','initialized-cold-04af74c1-v6') if isinstance(x,str) else x
  new=undo(new);new['reader_sha256']=old['reader_sha256']
  for key in ('producer_function_selector_source','preserved_actual_v6_refusal','exact_retained_flag_comparison'):new['provenance'].pop(key)
  self.assertEqual(new,old)
  command=json.loads((HERE/'initialized-cold-command-04af74c1-v7.json').read_bytes())
  self.assertEqual(len(command['control_files']),10);self.assertLess(command['control_total_bytes'],1048576)
  self.assertEqual(command['command'][-1],hashlib.sha256((HERE/'initialized-cold-policy-04af74c1-v7.json').read_bytes()).hexdigest())
if __name__=='__main__':unittest.main(verbosity=2)
