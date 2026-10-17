"""Pure source composition fixtures. Their owned rules have no public authority."""
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
FINITE=WHOLE/'finite-event-plan-v1'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module

bridge=load('finite_owned_bridge',HERE/'finite_owned_receiver_v1.py')
finite=bridge.captured_finite((FINITE/'event_plan_v1.py').read_bytes(),str(FINITE/'event_plan_v1.py'))

def pin(path):
    raw=path.read_bytes();return dict(path=str(path.resolve()),bytes=len(raw),sha256=bridge.sha(raw))
def save(path,doc):path.write_bytes(bridge.canonical(doc)+b'\n');return pin(path)

def assemble(directory,case_id='history_latest_positive',owner='prospective-fixture-owner'):
    directory.mkdir(parents=True,exist_ok=True)
    old=FINITE/'prepared-corpus-v1'/case_id;old_policy=json.loads((old/'policy.json').read_bytes())
    plan=json.loads(Path(old_policy['source_plan']['path']).read_bytes());context=json.loads(Path(old_policy['context']['path']).read_bytes())
    profile=json.loads((old/'profile.json').read_bytes());draws=json.loads((old/'draw-plan.json').read_bytes())
    entry_id='semantics.dx100_bfs_0_2'
    facts=bridge.facts_for(plan,context,profile,draws,entry_id)
    entry=dict(id=entry_id,version='0.2',kind='proof_semantics',target='dx100-mmio',contract_form=bridge.MODEL_KIND,
        rules=bridge.rule_rows(facts,owner),scope='inert rule-resolution fixture; full checked-entry Library validation remains required',public_admission=False)
    entry_pin=save(directory/'entry-with-owned-rules.json',entry);identity=dict(id=entry_id,sha256=entry_pin['sha256'])
    context=dict(context,entry_identity=identity,owned_premises=[dict(role=role,owner=identity,rule='finite_context_'+role.replace('-','_')) for role in finite.PREMISES])
    context_pin=save(directory/'context.json',context)
    receiver_pin=save(directory/'receiver.json',dict(schema='owned-finite-model-receiver-1',source_plan_sha256=old_policy['source_plan']['sha256'],
        context_sha256=context_pin['sha256'],entry_identity=identity,owned_premises_sha256=bridge.sha(bridge.canonical(context['owned_premises']))))
    source_policy=dict(old_policy,context=context_pin,receiver=receiver_pin,entry=entry_pin,entry_id=entry_id)
    selected=save(directory/'trace-policy.json',source_policy)
    prepared=finite.prepare(finite.OwnedSelection(finite.Pin.parse(selected)))
    artifacts={}
    for key,name,raw in [('c_text','trace.c',prepared.c_text.encode()),('certificate','trace-certificate.json',prepared.certificate_json),
        ('draws','draws.json',prepared.draw_plan_json),('profile','profile.json',prepared.resource_profile_json),('anchors','anchors.json',prepared.anchors_json)]:
        path=directory/name;path.write_bytes(raw);artifacts[key]=pin(path)
    assert prepared.c_text.encode()==(old/'trace.c').read_bytes()
    policy=save(directory/'composition-policy.json',dict(schema='finite-owned-receiver-selection-1',composer=pin(HERE/'finite_owned_receiver_v1.py'),
        producer=pin(FINITE/'event_plan_v1.py'),receiver_basis=pin(WHOLE/'receiver-state-draws-v2/receiver_state_draws_v2.py'),
        prepared=dict(policy=selected,**artifacts),entry_id=entry_id,premise_owner=owner))
    result=bridge.prepare(bridge.OwnedSelection(bridge.Pin.parse(policy)))
    outputs={}
    for name,raw in [('combined.c',result.c_text.encode()),('owned-receiver.c',result.receiver_c_text.encode()),
        ('composition-certificate.json',result.certificate_json),('draw-binding.json',result.draw_binding_json),('integration.json',result.integration_json)]:
        path=directory/name;path.write_bytes(raw);outputs[name]=pin(path)
    return dict(case_id=case_id,selection=policy,outputs=outputs,actual_verdict=None)


def build(output):
    output.mkdir(parents=True,exist_ok=False)
    cases=json.loads((FINITE/'prepared-corpus-v1/manifest.json').read_bytes())['cases'];rows=[]
    for case in cases:
        result=assemble(output/case['id'],case['id']);result.update(conditional_predicted_verdict=case['predicted_verdict']);rows.append(result)
    manifest=dict(schema='finite-owned-composition-corpus-1',date='2026-10-16 ET',cases=rows,
        all_rule_owners_are_synthetic_fixture_owners=True,actual_library_compiler_native_solver_or_public_admission=False,
        per_case_selected_entry_hashes_are_distinct=True,no_same_physical_entry_across_all_cases_claim=True)
    save(output/'manifest.json',manifest);return manifest

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('one fresh owned composition source directory required')
    result=build(Path(sys.argv[1]).resolve());print(json.dumps(dict(cases=len(result['cases']),actual_execution=False)))
