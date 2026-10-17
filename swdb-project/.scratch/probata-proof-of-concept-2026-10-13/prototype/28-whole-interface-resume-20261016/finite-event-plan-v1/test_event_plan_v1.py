"""No-child source preparation controls; never C/model execution."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('finite_fixture_builder',HERE/'build_corpus_v1.py')
builder=importlib.util.module_from_spec(spec);sys.modules[spec.name]=builder;spec.loader.exec_module(builder)
p=builder.producer

class Controls(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='pure-controls-',dir=HERE)
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
    def selected(self,case=None):
        case=deepcopy(case or builder.corpus.cases()[0]);policy=builder.bundle(self.root/'case',case['plan'],case['context'])
        return case,policy
    def prepare(self,policy):return p.prepare(p.OwnedSelection(p.Pin.parse(policy)))
    def test_every_closed_case_prepares_with_bound_profiles_and_separate_predictions(self):
        manifest=builder.build(self.root/'all')
        self.assertEqual(len(manifest['cases']),18)
        self.assertEqual({row['predicted_verdict'] for row in manifest['cases']},{'predicted_valid','predicted_invalid'})
        for row in manifest['cases']:
            cert=json.loads(Path(row['outputs']['certificate.json']['path']).read_bytes())
            plan=json.loads(Path(json.loads(Path(row['policy']['path']).read_bytes())['source_plan']['path']).read_bytes())
            self.assertNotIn('prediction',plan)
            self.assertFalse(cert['ownership_or_initialization_granted'])
            self.assertFalse(cert['actual_compiler_native_solver_or_public_admission'])
            self.assertTrue(cert['public_registry_premise_owner_resolution_required'])
            self.assertEqual(len(cert['physical_inputs']),11)
    def test_resource_derivation_exceeds_default_without_copying_large_profile(self):
        _,policy=self.selected();prepared=self.prepare(policy);profile=json.loads(prepared.resource_profile_json)
        self.assertEqual((profile['nodes_required'],profile['closure_nodes_required'],profile['node_limit']),(129,0,256))
        self.assertEqual((profile['draw_count'],profile['command_limit'],profile['event_limit'],profile['history_limit']),(4,2,3,4))
        self.assertEqual(profile['nodes_required'],sum(row['node_upper_bound'] for row in profile['per_event_node_obligations']))
        self.assertEqual(profile['ordinary_cells_required'],4)
        self.assertIn('#define DXM_NODES 256u',prepared.c_text)
        self.assertNotIn('#define DXM_NODES 4096',prepared.c_text)
    def test_generated_text_retains_backend_history_and_no_grant_at_entry(self):
        _,policy=self.selected();prepared=self.prepare(policy)
        # Header definitions retain resets/allocators; the emitted trace calls none of them.
        trace=prepared.c_text[prepared.c_text.index('static uint64_t dwe_trace_program'):]
        self.assertIn('dxc_cpu_cas(1u,0u,',trace)
        self.assertIn('dxc_cpu_write(1u,0u,',trace)
        for forbidden in ('dxm_claim_tile(', 'dxg_claim(', 'dxm_reset(', 'dxc_reset(', 'SWDB_ASSUME(', 'dxc_get_tile_ready('):
            self.assertNotIn(forbidden,trace)
        self.assertIn('same-thread-read-footprint-write',prepared.c_text)
        self.assertIn('store-footprint-cpu-access',prepared.c_text)
    def test_critical_frontier_is_scoped_and_wait_is_only_explicit(self):
        case=next(row for row in builder.corpus.cases() if row['plan']['id']=='outside_critical_store_positive')
        function,_,_=p.render(case['plan'],case['context'])
        frontier=function.index('unsigned dwe_frontier_5=dxc_count;')
        check=function.index('for(unsigned i=dwe_frontier_5;i<dxc_count;')
        self.assertLess(frontier,check)
        self.assertEqual(function.count('dwi_wait_ready('),1)
        self.assertGreater(function.index('dwi_wait_ready('),check)
        self.assertIn('pending==1u',function)
    def test_negative_properties_are_not_weakened_or_used_as_assumptions(self):
        cases=builder.corpus.cases();positive,_ ,_=p.render(cases[0]['plan'],cases[0]['context'])
        negative,_,_=p.render(cases[1]['plan'],cases[1]['context'])
        self.assertIn('(dwe_value_2==UINT64_C(2)) || (dwe_value_2==UINT64_C(3))',positive)
        self.assertIn('DXM_CHECK((dwe_value_2==UINT64_C(2)),"finite-event-property")',negative)
        self.assertNotIn('SWDB_ASSUME',positive+negative)
        wrong=next(row for row in cases if row['plan']['id']=='wrong_owner_negative')
        function,_,_=p.render(wrong['plan'],wrong['context'])
        self.assertIn('dxp_cpu_write_bits(1u,0u,0u,0u,',function)
    def test_draw_plan_full_domain_and_fatal_budget(self):
        _,policy=self.selected();prepared=self.prepare(policy);draws=json.loads(prepared.draw_plan_json)
        self.assertEqual(draws['domain'],[0,2**32-1]);self.assertTrue(draws['independent'])
        self.assertEqual([row['c_lvalue'] for row in draws['rows']],['dws_choice_table[%d]'%i for i in range(4)])
        self.assertFalse(draws['actual_draws_supplied'])
        self.assertIn('SWDB_CHECK(dws_choice_used<4u,"whole-choice-capacity")',prepared.c_text)
    def test_event_shape_thread_and_arbitrary_text_refuse(self):
        base=builder.corpus.cases()[0]
        mutations=[lambda e:e.update(kind='ownership_grant'),lambda e:e.update(kind='ready_query'),
            lambda e:e.update(c_text='dxm_claim_tile(1,0,4);'),lambda e:e.update(thread=True),lambda e:e.update(thread=2)]
        for mutate in mutations:
            case=deepcopy(base);mutate(case['plan']['events'][0])
            with self.subTest(case=case['plan']['events'][0]),self.assertRaises(p.Refused):p.render(case['plan'],case['context'])
    def test_mapping_alias_mmio_region_and_capacity_refuse(self):
        base=builder.corpus.cases()[0]
        mutations=[lambda p,c:p['objects'][1].update(physical_base=p['objects'][0]['physical_base']),
            lambda p,c:p['objects'][0].update(guest_base=builder.producer.MMIO[0]),
            lambda p,c:p['objects'][0].update(physical_base=builder.producer.MMIO[1]),
            lambda p,c:p['objects'][1].update(base_cell=63),
            lambda p,c:(c['regions'][-1].update(id=7),c['regions'].append(dict(id=6,begin=4100,end=4104))),
            lambda p,c:c.update(live_objects=['a'])]
        for mutate in mutations:
            case=deepcopy(base);mutate(case['plan'],case['context'])
            with self.subTest(case=case['plan']['objects']),self.assertRaises(p.Refused):p.render(case['plan'],case['context'])
    def test_lifetime_use_after_exit_and_critical_thread_mismatch_refuse(self):
        case=deepcopy(builder.corpus.cases()[0]);case['plan']['events']=[builder.corpus.event('lifetime_end',object='a'),builder.corpus.event('cpu_read',1,object='a',lane=0,out='escaped')]
        with self.assertRaises(p.Refused):p.render(case['plan'],case['context'])
        case=deepcopy(builder.corpus.cases()[0]);case['plan']['events']=[builder.corpus.event('critical_begin'),builder.corpus.event('critical_end',1)]
        with self.assertRaises(p.Refused):p.render(case['plan'],case['context'])
    def test_physical_pin_content_topology_and_final_readset(self):
        _,policy=self.selected();raw=Path(policy['path']).read_bytes()
        Path(policy['path']).write_bytes(raw+b' ')
        with self.assertRaises(p.Refused):self.prepare(policy)
        path=self.root/'physical';path.write_bytes(b'x');row=builder.pin(path);reads=p.Inputs();reads.read(row)
        path.unlink();path.symlink_to(HERE/'corpus_v1.py')
        with self.assertRaises(p.Refused):reads.recheck()
    def test_oversized_substitution_refuses_before_open_or_read(self):
        path=self.root/'oversized';path.write_bytes(b'x'*2048)
        selected=p.Pin(str(path),1,p.digest(b'x'))
        with patch.object(Path,'open',side_effect=AssertionError('oversized input was opened')):
            with self.assertRaisesRegex(p.Refused,'actual input extent'):p.Inputs().read(selected)
    def test_receiver_and_owner_entry_binding_are_checked_but_not_authority(self):
        _,policy=self.selected();document=json.loads(Path(policy['path']).read_bytes())
        context=json.loads(Path(document['context']['path']).read_bytes());context['owned_premises'][0]['owner']['id']='other'
        document['context']=builder.save(Path(document['context']['path']),context)
        changed=builder.save(Path(policy['path']),document)
        with self.assertRaises(p.Refused):self.prepare(changed)
    def test_unknown_json_fields_duplicate_and_nonfinite_refuse(self):
        path=self.root/'doc';path.write_bytes(b'{"x":1,"x":2}')
        with self.assertRaises(p.Refused):p.Inputs().document(builder.pin(path))
        path.write_bytes(b'{"x":NaN}')
        with self.assertRaises(p.Refused):p.Inputs().document(builder.pin(path))
        _,policy=self.selected();doc=json.loads(Path(policy['path']).read_bytes());doc['callback']='anything'
        changed=builder.save(Path(policy['path']),doc)
        with self.assertRaises(p.Refused):self.prepare(changed)

if __name__=='__main__':unittest.main()
