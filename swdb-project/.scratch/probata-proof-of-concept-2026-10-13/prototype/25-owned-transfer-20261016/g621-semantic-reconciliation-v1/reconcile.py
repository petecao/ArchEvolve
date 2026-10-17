"""2026-10-16 ET. Offline complete G621 encoding/declaration interpretation.

Joins the unchanged full cold capture and once-admitted encoding observations.
It performs no query, tool run, raw mutation or production admission.
"""
import collections
import hashlib
import json
import sys
from pathlib import Path

POC = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
V3 = HERE.parent/'cold-g621-encoding-v3'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def need(value, label):
    if not value:
        raise ValueError(label)


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def read_pinned(name, expected):
    path = POC/'evidence'/name
    need(pin(path)['sha256'] == expected, 'exact retained capture: '+name)
    return json.loads(path.read_bytes())


def reconcile(old, actual, context, semantic):
    need(old['raw_pre_post_equal'] and actual['all22_selected_inputs_pre_post_equal']
         and actual['selected_pre_post_equal'] and actual['tasks_observed'] == 20, 'complete original/raw and selected input identity')
    need(old['source_commit'] == actual['source_commit'] == 'd7f685c6fdbd7ff776eb1eaccc40099a2c48dc08', 'original exact source lineage')
    need(actual['source_theory_sha256'] == 'a2c295d2c6720a9c8c522f05e19723c2d2d2a32b63f9b198aab03f195269e4b6', 'complete Owners source')
    old_tasks = {(row['id'], row['artifact']['relative']): row for row in old['materialized_tasks']}
    need(len(old_tasks) == len(actual['tasks']) == 20, 'no missing/duplicate whole retained task')
    expected_declarations = {
        'div1': semantic['one']('(declare-fun div1 (Int Int) Int)'),
        'mod1': semantic['one']('(declare-fun mod1 (Int Int) Int)'),
        'state': semantic['one']('(declare-datatypes ((state 0)) (((stateqtmk (active (Array Int Bool)) (backing (Array Int Int))))))'),
        'fc': semantic['one']('(declare-fun fc () (Array Int Bool))'),
        'fc1': semantic['one']('(declare-fun fc1 () (Array Int Int))'),
    }
    declaration_by_hash = {digest(value): name for name, value in expected_declarations.items()}
    need(len(declaration_by_hash) == 5, 'independent exact five complete typed declarations')
    roots = old['import_source_closure']
    need(roots['vector_owned_state.Owners']['proposition_declarations'] == [] and
         roots['vector_owned_state.Owners']['file']['sha256'] == actual['source_theory_sha256'], 'source module contains definitions only')
    families = {}
    for name, row in roots.items():
        for kind, label in row.get('proposition_declarations', []):
            families.setdefault(label, []).append({'module': name, 'kind': kind,
                'file': row['file'], 'module_body_sha256': row['module_body_sha256']})
    support, rows, unique_ids = {}, [], collections.Counter()
    observed_task_keys = set()
    for task in actual['tasks']:
        key = (task['id'], task['artifact']['relative'])
        need(key in old_tasks and key not in observed_task_keys and task['artifact'] == old_tasks[key]['artifact'], 'whole actual retained task owner and hash')
        observed_task_keys.add(key)
        unique_ids[task['id']] += 1
        need(task['record_schema']['matching'] and task['record_schema']['constructor'] == 'stateqtmk', 'this task exact single product schema')
        need(task['goal_equivalent_after_local_schema_check'] and task['first_canonical_goal_difference'] is None
             and task['goal_canonical_sha256'] == task['expected_goal_canonical_sha256']
             == digest(semantic['canon'](semantic['source_goal'](task['id']))), 'complete actual source goal after reviewed identities')
        declarations = []
        for declaration in task['declaration_census']:
            role = declaration_by_hash.get(declaration['sha256'])
            need(role is not None, 'unattributed complete typed declaration')
            declarations.append(role)
        need(len(set(declarations)) == len(declarations)
             and set(declarations) == ({'div1', 'mod1', 'state', 'fc', 'fc1'} if task['id'] == 'empty.valid'
                                       else {'div1', 'mod1', 'state'}), 'complete per-goal declaration census; no extra sort/function')
        for definition in task['definitions']:
            if definition['name'] == 'empty':
                need(task['id'] == 'empty.valid' and task['empty']['matching']
                     and task['empty']['definition_count'] == 1 and task['empty']['ignored_argument']
                     and task['empty']['integer_dummy_signature_matches_source']
                     and task['empty']['form_sha256'] == definition['form_sha256']
                     and definition['form_sha256'] == '9d76bd048e79654661c1510e3cdcc92ad29e990c38287a182edd69cfd34e2bc8',
                     'independent complete empty constructor/type/ignored-argument interpretation')
                need({row['role'] for row in task['constant_maps']} == {'false', 'zero'} and
                     all(row['declaration_exact'] and row['full_quantified_formula_matches']
                         and row['matching_assertion_count'] == 1 for row in task['constant_maps']),
                     'both full typed quantified constant-map formulas, no conditional or missing map')
            else:
                need(definition['equivalent_after_local_schema_check'] and definition['source_role'] is not None,
                     'every other complete source/standard definition matched')
        need(task['unresolved'] == ([{'kind': 'definition', 'name': 'empty',
             'sha256': '9d76bd048e79654661c1510e3cdcc92ad29e990c38287a182edd69cfd34e2bc8'}]
             if task['id'] == 'empty.valid' else []), 'no hidden unresolved term/support/goal')
        for assertion in task['support_assertions']:
            key_sha = assertion['sha256']
            if assertion['scoped_complete_constant_map_match']:
                need(task['id'] == 'empty.valid' and key_sha in context['constant_map_support_hashes'].values(), 'constant-map definitional extension scoped to empty')
                attribution = {'kind': 'source empty constant false/zero total map',
                    'basis': 'fresh fc/fc1 typed constants with exact full universal selector equations; total constant maps supply a conservative extension witness'}
            else:
                need(assertion['prior_standard_attribution_present'] and key_sha in context['primary_standard_support'], 'known exact complete standard assertion hash')
                prior = context['primary_standard_support'][key_sha]
                labels = sorted({row['label'] for row in prior})
                need(all(label in families for label in labels), 'each selected standard support has a complete primary module proposition family')
                attribution = {'kind': 'selected standard arithmetic/Qed foundation under explicit source-to-driver TCB',
                    'prior_exact_task_attribution': prior,
                    'primary_source_proposition_families': {label: families[label] for label in labels},
                    'formula_translation_independently_reproved': False}
            if key_sha not in support:
                support[key_sha] = {'instances': 0, 'attribution': attribution}
            need(support[key_sha]['attribution'] == attribution, 'stable support role across every context')
            support[key_sha]['instances'] += 1
        rows.append({'id': task['id'], 'artifact': task['artifact'],
                     'full_goal_canonical_sha256': task['goal_canonical_sha256'],
                     'full_goal_source_equivalent': True, 'declaration_roles': declarations,
                     'all_source_definitions_matched': True,
                     'empty_interpretation_joined': task['id'] == 'empty.valid',
                     'support_assertion_count': len(task['support_assertions']),
                     'original_capture_flags_unchanged': True})
    need(set(unique_ids) == set(semantic['GOALS']) and set(unique_ids.values()) == {2}, 'all ten original goals, two physical retained copies each')
    need(len(old['leaves']) == 10 and all('valid' in row['native_results'] for row in old['leaves']), 'all ten actual native Valid results retained')
    return {'tasks': rows, 'support': support, 'declaration_signatures': expected_declarations,
            'goals': list(semantic['GOALS']), 'type_interpretation': {
                'Owners.state': 'monomorphic product (Int->Bool) x (Int->Int); one constructor with exactly active/backing selectors; every task independently checked',
                'maps': 'total mathematical functions interpreted by standard SMT arrays and select/store under the pinned Int/Map/Why3 driver foundation TCB',
                'empty': 'stateqtmk(fc,fc1), each complete universal selector formula forces false/zero maps; ignored Int dummy matches actual source, never unit coercion',
                'abs': 'exact pinned total Int->Int definition and source module, no name-only whitelist',
                'div_mod': 'exact declared Int x Int -> Int operations used only under inventoried selected ComputerDivision/Qed standard theory TCB'},
            'relative_consistency_argument': old['consistency'], 'import_source_closure': roots,
            'unknown_items_after_explicit_interpretation': [],
            'all_capture_false_flags_preserved': True,
            'independent_root_scientific_acceptance_required': True}


def main():
    attempts = []
    def audit(event, args):
        if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec', 'os.fork', 'ctypes.dlopen', 'socket.connect'}:
            attempts.append(event)
            raise RuntimeError('offline reconciliation forbids child/native/network')
    sys.addaudithook(audit)
    old = read_pinned('t25-owned-transfer10-cold-v3-root-stdout-20261016.json',
                     'cf62bd6a0bf73a171fc8e7ddd68f32c1bb38dcc4f7e8a055264cbc6a2f8e5f5e')
    actual_path = POC/'evidence/t25-owned-transfer10-encoding-v3-actual-stdout-20261016.json'
    actual = json.loads(actual_path.read_bytes())
    execution_path = POC/'evidence/t25-owned-transfer10-encoding-v3-actual-execution-20261016.json'
    execution = json.loads(execution_path.read_bytes())
    need(pin(actual_path) == execution['actual']['stdout'] and execution['postflight_passed']
         and execution['expected_metadata_exit2'], 'once-admitted actual capture and postflight')
    context = json.loads((V3/'context.json').read_bytes())
    semantic = {'__name__': '_g621_pure_interpretation'}
    for name in ('semantic_terms.py', 'encoding_probe.py'):
        exec(compile((V3/name).read_bytes(), str(V3/name), 'exec'), semantic)
    joined = reconcile(old, actual, context, semantic)
    result = {'date': '2026-10-16 ET', 'classification': 'COMPLETE_CONDITIONAL_OWNERSHIP10_INTERPRETATION_FOR_ROOT_REVIEW',
              'actual_capture': pin(actual_path), 'actual_execution': pin(execution_path),
              'full_original_cold_capture': pin(POC/'evidence/t25-owned-transfer10-cold-v3-root-stdout-20261016.json'),
              'encoding_context': pin(V3/'context.json'), 'source_interpretation': joined,
              'counts': {'original_goals': 10, 'materialized_tasks': 20,
                         'support_instances': sum(row['instances'] for row in joined['support'].values()),
                         'distinct_supports': len(joined['support']), 'typed_declarations': 5,
                         'bookkeeping_empty_definition_rows_reconciled': 2},
              'scope': 'Ten conditional unbounded mathematical Owners registry duties, exact historical d7 source and G621 proofs only. No original C member/source ownership/Heap/Typed/lifetime/caller/default/public-record admission.',
              'TCB': ['Selected complete standard Int/Real/Map/Qed module declarations and source-to-driver proposition splitting/renaming',
                      'Why3 record/array and built-in mathematical SMT Int/Bool interpretation',
                      'Normal compiler/VC generation and solver soundness, source-to-binary/loader/OS and between-check boundaries retained from actual full cold capture',
                      'Printed task bytes are materialized evidence, not independently intercepted actual solver-consumed bytes'],
              'no_empirical_consistency_from_zero_smokes': True, 'no_new_axiom_or_sibling_theorem_premise': True,
              'native_tool_proof_query_rerun': False, 'remote_raw_mutation': False,
              'external_attempts': attempts, 'scientific_acceptance': False,
              'source_body_Heap_Typed_caller_default_or_public_acceptance': False}
    output = POC/'evidence/t25-owned-transfer10-complete-interpretation-v2-20261016.json'
    output.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'interpretation': pin(output), 'counts': result['counts'], 'attempts': attempts}))


if __name__ == '__main__':
    main()
