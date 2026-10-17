"""2026-10-16 ET. Stronger explicit witnesses for the pending swap header duty.

Original complete premises and overlapping self-swap guards remain intact.
Only conclusion existential introduction changes; no scientific/source admission.
"""
import hashlib
import json
import re
from pathlib import Path

from swdb import vector_owned_swap_header_cases as previous


WITNESSES = (('left', 'nr', 'cr'), ('right', 'nl', 'cl'),
             ('other', 'OwnedEffects::size(h,observed)', 'OwnedEffects::capacity(h,observed)'))
HEADER = ('OwnedEffects::header(OwnedEffects::swap(h,l,r,a),observed,'
          'Owners::buffer(Owners::swap(owners,l,r),observed),')
EXISTENTIAL = r'(\exists integer size,capacity; '+HEADER+'size,capacity))'

PHYSICAL_CONTEXT = {'heap_reallocation.mlw': {'bytes': 8386,
                           'sha256': 'a8f89e41decdbd2890f72e7725590c62134650fde84a18a6ec7fd9d5bd9abbc5'},
 'vector_owned_effects.mlw': {'bytes': 3128,
                              'sha256': '6bfc13341d2faceb5a3fb64bd2d5bff22dd03c52a1fa3d5c4cb39b6e9c83f7f5'},
 'vector_owned_source_view.py': {'bytes': 10583,
                                 'sha256': 'c76c45afc64a84f6d1cbe1e23e05c175dc1b612abb5f23679d40e7db6c43f8f2'},
 'vector_owned_state.mlw': {'bytes': 2389,
                            'sha256': 'a2c295d2c6720a9c8c522f05e19723c2d2d2a32b63f9b198aab03f195269e4b6'},
 'vector_owned_swap_header_cases.py': {'bytes': 7014,
                                       'sha256': 'daa2ff0ec0c854fa28b534792bbdc099ae28a810671226d43494cec863148e03'},
 'vector_owned_swap_parts.py': {'bytes': 11992,
                                'sha256': '99783303b973a29b55d9f6f9e562295a41248699062982c105ac0a97e18a4f6b'},
 'vector_owned_transfer.py': {'bytes': 14594,
                              'sha256': '6fa50d3b0ff6610c541bfa787179b37c6c8b50e4155fb2b0605d00e1eaffd085'}}
KERNEL_DEFINITIONS = {'Heap.automatic_available': ('heap_reallocation.mlw',
                              '  predicate automatic_available (h:heap) (width alignment a:int) =\n'
                              '    0 <= width /\\ 0 < a /\\ 0 < alignment /\\ aligned a alignment /\\\n'
                              '    (forall b:int. live h b -> a <> h.address[b] /\\\n'
                              '      (a+width <= h.address[b] \\/ h.address[b]+h.extent[b] <= a))\n'
                              '  function begin_automatic (h:heap) (width a:int) : heap =\n'
                              '    { h with next = h.next+1;\n'
                              '      allocated = set h.allocated h.next True;\n'
                              '      alive = set h.alive h.next True;\n'
                              '      dynamic = set h.dynamic h.next False;\n'
                              '      writable = set h.writable h.next True;\n'
                              '      extent = set h.extent h.next width;\n'
                              '      address = set h.address h.next a;\n'
                              '      initialized = set h.initialized h.next (fun _ -> False) }\n'
                              '  function end_automatic (h:heap) (b:int) : heap = release h b'),
 'Heap.begin_automatic': ('heap_reallocation.mlw',
                          '  function begin_automatic (h:heap) (width a:int) : heap =\n'
                          '    { h with next = h.next+1;\n'
                          '      allocated = set h.allocated h.next True;\n'
                          '      alive = set h.alive h.next True;\n'
                          '      dynamic = set h.dynamic h.next False;\n'
                          '      writable = set h.writable h.next True;\n'
                          '      extent = set h.extent h.next width;\n'
                          '      address = set h.address h.next a;\n'
                          '      initialized = set h.initialized h.next (fun _ -> False) }\n'
                          '  function end_automatic (h:heap) (b:int) : heap = release h b'),
 'Heap.contents': ('heap_reallocation.mlw',
                   '  function contents (h:heap) (b o:int) : cell = h.memory[b][o]\n'
                   '  predicate initialized_at (h:heap) (b o:int) = h.initialized[b][o] = True\n'
                   '  predicate integer_at (h:heap) (b o v:int) = contents h b o = Integer v\n'
                   '  predicate pointer_at (h:heap) (b o target offset:int) =\n'
                   '    contents h b o = Pointer target offset\n'
                   '  predicate forms (h:heap) (b o:int) =\n'
                   '    live h b /\\ 0 <= o <= h.extent[b]\n'
                   '  predicate can_read (h:heap) (b o width:int) =\n'
                   '    live h b /\\ 0 <= o /\\ 0 < width /\\ o + width <= h.extent[b]\n'
                   '  predicate can_write (h:heap) (b o width:int) =\n'
                   '    can_read h b o width /\\ h.writable[b] = True\n'
                   '  predicate typed_reads (h:heap) (b o width alignment:int) =\n'
                   '    can_read h b o width /\\ aligned (h.address[b]+o) alignment\n'
                   '  predicate typed_writes (h:heap) (b o width alignment:int) =\n'
                   '    can_write h b o width /\\ aligned (h.address[b]+o) alignment\n'
                   '  predicate typed_forms (h:heap) (b o alignment:int) =\n'
                   '    forms h b o /\\ aligned (h.address[b]+o) alignment\n'
                   '  predicate freeable (h:heap) (b o:int) =\n'
                   '    live h b /\\ h.dynamic[b] = True /\\ o = 0'),
 'Heap.end_automatic': ('heap_reallocation.mlw',
                        '  function end_automatic (h:heap) (b:int) : heap = release h b'),
 'Heap.integer_at': ('heap_reallocation.mlw',
                     '  predicate integer_at (h:heap) (b o v:int) = contents h b o = Integer v\n'
                     '  predicate pointer_at (h:heap) (b o target offset:int) =\n'
                     '    contents h b o = Pointer target offset\n'
                     '  predicate forms (h:heap) (b o:int) =\n'
                     '    live h b /\\ 0 <= o <= h.extent[b]\n'
                     '  predicate can_read (h:heap) (b o width:int) =\n'
                     '    live h b /\\ 0 <= o /\\ 0 < width /\\ o + width <= h.extent[b]\n'
                     '  predicate can_write (h:heap) (b o width:int) =\n'
                     '    can_read h b o width /\\ h.writable[b] = True\n'
                     '  predicate typed_reads (h:heap) (b o width alignment:int) =\n'
                     '    can_read h b o width /\\ aligned (h.address[b]+o) alignment\n'
                     '  predicate typed_writes (h:heap) (b o width alignment:int) =\n'
                     '    can_write h b o width /\\ aligned (h.address[b]+o) alignment\n'
                     '  predicate typed_forms (h:heap) (b o alignment:int) =\n'
                     '    forms h b o /\\ aligned (h.address[b]+o) alignment\n'
                     '  predicate freeable (h:heap) (b o:int) =\n'
                     '    live h b /\\ h.dynamic[b] = True /\\ o = 0'),
 'Heap.load_int': ('heap_reallocation.mlw',
                   '  function load_int (h:heap) (b o:int) : int =\n'
                   '    match contents h b o with\n'
                   '    | Integer v -> v\n'
                   '    | Pointer _ _ -> 0\n'
                   '    end'),
 'Heap.put_integer': ('heap_reallocation.mlw',
                      '  function put_integer (h:heap) (b o v:int) : heap =\n'
                      '    { h with memory = set h.memory b (set h.memory[b] o (Integer v));\n'
                      '      initialized = set h.initialized b (set h.initialized[b] o True) }\n'
                      '  function put_pointer (h:heap) (b o target offset:int) : heap =\n'
                      '    { h with memory = set h.memory b (set h.memory[b] o (Pointer target offset));\n'
                      '      initialized = set h.initialized b (set h.initialized[b] o True) }'),
 'Heap.put_pointer': ('heap_reallocation.mlw',
                      '  function put_pointer (h:heap) (b o target offset:int) : heap =\n'
                      '    { h with memory = set h.memory b (set h.memory[b] o (Pointer target offset));\n'
                      '      initialized = set h.initialized b (set h.initialized[b] o True) }'),
 'OwnedEffects.capacity': ('vector_owned_effects.mlw',
                           '  function capacity (h:H.heap) (r:int) : int = H.load_int h r 16'),
 'OwnedEffects.copy_header': ('vector_owned_effects.mlw',
                              '  function copy_header (h:H.heap) (destination source:int) : H.heap =\n'
                              '    store_header h destination (target h source) (size h source) (capacity h '
                              'source)\n'
                              '  function move (h:H.heap) (destination source:int) : H.heap =\n'
                              '    store_header (copy_header h destination source) source 0 0 0\n'
                              '  function moved_phases (ready:phases) (destination source:int) : phases =\n'
                              '    set (set ready destination True) source True'),
 'OwnedEffects.header': ('vector_owned_effects.mlw',
                         '  predicate header (h:H.heap) (r b n c:int) =\n'
                         '    receiver h r /\\ 0 <= n <= c <= 18446744073709551615 /\\\n'
                         '    H.pointer_at h r 0 b 0 /\\ H.integer_at h r 8 n /\\\n'
                         '    H.integer_at h r 16 c /\\ H.initialized_at h r 0 /\\\n'
                         '    H.initialized_at h r 8 /\\ H.initialized_at h r 16'),
 'OwnedEffects.is_ready': ('vector_owned_effects.mlw',
                           '  predicate is_ready (ready:phases) (r:int) = ready[r] = True\n'
                           '  function target (h:H.heap) (r:int) : int =\n'
                           '    match H.contents h r 0 with\n'
                           '    | H.Pointer b _ -> b\n'
                           '    | H.Integer _ -> 0\n'
                           '    end\n'
                           '  function size (h:H.heap) (r:int) : int = H.load_int h r 8\n'
                           '  function capacity (h:H.heap) (r:int) : int = H.load_int h r 16'),
 'OwnedEffects.size': ('vector_owned_effects.mlw',
                       '  function size (h:H.heap) (r:int) : int = H.load_int h r 8\n'
                       '  function capacity (h:H.heap) (r:int) : int = H.load_int h r 16'),
 'OwnedEffects.store_header': ('vector_owned_effects.mlw',
                               '  function store_header (h:H.heap) (r b n c:int) : H.heap =\n'
                               '    H.put_integer (H.put_integer (H.put_pointer h r 0 b 0) r 8 n) r 16 c\n'
                               '  function copy_header (h:H.heap) (destination source:int) : H.heap =\n'
                               '    store_header h destination (target h source) (size h source) (capacity h '
                               'source)\n'
                               '  function move (h:H.heap) (destination source:int) : H.heap =\n'
                               '    store_header (copy_header h destination source) source 0 0 0\n'
                               '  function moved_phases (ready:phases) (destination source:int) : phases =\n'
                               '    set (set ready destination True) source True'),
 'OwnedEffects.swap': ('vector_owned_effects.mlw',
                       '  function swap (h:H.heap) (left right a:int) : H.heap =\n'
                       '    let temporary = H.fresh_id h in\n'
                       '    let h1 = H.begin_automatic h 24 a in\n'
                       '    let h2 = copy_header h1 temporary left in\n'
                       '    let h3 = copy_header h2 left right in\n'
                       '    let h4 = copy_header h3 right temporary in\n'
                       '    H.end_automatic h4 temporary'),
 'OwnedEffects.world': ('vector_owned_effects.mlw',
                        '  predicate world (h:H.heap) (s:O.state) (ready:phases) =\n'
                        '    H.well_formed h /\\ O.valid s (H.fresh_id h) /\\\n'
                        '    (forall r:int. O.active_owner s r ->\n'
                        '      receiver h r /\\\n'
                        '      (ready[r] = True -> exists n,c:int. header h r (O.buffer s r) n c)) /\\\n'
                        '    (forall r:int. O.active_owner s r /\\ 0 < O.buffer s r ->\n'
                        '      H.freeable h (O.buffer s r) 0)'),
 'Owners.active_owner': ('vector_owned_state.mlw',
                         '  predicate active_owner (s:state) (r:int) = s.active[r] = True\n'
                         '  function buffer (s:state) (r:int) : int = s.backing[r]'),
 'Owners.buffer': ('vector_owned_state.mlw', '  function buffer (s:state) (r:int) : int = s.backing[r]'),
 'Owners.swap': ('vector_owned_state.mlw',
                 '  function swap (s:state) (left right:int) : state =\n'
                 '    if left = right then s else\n'
                 '      { s with backing = set (set s.backing left s.backing[right]) right s.backing[left] '
                 '}')}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def identity():
    return {'id': 'vector-owned-swap-header-witness-1',
            'sha256': _sha(_json({'source': _sha(Path(__file__).read_bytes()),
                                  'previous': previous.identity()}))}


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
    tokens = re.findall(r'[A-Za-z_]\w*(?:::[A-Za-z_]\w*)*|[(),]', text)
    if ''.join(tokens) != re.sub(r'\s+', '', text) or len(tokens) > 96:
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


VARIABLE_SORTS = {name: 'integer' for name in (*OUTER_VARIABLES, 'size', 'capacity')}
VARIABLE_SORTS.update(h='heap', owners='owners', ready='phases')
TERM_SIGNATURES = {
    'OwnedEffects::header': (('heap', 'integer', 'integer', 'integer', 'integer'), 'proposition'),
    'OwnedEffects::swap': (('heap', 'integer', 'integer', 'integer'), 'heap'),
    'Owners::swap': (('owners', 'integer', 'integer'), 'owners'),
    'Owners::buffer': (('owners', 'integer'), 'integer'),
    'OwnedEffects::size': (('heap', 'integer'), 'integer'),
    'OwnedEffects::capacity': (('heap', 'integer'), 'integer'),
}


def _sort(term):
    if term[0] == 'variable':
        return VARIABLE_SORTS[term[1]]
    arguments, result = TERM_SIGNATURES[term[1]]
    if tuple(_sort(arg) for arg in term[2]) != arguments:
        raise ValueError('header witness term argument sort differs from exact source')
    return result


def _substitute(term, replacements):
    if term[0] == 'variable':
        return replacements.get(term[1], term)
    return ('call', term[1], tuple(_substitute(arg, replacements) for arg in term[2]))


def _existential_introduction(size, capacity):
    prefix = r'(\exists integer size,capacity; '
    if not EXISTENTIAL.startswith(prefix) or not EXISTENTIAL.endswith(')'):
        raise ValueError('the original two integer existential binders changed')
    body = EXISTENTIAL[len(prefix):-1]
    template = _term(body)
    if _render(template) != HEADER+'size,capacity)':
        raise ValueError('the complete original existential header body changed')
    if _sort(template) != 'proposition':
        raise ValueError('original header body must be a proposition')
    replacements = {'size': _term(size), 'capacity': _term(capacity)}
    if any(_sort(term) != 'integer' for term in replacements.values()):
        raise ValueError('every integer existential witness must have integer sort')
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
        'instance_to_existential_is_sufficient': True,
        'witness_sorts_checked_against_bound_source': True}


def declaration(*, elements=('int',)):
    physical = _physical_context()
    old, previous_files = previous.declaration(elements=elements)
    kernel = _kernel_bindings(previous_files)
    if old['original_statement'] != previous.HEADER_STATEMENT or len(old['obligations']) != 3:
        raise ValueError('the exact original header and three complete cases are required')
    files = {name: raw for name, raw in previous_files.items()
             if not name.startswith('obligations/') and name != 'manifest.json'}
    obligations = []
    for original, (case, size, capacity) in zip(old['obligations'], WITNESSES, strict=True):
        if original['case'] != case or original['statement'].count(EXISTENTIAL) != 1:
            raise ValueError('exact original inner existential or owner case changed')
        explicit, recovery = _existential_introduction(size, capacity)
        statement = original['statement'].replace(EXISTENTIAL, explicit)
        if statement.count(explicit) != 1 or statement.replace(explicit, EXISTENTIAL) != original['statement']:
            raise ValueError('full original quantified case inverse changed')
        recovery['full_statement_inverse_checked'] = True
        goal = 't25_owned_swap_header_witness_'+case
        path = f'obligations/{len(obligations):03d}-{goal}.c'
        reference = 'reference-cases/'+original['path']
        files[reference] = previous_files[original['path']]
        imports = previous_files[original['path']].decode().split('/*@ check lemma ', 1)[0]
        raw = (imports+'/*@ check lemma '+goal+': '+statement+';\n*/\n').encode()
        files[path] = raw
        obligations.append({**original, 'id': original['id']+'.witness', 'goal': goal,
            'path': path, 'statement': statement, 'explicit_header': explicit,
            'witness': {'size': size, 'capacity': capacity}, 'sha256': _sha(raw),
            'existential_introduction': recovery,
            'existential_reference': {'path': reference, 'sha256': original['sha256'],
                'statement': original['statement'], 'role': 'unproved original case; never a theorem premise'}})
    plan = {**old, 'checker': identity(), 'previous_checker': old['checker'],
        'obligations': obligations, 'physical_context': physical, 'kernel_bindings': kernel,
        'reconstruction': {'direction': 'three stronger cases imply the unchanged original universal by existential introduction and exhaustive original guards',
            'previous_partition': old['reconstruction'], 'added_premises': [], 'axioms_added': [],
            'self_swap_excluded': False, 'reverse_implication_claimed': False,
            'all_three_stronger_proofs_required': True, 'recovery_case_priority': ['left', 'right', 'other'],
            'self_swap': 'original left/right guards overlap; recovery may choose left first, but all three independent stronger targets remain required. Both source headers in fullA fix equal size/capacity fields for l==r; no separation premise is added.'},
        'source_admission': 'unsupported: all three stronger proofs, complete cold interpretation and source/lifetime correspondence remain required'}
    files['manifest.json'] = _json(plan)
    return plan, files


def prepare(directory, *, elements=('int',)):
    plan, files = declaration(elements=elements)
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    for name, raw in files.items():
        path = directory/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return plan


def check(directory, *, elements=('int',)):
    plan, files = declaration(elements=elements)
    directory = Path(directory)
    paths = list(directory.rglob('*'))
    parents = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
    if not directory.is_dir() or directory.is_symlink() or \
            any(path.is_symlink() or not (path.is_file() or path.is_dir()) for path in paths) or \
            {str(path.relative_to(directory)) for path in paths if path.is_file()} != set(files) or \
            {str(path.relative_to(directory)) for path in paths if path.is_dir()} != parents:
        raise ValueError('constructive header witness canonical membership differs')
    for name, raw in files.items():
        if (directory/name).read_bytes() != raw:
            raise ValueError('constructive header witness, complete source or reference differs: '+name)
    return plan


def check_launch(directory, *, elements=('int',)):
    check(directory, elements=elements)
    raise ValueError('constructive swap header source/proof route remains unsupported before all three stronger proofs, complete cold and source evidence')
