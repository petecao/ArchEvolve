"""Compiler-free source fixture assembly; no model or native evaluation."""
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module

producer=load('finite_source_producer',HERE/'event_plan_v1.py')
corpus=load('finite_source_corpus',HERE/'corpus_v1.py')

def pin(path):
    raw=path.read_bytes()
    return dict(path=str(path.resolve()),bytes=len(raw),sha256=producer.digest(raw))

def save(path,value):
    raw=producer.canonical(value)+b'\n';path.write_bytes(raw);return pin(path)

def bundle(directory,plan,context):
    directory.mkdir(parents=True,exist_ok=True)
    source=save(directory/'plan.json',plan)
    entry=save(directory/'entry-prospective.json',dict(kind='proof_semantics',target='dx100-mmio',
        contract_form='dx100-whole-interface-checked-body-1',scope='inert fixture snapshot; no public library authority'))
    identity=dict(id='trial.dx100.whole.checked-body.new0.2',sha256=entry['sha256'])
    context=dict(context,source_plan_sha256=source['sha256'],entry_identity=identity,
        owned_premises=[dict(role=role,owner=identity,rule='prospective_'+role.replace('-','_')) for role in producer.PREMISES])
    ctx=save(directory/'context.json',context)
    receiver=save(directory/'receiver.json',dict(schema='owned-finite-model-receiver-1',source_plan_sha256=source['sha256'],
        context_sha256=ctx['sha256'],entry_identity=identity,owned_premises_sha256=producer.digest(producer.canonical(context['owned_premises']))))
    headers={name:pin(WHOLE/name) for name,_ in producer.HEADERS}
    policy=save(directory/'policy.json',dict(schema='finite-trace-source-policy-1',source_plan=source,context=ctx,receiver=receiver,
        entry=entry,entry_id=identity['id'],headers=headers,hook_producer=pin(WHOLE/'model-entry-v3/whole_model_v3.py'),producer=pin(HERE/'event_plan_v1.py')))
    return policy


def build(output):
    output.mkdir(parents=True,exist_ok=False)
    rows=[]
    for case in corpus.cases():
        directory=output/case['plan']['id'];policy=bundle(directory,case['plan'],case['context'])
        prepared=producer.prepare(producer.OwnedSelection(producer.Pin.parse(policy)))
        outputs={}
        for name,raw in [('trace.c',prepared.c_text.encode()),('certificate.json',prepared.certificate_json),
            ('profile.json',prepared.resource_profile_json),('draw-plan.json',prepared.draw_plan_json),('anchors.json',prepared.anchors_json)]:
            (directory/name).write_bytes(raw);outputs[name]=pin(directory/name)
        rows.append(dict(id=case['plan']['id'],pair=case['pair'],predicted_verdict=case['prediction'],reason=case['reason'],
            policy=policy,outputs=outputs,actual_verdict=None))
    manifest=dict(schema='prospective-finite-event-corpus-1',date='2026-10-16 ET',cases=rows,
        predictions_are_producer_inputs=False,actual_compiler_native_solver_or_public_execution=False,
        required_public_registry_and_owned_receiver_resolution=True)
    save(output/'manifest.json',manifest)
    return manifest

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('one fresh source output directory required')
    result=build(Path(sys.argv[1]).resolve())
    print(json.dumps(dict(cases=len(result['cases']),actual_execution=False),sort_keys=True))
