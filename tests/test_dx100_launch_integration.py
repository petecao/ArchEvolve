"""Synthetic collector evidence only: no simulator or benchmark execution."""
from copy import deepcopy
import shlex
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import yaml

from archevolve.dx100_launch_contract import (ARTIFACTS, HANDOFF, COUNTERS, BEGIN, END,
    manifest, system_args, check_roi_evidence, check_launch_evidence)
from archevolve.dx100_validation import ROOT, SOURCE, collect, preflight, file_hash
from archevolve.dx100_validation_cli import main
from archevolve.evolution_store import digest


class LaunchIntegrationTests(unittest.TestCase):
    def setUp(self):
        folder = ROOT/'examples/dx100-reference-validation'
        self.plan, self.env, self.receipt = [yaml.safe_load((folder/name).read_text()) for name in
            ('workflow.yaml', 'environment.template.yaml', 'receipt.template.yaml')]
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.loaded, self.evidence = {}, {}

    def put(self, key, text, filename=None):
        path = self.root/(filename or key)
        path.write_text(text)
        self.loaded[key] = text
        self.evidence[key] = {'path': str(path), 'sha256': file_hash(path), 'bytes': path.stat().st_size}
        self.receipt['artifacts'][key] = {'path': str(path), 'sha256': file_hash(path)}

    def fixture(self, baseline=True):
        self.env['source_root'] = str(self.root/'source')
        self.env['target']['verify_max_ticks'] = 100
        variant = 'baseline' if baseline else 'dx100'
        self.receipt.update(mode='gem5', variant=variant, workload_id='kronecker18-root0', completion='completed', exit_code=0,
            stats_block_index=0, checkpoint_directory=str(self.root/'checkpoint'), guest_environment=self.plan['guest_environment'])
        raw = BEGIN+'\nsimTicks 10\n'+('' if baseline else '\n'.join(n+' 5' for n in COUNTERS)+'\n')+END+'\n'
        projection = raw if not baseline else raw.replace(END, ''.join(n+' 0 # explicit registered zero; stock text output suppresses zero\n' for n in COUNTERS)+END)
        self.put('raw_roi_stats', raw, 'roi.stats.txt')
        self.put('stats', projection, 'roi.stats.explicit-counters.txt')
        self.put('final_stats', raw+raw, 'stats.txt')
        self.put('counter_snapshot', json.dumps({'snapshot_tick':10, 'instruction_counters':dict.fromkeys(COUNTERS, 0 if baseline else 5),
            'raw_roi_sha256':self.evidence['raw_roi_stats']['sha256'], 'projected_roi_sha256':self.evidence['stats']['sha256']}), 'roi-counter-values.json')
        for key, (name, _) in ARTIFACTS.items():
            self.put(key, (ROOT/HANDOFF/name).read_text(), name)
            self.env['target'][key] = self.evidence[key]['path']
        self.put('exit_events', json.dumps({'guest_completed':True, 'events':[
            {'role':'roi_exit', 'cause':'m5_exit instruction encountered', 'code':0, 'tick':10},
            {'role':'post_roi_guest_exit', 'cause':'exiting with last active thread context', 'code':0, 'tick':20}],
            'wrapper_sha256':ARTIFACTS['wrapper'][1], 'stats_block_index':0, 'roi_stats':'roi.stats.explicit-counters.txt',
            'raw_roi_stats':'roi.stats.txt', 'counter_snapshot':'roi-counter-values.json'}), 'exit-events.json')
        for key in ('simulator', 'binary', 'graph', 'ramulator_library'):
            self.put(key, 'SYNTHETIC TEST ONLY '+key)
        self.put('guest_env_file', ''.join(k+'='+v+'\n' for k,v in self.plan['guest_environment'].items()))
        self.env['target']['guest_env_file'] = self.evidence['guest_env_file']['path']
        self.env['tools']['gem5'] = self.evidence['simulator']['path']
        args = [self.evidence['simulator']['path'], '--outdir='+str(self.root), self.evidence['wrapper']['path'],
            '--dx100-source-root', self.env['source_root'], '--verify-max-ticks', '100', '--',
            *system_args(self.evidence['ramulator_config']['path'], self.evidence['guest_env_file']['path'], self.receipt['checkpoint_directory']),
            '--cmd', self.evidence['binary']['path'], '--options', '-f '+self.evidence['graph']['path']+' -r 0 -n 1 -v -l -a', '--prog-interval=1000']
        self.put('command_json', json.dumps(args), 'command.json')
        self.receipt['command_argv'] = args
        self.receipt['benchmark_argv'] = [self.evidence['binary']['path'], '-f', self.evidence['graph']['path'], '-r', '0', '-n', '1', '-v', '-l', '-a']
        self.put('stdout', 'ROI started: 1 threads\nStarting '+('TDStep' if baseline else 'TDStepMAA')+': 1 elements\nROI End!!!\nVerification: PASS\n')
        self.put('stderr', '')
        self.put('config_ini', '[system.maa]\n'+'\n'.join(f'{k}={v}' for k,v in self.plan['expected_effective_model_parameters'].items()))
        macros = '\n'.join(f'#define {k} {v}' for k,v in self.plan['compile_constants'].items())+'\n#define GEM5 1\n'
        self.put('macro_dump', macros+('' if baseline else '#define MAA 1\n'))
        self.put('build_receipt', json.dumps({'workflow_sha256':digest(self.plan), 'source_commit':SOURCE, 'source_files':self.plan['source_files'],
            'binary_sha256':self.evidence['binary']['sha256'], 'macro_dump_sha256':self.evidence['macro_dump']['sha256'],
            'argv':['synthetic'], 'compiler_version':'synthetic', 'exit_code':0}))
        self.put('graph_receipt', json.dumps({'source_commit':SOURCE, 'workload_id':'kronecker18-root0', 'graph_sha256':self.evidence['graph']['sha256'],
            'generator_seed':27491095, 'generator_options':['-g', '18', '-k', '16', '-b', self.evidence['graph']['path']]}))
        self.receipt['environment_sha256'] = digest(self.env)

    def roi(self):
        return check_roi_evidence(self.loaded, self.evidence, self.receipt, self.env['target'])

    def mutate_json(self, key, mutation):
        obj = json.loads(self.loaded[key]);mutation(obj)
        self.put(key, json.dumps(obj), Path(self.evidence[key]['path']).name)

    def test_pinned_handoff_and_unbound_templates(self):
        self.assertEqual(manifest(ROOT), self.plan['launcher_contract'])
        run = yaml.safe_load((ROOT/'examples/dx100-reference-validation/run-plan.yaml').read_text())
        self.assertEqual(len(run['target_cases']), 4)
        self.assertEqual(len({c['checkpoint_directory'] for c in run['target_cases']}), 4)
        self.assertTrue(all(c['restore_environment']['VERIFY_MAX_TICKS'] is None for c in run['target_cases']))
        self.assertFalse(run['execute'])
        check = preflight(self.plan, self.env)
        self.assertEqual(check['status'], 'blocked_unbound_environment')
        self.assertIn('target.verify_max_ticks', check['missing'])
        self.assertFalse(check['ready_to_execute'])

    def test_complete_baseline_and_accelerated_synthetic_evidence(self):
        for baseline in (True, False):
            self.fixture(baseline)
            self.assertEqual(self.roi(), ([], []))
            result = collect(self.plan, self.env, self.receipt, self.root)
            self.assertEqual([e for e in result['provenance_errors'] if not e.startswith('preflight:')], [])
            self.assertEqual(result['log_checks']['missing'], [])
            self.assertFalse(result['target_validated'])
            self.assertIsNone(result['speedup'])

    def test_all_collector_checks_pass_with_mocked_site_preflight_only(self):
        self.fixture()
        with patch('archevolve.dx100_validation.preflight', return_value={'failures':[], 'missing':[], 'status':'synthetic_site_only'}):
            result=collect(self.plan,self.env,self.receipt,self.root)
        self.assertEqual(result['status'],'evidence_consistent_pending_review')
        self.assertFalse(result['target_validated'])
        self.assertIsNone(result['parameter_admission'])

    def test_command_contract_matches_pinned_shell_array(self):
        script=(ROOT/HANDOFF/'launch_16k.sh').read_text()
        restore=script.split('command=(',2)[2].split(')\nfi',1)[0]
        args=shlex.split(restore)
        stock=args[args.index('--')+1:]
        expected=[*system_args('$here/ramulator.yaml','$guest_env','$checkpoint'),
            '--cmd','$bfs','--options','$options','--prog-interval=1000']
        self.assertEqual(stock,expected)

    def test_modified_projection_and_rehashed_sidecar_rejected(self):
        self.fixture()
        self.put('stats', self.loaded['stats'].replace('simTicks 10','simTicks 11'), 'roi.stats.explicit-counters.txt')
        self.mutate_json('counter_snapshot', lambda x:x.update(projected_roi_sha256=self.evidence['stats']['sha256']))
        self.assertIn('roi_projection_not_zero_only', self.roi()[0])

    def test_missing_positive_invalid_or_mismatched_counter_rejected(self):
        for value in (1, None, True, -1, float('nan'), .5):
            self.fixture()
            self.mutate_json('counter_snapshot', lambda x:x['instruction_counters'].update({COUNTERS[0]:value}))
            self.assertIn('invalid_roi_derivation', self.roi()[0])
        self.fixture(False)
        self.mutate_json('counter_snapshot', lambda x:x['instruction_counters'].update({COUNTERS[0]:6}))
        self.assertIn('invalid_roi_derivation', self.roi()[0])

    def test_wrong_window_path_or_wrapper_rejected(self):
        for field,value in [('roi_stats','stats.txt'), ('wrapper_sha256','wrong'), ('stats_block_index',1)]:
            self.fixture()
            self.mutate_json('exit_events', lambda x:x.update({field:value}))
            self.assertTrue(self.roi()[0])
        self.fixture();self.receipt['stats_block_index']=1
        self.assertIn('frozen_roi_block_must_be_zero', self.roi()[0])

    def test_event_chain_ticks_and_budget_checked(self):
        for key,value in [('cause','m5_exit instruction encountered'), ('code',1), ('tick',9), ('tick',111)]:
            self.fixture()
            self.mutate_json('exit_events', lambda x:x['events'][1].update({key:value}))
            self.assertTrue(self.roi()[0])
        self.fixture()
        self.mutate_json('exit_events', lambda x:x.update(guest_completed=False, events=x['events'][:1]))
        self.assertEqual(self.roi(), ([], ['verifier_continuation_incomplete']))

    def test_actual_command_must_match_reviewed_settings_and_receipt(self):
        self.fixture()
        self.assertEqual(check_launch_evidence(self.loaded,self.evidence,self.receipt,self.env), ([], []))
        args = list(self.receipt['command_argv']);args[args.index('--l3_size=8MB')]='--l3_size=16MB'
        self.receipt['command_argv']=args;self.put('command_json',json.dumps(args),'command.json')
        self.assertIn('recorded_restore_command_mismatch', check_launch_evidence(self.loaded,self.evidence,self.receipt,self.env)[0])

    def test_missing_budget_does_not_hide_detected_artifact_mismatch(self):
        self.fixture()
        self.env['target']['verify_max_ticks']=None
        self.evidence['launcher']['sha256']='changed'
        errors,missing=check_launch_evidence(self.loaded,self.evidence,self.receipt,self.env)
        self.assertIn('launcher_reviewed_artifact_mismatch',errors)
        self.assertIn('launch_source_or_verification_budget_unbound',missing)

    def test_preflight_rejects_changed_artifact_pin_topology_and_invalid_budget(self):
        for key,value in [('wrapper_sha256','wrong'), ('verify_max_ticks',0), ('verify_max_ticks',True), ('cpu_clock','2GHz'), ('dram_topology',{'channels':2,'ranks':1,'bankgroups':4,'banks':8})]:
            env=deepcopy(self.env);env['target'][key]=value
            self.assertEqual(preflight(self.plan,env)['status'],'rejected')

    def test_collector_requires_and_archives_all_roi_companions(self):
        self.fixture()
        self.receipt['artifacts']['counter_snapshot']=None
        result=collect(self.plan,self.env,self.receipt,self.root)
        self.assertIn('artifact:counter_snapshot',result['missing'])
        self.fixture()
        for name,value in [('workflow',self.plan),('environment',self.env),('receipt',self.receipt)]:
            (self.root/(name+'.yaml')).write_text(yaml.safe_dump(value))
        args=['collect','--workflow',str(self.root/'workflow.yaml'),'--environment',str(self.root/'environment.yaml'),
            '--receipt',str(self.root/'receipt.yaml'),'--output-dir',str(self.root/'collected')]
        self.assertEqual(main(args),0)
        for key in ('raw_roi_stats','stats','counter_snapshot','exit_events','command_json','wrapper','final_stats'):
            self.assertEqual((self.root/'collected/evidence'/key).read_bytes(),Path(self.evidence[key]['path']).read_bytes())
        result=yaml.safe_load((self.root/'collected/result.yaml').read_text())
        self.assertFalse(result['target_validated'])


if __name__ == '__main__':
    unittest.main()
