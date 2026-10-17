"""AST-only audit-hook controls; never execute bootstrap or set resource limits."""
import ast
import hashlib
import json
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent;SOURCE=(HERE/'readonly_bootstrap_v4.py').read_bytes();TREE=ast.parse(SOURCE)
node=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='readonly_audit');ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'inert-audit-hook-only','exec'),ns);hook=ns['readonly_audit']
class Controls(unittest.TestCase):
    def test_readonly_opens_and_metadata_are_allowed(self):
        for args in [('/x','r',0),('/x','rb',524288),('/proc/self/maps','r',0)]:hook('open',args)
        for event in ('os.listdir','os.scandir','os.stat','import','compile','exec'):hook(event,())
    def test_write_and_update_opens_refuse(self):
        for mode,flags in [('w',0),('a',0),('x',0),('r+',0),(None,1),(None,2),(None,64),(None,512),(None,1024)]:
            with self.subTest(mode=mode,flags=flags),self.assertRaises(PermissionError):hook('open',('/x',mode,flags))
    def test_all_mutations_children_and_network_refuse(self):
        for event in ('os.system','os.remove','os.unlink','os.rename','os.replace','os.rmdir','os.mkdir','os.chmod','os.chown','os.link','os.symlink','os.truncate','os.utime','os.chdir','os.putenv','os.unsetenv','ctypes.dlopen','resource.setrlimit','subprocess.Popen','os.exec','os.spawn','os.posix_spawn','os.fork','socket.connect','socket.__new__'):
            with self.subTest(event=event),self.assertRaises(PermissionError):hook(event,())
    def test_caps_precede_diagnostic_import_and_stdin_is_exact(self):
        text=SOURCE.decode();self.assertLess(text.index('resource.setrlimit(resource.RLIMIT_AS'),text.index('import hashlib'))
        self.assertLess(text.index('resource.setrlimit(resource.RLIMIT_CPU'),text.index('sys.addaudithook'))
        script=(HERE/'complete_duplicate_census_v3.py').read_bytes();self.assertEqual(len(script),22966);self.assertIn(hashlib.sha256(script).hexdigest(),text)
        self.assertIn('read(22967)',text);self.assertIn("sys.argv = ['-', sys.argv[1]]",text)
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'bootstrap_executed':False,'resource_limits_or_actual_reader_executed':False,'bootstrap_sha256':hashlib.sha256(SOURCE).hexdigest()}))
    raise SystemExit(not result.wasSuccessful())
