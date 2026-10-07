import subprocess,unittest,yaml
from archevolve.hardware_catalog import load_catalog,query_catalog
BASE='b5f8e92a40a506f5e0b75863fc863f0744eff6d2'
class RecentBatch(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog,_=load_catalog();cls.base=yaml.safe_load(subprocess.check_output(['git','show',BASE+':catalog/hardware-v0.1.yaml'],text=True))
 def test_prior_design_operations_sources_and_selection_preserved(self):
  self.assertEqual(self.catalog['designs'][:16],self.base['designs'])
  for name in ('sources','claims'):
   for key,value in self.base[name].items():self.assertEqual(self.catalog[name][key],value)
  self.assertEqual(self.catalog['project_selections'],self.base['project_selections'])
  self.assertEqual((len(self.catalog['designs']),sum(len(d['operations']) for d in self.catalog['designs']),len(self.catalog['claims'])),(20,62,204))
 def test_added_prefetchers_have_only_assistance_role(self):
  for name in ('svr-micro2024','triangel-isca2024'):
   r=query_catalog(self.catalog,operation='read',design_id=name);self.assertTrue(r['matches']);self.assertEqual({m['status'] for m in r['matches']},{'assistance_only'})
 def test_recent_records_do_not_grant_generic_gather_or_RMW(self):
  for design in self.catalog['designs'][16:]:
   for request in [dict(operation='read',subtype='gather'),dict(operation='read_modify_write'),dict(operation='read',execution_role='execute')]:
    self.assertEqual(query_catalog(self.catalog,design_id=design['id'],**request)['matches'],[])
 def test_prefetch_type_storage_is_not_payload_index_ABI(self):
  for name in ('svr-micro2024','triangel-isca2024'):
   r=query_catalog(self.catalog,operation='read',design_id=name,payload_type='float64',index_width_bits=64)
   self.assertTrue(r['matches']);self.assertTrue(all(m['status']=='needs_evidence' for m in r['matches']))
if __name__=='__main__':unittest.main()
