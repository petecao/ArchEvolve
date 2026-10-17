"""2026-10-16 ET. Pure entry admission/result controls; never invoke main."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
PACKET = HERE / 'inert-dcdecf31-node1'
attempts = []

def deny_children(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.fork', 'os.posix_spawn', 'socket.connect', 'ctypes.dlopen'}:
        attempts.append(event)
        raise AssertionError('pure controls rejected '+event)

sys.addaudithook(deny_children)
source = (PACKET / 'entry.py').read_bytes()
tree = ast.parse(source)
tree.body = [node for node in tree.body if not isinstance(node, ast.If)]
entry = {'__file__': str(PACKET/'entry.py'), '__name__': 'closed_pure_controls'}
exec(compile(tree, str(PACKET/'entry.py'), 'exec'), entry)


def fixture():
    model = {'id': 'std-model', 'sha256': '0'*64}
    rows = []
    for index in range(5):
        rows.append({'id': 'record.'+str(index), 'evidence_kind': 'contract_fixture',
            'subject': {'kind': 'library_summary', 'id': 'contract.fixture_vector_closed_no_growth'},
            'job': {'adapter': 'wp'}, 'verdict': 'not_proven', 'failure_class': 'unsupported_construct',
            'settings': {'verifier_launched': False}, 'evidence': {'reports': []}})
    rows[0].update(verdict='proven', goals=[{'source': 'source_rule', 'status': 'valid'} for _ in range(24)],
        pins={'std_models': model}, assumptions=[
            {'reference': model, 'sentence': 'Allocation succeeds: every malloc (std::vector growth, new[]) returns usable memory, never null.'},
            {'reference': model, 'sentence': 'The pinned standard library model is the explicit TCB.'}],
        proof_setup_check={'runs': [{'invocation': 'checked-source-rule-evaluation', 'native_verifier_launched': False}]})
    rows[0]['settings'].update(tool='checked-vector-source-rule',
        proof_basis='checked closed source observation rule and exact conditional mathematical evidence',
        source_typed_bridge_established=False,
        original_diagnostic={'normal_verdict': 'not_proven'},
        native_projected_diagnostic={'normal_verdict': 'not_proven'}, current_model_records_created=[],
        historical_scientific_components=[{'targets': 35}, {'targets': 11}, {'targets': 9}, {'targets': 4}, {'targets': 23}])
    return rows


class Controls(unittest.TestCase):
    def refused_record(self, mutate):
        rows = fixture(); mutate(rows)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            entry['check_records'](rows)

    def aliases(self, root, count=5, current=4):
        base = root / entry['PYTEST_BASE']; base.mkdir(parents=True)
        targets = [base/(entry['CASE_PREFIX']+str(index)) for index in range(count)]
        for target in targets: target.mkdir()
        alias = base/(entry['CASE_PREFIX']+'current')
        alias.symlink_to(base/(entry['CASE_PREFIX']+str(current)))
        return base, targets, alias

    def test_public_case_census_preserves_source_and_native_boundaries(self):
        self.assertEqual(entry['check_records'](fixture())['source_rule_proven'], 1)
        self.refused_record(lambda rows: rows.pop())
        self.refused_record(lambda rows: rows[4].update(id=rows[3]['id']))
        self.refused_record(lambda rows: rows[1].update(verdict='proven'))
        self.refused_record(lambda rows: rows[1].update(failure_class='unknown'))
        self.refused_record(lambda rows: rows[0]['settings'].update(verifier_launched=True))
        self.refused_record(lambda rows: rows[0]['settings'].update(source_typed_bridge_established=True))
        self.refused_record(lambda rows: rows[0]['settings']['native_projected_diagnostic'].update(normal_verdict='proven'))
        self.refused_record(lambda rows: rows[0]['settings']['original_diagnostic'].update(normal_verdict='proven'))

    def test_complete_source_and_historical_math_and_assumptions(self):
        self.refused_record(lambda rows: rows[0]['goals'].pop())
        self.refused_record(lambda rows: rows[0]['goals'][0].update(source='native'))
        self.refused_record(lambda rows: rows[0]['goals'][0].update(status='unknown'))
        self.refused_record(lambda rows: rows[0]['settings']['historical_scientific_components'][0].update(targets=34))
        self.refused_record(lambda rows: rows[0]['assumptions'].pop())
        self.refused_record(lambda rows: rows[0]['assumptions'].pop(0))
        self.refused_record(lambda rows: rows[0]['proof_setup_check']['runs'].clear())
        self.refused_record(lambda rows: rows[0]['evidence']['reports'].append({'name':'wp_log'}))

    def test_exact_five_junit_cases_and_zero_skips(self):
        text = '<testsuites><testsuite tests="5" errors="0" failures="0" skipped="0">'+''.join(
            '<testcase classname="tests.test_vector_reallocation_closed_public_workflow" name="'+
            entry['SELECTION'].split('::')[-1]+'['+name+']"/>' for name in entry['CASE_IDS'])+'</testsuite></testsuites>'
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            path = Path(folder)/'junit.xml'; path.write_text(text)
            self.assertEqual(entry['junit_census'](path)['tests'], 5)
            for bad in (text.replace('skipped="0"','skipped="1"'), text.replace('[safe]','[other]'),
                        text.replace('tests="5"','tests="4"'), text.replace('errors="0"','errors="1"'),
                        text.replace('/></testsuite>','><failure/></testcase></testsuite>')):
                path.write_text(bad)
                with self.assertRaises(ValueError): entry['junit_census'](path)

    def test_all_five_names_have_the_same_actual_thirty_character_prefix(self):
        prefixes = [re.sub(r'[\W]', '_', entry['SELECTION'].split('::')[-1]+'['+name+']')[:30]
                    for name in entry['CASE_IDS']]
        self.assertEqual(prefixes, ['test_public_closed_source_proo']*5)
        self.assertEqual(len(entry['CASE_PREFIX']),30)

    def test_only_five_exact_current_targets_are_allowed_during_execution(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root = Path(folder); base, targets, alias = self.aliases(root)
            for index in range(5):
                alias.unlink(); alias.symlink_to(targets[index])
                self.assertEqual(entry['raw_extent'](root)['aliases'][0]['literal_target'],str(targets[index]))
            for bad in (targets[0].name, str(base/(entry['CASE_PREFIX']+'5')), str(root.parent), str(targets[0])+'/..'):
                alias.unlink(); alias.symlink_to(bad)
                with self.assertRaisesRegex(ValueError,'link literal differs'): entry['raw_extent'](root)

    def test_complete_run_requires_all_five_directories_and_current_four(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder); base,targets,alias=self.aliases(root)
            entry['raw_extent'](root,require_aliases=True)
            alias.unlink()
            with self.assertRaisesRegex(ValueError,'complete exact'): entry['raw_extent'](root,require_aliases=True)
            alias.symlink_to(targets[3])
            with self.assertRaisesRegex(ValueError,'fifth case'): entry['raw_extent'](root,require_aliases=True)
            alias.unlink();alias.symlink_to(targets[4]);targets[0].rmdir()
            with self.assertRaisesRegex(ValueError,'exact five physical'): entry['raw_extent'](root,require_aliases=True)
            targets[0].mkdir();(base/'extra').mkdir()
            with self.assertRaisesRegex(ValueError,'exact five physical'): entry['raw_extent'](root,require_aliases=True)

    def test_alias_targets_cannot_be_symlinks_or_nested_escape(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder);base,targets,alias=self.aliases(root)
            targets[4].rmdir();outside=root/'outside';outside.mkdir();targets[4].symlink_to(outside)
            with self.assertRaises(ValueError): entry['raw_extent'](root)
            targets[4].unlink();targets[4].mkdir();(root/'unlisted-current').symlink_to(targets[4])
            with self.assertRaisesRegex(ValueError,'unlisted raw output symlink'): entry['raw_extent'](root)

    def test_raw_total_per_file_and_final_reserve_are_bounded(self):
        old={key:entry[key] for key in ('TOTAL_BYTES','STAGE_BYTES','FINAL_RESERVE_BYTES')}
        entry.update(TOTAL_BYTES=7,STAGE_BYTES=4,FINAL_RESERVE_BYTES=0)
        try:
            with tempfile.TemporaryDirectory(dir=HERE) as folder:
                root=Path(folder);(root/'a').write_bytes(b'1234')
                self.assertEqual(entry['raw_extent'](root)['bytes'],4)
                (root/'b').write_bytes(b'1234')
                with self.assertRaisesRegex(ValueError,'total budget'): entry['raw_extent'](root)
                (root/'b').unlink();(root/'a').write_bytes(b'12345')
                with self.assertRaisesRegex(ValueError,'per-file budget'): entry['raw_extent'](root)
                (root/'a').write_bytes(b'1234');entry['FINAL_RESERVE_BYTES']=4
                with self.assertRaisesRegex(ValueError,'final metadata reserve'): entry['raw_extent'](root)
        finally:entry.update(old)

    def test_exact_reserved_limit_includes_final_json(self):
        old={key:entry[key] for key in ('TOTAL_BYTES','STAGE_BYTES','FINAL_RESERVE_BYTES','FINAL_RESULT_BYTES')}
        entry.update(TOTAL_BYTES=8192,STAGE_BYTES=8192,FINAL_RESERVE_BYTES=4096,FINAL_RESULT_BYTES=2048)
        try:
            with tempfile.TemporaryDirectory(dir=HERE) as folder:
                root=Path(folder);self.aliases(root)
                used=entry['raw_extent'](root,require_aliases=True)['bytes']
                (root/'payload').write_bytes(b'x'*(4096-used))
                result,code=entry['finalize_result'](root,{'status':'PRODUCER_WORKFLOW_COMPLETE'},0,clock=lambda:1)
                self.assertEqual(code,0)
                observed=entry['raw_extent'](root,require_aliases=True,reserve=0)
                self.assertEqual(observed['bytes'],result['finalization']['projected_total_bytes'])
                self.assertEqual((root/'closed-result.json').stat().st_size,result['finalization']['result_bytes'])
                self.assertLessEqual(observed['bytes'],8192)
            with tempfile.TemporaryDirectory(dir=HERE) as folder:
                root=Path(folder);self.aliases(root)
                used=entry['raw_extent'](root,require_aliases=True)['bytes']
                (root/'payload').write_bytes(b'x'*(4097-used))
                with self.assertRaisesRegex(ValueError,'final metadata reserve'):
                    entry['finalize_result'](root,{'status':'PRODUCER_WORKFLOW_COMPLETE'},0,clock=lambda:1)
                self.assertFalse((root/'closed-result.json').exists())
        finally:entry.update(old)

    def test_pre_and_post_fsync_time_and_final_size_refuse_success(self):
        with self.assertRaisesRegex(ValueError,'projected final metadata'):
            entry['final_payload']({'reason':'x'*entry['FINAL_RESULT_BYTES']},{'bytes':0,'regular_files':0,'aliases':[]},1)
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder);self.aliases(root)
            result,code=entry['finalize_result'](root,{'status':'PRODUCER_WORKFLOW_COMPLETE'},0,clock=lambda:1199.5)
            self.assertEqual((code,result['status']),(1,'REFUSED_OR_FAILED'))
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder);self.aliases(root);ticks=iter([1,1201])
            with self.assertRaisesRegex(ValueError,'deadline exceeded after final fsync'):
                entry['finalize_result'](root,{'status':'PRODUCER_WORKFLOW_COMPLETE'},0,clock=lambda:next(ticks))

    def test_finalization_requires_exclusive_result_namespace(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder);self.aliases(root);(root/'closed-result.json').write_bytes(b'prior')
            with self.assertRaises(FileExistsError):
                entry['finalize_result'](root,{'status':'PRODUCER_WORKFLOW_COMPLETE'},0,clock=lambda:1)
            self.assertEqual((root/'closed-result.json').read_bytes(),b'prior')

    def test_policy_gate_requires_source_exact_budgets_and_reserve(self):
        policy=json.loads((PACKET/'policy.json').read_bytes());entry['policy_gate'](policy)
        for key,bad in (('source_commit','0'*40),('profile_seconds',999),('selection','other'),('raw_name','other')):
            changed=copy.deepcopy(policy);changed[key]=bad
            with self.assertRaises(ValueError):entry['policy_gate'](changed)
        for key,bad in (('whole_tree_seconds',1500),('workers',2),('raw_budget_bytes',1<<30)):
            changed=copy.deepcopy(policy);changed['guard'][key]=bad
            with self.assertRaises(ValueError):entry['policy_gate'](changed)
        changed=copy.deepcopy(policy);changed['finalization']['reserve_bytes']=0
        with self.assertRaises(ValueError):entry['policy_gate'](changed)

    def test_full_physical_controller_packet_and_command_are_bound(self):
        policy=json.loads((PACKET/'policy.json').read_bytes());command=json.loads((PACKET/'command.json').read_bytes())
        self.assertEqual(command['source_commit'],'dcdecf317a0e9b34f3ce12d5b914eb823c439fbc')
        self.assertLessEqual(sum(row['bytes'] for row in command['controller_inputs']),1048576)
        self.assertEqual(len(command['controller_inputs']),len({row['name'] for row in command['controller_inputs']}))
        for row in command['controller_inputs']:
            data=Path(row['path']).read_bytes();self.assertEqual((len(data),hashlib.sha256(data).hexdigest()),(row['bytes'],row['sha256']))
        raw=command['raw_root']
        self.assertEqual(command['argv'],[policy['tools']['opam']['path'],'exec','--switch=framac-33','--',
            policy['linux_launch_binding']['python'],'-I','-B',raw+'/control/entry.py',command['source'],raw,
            raw+'/control/policy.json',hashlib.sha256((PACKET/'policy.json').read_bytes()).hexdigest()])
        self.assertEqual(command['root_guard'],policy['guard'])
        self.assertEqual(policy['linux_launch_binding']['entry_sha256'],hashlib.sha256(source).hexdigest())
        self.assertEqual(command['finalization'],policy['finalization'])
        self.assertEqual(command['pytest_alias_policy'],policy['pytest_alias_policy'])

    def test_v1_inverse_and_reference_finalization_are_exact(self):
        report=json.loads((HERE/'template-delta-v2.json').read_bytes())
        lines=(HERE/'entry_template.py').read_text().splitlines(keepends=True)
        for edit in reversed(report['line_edits']):
            a,b=edit['new_range'];self.assertEqual(lines[a:b],edit['new_lines']);lines[a:b]=edit['old_lines']
        restored=''.join(lines).encode()
        self.assertEqual(restored,Path(report['parent']['path']).read_bytes())
        self.assertEqual(hashlib.sha256(restored).hexdigest(),report['parent']['sha256'])
        self.assertIn('check_records',report['unchanged_functions']);self.assertIn('junit_census',report['unchanged_functions'])
        def func(text,name):
            node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
            return ast.dump(node,include_attributes=False)
        reference=Path(report['reference_finalization']['path']).read_text()
        self.assertEqual(hashlib.sha256(reference.encode()).hexdigest(),report['reference_finalization']['sha256'])
        self.assertEqual(func(source,'final_payload'),func(reference,'final_payload'))
        self.assertEqual(func(source,'finalize_result'),func(reference.replace('mixed-result.json','closed-result.json'),'finalize_result'))

    def test_pinned_pytest_source_and_helper_lineage_are_retained(self):
        observation=json.loads((HERE/'pytest-tmpdir-source-observation.json').read_bytes())
        policy=json.loads((PACKET/'policy.json').read_bytes())
        self.assertEqual(policy['pytest_alias_policy']['source'],{key:observation[key] for key in ('path','sha256','bytes')})
        self.assertEqual(observation['sha256'],'5099f71d89413191c9e7515c9d4fe9fc7083bb73306f2cf1f73a9f89c862ed90')
        delta=json.loads((HERE/'template-delta-v2.json').read_bytes())
        predecessor=Path(delta['parent']['path']).parent
        for name in ('reviewed_wp_gates.py','reviewed_native_gates.py','reviewed-function-lineage.json'):
            self.assertEqual((HERE/name).read_bytes(),(predecessor/name).read_bytes())
        for path in (HERE/'entry_template.py',HERE/'prepare.py',PACKET/'entry.py'):
            compile(path.read_bytes(),str(path),'exec')
        self.assertEqual(attempts,[])


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','pure_controls':result.testsRun,'failures':len(result.failures),
        'errors':len(result.errors),'child_native_network_attempts':attempts,'actual_profile_executed':False},sort_keys=True))
    raise SystemExit(not result.wasSuccessful())
