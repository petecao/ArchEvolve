"""2026-10-16 ET. No-child compiler observation refusal/budget controls."""
import ast
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
PACKET=HERE/'inert-032e1851-compiler-v1'
attempts=[]
def audit(event,args):
    if event in {'subprocess.Popen','os.system','os.fork','os.posix_spawn','socket.connect','ctypes.dlopen'}:
        attempts.append(event);raise AssertionError('no-child compiler controls: '+event)
sys.addaudithook(audit)
tree=ast.parse((PACKET/'entry.py').read_bytes())
tree.body=[n for n in tree.body if not isinstance(n,ast.If)]
entry={'__name__':'inert_compiler_controls','__file__':str(PACKET/'entry.py')}
exec(compile(tree,str(PACKET/'entry.py'),'exec'),entry)
worker=runpy.run_path(str(HERE/'worker.py'))
expected=json.loads((PACKET/'expected.json').read_bytes())


class Controls(unittest.TestCase):
    def test_changed_external_source_refuses_before_project_import(self):
        with tempfile.TemporaryDirectory(dir=HERE)as folder:
            root=Path(folder);source=root/'source.cc';source.write_text('changed')
            wanted=root/'expected.json';wanted.write_text(json.dumps({'fixture':{'sha256':'0'*64}}))
            args=['worker','--project',str(root/'missing-project'),'--source',str(source),
                  '--output',str(root),'--expected',str(wanted)]
            with mock.patch.object(sys,'argv',args),self.assertRaisesRegex(ValueError,'fixture differs'):
                worker['main']()

    def test_verifier_selector_refuses_before_project_import(self):
        with tempfile.TemporaryDirectory(dir=HERE)as folder:
            root=Path(folder);source=root/'source.cc';source.write_bytes(b'exact')
            wanted=root/'expected.json';wanted.write_text(json.dumps({'fixture':{
                'sha256':hashlib.sha256(b'exact').hexdigest()}}))
            args=['worker','--project',str(root/'missing-project'),'--source',str(source),
                  '--output',str(root),'--expected',str(wanted)]
            for variable in ('SWDB_FRAMA_C','SWDB_CBMC'):
                with self.subTest(variable=variable),mock.patch.object(sys,'argv',args), \
                        mock.patch.dict(os.environ,{'SWDB_FRAMA_C':'none','SWDB_CBMC':'none',variable:'enabled'}), \
                        self.assertRaisesRegex(ValueError,'selectors must remain disabled'):
                    worker['main']()

    def test_metadata_pins_exact_types_and_refuses_overwrite_nonfinite_or_oversize(self):
        with tempfile.TemporaryDirectory(dir=HERE)as folder:
            root=Path(folder);path=root/'metadata.json';value={'boolean':True,'integer':1,'float':1.0}
            pin=worker['save'](path,value)
            self.assertEqual(json.loads(path.read_bytes()),value)
            self.assertEqual(pin['sha256'],hashlib.sha256(path.read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError):worker['save'](path,value)
            with self.assertRaises(ValueError):worker['save'](root/'nan.json',{'x':float('nan')})
            with self.assertRaisesRegex(ValueError,'metadata exceeded'):
                worker['save'](root/'large.json',{'x':'x'*(16*1024**2)})
            self.assertFalse((root/'nan.json').exists());self.assertFalse((root/'large.json').exists())

    def test_root_staged_siblings_keep_post_exit_headroom(self):
        policy=expected['resource_policy']
        with tempfile.TemporaryDirectory(dir=HERE)as folder:
            root=Path(folder);profile=root/'profile';profile.mkdir()
            allowance=policy['root_headroom_bytes']-policy['root_post_exit_reserve_bytes']
            staged=root/'staged';staged.write_bytes(b'x')
            with staged.open('r+b')as stream:stream.truncate(allowance)
            self.assertEqual(entry['root_sibling_census'](profile,policy)['bytes'],allowance)
            (root/'final-metadata').write_bytes(b'x')
            with self.assertRaisesRegex(ValueError,'fixed headroom'):
                entry['root_sibling_census'](profile,policy)

    def test_final_profile_write_preserves_aggregate_root_allowance(self):
        policy=expected['resource_policy'];limit=policy['output_budget_bytes']-policy['root_headroom_bytes']
        with tempfile.TemporaryDirectory(dir=HERE)as folder:
            root=Path(folder);target=root/'final.json'
            with mock.patch.dict(entry,raw_bytes=lambda unused:limit-1):
                with self.assertRaisesRegex(ValueError,'projected aggregate'):
                    entry['bounded_bytes'](target,b'{}',root,policy,reserve=False)
            self.assertFalse(target.exists())

    def test_guard_and_main_have_no_verifier_or_native_user_program_dispatch(self):
        # The public controller dispatch is one exact Python observer worker.
        # Scientific/native semantics are deliberately absent, rather than
        # inferred from an empty report or an outcome label.
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
        calls=[n.func.id for n in ast.walk(main)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)]
        self.assertEqual(calls.count('guarded_compiler'),1)
        self.assertNotIn('guarded_generation',calls)
        self.assertNotIn('layout_checks',calls)
        self.assertEqual(expected['proof_policy']['verifier_calls'],0)
        self.assertEqual(expected['proof_policy']['proof_records'],0)
        self.assertNotIn('canonical_manifest',expected)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','tests':result.testsRun,'failures':len(result.failures),
        'errors':len(result.errors),'child_native_network_attempts':attempts,'actual_compiler_executed':False}))
    raise SystemExit(not result.wasSuccessful()or bool(attempts))
