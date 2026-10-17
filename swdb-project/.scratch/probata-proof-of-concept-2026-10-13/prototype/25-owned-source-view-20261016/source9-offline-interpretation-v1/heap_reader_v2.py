"""2026-10-16 ET. Independent source9 Heap interpretation, initially inert.

These typed mathematical definitions are transcribed from the exact retained
Heap module. Actual task equality, complete declarations/support, driver sum
encoding and independent review are required before any mathematical adoption.
There is no solver, project import, source-memory bridge or caller admission.
"""

HEAP_SOURCE = {
    'bytes': 8386,
    'sha256': 'a8f89e41decdbd2890f72e7725590c62134650fde84a18a6ec7fd9d5bd9abbc5',
    'module': 'heap_reallocation.Heap',
}

HEAP_FIELDS = (
    ('next', 'Int'),
    ('allocated', '(Array Int Bool)'),
    ('alive', '(Array Int Bool)'),
    ('dynamic', '(Array Int Bool)'),
    ('writable', '(Array Int Bool)'),
    ('extent', '(Array Int Int)'),
    ('address', '(Array Int Int)'),
    ('memory', '(Array Int (Array Int cell))'),
    ('initialized', '(Array Int (Array Int Bool))'),
)

# Each row is (complete typed parameters, result sort, complete source body).
# mk_heap is only an interpretation name. The real sole record constructor and
# all its selectors must first match HEAP_FIELDS exactly in each task.
HEAP_DEFINITIONS = {
    'H_live': ('(h heap) (b Int)', 'Bool',
        '(and (not (= b 0)) (= (select (alive h) b) true))'),
    'H_issued': ('(h heap) (b Int)', 'Bool',
        '(= (select (allocated h) b) true)'),
    'H_separated': ('(h heap) (b Int) (c Int)', 'Bool',
        '(or (<= (+ (select (address h) b) (select (extent h) b)) (select (address h) c)) '
        '(<= (+ (select (address h) c) (select (extent h) c)) (select (address h) b)))'),
    'H_aligned': ('(p Int) (alignment Int)', 'Bool',
        '(exists ((q Int)) (= p (* alignment q)))'),
    'H_well_formed': ('(h heap)', 'Bool',
        '(and (< 0 (next h)) '
        '(forall ((b Int)) (=> (H_issued h b) (and (< 0 b) (< b (next h))))) '
        '(forall ((b Int)) (=> (H_live h b) '
        '(and (H_issued h b) (<= 0 (select (extent h) b)) (< 0 (select (address h) b))))) '
        '(forall ((b Int) (c Int)) (=> (and (H_live h b) (H_live h c) (not (= b c))) '
        '(and (not (= (select (address h) b) (select (address h) c))) (H_separated h b c)))))'),
    'H_fresh_id': ('(h heap)', 'Int', '(next h)'),
    'H_same_object': ('(before heap) (after heap) (b Int)', 'Bool',
        '(and (= (select (allocated before) b) (select (allocated after) b)) '
        '(= (select (alive before) b) (select (alive after) b)) '
        '(= (select (dynamic before) b) (select (dynamic after) b)) '
        '(= (select (writable before) b) (select (writable after) b)) '
        '(= (select (extent before) b) (select (extent after) b)) '
        '(= (select (address before) b) (select (address after) b)))'),
    'H_contents': ('(h heap) (b Int) (o Int)', 'cell',
        '(select (select (memory h) b) o)'),
    'H_initialized_at': ('(h heap) (b Int) (o Int)', 'Bool',
        '(= (select (select (initialized h) b) o) true)'),
    'H_integer_at': ('(h heap) (b Int) (o Int) (v Int)', 'Bool',
        '(= (H_contents h b o) (Integer v))'),
    'H_pointer_at': ('(h heap) (b Int) (o Int) (target Int) (offset Int)', 'Bool',
        '(= (H_contents h b o) (Pointer target offset))'),
    'H_can_read': ('(h heap) (b Int) (o Int) (width Int)', 'Bool',
        '(and (H_live h b) (<= 0 o) (< 0 width) (<= (+ o width) (select (extent h) b)))'),
    'H_can_write': ('(h heap) (b Int) (o Int) (width Int)', 'Bool',
        '(and (H_can_read h b o width) (= (select (writable h) b) true))'),
    'H_typed_writes': ('(h heap) (b Int) (o Int) (width Int) (alignment Int)', 'Bool',
        '(and (H_can_write h b o width) (H_aligned (+ (select (address h) b) o) alignment))'),
    'H_freeable': ('(h heap) (b Int) (o Int)', 'Bool',
        '(and (H_live h b) (= (select (dynamic h) b) true) (= o 0))'),
    'H_put_integer': ('(h heap) (b Int) (o Int) (v Int)', 'heap',
        '(mk_heap (next h) (allocated h) (alive h) (dynamic h) (writable h) (extent h) (address h) '
        '(store (memory h) b (store (select (memory h) b) o (Integer v))) '
        '(store (initialized h) b (store (select (initialized h) b) o true)))'),
    'H_put_pointer': ('(h heap) (b Int) (o Int) (target Int) (offset Int)', 'heap',
        '(mk_heap (next h) (allocated h) (alive h) (dynamic h) (writable h) (extent h) (address h) '
        '(store (memory h) b (store (select (memory h) b) o (Pointer target offset))) '
        '(store (initialized h) b (store (select (initialized h) b) o true)))'),
    'H_load_int': ('(h heap) (b Int) (o Int)', 'Int',
        '(match (H_contents h b o) (((Integer v) v) ((Pointer target offset) 0)))'),
    'H_automatic_available': ('(h heap) (width Int) (alignment Int) (a Int)', 'Bool',
        '(and (<= 0 width) (< 0 a) (< 0 alignment) (H_aligned a alignment) '
        '(forall ((b Int)) (=> (H_live h b) (and (not (= a (select (address h) b))) '
        '(or (<= (+ a width) (select (address h) b)) '
        '(<= (+ (select (address h) b) (select (extent h) b)) a))))))'),
    'H_begin_automatic': ('(h heap) (width Int) (a Int)', 'heap',
        '(mk_heap (+ (next h) 1) (store (allocated h) (next h) true) '
        '(store (alive h) (next h) true) (store (dynamic h) (next h) false) '
        '(store (writable h) (next h) true) (store (extent h) (next h) width) '
        '(store (address h) (next h) a) (memory h) '
        '(store (initialized h) (next h) ((as const (Array Int Bool)) false)))'),
    'H_release': ('(h heap) (b Int)', 'heap',
        '(ite (= b 0) h (mk_heap (next h) (allocated h) (store (alive h) b false) '
        '(dynamic h) (writable h) (extent h) (address h) (memory h) (initialized h)))'),
    'H_end_automatic': ('(h heap) (b Int)', 'heap', '(H_release h b)'),
}

SCIENTIFIC_ACCEPTANCE = False
SOURCE_HEAP_TYPED_CALLER_ACCEPTANCE = False


# These are the complete eight laws of the observed polymorphic sum encoding.
# Projection laws imply constructor injectivity; the distinct index equations
# imply disjointness; the last law gives exhaustiveness. The two polymorphic
# match equations then agree with either constructor for every result sort.
# This is a datatype interpretation, never an imported desired source theorem.
CELL_LAWS = (
    '(par (a) (forall ((z a) (z1 a) (u Int)) (= (match_cell (Integer u) z z1) z)))',
    '(par (a) (forall ((z a) (z1 a) (u Int) (u1 Int)) (= (match_cell (Pointer u u1) z z1) z1)))',
    '(forall ((u Int)) (= (index_cell (Integer u)) 0))',
    '(forall ((u Int) (u1 Int)) (= (index_cell (Pointer u u1)) 1))',
    '(forall ((u Int)) (= (Integer_proj_1 (Integer u)) u))',
    '(forall ((u Int) (u1 Int)) (= (Pointer_proj_1 (Pointer u u1)) u))',
    '(forall ((u Int) (u1 Int)) (= (Pointer_proj_2 (Pointer u u1)) u1))',
    '(forall ((u cell)) (or (= u (Integer (Integer_proj_1 u))) '
    '(= u (Pointer (Pointer_proj_1 u) (Pointer_proj_2 u)))))',
)

CELL_DECLARATIONS = (
    '(declare-sort cell 0)',
    '(declare-fun Integer (Int) cell)',
    '(declare-fun Pointer (Int Int) cell)',
    '(declare-fun match_cell (par (a) (cell a a) a))',
    '(declare-fun index_cell (cell) Int)',
    '(declare-fun Integer_proj_1 (cell) Int)',
    '(declare-fun Pointer_proj_1 (cell) Int)',
    '(declare-fun Pointer_proj_2 (cell) Int)',
)


def need(value, label):
    if not value:
        raise ValueError(label)


def replace_symbols(tree, aliases):
    """Closed vocabulary renaming; full typed parameter rows remain compared."""
    if isinstance(tree, str):
        return aliases.get(tree, tree)
    return [replace_symbols(item, aliases) for item in tree]


def normalize_source_primitives(tree):
    """Only two source aliases and complete Integer/Pointer projection matches.

    Call after the closed per-task cell declaration/law check. Match binders
    disappear only when the entire branch is its own selected Int field or
    literal zero. No arbitrary selector, constructor or branch is eliminated.
    """
    if isinstance(tree, str):
        return tree
    need(isinstance(tree, list) and tree, 'nonempty complete mathematical term')
    if tree[0] == 'H_fresh_id':
        need(len(tree) == 2, 'exact source fresh_id application')
        return ['next', normalize_source_primitives(tree[1])]
    if tree[0] == 'H_end_automatic':
        need(len(tree) == 3, 'exact source end_automatic application')
        return ['H_release', *(normalize_source_primitives(x) for x in tree[1:])]
    if tree[0] == 'match_cell':
        need(len(tree) == 4, 'complete typed cell match application')
        value, integer, pointer = tree[1:]
        if integer == ['Integer_proj_1', value] and pointer == '0':
            return ['_source9_integer_or_zero', normalize_source_primitives(value)]
        if integer == '0' and pointer == ['Pointer_proj_1', value]:
            return ['_source9_pointer_target_or_zero', normalize_source_primitives(value)]
        raise ValueError('unrecognized complete cell projection match')
    if tree[0] == 'match':
        need(len(tree) == 3 and isinstance(tree[2], list) and len(tree[2]) == 2,
             'complete two-constructor cell source match')
        cases = {}
        for case in tree[2]:
            need(isinstance(case, list) and len(case) == 2 and isinstance(case[0], list),
                 'closed cell constructor branch')
            pattern, body = case
            name = pattern[0]
            need(name in {'Integer', 'Pointer'} and name not in cases
                 and len(pattern) == (2 if name == 'Integer' else 3)
                 and all(isinstance(x, str) for x in pattern[1:])
                 and len(set(pattern[1:])) == len(pattern)-1, 'complete source sum constructor fields')
            cases[name] = (pattern[1:], body)
        need(set(cases) == {'Integer', 'Pointer'}, 'both source constructors required')
        integer, pointer = cases['Integer'], cases['Pointer']
        if integer[1] == integer[0][0] and pointer[1] == '0':
            return ['_source9_integer_or_zero', normalize_source_primitives(tree[1])]
        if integer[1] == '0' and pointer[1] == pointer[0][0]:
            return ['_source9_pointer_target_or_zero', normalize_source_primitives(tree[1])]
        raise ValueError('source match does not have the complete selected projection branches')
    return [normalize_source_primitives(item) if isinstance(item, list) and item else item
            for item in tree]


def task_context(commands, parse, canonical):
    """Check every declaration, complete record products and the cell encoding.

    `parse` and `canonical` are the separately reviewed syntax/alpha helpers.
    No definition body or source goal is accepted by this context alone. The
    caller must reconcile every complete definition/support/goal afterward.
    """
    pending = [commands]
    while pending:
        item = pending.pop()
        if isinstance(item, str):
            need(not item.startswith('_source9_'), 'private interpretation vocabulary cannot occur in actual input')
        else:
            need(isinstance(item, list), 'complete mathematical syntax node')
            pending.extend(item)
    declarations = [row for row in commands if row[0].startswith('declare-')]
    sums = [row for row in declarations if row[0] == 'declare-datatypes'
            and row[1] == [['cell', '0']]]
    abstract = [row for row in declarations if row == ['declare-sort', 'cell', '0']]
    need(len(sums)+len(abstract) == 1, 'exactly one selected complete cell encoding')
    aliases, consumed, support = {}, [], []
    for sort, fields, name in (
        ('heap', HEAP_FIELDS, 'mk_heap'),
        ('state', (('active', '(Array Int Bool)'), ('backing', '(Array Int Int)')), 'mk_state'),
    ):
        rows = [row for row in declarations if row[0] == 'declare-datatypes'
                and row[1] == [[sort, '0']]]
        need(len(rows) == 1 and len(rows[0]) == 3 and len(rows[0][2]) == 1
             and len(rows[0][2][0]) == 1, 'complete single-constructor source record')
        constructor = rows[0][2][0][0]
        expected = [[field, parse(typ)] for field, typ in fields]
        need(isinstance(constructor[0], str) and constructor[1:] == expected,
             'complete ordered record field names and sorts')
        aliases[constructor[0]] = name
        consumed.append(rows[0])
    if sums:
        expected = parse('(declare-datatypes ((cell 0)) '
            '(((Integer (Integer_proj Int)) (Pointer (Pointer_proj Int) (Pointer_proj1 Int)))))')
        need(sums[0] == expected, 'complete native Integer/Pointer datatype fields')
        consumed.append(sums[0])
        mode = 'native_algebraic_sum'
    else:
        mode = 'closed_axiomatized_polymorphic_sum'
        for source in CELL_DECLARATIONS:
            expected = parse(source)
            need(declarations.count(expected) == 1, 'complete exact typed cell declaration')
            consumed.append(expected)
        assertions = [row for row in commands if row[0] == 'assert'][:-1]
        for source in CELL_LAWS:
            target = canonical(parse(source))
            matches = [row for row in assertions if canonical(row[1]) == target]
            need(len(matches) == 1, 'complete unique source sum encoding law')
            support.append(matches[0])
    for name in ('div1', 'mod1'):
        expected = parse('(declare-fun '+name+' (Int Int) Int)')
        need(declarations.count(expected) == 1, 'complete integer division signature')
        consumed.append(expected)
    constants = {}
    fc = parse('(declare-fun fc () (Array Int Bool))')
    if fc in declarations:
        need(declarations.count(fc) == 1, 'unique complete constant-map declaration')
        target = canonical(parse('(forall ((us Int)) (= (select fc us) false))'))
        assertions = [row for row in commands if row[0] == 'assert'][:-1]
        matches = [row for row in assertions if canonical(row[1]) == target]
        need(len(matches) == 1, 'complete typed false-map defining equation')
        consumed.append(fc); support.append(matches[0])
        constants['fc'] = parse('((as const (Array Int Bool)) false)')
    need(len(consumed) == len(declarations) and all(row in consumed for row in declarations),
         'no extra sort, function, constant or record declaration')
    # Candidates are named only after the entire parameter/result signature
    # matches. Complete bodies remain mandatory in the caller's next stage.
    for row in commands:
        if row[0] != 'define-fun':
            continue
        need(len(row) == 5 and isinstance(row[2], list), 'complete typed function definition')
        role = 'H_'+row[1]
        if role in HEAP_DEFINITIONS:
            params, result, _ = HEAP_DEFINITIONS[role]
            need([x[1] for x in row[2]] == [x[1] for x in parse('('+params+')')]
                 and row[3] == parse(result), 'complete Heap parameter/result signature')
            aliases[row[1]] = role
    return {'mode': mode, 'aliases': aliases, 'constants': constants,
            'declarations': consumed, 'sum_and_map_support': support,
            'definition_goal_or_scientific_acceptance': False}


def positional_body(parameters, body):
    """Alpha-rename function arguments by position, never by permutation.

    Function arguments are ordered even when their sorts coincide. Bound local
    variables are protected from substitution, including simultaneous let and
    the two constructor patterns. Private names cannot occur in actual tasks.
    """
    need(all(isinstance(row, list) and len(row) == 2 and isinstance(row[0], str)
             for row in parameters), 'closed typed function parameter rows')
    need(len({row[0] for row in parameters}) == len(parameters), 'unique ordered function parameters')
    environment = {row[0]: '_source9_parameter_'+str(index)
                   for index, row in enumerate(parameters)}
    def rename(tree, env):
        if isinstance(tree, str):
            return env.get(tree, tree)
        need(isinstance(tree, list) and tree, 'nonempty complete positional term')
        if tree[0] in ('forall', 'exists'):
            need(len(tree) == 3 and all(isinstance(row, list) and len(row) == 2 for row in tree[1]),
                 'complete inner binder in positional body')
            local = {key: value for key, value in env.items() if key not in {row[0] for row in tree[1]}}
            return [tree[0], tree[1], rename(tree[2], local)]
        if tree[0] == 'let':
            need(len(tree) == 3 and all(isinstance(row, list) and len(row) == 2 for row in tree[1]),
                 'complete simultaneous let in positional body')
            local = {key: value for key, value in env.items() if key not in {row[0] for row in tree[1]}}
            return ['let', [[row[0], rename(row[1], env)] for row in tree[1]], rename(tree[2], local)]
        if tree[0] == 'match':
            need(len(tree) == 3, 'complete sum match in positional body')
            cases = []
            for pattern, value in tree[2]:
                need(isinstance(pattern, list) and pattern, 'complete constructor pattern')
                local = {key: mapped for key, mapped in env.items() if key not in set(pattern[1:])}
                cases.append([pattern, rename(value, local)])
            return ['match', rename(tree[1], env), cases]
        return [rename(item, env) if isinstance(item, list) and item else
                env.get(item, item) if isinstance(item, str) else item for item in tree]
    return rename(body, environment)


def reconcile_heap_definitions(commands, context, parse, canonical):
    """Compare every observed Heap definition against its complete source body.

    The function's full parameter sorts and result sort are checked by
    task_context. Fixed aliases identify the complete source vocabulary, and
    the sum/false-map rules apply only after their complete context checks.
    Missing source-inlined fresh_id/end_automatic definitions are not invented.
    Other functions/support/goals remain the outer reader's separate duties.
    """
    aliases = {**context['aliases'], **context['constants']}
    matched = []
    for row in commands:
        if row[0] != 'define-fun':
            continue
        role = context['aliases'].get(row[1], '')
        if not role.startswith('H_'):
            continue
        parameters, result, body = HEAP_DEFINITIONS[role]
        expected = positional_body(parse('('+parameters+')'), parse(body))
        actual = positional_body(row[2], row[4])
        def normal(term):
            return canonical(normalize_source_primitives(replace_symbols(term, aliases)))
        need(row[3] == parse(result) and normal(actual) == normal(expected),
             'complete source Heap definition mismatch: '+role)
        matched.append({'name': row[1], 'role': role, 'complete_typed_body_equal': True})
    return matched
