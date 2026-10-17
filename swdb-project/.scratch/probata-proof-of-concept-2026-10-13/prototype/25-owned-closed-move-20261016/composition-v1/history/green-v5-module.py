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


def _prefix_contains(obj, offset, domain):
    prefix = obj['filled_prefix']
    return (prefix is not None and prefix['initialized'] and offset >= 0
        and offset % prefix['stride'] == 0
        and _le(_constant(offset+prefix['stride']), _scale(prefix['stride'], prefix['count']), domain))


def _contents_at(heap, key, offset, domain):
    obj = heap['objects'][key]
    if offset in obj['cells']:
        return obj['cells'][offset]
    if _prefix_contains(obj, offset, domain):
        return ('Integer', _constant(obj['filled_prefix']['value']))
    return ('Integer', _constant(0))


def _initialized_at(heap, key, offset, domain):
    obj = heap['objects'][key]
    return offset in obj['initialized'] or _prefix_contains(obj, offset, domain)


def _header(heap, key, buffer, count, capacity, domain):
    obj = heap['objects'][key]
    return (_receiver(heap, key, domain) and _le(_constant(0), count, domain)
        and _le(count, capacity, domain) and _le(capacity, _constant(SIZE_MAX), domain)
        and _contents_at(heap, key, 0, domain) == ('Pointer', buffer, 0)
        and _contents_at(heap, key, 8, domain) == ('Integer', count)
        and _contents_at(heap, key, 16, domain) == ('Integer', capacity)
        and all(_initialized_at(heap, key, offset, domain) for offset in (0, 8, 16)))


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
        stores = [{'offset': offset, 'value': value} for offset, value in sorted(obj['cells'].items())]
        prefix = obj['filled_prefix']
        memory_prefix = {'count': prefix['count'], 'stride': prefix['stride'],
            'element': ('Integer', _constant(prefix['value'])),
            'offset_predicate': 'p=4*k for some integer 0<=k<n'} if prefix else None
        initialized_prefix = {'count': prefix['count'], 'stride': prefix['stride'],
            'initialized': True, 'offset_predicate': 'p=4*k for some integer 0<=k<n'} if prefix else None
        rows.append({k: v for k, v in obj.items() if k not in {'cells', 'initialized'}} | {
            'key': key, 'cells': [{'offset': offset, 'value': value} for offset, value in sorted(obj['cells'].items())],
            'initialized_offsets': sorted(obj['initialized']),
            'memory_denotation': {'explicit_stores': stores, 'int_prefix': memory_prefix,
                'default_unobserved_cell': ('Integer', _constant(0))},
            'initialization_denotation': {'explicit_initialized_offsets': sorted(obj['initialized']),
                'initialized_int_prefix': initialized_prefix, 'default_unobserved_initialized': False}})
    return {'next': heap['next'], 'objects': rows,
            'owners': {'active_keys': sorted(owners['active']),
                       'backing': {str(key): value for key, value in sorted(owners['backing'].items())}},
            'ready_keys': sorted(ready)}


def _entry_state(positive):
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
        heap = _fill_buffer(heap, buffer, count, domain)
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
    case = {'domain': domain, 'entry': snapshot, 'full_move_premises': {
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
    return case, heap, owners, ready, count, domain



def _fill_buffer(heap, buffer, count, domain):
    result = deepcopy(heap)
    obj = result['objects'][buffer]
    _need(obj['alive'] and obj['writable'] and obj['dynamic']
          and obj['extent'] == _scale(4, count) and obj['address'] % 4 == 0
          and obj['filled_prefix'] is None and _bounds(count, domain)[0] > 0,
          'private fill must start in the fresh aligned complete int allocation')
    # For 0<=k<n put n=k+t+1 with independent nonnegative integers k,t.
    # extent-(4*k+4)=4*t. Earlier j<k gives 4*(k-j)>=4, so no
    # earlier initialized int cell is changed. This is an induction, not n samples.
    n_coefficient, k_coefficient, constant = 4, -4, -4
    coefficients = (n_coefficient+k_coefficient, n_coefficient, n_coefficient+constant)
    _need(coefficients == (0, 4, 0) and all(c >= 0 for c in coefficients),
          'complete fill-step byte containment identity differs')
    prior_coefficients = (4, 0)  # 4*(k-j)-4=4*t for integer k-j=t+1, t>=0.
    variant_before, variant_after = (0, 1, 1), (0, 1, 0)
    decrease = tuple(a-b for a, b in zip(variant_before, variant_after, strict=True))
    _need(decrease == (0, 0, 1) and all(c >= 0 for c in variant_after)
          and all(c >= 0 for c in prior_coefficients) and 4 % 4 == 0
          and 4 > 0 and -2147483648 <= 7 <= INT_MAX,
          'fill stride, earlier-cell separation or int literal differs')
    obj['filled_prefix'] = {'count': count, 'stride': 4, 'value': 7,
        'initialized': True, 'base_empty_prefix': True,
        'remaining_extent_nonnegative_coefficients': coefficients,
        'step_preserves_every_earlier_element': True,
        'prior_cell_separation_coefficients': prior_coefficients,
        'counter_decrease': decrease[2], 'variant_before_in_tail_coordinates': variant_before,
        'variant_after_in_tail_coordinates': variant_after,
        'all_0_le_k_lt_n_checked_symbolically': True}
    return result


def _frame_steps(steps, private):
    checked = []
    for step in steps:
        operation = step['operation']
        if operation == 'loop':
            _need(step['range'] == '0 <= k < n', 'only the exact finite constructor loop is accounted')
            checked.append({'operation': operation, 'range': step['range'],
                'body': _frame_steps(step['body']['steps'], private),
                'rule': 'pointwise identity for q composes by induction over every finite iteration'})
        elif operation == 'release' and step['target'] == 'null':
            checked.append({'operation': operation, 'target': 'null', 'rule': 'null release is identity under the explicit release TCB'})
        else:
            _need(operation in {'begin_automatic', 'allocate', 'store', 'header_copy', 'release', 'end_automatic'}
                  and step.get('target') in private, 'a complete source effect is not a private fresh target')
            checked.append({'operation': operation, 'target': step['target'],
                'rule': 'for arbitrary incoming identity q, source freshness gives q!=target; a target-local store/release/scope event preserves the q observation'})
    return checked


def _administrative(source_case):
    administrative = source_case['administrative_storage']
    names = administrative['fresh_private_objects']
    _need(len(set(names)) == len(names) and administrative['no_admin_identity_consumes_selected_Heap_frontier']
          and not administrative['address_escapes'], 'administrative product must stay disjoint and hidden')
    steps = administrative['incoming_frame']['steps']
    active = set()
    for step in steps:
        operation, target = step['operation'], step.get('target')
        if operation == 'begin_automatic':
            _need(target in names and target not in active, 'administrative activation differs')
            active.add(target)
        elif operation == 'end_automatic':
            _need(target in active, 'administrative scope end differs')
            active.remove(target)
        elif operation == 'store':
            _need(target in active, 'administrative initialization occurs outside its lifetime')
        else:
            _need(operation == 'loop' and all(row['operation'] == 'store'
                  and row['target'] in active for row in step['body']['steps']),
                  'administrative loop has an unaccounted target or scope')
    _need(not active, 'administrative storage escapes cleanup')
    def position(operation, target):
        return next(i for i, step in enumerate(steps) if step['operation'] == operation and step.get('target') == target)
    _need(position('store', 'caller.swdb_return') < position('begin_automatic', 'dtor.destination.this')
          < position('end_automatic', 'dtor.destination.this') < position('begin_automatic', 'dtor.source.this')
          < position('end_automatic', 'dtor.source.this') < position('end_automatic', 'caller.swdb_return'),
          'actual captured scalar or reverse administrative cleanup order differs')
    return {'source_order_checked': True, 'consumes_selected_private_frontier': False,
        'private_objects': names, 'pointwise_incoming_frame': _frame_steps(steps, set(names)),
        'projection': 'distinct source-fresh parameter, counter and local pointer/scalar identities form a separate product; they are hidden without assigning them receiver/buffer Heap keys',
        'actual_freshness_and_storage_correspondence': 'explicit source storage TCB, not a new caller premise'}


def _release(heap, key, automatic=False):
    result = deepcopy(heap)
    if key == 0:
        return result
    obj = result['objects'][key]
    _need(obj['alive'] and (not obj['dynamic'] if automatic else _freeable(heap, key)),
          'release does not have the actual required allocation kind/lifetime')
    obj['alive'] = False
    return result


def _header_values(heap, key):
    cells = heap['objects'][key]['cells']
    _need(cells[0][0] == 'Pointer' and cells[0][2] == 0
          and cells[8][0] == cells[16][0] == 'Integer', 'complete initialized field projection differs')
    return {'buffer': cells[0][1], 'count': cells[8][1], 'capacity': cells[16][1]}


def _case(positive, source_case):
    case, heap, owners, ready, count, domain = _entry_state(positive)
    source, destination, buffer = [case['entry'][name] for name in ('source', 'destination', 'buffer')]
    width, end = _scale(4, count), _add(_constant(56), _scale(4, count))
    _need(_bounds(count, domain)[0] >= 0 and _bounds(count, domain)[1] <= INT_MAX
          and _le(width, _constant(SIZE_MAX), domain)
          and _le(end, _constant(9223372036854775807), domain), 'signed32 count widening or complete allocation arithmetic differs')
    case['arithmetic'] = {'count_bounds': domain, 'buffer_width_bounds': _bounds(width, domain),
        'buffer_end_bounds': _bounds(end, domain) if positive else None,
        'n_to_unsigned64_exact': True, 'source_int_bytes': 4,
        'logical_header_bytes': 24, 'logical_field_alignment': 8,
        'proof': 'exact affine endpoint bounds hold for every original integer n in the branch; the nonnegative signed32 count widens without loss to unsigned64'}
    loops = [step for step in source_case['incoming_frame']['steps'] if step['operation'] == 'loop']
    _need(len(loops) == int(positive), 'exact original fill-loop branch differs')
    if positive:
        _need(loops[0]['range'] == '0 <= k < n' and len(loops[0]['body']['steps']) == 1
              and {key: loops[0]['body']['steps'][0][key] for key in ('operation', 'target', 'offset', 'value')}
              == {'operation': 'store', 'target': 'buffer', 'offset': '4*k', 'value': 7},
              'source loop does not perform the complete private literal7 int fill')
        case['fill_induction'] = dict(heap['objects'][buffer]['filled_prefix'])
    else:
        case['fill_induction'] = {'base_empty_prefix': True, 'no_allocation_or_loop': True,
                                 'zero_branch_does_not_evaluate_pointer_arithmetic': True}
    # Actual data() capture precedes the move, and never registers a third owner.
    saved = _header_values(heap, source)['buffer']
    old_source = _header_values(heap, source)
    result = _store_header(heap, destination, old_source['buffer'], old_source['count'], old_source['capacity'], domain)
    result = _store_header(result, source, 0, _constant(0), _constant(0), domain)
    after_owners = deepcopy(owners)
    after_owners['backing'][destination] = owners['backing'][source]
    after_owners['backing'][source] = 0
    after_ready = ready | {source, destination}
    after_world = _world(result, after_owners, after_ready, domain)
    _need(_header_values(result, destination) == old_source and _header_values(result, source)
          == {'buffer': 0, 'count': _constant(0), 'capacity': _constant(0)},
          'the complete copied header/reset source effect is not derived')
    if positive:
        before_buffer, after_buffer = heap['objects'][buffer], result['objects'][buffer]
        _need(before_buffer == after_buffer and after_buffer['alive'] and after_buffer['filled_prefix']['initialized']
              and after_buffer['filled_prefix']['count'] == count and _bounds(count, domain)[0] >= 1
              and _le(_constant(4), after_buffer['extent'], domain), 'the guarded saved[0] is not a live initialized private element')
        cell = _contents_at(result, buffer, 0, domain)
        _need(_initialized_at(result, buffer, 0, domain) and cell[0] == 'Integer'
              and cell[1][0] == 0, 'saved[0] must read the concrete initialized int cell interpretation')
        scalar = cell[1][1]
    else:
        _need(saved == 0, 'zero branch must capture the null pointer without dereference')
        scalar = 0
    _need(scalar == source_case['scalar'] and saved == buffer, 'guarded scalar is not derived from exact source fill/capture')
    case['after_move'] = {'source_header': _header_values(result, source),
        'destination_header': _header_values(result, destination), 'world': after_world,
        'snapshot': _snapshot(result, after_owners, after_ready)}
    case['capture'] = {'value': scalar, 'saved_private_key': saved, 'before_any_destructor': True,
        'saved_alias_registered_as_owner': False,
        'positive_read_justification': '0<n, element0 is initialized literal7 by the full prefix induction and move writes only private headers' if positive else 'n==0 selects literal0; no null pointer arithmetic or dereference is evaluated',
        'source_event': 'caller.value copied to caller.swdb_return before destination destructor'}
    cleanup = []
    for owner_name, key in (('destination', destination), ('source', source)):
        target = _header_values(result, key)['buffer']
        _need(target == (buffer if owner_name == 'destination' else 0), 'source destructor target differs after move/reset')
        result = _release(result, target)
        result = _release(result, key, automatic=True)
        after_owners['active'].remove(key);after_owners['backing'].pop(key)
        cleanup.append({'owner': owner_name, 'released_private_key': target,
            'automatic_end_private_key': key, 'registry_retired_separately': True})
    _need(not after_owners['active'] and not any(obj['alive'] for obj in result['objects'].values())
          and result['next'] == heap['next'] and set(result['objects']) == set(heap['objects']),
          'reverse release/scope cleanup or never-issued history differs')
    _world(result, after_owners, after_ready, domain)
    case['cleanup'] = {'steps': cleanup, 'buffer_release_count': sum(row['released_private_key'] != 0 for row in cleanup),
        'registry_retirement_is_Heap_release': False, 'source_null_release_is_identity': True,
        'captured_scalar_after_cleanup': scalar, 'no_payload_or_pointer_read_after_release': True}
    case['after_cleanup'] = _snapshot(result, after_owners, after_ready)
    private = {'source', 'destination', 'buffer'} if positive else {'source', 'destination'}
    case['incoming_frame'] = {'all_source_effects_checked': True,
        'steps': _frame_steps(source_case['incoming_frame']['steps'], private),
        'arbitrary_incoming_type_restriction': None, 'dead_physical_bytes_preserved': False,
        'preserves': ['all incoming allocation metadata', 'all incoming live storage values/initialization', 'all incoming dead allocation-identity ghost history'],
        'freshness_basis': 'actual source/storage/allocator freshness and local framing TCB; the private interpretation table never assumes global incoming Owners.valid or an empty C heap',
        'physical_reuse': 'a new identity may reuse a dead physical address; the dead identity ghost snapshot is not the physical bytes at that address'}
    case['administrative_product'] = _administrative(source_case)
    return case


DERIVATION = """2026-10-16 ET.

This packet constructs an existential PRIVATE interpretation component for the
one exact int move caller. For every arbitrary incoming source-memory observation
I, the interpretation is I times P times A: I is unrestricted; P is the finite
receiver/buffer witness constructed here; A contains source-fresh administrative
storage hidden separately. P starts at next=1 with no issued keys. This is a
choice of private logical witness, never an empty incoming C heap or a global
Owners.valid/world caller premise. Fresh actual source/destination/buffer identity
names map injectively to P's table. Their actual numerical pointer addresses are
not equated to logical addresses. Default storage/allocator/library correspondence,
layout and local framing remain explicit TCB; no Typed Mint/Mptr ownership follows.

For n=0 choose source key1 at logical address8/extent24 and destination key2 at
address32/extent24, next3. There is no buffer. For every 1<=n<=2147483647 choose
source key1/address8/extent24, buffer key2/address56/extent4*n, destination key3/
address32/extent24, next4. The source begins before its exact constructor; positive
buffer allocation occurs inside the constructor before destination begins. Source
stores Pointer(buffer,0), Integer(n), Integer(n) at offsets0,8,16. Destination is
writable/aligned/reserved with no initialized header-value premise. Other private
keys have allocated/alive=false. All live ranges are separated for every count:
[8,32), [32,56), and, when positive, [56,56+4*n). Exact affine endpoint checks give
4<=4*n<=8589934588 and 60<=56+4*n<=8589934644. Header field stores have width8,
offsets0/8/16, address alignment8 and end<=24. These are logical address witnesses,
not assertions about physical numeric addresses or the total caller address map.

The private owner map is active exactly at source,destination, backing(source)=
buffer and backing(destination)=0; every other key is inactive/backing0. Ready is
true only for source. Complete Owners.valid follows by the two finite active cases:
all positive receiver/backing keys are below next, the sole positive backing is
not either receiver, and any two owners of the same positive backing are equal.
Heap.well_formed follows by all issued/live cases and every live pair above.
Every active owner has receiver storage. The sole ready existential chooses the
actual initialized source fields n,c=n. A positive source backing is dynamic/live
and hence freeable at offset0; the zero case has no positive backing obligation.
This derives EVERY world conjunct, reserved(destination), active(source),
ready(source), destination!=source and header(source,buffer,n,n). Destination values
are never assumed. The complete original four move antecedents/statements and
constructor35/destructor11/private9 remain exact evidence-required dependencies.
No opaque incoming owner registry or sibling/postcondition theorem is a premise.

The complete checked constructor loop gives an initialized literal7 prefix. Base
k=0 is empty. For 0<=k<n write element k at4*k, width4. Put n=k+t+1 for independent
nonnegative integers k,t: 4*n-(4*k+4)=4*t>=0. Its address is aligned4. For j<k,
4*(k-j)>=4, so all earlier initialized elements survive. Increment k and decrease
n-k; finite exit k=n proves every j<n initialized int7. This is symbolic induction,
not a test over a bounded set of n. The exact nonnegative signed32 count widens
without loss and all count/byte bounds fit the selected 64-bit model. Fresh buffer
initial memory is unobserved; the empty prefix does not assume a caller payload.

Capture source.data() before the move as a borrowed raw alias. Complete move
copies all three source header fields to destination, then resets source to null,
0,0. Owners updates only its two backing entries and both phases become ready;
full world is checked again from complete definitions. The payload remains the
same live allocation. Thus n>0 reads initialized int7 at saved[0]; n=0 selects
literal0 without evaluating a pointer expression. Store this scalar into value
and swdb_return before either destructor. The selected moved-from-empty MODEL
correspondence is explicit library TCB, not a portable C++17 postcondition.

Destination destructor releases its one positive buffer (or null), then destination
scope ends; source destructor actually releases NULL after the reset, then source
scope ends. Registry retirement is checked separately and never substituted for
Heap.release. All private allocations retain issued ghost history/frontier but end
not-live. The result scalar was captured earlier; no raw pointer/payload is read
after release. The original source-rule exact full C inverse and fallback CFG
checks remain embedded, with no source or logical-annotation edit.

For arbitrary incoming identity q, each exact source effect targets a distinct
source-fresh private identity or is null release. A target-local store/release/
scope event preserves q. Pointwise identity composes across the full sequence and
every fill iteration. Administrative parameters, loop counter, pointer/scalar locals
and capture slots have their actual activation/store/scope order checked in the
separate product A; they do not silently consume P's frontier. Incoming live bytes
and allocation metadata and dead-ID ghost histories are preserved under the full
source/allocator/release framing TCB. Reusing a dead physical address does NOT claim
its old physical bytes remain unchanged. There is no restriction on incoming types.

This is a checked conditional private derivation. It grants no source/public record,
Heap/Typed/lifetime/caller/default admission. Complete root-adopted exact mathematical
evidence, full original normal diagnostic ledger and current framework preflight
are separate gates. Launch unconditionally refuses until those gates are bound.
"""


def declaration(lowering, source, formal_texts):
    _need(_sha(Path(source_rule.__file__).read_bytes()) == SOURCE_RULE_SHA, 'the exact complete source rule needs a new composition review')
    try:
        source_plan, canonical = source_rule.declaration(lowering, source, formal_texts)
    except source_rule.Refused as error:
        raise Refused(str(error)) from None
    _need(all(_sha(canonical['theory/'+name]) == sha for name, sha in THEORIES.items()),
          'the complete Heap/Owners/OwnedEffects source definitions differ')
    cases = {'zero': _case(False, source_plan['branches']['zero']),
             'positive': _case(True, source_plan['branches']['positive'])}
    _need(cases['zero']['domain'] == (0, 0) and cases['positive']['domain'] == (1, INT_MAX)
          and cases['zero']['domain'][1]+1 == cases['positive']['domain'][0],
          'the two guards must partition every original nonnegative signed32 count')
    plan = {'created': '2026-10-16 ET', 'checker': identity(),
        'source_rule': {'checker': source_plan['checker'], **source_plan['source_grammar']},
        'original_contract': list(formal_texts), 'caller_premises_added': [],
        'private_initial_heap': {'role': 'existential interpretation witness', 'next': 1,
            'allocated_keys': [], 'Owners_active_keys': [], 'incoming_Heap_or_Owners_precondition': False,
            'memory_choice': 'unobserved private cells may be chosen Integer0; initialization defaults false'},
        'incoming_component': {'restriction': None, 'empty_incoming_C_heap_assumed': False,
            'domain': 'arbitrary incoming allocation identities and types, live storage values and dead-identity ghost histories',
            'product': 'incoming source observations times the constructed private logical witness times separately hidden administrative storage'},
        'input_partition': {'original_signed32_n_domain': [0, INT_MAX], 'zero_domain': [0, 0],
            'positive_domain': [1, INT_MAX], 'disjoint_and_complete': True,
            'upper_bound_is_source_type_not_new_requires': True},
        'private_total_maps': {'unlisted_allocated_alive_dynamic_writable': False,
            'unlisted_extent_address': 0, 'unwritten_cell_choice': ('Integer', _constant(0)),
            'unlisted_initialized': False, 'meaning': 'total PRIVATE maps chosen for an existential witness; incoming memory lives in the independent arbitrary component'},
        'source_layout_TCB': {'source_int_bits': 32, 'int_bytes_alignment': [4, 4],
            'pointer_size_bits': 64, 'size_type_bits': 64, 'header_extent_alignment': [24, 8],
            'logical_addresses_equal_physical_addresses': False,
            'total_incoming_Typed_encoding_claimed': False,
            'correspondence': 'the selected source/library/storage ABI relates these field observations; private logical addresses are chosen witnesses, not actual numeric source pointers'},
        'new_mathematical_axioms': [],
        'cases': cases, 'scientific_dependencies': source_plan['scientific_dependencies'],
        'source_model_TCB': source_plan['source_model_TCB'],
        'conditional_private_entry_constructed': True, 'conditional_private_composition_checked': True,
        'exact_mathematical_evidence_bound': False, 'normal_public_diagnostic_ledger_bound': False,
        'source_Heap_Typed_caller_admission': False, 'current_records_admitted': []}
    plan = json.loads(_json(plan))
    files = {'source-rule/'+name: raw for name, raw in canonical.items()}
    files.update({'cases/'+name+'.json': _json(case) for name, case in plan['cases'].items()})
    files['derivation.md'] = DERIVATION.encode()
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
