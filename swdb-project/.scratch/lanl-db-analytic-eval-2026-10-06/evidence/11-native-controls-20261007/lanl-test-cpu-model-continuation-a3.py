"""Portable conditional-a3 guard tests only; source C/active a2 and remote host untouched."""
import ast,copy,contextlib,hashlib,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path('/private/tmp');DISPATCH=ROOT/'lanl-dispatch-cpu-model-continuation-a3.py';EXPORT=ROOT/'lanl-export-cpu-model-continuation-a3.py'
spec=importlib.util.spec_from_file_location('a3_conditional',DISPATCH);m=importlib.util.module_from_spec(spec)
with patch('subprocess.check_output',side_effect=AssertionError('import must be inert')),patch('subprocess.Popen',side_effect=AssertionError('import must be inert')):spec.loader.exec_module(m)
spec=importlib.util.spec_from_file_location('a2_guard_tests',ROOT/'lanl-test-cpu-model-continuation-a2.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
base.m=m;base.DISPATCH=DISPATCH;base.EXPORT=EXPORT

@contextlib.contextmanager
def failure_case():
    with tempfile.TemporaryDirectory(prefix='model-a3-chain-fixture-') as folder:
        root=Path(folder);first=root/'a1';failed=root/'a2';first.mkdir();failed.mkdir()
        (first/'records').mkdir();(first/'records/target.yaml').write_text('id: immutable-complete-target\n')
        original={'source_commit':m.C,'raw_directory':str(first),'phase':'model','cause':'metadata_processing_cap','application_performance_timings_collected':False,'completed_record_files':m.inventory(first/'records')}
        original['identity_sha256']=m.digest(original)
        shutil.copytree(first/'records',failed/'records');(failed/'records/protocol.yaml').write_text('id: complete-protocol\n')
        m.dump(failed/'failure-custody.json',original)
        pre={'phase':'model','source_commit':m.C,'source_clean':True,'continuation_helper_sha256':m.ACTIVE_A2_SHA,'failure_custody_identity':original['identity_sha256'],'scientific_recipe_changed':False,'native_or_provider_commands':0,'limits':{'runner_s':8000,'outer_s':8200,'metadata_stage_s':1100,'final_validate_s':1000,'scientific_collector_s_unchanged':900}}
        pre['identity_sha256']=m.digest(pre);m.dump(failed/'preregistration.json',pre)
        shutil.copyfile(ROOT/'lanl-dispatch-cpu-model-continuation-a2.py',failed/'runner.py')
        (failed/'runner-error.txt').write_text('TimeoutExpired: freeze-bfs processing deadline\n')
        (failed/'runner-exit-code.txt').write_text('1\n');(failed/'exit-code.txt').write_text('1\n')
        (failed/'started.txt').write_text('2026-10-07T05:29:00+00:00');(failed/'completed.txt').write_text('2026-10-07T05:49:00+00:00')
        m.dump(failed/'final-cleanup.json',{'survivors':{}})
        receipt={'source_commit':m.C,'raw_directory':str(failed),'phase':'model','cause':'metadata_processing_cap','application_performance_timings_collected':False,'runner_error_sha256':m.sha(failed/'runner-error.txt'),'runner_py_sha256':m.sha(failed/'runner.py'),'completed_record_files':m.inventory(failed/'records'),'original_a1_failure_custody_identity':original['identity_sha256']}
        receipt['identity_sha256']=m.digest(receipt)
        with patch.object(m,'ORIGINAL_A1_RAW',first),patch.object(m,'ORIGINAL_A1_IDENTITY',original['identity_sha256']):yield failed,receipt,pre,original

def seal(value):value['identity_sha256']=m.digest({k:v for k,v in value.items() if k!='identity_sha256'});return value

class Guards(base.Guards):
    def test_actual_reuse_loop_preserves_both_raw_requests_without_freeze(self):
        chars,target,protocols,estimates=base.sample()
        class FakeStore:
            def of_kind(self,kind):
                assert kind=='protocol';return [SimpleNamespace(data=p) for p in protocols.values()]
        function=next(n for n in ast.parse(DISPATCH.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='run_model')
        loop=next(n for n in ast.walk(function) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='kernel')
        with tempfile.TemporaryDirectory(prefix='a3-reused-protocol-requests-') as folder:
            raw=Path(folder);reused=[];selected={};bindings=[]
            def no_command(*args,**kwargs):raise AssertionError('complete protocol was refrozen')
            env={'request':m.request,'select_protocol':m.select_protocol,'dump':m.dump,'RAW':raw,'store':FakeStore(),'chars':chars,'reused':reused,'protocols':selected,'target':target,'TARGET':m.TARGET,'CHARS':m.CHARS,'digest':m.digest,'bfs_protocol':SimpleNamespace(verify_immutable=lambda p:None),'estimate_protocol':SimpleNamespace(validate_frozen=lambda p,s:None,bind=lambda s,p,c,t:bindings.append((p,c['id']))),'run':no_command,'Store':no_command}
            exec(compile(ast.Module(body=[loop],type_ignores=[]),'production-protocol-reuse-loop','exec'),env)
            self.assertEqual(len(reused),2);self.assertEqual(len(bindings),4)
            for kernel in ('bfs','bc'):
                self.assertEqual(json.loads((raw/(kernel+'-protocol-request.json')).read_text()),m.request(kernel,chars))
                self.assertEqual(selected[kernel],protocols[kernel])
    def test_processing_failure_custody_and_completed_bytes(self):
        with failure_case() as (failed,receipt,pre,original):
            self.assertEqual(m.failure_guard(receipt,failed),receipt)
            wrong=copy.deepcopy(receipt);wrong['source_commit']='b'*40;seal(wrong)
            with self.assertRaises(AssertionError):m.failure_guard(wrong,failed)
            (failed/'records/target.yaml').write_text('id: mutated\n')
            with self.assertRaises(AssertionError):m.failure_guard(receipt,failed)
    def test_nonprocessing_failure_and_success_not_resumed(self):
        with failure_case() as (failed,receipt,pre,original):
            for text in ('AssertionError: unknown whole-call result retained\n','AssertionError: scientific gap\n'):
                (failed/'runner-error.txt').write_text(text);receipt['runner_error_sha256']=m.sha(failed/'runner-error.txt');seal(receipt)
                with self.assertRaises(AssertionError):m.failure_guard(receipt,failed)
            (failed/'runner-error.txt').write_text('TimeoutExpired: freeze-bfs processing deadline\n');receipt['runner_error_sha256']=m.sha(failed/'runner-error.txt');seal(receipt)
            (failed/'acceptance.json').write_text('{}')
            with self.assertRaises(AssertionError):m.failure_guard(receipt,failed)
    def test_ast_caps_cleanup_and_export_shape(self):
        source,exported=DISPATCH.read_text(),EXPORT.read_text();tree=ast.parse(source);ast.parse(exported)
        self.assertEqual((m.INNER_S,m.OUTER_S,m.META_S,m.VALIDATE_S),(15000,15200,1800,1400))
        self.assertEqual(m.ALLOWED,{'freeze-protocol','estimate','validate'})
        for forbidden in ('collect-cpu-native-validation','freeze-cpu-error-band','validate-cpu-error-band','cpu-service-calibrate','cpu-memory-calibrate','codex exec','claude -p'):self.assertNotIn(forbidden,source)
        names=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
        self.assertGreaterEqual(names.count('stop_group'),2);self.assertIn('cleanup.cleanup_owned',names)
        self.assertIn('.prctl(36, 1, 0, 0, 0)',source);self.assertIn('deadline - time.monotonic() - 45',source)
        self.assertIn('17-linux-cleanup-smoke-mbit10-20261006-a1.json',source)
        self.assertIn("['estimate'] * 4 + ['protocol'] * 2 + ['target_description']",exported);self.assertIn('len(paths) == 8',exported)
        self.assertIn("proof['application_performance_timings_collected'] is False",exported)
        self.assertIn("module.preserve(raw / 'records', custody['completed_record_files'])",exported)
        self.assertIn("'original_a1_failure_custody'",exported)
    def test_original_a1_lineage_change_refused(self):
        with failure_case() as (failed,receipt,pre,original):
            receipt['original_a1_failure_custody_identity']='b'*64;seal(receipt)
            with self.assertRaises(AssertionError):m.failure_guard(receipt,failed)
            receipt['original_a1_failure_custody_identity']=original['identity_sha256'];seal(receipt)
            tampered=copy.deepcopy(original);tampered['completed_record_files']={};seal(tampered);m.dump(failed/'failure-custody.json',tampered)
            with self.assertRaises(AssertionError):m.failure_guard(receipt,failed)
    def test_actual_a2_helper_and_limit_pins_refused_if_changed(self):
        for field in ('helper','cap','commands','prior'):
            with self.subTest(field=field),failure_case() as (failed,receipt,pre,original):
                if field=='helper':pre['continuation_helper_sha256']='b'*64
                elif field=='cap':pre['limits']['metadata_stage_s']=9999
                elif field=='commands':pre['native_or_provider_commands']=1
                else:pre['failure_custody_identity']='b'*64
                seal(pre);m.dump(failed/'preregistration.json',pre)
                with self.assertRaises(AssertionError):m.failure_guard(receipt,failed)
    def test_preserved_a1_target_must_remain_in_a2_manifest(self):
        with failure_case() as (failed,receipt,pre,original):
            receipt['completed_record_files'].pop('target.yaml');seal(receipt)
            with self.assertRaises(AssertionError):m.failure_guard(receipt,failed)
    def test_completed_success_or_running_attempt_refused(self):
        with failure_case() as (failed,receipt,pre,original):
            (failed/'runner-exit-code.txt').write_text('0')
            with self.assertRaises(AssertionError):m.failure_guard(receipt,failed)
            (failed/'runner-exit-code.txt').unlink()
            with self.assertRaises(FileNotFoundError):m.failure_guard(receipt,failed)
    def test_scientific_functions_and_active_a2_bytes_unchanged(self):
        previous=(ROOT/'lanl-dispatch-cpu-model-continuation-a2.py').read_text();current=DISPATCH.read_text()
        def funcs(text):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
        a,b=funcs(previous),funcs(current)
        for name in ('metadata_argv','request','select_protocol','estimate_guard','estimate_command','freeze_command','admitted'):self.assertEqual(a[name],b[name])
        self.assertEqual(m.sha(ROOT/'lanl-dispatch-cpu-model-continuation-a2.py'),m.ACTIVE_A2_SHA)
        self.assertEqual(m.sha(ROOT/'lanl-export-cpu-model-continuation-a2.py'),'347a807c8ddab990cfea52419aa13a03dd5d2a3d6d4d5ac1eabc4388a8dfd837')

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Guards))
    proof={'scope':'Conditional administrative a3 guards: inert import, failed-only unchanged-chain custody, complete-output reuse, absent public metadata commands, scope/tamper/cap/cleanup/export checks. No remote/native/provider execution.','passed':result.wasSuccessful(),'tests':result.testsRun,'dispatch_sha256':m.sha(DISPATCH),'export_sha256':m.sha(EXPORT),'source_commit':m.C,'estimator_sha256':m.BUNDLE,'original_a1_custody_identity':m.ORIGINAL_A1_IDENTITY,'active_a2_mutated':False,'remote_execution':False}
    proof['identity_sha256']=m.digest(proof);(ROOT/'lanl-cpu-model-continuation-a3-mocked-proof.json').write_text(json.dumps(proof,indent=2)+'\n');raise SystemExit(0 if result.wasSuccessful() else 1)
