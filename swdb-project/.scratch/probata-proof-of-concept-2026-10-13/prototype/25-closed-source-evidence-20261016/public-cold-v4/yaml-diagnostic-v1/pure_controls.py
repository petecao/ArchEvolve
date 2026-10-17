from pathlib import Path
import ast,hashlib,json,sys,tempfile,unittest
P=Path('/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/.scratch/probata-proof-of-concept-2026-10-13')
D=P/'prototype/25-closed-source-evidence-20261016/public-cold-v4/yaml-diagnostic-v1'
attempts=[]
def no_child(event,args):
 if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in ('os.system','ctypes.dlopen'):
  attempts.append(event);raise RuntimeError('pure diagnostic controls forbid child/network/native tool')
sys.addaudithook(no_child)
tree=ast.parse((D/'diagnostic-v1.py').read_bytes());tree.body=[n for n in tree.body if not isinstance(n,ast.If)]
n={'__name__':'owned_pure_diag_control'};exec(compile(tree,'diagnostic-v1.py','exec'),n)
y={};exec(compile(n['YAML_BYTES'],'frozen_yaml.py','exec'),y)
class Controls(unittest.TestCase):
 def test_frozen_reader_exact(self):
  self.assertEqual(n['YAML_BYTES'],(D.parent/'record_yaml_subset.py').read_bytes())
  self.assertEqual(hashlib.sha256(n['YAML_BYTES']).hexdigest(),n['YAML_SHA'])
 def test_mapping_location_without_values(self):
  out=n['locate'](b'id: secret_value\nmissing_colon_secret\n',y['Reader'])
  self.assertFalse(out['parsed']);self.assertEqual(out['category'],'YAML mapping colon');self.assertEqual(out['candidate_line'],2)
  self.assertNotIn('secret',json.dumps(out))
 def test_comment_form_reports_flags_no_payload(self):
  out=n['locate'](b'# private_payload\nid: x\n',y['Reader'])
  self.assertEqual(out['candidate_line'],1);self.assertTrue(out['nearby_shape'][0]['comment']);self.assertNotIn('private_payload',json.dumps(out))
 def test_valid_scalar_and_nested(self):
  out=n['locate'](b'id: secret\nlist:\n- key: value\n  size: 4\n',y['Reader'])
  self.assertTrue(out['parsed']);self.assertNotIn('secret',json.dumps(out))
 def test_reader_unknown_keeps_refusal(self):
  for data in (b'a: !!python/object {}\n',b'a: &x value\n',b'a: @bad\n',b'a: 1\na: 2\n'):
   self.assertFalse(n['locate'](data,y['Reader'])['parsed'])
 def test_exact_parent_and_file_symlinks_refuse(self):
  with tempfile.TemporaryDirectory(dir='/private/tmp') as folder:
   root=Path(folder);old=n['ROOT'];n['ROOT']=root
   try:
    sub=root/'a';sub.mkdir();f=sub/'value';f.write_bytes(b'{}')
    data,row=n['read'](f);self.assertEqual(data,b'{}');self.assertEqual(row['bytes'],2)
    alias=sub/'alias';alias.symlink_to(f)
    with self.assertRaises(ValueError):n['read'](alias)
    parent=root/'b';parent.symlink_to(sub)
    with self.assertRaises(ValueError):n['read'](parent/'value')
   finally:n['ROOT']=old
 def test_mutation_and_child_events_refuse(self):
  for event,args in (('subprocess.Popen',()),('socket.connect',()),('os.mkdir',()),('ctypes.dlopen',()),('import',('swdb',)),('open',('/x','w',577))):
   with self.assertRaises((ValueError,RuntimeError)):n['audit'](event,args)
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
assert result.wasSuccessful() and not attempts
print(json.dumps({'date':'2026-10-16 ET','passed':result.testsRun,'failed':len(result.failures),'errors':len(result.errors),'child_attempts':attempts,'diagnostic_main_executed':False,'SSH_used':False}))
