"""2026-10-16 ET. Prospective actual-Library finite profile; executes no tools.

The selected existing new0.2 entry must already resolve the seven generic owned
premises. This builder neither creates a semantics entry nor chooses an owner.
Root must select the independently established exact context manifest after
examining derive()'s facts; a generated request grants no truth or authority.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)
def pin(path):
    path=Path(path).resolve();raw=path.read_bytes();return dict(path=str(path),bytes=len(raw),sha256=sha(raw))
def save(path,value,*,raw=False):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    data=value if raw else canonical(value)+b'\n'
    with path.open('xb') as stream:stream.write(data)
    return pin(path)
def portable(root,row):return dict(root='library',path=Path(row['path']).relative_to(root).as_posix(),sha256=row['sha256'])
def literal_cases():
    spec=importlib.util.spec_from_file_location('_finite_profile_literal_corpus',HERE/'corpus_public_v1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module.cases()

def context_for(row,identity,source_sha,roles):
    context=dict(row['context'],source_plan_sha256=source_sha,entry_identity=identity,
        owned_premises=[dict(role=role,owner=identity,rule='finite_context_'+role.replace('-','_')) for role in roles])
    return context

def derive(library_root,entry_id,owner):
    # Installed normal package only; never import a .scratch producer at runtime.
    from swdb import dx100_finite_trace as source
    from swdb.library import Library
    library=Library(Path(library_root));need(not library.problems,'valid source Library required')
    entry=library.get(entry_id);source.contracts.policy(library,entry)
    entry_pin=pin(library.files[entry_id]);need(source.canonical(source.strict(Path(entry_pin['path']).read_bytes()))==source.canonical(entry),'same physical JSON-subset semantics entry required')
    identity=dict(id=entry_id,sha256=entry_pin['sha256'])
    required=source.receiver.rule_rows(owner)+[source.logical_rule(owner)]
    by_id={row['id']:row for row in entry['rules']}
    need(all(source.canonical(by_id.get(row['id']))==source.canonical(row) for row in required),'actual same entry lacks exact selected owner generic rules')
    rows=[]
    for row in literal_cases():
        key=row['plan']['id'];raw=canonical(row['plan'])+b'\n';need(sha(raw)==source.PLAN_DIGESTS[key],'closed source Plan changed')
        context=context_for(row,identity,sha(raw),source.events.PREMISES)
        _,profile,_=source.events.render(row['plan'],context)
        count=profile['draw_count'];draws=dict(schema='finite-full-u32-draw-plan-1',count=count,scalar_type='uint32_t',domain=[0,2**32-1],independent=True,draw_before_trace=True,
            rows=[dict(index=i,c_lvalue='dws_choice_table[%d]'%i,anchor='finite.draw.%03d'%i) for i in range(count)],budget_failure='checked property; no assume/truncate/reset',actual_draws_supplied=False)
        facts=source.receiver.facts_for(row['plan'],context,profile,draws,entry_id)
        rows.append(dict(id=key,plan=row['plan'],context=context,profile=profile,facts=facts,
            manifest_row=dict(source_plan_sha256=sha(raw),context_sha256=sha(canonical(context)+b'\n'),facts_sha256=sha(canonical(facts))),
            prediction=row['prediction']))
    return dict(schema='finite-public-derived-context-requests-1',entry=entry_pin,same_entry=identity,owner=owner,cases=rows,
        owner_authority_or_public_result_granted=False)


def contract(key,source_pin,selection):
    return dict(id='contract.dx100_finite_'+key,kind='rewrite_contract',formal_frame=1,version='1.0',
        provenance=dict(origin=dict(intrinsic_specification='ticket28 closed finite owned-model fixture; 2026-10-16 ET')),
        proof_unit=dict(source=source_pin,function='dwe_finite_trace'),finite_trace_selection=selection,concurrency_frame=[],
        clauses=[dict(id=ident,role=role,statement=statement,discharge_mode='runtime_guard',negative_control=dict(id='finite-safety',check='finite-safety'),
            acsl=dict(text=text,uses=[]),proof_placement=dict(once='self')) for ident,role,statement,text in [
            ('frame','frame','The finite trace may update its complete owned modeled state.',r'assigns \everything;'),
            ('result','postcondition','Every reached finite model safety check holds and normal return is zero.',r'ensures \result == 0;')]],
        pattern_key=[dict(roles=['target'],address_shapes=['stream'],update_kind='read')],strategies=[],uses_intrinsics=[],uses_library_operations=[],
        runtime_guards=[],knobs=[],preservation_obligations=[],requirement_map=[],correctness_check=dict(kernel='dwe_finite_trace',check='finite-safety'),
        execution_witness=dict(check='finite-safety'),negative_controls=[dict(id=name,kind=name,check='finite-safety') for name in ('overlapping_pointer','double_claim','dropped_operand')])


def assemble(library_root,entry_id,owner,owned_manifest,producer_manifest,runtime,method_seed):
    from swdb import dx100_finite_trace as source
    from swdb.library import Library
    root=Path(library_root).resolve();library=Library(root);derived=derive(root,entry_id,owner)
    reads=source.receiver.Inputs();owned=source.strict(reads.read(owned_manifest))
    expected=dict(schema='finite-public-owned-contexts-1',owner=owner,same_entry=derived['same_entry'],contexts={row['id']:row['manifest_row'] for row in derived['cases']})
    need(source.canonical(owned)==source.canonical(expected),'externally selected exact owner/context manifest required; requests are not authority')
    closure=dict(schema=source.MANIFEST,files={name:pin(path) for name,path in source.producer_paths().items()})
    need(source.canonical(source.strict(reads.read(producer_manifest)))==source.canonical(closure),'root-selected installed producer closure differs')
    selected_runtime=source.strict(reads.read(runtime));need(set(selected_runtime)=={'compiler_wrapper','compiler_driver','numeric_runtime_receipt'},'root-selected runtime roles required')
    for row in selected_runtime.values():source.opaque_pin(row)
    method=source.strict(reads.read(method_seed))
    need(method.get('id')==source.METHOD and method.get('evidence_kind')=='execution'
        and ((method.get('c_lowering') or {}).get('translators') or []).count(dict(id=source.MANIFEST,sha256=producer_manifest['sha256']))==1,
        'root-selected actual installed finite method identity/producer manifest required')
    target=root/'finite-traces-v1';target.mkdir(exist_ok=False)
    owned_copy=save(target/'owned-manifest.json',reads.read(owned_manifest),raw=True)
    producers_copy=save(target/'producers.json',reads.read(producer_manifest),raw=True)
    runtime_copy=save(target/'runtime.json',reads.read(runtime),raw=True)
    selected_method=save(root/'methods/dx100-finite-whole-trace-v1.yaml',reads.read(method_seed),raw=True)
    entry=library.get(entry_id);headers={Path(row['path']).name:pin(library.resolve(row)) for row in entry['checked_body']['components']}
    package=Path(source.receiver.__file__).resolve().parent;out=[]
    for row in derived['cases']:
        key=row['id'];directory=target/key;directory.mkdir()
        selected_plan=save(directory/'plan.json',row['plan']);context=save(directory/'context.json',row['context'])
        receiver=save(directory/'receiver.json',dict(schema='owned-finite-model-receiver-1',source_plan_sha256=selected_plan['sha256'],context_sha256=context['sha256'],
            entry_identity=derived['same_entry'],owned_premises_sha256=sha(canonical(row['context']['owned_premises']))))
        source_policy=dict(schema='finite-trace-source-policy-1',source_plan=selected_plan,context=context,receiver=receiver,entry=derived['entry'],entry_id=entry_id,
            headers=headers,hook_producer=pin(package/'whole_model_v3.py'),producer=pin(Path(source.events.__file__)))
        policy=save(directory/'trace-policy.json',source_policy)
        prepared=source.events.prepare(source.events.OwnedSelection(source.events.Pin.parse(policy)))
        outputs={name:save(directory/filename,data,raw=True) for name,filename,data in [
            ('c_text','trace.c',prepared.c_text.encode()),('certificate','trace-certificate.json',prepared.certificate_json),('draws','draws.json',prepared.draw_plan_json),
            ('profile','profile.json',prepared.resource_profile_json),('anchors','anchors.json',prepared.anchors_json)]}
        prepared_pins=dict(policy=policy,**outputs)
        selected=save(directory/'owned-selection.json',source.receiver.owned_selection_metadata(source_policy,prepared_pins,derived['same_entry'],row['facts'],owner))
        composition=save(directory/'composition-policy.json',dict(schema='finite-owned-receiver-selection-2',composer=pin(Path(source.receiver.__file__)),
            producer=pin(Path(source.events.__file__)),receiver_basis=pin(package/'receiver_state_draws_basis_v2.py'),prepared=prepared_pins,entry_id=entry_id,premise_owner=owner,owned_selection=selected))
        source.receiver.prepare(source.receiver.OwnedSelection(source.receiver.Pin.parse(composition)))
        public=save(directory/'public-selection.json',dict(kind=source.KIND,composition=composition,producers=portable(root,producers_copy),runtime=portable(root,runtime_copy),owned_manifest=portable(root,owned_copy)))
        doc=contract(key,portable(root,selected_plan),portable(root,public))
        selected_contract=save(root/'rewrite_contracts'/('dx100_finite_'+key+'.yaml'),doc)
        out.append(dict(case_id=key,contract=dict(id=doc['id'],sha256=sha(canonical(doc))),physical_contract=selected_contract,
            conditional_predicted_verdict='proven' if row['prediction']=='predicted_valid' else 'refuted',actual_verdict=None))
    fresh=Library(root)
    for row in out:
        selected=source.select_baseline(fresh,row['contract']['id'],fresh.get(row['contract']['id']));source.compose(selected)
    reads.recheck();need(pin(library.files[entry_id])==derived['entry'],'selected entry changed during profile preparation')
    return dict(schema='finite-public-profile-1',date='2026-10-16 ET',cases=out,entry=derived['entry'],owned_manifest=owned_manifest,method=selected_method,
        record_assumptions=source.proof_semantics.record_assumptions(fresh,entry_id,derived['entry']['sha256']),
        source_CPP_correspondence=False,compiler_native_verifier_public_admission=False,required_actual_count=30,required_skip_count=0)

if __name__=='__main__':
    raise SystemExit('Call derive/assemble only from a separately reviewed root-owned no-child preparation controller; no default authority or execution.')
