"""Formal-half frame: ACSL formal halves, proof placements, concurrency and offload-only frames and
proof-semantics rules in the typed library, checked by `swdb validate` and indexed by `swdb build`.

Created: 2026-10-14 ET (Probata proof of concept ticket 20). Design: formal-verification map 16 items
2, 4 and 13, 17 item 5, 10 item 4, 15 item 5, 26 item 4, 12 item 1. Format:
docs/reference/format-v0.4-formal-frame.md.

Seam 4 (existing record seams): every case runs the public `swdb validate --library` or `swdb build`
on fixture library entries. The negative controls share one library and one validate run; each
control is its own entry (or logic-library file), and the test checks that exactly the expected
check fires for it. Frama-C cases skip when Frama-C 33.0 is missing.
"""
import copy
import json
import os
import re
import shutil
import subprocess

import pytest
import yaml

from conftest import make_records, run_swdb

PROTOTYPE = 'int fixture_unit(int *parent, int *frontier, int *dist, int *sum, int *queue, int n);'
GEM5 = {'gem5_commit': 'e4fc4afdf894f295442cef3604667a469fab8e62', 'path': 'src/mem/MAA/IF.cc',
        'lines': '193-212'}

GRAPH = """\
// Fixture logic library (Probata PoC ticket 20): one non-recursive and one primitive-recursive
// definition, and an inductive definition used only by a lemma.
predicate in_range(integer k, integer n) = 0 <= k < n;
logic integer count_pos(int *a, integer n) = n <= 0 ? 0 : count_pos(a, n - 1) + (a[n - 1] >= 0 ? 1 : 0);
inductive reach(int *next, integer a, integer b) {
  case refl: \\forall int *next, integer a; reach(next, a, a);
  case step: \\forall int *next, integer a, integer b; reach(next, next[a], b) ==> reach(next, a, b);
}
lemma reach_self: \\forall int *next, integer a; reach(next, a, a);
"""

#: logic-library files of the controls library: {name: (text, expected problem or None)}
LOGIC_CONTROLS = {
    'graph': (GRAPH, None),
    'nonrec': ('logic integer twice(integer x) = 2 * x;\n', None),
    'rec_pbad': ('predicate pbad(integer x) = !pbad(x);\n', 'primitive recursive'),
    'rec_up': ('logic integer up(integer n) = n <= 0 ? 0 : up(n + 1);\n', 'primitive recursive'),
    'rec_nobase': ('logic integer nobase(integer n) = nobase(n - 1) + 1;\n', 'primitive recursive'),
    'rec_mutual': ('logic integer ev(integer n) = n <= 0 ? 1 : od(n - 1);\n'
                   'logic integer od(integer n) = n <= 0 ? 0 : ev(n - 1);\n', 'mutual recursion'),
    'bad_axiom': ('axiomatic Ax {\n  logic integer ax_f(integer x);\n'
                  '  axiom ax_f_def: \\forall integer x; ax_f(x) == x;\n}\n', 'axiom'),
}


def frame_contract(cid, *, role=None, version='1.0', clauses=None, **extra):
    """One rewrite contract written in the formal-half frame (formal_frame 1)."""
    data = {
        'kind': 'rewrite_contract', 'id': cid, 'formal_frame': 1, 'version': version,
        'provenance': {'origin': {'intrinsic_specification': 'fixture-20'}},
        'proof_unit': {'prototype': PROTOTYPE},
        'concurrency_frame': [
            {'array': 'parent', 'shared_actions': ['claim', 'min_update'], 'history_reads': True},
            {'array': 'frontier', 'shared_actions': ['queue_reserve'], 'history_reads': False},
            {'array': 'dist', 'shared_actions': ['atomic_add_or'], 'history_reads': False},
            {'array': 'sum', 'shared_actions': ['openmp_reduction'], 'history_reads': False},
            {'array': 'queue', 'shared_actions': [], 'history_reads': False}],
        'clauses': clauses if clauses is not None else [
            {'id': 'bounds', 'role': 'legality', 'statement': 'Inputs are in bounds.',
             'discharge_mode': 'runtime_guard', 'negative_control': {'id': 'bad-n', 'check': 'bounds'},
             'acsl': {'text': 'requires n >= 0 && \\valid(parent + (0 .. n-1));', 'uses': []},
             'proof_placement': 'per_candidate'}],
        'pattern_key': [{'roles': ['index', 'target'], 'address_shapes': ['stream', 'single_valued_indirect'],
                         'update_kind': 'read'}],
        'strategies': [], 'uses_intrinsics': [], 'uses_library_operations': [], 'runtime_guards': [],
        'knobs': [], 'preservation_obligations': [], 'correctness_check': {'kernel': 'fixture', 'check': 'fixture'},
        'execution_witness': {'check': 'fixture'},
        'negative_controls': [{'id': kind, 'kind': kind, 'check': 'fixture'}
                              for kind in ('overlapping_pointer', 'double_claim', 'dropped_operand')],
        'requirement_map': []}
    if role:
        data['contract_role'] = role
    data.update(extra)
    return data


def clause(cid, text=None, placement='per_candidate', uses=(), **extra):
    data = {'id': cid, 'role': 'postcondition', 'statement': f'Fixture clause {cid}.',
            'discharge_mode': 'differential_test', 'negative_control': {'id': f'{cid}-control', 'check': cid}}
    if text is not None:
        data['acsl'] = {'text': text, 'uses': list(uses)}
    else:
        data['natural_language_only'] = True
    if placement is not None:
        data['proof_placement'] = placement
    data.update(extra)
    return data


def semantics(rules):
    return {'kind': 'proof_semantics', 'id': 'semantics.fixture', 'formal_frame': 1, 'version': '1',
            'provenance': {'origin': {'intrinsic_specification': 'fixture-20'}}, 'clauses': [], 'rules': rules}


def positive_entries():
    """{relative path: entry}: every new field, each placement form, five shared-action kinds."""
    offload_clauses = [
        {'id': 'bounds', 'role': 'legality', 'statement': 'Inputs are in bounds.',
         'discharge_mode': 'runtime_guard', 'negative_control': {'id': 'bad-n', 'check': 'bounds'},
         'acsl': {'text': 'requires n >= 0 && \\valid(parent + (0 .. n-1)) && '
                          '\\separated(parent + (0 .. n-1), frontier + (0 .. n-1));', 'uses': []},
         'proof_placement': 'per_candidate'},
        # discharge_mode differential_test, placement per_candidate: the two stay separate
        clause('frame', 'ensures \\forall integer k; 0 <= k < n ==> in_range(k, n) ==> '
                        'parent[k] == \\old(parent[k]) || parent[k] >= 0;\nassigns parent[0 .. n-1];',
               uses=['logic.graph']),
        clause('count', 'ensures \\result == count_pos(parent, n);', uses=['logic.graph'],
               placement={'once': 'contract.fixture_enable_a@1.0'}),
        clause('own', 'ensures \\result >= 0 && parent[0] == \\at(parent[0], Pre);', placement={'once': 'self'}),
        clause('wait', None, placement={'assumed': {'kind': 'proof_semantics', 'rule': 'semantics.fixture#wait-rule',
                                                     'evidence': 'gem5 IF.cc region stall; owner Yan-Ru at promotion'}}),
    ]
    return {
        'logic/graph.acsl': GRAPH,
        'rewrite_contracts/enable_a.yaml': frame_contract('contract.fixture_enable_a', role='enabling'),
        'rewrite_contracts/enable_b.yaml': frame_contract('contract.fixture_enable_b', role='enabling', version='2.1'),
        'rewrite_contracts/offload.yaml': frame_contract(
            'contract.fixture_offload', role='offload_only', clauses=offload_clauses,
            required_enabling_contracts=[{'contract': 'contract.fixture_enable_b', 'versions': '>=2.0, <3.0'},
                                         {'contract': 'contract.fixture_enable_a', 'versions': '>=1.0'}]),
        'proof_semantics/fixture.yaml': semantics([
            {'id': 'wait-rule', 'statement': 'A read waits for the producing command.', 'cites': GEM5},
            {'id': 'cross-core', 'statement': 'No stale CPU copy survives a DX100 store.',
             'assumed': {'owner': 'Eric'}}]),
    }


def write_library(root, entries):
    for rel, data in entries.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data if isinstance(data, str) else yaml.safe_dump(data, sort_keys=False))


def problems_by_file(stderr):
    found = {}
    for line in stderr.splitlines():
        match = re.match(r'^(/\S+): (\S+): (.*)$', line)
        if match:
            found.setdefault(os.path.basename(match.group(1)), []).append((match.group(2), match.group(3)))
    return found


def framac_available():
    if os.environ.get('SWDB_FRAMA_C'):
        return os.environ['SWDB_FRAMA_C'] != 'none'
    if not shutil.which('opam'):
        return False
    done = subprocess.run(['opam', 'exec', '--switch=framac-33', '--', 'frama-c', '-version'],
                          capture_output=True, text=True)
    return done.returncode == 0 and done.stdout.startswith('33.0')


FRAMAC = framac_available()
needs_framac = pytest.mark.skipif(not FRAMAC, reason='Frama-C 33.0 (opam switch framac-33) is missing')


@pytest.fixture(scope='module')
def positive(tmp_path_factory):
    folder = tmp_path_factory.mktemp('positive')
    records = make_records(folder)
    root = folder / 'library'
    write_library(root, positive_entries())
    return records, root


def test_fixture_library_with_every_new_field_validates_and_builds(positive):
    records, root = positive
    checked = run_swdb('validate', '--records', records.path, '--library', root)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    if FRAMAC:
        assert 'UNCHECKED' not in checked.stderr
        assert '6 acsl field(s) type-checked by Frama-C 33.0' in checked.stdout
    db = records.path.parent / 'build' / 'formal.sqlite'
    built = run_swdb('build', '--records', records.path, '--db', db)   # library: the folder beside records
    assert built.returncode == 0, built.stdout + built.stderr
    rows = run_swdb('sql', '--records', records.path, '--db', db, '--format', 'json',
                    'SELECT contract, versions FROM swdb_library_required_contracts '
                    "WHERE entry = 'contract.fixture_offload' ORDER BY position")
    assert rows.returncode == 0, rows.stderr
    assert json.loads(rows.stdout) == [{'contract': 'contract.fixture_enable_b', 'versions': '>=2.0, <3.0'},
                                       {'contract': 'contract.fixture_enable_a', 'versions': '>=1.0'}]
    placements = run_swdb('sql', '--records', records.path, '--db', db, '--format', 'json',
                          'SELECT clause, placement, target, assumed_kind FROM swdb_library_clause_placements '
                          "WHERE entry = 'contract.fixture_offload' ORDER BY clause")
    assert json.loads(placements.stdout) == [
        {'clause': 'bounds', 'placement': 'per_candidate', 'target': None, 'assumed_kind': None},
        {'clause': 'count', 'placement': 'once', 'target': 'contract.fixture_enable_a@1.0', 'assumed_kind': None},
        {'clause': 'frame', 'placement': 'per_candidate', 'target': None, 'assumed_kind': None},
        {'clause': 'own', 'placement': 'once', 'target': 'self', 'assumed_kind': None},
        {'clause': 'wait', 'placement': 'assumed', 'target': 'semantics.fixture#wait-rule',
         'assumed_kind': 'proof_semantics'}]
    kinds = run_swdb('sql', '--records', records.path, '--db', db, '--format', 'json',
                     'SELECT DISTINCT shared_action FROM swdb_library_shared_actions ORDER BY shared_action')
    assert [row['shared_action'] for row in json.loads(kinds.stdout)] == [
        'atomic_add_or', 'claim', 'min_update', 'openmp_reduction', 'queue_reserve']
    rules = run_swdb('sql', '--records', records.path, '--db', db, '--format', 'json',
                     'SELECT rule, gem5_commit, owner FROM swdb_proof_semantics_rules ORDER BY rule')
    assert json.loads(rules.stdout) == [{'rule': 'cross-core', 'gem5_commit': None, 'owner': 'Eric'},
                                        {'rule': 'wait-rule', 'gem5_commit': GEM5['gem5_commit'], 'owner': None}]


def test_without_framac_every_acsl_field_is_reported_unchecked_never_valid(positive):
    records, root = positive
    checked = run_swdb('validate', '--records', records.path, '--library', root, env={'SWDB_FRAMA_C': 'none'})
    assert checked.returncode == 0, checked.stderr
    unchecked = [line for line in checked.stderr.splitlines() if line.startswith('UNCHECKED: ')]
    assert len(unchecked) == 6, checked.stderr   # 4 offload clauses with acsl, one per enabling contract
    assert all('acsl' in line and 'Frama-C' in line for line in unchecked)
    assert '6 acsl field(s) unchecked' in checked.stdout
    assert 'type-checked' not in checked.stdout


# --- negative controls: one shared library, one validate run --------------------------------

def control_contract(name, text=None, *, uses=(), placement='per_candidate', **extra):
    return frame_contract(f'contract.ctl_{name}', clauses=[clause('c1', text, placement=placement, uses=uses)],
                          **extra)


#: case -> (entry, expected reason fragment or None for "passes", needs Frama-C)
def control_cases():
    c = control_contract
    cases = {
        # clause kinds (16 item 2)
        'kinds_pass': (c('kinds_pass', 'requires n >= 0;\nensures \\result >= 0;\nassigns parent[0 .. n-1];'), None, False),
        'behavior': (c('behavior', 'behavior b:\n  ensures \\result >= 0;'), 'behavior', False),
        'assigns_everything': (c('assigns_everything', 'assigns \\everything;'), '\\everything', False),
        'assigns_scalar': (c('assigns_scalar', 'assigns *frontier, parent[0];'), None, False),
        'constants_nothing': (c('constants_nothing', 'requires parent != \\null && \\true;\nensures \\false || \\result >= 0;\nassigns \\nothing;'), None, False),
        # quantifiers
        'bounded_forall': (c('bounded_forall', 'ensures \\forall integer k; 0 <= k < n ==> parent[k] == \\old(parent[k]);'), None, False),
        'bounded_exists': (c('bounded_exists', 'ensures \\result == 1 ==> \\exists integer k; 0 <= k && k < n && parent[k] == 0;'), None, False),
        'unguarded_forall': (c('unguarded_forall', 'ensures \\forall integer k; parent[k] >= 0;'), 'range guard', False),
        'disjunct_guard': (c('disjunct_guard', 'ensures \\forall integer k; 0 <= k < n || k > 5 ==> parent[k] == 0;'), 'range guard', False),
        'real_quantifier':(c('real_quantifier', 'ensures \\forall real x; 0.0 <= x <= 1.0 ==> x * x <= 1.0;'), 'not an integer', False),
        'lambda_sum': (c('lambda_sum', 'ensures \\result == \\sum(0, n - 1, \\lambda integer k; parent[k]);'), '\\lambda', False),
        # labels
        'old_at_pre': (c('old_at_pre', 'ensures parent[0] == \\at(parent[0], Pre) && n == \\old(n);'), None, False),
        'at_post': (c('at_post', 'ensures parent[0] == \\at(parent[0], Post);'), 'label', False),
        'at_c_label': (c('at_c_label', 'ensures parent[0] == \\at(parent[0], L1);'), 'label', False),
        # arithmetic
        'real_arith': (c('real_arith', 'ensures (real)\\result * 0.5 >= 0.0 && \\result + 1 > \\result;'), None, False),
        'float_builtin': (c('float_builtin', 'ensures \\round_double(\\NearestEven, 1.0) == 1.0;'), 'floating-point', False),
        # memory built-ins
        'valid_separated': (c('valid_separated', 'requires \\valid(parent + (0 .. n-1)) && \\separated(parent, frontier);'), None, False),
        'block_length': (c('block_length', 'requires \\block_length(parent) >= 4;'), 'memory built-in', False),
        'initialized': (c('initialized', 'requires \\initialized(parent + (0 .. n-1));'), 'memory built-in', False),
        # logic calls
        'logic_call': (c('logic_call', 'ensures \\result == count_pos(parent, n) + twice(n);', uses=['logic.graph', 'logic.nonrec']), None, False),
        'logic_unlisted': (c('logic_unlisted', 'ensures \\result == count_pos(parent, n);'), 'no listed logic-library entry', False),
        'logic_in_half': (c('logic_in_half', 'predicate local_p(integer x) = x > 0;\nensures local_p(\\result);'), 'formal half', False),
        'unknown_entry': (c('unknown_entry', 'ensures \\true;', uses=['logic.nowhere']), 'unknown logic-library entry', False),
        # inductive definitions and axioms
        'inductive_in_half': (c('inductive_in_half', 'inductive r(integer a) {\n  case c: r(0);\n}\nensures r(n);'), 'inductive', False),
        'calls_inductive': (c('calls_inductive', 'ensures reach(frontier, 0, n);', uses=['logic.graph']), 'inductive', False),
        'axiom_in_half': (c('axiom_in_half', 'axiomatic A {\n  logic integer f(integer x);\n  axiom f_def: \\forall integer x; 0 <= x <= 1 ==> f(x) == x;\n}\nensures \\true;'), 'axiom', False),
        'uses_axiom_file': (c('uses_axiom_file', 'ensures \\result == ax_f(n);', uses=['logic.bad_axiom']), 'axiom', False),
        'uses_mutual': (c('uses_mutual', 'ensures \\result == ev(n);', uses=['logic.rec_mutual']), 'mutual recursion', False),
        # Frama-C parse and type check
        'syntax_error': (c('syntax_error', 'ensures \\result >= ;'), 'Frama-C', True),
        'type_error': (c('type_error', 'ensures \\result == undeclared_name;'), 'undeclared_name', True),
        # proof placement
        'no_placement': (c('no_placement', 'ensures \\result >= 0;', placement=None), 'no proof placement', False),
        'assumed_kind': (c('assumed_kind', None, placement={'assumed': {'kind': 'hope', 'owner': 'Eric', 'evidence': 'none'}}), 'assumption kind', False),
        'assumed_no_owner': (c('assumed_no_owner', None, placement={'assumed': {'kind': 'summary', 'evidence': 'e'}}), 'rule or owner', False),
        'assumed_no_evidence': (c('assumed_no_evidence', None, placement={'assumed': {'kind': 'trusted_tool', 'owner': 'Yan-Ru'}}), 'evidence', False),
        'assumed_unknown_rule': (c('assumed_unknown_rule', None, placement={'assumed': {'kind': 'proof_semantics', 'rule': 'semantics.fixture#nope', 'evidence': 'e'}}), 'proof-semantics rule', False),
        'once_unknown': (c('once_unknown', 'ensures \\true;', placement={'once': 'contract.nowhere@1.0'}), 'not in the library', False),
        'once_wrong_version': (c('once_wrong_version', 'ensures \\true;', placement={'once': 'contract.fixture_enable_a@9.0'}), 'not in the library', False),
        'two_placements': (c('two_placements', 'ensures \\true;', placement={'once': 'self', 'assumed': {'kind': 'summary', 'owner': 'x', 'evidence': 'y'}}), 'exactly one', False),
        # concurrency frame
        'unknown_kind': (c('unknown_kind', concurrency_frame=[{'array': 'parent', 'shared_actions': ['teleport'], 'history_reads': False}]), 'shared-action kind', False),
        'history_maybe': (c('history_maybe', concurrency_frame=[{'array': 'parent', 'shared_actions': ['claim'], 'history_reads': 'maybe'}]), 'yes or no', False),
        'no_concurrency': (c('no_concurrency', concurrency_frame=None), 'concurrency frame', False),
        # offload-only and enabling contracts
        'required_unknown': (c('required_unknown', contract_role='offload_only', required_enabling_contracts=[{'contract': 'contract.nowhere', 'versions': '>=1.0'}]), 'unknown', False),
        'required_bad_range': (c('required_bad_range', contract_role='offload_only', required_enabling_contracts=[{'contract': 'contract.fixture_enable_a', 'versions': 'about 2'}]), 'version range', False),
        'enabling_lists': (c('enabling_lists', contract_role='enabling', enables=['contract.fixture_offload']), 'never lists', False),
    }
    for name, case in list(cases.items()):
        entry = case[0]
        if entry.get('concurrency_frame', ...) is None:
            del entry['concurrency_frame']
    return cases


SEMANTICS_CONTROLS = {
    'rule-cites': ({'id': 'rule-cites', 'statement': 'Cited rule.', 'cites': GEM5}, None),
    'rule-owner': ({'id': 'rule-owner', 'statement': 'Owned rule.', 'assumed': {'owner': 'Eric'}}, None),
    'rule-neither': ({'id': 'rule-neither', 'statement': 'Bare rule.'}, 'cites'),
    'rule-both': ({'id': 'rule-both', 'statement': 'Both.', 'cites': GEM5, 'assumed': {'owner': 'Eric'}}, 'cites'),
}


@pytest.fixture(scope='module')
def controls(tmp_path_factory):
    folder = tmp_path_factory.mktemp('controls')
    records = make_records(folder)
    root = folder / 'library'
    entries = {rel: data for rel, data in positive_entries().items() if not rel.startswith('logic/')}
    entries['proof_semantics/fixture.yaml'] = semantics(
        [{'id': 'wait-rule', 'statement': 'Wait rule.', 'cites': GEM5}]
        + [rule for rule, _ in SEMANTICS_CONTROLS.values()])
    for name, (text, _) in LOGIC_CONTROLS.items():
        entries[f'logic/{name}.acsl'] = text
    for name, (entry, _, _) in control_cases().items():
        entries[f'rewrite_contracts/ctl_{name}.yaml'] = entry
    write_library(root, entries)
    result = run_swdb('validate', '--records', records.path, '--library', root)
    return result, problems_by_file(result.stderr)


@pytest.mark.parametrize('name', sorted(control_cases()))
def test_each_frame_check_is_shown_by_its_control(controls, name):
    result, found = controls
    _, expected, framac = control_cases()[name]
    if framac and not FRAMAC:
        pytest.skip('Frama-C 33.0 is missing')
    got = found.get(f'ctl_{name}.yaml', [])
    if expected is None:
        assert got == [], got
        return
    assert got, f'no problem reported for ctl_{name}: ' + result.stderr[-2000:]
    assert all(expected in reason for _, reason in got), got


def test_a_missing_placement_names_the_entry_and_the_clause(controls):
    _, found = controls
    [(field, reason)] = found['ctl_no_placement.yaml']
    assert field == 'clauses[0].proof_placement'
    assert 'contract.ctl_no_placement' in reason and "'c1'" in reason


@needs_framac
def test_framac_messages_are_attached(controls):
    _, found = controls
    [(_, syntax)] = found['ctl_syntax_error.yaml']
    [(_, typed)] = found['ctl_type_error.yaml']
    assert 'Frama-C 33.0' in syntax and "unexpected token ';'" in syntax
    assert 'unbound logic variable undeclared_name' in typed


@pytest.mark.parametrize('name', sorted(LOGIC_CONTROLS))
def test_logic_library_rules_are_shown_by_their_controls(controls, name):
    _, found = controls
    expected = LOGIC_CONTROLS[name][1]
    got = found.get(f'{name}.acsl', [])
    if expected is None:
        assert got == [], got
    else:
        assert got and all(expected in reason for _, reason in got), got


@pytest.mark.parametrize('name', sorted(SEMANTICS_CONTROLS))
def test_proof_semantics_rules_need_exactly_one_of_cites_or_owner(controls, name):
    _, found = controls
    expected = SEMANTICS_CONTROLS[name][1]
    index = ['wait-rule', *SEMANTICS_CONTROLS].index(name)
    got = [(field, reason) for field, reason in found.get('fixture.yaml', []) if field.startswith(f'rules[{index}]')]
    if expected is None:
        assert got == []
    else:
        assert got and expected in got[0][1], found.get('fixture.yaml')


def test_controls_library_fails_validate(controls):
    result, found = controls
    assert result.returncode == 1
    # the positive base entries of the controls library stay clean
    for name in ('enable_a.yaml', 'enable_b.yaml', 'offload.yaml'):
        assert name not in found, found[name]


def test_frame_fields_need_the_frame_marker(tmp_path):
    records = make_records(tmp_path)
    root = tmp_path / 'library'
    entry = frame_contract('contract.old_style')
    del entry['formal_frame']
    write_library(root, {'rewrite_contracts/old.yaml': entry})
    result = run_swdb('validate', '--records', records.path, '--library', root, env={'SWDB_FRAMA_C': 'none'})
    assert result.returncode == 1
    assert 'formal_frame' in result.stderr
    # an old-style entry without frame fields keeps validating
    plain = copy.deepcopy(entry)
    for key in ('version', 'proof_unit', 'concurrency_frame'):
        del plain[key]
    plain['clauses'][0].pop('acsl')
    plain['clauses'][0].pop('proof_placement')
    plain['clauses'][0]['natural_language_only'] = True
    write_library(root, {'rewrite_contracts/old.yaml': plain})
    result = run_swdb('validate', '--records', records.path, '--library', root, env={'SWDB_FRAMA_C': 'none'})
    assert result.returncode == 0, result.stderr
