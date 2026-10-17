"""2026-10-16 ET. Independent Owners/OwnedEffects source9 interpretation.

Complete typed source definitions and all nine source goals are retained here.
Definitions are conditional source syntax, never desired-postcondition axioms.
Root's separate heap_reader provides the independently source-pinned Heap/cell
interpretation. Actual record/constructor aliases, all bodies/goals/support and
independent review must close before any mathematical adoption. No source-memory
bridge, lifetime, caller or default-catalog admission follows from this module.
"""

import hashlib
import json

OWNERS_SOURCE = {'bytes': 2389,
 'module': 'vector_owned_state.Owners',
 'sha256': 'a2c295d2c6720a9c8c522f05e19723c2d2d2a32b63f9b198aab03f195269e4b6'}

EFFECTS_SOURCE = {'bytes': 3128,
 'module': 'vector_owned_effects.OwnedEffects',
 'sha256': '6bfc13341d2faceb5a3fb64bd2d5bff22dd03c52a1fa3d5c4cb39b6e9c83f7f5'}

STATE_FIELDS = (('active', '(Array Int Bool)'), ('backing', '(Array Int Int)'))

# (complete typed parameters, result sort, complete source body).
# mk_state, Integer and Pointer are placeholders until exact task encoding checks.
OWNERS_EFFECTS_DEFINITIONS = {'E_is_ready': ('(ready (Array Int Bool)) (r Int)', 'Bool', '(= (select ready r) true)'),
 'E_target': ('(h heap) (r Int)', 'Int', '(match (H_contents h r 0) (((Pointer b o) b) ((Integer i) 0)))'),
 'E_size': ('(h heap) (r Int)', 'Int', '(H_load_int h r 8)'),
 'E_capacity': ('(h heap) (r Int)', 'Int', '(H_load_int h r 16)'),
 'E_receiver': ('(h heap) (r Int)',
                'Bool',
                '(and (H_typed_writes h r 0 8 8) (H_typed_writes h r 8 8 8) (H_typed_writes h r 16 8 8))'),
 'E_header': ('(h heap) (r Int) (b Int) (n Int) (c Int)',
              'Bool',
              '(and (E_receiver h r) (<= 0 n) (<= n c) (<= c 18446744073709551615) (H_pointer_at h r 0 b 0) '
              '(H_integer_at h r 8 n) (H_integer_at h r 16 c) (H_initialized_at h r 0) (H_initialized_at h r '
              '8) (H_initialized_at h r 16))'),
 'E_reserved': ('(h heap) (s state) (ready (Array Int Bool)) (r Int)',
                'Bool',
                '(and (O_active_owner s r) (= (select ready r) false) (= (O_buffer s r) 0) (E_receiver h '
                'r))'),
 'E_world': ('(h heap) (s state) (ready (Array Int Bool))',
             'Bool',
             '(and (H_well_formed h) (O_valid s (H_fresh_id h)) (forall ((r Int)) (=> (O_active_owner s r) '
             '(and (E_receiver h r) (=> (= (select ready r) true) (exists ((n Int) (c Int)) (E_header h r '
             '(O_buffer s r) n c)))))) (forall ((r Int)) (=> (and (O_active_owner s r) (< 0 (O_buffer s r))) '
             '(H_freeable h (O_buffer s r) 0))))'),
 'E_store_header': ('(h heap) (r Int) (b Int) (n Int) (c Int)',
                    'heap',
                    '(H_put_integer (H_put_integer (H_put_pointer h r 0 b 0) r 8 n) r 16 c)'),
 'E_copy_header': ('(h heap) (destination Int) (source Int)',
                   'heap',
                   '(E_store_header h destination (E_target h source) (E_size h source) (E_capacity h '
                   'source))'),
 'E_move': ('(h heap) (destination Int) (source Int)',
            'heap',
            '(E_store_header (E_copy_header h destination source) source 0 0 0)'),
 'E_moved_phases': ('(ready (Array Int Bool)) (destination Int) (source Int)',
                    '(Array Int Bool)',
                    '(store (store ready destination true) source true)'),
 'E_swap': ('(h heap) (left Int) (right Int) (a Int)',
            'heap',
            '(let ((temporary (H_fresh_id h))) (let ((h1 (H_begin_automatic h 24 a))) (let ((h2 '
            '(E_copy_header h1 temporary left))) (let ((h3 (E_copy_header h2 left right))) (let ((h4 '
            '(E_copy_header h3 right temporary))) (H_end_automatic h4 temporary))))))'),
 'E_incoming_frame': ('(before heap) (after heap) (left Int) (right Int)',
                      'Bool',
                      '(forall ((b Int)) (=> (H_issued before b) (and (H_same_object before after b) (=> '
                      '(and (not (= b left)) (not (= b right))) (forall ((p Int)) (and (= (H_contents before '
                      'b p) (H_contents after b p)) (= (H_initialized_at before b p) (H_initialized_at after '
                      'b p))))))))'),
 'O_empty': ('(dummy Int)',
             'state',
             '(mk_state ((as const (Array Int Bool)) false) ((as const (Array Int Int)) 0))'),
 'O_active_owner': ('(s state) (r Int)', 'Bool', '(= (select (active s) r) true)'),
 'O_buffer': ('(s state) (r Int)', 'Int', '(select (backing s) r)'),
 'O_exclusive': ('(s state)',
                 'Bool',
                 '(forall ((r Int) (q Int)) (=> (and (= (select (active s) r) true) (= (select (active s) q) '
                 'true) (not (= (select (backing s) r) 0)) (= (select (backing s) r) (select (backing s) '
                 'q))) (= r q)))'),
 'O_valid': ('(s state) (frontier Int)',
             'Bool',
             '(and (< 0 frontier) (O_exclusive s) (forall ((r Int)) (=> (= (select (active s) r) true) (and '
             '(< 0 r) (< r frontier) (<= 0 (select (backing s) r)) (< (select (backing s) r) frontier)))) '
             '(forall ((r Int) (q Int)) (=> (and (= (select (active s) r) true) (= (select (active s) q) '
             'true) (not (= (select (backing s) r) 0))) (not (= (select (backing s) r) q)))))'),
 'O_begin_owner': ('(s state) (r Int)',
                   'state',
                   '(mk_state (store (active s) r true) (store (backing s) r 0))'),
 'O_bind': ('(s state) (r Int) (b Int)', 'state', '(mk_state (active s) (store (backing s) r b))'),
 'O_move': ('(s state) (destination Int) (source Int)',
            'state',
            '(mk_state (active s) (store (store (backing s) destination (select (backing s) source)) source '
            '0))'),
 'O_swap': ('(s state) (left Int) (right Int)',
            'state',
            '(ite (= left right) s (mk_state (active s) (store (store (backing s) left (select (backing s) '
            'right)) right (select (backing s) left))))'),
 'O_retire': ('(s state) (r Int)', 'state', '(mk_state (store (active s) r false) (store (backing s) r 0))')}

MOVE_ACSL = ('OwnedEffects::world(h,owners,ready) && OwnedEffects::reserved(h,owners,ready,d) && '
 'Owners::active_owner(owners,s) && OwnedEffects::is_ready(ready,s) && d != s && '
 'OwnedEffects::header(h,s,b,n,c)')

SWAP_ACSL = ('OwnedEffects::world(h,owners,ready) && Owners::active_owner(owners,l) && Owners::active_owner(owners,r) && '
 'OwnedEffects::is_ready(ready,l) && OwnedEffects::is_ready(ready,r) && OwnedEffects::header(h,l,bl,nl,cl) '
 '&& OwnedEffects::header(h,r,br,nr,cr) && Heap::automatic_available(h,24,8,a)')

MOVE_BIND = '(h heap) (owners state) (ready (Array Int Bool)) (d Int) (s Int) (b Int) (n Int) (c Int)'

SWAP_BIND = ('(h heap) (owners state) (ready (Array Int Bool)) (l Int) (r Int) (a Int) (bl Int) (nl Int) (cl Int) (br '
 'Int) (nr Int) (cr Int)')

MOVE_PRE = ('(and (E_world h owners ready) (E_reserved h owners ready d) (O_active_owner owners s) (E_is_ready ready s) '
 '(not (= d s)) (E_header h s b n c))')

SWAP_PRE = ('(and (E_world h owners ready) (O_active_owner owners l) (O_active_owner owners r) (E_is_ready ready l) '
 '(E_is_ready ready r) (E_header h l bl nl cl) (E_header h r br nr cr) (H_automatic_available h 24 8 a))')

CONCLUSIONS = {'move.destination_header': ('(E_header (E_move h d s) d b n c)',
                             'OwnedEffects::header(OwnedEffects::move(h,d,s),d,b,n,c)'),
 'move.source_empty': ('(E_header (E_move h d s) s 0 0 0)',
                       'OwnedEffects::header(OwnedEffects::move(h,d,s),s,0,0,0)'),
 'move.incoming_frame': ('(E_incoming_frame h (E_move h d s) d s)',
                         'OwnedEffects::incoming_frame(h,OwnedEffects::move(h,d,s),d,s)'),
 'move.owner_correspondence': ('(E_world (E_move h d s) (O_move owners d s) (E_moved_phases ready d s))',
                               'OwnedEffects::world(OwnedEffects::move(h,d,s),Owners::move(owners,d,s),OwnedEffects::moved_phases(ready,d,s))'),
 'swap.left_header': ('(E_header (E_swap h l r a) l br nr cr)',
                      'OwnedEffects::header(OwnedEffects::swap(h,l,r,a),l,br,nr,cr)'),
 'swap.right_header': ('(E_header (E_swap h l r a) r bl nl cl)',
                       'OwnedEffects::header(OwnedEffects::swap(h,l,r,a),r,bl,nl,cl)'),
 'swap.temporary_lifetime': ('(and (not (H_live (E_swap h l r a) (H_fresh_id h))) (H_issued (E_swap h l r a) '
                             '(H_fresh_id h)))',
                             '!Heap::live(OwnedEffects::swap(h,l,r,a),Heap::fresh_id(h)) && '
                             'Heap::issued(OwnedEffects::swap(h,l,r,a),Heap::fresh_id(h))'),
 'swap.incoming_frame': ('(E_incoming_frame h (E_swap h l r a) l r)',
                         'OwnedEffects::incoming_frame(h,OwnedEffects::swap(h,l,r,a),l,r)'),
 'swap.owner_correspondence': ('(E_world (E_swap h l r a) (O_swap owners l r) ready)',
                               'OwnedEffects::world(OwnedEffects::swap(h,l,r,a),Owners::swap(owners,l,r),ready)')}

def source_statement(ident):
    move = ident.startswith('move.')
    variables = 'd,s,b,n,c' if move else 'l,r,a,bl,nl,cl,br,nr,cr'
    return (r'\forall Heap::heap h; \forall Owners::state owners; \forall OwnedEffects::phases ready; \forall integer '
            + variables + '; ' + (MOVE_ACSL if move else SWAP_ACSL) + ' ==> ' + CONCLUSIONS[ident][1])


def source_goal_text(ident):
    move = ident.startswith('move.')
    return '(not (forall ('+(MOVE_BIND if move else SWAP_BIND)+') (=> '+(MOVE_PRE if move else SWAP_PRE)+' '+CONCLUSIONS[ident][0]+')))'


SCIENTIFIC_ACCEPTANCE = False
SOURCE_HEAP_TYPED_CALLER_ACCEPTANCE = False


def need(value, label):
    if not value:
        raise ValueError(label)


def digest(tree):
    return hashlib.sha256(json.dumps(tree, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def rename_globals(tree, aliases, bound=frozenset()):
    """Rename only free symbols; preserve all quantifier/let/match scopes.

    The aliases are candidate typed source roles, whose complete definition
    bodies must subsequently match. They never establish a source fact alone.
    """
    if isinstance(tree, str):
        return tree if tree in bound else aliases.get(tree, tree)
    need(isinstance(tree, list) and tree, 'complete nonempty scoped term')
    if tree[0] in ('forall', 'exists'):
        need(len(tree) == 3 and all(isinstance(row, list) and len(row) == 2
                                   for row in tree[1]), 'complete quantified bindings')
        local = bound | {row[0] for row in tree[1]}
        return [tree[0], tree[1], rename_globals(tree[2], aliases, local)]
    if tree[0] == 'let':
        need(len(tree) == 3 and all(isinstance(row, list) and len(row) == 2
                                   for row in tree[1]), 'complete simultaneous let')
        bindings = [[row[0], rename_globals(row[1], aliases, bound)] for row in tree[1]]
        return ['let', bindings, rename_globals(tree[2], aliases,
                                               bound | {row[0] for row in tree[1]})]
    if tree[0] == 'match':
        need(len(tree) == 3, 'complete sum match')
        cases = []
        for pattern, body in tree[2]:
            need(isinstance(pattern, list) and pattern, 'complete constructor pattern')
            cases.append([[aliases.get(pattern[0], pattern[0]), *pattern[1:]],
                          rename_globals(body, aliases, bound | set(pattern[1:]))])
        return ['match', rename_globals(tree[1], aliases, bound), cases]
    return [rename_globals(item, aliases, bound) for item in tree]


def inline_source_aliases(tree):
    """The driver's two absent scalar accessors are exact source abbreviations."""
    if isinstance(tree, str):
        return tree
    need(isinstance(tree, list) and tree, 'complete source alias term')
    if tree[0] in ('E_size', 'E_capacity'):
        need(len(tree) == 3, 'complete typed header scalar accessor')
        return ['H_load_int', inline_source_aliases(tree[1]),
                inline_source_aliases(tree[2]), '8' if tree[0] == 'E_size' else '16']
    return [inline_source_aliases(item) if isinstance(item, list) and item else item
            for item in tree]


def _sort_signature(parameters, result):
    need(isinstance(parameters, list) and all(isinstance(row, list) and len(row) == 2
                                             and isinstance(row[0], str) for row in parameters),
         'complete ordered typed parameters')
    need(len({row[0] for row in parameters}) == len(parameters), 'unique function parameter names')
    return [row[1] for row in parameters], result


def candidate_roles(commands, context, parse):
    """Disambiguate overloads by entire ordered typed signatures, then compare bodies.

    Numeric suffixes are merely driver spelling candidates. A missing or
    altered complete body remains a hard refusal in reconcile_task.
    """
    aliases = dict(context['aliases'])
    rows = [row for row in commands if row[0] == 'define-fun']
    need(len({row[1] for row in rows}) == len(rows), 'unique actual task function definitions')
    signatures = {role: _sort_signature(parse('('+parameters+')'), parse(result))
                  for role, (parameters, result, _) in OWNERS_EFFECTS_DEFINITIONS.items()}
    for row in rows:
        need(len(row) == 5, 'complete actual definition shape')
        if row[1] in aliases:
            continue
        actual_signature = _sort_signature(row[2], row[3])
        matches = []
        for role, signature in signatures.items():
            base = role[2:]
            spelling = row[1]
            suffix = spelling[len(base):] if spelling.startswith(base) else None
            if suffix is not None and (suffix == '' or suffix.isdecimal() and not suffix.startswith('0')) \
                    and signature == actual_signature:
                matches.append(role)
        need(len(matches) <= 1, 'unique fully typed source role candidate')
        if matches:
            aliases[row[1]] = matches[0]
    return aliases


# A complete explicit alpha-renaming certificate. The correspondence is checked
# against every original binder name, sort and position on both sides. Reordering
# a closed universal block is sound; no binder crosses an implication/exists.
GOAL_BINDER_MAP = {
    'move': {'h': 'heap1', 'owners': 'state1', 'ready': 't', 'd': 'i2',
             's': 'i4', 'b': 'i', 'n': 'i3', 'c': 'i1'},
    'swap': {'h': 'heap1', 'owners': 'state1', 'ready': 't', 'l': 'i5', 'r': 'i8',
             'a': 'i', 'bl': 'i1', 'nl': 'i6', 'cl': 'i3', 'br': 'i2',
             'nr': 'i7', 'cr': 'i4'},
}


def reconcile_task(commands, ident, context, parse, canonical, normalize_primitives):
    """Compare complete typed Owners/Effects definitions and one full source goal.

    This does not consume unrelated definitions/support, adopt native results,
    prove source effects, or enable any source/Heap/Typed/caller route. The outer
    cold join must account for every command and every imported assertion.
    """
    need(ident in CONCLUSIONS, 'one of the nine exact original source duties')
    pending = [commands]
    while pending:
        item = pending.pop()
        if isinstance(item, str):
            need(not item.startswith(('$source9_', '_source9_', 'H_', 'O_', 'E_'))
                 and item not in {'mk_heap', 'mk_state'}, 'private source interpretation vocabulary')
        else:
            need(isinstance(item, list), 'complete retained mathematical syntax')
            pending.extend(item)
    aliases = candidate_roles(commands, context, parse)
    aliases.update(context['constants'])

    def normalized(body, parameters, prefix):
        names = [row[0] for row in parameters]
        need(len(set(names)) == len(names), 'unique complete alpha parameters')
        env = {name: '$source9_'+prefix+str(index) for index, name in enumerate(names)}
        renamed = rename_globals(body, aliases, frozenset(names))
        expanded = normalize_primitives(inline_source_aliases(renamed))
        return canonical(expanded, env=env)

    definitions, unhandled = [], []
    for row in commands:
        if row[0] != 'define-fun':
            continue
        role = aliases.get(row[1])
        if role not in OWNERS_EFFECTS_DEFINITIONS:
            unhandled.append(row)
            continue
        parameters, result, body = OWNERS_EFFECTS_DEFINITIONS[role]
        source_parameters = parse('('+parameters+')')
        need(_sort_signature(row[2], row[3]) == _sort_signature(source_parameters, parse(result)),
             'complete ordered source signature: '+role)
        actual = normalized(row[4], row[2], 'argument')
        expected = normalized(parse(body), source_parameters, 'argument')
        need(actual == expected, 'complete position-preserving source definition mismatch: '+role)
        definitions.append({'actual_name': row[1], 'role': role,
                            'command_sha256': digest(row),
                            'actual_ordered_parameters': row[2],
                            'source_ordered_parameters': source_parameters,
                            'result_sort': row[3],
                            'complete_normalized_body_sha256': digest(actual),
                            'complete_ordered_signature_and_body_equal': True})

    assertions = [row for row in commands if row[0] == 'assert']
    need(assertions and all(len(row) == 2 for row in assertions), 'complete assertion census')
    actual = assertions[-1][1]
    expected = parse(source_goal_text(ident))
    for term in (actual, expected):
        need(isinstance(term, list) and len(term) == 2 and term[0] == 'not'
             and isinstance(term[1], list) and len(term[1]) == 3 and term[1][0] == 'forall',
             'complete negated closed universal source goal')
        _sort_signature(term[1][1], 'Bool')
    source_parameters, actual_parameters = expected[1][1], actual[1][1]
    correspondence = GOAL_BINDER_MAP[ident.split('.')[0]]
    source_sorts = dict(source_parameters)
    actual_sorts = dict(actual_parameters)
    need(set(correspondence) == set(source_sorts)
         and set(correspondence.values()) == set(actual_sorts)
         and len(correspondence.values()) == len(set(correspondence.values()))
         and all(source_sorts[name] == actual_sorts[other]
                 for name, other in correspondence.items()),
         'total bijective complete typed universal goal correspondence')
    actual_in_source_order = [[correspondence[name], typ] for name, typ in source_parameters]
    actual_body = normalized(actual[1][2], actual_in_source_order, 'goal')
    source_body = normalized(expected[1][2], source_parameters, 'goal')
    need(actual_body == source_body, 'entire original antecedent and conclusion mismatch: '+ident)

    # Every direct/transitive source role referenced by the full source goal
    # must be observed with its complete body or be an exact declared alias.
    observed = {row['role'] for row in definitions} | set(context['aliases'].values())
    primitive = {'E_size', 'E_capacity', 'H_fresh_id', 'H_end_automatic'}
    required, queue = set(), [expected]
    while queue:
        item = queue.pop()
        if isinstance(item, str):
            if item in OWNERS_EFFECTS_DEFINITIONS and item not in required:
                required.add(item)
                queue.append(parse(OWNERS_EFFECTS_DEFINITIONS[item][2]))
        else:
            queue.extend(item)
    need(required <= observed | primitive, 'complete source role dependency closure')
    return {'id': ident, 'definitions': definitions, 'own_definition_count': len(definitions),
            'all_observed_own_definitions_equivalent': True, 'source_goal_equivalent': True,
            'actual_complete_goal_command_sha256': digest(assertions[-1]),
            'source_complete_goal_sha256': digest(expected),
            'complete_normalized_goal_body_sha256': digest(actual_body),
            'actual_complete_goal_binders': actual_parameters,
            'source_complete_goal_binders': source_parameters,
            'goal_binder_correspondence': correspondence,
            'complete_goal_source_roles': sorted(required),
            'unhandled_complete_definitions': unhandled,
            'support_assertions_not_consumed_here': assertions[:-1],
            'complete_support_or_scientific_acceptance': False,
            'source_Heap_Typed_caller_admission': False}
