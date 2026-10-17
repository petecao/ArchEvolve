"""Pure exact read-boundary controls; fake atime/content metadata, no compiler."""
import ast
import copy
import hashlib
from pathlib import Path
import sys
import types
import unittest
HERE=Path(__file__).resolve().parent

def deny(event,args):
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.','ctypes.dlopen')) or event=='os.system':raise RuntimeError('pure stat controls refuse '+event)
sys.addaudithook(deny)
def load(path):
 ns={'__name__':'pure_metadata_boundary','__file__':str(path)};exec(compile(path.read_bytes(),str(path),'exec'),ns);return ns
OLD_MODEL=load(HERE/'model-entry-v2/whole_model_v2.py')
MODEL=load(HERE/'model-entry-v3/whole_model_v3.py')
OLD_STATEMENTS=load(HERE/'source_statements_v1.py')
STATEMENTS=load(HERE/'source_statements_v2.py')
BASE=load(HERE/'test_source_statements_v1.py')
FIELDS=('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns')
class FakePath:
 def __init__(self,real,changes):
  self.real=real;self.calls=0
  source=real.lstat();self.before=types.SimpleNamespace(**{key:getattr(source,key) for key in FIELDS},st_atime=source.st_atime,st_atime_ns=source.st_atime_ns)
  self.after=copy.deepcopy(self.before)
  for key,value in changes.items():setattr(self.after,key,value)
 def lstat(self):self.calls+=1;return self.before if self.calls==1 else self.after
 def resolve(self,strict=True):return self
 def read_bytes(self):return self.real.read_bytes()
 def __str__(self):return str(self.real)
class Controls(unittest.TestCase):
 def test_model_read_atime_only_red_green_and_each_stable_field_refuses(self):
  real=HERE/'whole_adapters.h';raw=real.read_bytes();expected=hashlib.sha256(raw).hexdigest()
  def run(module,changes):
   fake=FakePath(real,changes);before=module['Path'];module['Path']=lambda path:fake
   try:return module['read_pin'](real,expected)
   finally:module['Path']=before
  with self.assertRaises(OLD_MODEL['Refused']):run(OLD_MODEL,{'st_atime':1,'st_atime_ns':1})
  self.assertEqual(run(MODEL,{'st_atime':1,'st_atime_ns':1})[0],raw)
  for key in FIELDS:
   with self.subTest(key=key),self.assertRaises(MODEL['Refused']):run(MODEL,{key:getattr(real.lstat(),key)+1})
 def test_assert_header_atime_only_red_green_and_each_stable_field_refuses(self):
  BASE['Controls'].setUpClass();case=BASE['Controls']('test_01_inventory_and_all_instances');case.setUp()
  try:
   lower,_=case.make();pin=lower.assertion_header;real=Path(pin['path'])
   def run(module,changes):
    before=module['Path'];module['Path']=lambda path:FakePath(real,changes)
    try:return module['Lowerer']._assertion_profile(lower,pin)
    finally:module['Path']=before
   with self.assertRaises(OLD_STATEMENTS['Refused']):run(OLD_STATEMENTS,{'st_atime':1,'st_atime_ns':1})
   run(STATEMENTS,{'st_atime':1,'st_atime_ns':1})
   for key in FIELDS:
    with self.subTest(key=key),self.assertRaises(STATEMENTS['Refused']):run(STATEMENTS,{key:getattr(real.lstat(),key)+1})
  finally:case.tearDown();BASE['Controls'].tearDownClass()
 def test_complete_text_and_ast_inverses(self):
  helper=ast.get_source_segment((HERE/'source_statements_v2.py').read_text(),next(n for n in ast.parse((HERE/'source_statements_v2.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='stable_metadata'))
  pairs=[(HERE/'source_statements_v1.py',HERE/'source_statements_v2.py','stable_metadata(path.lstat())==stable_metadata(before)','path.lstat()==before'),(HERE/'model-entry-v2/whole_model_v2.py',HERE/'model-entry-v3/whole_model_v3.py','stable_metadata(path.lstat()) == stable_metadata(before)','path.lstat() == before')]
  for old,new,after,before in pairs:
   a,b=old.read_text(),new.read_text();self.assertEqual(b.replace(helper+'\n\n\n','').replace(after,before),a)
   t=ast.parse(b);actual=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='stable_metadata');self.assertEqual(ast.get_source_segment(b,actual),helper)
   self.assertEqual(tuple(ast.literal_eval(n) for n in actual.body[-1].value.args[0].generators[0].iter.elts),FIELDS)
if __name__=='__main__':unittest.main(verbosity=2)
