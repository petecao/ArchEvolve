from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import tempfile
import unittest
import yaml

from archevolve.__main__ import ROOT,prepare_run
from archevolve.dx100_parameter_adapter import prepare_candidates,TILES
from archevolve.parameter_exploration import enumerate_configurations,validate_space
from archevolve.parameter_cli import main
from tools.render_mermaid import load_request,RequestError


class DX100DomainAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files,cls.manifest=prepare_run([ROOT/'examples/received/bfs-sparse.features.v1.2.yaml'],ROOT/'catalog/hardware-v0.1.yaml',max_candidates=2)
        cls.candidate=yaml.safe_load(cls.files['case-01/handoffs/candidate-02/candidate.yaml'])
        cls.input_hash=cls.manifest['cases'][0]['input_sha256']
        cls.catalog_hash=cls.manifest['identity']['catalog_sha256']
        cls.folder=ROOT/'docs/designs/dx100-parameter-domain'

    def adapt(self,candidate=None,folder=None,budget=6):
        folder=folder or self.folder
        return prepare_candidates(candidate or self.candidate,self.input_hash,self.catalog_hash,
            folder/'contract.yaml',folder/'verification.json',folder/'published-dx100-calibration.json',budget)

    def test_six_source_supported_candidates_are_not_admitted(self):
        before=deepcopy(self.candidate)
        files,plan=self.adapt()
        self.assertEqual([p['identity']['proposed_model_parameters']['num_tile_elements'] for p in plan['candidates']],TILES)
        self.assertEqual(plan['admitted_configurations'],[])
        self.assertFalse(plan['evaluation_performed']);self.assertFalse(plan['ready_to_execute'])
        self.assertIsNone(plan['selected_winner'])
        self.assertEqual(self.candidate,before)
        for p in plan['candidates']:
            self.assertEqual(p['status'],'candidate_pending_validation')
            self.assertFalse(p['independently_validated']);self.assertFalse(p['eligible_for_performance_ranking'])
            self.assertEqual(p['metrics'],{'latency_ms':None,'area_mm2':None,'power_w':None})
        profile=yaml.safe_load(files['candidate-domain.yaml'])
        self.assertIsNone(profile['vary']['num_tile_elements']['legal_domain'])
        self.assertEqual(profile['vary']['num_tile_elements']['independently_validated_values'],[])
        self.assertEqual(len(profile['parameter_inventory']),26)
        self.assertEqual(len(profile['coupling_constraints']),12)
        self.assertEqual(len(profile['source_files']),17)

    def test_only_tile_size_varies_and_boolean_freezes_are_preserved(self):
        _,plan=self.adapt()
        rows=[p['identity']['proposed_model_parameters'] for p in plan['candidates']]
        for key in rows[0]:
            if key!='num_tile_elements':self.assertEqual(len({r[key] for r in rows}),1)
        self.assertIs(rows[0]['reconfigure_row_table'],False)
        self.assertIs(rows[0]['no_reorder'],False)
        self.assertEqual(rows[0]['num_cores'],4);self.assertEqual(rows[0]['num_maas'],1)

    def test_rebuild_requests_and_unbound_execution_checks_are_explicit(self):
        files,plan=self.adapt()
        for p in plan['candidates']:
            n=p['identity']['proposed_model_parameters']['num_tile_elements']
            request=p['build_validation_request']
            self.assertEqual(request['compile_constants']['TILE_SIZE'],n)
            self.assertEqual(request['expected_cli_values']['--maa_num_tile_elements'],n)
            self.assertEqual(request['compile_constants']['NUM_CORES'],4)
            self.assertIn('max_outstanding_cpu_side_packets',request['direct_configuration_required'])
            self.assertIn('cache_snoop_latency',request['direct_configuration_required'])
            self.assertTrue({'dram_topology','effective_config','compiled_binary','worker_ownership','selected_mapping','request_and_address_bounds'} <= {g['id'] for g in p['execution_preflight']})
            receipt=request['required_receipts']
            self.assertIsNone(receipt['binary_sha256']);self.assertIsNone(receipt['config_ini_sha256'])
            self.assertIsNone(receipt['dram_topology']);self.assertIsNone(receipt['root'])
            self.assertEqual(receipt['correctness']['status'],'not_run')
            self.assertEqual(receipt['intended_path']['status'],'not_run')
            self.assertIn('candidates/'+p['id']+'/receipt.template.yaml',files)

    def test_reference_aliases_and_strict_explorer_are_not_overwritten(self):
        files,_=self.adapt()
        strict=yaml.safe_load(files['strict-space.template.yaml'])
        self.assertFalse(enumerate_configurations(self.candidate,strict)['configurations'])
        self.assertEqual(next(p['value'] for p in strict['parameters'] if p['id']=='tile_elements'),16384)
        self.assertIsNone(next(p['value'] for p in strict['parameters'] if p['id']=='effective_tile_elements'))
        self.assertIsNone(strict['cost_model']);self.assertIsNone(strict['legality_review'])
        profile=yaml.safe_load(files['candidate-domain.yaml'])
        self.assertEqual(profile['parameter_aliases']['effective_tile_elements']['model_parameter'],'num_tile_elements')
        with self.assertRaises(RequestError):validate_space(self.candidate,profile)

    def test_payload_bytes_are_not_area_estimates(self):
        _,plan=self.adapt()
        point=next(p for p in plan['candidates'] if p['identity']['proposed_model_parameters']['num_tile_elements']==16384)
        self.assertEqual(point['derived_storage']['scratchpad_payload_bytes'],2*1024*1024)
        self.assertEqual(point['derived_storage']['size_mmio_bytes'],64)
        self.assertIsNone(point['metrics']['area_mm2'])

    def test_budget_is_explicit_prefix_and_ids_are_stable(self):
        _,all_points=self.adapt();_,limited=self.adapt(budget=2)
        self.assertTrue(limited['truncated']);self.assertEqual(limited['candidate_count'],2)
        self.assertEqual([p['sha256'] for p in limited['candidates']],[p['sha256'] for p in all_points['candidates'][:2]])
        self.assertEqual(len({p['sha256'] for p in all_points['candidates']}),6)
        for bad in (0,-1,True,7):
            with self.assertRaises(RequestError):self.adapt(budget=bad)

    def test_wrong_design_revision_alias_or_source_hash_rejected(self):
        for field in ('design','revision','alias','source'):
            c=deepcopy(self.candidate)
            if field=='design':c['catalog_design_id']='maple-isca2022'
            if field=='revision':c['catalog_design_revision']='another'
            if field=='alias':c['parameter_contract'][0]['value']=99
            if field=='source':c['source_evidence']['sources']['dx100-bfs']['sha256']='0'*64
            with self.assertRaises(RequestError):self.adapt(candidate=c)

    def test_manifest_hash_mismatch_and_domain_promotion_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for name in ('contract.yaml','verification.json','published-dx100-calibration.json'):
                (root/name).write_bytes((self.folder/name).read_bytes())
            c=yaml.safe_load((root/'contract.yaml').read_text())
            c['parameters'][1]['legal_domain']={'min':1,'max':65535}
            (root/'contract.yaml').write_text(yaml.safe_dump(c))
            with self.assertRaisesRegex(RequestError,'differs'):self.adapt(folder=root)
            v=json.loads((root/'verification.json').read_text())
            v['contract_sha256']=sha256((root/'contract.yaml').read_bytes()).hexdigest()
            (root/'verification.json').write_text(json.dumps(v))
            with self.assertRaisesRegex(RequestError,'upgrade'):self.adapt(folder=root)

    def test_artifact_hashes_and_reproducibility(self):
        files,plan=self.adapt();again,p2=self.adapt()
        self.assertEqual((files,plan),(again,p2))
        m=json.loads(files['manifest.json'])
        for name,h in m['artifact_sha256'].items():self.assertEqual(sha256(files[name].encode()).hexdigest(),h)
        self.assertEqual(files['contract.snapshot.yaml'],(self.folder/'contract.yaml').read_text())

    def test_cli_integration_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);candidate=root/'candidate.yaml';candidate.write_text(yaml.safe_dump(self.candidate))
            args=['dx100-candidates','--candidate',str(candidate),'--input-sha256',self.input_hash,
                  '--catalog-sha256',self.catalog_hash,'--output-dir',str(root/'output')]
            self.assertEqual(main(args),0)
            plan=yaml.safe_load((root/'output/exploration.yaml').read_text())
            self.assertEqual(plan['candidate_count'],6)
            self.assertEqual(main(args),2)


if __name__=='__main__':unittest.main()
