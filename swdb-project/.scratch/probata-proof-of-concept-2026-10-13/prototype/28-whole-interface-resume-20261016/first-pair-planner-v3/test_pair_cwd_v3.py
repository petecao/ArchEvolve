"""No-child controls for the exact original-runtime working directory seam."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import runpy
import sys
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
OLD = WHOLE / 'production-route-v4/profile/pair_plan_v2.py'
SOURCE = HERE / 'pair_plan_v3.py'
EVENTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        EVENTS.append(event)
        raise RuntimeError('no child/native/network in planner controls')


sys.addaudithook(audit)
NEW = runpy.run_path(str(SOURCE), run_name='prospective_pair_plan_cwd_v3')
PREVIOUS = runpy.run_path(str(OLD), run_name='frozen_pair_plan_v2')


def selection():
    root = '/data/yanruj/EvolveSWDB_runs/explicit-public-profile-standin'
    return {'python': '/data1/yanruj/venvs/swdb-test/bin/python',
        'original_project': '/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project',
        'producer_project': '/data1/yanruj/explicit-new-producer-standin/swdb-project',
        'library_root': root + '/library', 'records': root + '/records', 'runs': root + '/runs',
        'verifier_lock': root + '/verifier.lock', 'pycache': root + '/pycache',
        'compiler_wrapper': '/data/yanruj/EvolveSWDB_runs/probata-source-gate-native-20261015-1102-node0/compiler-bin/clang++',
        'cbmc': '/data1/yanruj/explicit-cbmc-standin',
        'root_admission_receipt': {'path': root + '/explicit-admission-standin.json', 'bytes': 1, 'sha256': 'a' * 64}}


def profile():
    return {'contracts': [{'id': 'explicit-positive-standin', 'sha256': 'b' * 64, 'expected_result': 80},
        {'id': 'explicit-negative-standin', 'sha256': 'c' * 64, 'expected_result': 79}],
        'semantics_content_sha256': 'd' * 64, 'method_content_sha256': 'e' * 64, 'producer_manifest_sha256': 'f' * 64}


class PlannerControls(unittest.TestCase):
    def test_exact_one_edit_inverse_and_other_functions(self):
        old = "'argv': argv, 'cwd': selection['producer_project'],"
        new = "'argv': argv, 'cwd': str(Path(selection['original_project']).parent),"
        text = SOURCE.read_text()
        self.assertEqual(text.count(new), 1)
        self.assertEqual(text.replace(new, old, 1), OLD.read_text())
        for name in ('canonical', 'need'):
            def node(path):
                return ast.dump(next(n for n in ast.parse(path.read_bytes()).body if isinstance(n, ast.FunctionDef) and n.name == name))
            self.assertEqual(node(OLD), node(SOURCE))

    def test_only_job_cwd_changes_from_frozen_planner(self):
        selected = selection(); request = profile()
        before = PREVIOUS['plan'](request, selected); after = NEW['plan'](request, selected)
        self.assertEqual([job['cwd'] for job in before['jobs']], [selected['producer_project']] * 2)
        inverse = copy.deepcopy(after)
        for job in inverse['jobs']:
            job['cwd'] = selected['producer_project']
        self.assertEqual(inverse, before)
        self.assertEqual(after['environment']['PYTHONPATH'], selected['producer_project'])
        self.assertEqual(after['environment']['SWDB_HOME'], selected['original_project'])
        self.assertEqual(after['environment']['SWDB_CLANG'], selected['compiler_wrapper'])
        self.assertFalse(after['execution_authorized_by_this_plan'])

    def test_exact_selected_descriptor_frontend_cwd_and_unchanged_alias_source(self):
        descriptor_path = WHOLE / 'compiler-descriptor-v1/expected-absolute-compiler-descriptor-v1.json'
        self.assertEqual(hashlib.sha256(descriptor_path.read_bytes()).hexdigest(),
            '7ef1f44848dd60dae9a9732ce49752209197e80e1afcd3720649d173e386aba3')
        expected = json.loads(descriptor_path.read_bytes())
        actual = NEW['plan'](profile(), selection())
        for job in actual['jobs']:
            cwd = job['cwd']
            self.assertEqual(cwd, '/data1/yanruj/probata-resume-20261016-2baf722f')
            self.assertIn('-fdebug-compilation-dir=' + cwd, expected['runtime_identity']['frontend'])
            self.assertIn('-fcoverage-compilation-dir=' + cwd, expected['runtime_identity']['frontend'])
        retained = json.loads((WHOLE / 'compiler-descriptor-v1/passive-read-stdout-v1.json').read_bytes())
        self.assertEqual(retained['document']['runtime']['command'], ['clang++'])
        self.assertEqual(EVENTS, [])

    def test_all_original_selection_and_pair_refusals_remain(self):
        for mutate in (lambda s: s.update(unknown='unadmitted'), lambda s: s.update(original_project='relative'),
                       lambda s: s.update(records=s['original_project'] + '/records'),
                       lambda s: s.update(root_admission_receipt={})):
            selected = selection(); mutate(selected)
            for module in (PREVIOUS, NEW):
                with self.assertRaises(ValueError): module['plan'](profile(), selected)
        for result in (78, 81):
            request = profile(); request['contracts'][0]['expected_result'] = result
            with self.assertRaises(ValueError): NEW['plan'](request, selection())


if __name__ == '__main__':
    unittest.main(verbosity=2)
