"""2026-10-16 Eastern. Freeze scratch V2 and exact predecessor/current-hook inverses."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'finite-trace-public-v1'
PRODUCTION=HERE.parents[4]/'swdb'
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def pin(path):
    raw=path.read_bytes();return dict(path=str(path.resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def save(name,value):(HERE/name).write_bytes(canonical(value)+b'\n')
def inverse(old,new):
    a=old.read_text();b=new.read_text();changes=[]
    for tag,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes():
        if tag!='equal':changes.append(dict(old_start=i,old_end=j,new_start=k,new_end=l,before=a[i:j],after=b[k:l]))
    restored=b
    for row in reversed(changes):
        assert restored[row['new_start']:row['new_end']]==row['after']
        restored=restored[:row['new_start']]+row['before']+restored[row['new_end']:]
    assert restored==a
    nodes=lambda text:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.ClassDef,ast.FunctionDef))}
    aa,bb=nodes(a),nodes(b)
    return dict(predecessor=pin(old),successor=pin(new),byte_exact_inverse=True,edits=changes,
        changed_definition_ASTs=sorted(k for k in set(aa)|set(bb) if aa.get(k)!=bb.get(k)),
        unchanged_definition_ASTs=sorted(k for k in set(aa)&set(bb) if aa[k]==bb[k]))
def freeze():
    predecessor=json.loads((OLD/'source-packet-v1.json').read_bytes())
    for row in predecessor['owned_files']+predecessor['basis_files']:
        assert pin(Path(row['path']))==row
    for path in (HERE/'source-plans').glob('*.json'):
        assert path.read_bytes()==(OLD/'source-plans'/path.name).read_bytes()
    hooks=json.loads((HERE/'hook-inverse.json').read_bytes())
    for name,row in hooks['files'].items():
        assert pin(PRODUCTION/name)['sha256']==row['base_sha256']
        assert pin(HERE/'proposed/swdb'/name)['sha256']==row['proposed_sha256']
    changed=('proposed/swdb/dx100_finite_trace.py','proposed/swdb/dx100_finite_trace_adapter.py','proposed/swdb/_dx100_finite/finite_checks_v1.py')
    changes={name:inverse(OLD/name,HERE/name) for name in changed}
    assert changes[changed[0]]['changed_definition_ASTs']==['compose']
    assert changes[changed[1]]['changed_definition_ASTs']==['finish','run']
    assert set(changes[changed[2]]['changed_definition_ASTs'])=={'native_override','failure_origin','same_origin','replay_matches','check_adoption','read_outcome','native_row','public_record'}
    save('v2-repair-inverse.json',dict(date='2026-10-16 Eastern',files=changes,predecessor_source_packet=pin(OLD/'source-packet-v1.json'),
        predecessor_80_pins_unchanged=True,all_30_plan_bytes_unchanged=True,model_headers_receiver_and_source_resource_policy_unchanged=True))
    files=sorted(p for p in HERE.rglob('*') if p.is_file() and p.name!='source-packet-v2.json')
    assert not list(HERE.rglob('__pycache__'))
    for path in files:
        assert not path.is_symlink()
        if path.suffix=='.py':ast.parse(path.read_bytes())
    basis=[OLD/'source-packet-v1.json',HERE.parent/'finite-trace-public-v1-independent-review/independent-finite-public-v1-spec-review-20261016.json',
        PRODUCTION/'dx100_whole_checked.py',PRODUCTION/'library.py',*(PRODUCTION/name for name in hooks['files'])]
    basis += [Path(row['path']) for row in predecessor['basis_files']]
    basis=list(dict.fromkeys(basis))
    packet=dict(schema='finite-public-trace-source-packet-2',date='2026-10-16 Eastern',owned_files=[pin(p) for p in files],basis_files=[pin(p) for p in basis],
        public_kind='dx100-whole-interface-finite-trace-1',closed_plan_count=30,pure_test_count=16,actual_public_fixture_count_required=30,actual_skip_count_required=0,
        findings_repaired=['native failure blocks proven at exact public finish boundary','same actual generated assertion function/line required for replay and retained goal','physical portable Plan source checked before real Library.resolve erases aliases'],
        proposed_hooks=list(hooks['files']),hook_base='exact currently applied coherent V5 bytes',exact_hook_inverse=True,predecessor_V1_HOLD_unchanged=True,
        model_premise_draw_resource_capacity_checks_unchanged=True,root_owned_Library_context_method_runtime_and_producer_regeneration_still_required=True,
        actual_compiler_native_verifier_public_or_SSH_execution=False,actual_assertion_location_correspondence_unobserved=True,independent_review_required=True)
    save('source-packet-v2.json',packet)
    print(json.dumps(dict(packet=pin(HERE/'source-packet-v2.json'),core=pin(HERE/'proposed/swdb/dx100_finite_trace.py'),adapter=pin(HERE/'proposed/swdb/dx100_finite_trace_adapter.py'),checks=pin(HERE/'proposed/swdb/_dx100_finite/finite_checks_v1.py'),hooks=pin(HERE/'finite-hooks.patch')),sort_keys=True))
if __name__=='__main__':freeze()
