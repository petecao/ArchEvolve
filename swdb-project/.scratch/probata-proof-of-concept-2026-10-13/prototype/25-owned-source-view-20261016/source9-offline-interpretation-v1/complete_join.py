"""2026-10-16 ET. Complete retained source9 syntax/support join, without tools.

This joins immutable observations. It never runs a solver or establishes the
original C/Typed/lifetime interpretation. Source-to-driver standard proposition
translation and the historical runtime boundaries remain explicit TCB.
"""
import collections
import hashlib
import json
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
ATTEMPTS = []


def audit(event, args):
    if event.startswith(('subprocess.', 'socket.', 'os.exec', 'os.spawn',
                         'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        ATTEMPTS.append(event)
        raise RuntimeError('offline complete join forbids child/native/network')


sys.dont_write_bytecode = True
sys.addaudithook(audit)


def need(value, label):
    if not value:
        raise ValueError(label)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def pin(path):
    raw = path.read_bytes()
    need(path.is_file() and not path.is_symlink(), 'physical regular local input')
    return {'path': str(path.resolve()), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


PINS = {
    'cold': ('evidence/t25-owned-source9-cold-v1-actual-stdout-20261016.json',
             '2ec440bcc9c282c3dfeec44f98c79a6861c6882c19ad8b2cb8913b8880dc1e9c'),
    'capture': ('evidence/t25-owned-source9-math-ast-v3-actual-stdout-20261016.json',
                '9924e02166c0613047bf750b31a06508b67d5eb8853fec79a59c8f1d926b5a72'),
    'execution': ('evidence/t25-owned-source9-math-ast-v3-actual-execution-20261016.json',
                  '9235ac6f18cfaa595052755255268dd16f2f12881aeb92d06ed30269b7c39421'),
    'context': ('prototype/25-owned-transfer-20261016/cold-g621-encoding-v3/context.json',
                '03f9f790e108557d7f63766a4150c9714f8020f3142145998ca269d1ba4c613c'),
    'accepted_standard_basis': ('evidence/t25-owned-transfer10-complete-interpretation-v2-20261016.json',
                              'e872b1f96c961a2516c4ef39b9baae823b121aa253a11a9eeef08530596671ab'),
    'standard_basis_root_decision': ('evidence/t25-owned-transfer10-root-scoped-acceptance-20261016.json',
                                   'a7d02b87369485970533a96766521fc858a74509e125f00632a5cb5dddbf3ddb'),
    'own_join': ('evidence/t25-owned-source9-owners-effects-interpretation-v1-20261016.json',
                 '31f1b3f6ba45abb780f97cb4a281e25f5775a2e3a745e6211dedad93fffbcf69'),
}

# These four complete CVC5 renderings were not used by G621's selected tasks.
# Independently transcribed from the same pinned complete primary sources:
# int.Abs line54; int.ComputerDivision lines217-223; Qed lines35-39.
# Keep each complete antecedent and all four remainder sign cases.
ADDITIONAL_STANDARD = {
    '92ed3b6387a2ea7adfb0281282ed3f10092b199ffe0c64ac751db7f08385dad7': (
        'int.Abs', 'lemma', 'Abs_le',
        '(forall ((x Int) (y Int)) (= (<= (abs1 x) y) (and (<= (- y) x) (<= x y))))'),
    'b10a675182a54bd3e05baba0fae2deec3825802ec0c246d6ff6211f8f382cdf6': (
        'int.ComputerDivision', 'axiom', 'Div_bound',
        '(forall ((x Int) (y Int)) (=> (and (<= 0 x) (< 0 y)) (and (<= 0 (div1 x y)) (<= (div1 x y) x))))'),
    '54870e5c89b533678e220be22537d8796ab107f992c8d45a7cf79a926108d378': (
        'int.ComputerDivision', 'axiom', 'Mod_bound',
        '(forall ((x Int) (y Int)) (=> (not (= y 0)) (and (< (- (abs1 y)) (mod1 x y)) (< (mod1 x y) (abs1 y)))))'),
    'f0128a61c0627c057a80014c6828d71960dea19dc00202eeb22d7fea7964bc2f': (
        'frama_c_wp.qed.Qed', 'lemma', 'cmod_remainder',
        '(forall ((n Int) (d Int)) (and '
        '(=> (<= 0 n) (=> (< 0 d) (and (<= 0 (mod1 n d)) (< (mod1 n d) d)))) '
        '(=> (<= n 0) (=> (< 0 d) (and (< (- d) (mod1 n d)) (<= (mod1 n d) 0)))) '
        '(=> (<= 0 n) (=> (< d 0) (and (<= 0 (mod1 n d)) (< (mod1 n d) (- d))))) '
        '(=> (<= n 0) (=> (< d 0) (and (< d (mod1 n d)) (<= (mod1 n d) 0))))))'),
}


def interpret_commands(commands, ident, context, semantic, heap, own, standard_basis, roots):
    """Consume all mathematical commands; unknown declarations/support refuse."""
    need(all(isinstance(row, list) and row and row[0] in {
        'declare-sort', 'declare-fun', 'declare-const', 'declare-datatypes',
        'declare-datatype', 'define-fun', 'assert'} for row in commands), 'closed math command heads')
    ctx = heap['task_context'](commands, semantic['one'], semantic['canon'])
    heaps = heap['reconcile_heap_definitions'](commands, ctx, semantic['one'], semantic['canon'])
    owners = own['reconcile_task'](commands, ident, ctx, semantic['one'],
                                  semantic['canon'], heap['normalize_source_primitives'])
    expected_abs = semantic['one']('(define-fun abs1 ((x Int)) Int (ite (<= 0 x) x (- x)))')
    remaining = owners['unhandled_complete_definitions']
    heap_names = {row['name'] for row in heaps}
    need(len(heap_names) == len(heaps), 'unique interpreted Heap definitions')
    abs_rows = [row for row in remaining if row[1] not in heap_names]
    need(abs_rows == [expected_abs] and digest(expected_abs) ==
         context['standard_abs_source']['expected_SMT_definition_sha256'], 'one exact complete typed total abs definition')
    need({row[1] for row in remaining} == heap_names | {'abs1'} and
         len(remaining) == len(heaps)+1, 'no extra or unhandled complete definition')
    need(sum(row[0] == 'define-fun' for row in commands) ==
         len(heaps)+owners['own_definition_count']+1, 'complete disjoint definition coverage')
    support, standard_count, sum_count = [], 0, 0
    sum_hashes = {digest(row[1]) for row in ctx['sum_and_map_support']}
    for row in owners['support_assertions_not_consumed_here']:
        need(row[0] == 'assert' and len(row) == 2, 'complete support assertion shape')
        key = digest(row[1])
        if key in sum_hashes:
            attribution = {'kind': 'closed complete cell/constant-map definitional encoding',
                           'context_mode': ctx['mode']}
            sum_count += 1
        else:
            need(key in context['primary_standard_support'] and
                 (key in standard_basis or key in ADDITIONAL_STANDARD),
                 'no unknown support assertion, desired goal or sibling premise')
            if key in standard_basis:
                prior = standard_basis[key]['attribution']
            else:
                module, kind, label, complete_body = ADDITIONAL_STANDARD[key]
                need(semantic['canon'](row[1]) == semantic['canon'](semantic['one'](complete_body)),
                     'complete independently transcribed additional standard formula')
                primary = roots[module]
                need([kind, label] in primary['proposition_declarations'] and
                     {r['label'] for r in context['primary_standard_support'][key]} == {label},
                     'additional exact body primary source declaration')
                prior = {'kind': 'selected standard arithmetic/Qed foundation under explicit source-to-driver TCB',
                         'prior_exact_task_attribution': context['primary_standard_support'][key],
                         'primary_source_proposition_families': {label: [{'module': module, 'kind': kind,
                             'file': primary['file'], 'module_body_sha256': primary['module_body_sha256']}]},
                         'complete_primary_formula_independently_transcribed': True,
                         'formula_translation_independently_reproved': False}
            need(prior['kind'] == 'selected standard arithmetic/Qed foundation under explicit source-to-driver TCB'
                 and prior['prior_exact_task_attribution'] == context['primary_standard_support'][key],
                 'exact previously accepted complete standard assertion provenance')
            for label, families in prior['primary_source_proposition_families'].items():
                need(families and all(f['module'] in roots and
                     roots[f['module']]['file'] == f['file'] and
                     roots[f['module']]['module_body_sha256'] == f['module_body_sha256'] and
                     [f['kind'], label] in roots[f['module']]['proposition_declarations']
                     for f in families), 'same complete primary standard proposition family in source9 closure')
            attribution = prior
            standard_count += 1
        support.append({'body_sha256': key, 'attribution': attribution})
    need(len(support) == sum_count+standard_count == sum(row[0] == 'assert' for row in commands)-1,
         'every assertion consumed exactly once except original complete goal')
    return {'id': ident, 'mode': ctx['mode'], 'Heap_definitions': heaps,
            'own_definition_count': owners['own_definition_count'], 'abs_definition_count': 1,
            'full_goal_command_sha256': owners['actual_complete_goal_command_sha256'],
            'full_goal_source_equivalent': owners['source_goal_equivalent'],
            'support': support, 'standard_support_instances': standard_count,
            'sum_map_support_instances': sum_count}


def reconcile(cold, capture, context, semantic, heap, own, accepted, prior_own):
    need(cold['raw_pre_post_equal'] and capture['all29_content_and_nine_stat_pre_post_equal']
         and capture['task_count'] == 26 and capture['unique_math_commands'] == 115,
         'settled complete original capture and AST observation')
    need(cold['source_commit'] == capture['source_commit'] and cold['raw_root'] == capture['raw_root'],
         'same exact original source and raw root')
    trees = capture['deduplicated_complete_math_commands']
    need(len(trees) == 115 and all(digest(v) == k for k, v in trees.items()), 'all complete tree identities')
    old_tasks = cold['materialized_tasks']
    tasks = capture['tasks']
    need(len(old_tasks) == len(tasks) == len(prior_own['tasks']) == 26, 'complete ordered 26-task census')
    keys = [(row['id'], row['artifact']['relative']) for row in tasks]
    need(len(set(keys)) == 26 and keys == [(r['id'], r['artifact']['relative']) for r in old_tasks],
         'all original task owners/order, no duplicates')
    rows = []
    roots = cold['import_source_closure']
    basis = accepted['source_interpretation']['support']
    for task, original, previous in zip(tasks, old_tasks, prior_own['tasks']):
        need(task['artifact'] == original['artifact'] == previous['artifact'], 'original complete physical task hash')
        census = [{k: row[k] for k in ('index', 'kind', 'sha256')} for row in task['commands']]
        need(census == original['complete_command_census'] and
             digest(census) == task['complete_command_census_sha256'] and
             [row['index'] for row in census] == list(range(len(census))), 'all command order/content identities')
        math = []
        for row in task['commands']:
            if row['tree_ref'] is None:
                need(row['role'] == 'administrative' and row['kind'] in {
                    'set-logic', 'set-info', 'set-option', 'check-sat', 'get-info'}, 'only known administrative omission')
            else:
                need(row['tree_ref'] == row['sha256'] and row['tree_ref'] in trees and
                     trees[row['tree_ref']][0] == row['kind'], 'whole tree reference/head binding')
                math.append(trees[row['tree_ref']])
        need([r['sha256'] for r in task['commands'] if r['tree_ref']] ==
             previous['complete_ordered_math_command_sha256s'], 'independently reviewed Owners join task equality')
        row = interpret_commands(math, task['id'], context, semantic, heap, own, basis, roots)
        need(row['full_goal_source_equivalent'] and row['full_goal_command_sha256'] ==
             task['goal_command_sha256'] == previous['actual_complete_goal_command_sha256'] and
             task['commands'][task['goal_command_index']]['sha256'] == task['goal_command_sha256'],
             'full original goal and attribution retained')
        row['artifact'] = task['artifact']
        rows.append(row)
    need(context['standard_abs_source']['sha256'] == roots['int.Abs']['file']['sha256'],
         'complete primary int.Abs source identity')
    outcomes = [{'id': r['id'], 'native_results': r['native_results'],
                 'normal_verdict': r['normal_verdict']} for r in cold['leaves']]
    need(outcomes == capture['retained_outcomes'] and len(outcomes) == 9 and
         sum(r['normal_verdict'] == 'proven' for r in outcomes) == 8 and
         outcomes[-1] == {'id': 'swap.owner_correspondence', 'native_results': ['timeout']*3,
                         'normal_verdict': 'not_proven'}, 'eight Valid duties and original remaining timeout unchanged')
    counts = {'tasks': len(rows), 'distinct_math_commands': len(trees),
              'Heap_definition_instances': sum(len(r['Heap_definitions']) for r in rows),
              'Owners_Effects_definition_instances': sum(r['own_definition_count'] for r in rows),
              'abs_definition_instances': sum(r['abs_definition_count'] for r in rows),
              'standard_support_instances': sum(r['standard_support_instances'] for r in rows),
              'sum_map_support_instances': sum(r['sum_map_support_instances'] for r in rows)}
    need(counts == {'tasks': 26, 'distinct_math_commands': 115, 'Heap_definition_instances': 462,
                   'Owners_Effects_definition_instances': 346, 'abs_definition_instances': 26,
                   'standard_support_instances': 784, 'sum_map_support_instances': 158}, 'exact complete interpreted census')
    return {'counts': counts, 'tasks': rows, 'outcomes': outcomes, 'unknown_items': [],
            'complete_conditional_mathematical_interpretation': True,
            'independent_root_scientific_acceptance_required': True,
            'source_C_Heap_Typed_lifetime_caller_default_admission': False}


def load():
    data, observed = {}, []
    for role, (relative, expected) in PINS.items():
        path = POC/relative
        observed.append({'role': role, **pin(path)})
        need(observed[-1]['sha256'] == expected, 'exact retained input '+role)
        data[role] = json.loads(path.read_bytes())
    entry = runpy.run_path(str(HERE/'reconcile_owners_effects.py'))
    for role in ('Heap_context_V2', 'Owners_Effects_interpreter', 'accepted_typed_Boolean_alpha_syntax'):
        path, size, sha = entry['PINS'][role]
        r = pin(path)
        need(r['bytes'] == size and r['sha256'] == sha, 'exact reviewed interpreter dependency')
        observed.append({'role': role, **r})
    semantic = runpy.run_path(str(entry['PINS']['accepted_typed_Boolean_alpha_syntax'][0]))
    heap = runpy.run_path(str(HERE/'heap_reader_v2.py'))
    own = runpy.run_path(str(HERE/'owners_effects_reader.py'))
    # Recheck source statements and complete Owners result from its reviewed join.
    need(entry['main']() == data['own_join'], 'fresh full Owners source/theory/goal join reproduces retained result')
    execution = data['execution']
    need(execution['expected_metadata_exit2'] and execution['postflight_passed'] and
         execution['all29_content_and_nine_stat_pre_post_equal'] and
         execution['actual']['stdout'] == pin(POC/PINS['capture'][0]), 'once-admitted AST execution/postflight')
    for relative, module in [('share/why3/stdlib/int.mlw', 'int.Abs'),
                             ('share/frama-c/share/wp/why3/frama_c_wp/qed.mlw', 'frama_c_wp.qed.Qed')]:
        path = Path('/Users/yanrujhou/.opam/framac-33')/relative
        current = pin(path)
        source = data['cold']['import_source_closure'][module]['file']
        need(current['bytes'] == source['bytes'] and current['sha256'] == source['sha256'],
             'current local complete primary source counterpart')
        observed.append({'role': 'primary_source_counterpart_'+module, **current})
        if module == 'int.Abs':
            abs_source = data['context']['standard_abs_source']
            start, end = abs_source['module_byte_range']
            need(hashlib.sha256(path.read_bytes()[start:end]).hexdigest() ==
                 abs_source['module_body_sha256'], 'exact primary abs module byte range')
    return data, semantic, heap, own, observed


def main():
    data, semantic, heap, own, observed = load()
    result = reconcile(data['cold'], data['capture'], data['context'], semantic, heap, own,
                       data['accepted_standard_basis'], data['own_join'])
    need(not ATTEMPTS, 'no external attempts')
    return {'date': '2026-10-16 ET', 'classification': 'COMPLETE_SOURCE9_CONDITIONAL_MATH_INTERPRETATION_FOR_REVIEW',
            'inputs': observed, **result, 'TCB': data['standard_basis_root_decision']['TCB'],
            'zero_smoke_empirical_consistency_claim': False,
            'actual_solver_bytes_intercepted': False, 'formal_or_native_rerun': False,
            'external_attempts': ATTEMPTS, 'scientific_acceptance': False}


if __name__ == '__main__':
    print(json.dumps(main(), sort_keys=True, indent=2, allow_nan=False))
