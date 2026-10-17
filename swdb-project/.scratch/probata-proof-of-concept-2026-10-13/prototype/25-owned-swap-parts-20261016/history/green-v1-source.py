"""2026-10-16 ET. Exact parts of the original conditional swap-world duty.

Physical source definitions and the complete original antecedent determine every
leaf. This is a pure materializer, never a source or solver admission mechanism.
"""
import hashlib
import json
from pathlib import Path

from swdb import vector_owned_source_view as original


QUANTIFIERS = (r'\forall Heap::heap h; \forall Owners::state owners; '
               r'\forall OwnedEffects::phases ready; '
               r'\forall integer l,r,a,bl,nl,cl,br,nr,cr; ')
PREMISE = (r'OwnedEffects::world(h,owners,ready) && Owners::active_owner(owners,l) && '
           r'Owners::active_owner(owners,r) && OwnedEffects::is_ready(ready,l) && '
           r'OwnedEffects::is_ready(ready,r) && OwnedEffects::header(h,l,bl,nl,cl) && '
           r'OwnedEffects::header(h,r,br,nr,cr) && Heap::automatic_available(h,24,8,a)')
AFTER = 'OwnedEffects::swap(h,l,r,a)'
OWNERS = 'Owners::swap(owners,l,r)'
TARGET = 'OwnedEffects::world('+AFTER+','+OWNERS+',ready)'

# Exact physical source, not a new axiom or an independently stated contract.
DEFINITIONS = {
    'world': ('vector_owned_effects.mlw', '''  predicate world (h:H.heap) (s:O.state) (ready:phases) =
    H.well_formed h /\\ O.valid s (H.fresh_id h) /\\
    (forall r:int. O.active_owner s r ->
      receiver h r /\\
      (ready[r] = True -> exists n,c:int. header h r (O.buffer s r) n c)) /\\
    (forall r:int. O.active_owner s r /\\ 0 < O.buffer s r ->
      H.freeable h (O.buffer s r) 0)'''),
    'receiver': ('vector_owned_effects.mlw', '''  predicate receiver (h:H.heap) (r:int) =
    H.typed_writes h r 0 8 8 /\\ H.typed_writes h r 8 8 8 /\\
    H.typed_writes h r 16 8 8'''),
    'well_formed': ('heap_reallocation.mlw', '''  predicate well_formed (h:heap) =
    0 < h.next /\\
    (forall b:int. issued h b -> 0 < b < h.next) /\\
    (forall b:int. live h b ->
      issued h b /\\ 0 <= h.extent[b] /\\ 0 < h.address[b]) /\\
    (forall b,c:int. live h b /\\ live h c /\\ b <> c ->
      h.address[b] <> h.address[c] /\\ separated h b c)'''),
    'valid': ('vector_owned_state.mlw', '''  predicate valid (s:state) (frontier:int) =
    0 < frontier /\\ exclusive s /\\
    (forall r:int. s.active[r] = True ->
      0 < r < frontier /\\ 0 <= s.backing[r] < frontier) /\\
    (forall r,q:int. s.active[r] = True /\\ s.active[q] = True /\\
      s.backing[r] <> 0 -> s.backing[r] <> q)'''),
    'exclusive': ('vector_owned_state.mlw', '''  predicate exclusive (s:state) =
    forall r,q:int. s.active[r] = True /\\ s.active[q] = True /\\
      s.backing[r] <> 0 /\\ s.backing[r] = s.backing[q] -> r = q'''),
    'active_owner': ('vector_owned_state.mlw', '  predicate active_owner (s:state) (r:int) = s.active[r] = True'),
    'buffer': ('vector_owned_state.mlw', '  function buffer (s:state) (r:int) : int = s.backing[r]'),
    'is_ready': ('vector_owned_effects.mlw', '  predicate is_ready (ready:phases) (r:int) = ready[r] = True'),
    'fresh_id': ('heap_reallocation.mlw', '  function fresh_id (h:heap) : int = h.next'),
    'bytes': ('heap_reallocation.mlw', '  function bytes (h:heap) (b:int) : int = h.extent[b]'),
    'numerical_address': ('heap_reallocation.mlw', '  function numerical_address (h:heap) (b:int) : int = h.address[b]'),
}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def identity():
    return {'id': 'vector-owned-swap-conjunction-1',
            'sha256': _sha(_json({'source': _sha(Path(__file__).read_bytes()),
                                  'original': original.identity()}))}


def _sources(files):
    bindings = {}
    for name, (filename, text) in DEFINITIONS.items():
        raw = files['theory/'+filename]
        fragment = text.encode()
        if raw.count(fragment) != 1:
            raise ValueError('exact swap conclusion source definition changed: '+name)
        begin = raw.index(fragment)
        bindings[name] = {'path': 'theory/'+filename, 'begin': begin,
                          'end': begin+len(fragment), 'sha256': _sha(fragment),
                          'container_sha256': _sha(raw)}
    return bindings


def _parts():
    # observed/other are fresh indices, disjoint from every original binder.
    h, s = AFTER, OWNERS
    fresh = 'Heap::fresh_id('+h+')'
    active = lambda index: 'Owners::active_owner('+s+','+index+')'
    buffer = lambda index: 'Owners::buffer('+s+','+index+')'
    live = lambda index: 'Heap::live('+h+','+index+')'
    address = lambda index: 'Heap::numerical_address('+h+','+index+')'
    return [
        ('heap.frontier', '', '0 < '+fresh),
        ('heap.issued', 'observed', 'Heap::issued('+h+',observed) ==> 0 < observed < '+fresh),
        ('heap.live', 'observed', live('observed')+' ==> Heap::issued('+h+',observed) && '
         '0 <= Heap::bytes('+h+',observed) && 0 < '+address('observed')),
        ('heap.separated', 'observed,other', live('observed')+' && '+live('other')+' && observed != other ==> '
         +address('observed')+' != '+address('other')+' && Heap::separated('+h+',observed,other)'),
        ('owners.frontier', '', '0 < '+fresh),
        ('owners.exclusive', 'observed,other', active('observed')+' && '+active('other')+' && '
         +buffer('observed')+' != 0 && '+buffer('observed')+' == '+buffer('other')+' ==> observed == other'),
        ('owners.ranges', 'observed', active('observed')+' ==> 0 < observed < '+fresh+' && '
         '0 <= '+buffer('observed')+' < '+fresh),
        ('owners.disjoint', 'observed,other', active('observed')+' && '+active('other')+' && '
         +buffer('observed')+' != 0 ==> '+buffer('observed')+' != other'),
        *[('receiver.'+str(offset), 'observed', active('observed')+' ==> '
           'Heap::typed_writes('+h+',observed,'+str(offset)+',8,8)') for offset in (0, 8, 16)],
        ('header.ready', 'observed', active('observed')+' && OwnedEffects::is_ready(ready,observed) ==> '
         r'(\exists integer size,capacity; OwnedEffects::header('+h+',observed,'+buffer('observed')+',size,capacity))'),
        ('freeable.buffer', 'observed', active('observed')+' && 0 < '+buffer('observed')+' ==> '
         'Heap::freeable('+h+','+buffer('observed')+',0)'),
    ]


def declaration(*, elements=('int',)):
    old, previous = original.declaration(elements=elements)
    reference = next(row for row in old['obligations'] if row['id'] == 'swap.owner_correspondence')
    expected = QUANTIFIERS+PREMISE+' ==> '+TARGET
    if reference['statement'] != expected or len(old['obligations']) != 9:
        raise ValueError('complete original swap statement or dependency census changed')
    if any(word in expected for word in ('observed', 'other', 'capacity;')):
        raise ValueError('fresh decomposition index would capture an original variable')
    files = {name: raw for name, raw in previous.items()
             if not name.startswith('obligations/') and name != 'manifest.json'}
    bindings = _sources(files)
    dependencies = []
    for row in old['obligations']:
        name = 'reference-'+row['path']
        files[name] = previous[row['path']]
        if row['id'] != reference['id']:
            dependencies.append({'id': row['id'], 'goal': row['goal'], 'path': name,
                                 'sha256': row['sha256'],
                                 'role': 'unchanged original conditional duty; exact scientific evidence required separately'})
    obligations, groups = [], {name: [] for name in ('heap', 'owners', 'receiver', 'header', 'freeable')}
    imports = ('//@ import \\wp::why3: heap_reallocation::Heap;\n'
               '//@ import \\wp::why3: vector_owned_state::Owners;\n'
               '//@ import \\wp::why3: vector_owned_effects::OwnedEffects;\n')
    for suffix, indices, conclusion in _parts():
        statement = QUANTIFIERS+(r'\forall integer '+indices+'; ' if indices else '')+PREMISE+' ==> ('+conclusion+')'
        ident = 'swap.owner_correspondence.'+suffix
        goal = 't25_owned_swap_parts_'+suffix.replace('.', '_')
        path = f'obligations/{len(obligations):03d}-{goal}.c'
        raw = (imports+'/*@ check lemma '+goal+': '+statement+';\n*/\n').encode()
        files[path] = raw
        group = suffix.split('.')[0]
        groups[group].append(ident)
        obligations.append({'id': ident, 'goal': goal, 'group': group, 'path': path,
                            'kind': 'check_lemma', 'statement': statement,
                            'source_antecedent': PREMISE, 'fresh_universal_indices': indices.split(',') if indices else [],
                            'dependencies': [], 'status': 'pending', 'sha256': _sha(raw)})
    if len(obligations) != 13:
        raise ValueError('complete swap conjunction census changed')
    plan = {**old, 'checker': identity(), 'original_checker': old['checker'],
            'logical_target': reference['id'], 'original_statement': expected,
            'reference_path': 'reference-'+reference['path'], 'reference_sha256': reference['sha256'],
            'reference_role': 'original unproved compound target, never a theorem premise or launched target',
            'complete_source_antecedent': PREMISE, 'obligations': obligations,
            'unchanged_dependencies': dependencies, 'source_definition_bindings': bindings,
            'reconstruction': {'groups': groups, 'added_premises': [], 'axioms_added': [],
                               'equivalence': 'exact definition unfolding and conjunction/universal distribution',
                               'heap': 'four clauses reconstruct Heap.well_formed using exact fresh_id/bytes/numerical_address aliases',
                               'owners': 'four clauses reconstruct Owners.valid; exclusive/active_owner/buffer are exact source definitions',
                               'receiver': 'three offsets reconstruct receiver for every active owner',
                               'header': 'the unchanged existential remains under each active ready owner; no witness or premise is invented',
                               'freeable': 'the exact complete active positive-backing obligation is retained',
                               'world': 'the five groups reconstruct every conjunct of the exact original world definition'},
            'original_timeout_evidence_preserved': True,
            'source_admission': 'unsupported: native complete part evidence, reconstruction and source/lifetime correspondence remain required'}
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
    if directory.is_symlink() or any(path.is_symlink() or not (path.is_file() or path.is_dir()) for path in paths) or \
            {str(path.relative_to(directory)) for path in paths if path.is_file()} != set(files) or \
            {str(path.relative_to(directory)) for path in paths if path.is_dir()} != parents:
        raise ValueError('swap conjunction source/target membership differs')
    for name, raw in files.items():
        if (directory/name).read_bytes() != raw:
            raise ValueError('swap conjunction source, complete premise or conclusion differs: '+name)
    return plan


def check_launch(directory, *, elements=('int',)):
    check(directory, elements=elements)
    raise ValueError('swap source/proof route remains unsupported before complete scientific and source evidence')
