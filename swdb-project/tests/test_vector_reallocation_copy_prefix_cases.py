"""2026-10-16 ET. Pure source-equivalent prefix cases; no verifier or proof claim."""
import hashlib,json
from pathlib import Path
from swdb import vector_reallocation_vcs as packets
BASELINE=Path(__file__).parent/'fixtures/proof/vector-reallocation-copy-prefix-3a48.json'
PREFIX='grow.copy.step.advanced_copied_prefix'

def refused(action):
 try:action()
 except ValueError:return
 raise AssertionError('altered prefix preparation accepted')

def test_public_prefix_requires_exact_ten_reviewed_full_A_cases_and_other_fifty_one_inputs(tmp_path):
 baseline=json.loads(BASELINE.read_bytes());stage=tmp_path/'grow';plan=packets.prepare('std_vector_int_realloc_v3_grow',stage)
 assert len(plan['obligations'])==61
 parent=next(g for g in plan['logical_obligations']if g['id']=='grow.copy.step');group=parent['component_expansions'][0]
 assert group['id']==PREFIX and group['original_statement']==baseline['original_prefix']['statement']
 assert group['outer_antecedent']==baseline['full_A']and group['range']=='0 <= j < (k+1)'
 assert group['case_partition']==[{'id':'prior','guard':'j < k'},{'id':'written','guard':'j == k'}]
 assert group['fresh_index']=='j'and group['fresh_index_free_in_antecedent']is False
 assert group['dependencies']==[]and group['premises_added']==[]
 expected=baseline['expected_parts'];assert group['parts']==[r['id']for r in expected]
 rows={r['id']:r for r in plan['obligations']}
 for old in expected:
  row=rows[old['id']];assert row['statement']==old['statement']and row['dependencies']==[]and row['expected']=='proven'and row['status']=='pending'
  assert row['path'].startswith('009s14p')
 unchanged=[r for r in baseline['targets']if r['id']!=PREFIX]
 assert len(unchanged)==51 and [{k:r[k]for k in ['id','path','sha256']}for r in plan['obligations']if not r['id'].startswith(PREFIX+'.')]==unchanged
 assert plan['semantics']==baseline['semantics']and plan['sources']==baseline['sources']
 ref=stage/group['reference']['path'];assert hashlib.sha256(ref.read_bytes()).hexdigest()==baseline['original_prefix']['sha256']
 assert group['reference']['path']not in {r['path']for r in plan['obligations']}
 assert len(parent['parts'])==24 and set(group['parts'])<=set(parent['parts'])and PREFIX not in parent['parts']
 for event in plan['source_inventory']['events']:
  if event['id']in {'grow.copy','grow.loop.increment'}:assert set(group['parts'])<=set(event['obligations'])and PREFIX not in event['obligations']
 assert packets.check('std_vector_int_realloc_v3_grow',stage)==plan

def test_prefix_expansion_refuses_any_changed_original_guard_range_heap_or_new_index():
 original=json.loads(BASELINE.read_bytes())['original_prefix']['statement']
 for after in [original.replace(' && k < s',''),original.replace('k < s','k <= s'),original.replace('f,(k+1))','f,k)'),original.replace('bo+4*k','bo+4*(k+1)'),original.replace('Heap::copy_int(h,','Heap::copy_int(entry,')]:
  assert after!=original;refused(lambda after=after:packets.copy_prefix_parts(after))

def test_prefix_definitions_and_both_integer_cases_are_source_bound_and_jointly_complete():
 baseline=json.loads(BASELINE.read_bytes());parts,group=packets.copy_prefix_parts(baseline['original_prefix']['statement'])
 assert len(parts)==10 and group['parts']==[r['id']for r in baseline['expected_parts']]
 for source in group['definition_sources']:
  raw=(packets.HERE/source['path']).read_bytes();assert hashlib.sha256(raw[source['begin']:source['end']]).hexdigest()==source['sha256']
 assert {r['sha256']for r in group['definition_sources']}=={r['sha256']for r in baseline['definitions']if 'predicate copied_prefix 'in r['text']or 'predicate int32_at 'in r['text']}
 # Finite sanity of the separately reviewed unbounded integer partition, not a theorem certificate.
 for k in range(-3,5):
  for j in range(-3,6):
   domain=0<=j<k+1;prior=j<k;written=j==k
   assert not domain or prior!=written
   for mask in range(32):
    conclusions=[bool(mask&(1<<i))for i in range(5)]
    for A in [False,True]:assert (not(A and domain)or all(conclusions))==all(not(A and domain and branch)or value for branch in [prior,written]for value in conclusions)

def test_prefix_canonical_check_refuses_coherently_dropped_or_altered_case_and_definition(tmp_path):
 for attack in ['drop','same_case','range','omit_A','old_count','value','capture','definition','reference','dependency']:
  stage=tmp_path/attack;plan=packets.prepare('std_vector_int_realloc_v3_grow',stage);parent=next(g for g in plan['logical_obligations']if g['id']=='grow.copy.step');group=parent['component_expansions'][0];row=next(r for r in plan['obligations']if r['id']==group['parts'][-1])
  if attack=='drop':plan['obligations'].remove(row);(stage/row['path']).unlink();group['parts'].remove(row['id']);parent['parts'].remove(row['id'])
  elif attack=='dependency':row['dependencies']=[group['parts'][0]]
  elif attack=='definition':group['definition_sources'][0]['sha256']='0'*64
  elif attack=='reference':
   p=stage/group['reference']['path'];p.write_text('/* forged original prefix */\n');group['reference']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
  else:
   before=row['statement'];after=before.replace('j == k','j < k')if attack=='same_case'else before.replace('j < (k+1)','j <= (k+1)')if attack=='range'else before.replace(baseline_A(plan),'\\true')if attack=='omit_A'else before.replace('(k+1)','k')if attack=='old_count'else before.replace('Heap::load_int(entry,b,bo+4*j)','Heap::load_int(entry,b,bo+4*k)')if attack=='value'else before.replace('integer j;','integer k;')
   assert after!=before;row['statement']=after;p=stage/row['path'];p.write_text(p.read_text().replace(before,after));row['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
  (stage/'manifest.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n');refused(lambda:packets.check('std_vector_int_realloc_v3_grow',stage))

def baseline_A(plan):return next(g for g in plan['logical_obligations']if g['id']=='grow.copy.step')['antecedent']

def test_prefix_definition_mutation_refuses_and_other_member_target_censuses_remain_scoped(tmp_path):
 baseline=json.loads(BASELINE.read_bytes());original=packets.HERE;fake=tmp_path/'changed';fake.mkdir();source=(original/'heap_reallocation.mlw').read_text();(fake/'heap_reallocation.mlw').write_text(source.replace('int32_at now target (4*j) /\\','int32_at now target (4*j) \\/'))
 try:
  packets.HERE=fake;refused(lambda:packets.copy_prefix_parts(baseline['original_prefix']['statement']))
 finally:packets.HERE=original
 for member,count in [('reserve',67),('ctor_count_value',35),('dtor',11)]:
  plan=packets.prepare('std_vector_int_realloc_v3_'+member,tmp_path/member);assert len(plan['obligations'])==count and plan['source_inventory']['unmapped_executable_events']==[]
