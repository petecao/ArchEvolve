"""2026-10-16 Eastern. Pure scope-successor packet/inverse author."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'finite-trace-public-v2'
SOURCE=HERE.parent/'abi-memory-production-v1/proposed/swdb/dx100_checked_source.py'
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def pin(path):
    raw=path.read_bytes();return dict(path=str(path.resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def save(name,value):(HERE/name).write_bytes(canonical(value)+b'\n')
def inverse(a,b):
    original=a.read_text();current=b.read_text();edits=[]
    for tag,i,j,k,l in difflib.SequenceMatcher(a=original,b=current,autojunk=False).get_opcodes():
        if tag!='equal':edits.append(dict(old_start=i,old_end=j,new_start=k,new_end=l,before=original[i:j],after=current[k:l]))
    restored=current
    for row in reversed(edits):
        assert restored[row['new_start']:row['new_end']]==row['after'];restored=restored[:row['new_start']]+row['before']+restored[row['new_end']:]
    assert restored==original
    nodes=lambda text:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    aa,bb=nodes(original),nodes(current)
    return dict(predecessor=pin(a),successor=pin(b),byte_exact_inverse=True,edits=edits,
        changed_definition_ASTs=sorted(k for k in set(aa)|set(bb) if aa.get(k)!=bb.get(k)),unchanged_definition_ASTs=sorted(k for k in set(aa)&set(bb) if aa[k]==bb[k]))
def main():
    previous=json.loads((OLD/'source-packet-v2.json').read_bytes())
    for row in previous['owned_files']+previous['basis_files']:assert pin(Path(row['path']))==row
    assert pin(SOURCE)['sha256']=='84e76df70d0256fd6ebb4f99a4e26e30f164a603ccfecc9df1be597707ff358b'
    names=['proposed/swdb/dx100_finite_trace.py','proposed/swdb/_dx100_finite/finite_owned_receiver_v4.py','finite_profile_v1.py']
    changes={name:inverse(OLD/name,HERE/name) for name in names}
    changes['proposed/swdb/dx100_checked_source.py']=inverse(SOURCE,HERE/'proposed/swdb/dx100_checked_source.py')
    assert changes[names[0]]['changed_definition_ASTs']==['compose','producer_paths','record_assumptions']
    assert changes[names[1]]['changed_definition_ASTs']==['captured_rule_scope','prepare','resolve_rules','rule_scope_pin']
    assert changes[names[2]]['changed_definition_ASTs']==['assemble','derive']
    assert changes['proposed/swdb/dx100_checked_source.py']['changed_definition_ASTs']==['compose','producer_paths','record_assumptions']
    for name in ('dx100_finite_trace_adapter.py','proof_semantics.py','proof_setup.py','formal_frame.py','cbmc_adapter.py','_dx100_finite/finite_checks_v1.py','_dx100_finite/event_plan_v2.py'):
        assert (HERE/'proposed/swdb'/name).read_bytes()==(OLD/'proposed/swdb'/name).read_bytes()
    for path in (HERE/'source-plans').glob('*.json'):assert path.read_bytes()==(OLD/'source-plans'/path.name).read_bytes()
    save('scope-inverse-v3.json',dict(schema='finite-public-scope-inverse-3',date='2026-10-16 Eastern',files=changes,predecessor_V2_and_30_plans_unchanged=True,
        generic_recorder_old_0_1_and_native_model_verdict_policy_unchanged=True,four_finite_hooks_unchanged=True))
    a=SOURCE.read_text();b=(HERE/'proposed/swdb/dx100_checked_source.py').read_text()
    (HERE/'typed-source-hunk.patch').write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/swdb/dx100_checked_source.py',tofile='b/swdb/dx100_checked_source.py')))
    own=sorted(path for path in HERE.rglob('*') if path.is_file() and path.name!='source-packet-v3.json')
    assert not list(HERE.rglob('__pycache__'))
    for path in own:
        assert not path.is_symlink()
        if path.suffix=='.py':ast.parse(path.read_bytes())
    basis=[OLD/'source-packet-v2.json',HERE.parent/'finite-entry-rules-v1/source-packet-v1.json',HERE.parent/'finite-entry-rules-v1/entry_rules_v1.py',HERE.parent/'abi-memory-production-v1/source-packet-v1.json',SOURCE]
    basis += [Path(row['path']) for row in previous['basis_files']]
    packet=dict(schema='finite-public-trace-source-packet-3',date='2026-10-16 Eastern',owned_files=[pin(path) for path in own],basis_files=[pin(path) for path in dict.fromkeys(basis)],
        scope_module=pin(HERE/'proposed/swdb/_dx100_finite/context_rule_scope_v1.py'),fixed_typed_context_applicability=True,
        complete_generic_recorder_unchanged=True,no_caller_filter=True,closed_context_ID_families_and_full_physical_entry_references=True,
        all_common_trust_always_retained=True,source_rule_count_for_fixed_20_rule_entry=13,finite_rule_count_for_same_entry=14,
        pure_controls=dict(inherited=16,scope=6,total=22),actual_public_fixture_count_required=30,actual_skip_count_required=0,
        original_CPP_capture_ABI_and_native_correspondence_gates_unchanged=True,old_0_1_unchanged=True,
        actual_Library_preparation_compiler_native_verifier_public_SSH_execution=False,
        root_independent_review_complete_producer_union_and_regeneration_required=True)
    save('source-packet-v3.json',packet)
    print(json.dumps(dict(packet=pin(HERE/'source-packet-v3.json'),scope=packet['scope_module'],core=pin(HERE/'proposed/swdb/dx100_finite_trace.py'),source=pin(HERE/'proposed/swdb/dx100_checked_source.py'),receiver=pin(HERE/'proposed/swdb/_dx100_finite/finite_owned_receiver_v4.py'),source_patch=pin(HERE/'typed-source-hunk.patch')),sort_keys=True))
if __name__=='__main__':main()
