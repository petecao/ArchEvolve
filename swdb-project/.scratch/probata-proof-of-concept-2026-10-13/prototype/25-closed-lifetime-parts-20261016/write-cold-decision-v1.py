"""Write independent local decision from the reviewed passive metadata."""
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

path=EVIDENCE/'t25-closed-lifetime23-passive-cold-metadata-v1-20261016.json'
x=json.loads(path.read_text())
assert pin(path)['sha256']=='be868ec0f83e940da960da859f62f5486095b0ff0704dbfff7f53fd142d1f2ca'
assert x['classification']=='PASS_CONDITIONAL_23_SOURCE_MATH_COLD' and x['all_23_normal_producer_proven']
assert len(x['leaves'])==23 and all(r['normal_verdict']=='proven' and r['passed'] and 'valid' in r['native_results'] for r in x['leaves'])
assert x['raw_pre_post_equal'] and not x['unmatched_supports']
tasks=x['materialized_tasks']
refs=[EVIDENCE/'t25-closed-lifetime23-root-entry-review-v1-20261016.json',
      EVIDENCE/'t25-closed-lifetime23-cold-observer-parent-static-review-v1-20261016.json',
      EVIDENCE/'t25-closed-lifetime23-cold-observer-preparation-v1-20261016.json',
      EVIDENCE/'t25-closed-lifetime6-independent-cold-decision-20261016.json']
decision={
    'created':'2026-10-16 ET','classification':'INDEPENDENT_PASS_CONDITIONAL_23_CONJUNCTION_MATH',
    'source_commit':x['source_commit'],'raw_root':x['raw_root'],
    'observer':pin(HERE/'cold-observer-v1.py'),'passive_metadata':pin(path),
    'source_goal_transcription':pin(HERE/'cold-goals-v1.py'),
    'reviews_and_retained_original_timeout_decision':[pin(p) for p in refs],
    'frozen_packet':[pin(HERE/'inert-04af74c1-public-v1'/name) for name in ('packet.json','entry.py','expected.json','root-command.json')],
    'producer_result':x['result_pin'],'actual_lane':x['lane'],'actual_guards':x['guard'],
    'producer_complete':True,'all23_normal_mathematical_goals_proven':True,
    'checks':x['checks'],'passive_elapsed_seconds':x['elapsed_seconds'],
    'raw_files':x['raw_files'],'raw_bytes':x['raw_bytes'],'raw_pre_post_equal':True,
    'source_and_helper_count':x['source_and_helper_count'],
    'source_consumer_receipts':x['source_consumers'],
    'physical_selected_runtime_pins':len(x['runtime_pins']),
    'selected_runtime_source_files':len(x['selected_runtime_sources']),
    'identity_closure':'Exact frozen source/helpers/consumer tree+physical bytes, full fresh original anchors/provenance, canonical35files with only one host certificate leaf portably normalized, selected physical tools/WP artifacts/config/full support and drivers, compiler/libclang and all1983headers, source-after, guards/lane and artifact manifest checked. Continuous runtime immutability is not claimed.',
    'ordinary_goals':23,'registered_properties':46,'generated_smoke_goals':0,'CSV_data_rows':0,
    'internal_qed_inventory_only':[r['id'] for r in x['leaves'] if r['internal_qed_inventory_only']],
    'internal_qed_policy':'Exact native result valid/passed, ordinary Qed success1, complete sole source-owned registered check lemma and property closure, no missing external task, and exact canonical source formula. No external SMT task or solver submission is fabricated; Qed remains declared translation/proof TCB.',
    'leaves':x['leaves'],'native_attempt_arrays':[{'attempts':k,'goals':v} for k,v in Counter(str(r['native_results']) for r in x['leaves']).items()],
    'materialized_tasks':len(tasks),'tasks_by_goal':dict(Counter(t['id'] for t in tasks)),
    'materialized_task_count_is_submission_count':False,'submitted_byte_attestation':False,
    'source_goal_normalizations':[{'labels':list(k),'tasks':v} for k,v in Counter(tuple(t['normalization']) for t in tasks).items()],
    'source_definition_instances':sum(len(t['source_definitions']) for t in tasks),
    'source_reference_reconstruction':x['source_reference_equivalence'],
    'same_original_positive_formulas_conditionally_reconstructed':True,
    'reconstruction_policy':'Exact14exit+9cleanup same-premise conjunctions, fresh universally scoped indices, independently checked source definitions and original reference statements, and explicit final/scalar witnesses reconstruct the original two logical formulas. Their prior six-profile native timeout outcomes are preserved; no opaque sibling theorem or old proof is imported.',
    'original_six_profile_timeouts_changed':False,
    'non_goal_assertion_instances':sum(t['non_goal_assertions'] for t in tasks),
    'unique_non_goal_assertions':len({a['sha256'] for t in tasks for a in t['support_attribution']}),
    'unmatched_support_assertions':0,'prior_primary_support_attribution_pins':x['prior_support_source_attribution_pins'],
    'support_policy':'All1978actual non-goal assertion instances match45exact prior primary-source-attributed standard/Heap support formulas. No desired/sibling theorem or old proof is imported. Project Heap module has definitions and no axiom/lemma declarations.',
    'direct_import_roots':x['direct_import_roots'],'actual_import_modules':len(x['import_source_closure']),
    'normal_policy':'Unchanged normal engine/reader and complete configured portfolio, cache none, real arithmetic with pinned Typed/Var/Machine defaults, RTE/init/smoke/status-all. Global mathematical lemmas do not cover an actual C caller body.',
    'scientific_execution_by_this_audit':False,'project_imports':0,'compiler_native_verifier_solver_reruns':0,
    'remote_scope':'Stdlib-only passive in-place metadata plus fixed read-only Git, after exact root settlement and independent static review; no raw C/AST/SMT transfer or raw writes.',
    'root_adoption_performed':False,'conditional_math_adoption_eligible_for_root_decision':True,
    'source_typed_bridge_established':False,'current_constructor_body_record_admitted':False,
    'body_acceptance':False,'caller_acceptance':False,'public_proof_record_created':False,
    'universal_proof_setup_attested':False,'ticket25_complete':False,
    'remaining_gates':['Concrete complete scientific bundle binding and source operational interpretation review.',
        'Corrected source rule including original24/9/13census, alias initialization, automatic administrative storage, and live-memory/dead-history observation.',
        'Current source/body/caller/public-record and allocator/free/release/lifetime correspondence admission under an explicitly pinned TCB; conditional math alone does not supply them.'],
    'recommendation':'Root may adopt all23 source-bound mathematical leaves and their exact logical reference reconstruction under the declared translation/Qed/support/solver TCB. Preserve the old compound timeout outcomes. Do not infer source/Typed/body/caller/public-record or ticket completion.',
}
out=EVIDENCE/'t25-closed-lifetime23-independent-cold-decision-20261016.json';assert not out.exists()
out.write_text(json.dumps(decision,sort_keys=True,indent=2)+'\n')
review='''# Independent 23-leaf cold review — 2026-10-16 ET

PASS for conditional mathematical evidence. All 23 normal check-lemma goals are proven in the exact 04af74c1 producer, mbit10 node 1 generation 633, ended 2026-10-16T19:37:33Z. Twenty-one native goal arrays are `[valid]`; one retains `[timeout, valid]` and one `[timeout, unknown, valid]`. Earlier unsuccessful attempts are preserved. This is not a source/body/caller proof.

The reviewed passive observer completed on its first execution: 547,580 checks in 31.098 seconds, all 579 raw files / 26,032,027 bytes unchanged. All 335 selected source/helper pins, both 1,625-file consumer closures (1,338,051,679 bytes each), original full fresh anchor/provenance, all canonical files, current source/compiler/header context, selected tools/runtime/imports, actual source-after and producer artifact manifest closed exactly. Actual outer exit was 0 in 168.335 seconds, peak RSS 556,703,744 bytes, with no guard timeout/OOM. All producer outcomes are retained.

The complete native/ordinary census is 23 ordinary goals and 46 registered properties, no generated smoke goals and header-only property CSVs. `positive.exit_image.private.receiver` is legitimately internal-Qed-only, with exact native valid/passed and Qed success, the exact canonical source lemma, no missing external task and no fabricated SMT export. The other goals have 50 materialized tasks in total, all checked against independent full source formulas. Materialized task count is not an attested submission count.

Every leaf keeps the exact complete positive source antecedent and fresh index scope. The independently transcribed fourteen exit leaves and nine cleanup leaves match the complete original reference statements and explicit final/scalar witnesses. Conjunction distribution, fresh universal indices and checked source definitions reconstruct the same original logical targets. Only source-derived transformations are used: exact positive-state definition expansion, capture-free universal fresh-buffer equality substitution, the retained positive scalar branch, integer additive zero, and De Morgan/order negation in the source frame definition. All other antecedents/conclusions survive. No desired/sibling theorem or old accepted proof is an assertion.

All 1,978 non-goal assertion instances match 45 exact previously primary-source-attributed standard/Heap support formulas, with zero unmatched support. The complete 30-module import closure is retained; the project Heap module has definitions and no axioms or lemmas. Normal complete engine flags and native-reader outcomes are unchanged. The result remains conditional on the declared translation, Qed, standard-support and solver TCB.

No compiler, native helper, verifier, solver, project import or scientific rerun occurred in this audit. No raw C/AST/SMT was transferred or raw file written. The original two compound six-profile timeout outcomes remain unchanged; the new exact conjunction evidence supports a separate logical reconstruction and does not rewrite historical results.

Root may adopt the 23 mathematical leaves and their conditional reference reconstruction. Concrete scientific evidence binding and the corrected source operational rule remain separate gates. Source/Typed, current constructor body, allocator/free/release/lifetime correspondence, caller/public-record acceptance and ticket completion remain false.

Passive metadata SHA-256: `be868ec0f83e940da960da859f62f5486095b0ff0704dbfff7f53fd142d1f2ca` (962,942 bytes). Observer SHA-256: `d9cee2627a08bb08341ea0702c8e4003acc4194914327c56a976182446bc0161`. Independent parent static review SHA-256: `d4d63b72af96dfbecab974d773b2dbe4a1ee8560ab2338ad12b2fc92836e5c36`. The accompanying decision JSON pins the frozen packet, all leaves, source reconstruction, runtime and prior timeout decision.
'''
review_path=EVIDENCE/'t25-closed-lifetime23-independent-cold-review-20261016.md';assert not review_path.exists()
review_path.write_text(review)
print(json.dumps({'decision':pin(out),'review':pin(review_path)},indent=2))
