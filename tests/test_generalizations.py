from copy import deepcopy
import unittest
import yaml

from archevolve.__main__ import ROOT,reference_context,prepare_run
from archevolve.evidence_select import capability_requests
from archevolve.generalizations import propose_generalizations,query_pairs,parse_annotation,generalization_artifacts
from archevolve.hardware_planning import plan_hardware,query_block
from archevolve.normalize import load_normalized
from archevolve.workload_context import bind_context,request_groups
from tools.render_mermaid import load_request,RequestError


class GeneralizationTests(unittest.TestCase):
    def setUp(self):
        fixture,_=load_request(ROOT/'examples/planning/mixed-access.yaml')
        self.mixed=plan_hardware(fixture['case'],fixture['capability_requests'],fixture['source_groups'])
        self.catalog,_=load_request(ROOT/'catalog/hardware-v0.1.yaml')
        case=load_normalized(ROOT/'examples/received/bfs-sparse.features.v1.2.yaml',reference_context(ROOT))
        context,h=load_request(ROOT/'examples/bfs.source-observations.yaml')
        case=bind_context(case,context,h,'examples/bfs.source-observations.yaml')
        reqs,_=capability_requests(case)
        self.bfs=plan_hardware(case,reqs,request_groups(case,reqs))

    def report_for(self,expr):
        plan=deepcopy(self.mixed)
        plan['blocks']=[plan['blocks'][0]]
        plan['blocks'][0]['members']=[plan['blocks'][0]['members'][0]]
        plan['blocks'][0]['members'][0]['address_expression']=expr
        return propose_generalizations(plan)

    def test_bfs_observed_offset_uses_bound_source_annotation(self):
        report=propose_generalizations(self.bfs)
        self.assertEqual(len(report['proposals']),1)
        p=report['proposals'][0]
        self.assertEqual(p['identity']['request_id'],'access-02-read')
        self.assertEqual(p['identity']['site']['statement_ids'],['bfs-td-row-bounds'])
        self.assertEqual(p['identity']['site']['origin'],'source_context_access_expression')
        self.assertEqual(p['generalized_request']['requested_extension']['parameter']['baseline_setting'],1)
        self.assertEqual(p['minimum_request']['required_capabilities']['mutable_read_request_ids'],['access-04-read'])
        self.assertFalse(p['baseline_restoration']['program_equivalence_verified'])

    def test_mixed_offset_and_scale_are_separate_single_site_proposals(self):
        report=propose_generalizations(self.mixed)
        self.assertEqual(len(report['proposals']),3)
        nested=[p for p in report['proposals'] if p['identity']['request_id']=='gather-c-read']
        expressions={p['generalized_request']['requested_extension']['proposed_expression'] for p in nested}
        self.assertEqual(expressions,{'D[2 * i + ae_offset]','D[ae_scale * i + 1]'})
        self.assertEqual({p['identity']['kind'] for p in nested},{'configurable_index_offset','configurable_index_scale'})
        direct=next(p for p in report['proposals'] if p['identity']['request_id']=='stream-y-read')
        self.assertEqual(direct['identity']['observed_value'],2)

    def test_minimum_plan_and_catalog_are_unchanged(self):
        before=deepcopy((self.bfs,self.catalog))
        results=[query_block(self.catalog,b) for b in self.bfs['blocks']]
        artifacts=generalization_artifacts(self.bfs,results)
        self.assertEqual((self.bfs,self.catalog),before)
        report=yaml.safe_load(artifacts['generalization-proposals.yaml'])
        self.assertFalse(report['minimum_plan_changed']);self.assertFalse(report['catalog_changed'])
        self.assertTrue(all(b['optional_generalizations']==[] for b in self.bfs['blocks']))

    def test_all_added_cost_support_domain_and_implementation_fields_stay_unknown(self):
        for p in propose_generalizations(self.mixed)['proposals']:
            self.assertIsNone(p['hardware_support']);self.assertIsNone(p['additional_hardware_requirements'])
            self.assertIsNone(p['software_changes']);self.assertIsNone(p['admitted_parameter_domain'])
            self.assertTrue(all(v is None for v in p['additional_cost'].values()))
            self.assertFalse(p['cheapness_assessed']);self.assertFalse(p['legality_verified'])
            self.assertFalse(p['ready_for_implementation']);self.assertFalse(p['selected'])
            ext=p['generalized_request']['requested_extension']
            self.assertIsNone(ext['computation_location'])
            for k in ('legal_values','width_bits','signedness','configuration_granularity'):self.assertIsNone(ext['parameter'][k])

    def test_baseline_catalog_matches_do_not_certify_generalization(self):
        results=[query_block(self.catalog,b) for b in self.mixed['blocks']]
        report=propose_generalizations(self.mixed);pairs=query_pairs(report,results)
        self.assertTrue(pairs['pairs'][0]['minimum_result']['options'])
        for pair in pairs['pairs']:
            self.assertIsNone(pair['generalized_result']['supported'])
            self.assertIsNone(pair['generalized_result']['matching_designs'])
            with self.assertRaisesRegex(RequestError,'cannot certify'):
                query_block(self.catalog,pair['generalized_query'])
        self.assertIsNone(pairs['selected_generalization'])
        self.assertFalse(pairs['cost_comparison_performed'])

    def test_no_literals_no_fabricated_generalization(self):
        for expr in ('i','B[i]','g.out_neighbors_[j]','a+b','2+3','A[2]'):
            self.assertFalse(self.report_for(expr)['proposals'],expr)

    def test_unsupported_syntax_is_not_evaluated_or_guessed(self):
        for expr in ('f(i+2)','i << 2','i / 2','(int)i + 2','i + 1.5','i + True','__import__("os").system("echo bad")'):
            report=self.report_for(expr)
            self.assertFalse(report['proposals'],expr)
            self.assertEqual(report['diagnostics'][0]['reason'],'unsupported_annotation_syntax')
        self.assertEqual(parse_annotation('i+'+'1'*2000)[1],'expression_exceeds_parser_budget')

    def test_signs_positions_and_variable_capture_are_preserved(self):
        for expr,value in [('i-3',3),('i+-3',-3),('2*i',2),('i*2',2),('i+0',0)]:
            ps=self.report_for(expr)['proposals']
            self.assertEqual(len(ps),1)
            self.assertEqual(ps[0]['identity']['observed_value'],value)
            self.assertEqual(ps[0]['baseline_restoration']['status'],'annotation_ast_restores_observed_expression')
        p=self.report_for('ae_offset + 2')['proposals'][0]
        self.assertEqual(p['generalized_request']['requested_extension']['parameter']['name'],'ae_offset_')

    def test_budget_and_deterministic_identity(self):
        report=propose_generalizations(self.mixed,1)
        self.assertEqual(len(report['proposals']),1);self.assertTrue(report['truncated'])
        self.assertEqual(report['eligible_literal_sites'],3)
        full=propose_generalizations(self.mixed)
        self.assertEqual(report['proposals'][0],full['proposals'][0])
        self.assertEqual(full,propose_generalizations(deepcopy(self.mixed)))
        self.assertEqual(len({p['id'] for p in full['proposals']}),3)
        for bad in (0,True,257):
            with self.assertRaises(RequestError):propose_generalizations(self.mixed,bad)

    def test_effect_blocks_are_not_generalized(self):
        plan=deepcopy(self.mixed)
        for b in plan['blocks']:b['required_capabilities']['operations']=['read_modify_write']
        self.assertFalse(propose_generalizations(plan)['proposals'])

    def test_unbound_context_cannot_supply_bfs_offset_annotation(self):
        plan=deepcopy(self.bfs);plan['source_context_groups']=[]
        for b in plan['blocks']:
            for m in b['members']:m['statement_ids']=[];m['source_locations']=[];m['statement_binding_status']='unbound'
        self.assertFalse(propose_generalizations(plan)['proposals'])

    def test_forward_pipeline_emits_optional_sidecars_without_selecting_them(self):
        files,_=prepare_run([ROOT/'examples/received/bfs-sparse.features.v1.2.yaml'],ROOT/'catalog/hardware-v0.1.yaml',
            max_candidates=2,source_context_path=ROOT/'examples/bfs.source-observations.yaml')
        report=yaml.safe_load(files['case-01/generalization-proposals.yaml'])
        self.assertEqual(len(report['proposals']),1)
        request=yaml.safe_load(files['case-01/hardware-request.yaml'])
        self.assertTrue(all(b['optional_generalizations']==[] for b in request['hardware_plan']['blocks']))
        for c in request['candidates'][1:]:self.assertEqual(c['selected_configuration'],{})
        self.assertIn('generalization-queries.yaml',files['case-01/generalizations.md'])


if __name__=='__main__':unittest.main()
