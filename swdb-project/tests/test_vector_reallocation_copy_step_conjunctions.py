"""2026-10-16 ET. Compiler-free copy-step source preparation; no proof verdict."""
import hashlib,json
from pathlib import Path
from swdb import vector_reallocation_vcs as packets

BASELINE=Path(__file__).parent/'fixtures/proof/vector-reallocation-copy-step-37ffe407.json'

def refused(action):
 try:action()
 except ValueError:return
 raise AssertionError('mutated source preparation accepted')

def test_copy_step_keeps_all_fifteen_full_premise_conclusions_and_other_payloads(tmp_path):
 baseline=json.loads(BASELINE.read_bytes());plan=packets.prepare('std_vector_int_realloc_v3_grow',tmp_path/'step')
 assert len(plan['obligations'])==61
 group=next(g for g in plan['logical_obligations']if g['id']=='grow.copy.step')
 assert group['original_statement']==baseline['original_step']['statement']
 assert group['antecedent']=='t25v3_copy_inv(entry,h,r,o,b,bo,s,c,f,cap,k) && k < s'
 assert group['premises_added']==[] and group['dependencies']==[]
 assert len(group['parts'])==len(set(group['parts']))==24 and len(group['original_definition_parts'])==15
 assert group['capture_avoiding'] is True and group['nested_bound_variables']==['j']
 assert group['definition_substitution']['k']=='(k+1)'
 h='Heap::copy_int(h,b,bo+4*k,f,4*k)'
 expected=[
  'Heap::well_formed(entry)','Heap::well_formed('+h+')',
  't25v3_eligible(entry,r,o,b,bo,s,c)','t25v3_eligible('+h+',r,o,b,bo,s,c)',
  '0 <= (k+1) <= s <= c < cap <= 4611686018427387903',
  'f == Heap::fresh_id(entry)','!Heap::issued(entry,f)','f != r','f != b',
  'Heap::typed_writes('+h+',f,0,4*cap,4)','Heap::freeable('+h+',f,0)',
  'Heap::bytes('+h+',f) == 4*cap','t25v3_copy_frame(entry,'+h+',f)',
  'Heap::copied_prefix(entry,'+h+',b,bo,f,(k+1))',
  r'(\forall integer j; (k+1) <= j < cap ==> !Heap::initialized_at('+h+',f,4*j))',
 ]
 assert group['substituted_conjuncts']==expected
 rows={r['id']:r for r in plan['obligations']}
 for ident,conclusion in zip(group['original_definition_parts'],expected,strict=True):
  if ident=='grow.copy.step.advanced_copied_prefix':continue  # Its ten exact cases are checked separately.
  row=rows[ident]
  assert row['statement']==group['quantifiers']+group['antecedent']+' ==> '+conclusion
  assert row['dependencies']==[] and row['expected']=='proven'and row['status']=='pending'
 assert plan['sources']==baseline['sources'] and plan['semantics']==baseline['semantics']
 old={r['id']:(r['path'],r['sha256'])for r in baseline['targets']if r['id']!='grow.copy.step'}
 assert len(old)==37 and {r['id']:(r['path'],r['sha256'])for r in plan['obligations']if r['id']in old}==old
 ref=tmp_path/'step'/group['reference']['path']
 assert hashlib.sha256(ref.read_bytes()).hexdigest()==baseline['original_step']['sha256']
 assert group['reference']['path']not in {r['path']for r in plan['obligations']}
 assert {rows[ident]['path'].split('-')[0]for ident in group['parts']}==({'009s'+str(i).zfill(2)for i in range(1,16)if i!=14}|{'009s14p'+str(i).zfill(2)for i in range(1,11)})
 for event in plan['source_inventory']['events']:
  if event['id']in {'grow.copy','grow.loop.increment'}:
   assert set(group['parts'])<=set(event['obligations']) and 'grow.copy.step'not in event['obligations']
 assert packets.check('std_vector_int_realloc_v3_grow',tmp_path/'step')==plan

def test_copy_step_refuses_changed_original_guard_heap_transition_and_index():
 original=json.loads(BASELINE.read_bytes())['original_step']['statement']
 for changed in [original.replace(' && k < s',''),original.replace('k < s','k <= s'),
                 original.replace('bo+4*k','bo+4*(k+1)'),original.replace('cap,k+1)','cap,k)'),
                 original.replace('Heap::copy_int(h,','Heap::copy_int(entry,')]:
  refused(lambda changed=changed:packets.copy_step_parts(changed))

def test_copy_step_definition_binding_reconstructs_the_exact_fifteen_source_parts():
 original=json.loads(BASELINE.read_bytes())['original_step']['statement'];parts,group=packets.copy_step_parts(original)
 source=group['definition_source'];raw=(packets.HERE/source['path']).read_bytes();definition=raw[source['begin']:source['end']]
 assert hashlib.sha256(definition).hexdigest()==source['sha256']
 body=definition.decode().split('=',1)[1].strip().removesuffix(';')
 assert ''.join('&&'.join(group['definition_conjuncts']).split())==''.join(body.split())
 assert len(parts)==15 and group['definition_substitution']['h']=='Heap::copy_int(h,b,bo+4*k,f,4*k)'
 assert group['definition_substitution']['entry']=='entry'and group['definition_substitution']['k']=='(k+1)'

def test_copy_step_reference_and_every_leaf_remain_required_after_coherent_tampering(tmp_path):
 for attack in ['drop','sibling','guard','increment','reference','capture','source_definition']:
  stage=tmp_path/attack;plan=packets.prepare('std_vector_int_realloc_v3_grow',stage)
  group=next(g for g in plan['logical_obligations']if g['id']=='grow.copy.step');row=next(r for r in plan['obligations']if r['id']==group['parts'][-1])
  if attack=='drop':plan['obligations'].remove(row);(stage/row['path']).unlink();group['parts'].remove(row['id'])
  elif attack=='sibling':row['dependencies']=[group['parts'][0]]
  elif attack in {'guard','increment','capture'}:
   old=row['statement'];row['statement']=old.replace(' && k < s','')if attack=='guard'else old.replace('(k+1)','k')if attack=='increment'else old.replace('integer j;','integer k;')
   path=stage/row['path'];path.write_text(path.read_text().replace(old,row['statement']));row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
  elif attack=='reference':
   path=stage/group['reference']['path'];path.write_text('/* forged original step */\n');group['reference']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
  elif attack=='source_definition':group['definition_source']['sha256']='0'*64
  (stage/'manifest.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
  refused(lambda:packets.check('std_vector_int_realloc_v3_grow',stage))

def test_copy_step_has_exactly_one_reference_in_reserve_and_no_new_constructor_duties(tmp_path):
 plan=packets.prepare('std_vector_int_realloc_v3_reserve',tmp_path/'reserve')
 assert len(plan['obligations'])==67
 group=next(g for g in plan['logical_obligations']if g['id']=='grow.copy.step')
 assert len(group['parts'])==24 and len(group['original_definition_parts'])==15 and plan['source_inventory']['unmapped_executable_events']==[]
 for member,count in [('ctor_count_value',35),('dtor',11)]:
  other=packets.prepare('std_vector_int_realloc_v3_'+member,tmp_path/member)
  assert len(other['obligations'])==count and not any(g['id']=='grow.copy.step'for g in other['logical_obligations'])
