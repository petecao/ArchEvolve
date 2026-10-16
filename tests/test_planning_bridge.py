from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import yaml

from archevolve.__main__ import ROOT
from archevolve.evolution_runtime import OfflineEvolution
from archevolve.evolution_store import EvolutionStore,digest
from archevolve.planning_bridge import (HardwarePlanningBridge,SavedHardwareProposals,export_run,
                                         reflection_exchange,replay_reflection)
from archevolve.planning_replay import main
from tools.make_planning_replay_fixture import fixture
from tools.render_mermaid import RequestError,load_request


class PlanningBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'memory.sqlite'
        self.store=EvolutionStore(self.path)
        self.bridge=HardwarePlanningBridge(self.store,ROOT/'examples/received/bfs-sparse.features.v1.2.yaml',
            ROOT/'catalog/hardware-v0.1.yaml',ROOT/'examples/bfs.source-observations.yaml')
        self.document=fixture()
        self.proposer=SavedHardwareProposals(self.store,self.document)
        OfflineEvolution.initialize(self.store,**self.bridge.seed(3))
        self.loop=OfflineEvolution(self.store,self.proposer,self.bridge.evaluate)

    def tearDown(self):
        self.store.close();self.tmp.cleanup()

    def evaluation(self,index=0):
        return self.store.get(self.store.events('observation')[index]['record']['evaluation_ref'])

    def test_real_pipeline_replay_handoffs_feedback_and_no_ranking(self):
        before=deepcopy(self.bridge.catalog)
        with patch('socket.create_connection',side_effect=AssertionError('No network')):
            refs=self.loop.run_epoch()
        self.assertEqual(len(refs),3)
        self.assertEqual([self.evaluation(i)['planning_status'] for i in range(3)],['needs_information','needs_information','rejected'])
        self.assertTrue(all(not self.store.get(r)['eligible'] for r in refs))
        self.assertEqual(self.bridge.catalog,before)
        self.assertIsNone(self.loop.policy['area_limit_mm2'])
        self.assertEqual(self.loop.usage(),{'calls':3,'tokens':0,'evaluations':3})
        self.assertTrue(all(self.evaluation(i)['latency_ms'] is None for i in range(3)))
        files=self.store.get(self.evaluation()['artifact_bundle_ref'])['files']
        self.assertIn('handoffs/candidate-02/parameter-space.template.yaml',files)
        draft=yaml.safe_load(files['handoffs/candidate-02/intrinsic-draft.yaml'])
        self.assertEqual(draft['planned_block']['member_request_ids'],['access-02-read','access-03-read','access-04-read'])
        hardware=yaml.safe_load(files['hardware-request.yaml'])
        self.assertEqual(len(hardware['candidates']),2)
        self.assertEqual(hardware['candidates'][1]['selected_configuration'],{})
        self.assertTrue(all(op['concrete_signature'] is None for op in draft['operations']))

    def test_invalid_and_stale_plans_cannot_generate_packages(self):
        for change in ('binding','unknown_design','dropped_block','duplicate_block','role','extra_capability','parameter_edit'):
            with self.subTest(change=change):
                p=deepcopy(self.document['entries'][0]['content']);d=p['design']
                choice=next(c for c in d['block_choices'] if c['action']=='catalog_option')
                if change=='binding':d['bindings']['catalog_sha256']=digest('stale')
                if change=='unknown_design':choice['design_id']='invented'
                if change=='dropped_block':d['block_choices'].pop()
                if change=='duplicate_block':d['block_choices'].append(deepcopy(d['block_choices'][0]))
                if change=='role':choice['execution_role']='invented'
                if change=='extra_capability':d['new_capability']='invented'
                if change=='parameter_edit':p['mutation']='admitted_parameter'
                result=self.bridge.evaluate({'candidate':p,'candidate_ref':digest(p),'task':self.loop.policy['tasks'][0],'mode':'offline_planning'})
                self.assertEqual(result['planning_status'],'rejected')
                self.assertIsNone(result['artifact_bundle_ref'])

    def test_partial_catalog_match_does_not_become_composed_solution(self):
        p=deepcopy(self.document['entries'][0]['content'])
        choice=next(c for c in p['design']['block_choices'] if c['action']=='catalog_option')
        choice.update(design_id='dx100-artifact-e4fc4af',execution_role='assist')
        result=self.bridge.evaluate({'candidate':p,'candidate_ref':digest(p),'task':self.loop.policy['tasks'][0],'mode':'offline_planning'})
        self.assertEqual(result['planning_status'],'rejected')

    def test_reflection_reads_actual_failures_and_stays_pending(self):
        self.loop.run_epoch();active=self.loop.active('strategy')
        exchange=reflection_exchange(self.loop,'strategy')
        history=exchange['request']['context']['history']
        self.assertEqual(history[2]['evaluation']['planning_status'],'rejected')
        self.assertTrue(history[0]['evaluation']['issues'])
        content=deepcopy(exchange['request']['context']['strategy'])
        content['reasoning_guidance'].append('Check exact operation support before requesting a CPU CAS offload.')
        exchange.update(provenance='Hand-authored test response to actual structural feedback',response={'content':content,'tokens':0})
        ref=replay_reflection(self.loop,exchange)
        self.assertEqual(self.loop.active('strategy'),active)
        self.assertEqual(self.store.get(ref)['feedback_refs'],self.loop.history())
        self.assertEqual(self.store.get(ref)['author_reflector'],self.loop.active('reflector'))
        self.assertEqual(self.loop.usage()['tokens'],0)
        with self.assertRaisesRegex(ValueError,'separate evidence campaign'):self.loop.trial(ref)
        with self.assertRaisesRegex(ValueError,'cannot promote'):self.loop.promote(ref,{})
        with self.assertRaisesRegex(RequestError,'context changed'):replay_reflection(self.loop,exchange)

    def test_reflection_cannot_change_core_or_supply_live_token_receipts(self):
        self.loop.run_epoch()
        ex=reflection_exchange(self.loop,'reflector')
        ex['provenance']='test';ex['response']={'content':deepcopy(ex['request']['context']['reflector']),'tokens':1}
        with self.assertRaisesRegex(RequestError,'tokens: 0'):replay_reflection(self.loop,ex)
        ex['response']['tokens']=0;ex['response']['content']['evaluator']='accept all'
        with self.assertRaisesRegex(ValueError,'Only reflector'):replay_reflection(self.loop,ex)

    def test_saved_response_never_rebinds_parent_or_strategy_or_history(self):
        for field in ('parent','strategy','history'):
            doc=deepcopy(self.document)
            if field=='parent':doc['entries'][0]['content']['parent_ref']=digest('other')
            if field=='strategy':doc['entries'][0]['strategy_sha256']=digest('other')
            if field=='history':doc['entries'][0]['history_sha256']=digest('other')
            proposer=SavedHardwareProposals(self.store,doc)
            ctx=self.loop._context(self.loop.active('reflector'),self.loop.active('strategy'))
            ctx['task']=self.loop.policy['tasks'][0];ctx['parent_ref']=self.document['entries'][0]['content']['parent_ref']
            with self.assertRaises(RequestError):proposer({'operation':'propose','sequence':0,'context':ctx})

    def test_structural_mode_cannot_accept_timing_claims(self):
        def bad(request):
            result=self.bridge.evaluate(request);result['latency_ms']=1
            return result
        self.loop.evaluator=bad
        refs=self.loop.run_epoch()
        self.assertTrue(all(not self.store.get(r)['eligible'] for r in refs))
        self.assertTrue(all('cannot carry' in self.store.get(r)['reasons'][0] for r in refs))

    def test_resume_preserves_context_and_export_hashes(self):
        self.loop.run_epoch();exchange=reflection_exchange(self.loop,'reflector')
        self.store.close();self.store=EvolutionStore(self.path)
        loop=OfflineEvolution(self.store,None,None)
        self.assertEqual(reflection_exchange(loop,'reflector'),exchange)
        directory=Path(self.tmp.name)/'export'
        report=export_run(self.store,directory)
        self.assertEqual(report['llm_calls'],0);self.assertEqual(report['hardware_evaluations'],0)
        self.assertTrue((directory/'proposal-001/handoffs/candidate-02/intrinsic-draft.yaml').exists())
        self.assertFalse((directory/'proposal-003/handoffs').exists())
        with self.assertRaises(RequestError):export_run(self.store,directory)

    def test_planning_initialization_does_not_weaken_evidence_modes(self):
        for mode in ('offline_evidence','synthetic_demo'):
            seed=self.bridge.seed(3);seed['policy']['mode']=mode
            other=EvolutionStore(Path(self.tmp.name)/(mode+'.sqlite'))
            try:
                with self.assertRaises(ValueError):OfflineEvolution.initialize(other,**seed)
            finally:other.close()

    def test_cli_end_to_end_and_fixture_pins(self):
        saved,_=load_request(ROOT/'examples/planning-replay/bfs.proposals.yaml')
        self.assertEqual(saved,self.document)
        out=Path(self.tmp.name)/'cli';db=Path(self.tmp.name)/'cli.sqlite'
        args=['run','--input',str(ROOT/'examples/received/bfs-sparse.features.v1.2.yaml'),
              '--catalog',str(ROOT/'catalog/hardware-v0.1.yaml'),'--source-context',str(ROOT/'examples/bfs.source-observations.yaml'),
              '--proposals',str(ROOT/'examples/planning-replay/bfs.proposals.yaml'),'--store',str(db),'--output-dir',str(out)]
        self.assertEqual(main(args),0)
        self.assertEqual(main(args),2)
        context=Path(self.tmp.name)/'context.yaml'
        self.assertEqual(main(['export-reflection','--store',str(db),'--output',str(context)]),0)
        value,_=load_request(context)
        self.assertIsNone(value['response'])
        self.assertEqual(len(value['request']['context']['history']),3)


if __name__=='__main__':unittest.main()
