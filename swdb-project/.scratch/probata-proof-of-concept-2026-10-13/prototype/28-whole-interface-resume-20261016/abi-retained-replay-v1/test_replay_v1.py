"""2026-10-16 ET. No-child synthetic ABI controls; no retained remote payload read."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent

def audit(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:raise AssertionError('no child/native/network in replay controls')
sys.addaudithook(audit)

def extract(names,ns):
    tree=ast.parse((HERE/'replay_entry_v1.py').read_bytes());nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
    assert {n.name for n in nodes}==set(names);exec(compile(ast.Module(nodes,type_ignores=[]),'exact_replay_source_controls','exec'),ns)
    return ns

def namespace():
    ns=dict(ast=ast,hashlib=hashlib,json=json,Path=Path,re=re,stat=stat,sys=sys,types=types,time=time,started=time.monotonic(),READS={})
    return extract({'need','canonical','digest','stable','deadline','strict','physical','bounded','module_source','checked_modules','replay','readonly'},ns)

def row(path):
    raw=path.read_bytes();return dict(path=str(path.resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def synthetic_abi(legacy,probe):
    types_map=dict(zip(legacy.TYPE_KEYS,('unsigned int','int','float','unsigned long','long','double')))
    integers=dict(char_bit=8,int_bits=32,pointer_bits=64,little_endian=1,float_radix=2,float_mantissa=24,double_mantissa=53,source_cores=4,source_tiles=32,source_registers=32,source_tile_words=16384)
    for key,width in zip(legacy.TYPE_KEYS,(4,4,4,8,8,8)):integers['size_'+key]=width;integers['align_'+key]=width
    roots=[]
    for i,key in enumerate(legacy.TYPE_KEYS):
        value=dict(kind='TypeAliasDecl',name='dws_probe_'+key,loc=dict(offset=0,file=str(probe),line=1),type=dict(qualType=types_map[key]))
        raw=json.dumps(value,separators=(',',':'))
        if i<4:
            nested='{"id":"0x%x","kind":"UsingType","type":{"qualType":"std::%s"},"decl":{"id":"0x%x","kind":"UsingShadowDecl","name":"%s"},"type":{"qualType":"%s"},"inner":[]}'%(i+1,key,i+17,key,types_map[key])
            raw=raw[:-1]+',"inner":['+nested+']}'
        roots.append(raw)
    for key in legacy.ABI_INTS:
        roots.append(json.dumps(dict(kind='EnumConstantDecl',name='dws_probe_'+key,loc=dict(offset=0,file=str(probe),line=1),inner=[dict(kind='ConstantExpr',value=str(integers[key]))]),separators=(',',':')))
    assert len(roots)==29
    return (' \n'+'\n'.join(roots)+'\n').encode()


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved={name:module for name,module in sys.modules.items() if name=='swdb' or name.startswith('swdb.')}
        for name in cls.saved:sys.modules.pop(name)
        cls.ns=namespace();policy=json.loads((HERE/'controls/policy.json').read_bytes())
        cls.controls={name:row(HERE/'controls'/Path(value['path']).name) for name,value in policy['controls'].items()}
        cls.helper,cls.legacy,cls.api,cls.origins,cls.closed=cls.ns['checked_modules'](dict(controls=cls.controls))
    @classmethod
    def tearDownClass(cls):
        for name in list(sys.modules):
            if name=='swdb' or name.startswith('swdb.'):sys.modules.pop(name)
        sys.modules.update(cls.saved)

    def test_complete_original_refusal_real_transport_inverse_and_legacy_ABI_domain(self):
        with tempfile.TemporaryDirectory(dir=HERE,prefix='synthetic-probe-') as temporary:
            probe=Path(temporary).resolve()/'probe.cpp';probe.write_bytes((WHOLE/'compiler_abi_probe_v1.cpp').read_bytes())
            raw=synthetic_abi(self.legacy,probe)
            with self.assertRaisesRegex(self.legacy.Refused,'malformed compiler JSON stream') as caught:self.legacy.observed_abi(raw,probe_path=probe,api=self.api)
            self.assertEqual(str(caught.exception.__cause__),'duplicate compiler JSON key')
            derived,transport=self.helper._transport(raw,expected_roots=29,expected_renames=4)
            observed=self.legacy.observed_abi(derived,probe_path=probe,api=self.api)
            self.assertEqual(observed['root_count'],29);self.assertEqual(observed['constants']['source_tiles'],32)
            self.assertEqual(observed['abi']['sizes'],[4,4,4,8,8,8]);self.assertEqual(observed['abi']['pointer_bits'],64)
            self.assertEqual(transport['normalization']['original_minified_token_sha256'],transport['inverse']['original_minified_token_sha256'])
            # Only closed-original eligibility is a named protocol stand-in here;
            # source grammar/inverse and the legacy reader above are real code.
            facade=types.SimpleNamespace(normalize_abi=lambda incoming:(derived,dict(transport,selected_family='synthetic29')))
            out=self.ns['replay'](raw,str(probe),facade,self.legacy,self.api,'synthetic29')
            self.assertFalse(out['fresh_compiler_ABI_theorem']);self.assertFalse(out['source_call_or_public_admission'])
            with self.assertRaisesRegex(self.helper.Refused,'exact retained'):self.helper.normalize_abi(raw)

    def test_wrong_geometry_width_roots_and_probe_origin_refuse(self):
        with tempfile.TemporaryDirectory(dir=HERE,prefix='synthetic-probe-') as temporary:
            probe=Path(temporary).resolve()/'probe.cpp';probe.write_bytes((WHOLE/'compiler_abi_probe_v1.cpp').read_bytes());raw=synthetic_abi(self.legacy,probe)
            derived,_=self.helper._transport(raw,expected_roots=29,expected_renames=4)
            for key,value in [('source_tiles','64'),('pointer_bits','32')]:
                roots=[json.loads(line) for line in derived.splitlines()]
                next(v for v in roots if v['name']=='dws_probe_'+key)['inner'][0]['value']=value
                altered=b'\n'.join(json.dumps(v).encode() for v in roots)+b'\n'
                with self.assertRaises(ValueError):self.legacy.observed_abi(altered,probe_path=probe,api=self.api)
            with self.assertRaises(ValueError):self.helper._transport(raw,expected_roots=28,expected_renames=4)
            with self.assertRaises(ValueError):self.helper._transport(raw,expected_roots=29,expected_renames=3)
            other=Path(temporary).resolve()/'other.cpp';other.write_bytes(probe.read_bytes())
            with self.assertRaisesRegex(self.legacy.Refused,'nonlocal ABI'):self.legacy.observed_abi(derived,probe_path=other,api=self.api)

    def test_unknown_duplicate_roles_are_not_repaired(self):
        for raw in (b'{"kind":"TypeAliasDecl","x":1,"x":2}',b'{"kind":"TypeAliasDecl","x":NaN}',b'{"kind":"TypeAliasDecl"} trailing'):
            with self.assertRaises(ValueError):self.helper._transport(raw,expected_roots=1,expected_renames=0)

    def test_input_extent_checked_before_open(self):
        with tempfile.TemporaryDirectory(dir=HERE,prefix='extent-') as temporary:
            path=Path(temporary).resolve()/'input';path.write_bytes(b'x'*1024)
            selected=dict(path=str(path),bytes=1,sha256='0'*64)
            with patch.object(Path,'open',side_effect=AssertionError('must refuse before reading')):
                with self.assertRaisesRegex(ValueError,'extent/identity'):self.ns['physical'](selected,True)

    def test_legacy_and_primitive_full_bytes_and_validator_AST_unchanged(self):
        inverse=json.loads((HERE/'scanner-inverse-v1.json').read_bytes())
        for role,record in inverse['complete_module_bytes_unchanged'].items():
            self.assertEqual(Path(record['basis']['path']).read_bytes(),Path(record['staged']['path']).read_bytes())
        tree=ast.parse((HERE/'controls/whole_interface_v4.py').read_bytes())
        original=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_abi')
        function=ast.parse((HERE/'controls/whole_interface_v4.py').read_bytes())
        self.assertEqual(ast.dump(original),ast.dump(next(n for n in function.body if isinstance(n,ast.FunctionDef) and n.name=='validate_abi')))
        self.assertEqual(self.helper.NORMALIZER_SHA,hashlib.sha256((HERE/'controls/role_normalized_gzip_v2.py').read_bytes()).hexdigest())

    def test_all_identity_and_reader_functions_inverse_exact(self):
        inverse=json.loads((HERE/'scanner-inverse-v1.json').read_bytes());basis=Path(inverse['basis']['path']).read_text();current=(HERE/'replay_entry_v1.py').read_text()
        def functions(text):return {n.name:ast.get_source_segment(text,n) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
        a,b=functions(basis),functions(current)
        self.assertEqual(a['pam_identity'],b['pam_identity']);self.assertEqual(a['scan'],b['scan'])
        self.assertEqual(b['transport_identity'].replace("'185s'","'35s'"),a['transport_identity'])
        self.assertIn(str(Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-tu-2baf722f-v1')),inverse['added_needles'])

    def test_resource_and_readonly_envelope_without_executing_it(self):
        command=json.loads((HERE/'command-v1.json').read_bytes());policy=json.loads((HERE/'controls/policy.json').read_bytes())
        self.assertIn('env -i',command['remote_shell_command']);self.assertIn('185s /usr/bin/python3 -I -B -',command['remote_shell_command'])
        self.assertEqual(policy['resource']['RLIMIT_AS'],512*2**20);self.assertEqual(policy['resource']['wall_seconds'],180)
        self.assertEqual(command['max_stdout_bytes'],65536);self.assertTrue(command['root_once_admission_required'])
        for event,args in [('subprocess.Popen',()),('os.rename',()),('socket.connect',()),('open',('file','wb',1))]:
            with self.assertRaises(PermissionError):self.ns['readonly'](event,args)
        self.ns['readonly']('open',('file','rb',0))

    def test_two_closed_original_families_and_actual_outcomes_remain_prospective(self):
        policy=json.loads((HERE/'controls/policy.json').read_bytes())
        self.assertEqual({row['family']:(row['ABI']['bytes'],row['ABI']['sha256']) for row in policy['artifacts']},self.helper.FAMILIES)
        self.assertEqual(len({row['probe']['path'] for row in policy['artifacts']}),2)
        self.assertTrue(all(row['probe']['bytes']==1588 and row['probe']['sha256']==self.legacy.ABI_PROBE_SHA for row in policy['artifacts']))
        self.assertFalse(policy['fresh_compiler_source_or_public_admission'])
        for path in HERE.rglob('*.py'):ast.parse(path.read_bytes())

if __name__=='__main__':unittest.main(verbosity=2)
