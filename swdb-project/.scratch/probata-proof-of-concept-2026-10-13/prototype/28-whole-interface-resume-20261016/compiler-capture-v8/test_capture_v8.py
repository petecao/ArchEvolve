"""2026-10-16 ET. Source inverses and synthetic stdlib/no-child gzip controls."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
import zlib

EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('lossless pure controls refuse '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;LOSSLESS=WHOLE/'lossless-capture-v1'

def load(path):
    result={'__name__':'inert_lossless_controls','__file__':str(path)}
    exec(compile(path.read_bytes(),str(path),'exec'),result);return result

C=load(LOSSLESS/'lossless_gzip_v1.py')
A=load(LOSSLESS/'compiler_unit_adapter_v3.py')
OLD_A=load(WHOLE/'compiler_unit_adapter_v2.py')
ENTRY=HERE/'linux_compiler_capture_v8.py';SOURCE=ENTRY.read_bytes();E=load(ENTRY)

def compress(data,*,expanded=536870912,compressed=134217728,chunk=65536,check=lambda:None):
    sink=io.BytesIO();writer=C['Capture'](zlib,sink,expanded_limit=expanded,compressed_limit=compressed,check=check)
    for start in range(0,len(data),chunk):writer.feed(data[start:start+chunk])
    receipt=writer.finish();return sink.getvalue(),receipt


def decode(payload,receipt,*,expanded=536870912,compressed=134217728,check=lambda:None):
    return C['decode'](zlib,io.BytesIO(payload),receipt,expanded_limit=expanded,compressed_limit=compressed,check=check)


class Controls(unittest.TestCase):
    def test_lossless_roundtrip_raw_and_retained_hashes_match(self):
        data=(b'{"complete original TU with whitespace":true}\n'*8000)+b'END'
        payload,receipt=compress(data,chunk=7)
        self.assertEqual(decode(payload,receipt),data)
        self.assertEqual(receipt['expanded_sha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(receipt['compressed_sha256'],hashlib.sha256(payload).hexdigest())
        self.assertEqual((receipt['expanded_bytes'],receipt['compressed_bytes']),(len(data),len(payload)))
        self.assertEqual(payload[:2],b'\x1f\x8b')
        self.assertEqual(EVENTS,[])

    def test_expanded_and_retained_caps_are_distinct_and_fail_before_writing_overflow(self):
        sink=io.BytesIO();writer=C['Capture'](zlib,sink,expanded_limit=3,compressed_limit=100,check=lambda:None)
        with self.assertRaisesRegex(C['Refused'],'expanded compiler'):writer.feed(b'four')
        self.assertEqual(sink.getvalue(),b'')
        sink=io.BytesIO();writer=C['Capture'](zlib,sink,expanded_limit=1000,compressed_limit=10,check=lambda:None)
        writer.feed(b'aaa')
        with self.assertRaisesRegex(C['Refused'],'retained gzip'):writer.finish()
        self.assertLessEqual(len(sink.getvalue()),10)
        for expanded,compressed in ((0,1),(True,100),(536870913,10),(100,134217729)):
            with self.assertRaises(C['Refused']):compress(b'x',expanded=expanded,compressed=compressed)

    def test_strict_single_member_corruption_truncation_and_trailing_data_refuse(self):
        payload,receipt=compress(b'complete bytes'*1000)
        for bad in (payload[:-1],payload[:8],payload+b' ',payload+payload,bytes([payload[0]^1])+payload[1:],
            payload[:-8]+bytes([payload[-8]^1])+payload[-7:],zlib.compress(b'complete bytes'*1000)):
            with self.subTest(length=len(bad)),self.assertRaises(C['Refused']):decode(bad,receipt)

    def test_receipt_shapes_types_hashes_counts_and_profiles_refuse_mutations(self):
        payload,receipt=compress(b'exact bytes')
        for key,value in (('expanded_bytes',9),('compressed_bytes',1),('expanded_sha256','a'*64),
            ('compressed_sha256','b'*64),('level',9),('wbits',47),('expanded_limit',1),('compressed_limit',True),
            ('codec','zlib'),('compiler_zero_exit_and_source_runtime_checks_separately_required',False)):
            changed=dict(receipt);changed[key]=value
            with self.subTest(key=key),self.assertRaises(C['Refused']):decode(payload,changed)
        changed=dict(receipt);changed['extra']=True
        with self.assertRaises(C['Refused']):decode(payload,changed)

    def test_decoder_expansion_limit_stops_repetitive_bomb_with_bounded_emits(self):
        payload,receipt=compress(b'A'*500000)
        receipt=dict(receipt,expanded_limit=100,expanded_bytes=100)
        with self.assertRaisesRegex(C['Refused'],'expanded decode'):decode(payload,receipt,expanded=100)
        # Exact limit also permits complete trailer consumption without unbounded flush.
        payload,receipt=compress(b'A'*65536,expanded=65536)
        self.assertEqual(decode(payload,receipt,expanded=65536),b'A'*65536)

    def test_decoder_short_reads_and_callback_deadlines(self):
        data=b'bounded original bytes'*8000;payload,receipt=compress(data)
        class Source:
            def __init__(self):self.at=0
            def read(self,count):
                self_count=count
                if self_count>65536:raise AssertionError('unbounded read')
                result=payload[self.at:self.at+7];self.at+=len(result);return result
        self.assertEqual(C['decode'](zlib,Source(),receipt,expanded_limit=536870912,compressed_limit=134217728,check=lambda:None),data)
        def stop():raise ValueError('entry deadline')
        with self.assertRaisesRegex(ValueError,'entry deadline'):decode(payload,receipt,check=stop)
        with self.assertRaisesRegex(ValueError,'entry deadline'):compress(data,check=stop)

    def test_capture_refuses_empty_oversize_chunks_short_sink_and_double_finish(self):
        class ShortSink:
            def write(self,data):return max(0,len(data)-1)
        with self.assertRaisesRegex(C['Refused'],'short gzip'):C['Capture'](zlib,ShortSink(),expanded_limit=100,compressed_limit=100,check=lambda:None).feed(b'x')
        sink=io.BytesIO();writer=C['Capture'](zlib,sink,expanded_limit=100000,compressed_limit=1000,check=lambda:None)
        for chunk in (b'',b'A'*65537):
            with self.assertRaises(C['Refused']):writer.feed(chunk)
        with self.assertRaises(C['Refused']):writer.finish()
        writer.feed(b'x');writer.finish()
        with self.assertRaises(C['Refused']):writer.finish()
        with self.assertRaises(C['Refused']):writer.feed(b'x')

    def test_adapter_preserves_full_json_parser_output_and_strict_refusals(self):
        raw=b'{"kind":"TranslationUnitDecl","inner":[{"kind":"VarDecl","name":"x"}]}'
        self.assertEqual(A['parse_json_roots'](raw,full_tu=True,expanded_limit=536870912),OLD_A['parse_json_roots'](raw,full_tu=True))
        for bad in (raw+b'{}',raw[:-1],b'{"kind":"TranslationUnitDecl","kind":"TranslationUnitDecl"}',b'[]',b'{"kind":NaN}'):
            with self.assertRaises(A['Refused']):A['parse_json_roots'](bad,full_tu=True,expanded_limit=536870912)

    def test_adapter_expanded_allowance_never_changes_abi_or_retained_constants(self):
        raw=json.dumps({'kind':'TranslationUnitDecl','inner':[],'padding':'x'*2000}).encode()
        original=A['STAGE_BYTES'];A['STAGE_BYTES']=1024
        try:
            with self.assertRaises(A['Refused']):A['parse_json_roots'](raw,full_tu=True)
            self.assertEqual(A['parse_json_roots'](raw,full_tu=True,expanded_limit=4096)[0]['kind'],'TranslationUnitDecl')
            for full,bound in ((False,4096),('True',4096),(True,536870913),(True,True),(True,0)):
                with self.assertRaises(A['Refused']):A['parse_json_roots'](raw,full_tu=full,expanded_limit=bound)
        finally:A['STAGE_BYTES']=original
        self.assertEqual((A['STAGE_BYTES'],A['TOTAL_BYTES']),(134217728,268435456))

    def test_exact_adapter_inverse_and_every_other_function_ast_unchanged(self):
        delta=json.loads((HERE/'compiler-capture-v8-inverse.json').read_bytes())
        current=(LOSSLESS/'compiler_unit_adapter_v3.py').read_text();inverse=current
        for edit in reversed(delta['adapter_edits']):
            self.assertEqual(inverse.count(edit['new']),1);inverse=inverse.replace(edit['new'],edit['old'],1)
        original=Path(delta['adapter_predecessor']['path']).read_text();self.assertEqual(inverse,original)
        before={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(original).body if isinstance(n,ast.FunctionDef)}
        after={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(current).body if isinstance(n,ast.FunctionDef)}
        self.assertEqual(set(before),set(after))
        for name in before:
            if name not in {'parse_json_roots','prepare_unit'}:self.assertEqual(before[name],after[name])

    def test_entry_inverse_all_old_nonmain_functions_resources_and_stat_fields_exact(self):
        delta=json.loads((HERE/'compiler-capture-v8-inverse.json').read_bytes());inverse=SOURCE.decode()
        for edit in reversed(delta['entry_edits']):
            self.assertEqual(inverse.count(edit['new']),1);inverse=inverse.replace(edit['new'],edit['old'],1)
        original=Path(delta['predecessor']['path']).read_text();self.assertEqual(inverse,original)
        before={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(original).body if isinstance(n,ast.FunctionDef)}
        after={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(SOURCE).body if isinstance(n,ast.FunctionDef)}
        self.assertEqual(set(after)-set(before),{'bind_zlib','lossless_recipe','stream_caller_ast'})
        for name in before:
            if name!='main':self.assertEqual(before[name],after[name])
        self.assertEqual((E['ENTRY_SECONDS'],E['WHOLE_SECONDS'],E['RSS_BYTES'],E['STAGE_BYTES'],E['TOTAL_BYTES'],E['FINAL_METADATA_RESERVE']),
            (165,180,4294967296,134217728,268435456,1048576))

    def test_exact_staged_membership_pins_and_unchanged_runtime_source_role_guards(self):
        policy_path=HERE/'linux_compiler_capture_policy_v8.json';policy=json.loads(policy_path.read_bytes())
        old=json.loads((WHOLE/'compiler-capture-v7/linux_compiler_capture_policy_v7.json').read_bytes())
        for key in old:
            if key not in {'schema','raw_name','entry_sha256','controller_files','capture_recipe'}:self.assertEqual(policy[key],old[key])
        command=json.loads((HERE/'linux_compiler_capture_command_v8.json').read_bytes())
        controls={Path(row['path']).name:{key:row[key] for key in ('bytes','sha256')} for row in command['controller_inputs']}
        self.assertEqual(set(controls),set(policy['controller_files'])|{policy_path.name})
        for row in command['controller_inputs']:
            data=Path(row['path']).read_bytes();self.assertEqual(len(data),row['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'])
        self.assertEqual(command['argv'][-1],hashlib.sha256(policy_path.read_bytes()).hexdigest())
        self.assertLess(sum(row['bytes'] for row in command['controller_inputs']),1048576)
        self.assertEqual(command['root_guard'],json.loads((WHOLE/'compiler-capture-v7/linux_compiler_capture_command_v7.json').read_bytes())['root_guard'])
        self.assertFalse(command['actual_launched']);self.assertFalse(command['public_proof'])

    def test_four_original_argv_unchanged_except_fresh_namespace_no_caller_filter(self):
        new=json.loads((HERE/'linux_compiler_capture_policy_v8.json').read_bytes())['capture_recipe']
        old=json.loads((WHOLE/'compiler-capture-v7/linux_compiler_capture_policy_v7.json').read_bytes())['capture_recipe']
        self.assertEqual(len(new['commands']),4)
        for before,after in zip(old['commands'],new['commands']):
            expected=[part.replace('full-tu-2baf722f-v7','full-tu-2baf722f-v8') for part in before['argv']]
            self.assertEqual(after['argv'],expected)
        self.assertFalse(any('ast-dump-filter' in item for item in new['commands'][1]['argv']))
        self.assertTrue(new['commands'][1]['stdout'].endswith('caller.ast.json.gz'))
        self.assertEqual(new['lossless_caller_stdout']['expanded_limit'],536870912)
        self.assertEqual(new['budgets'],old['budgets'])

    def test_zlib_origin_is_actual_root_builtin_and_existing_native_closure(self):
        policy=json.loads((HERE/'linux_compiler_capture_policy_v8.json').read_bytes())
        origin=next(row for row in json.loads((HERE/'linux_compiler_capture_command_v8.json').read_bytes())['controller_inputs']
            if Path(row['path']).name=='t28-selected-python-zlib-origin-observation-20261016.json')
        self.assertEqual(origin['sha256'],'bc53f66a5c159b43af8b3fbc69a0ec367c39197589e57fd8af505e5730ae4e3d')
        observed=json.loads(Path(origin['path']).read_bytes());binding=policy['zlib_binding']
        self.assertEqual(binding,{key:observed[key] for key in binding})
        self.assertEqual(binding['builtin'],1);self.assertEqual(binding['spec_origin'],'built-in');self.assertIsNone(binding['module_file'])
        self.assertIn(binding['physical_interpreter'],policy['native_runtime']['pins'])
        self.assertTrue(all(row in policy['native_runtime']['pins'] for row in binding['mapped_compression_objects']))
        self.assertNotIn('scope',binding)
        source=(WHOLE.parents[1]/'prototype/resume-root-20261016/observe_zlib_origin_v1.py').read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(),'e91bb40d169616dc89f1c811fceb5ec0fb409f5d0701588041ff3d882fc808da')
        self.assertEqual(len(b'probe-origin-only'),17)

    def test_policy_and_command_complete_json_inverses(self):
        delta=json.loads((HERE/'compiler-capture-v8-inverse.json').read_bytes())
        for key in ('policy','command'):
            current=json.loads(Path(delta[key]['path']).read_bytes())
            previous=json.loads(Path(delta['old_'+key]['path']).read_bytes())
            for edit in reversed(delta[key+'_edits']):
                if not edit['path']:
                    self.assertEqual(current,edit['new']);current=copy.deepcopy(edit['old']);continue
                cursor=current
                for part in edit['path'][:-1]:cursor=cursor[part]
                leaf=edit['path'][-1];operation=edit.get('operation','replace')
                if operation=='add':self.assertEqual(cursor.pop(leaf),edit['new'])
                elif operation=='remove':self.assertNotIn(leaf,cursor);cursor[leaf]=copy.deepcopy(edit['old'])
                else:self.assertEqual(cursor[leaf],edit['new']);cursor[leaf]=copy.deepcopy(edit['old'])
            self.assertEqual(current,previous)

    def test_whole_synthetic_prepare_matches_old_semantics_after_lossless_decode(self):
        fixture=load(WHOLE/'test_compiler_unit_adapter_v2.py')
        case=fixture['Controls']();type(case).setUpClass()
        try:
            declaration=next(row for row in case.declarations if row['name']=='maa_alu_scalar')
            tu,_args=case.fixture(declaration);probe=WHOLE/'compiler_abi_probe_v1.cpp'
            raw=json.dumps(tu).encode();payload,receipt=compress(raw)
            arguments=dict(full_tu_raw=raw,abi_raw=fixture['stream'](fixture['abi_roots']()),source_path=case.source,
                source_bytes=case.source.read_bytes(),probe_path=probe,probe_bytes=probe.read_bytes(),
                declarations=case.declarations,compiler_capture_pin='a'*64)
            expected=OLD_A['prepare_unit'](fixture['API'],**arguments)
            arguments['full_tu_raw']=decode(payload,receipt)
            arguments.update(full_tu_compressed_bytes=len(payload),full_tu_expanded_limit=536870912)
            self.assertEqual(A['prepare_unit'](fixture['API'],**arguments),expected)
            for key,value in (('full_tu_compressed_bytes',134217729),('full_tu_compressed_bytes',True),
                ('full_tu_expanded_limit',True),('full_tu_expanded_limit',536870913)):
                changed=dict(arguments);changed[key]=value
                with self.assertRaises(A['Refused']):A['prepare_unit'](fixture['API'],**changed)
        finally:type(case).tearDownClass()

    def mocked_collector(self,*,returncode=0,raise_on_read=False):
        chunks=iter([b'{"kind":"TranslationUnitDecl","inner":[]}',b''])
        events=[]
        class Pipe:
            def fileno(self):return 55
            def close(self):events.append('closed')
        class Process:
            stdout=Pipe();pid=123
            def wait(self,timeout=None):return returncode
        class Selection:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def register(self,*args):pass
            def select(self,timeout):return [True]
        def read(fd,count):
            self.assertEqual(count,65536)
            if raise_on_read:raise ValueError('synthetic collector failure')
            return next(chunks)
        saved={key:E[key] for key in ('subprocess','selectors','os')}
        E['subprocess']=types.SimpleNamespace(PIPE=object(),Popen=lambda *args,**kwargs:Process())
        E['selectors']=types.SimpleNamespace(DefaultSelector=Selection,EVENT_READ=1)
        E['os']=types.SimpleNamespace(set_blocking=lambda *args:None,read=read,killpg=lambda *args:events.append('killed'))
        return events,saved

    def test_collector_mock_preserves_complete_stdout_and_retained_receipt(self):
        events,saved=self.mocked_collector()
        try:
            with tempfile.TemporaryDirectory() as temp:
                out=Path(temp).resolve();row={}
                E['stream_caller_ast']({'stdout':str(out/'caller.ast.json.gz'),'argv':['inert-no-execution']},out=out,
                    environment={},remaining=45,bytes_used=lambda:0,limit=lambda:None,codec=types.SimpleNamespace(**C),zlib_module=zlib,row=row)
                receipt=json.loads((out/'caller.ast.gzip.json').read_bytes())
                self.assertEqual(decode((out/'caller.ast.json.gz').read_bytes(),receipt),b'{"kind":"TranslationUnitDecl","inner":[]}')
                self.assertEqual(row['returncode'],0);self.assertEqual(events,['closed'])
        finally:E.update(saved)

    def test_collector_mock_nonzero_and_read_failures_kill_wait_and_never_finish_receipt(self):
        for returncode,raise_on_read in ((-25,False),(0,True)):
            events,saved=self.mocked_collector(returncode=returncode,raise_on_read=raise_on_read)
            try:
                with tempfile.TemporaryDirectory() as temp:
                    out=Path(temp).resolve();row={}
                    with self.assertRaises(ValueError):
                        E['stream_caller_ast']({'stdout':str(out/'caller.ast.json.gz'),'argv':['inert-no-execution']},out=out,
                            environment={},remaining=45,bytes_used=lambda:0,limit=lambda:None,codec=types.SimpleNamespace(**C),zlib_module=zlib,row=row)
                    self.assertFalse((out/'caller.ast.gzip.json').exists());self.assertEqual(events,['killed','closed'])
            finally:E.update(saved)
        self.assertEqual(EVENTS,[])


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'child_events':EVENTS,
        'controller_sha256':hashlib.sha256(SOURCE).hexdigest(),'adapter_sha256':hashlib.sha256((LOSSLESS/'compiler_unit_adapter_v3.py').read_bytes()).hexdigest(),
        'codec_sha256':hashlib.sha256((LOSSLESS/'lossless_gzip_v1.py').read_bytes()).hexdigest(),
        'policy_sha256':hashlib.sha256((HERE/'linux_compiler_capture_policy_v8.json').read_bytes()).hexdigest(),
        'command_sha256':hashlib.sha256((HERE/'linux_compiler_capture_command_v8.json').read_bytes()).hexdigest(),
        'controls_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'actual_controller_compiler_native_or_network':False},sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun==18 and not result.skipped and not EVENTS else 1)
