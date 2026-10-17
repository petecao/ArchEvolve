"""2026-10-16 ET. Public total allocator formal-half namespace visibility.

Scripted syntax visibility is not Frama-C and establishes no proof acceptance.
"""
import json
import sys
from pathlib import Path
import yaml
from conftest import run_swdb
from testkit.dx100_allocation import prove_allocation


def _parser(root):
 parser=root/'counter-declaration-visibility.py';observations=root/'counter-declaration-visibility.jsonl'
 parser.write_text('''import json,re,sys
from pathlib import Path
if sys.argv[1:] == ['-version']:
 print('33.0');raise SystemExit(0)
assert '-wp'not in sys.argv,'visibility control must never invoke WP'
source=Path(sys.argv[-1]).read_text()
frames=list(re.finditer(r'assigns\\s+([A-Za-z_]+),\\s*SPD_count,\\s*region_count;',source))
visible=all(all(len([m for m in re.finditer(r'(?:int|signed char)\\s+'+name+r'\\s*;',source)if m.start()<frame.start()])==1 for name in [frame[1],'SPD_count','region_count'])for frame in frames)
with Path('''+repr(str(observations))+''').open('a')as log:log.write(json.dumps({'source':source,'frames':len(frames),'visible':visible})+'\\n')
if not visible:
 print('[kernel:annot-error] formal_half.c:5: unbound logic variable REG_count. Ignoring specification of function trust_fixture')
 raise SystemExit(1)
''')
 return parser,observations


def test_total_allocator_formal_half_sees_exact_counter_namespace_without_helper_axioms(tmp_path):
 result,records,entry,marker=prove_allocation(tmp_path,102)
 assert result.returncode==0,result.stdout+result.stderr
 assert marker.exists(),'only explicit exit99 stand-in'
 parser,observations=_parser(tmp_path)
 checked=run_swdb('validate','--records',records.path,'--library',tmp_path/'library',env={'SWDB_FRAMA_C':f'{sys.executable} {parser}','SWDB_CBMC':'none'})
 assert checked.returncode==0,checked.stdout+checked.stderr
 rows=[json.loads(line)for line in observations.read_text().splitlines()]
 framed=[r for r in rows if r['frames']]
 assert framed and all(r['visible']for r in framed)
 assert all(r'assigns REG_count, SPD_count, region_count; ensures \result == 102;'in r['source']for r in framed)
 assert all('get_new_tile_unsigned_int'not in r['source']and 'get_new_reg_unsigned_int'not in r['source']and r'terminates \false'not in r['source']for r in framed)


def test_total_allocator_namespace_gates_preserve_wrong_post_and_unknown_name_refusal(tmp_path):
 import copy
 import shutil
 result,records,entry,marker=prove_allocation(tmp_path,102)
 assert result.returncode==0,result.stdout+result.stderr
 assert marker.exists()
 # Formal-half validation needs seed metadata, not a stale proof record when
 # deliberately varying its contract. Keep the original producer immutable.
 validation_records=tmp_path/'visibility-records'
 shutil.copytree(records.path,validation_records,ignore=shutil.ignore_patterns('proofs','*.sqlite','*.sqlite-*'))
 contract_path=tmp_path/'library/rewrite_contracts/trust.yaml'
 semantics_path=tmp_path/'library/proof_semantics/dx100_trust_fixture.yaml'
 contract_bytes=contract_path.read_bytes();semantics_bytes=semantics_path.read_bytes()
 original=yaml.safe_load(contract_bytes);semantics=yaml.safe_load(semantics_bytes)
 parser,observations=_parser(tmp_path)
 for case in ['wrong-result','unknown-counter','wrong-subject','wrong-semantics','wrong-layout','superseded-semantics']:
  contract=copy.deepcopy(original);data=copy.deepcopy(semantics)
  extra=semantics_path.with_name('superseding-allocator.yaml')
  if case=='wrong-result':contract['clauses'][0]['acsl']['text']=contract['clauses'][0]['acsl']['text'].replace('== 102','== 101')
  elif case=='unknown-counter':contract['clauses'][0]['acsl']['text']=contract['clauses'][0]['acsl']['text'].replace('REG_count','unknown_count')
  elif case=='wrong-subject':contract['id']='contract.unrelated_counter_fixture.v1'
  elif case=='wrong-semantics':data['id']='semantics.unrelated_allocator_fixture'
  elif case=='wrong-layout':data['model']['layout']='unadmitted-allocator-layout'
  elif case=='superseded-semantics':
   successor=copy.deepcopy(data);successor.update(id='semantics.unadmitted_successor',sequence=data['sequence']+1)
   extra.write_text(yaml.safe_dump(successor,sort_keys=False))
  before=len(observations.read_text().splitlines())if observations.exists()else 0
  try:
   contract_path.write_text(yaml.safe_dump(contract,sort_keys=False));semantics_path.write_text(yaml.safe_dump(data,sort_keys=False))
   checked=run_swdb('validate','--records',validation_records,'--library',tmp_path/'library',env={'SWDB_FRAMA_C':f'{sys.executable} {parser}','SWDB_CBMC':'none'})
   rows=[json.loads(line)for line in observations.read_text().splitlines()[before:]]
   framed=[r for r in rows if r['frames']]
   (tmp_path/(case+'.validation.json')).write_text(json.dumps({'returncode':checked.returncode,'stdout':checked.stdout,'stderr':checked.stderr,'observations':rows},indent=2)+'\n')
   assert framed,case
   if case=='wrong-result':
    assert checked.returncode==0,checked.stdout+checked.stderr
    assert all(r['visible']and r'ensures \result == 101;'in r['source']for r in framed)
   else:
    assert checked.returncode!=0,case
    assert 'unbound logic variable'in checked.stderr
    assert any(not r['visible']for r in framed)
   assert all('get_new_tile_unsigned_int'not in r['source']and 'get_new_reg_unsigned_int'not in r['source']and r'terminates \false'not in r['source']for r in framed)
  finally:
   contract_path.write_bytes(contract_bytes);semantics_path.write_bytes(semantics_bytes)
   if extra.exists():extra.unlink()
 assert contract_path.read_bytes()==contract_bytes and semantics_path.read_bytes()==semantics_bytes
