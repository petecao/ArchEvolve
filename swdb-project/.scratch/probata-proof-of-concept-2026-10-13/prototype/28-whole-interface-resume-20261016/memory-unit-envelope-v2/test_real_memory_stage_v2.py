"""2026-10-16 ET. Exact 36-payload/18-inner-control staging without execution."""
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent
ENV=runpy.run_path(str(HERE/'test_envelope_v2.py'),run_name='pure_memory_envelope_stage_controls')
def sha(raw):return hashlib.sha256(raw).hexdigest()
class Controls(unittest.TestCase):
    def test_real_stage_layout_and_all18_observer_controls(self):
        ns=ENV['namespace']();command=json.loads((HERE/'command-v2.json').read_bytes());policy=json.loads((HERE/'envelope-policy-v2.json').read_bytes())
        observer=runpy.run_path(str(WHOLE/'memory-normalized-ingress-v3/observer/observe_memory_entry_v1.py'),run_name='memory_observer_control_functions_only')
        with tempfile.TemporaryDirectory() as directory:
            raw=Path(directory).resolve()/ns['RAW_NAME'];(raw/'control').mkdir(parents=True)
            selected=json.loads(json.dumps(policy).replace(command['raw'],str(raw)))
            for name,row in command['stage_sources'].items():
                target=raw/'control'/name;target.write_bytes(Path(row['path']).read_bytes());selected['controls'][name]=ns['pin'](target)
            observed=json.loads(json.dumps(json.loads((HERE/'observation-policy-v1.json').read_bytes())).replace(command['raw'],str(raw)))
            for name in observed['controls']:observed['controls'][name]={**selected['controls'][name],'path':str(raw/'observer/control'/name)}
            target=raw/'control/observation-policy-v1.json';target.write_text(json.dumps(observed,sort_keys=True,separators=(',',':')))
            selected['controls'][target.name]=ns['pin'](target);selected['observer_policy']={**ns['pin'](target),'path':str(raw/'observer/control'/target.name)}
            ns['stage_layout'](raw,selected)
            values,modules=observer['controls'](observed,raw/'observer/control')
            self.assertEqual((len(values),len(modules)),(18,15))
            source=raw/'library_fixture/proof_units/same_thread_memory_v1.cpp'
            self.assertEqual((source.stat().st_size,sha(source.read_bytes())),(3258,'55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'))
            self.assertIsNone(observed['capture']['prepared'])
            for name in ('compiler_unit_adapter_v3.py','compiler_unit_adapter_v4.py'):
                file=raw/'observer/control'/name;file.write_bytes(values[name]+b'\n')
                with self.assertRaises(ValueError):observer['controls'](observed,raw/'observer/control')
                file.write_bytes(values[name])
    def test_all_physical_payloads_and_total_census_exact(self):
        command=json.loads((HERE/'command-v2.json').read_bytes());policy=json.loads((HERE/'envelope-policy-v2.json').read_bytes())
        self.assertEqual(len(command['stage_sources']),36);self.assertEqual(set(command['stage_sources']),set(policy['controls']))
        for name,row in command['stage_sources'].items():
            raw=Path(row['path']).read_bytes();self.assertEqual((len(raw),sha(raw)),(row['bytes'],row['sha256']))
            self.assertEqual((row['bytes'],row['sha256']),(policy['controls'][name]['bytes'],policy['controls'][name]['sha256']))
        self.assertEqual(command['root_controls_bytes_including_policy'],sum(row['bytes'] for row in policy['controls'].values())+(HERE/'envelope-policy-v2.json').stat().st_size)
        self.assertFalse(command['root_metadata_complete']);self.assertIsNone(policy['node']);self.assertIsNone(policy['guard_files'])
        self.assertEqual(policy['budgets'],{'whole_seconds':1200,'entry_seconds':1180,'rss_bytes':4294967296,'total_bytes':268435456,'file_bytes':4194304,'control_bytes':1048576})
if __name__=='__main__':unittest.main(verbosity=2)
