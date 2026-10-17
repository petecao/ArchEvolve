"""2026-10-16 ET. Author the second source-only public witness slice."""
from pathlib import Path
import hashlib
import pprint

PROJECT = Path(__file__).resolve().parent.parents[3]
path = PROJECT/'swdb/vector_owned_swap_header_witness.py'
expected = {
    'vector_owned_swap_header_cases.py': 'daa2ff0ec0c854fa28b534792bbdc099ae28a810671226d43494cec863148e03',
    'vector_owned_swap_parts.py': '99783303b973a29b55d9f6f9e562295a41248699062982c105ac0a97e18a4f6b',
    'vector_owned_source_view.py': 'c76c45afc64a84f6d1cbe1e23e05c175dc1b612abb5f23679d40e7db6c43f8f2',
    'vector_owned_transfer.py': '6fa50d3b0ff6610c541bfa787179b37c6c8b50e4155fb2b0605d00e1eaffd085',
    'heap_reallocation.mlw': 'a8f89e41decdbd2890f72e7725590c62134650fde84a18a6ec7fd9d5bd9abbc5',
    'vector_owned_state.mlw': 'a2c295d2c6720a9c8c522f05e19723c2d2d2a32b63f9b198aab03f195269e4b6',
    'vector_owned_effects.mlw': '6bfc13341d2faceb5a3fb64bd2d5bff22dd03c52a1fa3d5c4cb39b6e9c83f7f5',
}
pins = {}
for name, sha in expected.items():
    raw = (PROJECT/'swdb'/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == sha
    pins[name] = {'bytes': len(raw), 'sha256': sha}
fragments = {}
for namespace, filename, names in [
    ('OwnedEffects', 'vector_owned_effects.mlw', ('header', 'size', 'capacity', 'world', 'store_header', 'copy_header', 'swap', 'is_ready')),
    ('Heap', 'heap_reallocation.mlw', ('load_int', 'integer_at', 'contents', 'put_integer', 'put_pointer', 'begin_automatic', 'end_automatic', 'automatic_available')),
    ('Owners', 'vector_owned_state.mlw', ('swap', 'buffer', 'active_owner'))]:
    text = (PROJECT/'swdb'/filename).read_text()
    for name in names:
        starts = [text.index(prefix+name+' ') for prefix in ('  function ', '  predicate ') if prefix+name+' ' in text]
        assert len(starts) == 1
        begin = starts[0]
        end = text.find('\n\n', begin)
        if end < 0: end = text.index('\nend', begin)
        fragments[namespace+'.'+name] = (filename, text[begin:end])
s = path.read_text().replace('import json\n', 'import json\nimport re\n')
constants = '\nPHYSICAL_CONTEXT = '+pprint.pformat(pins, sort_dicts=True, width=110)+'\nKERNEL_DEFINITIONS = '+pprint.pformat(fragments, sort_dicts=True, width=110)+'\n'
s = s.replace('\n\ndef _sha(raw):', constants+'\n\ndef _sha(raw):', 1)
helpers = '''

OUTER_VARIABLES = ('h', 'owners', 'ready', 'l', 'r', 'a', 'bl', 'nl', 'cl', 'br', 'nr', 'cr', 'observed')
TERM_ARITIES = {'OwnedEffects::header': 5, 'OwnedEffects::swap': 4, 'Owners::swap': 3,
                'Owners::buffer': 2, 'OwnedEffects::size': 2, 'OwnedEffects::capacity': 2}


def _physical_context():
    here = Path(__file__).parent
    for name, expected in PHYSICAL_CONTEXT.items():
        path = here/name
        if path.is_symlink() or not path.is_file():
            raise ValueError('physical source/kernel context must be regular: '+name)
        raw = path.read_bytes()
        if len(raw) != expected['bytes'] or _sha(raw) != expected['sha256']:
            raise ValueError('exact physical source/kernel context changed: '+name)
    return PHYSICAL_CONTEXT


def _kernel_bindings(files):
    bindings = {}
    for name, (filename, text) in KERNEL_DEFINITIONS.items():
        raw = files['theory/'+filename]
        fragment = text.encode()
        if _sha(raw) != PHYSICAL_CONTEXT[filename]['sha256'] or raw.count(fragment) != 1:
            raise ValueError('exact original kernel definition changed: '+name)
        begin = raw.index(fragment)
        bindings[name] = {'path': 'theory/'+filename, 'begin': begin,
            'end': begin+len(fragment), 'sha256': _sha(fragment), 'container_sha256': _sha(raw)}
    return bindings


def _term(text):
    # This is a closed first-order term grammar, not an ACSL/Why3 parser. Its
    # only application is substitution into the pinned original header body.
    tokens = re.findall(r'[A-Za-z_]\\w*(?:::[A-Za-z_]\\w*)*|[(),]', text)
    if ''.join(tokens) != re.sub(r'\\s+', '', text) or len(tokens) > 96:
        raise ValueError('closed bounded header term required')
    index = 0
    def parse(depth):
        nonlocal index
        if depth > 16 or index >= len(tokens):
            raise ValueError('bounded complete header term required')
        name = tokens[index]; index += 1
        if name in ('(', ')', ','):
            raise ValueError('header term identifier required')
        if index == len(tokens) or tokens[index] != '(':
            if name not in (*OUTER_VARIABLES, 'size', 'capacity'):
                raise ValueError('unbound header term variable')
            return ('variable', name)
        if name not in TERM_ARITIES:
            raise ValueError('unreviewed header term function')
        index += 1
        args = [parse(depth+1)]
        while index < len(tokens) and tokens[index] == ',':
            index += 1; args.append(parse(depth+1))
        if index >= len(tokens) or tokens[index] != ')' or len(args) != TERM_ARITIES[name]:
            raise ValueError('header term delimiter or arity differs')
        index += 1
        return ('call', name, tuple(args))
    result = parse(0)
    if index != len(tokens):
        raise ValueError('trailing header term syntax')
    return result


def _render(term):
    if term[0] == 'variable':
        return term[1]
    return term[1]+'('+','.join(_render(arg) for arg in term[2])+')'


def _variables(term):
    if term[0] == 'variable':
        return {term[1]}
    return set().union(*(_variables(arg) for arg in term[2]))


def _substitute(term, replacements):
    if term[0] == 'variable':
        return replacements.get(term[1], term)
    return ('call', term[1], tuple(_substitute(arg, replacements) for arg in term[2]))


def _existential_introduction(size, capacity):
    prefix = r'(\\exists integer size,capacity; '
    if not EXISTENTIAL.startswith(prefix) or not EXISTENTIAL.endswith(')'):
        raise ValueError('the original two integer existential binders changed')
    body = EXISTENTIAL[len(prefix):-1]
    template = _term(body)
    if _render(template) != HEADER+'size,capacity)':
        raise ValueError('the complete original existential header body changed')
    replacements = {'size': _term(size), 'capacity': _term(capacity)}
    variables = set().union(*(_variables(term) for term in replacements.values()))
    if variables & {'size', 'capacity'} or not variables <= set(OUTER_VARIABLES):
        raise ValueError('existential witness captures a binder or introduces a free name')
    instance = _render(_substitute(template, replacements))
    return instance, {'rule': 'capture-free integer existential introduction',
        'binders': [{'name': name, 'type': 'integer', 'witness': _render(term)}
                    for name, term in replacements.items()],
        'original_existential': EXISTENTIAL, 'instance': instance,
        'outer_universal_variables': list(OUTER_VARIABLES),
        'witness_free_variables': sorted(variables), 'bound_variable_capture': False,
        'instance_to_existential_is_sufficient': True}
'''
s = s.replace('\n\ndef declaration(*, elements=', helpers+'\n\ndef declaration(*, elements=', 1)
s = s.replace("    old, previous_files = previous.declaration(elements=elements)", "    physical = _physical_context()\n    old, previous_files = previous.declaration(elements=elements)\n    kernel = _kernel_bindings(previous_files)", 1)
s = s.replace("        explicit = HEADER+size+','+capacity+')'", "        explicit, recovery = _existential_introduction(size, capacity)")
s = s.replace("        statement = original['statement'].replace(EXISTENTIAL, explicit)", "        statement = original['statement'].replace(EXISTENTIAL, explicit)\n        if statement.count(explicit) != 1 or statement.replace(explicit, EXISTENTIAL) != original['statement']:\n            raise ValueError('full original quantified case inverse changed')\n        recovery['full_statement_inverse_checked'] = True")
s = s.replace("'witness': {'size': size, 'capacity': capacity}, 'sha256': _sha(raw),", "'witness': {'size': size, 'capacity': capacity}, 'sha256': _sha(raw),\n            'existential_introduction': recovery,")
s = s.replace("'obligations': obligations,\n        'reconstruction'", "'obligations': obligations, 'physical_context': physical, 'kernel_bindings': kernel,\n        'reconstruction'")
s = s.replace("'self_swap_excluded': False, 'reverse_implication_claimed': False}", "'self_swap_excluded': False, 'reverse_implication_claimed': False,\n            'all_three_stronger_proofs_required': True, 'recovery_case_priority': ['left', 'right', 'other'],\n            'self_swap': 'original left/right guards overlap; recovery may choose left first, but all three independent stronger targets remain required. Both source headers in fullA fix equal size/capacity fields for l==r; no separation premise is added.'}")
compile(s, str(path), 'exec')
path.write_text(s)
