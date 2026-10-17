"""2026-10-16 ET. Child-free V10 sparse-source protocol and inverse controls."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import os,stat,shutil,subprocess

HERE=Path(__file__).resolve().parent
ATTEMPTS=[]


def audit(event,args):
    if event in ('subprocess.Popen','os.system','os.exec','os.posix_spawn') or event.startswith('socket.'):
        ATTEMPTS.append(event);raise AssertionError('no child/native/network in pure controls')


sys.addaudithook(audit)
import signal
signal.alarm(30)
PACKET=HERE/'inert-abb598a4-public3-v1'
SPEC=json.loads((PACKET/'source-projection-spec.json').read_bytes())
ROWS=json.loads((PACKET/'selected-Git-metadata.json').read_bytes())
ns={'P':Path,'os':os,'stat':stat,'shutil':shutil,'subprocess':subprocess,'json':json,'hashlib':hashlib}
exec(compile((HERE/'sparse_source.py').read_bytes(),'<inert-sparse-helper-definitions>','exec'),ns)


class Controls(unittest.TestCase):
    def test_source_spec_exact426regular_leaves_338package_and_derived_budget(self):
        self.assertEqual(len(ROWS),426)
        self.assertEqual(sum(r['bytes']for r in ROWS),6223086)
        self.assertEqual(sum(r['path'].startswith('swdb-project/swdb/')for r in ROWS),338)
        self.assertEqual({r['mode']for r in ROWS},{'100644'})
        self.assertEqual(hashlib.sha256(json.dumps(ROWS,sort_keys=True,separators=(',',':')).encode()).hexdigest(),SPEC['inventory_sha256'])
        self.assertEqual(SPEC['bytes']+SPEC['metadata_headroom_bytes'],1079964910)

    def test_Git_inventory_refuses_symlinks_submodules_escape_duplicate_and_control_names(self):
        for mode,kind,path in [('120000','blob','swdb-project/swdb/link'),('160000','commit','swdb-project/swdb/sub'),
                               ('100644','blob','swdb-project/../escape'),('100644','blob','swdb-project/swdb/a\nextra')]:
            raw=f'{mode} {kind} '.encode()+b'0'*40+b' 1\t'+path.encode()+b'\0'
            with self.assertRaises(AssertionError):ns['sparse_inventory'](raw)
        raw=b'100644 blob '+b'0'*40+b' 1\tswdb-project/swdb/a\0'
        with self.assertRaises(AssertionError):ns['sparse_inventory'](raw+raw)

    def test_primary_and_parent_alias_configs_cannot_be_pinned(self):
        with tempfile.TemporaryDirectory(dir=HERE)as td:
            p=Path(td);(p/'real').mkdir();(p/'real/config').write_text('[core]\n')
            (p/'alias').symlink_to(p/'real/config');(p/'parent').symlink_to(p/'real')
            with self.assertRaises(AssertionError):ns['sparse_pin'](p/'alias')
            with self.assertRaises(AssertionError):ns['sparse_pin'](p/'parent/config')
            self.assertEqual(ns['sparse_pin'](p/'real/config')['bytes'],7)

    def test_existing_destination_refuses_before_any_Git_or_write(self):
        calls=[];old=ns['sparse_git'];ns['sparse_git']=lambda *a,**k:calls.append(a)
        try:
            with patch.object(os.path,'lexists',return_value=True):
                with self.assertRaisesRegex(AssertionError,'fresh isolated clone'):
                    ns['sparse_materialize'](Path('/unexecuted/primary'),Path('/data1/yanruj/probata-resume-20261016-abb598a4'),SPEC['source_commit'],SPEC)
            self.assertEqual(calls,[])
        finally:ns['sparse_git']=old

    def test_derived_source_budget_plus_unchanged10GiB_floor_refuses_before_clone(self):
        calls=[];old=ns['sparse_git']
        def fake(root,*a,**k):
            calls.append(a)
            if a[0]=='ls-tree':
                return b''.join(f"{r['mode']} blob {r['oid']} {r['bytes']}\t{r['path']}".encode()+b'\0'for r in ROWS)
            if a[0]=='rev-parse':return SPEC['consumer_oids'][a[1].split(':swdb-project/',1)[1]].encode()+b'\n'
            raise AssertionError('no clone/config/checkout may start below reserve')
        ns['sparse_git']=fake
        try:
            with patch.object(os.path,'lexists',return_value=False),patch.object(shutil,'disk_usage',return_value=types.SimpleNamespace(free=10*1024**3+1079964910-1)):
                with self.assertRaises(AssertionError):
                    ns['sparse_materialize'](Path('/unexecuted/primary'),Path('/data1/yanruj/probata-resume-20261016-abb598a4'),SPEC['source_commit'],SPEC)
            self.assertFalse(any(a[0]in('clone','config','checkout')for a in calls))
        finally:ns['sparse_git']=old

    def test_exact_V10_inverse_and_nested_remote_syntax(self):
        current=(PACKET/'root-launcher-candidate.py').read_text()
        remote=next(n.value.right.value for n in ast.parse(current).body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='script')
        compile('cfg={}\n'+remote,'<inert-nested-remote>','exec')
        for row in reversed(json.loads((PACKET/'launcher-delta-v1.json').read_bytes())['changes']):
            self.assertEqual(current.count(row['after']),1);current=current.replace(row['after'],row['before'],1)
        self.assertEqual(current,(HERE.parents[1]/'resume-root-20261016/launch_reviewed_main_v10.py').read_text())

    def test_sparse_mutations_are_only_new_clone_and_its_private_config(self):
        source=(HERE/'sparse_source.py').read_text();tree=ast.parse(source)
        calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='sparse_git']
        config=[n for n in calls if len(n.args)>1 and isinstance(n.args[1],ast.Constant)and n.args[1].value=='config']
        self.assertEqual(len(config),3)
        self.assertTrue(all(ast.unparse(n.args[0])=='source' for n in config))
        self.assertFalse(any(len(n.args)>1 and isinstance(n.args[1],ast.Constant)and n.args[1].value in ('worktree','sparse-checkout','update-ref')for n in calls if ast.unparse(n.args[0])=='source'))
        self.assertNotIn('.unlink(',source);self.assertNotIn('rmtree(',source)
        self.assertIn("'clone','--shared','--no-checkout','--no-hardlinks','--no-tags'",source)
        self.assertIn("'checkout','--detach',sha",source)
        self.assertIn("sparse_primary_snapshot(repo)==before",source)
        self.assertIn("found==expected",source)

    def test_public13_consumer_and_Linux_admission_have_no_common_dir_assumption(self):
        old=PACKET/'entry.py'
        source=old.read_text();selected={n.name:ast.get_source_segment(source,n)for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name in ('linux_admission','consumer_closure')}
        self.assertEqual(len(selected),2)
        self.assertFalse(any('--git-common-dir'in s or '/worktrees/'in s for s in selected.values()))
        self.assertIn("'hash-object','--no-filters','--stdin-paths'",selected['consumer_closure'])


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','passed':result.testsRun-len(result.failures)-len(result.errors),
                      'failures':len(result.failures),'errors':len(result.errors),'child_native_network_attempts':ATTEMPTS,
                      'actual_clone_launcher_or_SSH':False},sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful()and not ATTEMPTS else 1)
