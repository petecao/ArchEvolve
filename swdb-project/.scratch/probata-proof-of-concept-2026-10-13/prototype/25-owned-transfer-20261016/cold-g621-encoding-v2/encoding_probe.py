"""2026-10-16 ET. Closed metadata recognizers; no proof or declaration admission.

The complete physical task digest and command census are checked by the observer.
These recognizers describe syntax only. Unknown shapes remain pending. No raw
formula, full source or solver payload is exported.
"""


def record_schema(commands):
    declarations = [c for c in commands if c[0] in ('declare-datatype', 'declare-datatypes')]
    result = {'matching': False, 'declaration_count': len(declarations),
              'declaration_sha256s': [digest(c) for c in declarations]}
    if len(declarations) != 1:
        return result
    declaration = declarations[0]
    # Only the exact monomorphic source record product is eligible. Do not infer
    # a constructor role from a name, an extra datatype or similar selectors.
    if len(declaration) != 3 or declaration[0] != 'declare-datatypes':
        return result
    sorts, bodies = declaration[1:]
    if sorts != [['state', '0']] or not isinstance(bodies, list) or len(bodies) != 1:
        return result
    constructors = bodies[0]
    if not isinstance(constructors, list) or len(constructors) != 1:
        return result
    constructor = constructors[0]
    if not isinstance(constructor, list) or len(constructor) != 3 or not isinstance(constructor[0], str):
        return result
    if constructor[1:] != [['active', ['Array', 'Int', 'Bool']],
                            ['backing', ['Array', 'Int', 'Int']]]:
        return result
    result.update(matching=True, sort='state', constructor=constructor[0],
                  fields=[{'name': 'active', 'index': 'Int', 'value': 'Bool'},
                          {'name': 'backing', 'index': 'Int', 'value': 'Int'}])
    return result


def aliases(tree, constructor):
    if isinstance(tree, str):
        return 'mk_state' if tree == constructor else tree
    return [aliases(value, constructor) for value in tree]


def constant_maps(commands, allowed_hashes):
    assertions = [c[1] for c in commands if len(c) == 2 and c[0] == 'assert']
    results = []
    # Symbols are also bound by the original complete assertion digest. The
    # formula recognizer requires the full universal equality, not its symbols.
    for role, name, value, typ in [('false', 'fc', 'false', 'Bool'),
                                   ('zero', 'fc1', '0', 'Int')]:
        declared = [c for c in commands if c[:2] == ['declare-fun', name]]
        declaration_ok = declared == [['declare-fun', name, [], ['Array', 'Int', typ]]]
        expected = one('(forall ((index Int)) (= (select '+name+' index) '+value+'))')
        candidates = [a for a in assertions if digest(a) == allowed_hashes[role]]
        matches = [a for a in candidates if canon(a) == canon(expected)]
        results.append({'role': role, 'name': name, 'array_index': 'Int',
                        'array_value': typ, 'declaration_exact': declaration_ok,
                        'matching_assertion_count': len(matches),
                        'assertion_sha256': allowed_hashes[role],
                        'full_quantified_formula_matches': declaration_ok and len(candidates) == len(matches) == 1})
    return results


def empty_shape(commands, schema, maps):
    rows = [c for c in commands if c[:2] == ['define-fun', 'empty']]
    result = {'definition_count': len(rows), 'matching': False}
    if len(rows) != 1:
        return result
    row = rows[0]
    result['form_sha256'] = digest(row)
    if not schema['matching'] or not all(r['full_quantified_formula_matches'] for r in maps):
        return result
    if len(row) != 5 or not isinstance(row[2], list) or len(row[2]) != 1:
        return result
    binding = row[2][0]
    if not isinstance(binding, list) or len(binding) != 2 or not isinstance(binding[0], str) or binding[1] != 'Int':
        return result
    result.update(matching=row[3:] == ['state', [schema['constructor'], 'fc', 'fc1']],
                  argument_types=['Int'], ignored_argument=binding[0] not in symbols(row[4]),
                  integer_dummy_signature_matches_source=True)
    return result


def first_difference(actual, expected, path=()):
    """One bounded path/shape/hash row; never serialize either term or atom."""
    if actual == expected:
        return None
    known = {'not','forall','exists','=>','and','or','=','<','<=','>','>=','+','-',
             'select','store','ite','active','backing','active_owner','buffer',
             'exclusive','valid','empty','begin_owner','bind','move','swap','retire','mk_state'}
    def shape(value):
        if isinstance(value,list):
            head=value[0] if value and isinstance(value[0],str) else None
            return {'kind':'list','items':len(value),'operator':head if head in known else None,
                    'unknown_head_sha256':digest(head) if head is not None and head not in known else None}
        return {'kind':'atom','atom_type':type(value).__name__,
                'category':'alpha_binder' if isinstance(value,str) and value.startswith('@') else 'other',
                'sha256':digest(value)}
    if isinstance(actual,list) and isinstance(expected,list) and len(actual)==len(expected):
        heads_differ = actual and expected and isinstance(actual[0],str) and isinstance(expected[0],str) and actual[0]!=expected[0]
        if not heads_differ:
            for index,(left,right) in enumerate(zip(actual,expected)):
                if left!=right:
                    return first_difference(left,right,(*path,index))
    need(len(path)<=120,'bounded canonical mismatch path')
    return {'path':list(path),'actual_shape':shape(actual),'expected_shape':shape(expected),
            'actual_node_sha256':digest(actual),'expected_node_sha256':digest(expected)}


def inspect_task(commands, ident, allowed_hashes, support):
    schema = record_schema(commands)
    maps = constant_maps(commands, allowed_hashes)
    definitions = []
    unresolved = []
    for row in commands:
        if row[0] != 'define-fun':
            continue
        need(len(row) == 5 and isinstance(row[1], str), 'complete definition metadata')
        role = row[1] if row[1] in DEFINITIONS else None
        actual = ['forall', row[2], row[4]]
        # The alias exists only after this task independently proves the exact
        # datatype syntax. No global replacement or name-only admission exists.
        equivalent = role is not None and schema['matching'] and canon(aliases(actual, schema['constructor'])) == canon(definition_expected(role))
        definitions.append({'name': row[1], 'form_sha256': digest(row), 'source_role': role,
                            'equivalent_after_local_schema_check': equivalent})
        if role is None or not equivalent:
            unresolved.append({'kind': 'definition', 'name': row[1], 'sha256': digest(row)})
    assertions = [c[1] for c in commands if c[0] == 'assert' and len(c) == 2]
    need(assertions and len(assertions) == sum(c[0] == 'assert' for c in commands), 'complete assertion census')
    scoped_map_matches = {r['assertion_sha256'] for r in maps if r['full_quantified_formula_matches']}
    support_rows = []
    for assertion in assertions[:-1]:
        value = digest(assertion)
        attributed = value in support
        map_match = value in scoped_map_matches
        support_rows.append({'sha256': value, 'prior_standard_attribution_present': attributed,
                             'scoped_complete_constant_map_match': map_match})
        if not attributed and not map_match:
            unresolved.append({'kind': 'support_assertion', 'sha256': value})
    if not schema['matching']:
        unresolved.append({'kind': 'record_schema'})
    goal = aliases(assertions[-1], schema['constructor']) if schema['matching'] else assertions[-1]
    actual_canonical_goal = canon(goal)
    expected_canonical_goal = canon(source_goal(ident))
    goal_equivalent = schema['matching'] and actual_canonical_goal == expected_canonical_goal
    if not goal_equivalent:
        unresolved.append({'kind': 'goal', 'sha256': digest(assertions[-1])})
    return {'record_schema': schema, 'constant_maps': maps,
            'empty': empty_shape(commands, schema, maps), 'definitions': definitions,
            'goal_equivalent_after_local_schema_check': goal_equivalent,
            'goal_sha256': digest(assertions[-1]), 'support_assertions': support_rows,
            'goal_canonical_sha256': digest(actual_canonical_goal),
            'expected_goal_canonical_sha256': digest(expected_canonical_goal),
            'first_canonical_goal_difference': first_difference(actual_canonical_goal, expected_canonical_goal),
            'unresolved': unresolved, 'scientific_acceptance': False,
            'other_declarations_admitted': False,
            'actual_submission_attested': False}
