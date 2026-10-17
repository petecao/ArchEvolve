"""NOT RUN: reviewed-source-only codec tests; synthetic temporary files only.

No target module imports, main/Store/public/report/compiler/provider/SSH calls.
A future parent-reviewed invocation lifts exactly the new codec definitions and
five closed assignments. Production bounds stay100MiB/1GiB/3600s; only this
isolated namespace uses256B/4096B caps to exercise both routes cheaply.
"""
import ast
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time
import unittest
from unittest import mock
import zlib

EXPORTER=Path('/private/tmp/lanl14_final_export_lossless_gzip_20261007_a1.py')
EXPORTER_SHA='928af82facd9f36dfdbca6595d2c2e9d1091dd0064c9fe53fc41c163879e026e'
READER=Path('/private/tmp/lanl14_readonly_nine_export_admission_lossless_gzip_20261007_a1.py')
READER_SHA='6909c422990a071b1a8d08c634c1c086f0218c5851d38996b6f4798759499570'
ASSIGNS=('MAX_GIT_REPORT_BYTES','MAX_ORIGINAL_REPORT_BYTES','REPORT_CODEC_SECONDS','REPORT_TRANSFER_POLICY','REPORT_STAT_KEYS')
DEFS=('_report_require','_report_deadline','_report_remaining','_report_stamp','_report_chunks','_report_file_pin','_ReportCappedWriter','_report_transfer_contract','_report_decoded_chunks','read_report_transfer','_report_compare_original','prepare_report_transfer')
SMALL=b'{\n "format":"synthetic.codec.only", "trials":[{"position":0},{"position":1},{"position":2},{"position":3},{"position":4}], "value":-0.0, "unknown":null, "text":"\\u03bb"\n}\n'
LARGE=b' '*1024+SMALL
SYNTHETIC_SEMANTIC='1'*64

def _closed_constant(node):
 if isinstance(node,ast.Constant) and type(node.value) in (str,int):return True
 if isinstance(node,ast.Tuple):return all(_closed_constant(v) for v in node.elts)
 if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Mult):return _closed_constant(node.left) and _closed_constant(node.right)
 return False

def source_lift():
 trees=[]
 for path,pin in ((EXPORTER,EXPORTER_SHA),(READER,READER_SHA)):
  raw=path.read_bytes()
  if len(raw)>131072 or hashlib.sha256(raw).hexdigest()!=pin:raise AssertionError('Exact reviewed codec source pin differs')
  tree=ast.parse(raw);assigns={n.targets[0].id:n for n in tree.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
  definitions={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  selected=[assigns[n] for n in ASSIGNS]+[definitions[n] for n in DEFS]
  if not all(_closed_constant(assigns[n].value) for n in ASSIGNS):raise AssertionError('Closed constant AST required')
  trees.append(selected)
 if [ast.dump(n,include_attributes=False) for n in trees[0]]!=[ast.dump(n,include_attributes=False) for n in trees[1]]:raise AssertionError('Both exact codec implementations must agree')
 namespace={'__builtins__':__builtins__,'Path':Path,'gzip':gzip,'hashlib':hashlib,'json':json,'os':os,'re':re,'stat':stat,'time':time,'zlib':zlib}
 module=ast.fix_missing_locations(ast.Module(body=trees[0],type_ignores=[]))
 exec(compile(module,'reviewed-exact-codec-AST-only','exec'),namespace)
 if namespace['MAX_GIT_REPORT_BYTES']!=104857600 or namespace['MAX_ORIGINAL_REPORT_BYTES']!=1073741824 or namespace['REPORT_CODEC_SECONDS']!=3600:raise AssertionError('Original production administrative bounds differ')
 namespace['MAX_GIT_REPORT_BYTES']=256;namespace['MAX_ORIGINAL_REPORT_BYTES']=4096
 return namespace

class CodecTests(unittest.TestCase):
 def setUp(self):
  self.n=source_lift();self.temp=tempfile.TemporaryDirectory(prefix='lanl14-isolated-codec-',dir='/private/tmp');self.root=Path(self.temp.name).resolve()
 def tearDown(self):self.temp.cleanup()
 def write(self,name,raw):
  path=self.root/name;fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,'wb') as f:f.write(raw)
  return path
 def prepared(self,raw=SMALL,name='original.json',output='transfer.json.gz'):
  original=self.write(name,raw)
  return original,self.n['prepare_report_transfer'](original,self.root/output,SYNTHETIC_SEMANTIC)
 def corrupted(self,raw,transfer,name='corrupt.json.gz'):
  target=self.write(name,raw);copy=json.loads(json.dumps(transfer));copy['exported']['bytes']=len(raw);copy['exported']['sha256']=hashlib.sha256(raw).hexdigest();copy['exported']['path']=target.name
  return target,copy
 def test_small_report_keeps_exact_original_bytes_and_no_gzip_output(self):
  original,(selected,transfer,_,_)=self.prepared()
  self.assertEqual(selected,original);self.assertEqual(transfer['encoding'],'identity');self.assertFalse((self.root/'transfer.json.gz').exists())
  self.assertEqual(self.n['read_report_transfer'](selected,transfer),SMALL);self.assertEqual(original.read_bytes(),SMALL)
 def test_conditional_gzip_is_deterministic_and_preserves_every_original_byte(self):
  original,(selected,transfer,_,_)=self.prepared(LARGE)
  _,(second,other,_,_)=self.prepared(LARGE,name='second.json',output='second.json.gz')
  self.assertEqual(transfer['encoding'],'gzip');self.assertEqual(selected.read_bytes(),second.read_bytes())
  self.assertEqual(selected.read_bytes()[:10],b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff')
  self.assertLessEqual(selected.stat().st_size,256);self.assertEqual(stat.S_IMODE(selected.stat().st_mode),0o600)
  self.assertEqual(gzip.decompress(selected.read_bytes()),LARGE)  # Independent stdlib format oracle.
  self.assertEqual(self.n['read_report_transfer'](selected,transfer),LARGE);self.assertEqual(original.read_bytes(),LARGE)
 def test_crc_corruption_is_refused_with_explicit_matching_transfer_pin(self):
  _,(selected,transfer,_,_)=self.prepared(LARGE);bad=bytearray(selected.read_bytes());bad[-8]^=1
  target,changed=self.corrupted(bytes(bad),transfer)
  with self.assertRaises((ValueError,zlib.error)):self.n['read_report_transfer'](target,changed)
 def test_trailing_bytes_are_refused(self):
  _,(selected,transfer,_,_)=self.prepared(LARGE);target,changed=self.corrupted(selected.read_bytes()+b'junk',transfer)
  with self.assertRaises(ValueError):self.n['read_report_transfer'](target,changed)
 def test_concatenated_second_gzip_member_is_refused(self):
  _,(selected,transfer,_,_)=self.prepared(LARGE)
  empty_member=gzip.compress(b'',compresslevel=9,mtime=0)
  self.assertEqual(len(empty_member),20);self.assertEqual(gzip.decompress(empty_member),b'')
  concatenated=selected.read_bytes()+empty_member
  self.assertLessEqual(len(concatenated),256)  # Reach member refusal, not encoded-size refusal.
  target,changed=self.corrupted(concatenated,transfer)
  with self.assertRaises(ValueError):self.n['read_report_transfer'](target,changed)
 def test_truncated_footer_is_refused(self):
  _,(selected,transfer,_,_)=self.prepared(LARGE);target,changed=self.corrupted(selected.read_bytes()[:-1],transfer)
  with self.assertRaises((ValueError,zlib.error)):self.n['read_report_transfer'](target,changed)
 def test_malformed_header_is_refused(self):
  _,(selected,transfer,_,_)=self.prepared(LARGE);bad=bytearray(selected.read_bytes());bad[0]=0
  target,changed=self.corrupted(bytes(bad),transfer)
  with self.assertRaises((ValueError,zlib.error)):self.n['read_report_transfer'](target,changed)
 def test_decoded_size_overflow_is_refused_before_accepting_output(self):
  _,(selected,transfer,_,_)=self.prepared(LARGE);changed=json.loads(json.dumps(transfer));changed['original']['bytes']=257
  with self.assertRaises(ValueError):self.n['read_report_transfer'](selected,changed)
 def test_wrong_original_hash_is_refused_after_lossless_decode(self):
  _,(selected,transfer,_,_)=self.prepared(LARGE);changed=json.loads(json.dumps(transfer));changed['original']['sha256']='0'*64
  with self.assertRaises(ValueError):self.n['read_report_transfer'](selected,changed)
 def test_incompressible_git_overflow_retains_original_and_bounded_partial(self):
  original=self.write('opaque.synthetic',bytes(range(256))*4);gzip_path=self.root/'opaque.synthetic.gz'
  with self.assertRaises(ValueError):self.n['prepare_report_transfer'](original,gzip_path,SYNTHETIC_SEMANTIC)
  self.assertEqual(original.read_bytes(),bytes(range(256))*4);self.assertTrue(gzip_path.exists());self.assertLessEqual(gzip_path.stat().st_size,256)
 def test_original_administrative_overflow_refuses_before_open_or_gzip_creation(self):
  original=self.write('oversize.synthetic',b'x'*4097);gzip_path=self.root/'oversize.synthetic.gz'
  with mock.patch.object(os,'open',side_effect=AssertionError('No body open allowed')):
   with self.assertRaises(ValueError):self.n['prepare_report_transfer'](original,gzip_path,SYNTHETIC_SEMANTIC)
  self.assertFalse(gzip_path.exists());self.assertEqual(original.stat().st_size,4097)
 def test_same_size_inode_swap_during_read_is_refused(self):
  original,(selected,transfer,_,_)=self.prepared();replacement=self.write('replacement.json',SMALL);real_fstat=os.fstat;calls=0
  def swapped(fd):
   nonlocal calls
   calls+=1
   if calls==2:os.replace(replacement,original)
   return real_fstat(fd)
  with mock.patch.object(os,'fstat',side_effect=swapped):
   with self.assertRaises(ValueError):self.n['read_report_transfer'](selected,transfer)
  self.assertEqual(original.read_bytes(),SMALL)
 def test_symlink_input_and_existing_partial_output_are_not_replayed(self):
  original=self.write('large.json',LARGE);link=self.root/'link.json';link.symlink_to(original)
  with self.assertRaises(ValueError):self.n['prepare_report_transfer'](link,self.root/'link.gz',SYNTHETIC_SEMANTIC)
  partial=self.write('partial.gz',b'preserved')
  with self.assertRaises(ValueError):self.n['prepare_report_transfer'](original,partial,SYNTHETIC_SEMANTIC)
  self.assertEqual(partial.read_bytes(),b'preserved');self.assertEqual(original.read_bytes(),LARGE)

if __name__=='__main__':unittest.main(verbosity=2)
