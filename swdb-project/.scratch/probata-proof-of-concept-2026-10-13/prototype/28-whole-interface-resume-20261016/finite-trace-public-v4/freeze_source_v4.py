"""2026-10-16 Eastern. Freeze only the candidate-none summary attribution successor."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'finite-trace-public-v3'
PRODUCTION=HERE.parents[4]/'swdb'
def pin(path):
    raw=path.read_bytes();return dict(path=str(path.resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def save(name,value):(HERE/name).write_bytes(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n')
def inverse(old,new):
    a=old.read_text();b=new.read_text();edits=[]
    aa=a.splitlines(keepends=True);bb=b.splitlines(keepends=True)
    offsets=lambda rows:[0]+[sum(map(len,rows[:i])) for i in range(1,len(rows)+1)]
    ao,bo=offsets(aa),offsets(bb)
    for tag,i,j,k,l in difflib.SequenceMatcher(a=aa,b=bb,autojunk=False).get_opcodes():
        if tag!='equal':edits.append(dict(old_start=ao[i],old_end=ao[j],new_start=bo[k],new_end=bo[l],before=a[ao[i]:ao[j]],after=b[bo[k]:bo[l]]))
    restored=b
    for row in reversed(edits):
        assert restored[row['new_start']:row['new_end']]==row['after'];restored=restored[:row['new_start']]+row['before']+restored[row['new_end']:]
    assert restored==a
    nodes=lambda text:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    aa,bb=nodes(a),nodes(b)
    return dict(predecessor=pin(old),successor=pin(new),byte_exact_inverse=True,edits=edits,changed_definition_ASTs=sorted(k for k in set(aa)|set(bb) if aa.get(k)!=bb.get(k)),unchanged_definition_ASTs=sorted(k for k in set(aa)&set(bb) if aa[k]==bb[k]))
def main():
    previous=json.loads((OLD/'source-packet-v3.json').read_bytes())
    for row in previous['owned_files']+previous['basis_files']:assert pin(Path(row['path']))==row
    changed=('dx100_finite_trace_adapter.py','cbmc_adapter.py','proof_setup.py')
    changes={name:inverse(OLD/'proposed/swdb'/name,HERE/'proposed/swdb'/name) for name in changed}
    assert changes[changed[0]]['changed_definition_ASTs']==['check_launch','check_summary_job','prepared_context']
    assert changes[changed[1]]['changed_definition_ASTs']==['CbmcAdapter']
    assert changes[changed[2]]['changed_definition_ASTs']==['begin']
    for path in (OLD/'proposed/swdb').rglob('*.py'):
        name=str(path.relative_to(OLD/'proposed/swdb'))
        if name not in changed:assert (HERE/'proposed/swdb'/name).read_bytes()==path.read_bytes()
    for path in (HERE/'source-plans').glob('*.json'):assert path.read_bytes()==(OLD/'source-plans'/path.name).read_bytes()
    save('attribution-inverse-v4.json',dict(date='2026-10-16 Eastern',files=changes,predecessor_V3_106_pins_unchanged=True,
        source_CPP_and_scoped_rule_modules_generic_recorder_old0_1_model_native_policies_unchanged=True))
    hooks=json.loads((HERE/'hook-inverse.json').read_bytes())
    for name,row in hooks['files'].items():assert pin(PRODUCTION/name)['sha256']==row['base_sha256']
    save('invocation-schema-v4.json',dict(producer=pin(PRODUCTION/'proof.py'),unit_fields=['candidate','function','tree','tree_sha256','contract','contract_sha256','correctness_policy'],
        normal_summary=dict(candidate=None,correctness_policy=None,function='dwe_finite_trace',contract='selected normal rewrite_contract ID and semantic SHA',tree='canonical pinned Plan parent',tree_sha256='exact raw Plan SHA'),
        record_subject='library_summary',candidate_c_model_and_partial_summary_forms_refused=True,
        guard_locations=['proof_setup.begin before compose','CbmcAdapter.run before _tools','prepared_context before compose','check_launch before recheck'],
        no_claim_of_typed_Plan_candidate_support=True))
    own=sorted(p for p in HERE.rglob('*') if p.is_file() and p.name!='source-packet-v4.json')
    assert not list(HERE.rglob('__pycache__'))
    for path in own:
        if path.suffix=='.py':ast.parse(path.read_bytes())
    basis=[OLD/'source-packet-v3.json',PRODUCTION/'proof.py',PRODUCTION/'library.py',PRODUCTION/'dx100_whole_checked.py']+[Path(row['path']) for row in previous['basis_files']]
    packet=dict(schema='finite-public-trace-source-packet-4',date='2026-10-16 Eastern',owned_files=[pin(p) for p in own],basis_files=[pin(p) for p in dict.fromkeys(basis)],
        candidate_none_summary_only=True,all_seven_real_ProofUnit_fields_bound=True,guard_before_tool_probe_and_all_phases=True,
        V3_scope_and_V2_native_origin_repairs_preserved=True,generic_recorder_SourceUnit_old0_1_and_all_common_assumptions_unchanged=True,
        pure_controls=dict(inherited=22,attribution=4,total=26),actual_finite_summary_count_required=30,actual_skip_count_required=0,
        finite_summary_is_not_candidate_evidence=True,actual_Library_CLI_compiler_native_verifier_SSH_execution=False,
        root_independent_review_apply_and_complete_producer_regeneration_required=True)
    save('source-packet-v4.json',packet)
    print(json.dumps(dict(packet=pin(HERE/'source-packet-v4.json'),adapter=pin(HERE/'proposed/swdb/dx100_finite_trace_adapter.py'),cbmc=pin(HERE/'proposed/swdb/cbmc_adapter.py'),setup=pin(HERE/'proposed/swdb/proof_setup.py'),hooks=pin(HERE/'finite-hooks.patch')),sort_keys=True))
if __name__=='__main__':main()
