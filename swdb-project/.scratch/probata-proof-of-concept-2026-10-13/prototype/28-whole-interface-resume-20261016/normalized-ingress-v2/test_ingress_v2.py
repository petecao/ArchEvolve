"""2026-10-16 ET: no-child source/inverse and real consumer-seam controls.

Only literal AST fixture identities are substituted in the test namespace. The
actual production legacy prepare_unit/parser/location function ASTs are executed
unchanged on that small JSON TU. No project module or actual AST is imported.
ABI observation and physical source/probe reads are inert fixture doubles.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
import unittest

EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in ('os.system','ctypes.dlopen'):
        EVENTS.append(event);raise ValueError('inert controls refuse '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent
V1=HERE.parent/'normalized-ingress-v1'
LEGACY=HERE.parent/'production-route-v3/proposed/swdb/_dx100_whole/compiler_unit_adapter_v3.py'
WRAPPER=HERE/'proposed/normalized_compiler_adapter_v1.py'
SOURCE=HERE/'proposed/normalized_capture_ingress_v2.py'
SOURCE_BYTES=b'int literal_caller() { return 0; }'
PROBE_BYTES=b'/* inert ABI read double */'
SOURCE_PATH='/inert/source.cpp'
PROBE_PATH='/inert/probe.cpp'

def module_nodes(raw,names):
    return [node for node in ast.parse(raw).body if isinstance(node,ast.Assign) or
        isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name in names]

def consumer():
    class FixturePath:
        def __init__(self,path):self.path=str(path)
        def __str__(self):return self.path
        def resolve(self):return self
        def read_bytes(self):
            if self.path==SOURCE_PATH:return SOURCE_BYTES
            if self.path==PROBE_PATH:return PROBE_BYTES
            raise ValueError('unadmitted fixture read')
    names={'Refused','need','sha','strict_decoder','parse_json_roots','resolve_locations','prepare_unit'}
    code=ast.Module(module_nodes(LEGACY.read_bytes(),names),type_ignores=[])
    abi_calls=[]
    def abi(raw,**kwargs):abi_calls.append((raw,kwargs));return {'abi':{'literal_fixture':True}}
    legacy_env={'copy':copy,'hashlib':hashlib,'json':json,'Path':FixturePath,'re':re,'observed_abi':abi}
    exec(compile(code,str(LEGACY),'exec'),legacy_env)
    call={'kind':'CallExpr','range':{'begin':{'offset':1},'end':{'offset':2}},'inner':[
        {'kind':'DeclRefExpr','referencedDecl':{'name':'wait_ready'}}]}
    tu={'kind':'TranslationUnitDecl','inner':[{'kind':'FunctionDecl','name':'literal_caller','mangledName':'_Z14literal_callerv',
        'loc':{'file':SOURCE_PATH,'line':1,'offset':0},'inner':[call]}]}
    raw=json.dumps(tu,separators=(',',':')).encode()
    calls=[]
    def delegate(*args,**kwargs):
        calls.append(kwargs)
        return legacy_env['prepare_unit'](*args,**kwargs)
    wrapper_env={'hashlib':hashlib,'Path':Path,'legacy':SimpleNamespace(__file__=str(LEGACY),prepare_unit=delegate)}
    exec(compile(ast.Module(module_nodes(WRAPPER.read_bytes(),{'need','prepare_unit'}),type_ignores=[]),str(WRAPPER),'exec'),wrapper_env)
    # These changes exist only in this private literal test namespace. The
    # production source pins and exact actual stream constants remain fixed.
    wrapper_env.update(EXPANDED_BYTES=len(raw),EXPANDED_SHA=hashlib.sha256(raw).hexdigest(),COMPRESSED_BYTES=13)
    api={'_span':lambda node:(node['range']['begin']['offset'],node['range']['end']['offset']),
        'bind_call':lambda tree,**kwargs:{'caller_mangled':kwargs['caller'],'call_range':kwargs['call_range']}}
    kwargs={'full_tu_raw':raw,'abi_raw':b'ABI-LITERAL-DOUBLE','source_path':SOURCE_PATH,'source_bytes':SOURCE_BYTES,
        'probe_path':PROBE_PATH,'probe_bytes':PROBE_BYTES,'declarations':[{'name':'wait_ready'}],
        'compiler_capture_pin':'0'*64,'full_tu_compressed_bytes':13,'full_tu_expanded_limit':201326592}
    return legacy_env,wrapper_env,api,kwargs,calls,abi_calls


class Controls(unittest.TestCase):
    def test_exact_inverse_and_unchanged_ingress_gates(self):
        inverse=json.loads((HERE/'inverse-v2.json').read_bytes());raw=SOURCE.read_text()
        self.assertEqual(len(inverse['edits']),4)
        for change in reversed(inverse['edits']):
            at=change['offset'];self.assertEqual(raw[at:at+len(change['new'])],change['new'])
            raw=raw[:at]+change['old']+raw[at+len(change['new']):]
        self.assertEqual(raw.encode(),(V1/'proposed/normalized_capture_ingress_v1.py').read_bytes())
        def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef)}
        old,new=functions(V1/'proposed/normalized_capture_ingress_v1.py'),functions(SOURCE)
        self.assertEqual(set(old),set(new))
        self.assertTrue(all(old[name]==new[name] for name in old if name!='complete_capture'))
        self.assertEqual(hashlib.sha256(LEGACY.read_bytes()).hexdigest(),'775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c')

    def test_actual_production_constants_are_the_known_transport(self):
        assignments={n.targets[0].id:ast.literal_eval(n.value) for n in ast.parse(WRAPPER.read_bytes()).body if isinstance(n,ast.Assign)}
        self.assertEqual(assignments['EFFECTIVE_LIMIT'],201326592)
        self.assertEqual(assignments['LEGACY_CEILING'],536870912)
        self.assertEqual(assignments['EXPANDED_BYTES'],178924116)
        self.assertEqual(assignments['COMPRESSED_BYTES'],12787585)
        self.assertEqual(assignments['EXPANDED_SHA'],'1f0616302273d146fc88e1c676d25c41230432ee8ec259a92ae65f8fbb5755a3')
        self.assertEqual(assignments['KIND'],'complete-original-tu-paired-type-gzip-2')

    def test_real_legacy_192_refuses_and_512_remains_unchanged(self):
        legacy,wrapper,api,kwargs,calls,abi_calls=consumer()
        with self.assertRaisesRegex(ValueError,'bounded lossless caller ingress'):legacy['prepare_unit'](api,**kwargs)
        self.assertEqual(abi_calls,[])
        prepared=legacy['prepare_unit'](api,**dict(kwargs,full_tu_expanded_limit=536870912))
        self.assertEqual(prepared['schema'],'whole-interface-original-tu-preparation-1')
        self.assertEqual(len(prepared['calls']),1)
        self.assertNotIn('normalized_transport',prepared)

    def test_stricter_wrapper_reaches_real_legacy_parser_and_call_preparation(self):
        legacy,wrapper,api,kwargs,calls,abi_calls=consumer()
        prepared=wrapper['prepare_unit'](api,transport_kind=wrapper['KIND'],**kwargs)
        self.assertEqual(len(calls),1);self.assertIs(calls[0]['full_tu_raw'],kwargs['full_tu_raw'])
        self.assertEqual(calls[0]['full_tu_expanded_limit'],536870912)
        self.assertEqual(len(abi_calls),1);self.assertEqual(len(prepared['calls']),1)
        self.assertEqual(prepared['schema'],'whole-interface-normalized-original-tu-preparation-1')
        self.assertEqual(prepared['normalized_transport']['effective_expanded_limit_bytes'],201326592)
        self.assertEqual(prepared['normalized_transport']['legacy_consumer_implementation_ceiling_bytes'],536870912)
        self.assertFalse(prepared['normalized_transport']['original_wire_identity_is_normalized_identity'])
        self.assertFalse(prepared['public_admission'])

    def test_wrong_transport_and_type_extent_hash_limit_refuse_before_delegate(self):
        for change in ({'transport_kind':'lossless-complete-original-tu-v1'},{'full_tu_expanded_limit':536870912},
            {'full_tu_expanded_limit':True},{'full_tu_raw':bytearray(b'wrong')},{'full_tu_raw':b'wrong'},
            {'full_tu_compressed_bytes':True},{'full_tu_compressed_bytes':14}):
            legacy,wrapper,api,kwargs,calls,abi_calls=consumer();selected={'transport_kind':wrapper['KIND'],**kwargs};selected.update(change)
            with self.subTest(change=change):
                with self.assertRaises(ValueError):wrapper['prepare_unit'](api,**selected)
                self.assertEqual(calls,[]);self.assertEqual(abi_calls,[])
        legacy,wrapper,api,kwargs,calls,abi_calls=consumer();raw=kwargs['full_tu_raw'];changed=raw.replace(b'wait_ready',b'wait_reado')
        self.assertEqual(len(raw),len(changed))
        with self.assertRaises(ValueError):wrapper['prepare_unit'](api,transport_kind=wrapper['KIND'],**dict(kwargs,full_tu_raw=changed))
        self.assertEqual(calls,[])

    def test_real_legacy_receipt_validation_and_primitive_copies_stay_closed(self):
        legacy,wrapper,api,kwargs,calls,abi_calls=consumer()
        with self.assertRaisesRegex(ValueError,'receipt pin required'):
            wrapper['prepare_unit'](api,transport_kind=wrapper['KIND'],**dict(kwargs,compiler_capture_pin='bad'))
        self.assertEqual(len(calls),1);self.assertEqual(abi_calls,[])
        for name in ('closed_python_surface.py','role_normalized_gzip_v2.py','lossless_gzip_v2.py'):
            self.assertEqual((HERE/'proposed'/name).read_bytes(),(V1/'proposed'/name).read_bytes())

    def test_no_child_or_project_import(self):self.assertEqual(EVENTS,[])

if __name__=='__main__':unittest.main(verbosity=2)
