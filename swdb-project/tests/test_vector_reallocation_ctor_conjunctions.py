"""Next pure source preparation tracer; 2026-10-16 ET. No tool execution."""
import hashlib,json
from pathlib import Path
import pytest
from swdb import vector_reallocation_vcs as packets

def test_compound_arguments_keep_precedence_during_simultaneous_substitution():
 parts,_receipt=packets.predicate_conjuncts(
  'predicate p(integer x, integer y) = 4*x == y && Heap::f(x,y) == 0;',
  ['a+1','Heap::put_integer(h,r,o+8,n)'])
 assert parts==['4*(a+1) == Heap::put_integer(h,r,o+8,n)',
                'Heap::f((a+1),Heap::put_integer(h,r,o+8,n)) == 0']

def test_constructor_positive_post_requires_exact_six_independent_definition_parts(tmp_path):
 baseline=json.loads((Path(__file__).parent/'fixtures/proof/vector-reallocation-ctor-positive-046f.json').read_bytes())
 plan=packets.prepare('std_vector_int_realloc_v3_ctor_count_value',tmp_path/'ctor')
 assert len(plan['obligations'])==35
 group=next(g for g in plan['logical_obligations']if g['id']=='ctor.qualified.positive_post')
 assert group['original_statement']==baseline['original_positive_post']['statement']
 assert group['parts']==['ctor.qualified.positive_post.'+name for name in ['repr','cells.access','cells.initialization','cells.integer','cells.bounds','eligibility']]
 assert group['antecedent']=='t25v3_ctor_inv(h,r,o,b,n,n,v)'
 assert group['dependencies']==[] and group['premises_added']==[]
 reference=tmp_path/'ctor'/group['reference']['path']
 assert hashlib.sha256(reference.read_bytes()).hexdigest()==baseline['original_positive_post']['sha256']
 expected={r['id']:(r['path'],r['sha256'])for r in baseline['targets']if r['id']!='ctor.qualified.positive_post'}
 assert {r['id']:(r['path'],r['sha256'])for r in plan['obligations']if r['id']in expected}==expected
 assert plan['semantics']==baseline['semantics'] and plan['sources']==baseline['sources']
 rows={r['id']:r for r in plan['obligations']}
 for ident in group['parts']:
  row=rows[ident]
  assert row['dependencies']==[] and row['status']=='pending'
  assert group['antecedent']in row['statement']
  assert row['statement'].startswith(group['quantifiers'])
 now='Heap::put_integer(h,r,o+8,n)'
 load='Heap::load_int('+now+',b,(0+4*j))'
 expected=[
  't25_repr('+now+',r,o,b,0,n,n)',
  'Heap::typed_reads('+now+',b,(0+4*j),4,4)',
  'Heap::initialized_at('+now+',b,(0+4*j))',
  'Heap::integer_at('+now+',b,(0+4*j),'+load+')',
  '-2147483648 <= '+load+' <= 2147483647',
  '(n == 0 || (Heap::freeable('+now+',b,0) && r != b))',
 ]
 for index,(ident,conclusion)in enumerate(zip(group['parts'],expected,strict=True)):
  prefix=group['quantifiers']+(r'\forall integer j; 'if 1<=index<=4 else '')
  premise=group['antecedent']+(' && 0 <= j < n'if 1<=index<=4 else '')
  assert rows[ident]['statement']==prefix+premise+' ==> '+conclusion
  text=(tmp_path/'ctor'/rows[ident]['path']).read_text()
  assert text.count('check lemma ')==1 and 't25_cell_bridge'not in text and 't25_region_bridge'not in text
 for source in group['definition_sources']:
  raw=(packets.HERE/source['path']).read_bytes()
  assert hashlib.sha256(raw[source['begin']:source['end']]).hexdigest()==source['sha256']
 assert group['fresh_index']=='j'and group['fresh_index_free_in_antecedent']is False
 assert group['region_range_from_definition']=='0 <= j < n'
 assert packets.check('std_vector_int_realloc_v3_ctor_count_value',tmp_path/'ctor')==plan


def test_compound_argument_extension_preserves_capture_and_operator_guards():
 for value in ['x+', 'x/0', 'x < 1', 'x && 0', 'Heap::f(x,)', 'Heap::f((x+1)', '*x']:
  with pytest.raises(ValueError):packets.predicate_conjuncts('predicate p(integer x) = x < 1 && x < 2;', [value])
 with pytest.raises(ValueError,match='capture'):
  packets.predicate_conjuncts(r'predicate p(integer x) = (\forall integer j; x < j) && x < 2;', ['Heap::f(a+j)'])


def test_constructor_split_refuses_a_new_premise_at_the_public_preparation_boundary(tmp_path):
 original=packets.constructor_specs()
 for added in [' && n > 0',' && r != b',' && Heap::freeable(h,b,0)']:
  changed=[(*row[:3],row[3].replace(' ==> ',added+' ==> '))if row[0]=='ctor.qualified.positive_post'else row for row in original]
  with pytest.MonkeyPatch.context()as patch:
   patch.setattr(packets,'constructor_specs',lambda:changed)
   with pytest.raises(ValueError,match='exact full premise'):
    packets.prepare('std_vector_int_realloc_v3_ctor_count_value',tmp_path/'refused')


def test_all_six_components_and_definition_receipts_are_canonical(tmp_path):
 for attack in ['drop','sibling','premise','range','capture','bridge','substitution','reference']:
  stage=tmp_path/attack;plan=packets.prepare('std_vector_int_realloc_v3_ctor_count_value',stage)
  group=plan['logical_obligations'][0];row=next(r for r in plan['obligations']if r['id']==group['parts'][2])
  if attack=='drop':
   plan['obligations'].remove(row);(stage/row['path']).unlink();group['parts'].remove(row['id'])
  elif attack=='sibling':row['dependencies']=[group['parts'][0]]
  elif attack in {'premise','range','capture'}:
   before=row['statement'];after=before.replace(' ==> ',' && r != b ==> ')if attack=='premise'else before.replace('j < n','j <= n')if attack=='range'else before.replace('integer j;','integer n;')
   row['statement']=after;path=stage/row['path'];path.write_text(path.read_text().replace(before,after));row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
  elif attack=='bridge':group['definition_sources'][3]['ACSL_spelling_bridge']='predicate forged = false;'
  elif attack=='substitution':group['definition_expansions'][0]['definition_substitution']['b']='r'
  elif attack=='reference':
   path=stage/group['reference']['path'];path.write_text('/* forged original whole target */\n');group['reference']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
  (stage/'manifest.json').write_text(json.dumps(plan,sort_keys=True,indent=2)+'\n')
  with pytest.raises(ValueError):packets.check('std_vector_int_realloc_v3_ctor_count_value',stage)


def test_full_original_premise_distributes_over_exact_six_conclusions():
 for mask in range(1<<6):
  terms=[bool(mask&(1<<index))for index in range(6)]
  for premise in [False,True]:assert (not premise or all(terms))==all(not premise or term for term in terms)


def test_constructor_term_extension_preserves_all_thirty_eight_reviewed_grow_inputs(tmp_path):
 baseline=json.loads((Path(__file__).parent/'fixtures/proof/vector-reallocation-grow-and15-a20.json').read_bytes())
 plan=packets.prepare('std_vector_int_realloc_v3_grow',tmp_path/'grow')
 assert [{key:row[key]for key in ['id','path','sha256']}for row in plan['obligations']]==baseline['targets']
