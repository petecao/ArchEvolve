"""Write the local independent decision from retained passive metadata only."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent.parent
EVIDENCE=BASE/'evidence'

def pin(path):
    data=path.read_bytes()
    return {'path':str(path.relative_to(BASE)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

metadata_path=EVIDENCE/'t25-closed-lifetime6-passive-cold-metadata-v6-20261016.json'
metadata=json.loads(metadata_path.read_text())
assert pin(metadata_path)['sha256']=='64af07b2da9ca8c2137041dd59e6c0f5d6fc31f2c064c62d5427b4a756e08ed5'
assert metadata['classification']=='COMPLETE_SIX_SOURCE_COLD_NOT_PROVEN'
assert metadata['raw_pre_post_equal'] and not metadata['all_six_normal_producer_proven']
proven=[r['id'] for r in metadata['leaves'] if r['normal_verdict']=='proven' and r['passed'] and 'valid' in r['native_results']]
pending=[r['id'] for r in metadata['leaves'] if r['normal_verdict']!='proven']
assert proven==['receiver.entry','constructor.frame','buffer.identity','zero.cleanup']
assert pending==['positive.exit_image','positive.cleanup']
assert all(r['native_results']==['timeout','unknown','timeout'] and r['failure_class']=='timeout' for r in metadata['leaves'] if r['id'] in pending)
attempts=[]
for version in (1,3,4,5,6):
    path=EVIDENCE/f't25-closed-lifetime6-passive-cold-metadata-v{version}-20261016.json'
    value=json.loads(path.read_text())
    attempts.append({'version':version,**pin(path),'classification':value['classification'],
                     'error':value.get('error'),'acceptance':False})
reviews=[]
for version in (1,3,4,5,6):
    path=EVIDENCE/f't25-closed-lifetime6-cold-auditor-parent-static-review-v{version}-20261016.json'
    reviews.append(pin(path))
packet=HERE/'inert-fb197c5d-public-v1'
packet_pins=[pin(packet/name) for name in ('packet.json','entry.py','expected.json','root-command.json')]
tasks=metadata['materialized_tasks']
decision={
    'created':'2026-10-16 ET',
    'classification':'INDEPENDENT_INTEGRITY_PASS_WITH_FOUR_CONDITIONAL_MATH_GOALS_AND_TWO_TIMEOUTS',
    'source_commit':metadata['source_commit'],'raw_root':metadata['raw_root'],
    'frozen_packet':packet_pins,'auditor':pin(HERE/'cold-auditor-v6.py'),
    'passive_metadata':pin(metadata_path),'producer_result':metadata['result_pin'],
    'independent_parent_static_reviews':reviews,
    'actual_lane':metadata['lane'],'actual_guards':metadata['guard'],
    'producer_complete':True,'cold_integrity_complete':True,
    'checks':metadata['checks'],'passive_elapsed_seconds':metadata['elapsed_seconds'],
    'raw_files':metadata['raw_files'],'raw_bytes':metadata['raw_bytes'],'raw_pre_post_equal':True,
    'source_and_helper_count':metadata['source_and_helper_count'],
    'source_consumer_receipts':metadata['source_consumers'],
    'selected_runtime_physical_pins':len(metadata['runtime_pins']),
    'selected_runtime_source_files':len(metadata['selected_runtime_sources']),
    'source_compiler_context':'Exact frozen fb197 source/helpers/consumers, fresh canonical inputs and original anchors/provenance, selected physical tools/WP artifacts/config, full standard support/driver surfaces, libclang and all 1983 selected headers checked. Compiler use-time binding is retained producer evidence; continuous immutability is not claimed.',
    'normal_engine_policy':'Unchanged normal engine and native reader, Typed+Var+Machine with real arithmetic, complete configured three-prover portfolio, no cache, RTE/init/smoke/status-all flags. Six global lemmas have six ordinary goals, twelve registered properties, no generated smoke goals and header-only property CSVs; this does not cover a caller C body.',
    'ordinary_goals':6,'registered_properties':12,'generated_smoke_goals':0,'property_csv_data_rows':0,
    'leaves':metadata['leaves'],'conditional_math_proven_goal_ids':proven,
    'unproven_goal_ids':pending,'all_six_proven':False,
    'materialized_tasks':len(tasks),'materialized_tasks_by_goal':dict(Counter(t['id'] for t in tasks)),
    'actual_solver_submission_count':None,'submitted_byte_attestation':False,
    'all_actual_task_goals_source_equivalent':True,
    'goal_source_normalizations':[
        {'labels':list(k),'tasks':v} for k,v in Counter(tuple(t['normalization']) for t in tasks).items()],
    'source_definition_instances':sum(len(t['source_definitions']) for t in tasks),
    'source_definition_policy':'All actual definitions match independently transcribed source. Only P_t25_frame admits exact De Morgan/order-negation form. The positive-state function is fully unfolded in matching source-goal variants; only that unused definition is absent from positive SMT closure. Complete printed common source declarations remain checked.',
    'source_goal_policy':'The full positive source antecedent is retained. forall b with b=next(before) is eliminated by capture-free defining-equality substitution, retaining all nine other antecedents. Cleanup scalar-branch reduction uses the retained 0<n premise. No actual goal or raw source was changed.',
    'non_goal_assertion_instances':sum(t['non_goal_assertions'] for t in tasks),
    'unique_non_goal_assertions':len({a['sha256'] for t in tasks for a in t['support_attribution']}),
    'unmatched_support_assertions':0,
    'prior_support_primary_source_attribution_pins':metadata['prior_support_source_attribution_pins'],
    'support_policy':'All 770 non-goal assertion instances match 46 exact prior primary-source-attributed standard/Heap support formulas. No old goal/proof, desired or sibling theorem is imported as an assertion. The prospective new false-array recognition was not needed for this actual run.',
    'complete_common_task_and_import_audit':True,
    'direct_import_roots':metadata['direct_import_roots'],
    'import_modules':len(metadata['import_source_closure']),
    'heap_module_has_axioms_or_lemmas':False,
    'scientific_execution_by_this_audit':False,
    'remote_execution_scope':'Stdlib-only in-place metadata reading plus fixed read-only Git. No compiler, native helper, verifier, solver or project import; no raw C/AST/SMT transferred or raw files written.',
    'observer_attempt_history':attempts,
    'unexecuted_observer_versions':[2],
    'observer_refusals_preserved':True,
    'first_refusal_diagnosis':'Original actual V1 refusal did not retain open-event values. A local read-only Git reproduction identified its stdin FIFO wrapper (integer fd 4, mode w, flags 16778753). Reviewed V3 omits unused stdin and narrowly permits writable FIFO descriptors only during fixed read-only Git; pathname and regular-file writes including mutation flags remain refused.',
    'root_adoption_performed':False,'four_goal_conditional_reuse_eligible_for_root_decision':True,
    'all_six_acceptance':False,'universal_proof_setup_attested':False,
    'source_typed_bridge_established':False,'current_constructor_body_record_admitted':False,
    'body_acceptance':False,'caller_acceptance':False,'public_proof_record_created':False,
    'ticket25_complete':False,
    'remaining_dependencies':['Both positive gluing duties remain unproven under the actual normal timeout outcomes.',
        'Current constructor body record and complete actual caller ordinary proof remain pending; retained conditional model math is not an opaque source premise.',
        'Source allocation/freshness/validity/freeability/frame/release and Typed/lifetime bridge remain explicit TCB/dependency gates; no stronger public caller requires were introduced.'],
    'recommendation':'Retain this complete partial result. Root may adopt only the first four duties as conditional mathematical evidence under the declared translation/support/solver TCB. Do not admit the complete six-duty profile or any source/body/caller/public proof record.',
}
decision_path=EVIDENCE/'t25-closed-lifetime6-independent-cold-decision-20261016.json'
assert not decision_path.exists();decision_path.write_text(json.dumps(decision,sort_keys=True,indent=2)+'\n')
review='''# Independent six-duty cold review — 2026-10-16 ET

Integrity PASS; all-six mathematical proof acceptance remains false. The exact fb197c5d producer on mbit10 node 0, generation 611, completed normally. Four duties have normal `proven` verdicts: `receiver.entry`, `constructor.frame`, `buffer.identity`, and `zero.cleanup`. `positive.exit_image` and `positive.cleanup` each remain `not_proven` / `timeout`, retaining attempts `[timeout, unknown, timeout]`.

The independent passive auditor checked 209,460 conditions in 16.195 seconds. All 364 raw files (23,879,857 bytes) matched before/after; source, canonical inputs, original anchor/provenance, compiler/header context, selected tools and runtime sources, native reader, consumer trees and physical files, launch/guard/lane metadata, and the producer artifact manifest closed exactly. Both 1,624-file consumer receipts cover 1,338,047,287 bytes and match. Producer outer exit was 0 in 222.556 seconds, peak RSS 1,066,860,544 bytes, without guard timeout or OOM.

All six ordinary goals, twelve registered properties, header-only CSVs, common exports and all 24 materialized SMT tasks were retained. Twelve first-four tasks match literal source formulas; six exit-image tasks match exact source positive-state definition unfolding and capture-free universal fresh-buffer equality substitution; six cleanup tasks additionally reduce the scalar branch using the retained positive antecedent. All nine other positive antecedents remain present. Every actual source definition is checked; the only source form normalization is De Morgan plus exact order negation in `P_t25_frame`. The positive SMT census omits only the fully expanded, unreferenced positive-state function. Complete printed source declarations remain checked.

All 770 non-goal assertion instances match 46 exact primary-source-attributed standard/Heap support formulas. No unmatched support, desired/sibling theorem, or opaque old proof is present. All 30 actual import modules close; the project Heap module has definitions and no axiom/lemma declarations. The unchanged normal engine flags and native-reader outcomes are preserved. Materialized task count is not an attested solver submission count, and proof checking remains conditional on the declared translation, standard-support and solver TCB.

The auditor is stdlib/read-only Git only. No project import, compiler, native helper, verifier, solver, or scientific rerun occurred; no raw C/AST/SMT was transferred or raw file written. V1, V3, V4, and V5 passive observer refusals are preserved; V2 was never executed. Each executed successor had an independent parent source review. The fixes concern Git pipe classification and exact source-equivalent term/census representations, and never alter producer outcomes or source formulas.

The complete six-duty profile is not accepted. Root may consider only the four proven duties as conditional mathematical evidence. Source/Typed, allocator/free/release/lifetime correspondence, current constructor body admission, complete caller ordinary proof, public proof record, and ticket completion remain pending. Retained constructor/destructor/model evidence is not imported as an opaque premise.

Evidence: `t25-closed-lifetime6-passive-cold-metadata-v6-20261016.json` SHA-256 `64af07b2da9ca8c2137041dd59e6c0f5d6fc31f2c064c62d5427b4a756e08ed5` (462,006 bytes). Auditor SHA-256 `9a373fe5a32bd11c36149d65f1470c98def984dec10c35465ac7d198f7f8651b`. Parent V6 source-review receipt SHA-256 `562e09cf0f0ec7fddb3fde3b34a43f4423979467624f14fb69ceb4ab966c1bad`. Producer result SHA-256 `d91ab4ab367a08cd0387d1fae18d9e207b09d9a0971c90ba0c3f9a5a4d7043df`. The accompanying independent decision JSON pins every review and retained refusal.
'''
review_path=EVIDENCE/'t25-closed-lifetime6-independent-cold-review-20261016.md'
assert not review_path.exists();review_path.write_text(review)
print(json.dumps({'decision':pin(decision_path),'review':pin(review_path)},indent=2))
