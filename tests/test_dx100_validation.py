from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest
import yaml
from unittest.mock import patch

from archevolve.__main__ import ROOT
from archevolve.dx100_validation import (prepare,preflight,geometry,check_config,stats_blocks,analyze_logs,
                                         check_macros,collect,compare_collections,file_hash,SOURCE)
from archevolve.dx100_validation_cli import main
from archevolve.evolution_store import digest
from tools.render_mermaid import RequestError


class DX100ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=ROOT/'examples/dx100-reference-validation'
        cls.plan,cls.env,cls.build,cls.run_plan,cls.receipt=[yaml.safe_load((folder/n).read_text()) for n in
            ('workflow.yaml','environment.template.yaml','build-recipes.yaml','run-plan.yaml','receipt.template.yaml')]

    def logs(self,variant='dx100',passed=True):
        prefix='TDStepMAA' if variant=='dx100' else 'TDStep'
        return 'ROI started: 1 threads\nStarting '+prefix+': 1 elements\nStarting '+prefix+': 10000 elements\nROI End!!!\nVerification: '+('PASS' if passed else 'FAIL')+'\n'

    def stats(self,read=2,ranges=1):
        return '---------- Begin Simulation Statistics ----------\nsystem.maa.numInst_INDRD '+str(read)+'\nsystem.maa.numInst_RANGE '+str(ranges)+'\nsimTicks 1000\n---------- End Simulation Statistics ----------\n'

    def analyze(self,stdout=None,variant='dx100',stats=None,**kw):
        args=dict(stdout=self.logs(variant) if stdout is None else stdout,stderr='',mode='gem5',variant=variant,
                  completion='completed',exit_code=0,stats=self.stats() if stats is None else stats,block_index=0,counters=self.plan['required_target_counters'])
        args.update(kw)
        return analyze_logs(**args)

    def macros(self,mode='gem5',variant='dx100'):
        values={k:v for k,v in self.plan['compile_constants'].items() if mode=='gem5' or k!='MEM_SIZE'}
        lines=[f'#define {k} {v}' for k,v in values.items()]+['#define '+('GEM5' if mode=='gem5' else 'FUNC')+' 1']
        if variant=='dx100':lines.append('#define MAA 1')
        return '\n'.join(lines)+'\n'

    def test_preparation_is_unbound_and_source_pinned(self):
        self.assertEqual(self.plan['source_commit'],SOURCE)
        self.assertEqual(self.plan['tile_elements'],16384)
        self.assertGreater(len(self.plan['source_files']),30)
        self.assertFalse(self.plan['execution_performed'])
        self.assertIsNone(self.run_plan['target_argv'])
        self.assertTrue(all(v is None for v in self.env['great_lakes'].values()))
        out=preflight(self.plan,self.env)
        self.assertEqual(out['status'],'blocked_unbound_environment')
        self.assertFalse(out['ready_to_execute'])
        self.assertIn('target.verifier_continuation_review',out['missing'])
        self.assertIn('tools.gem5',out['missing'])

    def test_effective_launcher_overrides_are_separate_from_defaults(self):
        for key in ('max_outstanding_cache_side_packets','max_outstanding_cpu_side_packets'):
            self.assertEqual(self.plan['declared_model_defaults'][key],512)
            self.assertEqual(self.plan['expected_effective_model_parameters'][key],32768)
        self.assertIn('m5_exit',self.plan['verifier_exit_issue'])
        self.assertIn('allocates',self.plan['baseline_issue'])

    def test_build_variants_and_graph_runs_are_explicit(self):
        recipes={r['id']:r for r in self.build['recipes']}
        self.assertIn('-DFUNC',recipes['functional-dx100']['argv'])
        self.assertIn('-DMAA',recipes['functional-dx100']['argv'])
        self.assertNotIn('-DMAA',recipes['functional-baseline']['argv'])
        self.assertIn('-DGEM5',recipes['gem5-baseline']['argv'])
        self.assertIn('-DTILE_SIZE=16384',recipes['gem5-dx100']['argv'])
        self.assertIn('{build}/m5op.o',recipes['gem5-dx100']['argv'])
        self.assertFalse(self.build['execute']);self.assertFalse(self.run_plan['execute'])
        self.assertTrue(self.run_plan['required_target_settings']['maa_enabled_for_both_variants'])
        for w in self.plan['workloads']:
            self.assertEqual(w['benchmark_options'],['-f','{graph}','-r','0','-n','1','-v','-l','-a'])

    def test_topology_slice_family_and_invalid_initial_geometry(self):
        self.assertEqual(geometry(None)['status'],'unresolved')
        result=geometry({'channels':2,'ranks':1,'bankgroups':4,'banks':4})
        self.assertEqual(result['slice_family'],[4,8,16,32])
        self.assertEqual(result['status'],'necessary_geometry_pass')
        for values in ({'channels':2,'ranks':1,'bankgroups':1,'banks':4},
                       {'channels':2,'ranks':1,'bankgroups':3,'banks':4},
                       {'channels':4,'ranks':1,'bankgroups':4,'banks':4},
                       {'channels':True,'ranks':1,'bankgroups':4,'banks':4}):
            self.assertEqual(geometry(values)['status'],'rejected')

    def test_guest_environment_must_be_explicit_and_bound(self):
        from archevolve.dx100_validation import guest_env_text
        with tempfile.TemporaryDirectory() as temp:
            guest=Path(temp)/'guest.env';guest.write_text(guest_env_text(self.plan))
            env=deepcopy(self.env);env['target']['guest_env_file']=str(guest)
            env['target']['system_argv']=['--env',str(guest)]
            self.assertNotIn('guest_environment_file_mismatch',preflight(self.plan,env)['failures'])
            env['target']['system_argv']=[]
            self.assertIn('explicit_guest_env_option_required',preflight(self.plan,env)['failures'])
            guest.write_text('OMP_NUM_THREADS=8\n')
            self.assertIn('guest_environment_file_mismatch',preflight(self.plan,env)['failures'])
        env=deepcopy(self.env);env['target']={}
        self.assertIn('target.dram_topology',preflight(self.plan,env)['missing'])

    def test_incomplete_run_is_not_refuted_for_absent_activity(self):
        out=self.analyze(completion='timeout',exit_code=124,stats=self.stats(0,0))
        self.assertEqual(out['status'],'inconclusive')
        self.assertEqual(out['intended_path_observation'],'unresolved')

    def test_effective_config_not_reference_defaults_is_checked(self):
        params=self.plan['expected_effective_model_parameters']
        text='[system.maa]\n'+'\n'.join(f'{k}={v}' for k,v in params.items())
        self.assertEqual(check_config(text,params)['status'],'reference_parameters_observed')
        wrong=text.replace('max_outstanding_cache_side_packets=32768','max_outstanding_cache_side_packets=512')
        self.assertEqual(check_config(wrong,params)['status'],'rejected')
        missing='\n'.join(l for l in text.splitlines() if not l.startswith('num_regs_per_core='))
        self.assertEqual(check_config(missing,params)['status'],'unresolved')
        self.assertEqual(check_config(text+'\n[other.maa]\nnum_tile_elements=16384\nnum_maas=1',params)['status'],'unresolved')

    def test_verifier_failure_overrides_zero_exit_and_pass_line(self):
        self.assertEqual(self.analyze(stdout=self.logs(passed=False))['status'],'refuted')
        self.assertEqual(self.analyze(stdout=self.logs()+'Verification: FAIL\n')['status'],'refuted')
        self.assertEqual(self.analyze(stderr='panic: bad state')['status'],'refuted')
        self.assertEqual(self.analyze(exit_code=1)['status'],'refuted')

    def test_roi_exit_before_verifier_remains_inconclusive(self):
        out=self.analyze(stdout=self.logs().replace('Verification: PASS\n',''))
        self.assertEqual(out['status'],'inconclusive')
        self.assertIn('exactly_one_BFSVerifier_PASS_required',out['missing'])
        self.assertFalse(out['target_timing_validated'])

    def test_markers_alone_do_not_prove_accelerator_execution(self):
        out=self.analyze(stats=self.stats(0,0))
        self.assertEqual(out['intended_path_observation'],'refuted')
        self.assertEqual(out['status'],'refuted')
        missing=self.analyze(stats=self.stats().replace('system.maa.numInst_INDRD 2\n',''))
        self.assertEqual(missing['status'],'inconclusive')
        control=self.analyze(variant='baseline',stats=self.stats(0,0))
        self.assertEqual(control['intended_path_observation'],'idle_accelerator_observed')
        self.assertEqual(self.analyze(variant='baseline')['status'],'refuted')

    def test_explicit_roi_selection_and_truncated_stats(self):
        self.assertEqual(len(stats_blocks(self.stats()+self.stats(0,0))),2)
        self.assertEqual(self.analyze(stats=self.stats()+self.stats(0,0),block_index=0)['intended_path_observation'],'required_activity_observed')
        self.assertEqual(self.analyze(stats=self.stats()+self.stats(0,0),block_index=1)['status'],'refuted')
        self.assertEqual(self.analyze(block_index=None)['status'],'inconclusive')
        with self.assertRaises(RequestError):stats_blocks(self.stats().replace('---------- End Simulation Statistics ----------',''))
        with self.assertRaises(RequestError):stats_blocks(self.stats().replace('simTicks 1000','system.maa.numInst_RANGE 9'))

    def test_macro_dump_checks_mode_tile_size_and_maa_flag(self):
        for mode in ('functional','gem5'):
            for variant in ('baseline','dx100'):
                self.assertEqual(check_macros(self.macros(mode,variant),self.plan,mode,variant)['status'],'expected_definitions_observed')
        self.assertEqual(check_macros(self.macros().replace('TILE_SIZE 16384','TILE_SIZE 8192'),self.plan,'gem5','dx100')['status'],'rejected')
        self.assertEqual(check_macros(self.macros(),self.plan,'gem5','baseline')['status'],'rejected')

    def test_functional_pass_never_becomes_target_timing_evidence(self):
        result=self.analyze(mode='functional',stats=None)
        self.assertEqual(result['intended_path_observation'],'not_applicable_functional_model')
        self.assertFalse(result['target_timing_validated']);self.assertIsNone(result['latency_ms'])

    def test_empty_receipt_is_inconclusive_and_stale_bindings_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            result=collect(self.plan,self.env,self.receipt,Path(temp))
            self.assertEqual(result['status'],'inconclusive')
            self.assertFalse(result['target_validated'])
            r=deepcopy(self.receipt);r['workflow_sha256']=digest('different')
            with self.assertRaises(RequestError):collect(self.plan,self.env,r,Path(temp))

    def make_functional_receipt(self,root):
        receipt=deepcopy(self.receipt)
        receipt.update(environment_sha256=digest(self.env),mode='functional',variant='dx100',completion='completed',exit_code=0,
                       workload_id='kronecker18-root0',guest_environment=self.plan['guest_environment'],command_argv=['recorded-fixture-only'])
        def put(name,content):
            path=root/name;path.write_text(content)
            receipt['artifacts'][name]={'path':name,'sha256':file_hash(path)}
        put('stdout',self.logs());put('stderr','');put('binary','synthetic binary');put('graph','synthetic graph')
        put('macro_dump',self.macros('functional','dx100'))
        put('build_receipt',json.dumps({'workflow_sha256':digest(self.plan),'source_commit':SOURCE,'source_files':self.plan['source_files'],
            'binary_sha256':receipt['artifacts']['binary']['sha256'],'macro_dump_sha256':receipt['artifacts']['macro_dump']['sha256'],
            'argv':['fixture'],'compiler_version':'synthetic','exit_code':0}))
        put('graph_receipt',json.dumps({'source_commit':SOURCE,'workload_id':'kronecker18-root0','graph_sha256':receipt['artifacts']['graph']['sha256'],
            'generator_seed':27491095,'generator_options':['-g','18','-k','16','-b','graph']}))
        receipt['benchmark_argv']=['binary','-f','graph','-r','0','-n','1','-v','-l','-a']
        return receipt

    def test_collector_hashes_raw_files_without_promoting_even_fixture_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);receipt=self.make_functional_receipt(root)
            result=collect(self.plan,self.env,receipt,root)
            self.assertFalse(result['provenance_errors'])
            self.assertEqual(result['log_checks']['verifier_tokens'],['PASS'])
            self.assertEqual(result['status'],'inconclusive')  # environment is still unbound
            (root/'stdout').write_text('Verification: PASS\nchanged')
            changed=collect(self.plan,self.env,receipt,root)
            self.assertEqual(changed['status'],'rejected_receipt')
            self.assertIn('artifact_hash:stdout',changed['provenance_errors'])

    def test_cli_collect_archives_raw_output_without_claiming_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);receipt=self.make_functional_receipt(root)
            (root/'receipt.yaml').write_text(yaml.safe_dump(receipt))
            fixture=ROOT/'examples/dx100-reference-validation'
            self.assertEqual(main(['collect','--workflow',str(fixture/'workflow.yaml'),'--environment',str(fixture/'environment.template.yaml'),
                                  '--receipt',str(root/'receipt.yaml'),'--output-dir',str(root/'collected')]),0)
            self.assertEqual((root/'collected/evidence/stdout').read_bytes(),(root/'stdout').read_bytes())
            report=yaml.safe_load((root/'collected/result.yaml').read_text())
            self.assertEqual(report['status'],'inconclusive')
            self.assertFalse(report['target_validated'])

    def test_compare_requires_same_graph_environment_and_mode(self):
        common={'workflow_sha256':'w','environment_sha256':'e','workload_id':'x','mode':'functional','artifacts':{'graph':{'sha256':'g'}},
                'log_checks':{'frontier_sizes':[1,5]},'status':'inconclusive'}
        b={**common,'variant':'baseline'};a={**deepcopy(common),'variant':'dx100'}
        self.assertEqual(compare_collections(b,a)['status'],'frontiers_match_other_checks_inconclusive')
        a['artifacts']['graph']['sha256']='other'
        self.assertEqual(compare_collections(b,a)['status'],'not_comparable')
        a={**deepcopy(common),'variant':'dx100'};a['log_checks']['frontier_sizes']=[1,4]
        self.assertEqual(compare_collections(b,a)['status'],'frontier_mismatch')
        a={**deepcopy(common),'variant':'dx100','status':'refuted_checks'}
        self.assertEqual(compare_collections(b,a)['status'],'refuted_checks')

    @unittest.skipUnless((ROOT/'sources/DX100/.git').exists(),'Pinned DX100 checkout required for source-audit integration test')
    def test_cli_prepares_and_will_not_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'prepared'
            args=['prepare','--source-root',str(ROOT/'sources/DX100'),'--output-dir',str(out)]
            self.assertEqual(main(args),0)
            self.assertEqual(yaml.safe_load((out/'workflow.yaml').read_text()),self.plan)
            self.assertTrue((out/'build-receipt.template.json').exists())
            self.assertTrue((out/'graph-receipt.template.json').exists())
            self.assertEqual(main(args),2)


if __name__=='__main__':unittest.main()
