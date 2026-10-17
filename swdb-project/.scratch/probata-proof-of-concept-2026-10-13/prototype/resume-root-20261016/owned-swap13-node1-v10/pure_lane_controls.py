"""2026-10-16 ET. Pure node0/node1 compatibility of the unchanged13 entry.

Uses the exact frozen Linux admission function with fake physical metadata;
no project import, actual environment/Git/SSH/lane/compiler/native execution.
"""
import ast
import hashlib
import json
from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
POC=HERE.parents[2]
PACKET=POC/'prototype/25-owned-swap-parts-20261016/public13-v1/inert-a102e275-public13-v1'
SOURCE=(PACKET/'entry.py').read_text()
NODE=next(n for n in ast.parse(SOURCE).body if isinstance(n,ast.FunctionDef)and n.name=='linux_admission')
FUNCTION=ast.get_source_segment(SOURCE,NODE)
EXPECTED=json.loads((PACKET/'expected.json').read_bytes())
COMMAND=json.loads((PACKET/'root-command.json').read_bytes())
RAW=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-a102e275-t25-owned-swap13-public-v1')
REPO=Path(EXPECTED['remote_project']).parent
ENTRY_SHA=hashlib.sha256((PACKET/'entry.py').read_bytes()).hexdigest()
EXPECTED_SHA=hashlib.sha256((PACKET/'expected.json').read_bytes()).hexdigest()
ATTEMPTS=[]


def audit(event,args):
    if event in ('subprocess.Popen','os.system','os.exec','os.posix_spawn')or event.startswith('socket.'):
        ATTEMPTS.append(event);raise AssertionError('no child/native/network in lane controls')


sys.addaudithook(audit)


def check(node,mutate=None):
    launch={'node':node,'source':str(REPO),'source_commit':EXPECTED['source_commit'],
            'rss_cap_bytes':8589934592,'workers':1,'timeout_seconds':2800,
            'command':[s.replace('{SOURCE}',str(REPO)).replace('{OUTPUT}',str(RAW))for s in COMMAND],
            'reviewed_wrapper_reuse':EXPECTED['linux_launch_binding']['wrappers'].copy()}
    if mutate:mutate(launch)
    class MetadataPath(type(Path())):
        def resolve(self,strict=False):return self
        def read_bytes(self):
            if str(self)==str(RAW/'launch.json'):return json.dumps(launch).encode()
            raise AssertionError('unlisted physical read')
    def sha(path):
        if path=='<frozen-entry>':return ENTRY_SHA
        return EXPECTED['linux_launch_binding']['wrappers'][Path(path).name]
    ns={'Path':MetadataPath,'os':os,'json':json,'hashlib':hashlib,'sha':sha,
        'pin':lambda path:{'path':str(path),'sha256':hashlib.sha256(json.dumps(launch,sort_keys=True).encode()).hexdigest()},
        '__file__':'<frozen-entry>','EXPECTED_SHA256':EXPECTED_SHA}
    exec(compile(FUNCTION,'<unchanged-linux-admission-only>','exec'),ns)
    with patch.dict(os.environ,{'PROBATA_OUTPUT':str(RAW),'SWDB_VERIFIER_LOCK':str(RAW/'verifier.lock'),
                               'SWDB_VERIFIER_RSS_CAP_BYTES':'8589934592'},clear=True):
        return ns['linux_admission'](EXPECTED,MetadataPath(REPO),MetadataPath(RAW/'owned-swap13-public-v1-profile'))


class Controls(unittest.TestCase):
    def test_unchanged_entry_accepts_exact_guarded_node0_and_node1_roles(self):
        zero,one=check(0),check(1)
        self.assertNotEqual(zero.pop('launch'),one.pop('launch'))
        self.assertEqual(zero,one)

    def test_node1_retains_source_cap_timeout_worker_and_wrapper_refusals(self):
        mutations=[lambda x:x.update(source='/wrong/source'),lambda x:x.update(source_commit='0'*40),
                   lambda x:x.update(rss_cap_bytes=4294967296),lambda x:x.update(workers=2),
                   lambda x:x.update(timeout_seconds=2799),
                   lambda x:x['reviewed_wrapper_reuse'].update({'watch.py':'0'*64}),
                   lambda x:x['command'].__setitem__(-1,'/wrong/raw')]
        for mutate in mutations:
            with self.assertRaises(ValueError):check(1,mutate)

    def test_entry_has_no_node_selector_or_managed_worktree_assumption(self):
        tree=ast.parse(FUNCTION)
        self.assertFalse(any(isinstance(n,ast.Constant)and n.value in ('node','numa_memory_policy','--git-common-dir')for n in ast.walk(tree)))
        self.assertEqual(EXPECTED['resource_policy']['cap_bytes'],8589934592)
        self.assertEqual(EXPECTED['resource_policy']['workers'],1)


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','tests':result.testsRun,'errors':len(result.errors),
                      'failures':len(result.failures),'child_native_network_attempts':ATTEMPTS,'actual_dispatch':False},sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful()and not ATTEMPTS else 1)
