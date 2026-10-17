from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
import yaml

from archevolve.__main__ import ROOT,prepare_run
from archevolve.evolution_policy import COHORT_PINS
from archevolve.evolution_store import digest
from archevolve.parameter_cli import artifacts,main
from archevolve.parameter_exploration import template,enumerate_configurations,compare_evaluations,evaluation_template,evaluated_identity
from tools.render_mermaid import load_request,RequestError


class ParameterExplorationTests(unittest.TestCase):
    def setUp(self):
        self.candidate,_=load_request(ROOT/'examples/parameters/candidate.yaml')
        self.space,_=load_request(ROOT/'examples/parameters/space.yaml')

    def plan(self,space=None):
        return enumerate_configurations(self.candidate,space or self.space)

    def cohort(self):
        return {**{k:digest(k) for k in COHORT_PINS},'catalog_sha256':self.space['bindings']['catalog_sha256'],
                'evidence_tier':'analytical_planning','target_kind':'analytical_model','latency_unit':'ms',
                'area_unit':'mm2','area_convention':'incremental_accelerator'}

    def batch(self,space=None):
        plan=self.plan(space);c=self.cohort();batch=evaluation_template(plan)
        for i,config in enumerate(plan['configurations'][:2]):
            impl=evaluated_identity(config,digest('software'+str(i)),digest('hardware'+str(i)),digest('build'+str(i)))
            row={'candidate_id':config['id'],'candidate_sha256':digest(impl),'evaluated_candidate_sha256':digest(impl),
                 'design_role':'accelerator_candidate','status':'completed','target_refuted':False,
                 'cohort':c,'placeholder_fields':[],'model_applicability':'in_domain','metrics_complete':True,
                 'latency_ms':10-i,'area_mm2':2+i,'evidence_refs':['synthetic-test-only'],
                 'correctness':'functional_model_pass','execution_witness':'pass','legality':'conditional_reviewed',
                 'evidence_kind':'analytical_model','synthetic':True}
            batch['records'].append({'configuration_id':config['id'],'implementation':impl,'evaluation':row})
        return batch,c

    def test_synthetic_finite_sweep_checks_power_of_two_and_coupling(self):
        before=deepcopy((self.candidate,self.space));plan=self.plan()
        self.assertEqual(plan['total_combinations'],9)
        self.assertEqual(plan['combinations_checked'],9)
        self.assertEqual(len(plan['configurations']),5)
        self.assertEqual(len(plan['rejected']),4)
        self.assertFalse(plan['truncated'])
        self.assertIsNone(plan['cost_model'])
        for config in plan['configurations']:
            v=config['identity']['values']
            self.assertIn(v['depth'],[4,8]);self.assertLessEqual(v['lanes']*v['depth'],16)
            self.assertEqual(config['evaluation'],{'status':'not_run','latency_ms':None,'area_mm2':None,'power_w':None})
            self.assertTrue(config['software_handoff']['pending_parameters'])
        self.assertEqual((self.candidate,self.space),before)

    def test_unknown_domains_and_coupling_block_even_when_reviews_exist(self):
        for key in ('legal_domain','review','role'):
            s=deepcopy(self.space)
            s['parameters'][0][key]='unresolved' if key=='role' else None
            self.assertFalse(self.plan(s)['configurations'])
        for key in ('coupled_constraints','legality_review'):
            s=deepcopy(self.space);s[key]=None
            self.assertFalse(self.plan(s)['configurations'])
        s=deepcopy(self.space);s['coupled_constraints']=[]
        self.assertEqual(len(self.plan(s)['configurations']),9)

    def test_reference_values_do_not_become_domains_or_selections(self):
        candidate=deepcopy(self.candidate)
        candidate['parameter_contract'][0].update(state='fixed_reference',value=16384)
        space=template(candidate,digest('input'),digest('catalog'))
        plan=enumerate_configurations(candidate,space)
        self.assertFalse(plan['configurations'])
        self.assertEqual(space['parameters'][0]['value'],16384)
        self.assertIsNone(space['parameters'][0]['legal_domain'])
        self.assertEqual(space['parameters'][0]['role'],'unresolved')

    def test_reference_only_requires_explicit_review_and_is_not_selected(self):
        s=deepcopy(self.space)
        p=next(p for p in s['parameters'] if p['id']=='lanes')
        p.update(role='reference_only',legal_domain=None)
        s['coupled_constraints']=[]
        plan=self.plan(s)
        self.assertEqual(len(plan['configurations']),3)
        self.assertTrue(all('lanes' not in c['identity']['values'] for c in plan['configurations']))
        p['review']=None
        self.assertFalse(self.plan(s)['configurations'])

    def test_limits_report_checked_prefix_and_do_not_claim_exhaustiveness(self):
        for budget in ({'max_configurations':2,'max_combinations_checked':9},{'max_configurations':9,'max_combinations_checked':2}):
            s=deepcopy(self.space);s['budget']=budget
            p=self.plan(s)
            self.assertTrue(p['truncated']);self.assertGreater(p['unvisited_combinations'],0)
            self.assertLessEqual(p['combinations_checked'],budget['max_combinations_checked'])
            self.assertLessEqual(len(p['configurations']),budget['max_configurations'])

    def test_large_range_is_lazy_and_failed_prefix_is_not_no_solution(self):
        s=deepcopy(self.space)
        s['parameters'][0]['legal_domain']={'kind':'integer_range','min':1,'max':10**12,'step':1}
        s['coupled_constraints']=[{'id':'none-in-prefix','kind':'allowed_tuples','parameters':['lanes'],'values':[[100000]]}]
        s['budget']={'max_configurations':2,'max_combinations_checked':3}
        p=self.plan(s)
        self.assertEqual(p['combinations_checked'],3)
        self.assertEqual(p['status'],'no_admissible_configuration_in_checked_prefix')
        self.assertTrue(p['truncated'])

    def test_domain_rejects_unbounded_invalid_and_duplicate_values(self):
        for d in ({'kind':'integer_range','min':1,'max':None,'step':1},{'kind':'integer_range','min':1,'max':5,'step':0},
                  {'kind':'enum','values':[]},{'kind':'enum','values':[True]},{'kind':'enum','values':[1,1.0]},
                  {'kind':'enum','values':[float('inf')]},{'kind':'python','expression':'exit()'}):
            s=deepcopy(self.space);s['parameters'][0]['legal_domain']=d
            with self.assertRaises(RequestError):self.plan(s)

    def test_constraint_unknown_parameter_and_code_are_rejected(self):
        for c in ({'id':'x','kind':'equal','parameters':['lanes','missing']},
                  {'id':'x','kind':'eval','parameters':['lanes'],'expression':'exit()'},
                  {'id':'x','kind':'product_at_most','parameters':['lanes'],'limit':None}):
            s=deepcopy(self.space);s['coupled_constraints']=[c]
            with self.assertRaises(RequestError):self.plan(s)

    def test_identities_change_with_values_and_scope_and_bind_software(self):
        plan=self.plan();ids={c['sha256'] for c in plan['configurations']}
        self.assertEqual(len(ids),len(plan['configurations']))
        s=deepcopy(self.space);s['budget']['max_configurations']=63
        self.assertTrue(ids.isdisjoint({c['sha256'] for c in self.plan(s)['configurations']}))
        config=plan['configurations'][0]
        self.assertNotEqual(digest(evaluated_identity(config,digest('s1'),digest('h'),digest('b'))),digest(evaluated_identity(config,digest('s2'),digest('h'),digest('b'))))

    def test_no_silent_catalog_changes_or_missing_parameters(self):
        for kind in ('drop','unit','value','candidate'):
            s=deepcopy(self.space)
            if kind=='drop':s['parameters'].pop()
            if kind=='unit':s['parameters'][0]['unit']='bytes'
            if kind=='value':s['parameters'][0]['value']=16
            if kind=='candidate':s['candidate_sha256']=digest('other')
            with self.assertRaises(RequestError):self.plan(s)

    def test_offline_comparison_keeps_tradeoffs_pending_unknowns_and_no_winner(self):
        batch,c=self.batch();out=compare_evaluations(self.candidate,self.space,batch,c)
        self.assertEqual(len(out['frontier']['frontier_ids']),2)
        self.assertEqual(len(out['pending_configuration_ids']),3)
        self.assertIsNone(out['selected_winner']);self.assertIsNone(out['forecast_cost_model'])
        self.assertEqual(out['unresolved_cost_limits'],['area_mm2','power_w'])

    def test_wrong_configuration_mode_missing_cost_and_placeholder_cannot_rank(self):
        for kind in ('configuration','implementation','mode','unknown_area','placeholder','cohort'):
            batch,c=self.batch();item=batch['records'][0]
            if kind=='configuration':item['implementation']['configuration_sha256']=digest('other')
            if kind=='implementation':item['implementation']['software_sha256']=digest('other')
            if kind=='mode':item['evaluation']['synthetic']=False
            if kind=='unknown_area':item['evaluation']['area_mm2']=None
            if kind=='placeholder':item['evaluation']['placeholder_fields']=['accelerator_time']
            if kind=='cohort':item['evaluation']['cohort']={**c,'roi_sha256':digest('other')}
            out=compare_evaluations(self.candidate,self.space,batch,c)
            self.assertNotIn(item['configuration_id'],out['frontier']['eligible_ids'])

    def test_duplicate_rows_and_stale_space_rejected(self):
        batch,c=self.batch();batch['records'].append(deepcopy(batch['records'][0]))
        with self.assertRaises(RequestError):compare_evaluations(self.candidate,self.space,batch,c)
        batch,c=self.batch();batch['space_sha256']=digest('old')
        with self.assertRaises(RequestError):compare_evaluations(self.candidate,self.space,batch,c)

    def test_cost_caps_require_actual_values_and_frozen_model(self):
        s=deepcopy(self.space);s['cost_limits']={'area_mm2':1,'power_w':None}
        batch,c=self.batch()
        # Changing policy changes configuration identities, so old receipts cannot be reused.
        with self.assertRaises(RequestError):compare_evaluations(self.candidate,s,batch,c)
        s['cost_model']={'sha256':digest('declared-model'),'description':'synthetic','evidence_refs':['fixture']}
        batch=evaluation_template(self.plan(s))
        with self.assertRaisesRegex(RequestError,'Cost model'):compare_evaluations(self.candidate,s,batch,c)

    def test_area_and_power_limits_filter_imported_values(self):
        for limits,reason in [({'area_mm2':1,'power_w':None},'area_limit_exceeded'),
                              ({'area_mm2':None,'power_w':3},'power_unknown_or_limit_exceeded')]:
            s=deepcopy(self.space);s['cost_limits']=limits
            batch,c=self.batch(s)
            result=compare_evaluations(self.candidate,s,batch,c)
            self.assertFalse(result['frontier']['frontier_ids'])
            self.assertTrue(all(reason in v for v in result['frontier']['excluded'].values()))
        batch,c=self.batch(s)
        for item in batch['records']:item['evaluation']['power_w']=2
        self.assertEqual(len(compare_evaluations(self.candidate,s,batch,c)['frontier']['frontier_ids']),2)

    def test_equal_order_and_exact_decimal_product_constraints(self):
        from archevolve.parameter_exploration import constraint_passes
        self.assertTrue(constraint_passes({'kind':'equal','parameters':['a','b']},{'a':4,'b':4}))
        self.assertFalse(constraint_passes({'kind':'less_equal','parameters':['a','b']},{'a':5,'b':4}))
        self.assertTrue(constraint_passes({'kind':'product_at_most','parameters':['a','b'],'limit':0.3},{'a':0.1,'b':3}))

    def test_reviews_require_resolvable_evidence(self):
        s=deepcopy(self.space);s['parameters'][0]['review']['evidence_refs']=['unresolved-reference']
        with self.assertRaisesRegex(RequestError,'evidence'):self.plan(s)

    def test_cli_preserves_outputs_and_produces_configuration_handoffs(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/'run'
            args=['enumerate','--candidate',str(ROOT/'examples/parameters/candidate.yaml'),'--space',str(ROOT/'examples/parameters/space.yaml'),'--output-dir',str(output)]
            self.assertEqual(main(args),0)
            original=(output/'exploration.yaml').read_bytes()
            self.assertEqual(len(list(output.glob('configurations/*/software-handoff.yaml'))),5)
            self.assertEqual(main(args),2)
            self.assertEqual((output/'exploration.yaml').read_bytes(),original)

    def test_forward_handoffs_include_blocked_real_parameter_template(self):
        files,_=prepare_run([ROOT/'examples/received/bfs-sparse.features.v1.2.yaml'],ROOT/'catalog/hardware-v0.1.yaml',max_candidates=2)
        c=yaml.safe_load(files['case-01/handoffs/candidate-02/candidate.yaml'])
        s=yaml.safe_load(files['case-01/handoffs/candidate-02/parameter-space.template.yaml'])
        self.assertFalse(s['synthetic'])
        self.assertFalse(enumerate_configurations(c,s)['configurations'])
        self.assertIsNone(s['cost_model'])
        self.assertEqual(c['selected_configuration'],{})


if __name__=='__main__':unittest.main()
