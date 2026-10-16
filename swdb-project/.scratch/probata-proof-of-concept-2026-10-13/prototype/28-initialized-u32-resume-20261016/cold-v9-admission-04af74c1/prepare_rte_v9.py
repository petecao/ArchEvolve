"""Version the exact two original initialization reads; no audit or tools."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'cold-v8-admission-04af74c1'
old = (BASE / 'initialized_cold_obligations_v3.py').read_text()
before = "and name=='trust_fixture_assert_rte_initialization'\n"
after = "and name in {'trust_fixture_assert_rte_initialization','trust_fixture_assert_rte_initialization_2'}\n"
assert old.count(before) == 1
new = old.replace(before, after)
addition = r'''
def initialized_reads_v4(props,generated,validated_query,expected_wp_input):
 """Both source return operands keep distinct ordinary initialization goals."""
 assert validated_query['complete_ACSL_and_C_comparison'] is True
 number=validated_query['expected_result'];assert type(number) is int and number in {711,1107}
 assert validated_query['reference_sha256']=={711:'a324f08bed8b8101fcff22461e408b440f2f227f0d4d4ac6f5dcbed1611bccdb',1107:'46244c04dd878c93606add23f68a68732a5fe550d3d6b7ca308fedd4312fe094'}[number]
 assert validated_query['reference_is_native_proof'] is False
 first='trust_fixture_assert_rte_initialization';second=first+'_2'
 reads={first:('first',[]),second:('second',[first])}
 selected={name:p for name,p in props.items() if p['emitter']=='rte'}
 assert set(selected)==set(reads),'complete two-read source initialization census differs'
 for name,(local,dependencies) in reads.items():
  want={'property':name,'kind':'other','property_variant':'IPCodeAnnot','function':'trust_fixture',
   'source_file':str(expected_wp_input),'line':47,'extern':False,'emitter':'rte','origin':None,
   'call_context':None,'status_registered':True,'property_export_origin':'registered',
   'generated_smoke_failure':False,'description':'assert rte: initialization: '+r'\initialized(&'+local+');',
   'dependencies':dependencies}
  assert selected[name]==want,'source RTE read property/site/dependency differs'
  goals=[g for g in generated.values() if g['property']==name or name in g['targets']]
  assert goals==[{'goal':'typed_real_'+name,'property':name,'function':'trust_fixture','line':47,
   'passed':True,'smoke':False,'results':['valid'],'targets':[]}],'source RTE read lacks its unique direct Valid ordinary goal'
 return {'properties':list(reads),'source_locals':['first','second'],'source_line':47,
  'ordinary_direct_valid':2,'initialization_omitted_or_assumed':False}

def init_termination_v4(props,generated,validated_query,expected_wp_input):
 """Retain the sole registered unproved helper termination, never credit it."""
 assert validated_query['complete_ACSL_and_C_comparison'] is True and validated_query['reference_is_native_proof'] is False
 number=validated_query['expected_result'];assert type(number) is int and number in {711,1107}
 assert validated_query['reference_sha256']=={711:'a324f08bed8b8101fcff22461e408b440f2f227f0d4d4ac6f5dcbed1611bccdb',1107:'46244c04dd878c93606add23f68a68732a5fe550d3d6b7ca308fedd4312fe094'}[number]
 name='init_MAA_terminates'
 want={'property':name,'kind':'contract','property_variant':'IPPredicate','function':'init_MAA',
  'source_file':str(expected_wp_input),'line':27,'extern':False,'emitter':'','origin':None,
  'call_context':None,'status_registered':True,'property_export_origin':'registered',
  'generated_smoke_failure':False,'description':'terminates\n'+r'\true','dependencies':[]}
 assert props[name]==want,'implicit init termination property/site/status differs'
 assert not any(g['property']==name or name in g['targets'] for g in generated.values()),'unproved init termination acquired a native goal/target'
 assert not any(p['origin']==name or name in p['dependencies'] for key,p in props.items() if key!=name),'unproved init termination acquired an active dependency'
 return {'property':name,'CSV_status':'Unknown','native_goals':0,'Extern':False,
  'termination_proven':False,'partial_normal_return_scope_unchanged':True}

'''
anchor = 'def current_csv(rows,props,generated,failed,*,validated_query,expected_wp_input):\n'
assert new.count(anchor) == 1
new = new.replace(anchor, addition + anchor)
anchor = " unused=unused_arity0_v3(rows,props,generated,validated_query,expected_wp_input)\n"
assert new.count(anchor) == 1
new = new.replace(anchor, anchor + ' rte=initialized_reads_v4(props,generated,validated_query,expected_wp_input)\n termination=init_termination_v4(props,generated,validated_query,expected_wp_input)\n')
anchor = " result['CSV_rows']=len(rows);result['unused_requires_false_overload']=unused\n"
assert new.count(anchor) == 1
new = new.replace(anchor, anchor + " result['source_initialization_reads']=rte\n result['unproved_init_termination']=termination\n")
anchor = "   else:\n    assert '_requires' in name and row['status']=='Valid' and attached==[] and p['dependencies']\n"
assert new.count(anchor) == 1
replacement = "   elif name=='init_MAA_terminates':\n    assert row['status']=='Unknown' and expected[name][1]==r'\\true' and attached==[] and p['dependencies']==[] and p['origin'] is None\n" + anchor
new = new.replace(anchor, replacement)
(HERE / 'initialized_cold_obligations_v4.py').write_text(new)
