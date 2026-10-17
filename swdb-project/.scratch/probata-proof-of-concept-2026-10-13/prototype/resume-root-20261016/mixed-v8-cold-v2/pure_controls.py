"""2026-10-16 ET. Child-free reader controls; no remote or proof execution."""
import ast
import copy
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent
ATTEMPTS = []


def audit(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.exec', 'os.fork', 'os.posix_spawn', 'ctypes.dlopen'} or event.startswith('socket.'):
        ATTEMPTS.append(event)
        raise RuntimeError('no external execution in pure controls')


sys.addaudithook(audit)
module = types.ModuleType('inert_mixed_cold_controls')
exec(compile((HERE / 'entry.py').read_text(), '<inert-reader-definitions-only>', 'exec'), module.__dict__)


class Controls(unittest.TestCase):
    def setUp(self):
        self.read, self.pin, self.bytes = module.read, module.pin, module.read_bytes

    def tearDown(self):
        module.read, module.pin, module.read_bytes = self.read, self.pin, self.bytes

    def records(self):
        result = [{'job': {'adapter': 'wp'}, 'subject': {'kind': 'c_model', 'id': name}}
                  for name in module.CONTEXT['model_names']]
        result += [{'job': {'adapter': adapter}, 'subject': {'kind': 'library_summary', 'id': name}}
                   for adapter in ('wp', 'cbmc') for name in
                   ('contract.fixture_pair_pointer_values', 'contract.fixture_pair_pointer_wrong_identity')]
        return result

    def test_all_eight_roles_order_and_duplicate_refusal(self):
        records = self.records()
        self.assertEqual(module.record_order(list(reversed(records))), records)
        with self.assertRaises(ValueError):
            module.record_order([*records[:7], records[0]])
        records[-1]['subject']['id'] = 'unreviewed.subject'
        with self.assertRaises(ValueError):
            module.record_order(records)

    def cbmc(self, *, wrong=False, extra_failure=None):
        labels = ['swdb_reach.end']
        if wrong:
            labels += ['contract.fixture_pair_pointer_wrong_identity#post.ensures1']
        if extra_failure:
            labels += [extra_failure]
        goals = [{'goal': 'g%d' % index, 'property': name, 'status': 'failure'}
                 for index, name in enumerate(labels)]
        results = [{'property': goal['goal'], 'status': 'FAILURE'} for goal in goals]
        record = {'id': 'record', 'subject': {'id': 'contract.fixture_pair_pointer_wrong_identity' if wrong else
                  'contract.fixture_pair_pointer_values'}, 'goals': goals,
                  'settings': {'agreement': {'verdict': 'agree', 'runs': 49, 'sampled': False,
                      'c_output_sha256': 'x', 'cxx_output_sha256': 'x'}, 'forms': {}}}
        module.read = lambda path: [{'result': results}]
        module.pin = lambda path: {'sha256': 'x', 'path': str(path), 'bytes': 1}
        return record, results

    def test_cbmc_safe_reach_failure_is_expected_but_extra_failure_refuses(self):
        record, results = self.cbmc()
        observed = module.cbmc_context(Path('/unused/nonexistent'), record)
        self.assertEqual(observed['failed_property_labels'], ['swdb_reach.end'])
        record, results = self.cbmc(extra_failure='unmodeled_assertion')
        with self.assertRaises(ValueError):
            module.cbmc_context(Path('/unused/nonexistent'), record)

    def test_cbmc_missing_actual_property_refuses(self):
        record, results = self.cbmc()
        results.append({'property': 'hidden', 'status': 'SUCCESS'})
        with self.assertRaises(ValueError):
            module.cbmc_context(Path('/unused'), record)

    def test_cbmc_failed_unwind_cannot_hide_as_reachability(self):
        record, results = self.cbmc()
        results[0]['description'] = 'unwinding assertion'
        with self.assertRaises(ValueError):
            module.cbmc_context(Path('/unused'), record)

    def test_native_draw_count_or_sampling_change_refuses(self):
        for key, value in [('runs', 48), ('sampled', True), ('verdict', 'different')]:
            record, results = self.cbmc()
            record['settings']['agreement'][key] = value
            with self.assertRaises(ValueError):
                module.cbmc_context(Path('/unused'), record)

    def test_unknown_special_or_new_raw_member_refuses(self):
        old_raw, old_profile, old_context = module.RAW, module.PROFILE, module.CONTEXT
        try:
            with tempfile.TemporaryDirectory() as folder:
                module.RAW = Path(folder).resolve()
                module.PROFILE = module.RAW / 'mixed-pair-profile'
                module.CONTEXT = {'aliases': {}, 'raw_membership': []}
                self.assertEqual(module.raw_membership(), [])
                (module.RAW / 'unexpected').write_bytes(b'x')
                with self.assertRaises(ValueError):
                    module.raw_membership()
                (module.RAW / 'unexpected').unlink()
                (module.RAW / 'alias').symlink_to('/unreviewed')
                with self.assertRaises(ValueError):
                    module.raw_membership()
        finally:
            module.RAW, module.PROFILE, module.CONTEXT = old_raw, old_profile, old_context

    def test_semantic_unavailability_is_never_accepted(self):
        text = (HERE / 'entry.py').read_text()
        tree = ast.parse(text)
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        segment = ast.get_source_segment(text, main)
        self.assertIn("'scientific_cold_acceptance': False", segment)
        self.assertIn("'full_original_solver_task_files_retained': 0", segment)
        self.assertIn('return 2', segment)
        self.assertNotIn('subprocess.', segment)

    def test_reader_has_no_project_imports_or_actual_tool_probes(self):
        tree = ast.parse((HERE / 'entry.py').read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertFalse((node.module or '').startswith('swdb'))
            if isinstance(node, ast.Import):
                self.assertFalse(any(alias.name.startswith('swdb') for alias in node.names))
        self.assertEqual(ATTEMPTS, [])

    def wp_fixture(self,index):
        actual=HERE.parents[2]/'evidence/t25-mixed-v8-report-diagnostic-v1-actual-stdout-20261016.json'
        c=json.loads(actual.read_bytes())['contexts'][index]
        native=copy.deepcopy(c['native_goals']);standard=copy.deepcopy(c['standard_goals'])
        properties=copy.deepcopy(c['properties']);normal=copy.deepcopy(c['record_goals'])
        extras=set(c['native_only_goal_ids'])
        # These are synthetic observations, not newly captured actual results.
        # Native results/source conventions follow the pinned evaluated reader.
        for row in native:
            if row['goal'] in extras:row['results']=['valid']
        for row in properties:row['call_context']=None
        for row in normal:row['source']='wp_inventory' if row['goal'] in extras else 'wp_json'
        caller='swdb_pair_pointer_values' if index==4 else 'swdb_pair_pointer_wrong_identity'
        lines=['/* synthetic source-callsite control, never compiled */',f'int {caller}(void) {{']+['']*55
        for name,line in zip(module.CONTEXT['model_names'],(45,49,53,56)):lines[line-1]=name+'();'
        lines[-1]='}'
        record={'subject':c['subject'],'id':c['record'],'goals':normal}
        return native,standard,properties,record,'\n'.join(lines)+'\n'

    def test_complete_actual_shaped_six_context_union_and_closed_dual_owner_metadata(self):
        for index in range(6):
            result=module.reconcile_wp_reports(*self.wp_fixture(index))
            self.assertFalse(result['scientific_or_full_task_closure_accepted'])
            self.assertEqual(len(result['inventory_only_CFG_goals']),2 if index<4 else 0)
            self.assertEqual(len(result['exact_source_bound_dual_owner_smokes']),4 if index>=4 else 0)

    def test_missing_duplicate_or_new_native_standard_record_goal_refuses(self):
        for role in (0,1,3):
            values=list(self.wp_fixture(0));table=values[role]['goals'] if role==3 else values[role]
            table.append(copy.deepcopy(table[0]))
            with self.assertRaises(ValueError):module.reconcile_wp_reports(*values)
        for where in (0,1,3):
            values=list(self.wp_fixture(0));table=values[where]['goals'] if where==3 else values[where]
            table.pop()
            with self.assertRaises(ValueError):module.reconcile_wp_reports(*values)
        values=list(self.wp_fixture(0));values[1].append({'goal':'unlisted_standard'})
        with self.assertRaises(ValueError):module.reconcile_wp_reports(*values)

    def test_inventory_only_CFG_status_property_and_provenance_are_not_waived(self):
        mutations=[('native','passed',False),('native','smoke',True),('native','line',12),
                   ('native','function','other'),('native','results',[]),
                   ('normal','status','unknown'),('normal','source','wp_json'),
                   ('normal','solver','invented'),('normal','seconds',0),
                   ('property','dependencies',['hidden']),('property','extern',True),
                   ('property','origin','hidden'),('property','function','other')]
        for role,key,value in mutations:
            values=list(self.wp_fixture(0));gid=next(g['goal']for g in values[0]if g['goal'].endswith('_terminates'))
            table=values[0]if role=='native' else values[3]['goals']if role=='normal'else values[2]
            row=next(g for g in table if g.get('goal')==gid or g.get('property')==gid.removeprefix('typed_real_'))
            row[key]=value
            with self.subTest(role=role,key=key):
                with self.assertRaises(ValueError):module.reconcile_wp_reports(*values)

    def test_only_four_exact_caller_callee_smokes_may_differ(self):
        for role,key,value in [('native','function','other'),('standard','function','other'),
                               ('native','line',44),('native','smoke',False),('native','passed',False),
                               ('normal','function','other'),('normal','status','unknown'),
                               ('property','dependencies',['hidden'])]:
            values=list(self.wp_fixture(4));gid='typed_real_std_pair_int_int_ptr_ctor_default_wp_smoke_dead_call_s18'
            table=values[0]if role=='native' else values[1]if role=='standard'else values[3]['goals']if role=='normal'else values[2]
            row=next(g for g in table if g.get('goal')==gid or g.get('property')==gid.removeprefix('typed_real_'));row[key]=value
            with self.subTest(role=role,key=key):
                with self.assertRaises(ValueError):module.reconcile_wp_reports(*values)
        values=list(self.wp_fixture(4));next(g for g in values[0]if not g['smoke'])['function']='other'
        with self.assertRaises(ValueError):module.reconcile_wp_reports(*values)
        values=list(self.wp_fixture(4));gid='typed_real_std_pair_int_int_ptr_ctor_default_wp_smoke_dead_call_s18'
        for table in (values[0],values[1],values[3]['goals']):table[:]=[g for g in table if g['goal']!=gid]
        with self.assertRaises(ValueError):module.reconcile_wp_reports(*values)

    def test_query_call_scope_line_duplicates_and_comment_string_substitutes_refuse(self):
        original=self.wp_fixture(4)[-1];name=module.CONTEXT['model_names'][0]
        for query in ('\n'+original,original.replace(name+'();','/* '+name+'(); */'),
                      original.replace(name+'();','"'+name+'();";'),
                      original.replace(name+'();',name+'(); '+name+'();'),
                      original.replace('swdb_pair_pointer_values','other_caller')):
            with self.assertRaises(ValueError):module.query_callsites(query,'swdb_pair_pointer_values')

    def test_exact_V1_observer_and_entry_inverse_and_unchanged_context(self):
        prior=HERE.parent/'mixed-v8-cold-v1'
        helper=(HERE/'report_reconciliation.py').read_text()
        before="""    need(len({g['goal'] for g in native}) == len(native) and
         {g['goal'] for g in native} == {g['goal'] for g in standard}, 'complete native/standard WP goal identity')
    peers = {g['goal']: g for g in standard}
    for goal in native:
        need(all(goal.get(k) == peers[goal['goal']].get(k) for k in
                 ('goal', 'property', 'function', 'line', 'smoke', 'passed')), 'native/standard property owner')
    props = inventory['properties']
"""
        after="""    props = inventory['properties']
    raw_input = directory / 'wp_input.c'
    reconciliation = reconcile_wp_reports(native, standard, props, record, read_bytes(raw_input).decode())
"""
        for name in ('observer.py','entry.py'):
            source=(HERE/name).read_text();source=source.replace(helper+'\n\n','',1).replace(after,before,1)
            source=source.replace("\n            'closed_report_reconciliation': reconciliation,",'',1)
            source=source.replace('cold capture V2.','cold capture.',1).replace("'schema': 'mixed-v8-available-cold-evidence-2'","'schema': 'mixed-v8-available-cold-evidence-1'",1)
            self.assertEqual(source,(prior/name).read_text())
        self.assertEqual((HERE/'context.json').read_bytes(),(prior/'context.json').read_bytes())


if __name__ == '__main__':
    unittest.main(verbosity=2)
