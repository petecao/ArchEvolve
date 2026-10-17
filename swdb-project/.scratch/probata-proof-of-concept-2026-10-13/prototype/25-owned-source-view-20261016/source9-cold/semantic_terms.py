"""2026-10-16 ET. Independent source9 syntax; unknown encodings stay unresolved.
No solver, project import, scientific adoption or source/Heap bridge is executed.
"""
import hashlib
import itertools
import json
import re

def need(value, label):
    if not value:
        raise ValueError(label)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()

def forms(text):
    """Complete bounded SMT-LIB tokenization, preserving strings/quoted symbols."""
    need(len(text.encode()) <= 1024 * 1024, "SMT input byte cap")
    lexer = re.compile(r'\s+|;[^\n]*(?:\n|$)|"(?:[^"\\]|\\.|"")*"|\|[^|\\]*\||[()]|[^\s();"|]+')
    stack = [[]]
    end = tokens = 0
    for match in lexer.finditer(text):
        need(match.start() == end, "complete SMT token coverage")
        end = match.end()
        token = match[0]
        if token.isspace() or token.startswith(";"):
            continue
        tokens += 1
        need(tokens <= 100000, "SMT token cap")
        if token == "(":
            item = []
            stack[-1].append(item)
            stack.append(item)
            need(len(stack) <= 160, "SMT depth cap")
        elif token == ")":
            need(len(stack) > 1, "SMT balanced close")
            stack.pop()
        else:
            stack[-1].append(token)
    need(end == len(text) and len(stack) == 1, "complete balanced SMT")
    return stack[0]

def substitute(tree, mapping):
    if isinstance(tree, str):
        return mapping.get(tree, tree)
    if tree and tree[0] in ("forall", "exists"):
        bound = {row[0] for row in tree[1]}
        local = {k: v for k, v in mapping.items() if k not in bound}
        # Source and driver use disjoint bound names for definition application.
        # Reject potential capture rather than silently alpha-renaming a binder.
        free = set().union(*(symbols(v) for v in local.values())) if local else set()
        need(not bound & free, "capture-free substitution")
        return [tree[0], tree[1], substitute(tree[2], local)]
    return [substitute(v, mapping) for v in tree]

def symbols(tree):
    if isinstance(tree, str):
        return {tree}
    return set().union(*(symbols(x) for x in tree)) if tree else set()

def canon(tree, env=None, depth=0, binder_depth=0):
    """Only alpha-renaming, let substitution and explicit propositional identities.

    Binder depth is separate from resource/traversal depth so inert lets and
    connective wrappers cannot rename otherwise identical bound variables.
    No antecedent is dropped. Quantifier reordering is limited to a same-kind
    adjacent block; conjunction/disjunction order and equality symmetry are
    normalized. There is no existential-witness elimination or arithmetic solver.
    """
    env = {} if env is None else env
    need(depth < 120, "normalization depth")
    if isinstance(tree, str):
        return env.get(tree, tree)
    need(bool(tree), "empty expression refused")
    head = tree[0]
    if head == "!":
        # Attributes affect triggers/labels, not the asserted formula. Retain the
        # original full command digest in the reader's census.
        need(len(tree) >= 4 and len(tree) % 2 == 0 and
             all(isinstance(tree[i], str) and tree[i].startswith(":")
                 for i in range(2, len(tree), 2)), "closed SMT annotation shape")
        return canon(tree[1], env, depth + 1, binder_depth)
    if head == "let":
        need(len(tree) == 3 and all(len(r) == 2 for r in tree[1]), "let shape")
        names = [r[0] for r in tree[1]]
        need(len(names) == len(set(names)), "unique simultaneous let names")
        additions = {r[0]: canon(r[1], env, depth + 1, binder_depth) for r in tree[1]}
        return canon(tree[2], {**env, **additions}, depth + 1, binder_depth)
    if head in ("forall", "exists"):
        need(len(tree) == 3, "quantifier shape")
        bindings = list(tree[1])
        body = tree[2]
        while isinstance(body, list) and body and body[0] == head:
            bindings += body[1]
            body = body[2]
        need(all(len(r) == 2 and isinstance(r[0], str) for r in bindings), "binder shape")
        need(len({r[0] for r in bindings}) == len(bindings), "no shadowed merged binder")
        groups = {}
        for name, typ in bindings:
            groups.setdefault(json.dumps(typ, sort_keys=True), []).append(name)
        ways = 1
        for names in groups.values():
            for n in range(1, len(names) + 1):
                ways *= n
        need(ways <= 720, "bounded alpha permutations")
        keys = sorted(groups)
        candidates = []
        for choices in itertools.product(*(itertools.permutations(groups[k]) for k in keys)):
            names = {name: "@%d:%s:%d" % (binder_depth, key, index)
                     for key, choice in zip(keys, choices) for index, name in enumerate(choice)}
            candidates.append(canon(body, {**env, **names}, depth + 1, binder_depth + 1))
        return [head, [[k, len(groups[k])] for k in keys],
                min(candidates, key=lambda x: json.dumps(x, sort_keys=True))]
    if head == "=>" and len(tree) > 3:
        return canon(["=>", tree[1], ["=>", *tree[2:]]], env, depth + 1, binder_depth)
    args = [canon(x, env, depth + 1, binder_depth) for x in tree[1:]]
    if head in ("and", "or"):
        flat = []
        for value in args:
            flat.extend(value[1:] if isinstance(value, list) and value and value[0] == head else [value])
        args = sorted(flat, key=lambda x: json.dumps(x, sort_keys=True))
        if len(args) == 1:
            return args[0]
    if head == "=" and len(args) == 2:
        args.sort(key=lambda x: json.dumps(x, sort_keys=True))
    return [env.get(head, head) if isinstance(head, str) else head, *args]

def one(text):
    result = forms(text)
    need(len(result) == 1, "one independent term")
    return result[0]


MOVE_ACSL = ('OwnedEffects::world(h,owners,ready) && OwnedEffects::reserved(h,owners,ready,d) && '
    'Owners::active_owner(owners,s) && OwnedEffects::is_ready(ready,s) && d != s && OwnedEffects::header(h,s,b,n,c)')
SWAP_ACSL = ('OwnedEffects::world(h,owners,ready) && Owners::active_owner(owners,l) && '
    'Owners::active_owner(owners,r) && OwnedEffects::is_ready(ready,l) && OwnedEffects::is_ready(ready,r) && '
    'OwnedEffects::header(h,l,bl,nl,cl) && OwnedEffects::header(h,r,br,nr,cr) && Heap::automatic_available(h,24,8,a)')
MOVE_BIND = '(h heap) (owners state) (ready (Array Int Bool)) (d Int) (s Int) (b Int) (n Int) (c Int)'
SWAP_BIND = '(h heap) (owners state) (ready (Array Int Bool)) (l Int) (r Int) (a Int) (bl Int) (nl Int) (cl Int) (br Int) (nr Int) (cr Int)'
MOVE_PRE = '(and (E_world h owners ready) (E_reserved h owners ready d) (O_active_owner owners s) (E_is_ready ready s) (not (= d s)) (E_header h s b n c))'
SWAP_PRE = '(and (E_world h owners ready) (O_active_owner owners l) (O_active_owner owners r) (E_is_ready ready l) (E_is_ready ready r) (E_header h l bl nl cl) (E_header h r br nr cr) (automatic_available h 24 8 a))'
CONCLUSIONS = {
    'move.destination_header': ('(E_header (E_move h d s) d b n c)', 'OwnedEffects::header(OwnedEffects::move(h,d,s),d,b,n,c)'),
    'move.source_empty': ('(E_header (E_move h d s) s 0 0 0)', 'OwnedEffects::header(OwnedEffects::move(h,d,s),s,0,0,0)'),
    'move.incoming_frame': ('(E_incoming_frame h (E_move h d s) d s)', 'OwnedEffects::incoming_frame(h,OwnedEffects::move(h,d,s),d,s)'),
    'move.owner_correspondence': ('(E_world (E_move h d s) (O_move owners d s) (E_moved_phases ready d s))', 'OwnedEffects::world(OwnedEffects::move(h,d,s),Owners::move(owners,d,s),OwnedEffects::moved_phases(ready,d,s))'),
    'swap.left_header': ('(E_header (E_swap h l r a) l br nr cr)', 'OwnedEffects::header(OwnedEffects::swap(h,l,r,a),l,br,nr,cr)'),
    'swap.right_header': ('(E_header (E_swap h l r a) r bl nl cl)', 'OwnedEffects::header(OwnedEffects::swap(h,l,r,a),r,bl,nl,cl)'),
    'swap.temporary_lifetime': ('(and (not (live (E_swap h l r a) (fresh_id h))) (issued (E_swap h l r a) (fresh_id h)))', '!Heap::live(OwnedEffects::swap(h,l,r,a),Heap::fresh_id(h)) && Heap::issued(OwnedEffects::swap(h,l,r,a),Heap::fresh_id(h))'),
    'swap.incoming_frame': ('(E_incoming_frame h (E_swap h l r a) l r)', 'OwnedEffects::incoming_frame(h,OwnedEffects::swap(h,l,r,a),l,r)'),
    'swap.owner_correspondence': ('(E_world (E_swap h l r a) (O_swap owners l r) ready)', 'OwnedEffects::world(OwnedEffects::swap(h,l,r,a),Owners::swap(owners,l,r),ready)'),
}


def source_statement(ident):
    move = ident.startswith('move.')
    variables = 'd,s,b,n,c' if move else 'l,r,a,bl,nl,cl,br,nr,cr'
    return (r'\forall Heap::heap h; \forall Owners::state owners; \forall OwnedEffects::phases ready; \forall integer '
            + variables + '; ' + (MOVE_ACSL if move else SWAP_ACSL) + ' ==> ' + CONCLUSIONS[ident][1])


def source_goal(ident):
    move = ident.startswith('move.')
    return one('(not (forall ('+(MOVE_BIND if move else SWAP_BIND)+') (=> '
               +(MOVE_PRE if move else SWAP_PRE)+' '+CONCLUSIONS[ident][0]+')))')


# Complete independent OwnedEffects interpretation. Heap and Owners are their
# separate pinned source modules, never inferred from unary receiver validity.
DEFINITIONS = {
    'E_is_ready': ('(ready (Array Int Bool)) (r Int)', '(= (select ready r) true)'),
    'E_target': ('(h heap) (r Int)', '(match (contents h r 0) (((Pointer b o) b) ((Integer i) 0)))'),
    'E_size': ('(h heap) (r Int)', '(load_int h r 8)'),
    'E_capacity': ('(h heap) (r Int)', '(load_int h r 16)'),
    'E_receiver': ('(h heap) (r Int)', '(and (typed_writes h r 0 8 8) (typed_writes h r 8 8 8) (typed_writes h r 16 8 8))'),
    'E_header': ('(h heap) (r Int) (b Int) (n Int) (c Int)', '(and (E_receiver h r) (<= 0 n) (<= n c) (<= c 18446744073709551615) (pointer_at h r 0 b 0) (integer_at h r 8 n) (integer_at h r 16 c) (initialized_at h r 0) (initialized_at h r 8) (initialized_at h r 16))'),
    'E_reserved': ('(h heap) (s state) (ready (Array Int Bool)) (r Int)', '(and (O_active_owner s r) (= (select ready r) false) (= (O_buffer s r) 0) (E_receiver h r))'),
    'E_world': ('(h heap) (s state) (ready (Array Int Bool))', '(and (well_formed h) (O_valid s (fresh_id h)) (forall ((r Int)) (=> (O_active_owner s r) (and (E_receiver h r) (=> (= (select ready r) true) (exists ((n Int) (c Int)) (E_header h r (O_buffer s r) n c)))))) (forall ((r Int)) (=> (and (O_active_owner s r) (< 0 (O_buffer s r))) (freeable h (O_buffer s r) 0))))'),
    'E_store_header': ('(h heap) (r Int) (b Int) (n Int) (c Int)', '(put_integer (put_integer (put_pointer h r 0 b 0) r 8 n) r 16 c)'),
    'E_copy_header': ('(h heap) (destination Int) (source Int)', '(E_store_header h destination (E_target h source) (E_size h source) (E_capacity h source))'),
    'E_move': ('(h heap) (destination Int) (source Int)', '(E_store_header (E_copy_header h destination source) source 0 0 0)'),
    'E_moved_phases': ('(ready (Array Int Bool)) (destination Int) (source Int)', '(store (store ready destination true) source true)'),
    'E_swap': ('(h heap) (left Int) (right Int) (a Int)', '(let ((temporary (fresh_id h))) (let ((h1 (begin_automatic h 24 a))) (let ((h2 (E_copy_header h1 temporary left))) (let ((h3 (E_copy_header h2 left right))) (let ((h4 (E_copy_header h3 right temporary))) (end_automatic h4 temporary))))))'),
    'E_incoming_frame': ('(before heap) (after heap) (left Int) (right Int)', '(forall ((b Int)) (=> (issued before b) (and (same_object before after b) (=> (and (not (= b left)) (not (= b right))) (forall ((p Int)) (and (= (contents before b p) (contents after b p)) (= (initialized_at before b p) (initialized_at after b p))))))))'),
    'O_empty': ('(dummy Int)', '(mk_state ((as const (Array Int Bool)) false) ((as const (Array Int Int)) 0))'),
    'O_active_owner': ('(s state) (r Int)', '(= (select (active s) r) true)'),
    'O_buffer': ('(s state) (r Int)', '(select (backing s) r)'),
    'O_exclusive': ('(s state)', '(forall ((r Int) (q Int)) (=> (and (= (select (active s) r) true) (= (select (active s) q) true) (not (= (select (backing s) r) 0)) (= (select (backing s) r) (select (backing s) q))) (= r q)))'),
    'O_valid': ('(s state) (frontier Int)', '(and (< 0 frontier) (O_exclusive s) (forall ((r Int)) (=> (= (select (active s) r) true) (and (< 0 r) (< r frontier) (<= 0 (select (backing s) r)) (< (select (backing s) r) frontier)))) (forall ((r Int) (q Int)) (=> (and (= (select (active s) r) true) (= (select (active s) q) true) (not (= (select (backing s) r) 0))) (not (= (select (backing s) r) q)))))'),
    'O_begin_owner': ('(s state) (r Int)', '(mk_state (store (active s) r true) (store (backing s) r 0))'),
    'O_bind': ('(s state) (r Int) (b Int)', '(mk_state (active s) (store (backing s) r b))'),
    'O_move': ('(s state) (destination Int) (source Int)', '(mk_state (active s) (store (store (backing s) destination (select (backing s) source)) source 0))'),
    'O_swap': ('(s state) (left Int) (right Int)', '(ite (= left right) s (mk_state (active s) (store (store (backing s) left (select (backing s) right)) right (select (backing s) left))))'),
    'O_retire': ('(s state) (r Int)', '(mk_state (store (active s) r false) (store (backing s) r 0))'),
}


def required_definitions(ident):
    selected = symbols(source_goal(ident)) & set(DEFINITIONS)
    while True:
        expanded = selected | set().union(*(symbols(one(DEFINITIONS[name][1])) & set(DEFINITIONS) for name in selected))
        if expanded == selected:
            return selected
        selected = expanded


def ordered_alpha(tree, env=None, level=0, binder_depth=0):
    """A cheaper strict binder-order variant for nine-Int source binders.

    This never permutes quantifiers or connectives. It only renames bound
    variables and expands simultaneous lets. Unknown equivalent reorderings
    remain unresolved rather than paying an unbounded factorial search.
    """
    env = {} if env is None else env
    need(level < 120, 'bounded strict alpha normalization')
    if isinstance(tree, str):
        return env.get(tree, tree)
    need(bool(tree), 'nonempty alpha expression')
    if tree[0] == 'let':
        additions = {name: ordered_alpha(value, env, level+1, binder_depth) for name, value in tree[1]}
        need(len(additions) == len(tree[1]), 'distinct let bindings')
        return ordered_alpha(tree[2], {**env, **additions}, level+1, binder_depth)
    if tree[0] in ('forall', 'exists'):
        need(len(tree) == 3 and len({row[0] for row in tree[1]}) == len(tree[1]), 'closed alpha binder')
        names = {row[0]: '@ordered:%d:%d' % (binder_depth, index) for index, row in enumerate(tree[1])}
        return [tree[0], [row[1] for row in tree[1]], ordered_alpha(tree[2], {**env, **names}, level+1, binder_depth+1)]
    if tree[0] == '!':
        need(len(tree) >= 4 and len(tree) % 2 == 0 and all(isinstance(tree[i], str) and tree[i].startswith(':') for i in range(2, len(tree), 2)), 'closed trigger annotation')
        return ordered_alpha(tree[1], env, level+1, binder_depth)
    return [ordered_alpha(value, env, level+1, binder_depth) for value in tree]


def compare(actual, expected):
    if ordered_alpha(actual) == ordered_alpha(expected):
        return True, 'strict_ordered_alpha_and_simultaneous_let'
    try:
        if canon(actual) == canon(expected):
            return True, 'reviewed_corrected_binder_alpha_and_propositional_order'
    except ValueError:
        pass
    return False, 'unrecognized_source_encoding'


def replace_symbols(tree, aliases):
    return aliases.get(tree, tree) if isinstance(tree, str) else [replace_symbols(value, aliases) for value in tree]


def type_shapes(commands):
    """Selected datatype metadata only; no constructor alias or proof grant."""
    rows = []
    for command in commands:
        if command[0] not in {'declare-datatype', 'declare-datatypes'}:
            continue
        sorts, bodies = (command[1], command[2]) if command[0] == 'declare-datatypes' and len(command) == 3 else ([], [])
        need(isinstance(sorts, list) and isinstance(bodies, list) and len(sorts) == len(bodies) <= 20, 'bounded complete datatype metadata')
        for sort, constructors in zip(sorts, bodies):
            need(isinstance(sort, list) and len(sort) == 2 and isinstance(constructors, list) and len(constructors) <= 20, 'closed datatype declaration metadata')
            fields = [item[1:] for item in constructors if isinstance(item, list) and item]
            expected_heap = [['next', 'Int'], ['allocated', ['Array', 'Int', 'Bool']], ['alive', ['Array', 'Int', 'Bool']], ['dynamic', ['Array', 'Int', 'Bool']], ['writable', ['Array', 'Int', 'Bool']], ['extent', ['Array', 'Int', 'Int']], ['address', ['Array', 'Int', 'Int']], ['memory', ['Array', 'Int', ['Array', 'Int', 'cell']]], ['initialized', ['Array', 'Int', ['Array', 'Int', 'Bool']]]]
            matched = False
            if sort == ['heap', '0']:
                matched = len(constructors) == 1 and fields == [expected_heap]
            elif sort == ['state', '0']:
                matched = len(constructors) == 1 and fields == [[['active', ['Array', 'Int', 'Bool']], ['backing', ['Array', 'Int', 'Int']]]]
            elif sort == ['cell', '0']:
                matched = len(constructors) == 2 and all(isinstance(item, list) and item and item[0] in {'Integer', 'Pointer'} for item in constructors)
                if matched:
                    types = {item[0]: [field[1] for field in item[1:] if isinstance(field, list) and len(field) == 2] for item in constructors}
                    matched = types == {'Integer': ['Int'], 'Pointer': ['Int', 'Int']} and all(len(item)-1 == len(types[item[0]]) for item in constructors)
            descriptors = []
            for item in constructors:
                need(isinstance(item, list) and item and isinstance(item[0], str) and len(item) <= 33, 'bounded constructor metadata')
                need(all(isinstance(field, list) and len(field) == 2 and isinstance(field[0], str) for field in item[1:]), 'closed selector metadata')
                descriptors.append({'name': item[0], 'selectors': [{'name': field[0], 'sort': field[1]} for field in item[1:]]})
            rows.append({'sort': sort[0], 'arity': sort[1], 'constructors': descriptors, 'source_structural_shape_matches': matched, 'declaration_sha256': digest(command), 'constructor_alias_or_encoding_admitted': False})
    return rows


def task_semantics(text, ident, support):
    """Complete cold syntax census, retaining every unresolved obligation.

    This first source9 reader does not invent a Heap/Owners product encoding or
    bless arbitrary declarations. A partial match always remains nonadmission.
    """
    commands = forms(text)
    allowed = {'set-logic', 'set-info', 'set-option', 'declare-sort', 'declare-fun', 'declare-const', 'declare-datatypes', 'declare-datatype', 'define-fun', 'assert', 'check-sat', 'get-info'}
    need(all(isinstance(row, list) and row and row[0] in allowed for row in commands), 'closed complete SMT command census')
    checks = [index for index, row in enumerate(commands) if row[0] == 'check-sat']
    need(len(checks) == 1 and commands[checks[0]] == ['check-sat'] and all(row == ['get-info', ':reason-unknown'] for row in commands[checks[0]+1:]), 'sole complete query and epilogue')
    assertions = [row[1] for row in commands if row[0] == 'assert' and len(row) == 2]
    need(assertions and len(assertions) == sum(row[0] == 'assert' for row in commands), 'complete assertion shapes')
    definitions = [row for row in commands if row[0] == 'define-fun']
    aliases = {}
    for row in definitions:
        need(len(row) == 5 and isinstance(row[1], str), 'complete definition shape')
        base = re.sub(r'\d+$', '', row[1])
        candidates = [name for name, (binding, _) in DEFINITIONS.items() if name[2:] == base and [item[1] for item in one('('+binding+')')] == [item[1] for item in row[2]]]
        if len(candidates) == 1:
            aliases[row[1]] = candidates[0]
    unresolved = [{'kind': 'complete_Heap_Owners_cell_record_and_phase_driver_encoding_pending'}]
    observed = []
    for row in definitions:
        role = aliases.get(row[1])
        matched, normalization = (False, 'unrecognized_definition')
        if role:
            binding, body = DEFINITIONS[role]
            matched, normalization = compare(replace_symbols(['forall', row[2], row[4]], aliases), one('(forall ('+binding+') '+body+')'))
        observed.append({'name': row[1], 'source_role': role, 'form_sha256': digest(row), 'source_equivalent': matched, 'normalization': normalization})
        if not matched:
            unresolved.append({'kind': 'source_or_support_definition', 'name': row[1], 'form_sha256': digest(row)})
    missing = required_definitions(ident) - {row['source_role'] for row in observed if row['source_equivalent']}
    unresolved += [{'kind': 'missing_or_unmatched_required_source_definition', 'role': name} for name in sorted(missing)]
    hypothesis_rows = []
    for value in assertions[:-1]:
        names = symbols(value)
        need(not any(name.startswith(('check_lemma_', 'wp_goal', 'P_t25', 'L_t25')) or 't25_owned_effect' in name for name in names), 'no desired or sibling theorem premise')
        key = digest(value)
        hypothesis_rows.append({'sha256': key, 'symbols': sorted(names), 'primary_source_attribution': support.get(key)})
        if key not in support:
            unresolved.append({'kind': 'support_assertion', 'sha256': key, 'symbols': sorted(names)})
    goal_match, normalization = compare(replace_symbols(assertions[-1], aliases), source_goal(ident))
    if not goal_match:
        unresolved.append({'kind': 'goal_encoding', 'actual_sha256': digest(assertions[-1]), 'source_sha256': digest(source_goal(ident))})
    declarations = [{'kind': row[0], 'name': row[1] if len(row)>1 and isinstance(row[1], str) else None, 'sha256': digest(row)} for row in commands if row[0].startswith('declare-')]
    return {'complete_command_census': [{'index': index, 'kind': row[0], 'sha256': digest(row)} for index, row in enumerate(commands)],
            'goal_sha256': digest(assertions[-1]), 'source_goal_sha256': digest(source_goal(ident)), 'goal_equivalent': goal_match, 'goal_normalization': normalization,
            'definitions': observed, 'hypotheses': hypothesis_rows, 'declarations': declarations, 'type_shapes': type_shapes(commands), 'unresolved': unresolved,
            'source_type_semantics_established': False, 'scientific_acceptance': False, 'actual_submission_attested': False}
