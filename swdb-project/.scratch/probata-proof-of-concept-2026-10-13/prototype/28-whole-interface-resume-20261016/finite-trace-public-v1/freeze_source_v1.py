"""2026-10-16 ET. Pure metadata/inverse packet author; no project imports/tools."""
import ast
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
PACKAGE=HERE/'proposed/swdb/_dx100_finite'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def pin(path):
    path=path.resolve();raw=path.read_bytes();return dict(path=str(path),bytes=len(raw),sha256=sha(raw))
def save(name,value):(HERE/name).write_bytes(canonical(value)+b'\n')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def inverse(old,new,name):
    a=old.read_text();b=new.read_text();ops=[dict(tag=tag,old_start=i,old_end=j,new_start=k,new_end=l,before=a[i:j],after=b[k:l]) for tag,i,j,k,l in difflib.SequenceMatcher(a=a,b=b,autojunk=False).get_opcodes() if tag!='equal']
    restored=b
    for row in reversed(ops):assert restored[row['new_start']:row['new_end']]==row['after'];restored=restored[:row['new_start']]+row['before']+restored[row['new_end']:]
    assert restored==a
    at=ast.parse(a);bt=ast.parse(b)
    nodes=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    aa,bb=nodes(at),nodes(bt)
    value=dict(date='2026-10-16 ET',predecessor=pin(old),successor=pin(new),byte_exact_inverse=True,edits=ops,
        changed_definition_ASTs=sorted(key for key in set(aa)|set(bb) if aa.get(key)!=bb.get(key)),
        unchanged_definition_ASTs=sorted(key for key in set(aa)&set(bb) if aa[key]==bb[key]))
    save(name,value);return value

def main():
    e=inverse(PACKAGE/'event_plan_v1.py',PACKAGE/'event_plan_v2.py','event-plan-v2-inverse.json')
    r=inverse(PACKAGE/'finite_owned_receiver_v3.py',PACKAGE/'finite_owned_receiver_v4.py','receiver-v4-inverse.json')
    assert e['changed_definition_ASTs']==['preflight','render'];assert r['changed_definition_ASTs']==['captured_finite']
    E=load('_freeze_pure_events',PACKAGE/'event_plan_v2.py');C=load('_freeze_pure_corpus',HERE/'corpus_public_v1.py')
    profiles=[]
    for row in C.cases():
        text,profile,anchors=E.render(row['plan'],row['context']);profiles.append(dict(case_id=row['plan']['id'],source=pin(HERE/'source-plans'/(row['plan']['id']+'.json')),
            derived_resource_profile=profile,trace_function_sha256=sha(text.encode()),anchor_sha256=sha(canonical(anchors)),actual_loops_native_verifier=None))
    save('source-resource-census.json',dict(date='2026-10-16 ET',cases=profiles,max_nodes=max(x['derived_resource_profile']['nodes_required'] for x in profiles),
        max_node_limit=max(x['derived_resource_profile']['node_limit'] for x in profiles),capacity_check_disabled=False,actual_public_admission=False))
    own=[path for path in sorted(HERE.rglob('*')) if path.is_file() and path.name!='source-packet-v1.json' and not path.name.startswith('independent-')]
    for path in own:
        if path.suffix=='.py':ast.parse(path.read_bytes())
    inputs=[HERE.parent/'finite-event-plan-v1/corpus_v1.py',HERE.parent/'finite-event-plan-v1/event_plan_v1.py',HERE.parent/'finite-owned-receiver-v3/finite_owned_receiver_v3.py',
        HERE.parent/'receiver-state-draws-v2/receiver_state_draws_v2.py',HERE.parent/'model-entry-v3/whole_model_v3.py']
    inputs += [HERE.parent/name for name,_ in E.HEADERS]
    inputs += [HERE.parent/'production-route-v4/proposed/swdb'/name for name in ('cbmc_adapter.py','formal_frame.py','proof_setup.py','proof_semantics.py','cbmc_translator.py','dx100_whole_checked.py')]
    inputs += [HERE.parents[4]/'swdb'/name for name in ('level_rule.py','handoff_level.py')]
    save('source-packet-v1.json',dict(date='2026-10-16 ET',schema='finite-public-trace-source-packet-1',owned_files=[pin(p) for p in own],basis_files=[pin(p) for p in inputs],
        public_kind='dx100-whole-interface-finite-trace-1',normal_package_additions=['dx100_finite_trace.py','dx100_finite_trace_adapter.py','_dx100_finite/'],
        proposed_hooks=['cbmc_adapter.py','formal_frame.py','proof_semantics.py','proof_setup.py'],original_SourceUnit_hooks_inverse_exact=True,
        closed_plan_count=30,original18_source_bytes_preserved=True,pure_test_count=13,actual_public_fixture_count_required=30,actual_skip_count_required=0,
        new_six_generic_premises_and_logical_query_rule_require_actual_same_physical_entry=True,
        root_selected_owner_context_runtime_method_and_joint_SourceUnit_rebind_required=True,
        no_project_imports_compiler_native_verifier_or_SSH_executed=True,actual_Library_preparation_or_scientific_acceptance=False))
    print(json.dumps(dict(packet=pin(HERE/'source-packet-v1.json'),core=pin(HERE/'proposed/swdb/dx100_finite_trace.py'),adapter=pin(HERE/'proposed/swdb/dx100_finite_trace_adapter.py'),hooks=pin(HERE/'finite-hooks.patch')),sort_keys=True))

if __name__=='__main__':main()
