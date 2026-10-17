"""Planning and conjunctive block retrieval, independent of performance claims."""
from copy import deepcopy
import unittest
from unittest.mock import patch
import yaml

from archevolve.__main__ import ROOT, prepare_run, reference_context
from archevolve.evidence_select import capability_requests, select_evidence_candidates
from archevolve.hardware_planning import plan_hardware, query_block
from archevolve.normalize import load_normalized
from archevolve.workload_context import bind_context, request_groups
from tools.render_mermaid import RequestError, load_request


class HardwarePlanningTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / 'examples/received/bfs-sparse.features.v1.2.yaml'
        self.case = load_normalized(self.path, reference_context(ROOT))
        context, digest = load_request(ROOT / 'examples/bfs.source-observations.yaml')
        self.case = bind_context(self.case, context, digest, 'examples/bfs.source-observations.yaml')
        self.requests, _ = capability_requests(self.case)
        self.source_groups = request_groups(self.case, self.requests)
        self.plan = plan_hardware(self.case, self.requests, self.source_groups)
        self.catalog, self.digest = load_request(ROOT / 'catalog/hardware-v0.1.yaml')

    def indexed(self, plan=None):
        return next(b for b in (plan or self.plan)['blocks'] if b['family'] == 'indexed-read')

    def test_bfs_groups_three_reads_before_catalog_lookup(self):
        with patch('archevolve.hardware_catalog.query_catalog', side_effect=AssertionError('Planner must not query')):
            before = deepcopy((self.case, self.requests, self.source_groups))
            plan = plan_hardware(self.case, self.requests, self.source_groups)
        self.assertEqual((self.case, self.requests, self.source_groups), before)
        self.assertEqual(plan['counts'], {'access_requests':5, 'planned_blocks':3, 'unique_typed_clauses':4})
        indexed = self.indexed(plan)
        self.assertEqual(indexed['member_request_ids'], ['access-02-read', 'access-03-read', 'access-04-read'])
        self.assertEqual(indexed['required_capabilities']['address_patterns'], ['indirect', 'ranged_indirect'])
        self.assertFalse(plan['catalog_used_for_grouping'])

    def test_original_per_access_types_mutability_and_source_context_survive(self):
        indexed = self.indexed()
        parent = next(m for m in indexed['members'] if m['request_id'] == 'access-04-read')
        self.assertTrue(parent['mutable_target'])
        self.assertEqual(parent['statement_ids'], ['bfs-td-parent-read'])
        self.assertEqual(parent['source_locations'][0]['start_line'], 243)
        self.assertEqual(indexed['required_capabilities']['mutable_read_request_ids'], ['access-04-read'])
        self.assertIsNone(indexed['resource_requirements']['simultaneous_streams'])
        self.assertEqual(indexed['hardware_composition_status'], 'not_established')
        self.assertEqual(self.plan['source_context_groups'], self.source_groups)
        dep = next(d for d in self.plan['source_dependencies'] if d['to_statement'] == 'bfs-td-parent-cas' and d['from_statement'] == 'bfs-td-parent-read')
        self.assertNotEqual(dep['from_block_ids'], dep['to_block_ids'])
        store = next(d for d in self.plan['source_dependencies'] if d['to_statement'] == 'bfs-td-parent-store')
        self.assertEqual(store['to_block_ids'], [])  # CPU context effect is not dropped or invented as a request.

    def test_grouping_is_deterministic_under_member_permutation(self):
        self.assertEqual(self.plan, plan_hardware(self.case, list(reversed(self.requests)), self.source_groups))

    def test_near_unit_profile_does_not_reclassify_indirection(self):
        case = load_normalized(ROOT / 'examples/received/bfs-fully-connected.features.v1.2.yaml', reference_context(ROOT))
        requests, _ = capability_requests(case)
        plan = plan_hardware(case, requests, request_groups(case, requests))
        self.assertEqual(self.indexed()['member_request_ids'], self.indexed(plan)['member_request_ids'])
        self.assertEqual(self.indexed()['required_capabilities'], self.indexed(plan)['required_capabilities'])

    def test_different_types_widths_and_unknown_evidence_split(self):
        for field, value in [('payload_type','int64'), ('index_width_bits',64), ('payload_type',None), ('index_width_bits',None)]:
            requests = deepcopy(self.requests)
            next(r for r in requests if r['id']=='access-04-read')[field] = value
            plan = plan_hardware(self.case, requests, self.source_groups)
            self.assertEqual(len([b for b in plan['blocks'] if b['family']=='indexed-read']), 2)
            self.assertTrue(plan['separations'])

    def test_stream_and_distinct_update_subtypes_stay_separate(self):
        requests = deepcopy(self.requests)
        update = deepcopy(next(r for r in requests if r['purpose']=='update'))
        update.update(id='synthetic-add', subtype='add')
        requests.append(update)
        plan = plan_hardware(self.case, requests, self.source_groups)
        self.assertEqual(len(plan['blocks']), 4)
        self.assertTrue(any(b['family']=='stream-read' for b in plan['blocks']))
        self.assertEqual(len([b for b in plan['blocks'] if b['family'].startswith('effect-')]), 2)

    def test_duplicate_identity_rejected(self):
        with self.assertRaises(RequestError):
            plan_hardware(self.case, self.requests+self.requests[:1], self.source_groups)

    def test_typed_queries_deduplicate_but_keep_all_members(self):
        from archevolve.hardware_catalog import query_catalog
        with patch('archevolve.hardware_catalog.query_catalog', wraps=query_catalog) as lookup:
            result = query_block(self.catalog, self.indexed())
        self.assertEqual(lookup.call_count, 2)
        gather = next(q for q in result['capability_results'] if q['query']['address_pattern']=='indirect')
        self.assertEqual(gather['member_request_ids'], ['access-02-read','access-04-read'])
        self.assertTrue(any(o['design_id']=='dx100-artifact-e4fc4af' and o['execution_role']=='execute' for o in result['options']))

    def test_no_cross_design_or_cross_role_union(self):
        for cross_role in (False, True):
            def lookup(catalog, **query):
                indirect = query['address_pattern']=='indirect'
                match = {'design_id':'same' if cross_role else 'A' if indirect else 'B',
                         'operation':{'support':'code_observed', 'execution_role':'execute' if indirect or not cross_role else 'assist'}}
                return {'query':query,'matches':[match], 'excluded':[]}
            with patch('archevolve.hardware_catalog.query_catalog', side_effect=lookup):
                result = query_block({}, self.indexed())
            self.assertFalse(result['options'])
            self.assertEqual(len(result['partial_designs']),2)
            self.assertEqual(result['status'],'needs_information_or_explicit_replanning')

    def test_unknown_operation_support_cannot_complete_block(self):
        def lookup(catalog, **query):
            match={'design_id':'same','operation':{'support':'unknown' if query['address_pattern']=='ranged_indirect' else 'code_observed','execution_role':'execute'}}
            return {'query':query,'matches':[match],'excluded':[]}
        with patch('archevolve.hardware_catalog.query_catalog',side_effect=lookup):
            result=query_block({},self.indexed())
        self.assertFalse(result['options'])
        self.assertEqual(len(result['partial_designs'][0]['missing_clause_ids']),1)

    def test_assistance_retains_role_and_missing_type_evidence(self):
        result = query_block(self.catalog, self.indexed())
        assist = next(o for o in result['options'] if o['design_id']=='maple-isca2022' and o['execution_role']=='assist')
        self.assertFalse(assist['satisfies_returned_value_request'])
        self.assertEqual(assist['status'], 'assist_alternative_not_executor')
        request,_ = select_evidence_candidates(self.case,self.catalog,'catalog',self.digest,20)
        maple = next(c for c in request['candidates'] if c.get('catalog_design_id')=='maple-isca2022' and c['candidate_scope']=='read_execute')
        self.assertEqual(maple['status'],'needs_evidence')
        self.assertIn('payload_types',maple['missing_evidence'])

    def test_selection_is_per_block_and_spreads_global_budget(self):
        request,trace=select_evidence_candidates(self.case,self.catalog,'catalog',self.digest,4)
        self.assertEqual(len({c['planned_block_id'] for c in request['candidates'][1:]}),3)
        for c in request['candidates'][1:]:
            covered={r['id'] for o in c['operation_options'] for r in o['matched_requests']}
            self.assertEqual(covered,set(c['planned_block']['member_request_ids']))
        _,small=select_evidence_candidates(self.case,self.catalog,'catalog',self.digest,1)
        self.assertTrue(all(r['handoff_status']=='none_within_focus_and_global_budget' for r in small['block_catalog_results']))
        self.assertTrue(small['capability_queries'])

    def test_planning_runs_before_any_retrieval(self):
        import archevolve.evidence_select as module
        events=[]
        original_plan, original_query=module.plan_hardware,module.query_block
        def plan(*a):
            events.append('plan')
            return original_plan(*a)
        def query(*a):
            events.append('query')
            return original_query(*a)
        with patch.object(module,'plan_hardware',side_effect=plan),patch.object(module,'query_block',side_effect=query):
            select_evidence_candidates(self.case,self.catalog,'catalog',self.digest,1)
        self.assertEqual(events,['plan','query','query','query'])

    def test_mixed_fixture_groups_by_capabilities_preserving_index_arithmetic(self):
        fixture,_=load_request(ROOT/'examples/planning/mixed-access.yaml')
        plan=plan_hardware(fixture['case'],fixture['capability_requests'],fixture['source_groups'])
        self.assertEqual(plan['counts'],{'access_requests':4,'planned_blocks':2,'unique_typed_clauses':2})
        indexed=self.indexed(plan)
        self.assertEqual({m['address_expression'] for m in indexed['members']},{'B[i]','D[2*i+1]'})
        self.assertEqual(indexed['optional_generalizations'],[])
        self.assertTrue(fixture['synthetic'])

    def test_handoff_cannot_change_planned_contract(self):
        from archevolve.intrinsic_handoff import draft_intrinsics, validate_draft
        request,_=select_evidence_candidates(self.case,self.catalog,'catalog',self.digest,4)
        candidate=request['candidates'][1]
        draft=draft_intrinsics(request,candidate)
        draft['planned_block']['member_request_ids']=[]
        with self.assertRaisesRegex(RequestError,'planned capability'):
            validate_draft(draft,candidate)

    def test_generated_plan_diagrams_and_handoff_have_same_block_identity(self):
        artifacts,manifest=prepare_run([self.path],ROOT/'catalog/hardware-v0.1.yaml',source_context_path=ROOT/'examples/bfs.source-observations.yaml')
        plan=yaml.safe_load(artifacts['case-01/hardware-plan.yaml'])
        draft=yaml.safe_load(artifacts['case-01/handoffs/candidate-02/intrinsic-draft.yaml'])
        self.assertIn(draft['planned_block_id'],[b['id'] for b in plan['blocks']])
        self.assertEqual(draft['planned_block'],next(b for b in plan['blocks'] if b['id']==draft['planned_block_id']))
        self.assertIn('flowchart LR',artifacts['case-01/planning-after.mmd'])
        self.assertEqual(manifest['pipeline_version'],'offline-0.4')
        self.assertEqual(manifest['llm_calls'],0)
        self.assertFalse(manifest['evaluation_performed'])


if __name__ == '__main__':
    unittest.main()
