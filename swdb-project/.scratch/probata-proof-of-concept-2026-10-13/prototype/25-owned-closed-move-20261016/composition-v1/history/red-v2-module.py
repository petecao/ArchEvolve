"""2026-10-16 ET. Closed int-move private logical entry construction.

The empty private heap is an existential witness paired with arbitrary incoming
source memory. It is never an incoming C-heap, Owners.valid or Typed premise.
The exact source rule and explicit storage/allocator/library correspondence are
required; scientific evidence and normal diagnostic binding remain separate.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from swdb import vector_owned_move_source as source_rule


class Refused(ValueError):
    pass


INT_MAX = 2147483647
SIZE_MAX = 18446744073709551615
SOURCE_RULE_SHA = '978518aa169bf6975a906a43d96ffe450f9a2e1fefd158cccd338c67b16337bc'
THEORIES = {
    'heap_reallocation.mlw': 'a8f89e41decdbd2890f72e7725590c62134650fde84a18a6ec7fd9d5bd9abbc5',
    'vector_owned_state.mlw': 'a2c295d2c6720a9c8c522f05e19723c2d2d2a32b63f9b198aab03f195269e4b6',
    'vector_owned_effects.mlw': '6bfc13341d2faceb5a3fb64bd2d5bff22dd03c52a1fa3d5c4cb39b6e9c83f7f5',
}


def _need(value, reason):
    if not value:
        raise Refused(reason)


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identity():
    here = Path(__file__).parent
    return {'id': 'vector-owned-move-private-composition-1', 'sha256': _sha(_json({
        'source_rule': source_rule.identity(),
        'module': _sha(Path(__file__).read_bytes()),
        'theories': {name: _sha((here/name).read_bytes()) for name in THEORIES}}))}


# Only affine expressions a*n+b over the original signed32 count are needed.
# Bounds are exact endpoint bounds, not sampling of representative n values.
def _constant(value):
    return (0, value)


def _add(left, right):
    return (left[0]+right[0], left[1]+right[1])


def _scale(factor, value):
    return (factor*value[0], factor*value[1])


def _bounds(value, domain):
    values = [value[0]*n+value[1] for n in domain]
    return min(values), max(values)


def _le(left, right, domain):
    return _bounds(_add(right, _scale(-1, left)), domain)[0] >= 0


def _new(heap, extent, address, dynamic):
    result = deepcopy(heap)
    key = result['next']
    _need(key not in result['objects'] and key > 0, 'logical allocation must be never issued')
    result['objects'][key] = {'allocated': True, 'alive': True,
        'dynamic': dynamic, 'writable': True, 'extent': extent, 'address': address,
        'cells': {}, 'initialized': set(), 'filled_prefix': None}
    result['next'] += 1
    return result, key


def _typed_write(heap, key, offset, width, alignment, domain):
    obj = heap['objects'][key]
    return (key != 0 and obj['allocated'] and obj['alive'] and obj['writable']
        and offset >= 0 and width > 0 and _le(_constant(offset+width), obj['extent'], domain)
        and (obj['address']+offset) % alignment == 0)


def _put(heap, key, offset, value, domain):
    _need(_typed_write(heap, key, offset, 8, 8, domain), 'private header store safety differs')
    result = deepcopy(heap)
    result['objects'][key]['cells'][offset] = value
    result['objects'][key]['initialized'].add(offset)
    return result


def _store_header(heap, key, buffer, count, capacity, domain):
    result = _put(heap, key, 0, ('Pointer', buffer, 0), domain)
    result = _put(result, key, 8, ('Integer', count), domain)
    return _put(result, key, 16, ('Integer', capacity), domain)


def _receiver(heap, key, domain):
    return all(_typed_write(heap, key, offset, 8, 8, domain) for offset in (0, 8, 16))


def _header(heap, key, buffer, count, capacity, domain):
    obj = heap['objects'][key]
    return (_receiver(heap, key, domain) and _le(_constant(0), count, domain)
        and _le(count, capacity, domain) and _le(capacity, _constant(SIZE_MAX), domain)
        and obj['cells'].get(0) == ('Pointer', buffer, 0)
        and obj['cells'].get(8) == ('Integer', count)
        and obj['cells'].get(16) == ('Integer', capacity)
        and {0, 8, 16} <= obj['initialized'])


def _heap_well_formed(heap, domain):
    _need(heap['next'] > 0, 'Heap.next must be positive')
    rows = list(heap['objects'].items())
    for key, obj in rows:
        _need(0 < key < heap['next'] and obj['allocated'], 'every issued private key must precede next')
        if obj['alive']:
            _need(_le(_constant(0), obj['extent'], domain) and obj['address'] > 0,
                  'every live private object has nonnegative extent and positive logical address')
    pairs = []
    for index, (left, a) in enumerate(rows):
        for right, b in rows[index+1:]:
            if a['alive'] and b['alive']:
                separated = (_le(_add(_constant(a['address']), a['extent']), _constant(b['address']), domain)
                    or _le(_add(_constant(b['address']), b['extent']), _constant(a['address']), domain))
                _need(a['address'] != b['address'] and separated,
                      'all live distinct private allocations must be pairwise separated')
                pairs.append([left, right])
    return {'derived': True, 'issued_cases': [key for key, _ in rows],
            'live_pair_cases': pairs, 'other_integer_keys': 'allocated=false and alive=false'}


def _owners_valid(owners, frontier):
    active, backing = owners['active'], owners['backing']
    _need(frontier > 0 and set(backing) == active, 'closed two-owner total map representation differs')
    for receiver in active:
        _need(0 < receiver < frontier and 0 <= backing[receiver] < frontier,
              'every active owner and backing lies below the private frontier')
        for other in active:
            if backing[receiver] != 0:
                _need(backing[receiver] != other, 'a backing key cannot be an active receiver')
                if backing[receiver] == backing[other]:
                    _need(receiver == other, 'nonzero private backing exclusivity failed')
    return {'derived': True, 'active_cases': sorted(active),
            'exclusive_and_receiver_distinct_cases': [[r, q] for r in sorted(active) for q in sorted(active)],
            'other_integer_keys': 'active=false and backing=0'}


def _freeable(heap, key):
    return key in heap['objects'] and key != 0 and heap['objects'][key]['alive'] and heap['objects'][key]['dynamic']


def _world(heap, owners, ready, domain):
    wf = _heap_well_formed(heap, domain)
    valid = _owners_valid(owners, heap['next'])
    witnesses, freeable = [], []
    for receiver in sorted(owners['active']):
        _need(_receiver(heap, receiver, domain), 'every active private receiver must be writable and aligned')
        if receiver in ready:
            cells = heap['objects'][receiver]['cells']
            _need(cells.get(8, (None,))[0] == cells.get(16, (None,))[0] == 'Integer',
                  'a ready header needs actual initialized integer field witnesses')
            _need(_header(heap, receiver, owners['backing'][receiver], cells[8][1], cells[16][1], domain),
                  'world ready existential header is not derived')
            witnesses.append(receiver)
        if owners['backing'][receiver] > 0:
            _need(_freeable(heap, owners['backing'][receiver]), 'every positive owner backing must be freeable at offset0')
            freeable.append(receiver)
    return {'derived': True, 'Heap.well_formed': wf, 'Owners.valid': valid,
            'receiver_cases': sorted(owners['active']), 'ready_header_witnesses': witnesses,
            'positive_freeable_cases': freeable, 'all_other_owner_cases': 'inactive, so both universal implications are vacuous'}


def _snapshot(heap, owners, ready):
    rows = []
    for key, obj in sorted(heap['objects'].items()):
        rows.append({k: v for k, v in obj.items() if k not in {'cells', 'initialized'}} | {
            'key': key, 'cells': [{'offset': offset, 'value': value} for offset, value in sorted(obj['cells'].items())],
            'initialized_offsets': sorted(obj['initialized'])})
    return {'next': heap['next'], 'objects': rows,
            'owners': {'active_keys': sorted(owners['active']),
                       'backing': {str(key): value for key, value in sorted(owners['backing'].items())}},
            'ready_keys': sorted(ready)}


def _entry(positive):
    domain = (1, INT_MAX) if positive else (0, 0)
    count = (1, 0) if positive else _constant(0)
    heap = {'next': 1, 'objects': {}}
    heap, source = _new(heap, _constant(24), 8, False)
    heap = _store_header(heap, source, 0, _constant(0), _constant(0), domain)
    buffer = 0
    chronology = [{'operation': 'begin_automatic', 'source': 'source', 'private_key': source}]
    if positive:
        heap, buffer = _new(heap, _scale(4, count), 56, True)
        heap = _put(heap, source, 0, ('Pointer', buffer, 0), domain)
        heap = _put(heap, source, 16, ('Integer', count), domain)
        heap['objects'][buffer]['filled_prefix'] = {'count': count, 'stride': 4, 'value': 7}
        heap = _put(heap, source, 8, ('Integer', count), domain)
        chronology.append({'operation': 'allocate', 'source': 'buffer', 'private_key': buffer})
    heap, destination = _new(heap, _constant(24), 32, False)
    chronology.append({'operation': 'begin_automatic', 'source': 'destination', 'private_key': destination})
    owners = {'active': {source, destination}, 'backing': {source: buffer, destination: 0}}
    ready = {source}
    world = _world(heap, owners, ready, domain)
    reserved = (destination in owners['active'] and destination not in ready
        and owners['backing'][destination] == 0 and _receiver(heap, destination, domain))
    _need(reserved and source in owners['active'] and source in ready and destination != source
          and _header(heap, source, buffer, count, count, domain), 'complete move entry antecedent differs')
    injection = {row['source']: row['private_key'] for row in chronology}
    _need(len(set(injection.values())) == len(injection) == 2+int(positive), 'finite fresh source/private-key injection differs')
    snapshot = _snapshot(heap, owners, ready)
    snapshot.update(source=source, destination=destination, buffer=buffer)
    return {'domain': domain, 'entry': snapshot, 'full_move_premises': {
        'OwnedEffects.world': world,
        'OwnedEffects.reserved': {'derived': reserved, 'destination_header_values_assumed': False},
        'Owners.active_owner(source)': {'derived': source in owners['active']},
        'OwnedEffects.is_ready(source)': {'derived': source in ready},
        'destination != source': {'derived': destination != source},
        'OwnedEffects.header(source,b,n,n)': {'derived': _header(heap, source, buffer, count, count, domain)}},
        'injection': {'mapping': injection, 'injective': True,
            'source_creation_order': chronology, 'private_keys_claim_global_Heap_next': False,
            'logical_addresses_are_actual_pointer_values': False,
            'basis': 'fresh distinct actual lexical/allocator identities, framed from arbitrary incoming identities, map to this finite table under the explicit source storage/allocator TCB'}}


def declaration(lowering, source, formal_texts):
    _need(_sha(Path(source_rule.__file__).read_bytes()) == SOURCE_RULE_SHA, 'the exact complete source rule needs a new composition review')
    try:
        source_plan, canonical = source_rule.declaration(lowering, source, formal_texts)
    except source_rule.Refused as error:
        raise Refused(str(error)) from None
    _need(all(_sha(canonical['theory/'+name]) == sha for name, sha in THEORIES.items()),
          'the complete Heap/Owners/OwnedEffects source definitions differ')
    cases = {'zero': _entry(False), 'positive': _entry(True)}
    plan = {'created': '2026-10-16 ET', 'checker': identity(),
        'source_rule': {'checker': source_plan['checker'], **source_plan['source_grammar']},
        'original_contract': list(formal_texts), 'caller_premises_added': [],
        'private_initial_heap': {'role': 'existential interpretation witness', 'next': 1,
            'allocated_keys': [], 'Owners_active_keys': [], 'incoming_Heap_or_Owners_precondition': False,
            'memory_choice': 'unobserved private cells may be chosen Integer0; initialization defaults false'},
        'incoming_component': {'restriction': None, 'empty_incoming_C_heap_assumed': False,
            'domain': 'arbitrary incoming allocation identities and types, live storage values and dead-identity ghost histories',
            'product': 'incoming source observations times the constructed private logical witness times separately hidden administrative storage'},
        'cases': cases, 'scientific_dependencies': source_plan['scientific_dependencies'],
        'source_model_TCB': source_plan['source_model_TCB'],
        'conditional_private_entry_constructed': True, 'exact_mathematical_evidence_bound': False,
        'source_Heap_Typed_caller_admission': False, 'current_records_admitted': []}
    plan = json.loads(_json(plan))
    files = {'source-rule/'+name: raw for name, raw in canonical.items()}
    files.update({'cases/'+name+'.json': _json(case) for name, case in plan['cases'].items()})
    files['manifest.json'] = _json(plan)
    return plan, files


def prepare(lowering, source, formal_texts, directory):
    plan, files = declaration(lowering, source, formal_texts)
    directory = Path(directory); directory.mkdir(exist_ok=False)
    for name, raw in files.items():
        path = directory/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    return plan


def check(lowering, source, formal_texts, directory):
    plan, files = declaration(lowering, source, formal_texts)
    directory = Path(directory); paths = list(directory.rglob('*'))
    parents = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
    _need(not directory.is_symlink() and not any(p.is_symlink() or not (p.is_file() or p.is_dir()) for p in paths)
        and {str(p.relative_to(directory)) for p in paths if p.is_file()} == set(files)
        and {str(p.relative_to(directory)) for p in paths if p.is_dir()} == parents,
        'private composition canonical membership or path differs')
    _need(all((directory/name).read_bytes() == raw for name, raw in files.items()),
          'private composition complete source/witness/derivation/dependency differs')
    return plan


def check_launch(lowering, source, formal_texts, directory):
    check(lowering, source, formal_texts, directory)
    raise Refused('complete exact mathematical evidence, normal diagnostic ledger and framework admission remain required')
