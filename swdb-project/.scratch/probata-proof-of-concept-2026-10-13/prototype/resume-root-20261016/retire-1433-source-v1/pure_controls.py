"""2026-10-16 ET. No-child source-retirement controls; no actual /proc/SSH/Git."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
attempts = []


def audit(event, args):
    if event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec') or event.startswith('socket.'):
        attempts.append(event)
        raise AssertionError('child/native/network prohibited in pure controls')


sys.addaudithook(audit)
spec = importlib.util.spec_from_file_location('inert_retirement1433', HERE/'retirement.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def rows():
    argv = ['/usr/bin/python3', '-I', '-B', '-', '--retire-reviewed-1433']
    return [
        {'pid': 100, 'parent': 99, 'start_ticks': '1000', 'comm': 'python3', 'uids': ['7']*4, 'argv': argv},
        {'pid': 99, 'parent': 98, 'start_ticks': '999', 'comm': 'timeout', 'uids': ['7']*4,
         'argv': ['/usr/bin/timeout', '--signal=TERM', '--kill-after=5s', '300s', *argv]},
        {'pid': 98, 'parent': 97, 'start_ticks': '998', 'comm': 'sshd', 'uids': ['7']*4,
         'argv': ['sshd: yanruj@notty', '', '']},
        {'pid': 97, 'parent': 96, 'start_ticks': '997', 'comm': 'sshd', 'uids': ['0']*4,
         'argv': ['sshd: yanruj [priv]', '']},
        {'pid': 96, 'parent': 1, 'start_ticks': '996', 'comm': 'sshd', 'uids': ['0']*4,
         'argv': ['sshd: /usr/sbin/sshd -D [listener] 0 of 10-100 startups']},
        {'pid': 1, 'parent': 0, 'start_ticks': '70', 'comm': 'systemd', 'uids': ['0']*4,
         'argv': ['/usr/lib/systemd/systemd', '--system']},
    ]


class Controls(unittest.TestCase):
    def test_exact_six_row_birth_UID_command_transport(self):
        m.validate_transport_rows(rows(), 7)

    def test_transport_mutations_do_not_create_name_only_exceptions(self):
        mutations = [(0, 'argv', ['python3']), (1, 'argv', ['timeout']),
                     (2, 'uids', ['0']*4), (2, 'argv', ['sshd: other@notty', '', '']),
                     (3, 'uids', ['7']*4), (3, 'argv', ['sshd: yanruj@notty', '', '']),
                     (4, 'comm', 'sh'), (4, 'argv', ['sshd: /tmp/sshd -D [listener] 0']),
                     (5, 'pid', 2), (5, 'argv', ['/tmp/systemd']),
                     (0, 'parent', 96), (0, 'start_ticks', '10'), (2, 'pid', 100)]
        for index, key, value in mutations:
            with self.subTest(index=index, key=key):
                r = rows(); r[index][key] = value
                with self.assertRaises(ValueError):
                    m.validate_transport_rows(r, 7)
        with self.assertRaises(ValueError):
            m.validate_transport_rows(rows()[:5], 7)

    def test_cmdline_environment_cwd_exe_fd_all_match_without_payload_export(self):
        wanted = '/exact/source1433'
        for command, env, links in [(wanted.encode(), b'', []), (b'', b'X='+wanted.encode(), []),
                                    (b'', b'', [wanted+'/file']), (b'', b'', [wanted+' (deleted)'])]:
            self.assertEqual(m.reference_matches(command, env, links, (wanted,)), [wanted])
        self.assertEqual(m.reference_matches(b'unrelated', b'SECRET=value', ['/other'], (wanted,)), [])

    def test_bounded_file_pin_refuses_alias_and_alias_parent(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            p = Path(td); (p/'real').mkdir(); (p/'real/file').write_bytes(b'abc')
            (p/'alias').symlink_to(p/'real/file'); (p/'dirlink').symlink_to(p/'real')
            with self.assertRaises(ValueError):m.file_pin(p/'alias')
            with self.assertRaises(ValueError):m.file_pin(p/'dirlink/file')
            with self.assertRaises(ValueError):m.file_pin(p/'real/file', 2)
            self.assertEqual(m.file_pin(p/'real/file', blob=True)['git_blob'],
                             hashlib.sha1(b'blob 3\0abc').hexdigest())

    def test_source_manifest_checks_complete_Git_bytes_and_two_unfollowed_aliases(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            root = Path(td); (root/'.git').write_text('gitdir: /unexecuted/only\n');
            (root/'source.c').write_bytes(b'abc')
            names = ['source.c', *m.LINKS]
            for name, target in m.LINKS.items():
                path = root/name; path.parent.mkdir(parents=True, exist_ok=True); path.symlink_to(target)
            values = [('100644', 'source.c', b'abc')]+[('120000', n, t.encode()) for n, t in m.LINKS.items()]
            data = b''.join(mode.encode()+b' blob '+hashlib.sha1(b'blob '+str(len(v)).encode()+b'\0'+v).hexdigest().encode()+b'\t'+n.encode()+b'\0' for mode,n,v in values)
            with patch.object(m, 'SOURCE', root), patch.object(m, 'EXPECTED_FILES', 3), \
                 patch.object(m, 'EXPECTED_BYTES', sum(len(v) for _,_,v in values)), \
                 patch.object(m, 'git', lambda *args: data):
                result = m.source_manifest()
                self.assertEqual(result['files'], 3)
                self.assertEqual(len(result['unlink_only_aliases']), 2)
                self.assertFalse(result['external_alias_targets_read_or_followed'])
                (root/'source.c').write_bytes(b'abd')
                with self.assertRaises(ValueError):m.source_manifest()
                (root/'source.c').write_bytes(b'abc'); (root/'untracked').write_bytes(b'x')
                with self.assertRaises(ValueError):m.source_manifest()
                (root/'untracked').unlink(); (root/'empty-extra').mkdir()
                with self.assertRaises(ValueError):m.source_manifest()

    def test_tracked_unknown_modes_or_link_sets_refuse(self):
        for raw in (b'160000 commit '+b'0'*40+b'\tmodule\0',
                    b'100644 blob '+b'0'*40+b'\t../escape\0'):
            with self.assertRaises(ValueError):m.parse_tracked(raw)

    def test_raw_retention_nofollow_hash_and_literal_membership_detect_changes(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            root = Path(td); (root/'metadata.json').write_text('{}')
            (root/'unfollowed').symlink_to('/never/read/or/delete/target')
            first = m.raw_manifest([root]); self.assertEqual(first, m.raw_manifest([root]))
            (root/'metadata.json').write_text('{"changed":true}')
            self.assertNotEqual(first, m.raw_manifest([root]))

    def test_raw_unknown_specials_refuse(self):
        with tempfile.TemporaryDirectory(dir=HERE) as td:
            root = Path(td); os.mkfifo(root/'fifo')
            with self.assertRaises(ValueError):m.raw_manifest([root])

    def test_PAM_literal_and_function_exact_reviewed_V3_identity(self):
        old = HERE.parents[1]/'25-owned-transfer-20261016/cold-g621-encoding-v1/root-admitted-scoped-preflight-v3.py'
        def selected(path):
            source = path.read_text(); lines = source.splitlines(True); found = {}
            for n in ast.parse(source).body:
                if isinstance(n, ast.FunctionDef) and n.name == 'pam_identity':found['fn'] = ''.join(lines[n.lineno-1:n.end_lineno])
                if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'WANTED_PAM':found['wanted'] = ast.literal_eval(n.value)
            return found
        self.assertEqual(selected(HERE/'retirement.py'), selected(old))

    def test_only_exact_recovery_ref_and_nonforced_source_remove_mutations(self):
        tree = ast.parse((HERE/'retirement.py').read_bytes())
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'git']
        mutating = []
        for n in calls:
            if len(n.args)>1 and isinstance(n.args[1], ast.Constant) and (n.args[1].value == 'update-ref' or
                    n.args[1].value == 'worktree' and len(n.args)>2 and isinstance(n.args[2],ast.Constant) and n.args[2].value!='list'):
                mutating.append(ast.unparse(n))
        self.assertEqual(mutating, ["git(PRIMARY, 'worktree', 'remove', str(SOURCE), timeout=60)",
                                    "git(PRIMARY, 'update-ref', RECOVERY, COMMIT, '0' * 40)"])
        source = (HERE/'retirement.py').read_text()
        self.assertNotIn("'--force'", source)
        self.assertNotIn('shutil.rmtree(', source)
        self.assertEqual(len([n for n in ast.walk(tree) if isinstance(n,ast.Call) and
                              isinstance(n.func,ast.Attribute) and n.func.attr in ('unlink','rmdir')]), 0)

    def test_actual_main_requires_explicit_isolated_mode(self):
        with patch.object(sys, 'argv', ['inert-review-only']):
            with self.assertRaisesRegex(ValueError, 'root-admitted explicit'):
                m.main()

    def test_worktree_registration_keeps_every_other_record(self):
        data = b'worktree /primary\0HEAD aaa\0branch refs/heads/yanrujhou_main\0\0worktree /selected\0HEAD bbb\0detached\0\0'
        with patch.object(m, 'git', lambda *args: data):
            self.assertEqual(m.worktree_registration(), {
                '/primary':['HEAD aaa','branch refs/heads/yanrujhou_main'],
                '/selected':['HEAD bbb','detached']})

    def test_unknown_own_UID_permission_denial_refuses(self):
        process = SimpleNamespace(name='123', stat=lambda:SimpleNamespace(st_uid=os.getuid()))
        class Proc:
            name = process.name
            def stat(self):return process.stat()
            def __truediv__(self, child):return Path('/unexecuted/proc/123')/child
        fake = SimpleNamespace(iterdir=lambda:[Proc()])
        with patch.object(m,'Path',lambda name:fake if name=='/proc' else Path(name)), \
             patch.object(m,'proc_bytes',side_effect=PermissionError('pure denied')):
            with self.assertRaisesRegex(ValueError,'123'):
                m.reader_scan(('/exact/source1433',),{'allowed_unreadable_current_transport_pid':9999})

    def test_disappearing_process_requires_complete_rescan_and_three_unresolved_refuse(self):
        class Gone:
            name = '123'
            def stat(self):raise FileNotFoundError('pure vanished')
        rounds = [0]
        def finite():
            rounds[0]+=1
            return [Gone()] if rounds[0]==1 else []
        fake = SimpleNamespace(iterdir=finite)
        with patch.object(m,'Path',lambda name:fake if name=='/proc' else Path(name)):
            r=m.reader_scan(('/exact/source1433',),{})
            self.assertEqual([q['vanished'] for q in r],[1,0])
        fake.iterdir=lambda:[Gone()]
        with patch.object(m,'Path',lambda name:fake if name=='/proc' else Path(name)):
            with self.assertRaisesRegex(ValueError,'unresolved races'):
                m.reader_scan(('/exact/source1433',),{})


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'date':'2026-10-16 ET','tests':result.testsRun,'failures':len(result.failures),
                      'errors':len(result.errors),'child_native_network_attempts':attempts,
                      'actual_retirement_or_proc_or_SSH_or_Git':False},sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() and not attempts else 1)
