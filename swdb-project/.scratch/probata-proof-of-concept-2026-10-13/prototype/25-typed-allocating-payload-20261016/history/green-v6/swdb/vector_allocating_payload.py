"""2026-10-16 ET. Checked original allocating scalar-payload constructor sources.

The isolated typed-payload route keeps the original version2 C contracts intact.
It never treats payload transport as an IEEE equality proof, a physical memory
encoding or a caller admission. Every actual tool/evidence gate is separate.
"""
import ast
import hashlib
import json
from pathlib import Path

from swdb import std_models


class Refused(ValueError):
    pass


PARENT = {'id': 'swdb-std-models-2',
          'sha256': 'cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2'}
HEAP_SHA256 = 'a8f89e41decdbd2890f72e7725590c62134650fde84a18a6ec7fd9d5bd9abbc5'
ELEMENTS = ('float', 'double', 'int *')
MEMBERS = ('ctor_count', 'ctor_count_value', 'copy_ctor')
UINT64_MAX = 18446744073709551615
PTRDIFF64_MAX = 9223372036854775807


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def _need(value, reason):
    if not value:
        raise Refused(reason)


def _registry():
    raw = Path(__file__).with_name('c_lowering.py').read_bytes()
    text = raw.decode()
    declarations, values = [], {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in {'INTEGER_TYPES', 'FLOAT_TYPES', 'INTERNAL_TYPES'}:
            name = node.targets[0].id
            _need(name not in values, 'duplicate scalar type registry declaration')
            value = ast.literal_eval(node.value)
            values[name] = sorted(value) if isinstance(value, set) else value
            literal = ast.get_source_segment(text, node).encode()
            declarations.append({'name': name, 'sha256': _sha(literal), 'bytes': len(literal)})
    _need(set(values) == {'INTEGER_TYPES', 'FLOAT_TYPES', 'INTERNAL_TYPES'}
          and {'float', 'double'} <= set(values['FLOAT_TYPES']) and 'int' in values['INTEGER_TYPES'],
          'literal original scalar type domain changed')
    return {'source_module': 'c_lowering.py', 'container_sha256': _sha(raw),
            'declarations': sorted(declarations, key=lambda row: row['name']),
            'canonical_values': values, 'canonical_sha256': _sha(_json(values))}


def identity():
    registry = _registry()
    return {'id': 'vector-allocating-typed-payload-1', 'sha256': _sha(_json({
        'source': _sha(Path(__file__).read_bytes()),
        'typed_theory': _sha(Path(__file__).with_name('vector_typed_payload.mlw').read_bytes()),
        'heap_theory': _sha(Path(__file__).with_name('heap_reallocation.mlw').read_bytes()), 'parent_model': PARENT,
        'literal_type_registry': registry['declarations'], 'type_values': registry['canonical_sha256']}))}


def _body(vector, element, member):
    copy = member == 'copy_ctor'
    count = 'other->size' if copy else 'n'
    comparison = 'other->data[j]' if copy else ('value' if member == 'ctor_count_value' else '0')
    fill = 'other->data[k]' if copy else ('value' if member == 'ctor_count_value' else f'({element})0')
    suffix = 'ptr' if element == 'int *' else element
    return ('{\n'
        '  this->data = NULL; this->size = 0; this->capacity = 0;\n'
        f'  if ({count} == 0) return;\n'
        f'  this->data = swdb_alloc_{"int_"+suffix if element == "int *" else suffix}({count});   /* allocation succeeds (assumption entry) */\n'
        f'  this->capacity = {count};\n'
        f'  /*@ loop invariant 0 <= k <= {count};\n'
        f'      loop invariant \\forall integer j; 0 <= j < k ==> this->data[j] == {comparison};\n'
        '      loop invariant \\initialized(this->data + (0 .. k - 1));\n'
        f'      loop assigns k, this->data[0 .. {count} - 1];\n'
        f'      loop variant {count} - k; */\n'
        f'  for (size_t k = 0; k < {count}; ++k) this->data[k] = {fill};\n'
        f'  this->size = {count};\n'+'}')


def _layout(vector, element):
    width = 4 if element == 'float' else 8
    extra = (' && FLT_RADIX == 2 && FLT_MANT_DIG == 24 && FLT_MAX_EXP == 128' if element == 'float'
             else ' && FLT_RADIX == 2 && DBL_MANT_DIG == 53 && DBL_MAX_EXP == 1024' if element == 'double' else '')
    return (f'\n/* Conditional target layout; these assertions have not been executed. */\n'
        f'_Static_assert(CHAR_BIT == 8 && sizeof(size_t) == 8 && _Alignof(size_t) == 8 &&\n'
        f'               sizeof(ptrdiff_t) == 8 && sizeof(void *) == 8 && _Alignof(void *) == 8 &&\n'
        f'               sizeof({element}) == {width} && _Alignof({element}) == {width}{extra} &&\n'
        f'               sizeof({vector}) == 24 && _Alignof({vector}) == 8 &&\n'
        f'               offsetof({vector}, data) == 0 && offsetof({vector}, size) == 8 &&\n'
        f'               offsetof({vector}, capacity) == 16, "typed constructor target layout");\n').encode()


def _source(element, member, raw):
    vector = 'std_vector_'+('int_ptr' if element == 'int *' else element)
    function = vector+'_'+member
    original = std_models.model_text(function)
    _need(original is not None and isinstance(raw, bytes) and raw == original.encode(),
          'complete original model/helper/contract source differs: '+function)
    params = f'{vector} *this, const {vector} *other' if member == 'copy_ctor' else f'{vector} *this, size_t n'
    if member == 'ctor_count_value':
        params += ', '+('int *value' if element == 'int *' else element+' value')
    signature = 'static void '+function+'('+params+') '
    _need(original.count(signature) == 1 and original.split(signature)[1] == _body(vector, element, member),
          'complete constructor body, loop annotations or effect grammar differs: '+function)
    prefix = b'#include <stddef.h>\n#include <stdint.h>\n#include <limits.h>\n#include <float.h>\n'
    view = prefix+raw+_layout(vector, element)
    count = 'other->size' if member == 'copy_ctor' else 'n'
    width = 4 if element == 'float' else 8
    maximum = min(PTRDIFF64_MAX, UINT64_MAX//width)
    row = {'function': function, 'element': element, 'member': member,
        'original_path': 'original/'+function+'.c', 'original_sha256': _sha(raw),
        'view_path': 'views/'+function+'.c', 'view_sha256': _sha(view),
        'original_range': [len(prefix), len(prefix)+len(raw)],
        'original_contract_modified': False, 'source_effects_checked': True,
        'layout_assertions_executed': False, 'original_contract_proved': False,
        'element_access': 'typed copy or typed zero store; no arithmetic or pointee access',
        'loop': {'unbounded': True, 'count': count, 'stride': width, 'variant': count+' - k',
                 'source_read': 'other->data[k]' if member == 'copy_ctor' else None,
                 'destination_store': 'this->data[k]', 'allocator_calls_positive_branch': 1,
                 'payload_reads_or_writes_zero_branch': 0},
        'numeric_source_domain': {'size_t_bits': 64, 'signed_ptrdiff_bits': 64,
            'maximum_count': maximum, 'maximum_bytes': maximum*width,
            'maximum_one_past_offset': maximum*width,
            'allocation_bytes_no_unsigned_wrap': maximum*width <= UINT64_MAX,
            'target_layout_executed': False,
            'applicability': 'conditional typed source/domain image, not an extra original requires clause',
            'original_readable_to_full_byte_bound_proved': False,
            'source_object_extent_and_separation_discharge_required': member == 'copy_ctor',
            'count_constructor_original_max_size_clause_unchanged': member != 'copy_ctor'},
        'source_requires_unchanged': ['valid writable receiver', 'count within original max_size']
            if member != 'copy_ctor' else ['valid writable receiver', 'original readable source', 'separated receivers'],
        'source_events': ['zero receiver pointer/size/capacity', 'return on zero count',
            'fresh typed allocation', 'set capacity', 'loop begin private k', 'typed payload copy/fill',
            'loop end private k', 'set size'],
        'source_frame': {'writes': ['receiver fields', 'fresh backing element objects', 'fresh loop counter'],
            'copy_source_read_only': member == 'copy_ctor', 'frees': [], 'pointer_escape': False,
            'incoming_live_bytes_and_identity_history_require_frame': True,
            'dead_physical_bytes_preserved': False}}
    return row, raw, view


def _classification():
    # These are independent worked IEEE interchange-format witnesses. Neither
    # native Python float nor a scalar integer stands in for a payload.
    examples = [('float.nan', '0'+'1'*8+'1'+'0'*21+'1', 8),
                ('double.nan', '0'+'1'*11+'1'+'0'*50+'1', 11),
                ('float.negative_zero', '1'+'0'*31, 8),
                ('double.positive_infinity', '0'+'1'*11+'0'*52, 11)]
    rows = []
    for name, bits, exponent_width in examples:
        width = 32 if exponent_width == 8 else 64
        _need(len(bits) == width and set(bits) <= {'0', '1'}, 'complete symbolic IEEE payload bit fields required')
        exponent, fraction = bits[1:1+exponent_width], bits[1+exponent_width:]
        nan = set(exponent) == {'1'} and '1' in fraction
        rows.append({'id': name, 'sign': bits[0], 'exponent_bits': exponent,
            'fraction_bits': fraction, 'same_typed_payload': True, 'is_nan': nan,
            'self_C_equal': not nan, 'source_or_hardware_encoding_proved': False})
    return rows


def _relation_examples():
    def fp(element, sign, exponent, fraction):
        expected = (8, 23) if element == 'float' else (11, 52)
        _need(len(exponent) == expected[0] and len(fraction) == expected[1]
              and sign in ('0', '1') and set(exponent+fraction) <= {'0', '1'},
              'symbolic complete IEEE relation witness required')
        return {'element': element, 'sign': sign, 'exponent': exponent, 'fraction': fraction,
                'is_nan': set(exponent) == {'1'} and '1' in fraction,
                'is_zero': '1' not in exponent+fraction}
    def pointer(category, token, bits):
        _need(category in ('null', 'encoded') and len(bits) == 64 and set(bits) <= {'0', '1'}
              and isinstance(token, str), 'typed nominal pointer witness required')
        return {'element': 'int *', 'category': category, 'value_token': token, 'representation_bits': bits}
    f_nan = fp('float', '0', '1'*8, '1'+'0'*21+'1')
    d_nan = fp('double', '0', '1'*11, '1'+'0'*50+'1')
    rows = [
        ('float.nan_payload_change', f_nan, fp('float', '1', '1'*8, '1'+'0'*20+'10')),
        ('double.nan_payload_change', d_nan, fp('double', '1', '1'*11, '1'+'0'*49+'10')),
        ('float.nan_to_infinity', f_nan, fp('float', '0', '1'*8, '0'*23)),
        ('cross_format.nan', f_nan, d_nan),
        ('float.signed_zero_change', fp('float', '0', '0'*8, '0'*23), fp('float', '1', '0'*8, '0'*23)),
        ('pointer.same_value_changed_representation', pointer('encoded', 'alpha', '0'*63+'1'),
         pointer('encoded', 'alpha', '1'+'0'*62+'1')),
        ('pointer.null_changed_representation', pointer('null', '', '0'*64), pointer('null', '', '1'*64)),
        ('pointer.changed_value_same_bits', pointer('encoded', 'alpha', '0'*63+'1'),
         pointer('encoded', 'beta', '0'*63+'1'))]
    result = []
    for name, left, right in rows:
        same_kind = left['element'] == right['element']
        nan_pair = same_kind and left.get('is_nan', False) and right.get('is_nan', False)
        if same_kind and left['element'] == 'int *':
            c_equal = (left['category'] == right['category'] and
                       (left['category'] == 'null' or left['value_token'] == right['value_token']))
        else:
            c_equal = bool(same_kind and not left.get('is_nan', False) and not right.get('is_nan', False)
                           and (left == right or left.get('is_zero', False) and right.get('is_zero', False)))
        result.append({'id': name, 'left': left, 'right': right, 'exact_payload': left == right,
            'C_equal': c_equal, 'value_copy': bool(c_equal or nan_pair),
            'source_or_hardware_transport_admitted': False,
            'pointer_bitpatterns_or_pointees_admitted': False})
    return result


def _mathematics():
    q = r'\forall TypedPayload::state s; '
    kind = r'\forall TypedPayload::scalar_kind kind; '
    value = r'\forall TypedPayload::payload value; '
    integers = r'\forall integer b,n,k,address; '
    h = r'TypedPayload::objects(s)'
    width = r'TypedPayload::stride(kind)'
    region = (r'Heap::well_formed('+h+r') && 0 < n && 0 <= k <= n && '
        r'Heap::bytes('+h+r',b) == '+width+r'*n && '
        r'Heap::typed_writes('+h+r',b,0,'+width+r'*n,'+width+r')')
    invariant = region+r' && TypedPayload::has_kind(kind,value) && TypedPayload::prefix(s,b,k,kind,value)'
    store = r'TypedPayload::put(s,b,TypedPayload::stride(kind)*k,value)'
    stored_h = r'TypedPayload::objects('+store+r')'
    allocated = r'TypedPayload::allocate(s,n,address,kind)'
    allocated_h = r'TypedPayload::objects('+allocated+r')'
    fresh = r'Heap::fresh_id('+h+r')'
    copy_q = r'\forall TypedPayload::state before; '+q+kind+r'\forall integer source; '+integers
    copy_invariant = (region+r' && source != b && TypedPayload::image(s,source,n,kind) && '
        r'TypedPayload::source_unchanged(before,s,source,n,kind) && TypedPayload::copied(before,s,source,b,k,kind)')
    copy_store = r'TypedPayload::put(s,b,'+width+r'*k,TypedPayload::read(s,source,'+width+r'*k))'
    class_invariant = region+r' && TypedPayload::has_kind(kind,value) && TypedPayload::class_prefix(s,b,k,kind,value)'
    class_copy_invariant = (region+r' && source != b && TypedPayload::image(s,source,n,kind) && '
        r'TypedPayload::source_unchanged(before,s,source,n,kind) && TypedPayload::class_copied(before,s,source,b,k,kind)')
    stored_q = r'\forall TypedPayload::payload stored; '
    class_store = r'TypedPayload::put(s,b,'+width+r'*k,stored)'
    rows = [
        ('store.exact_payload', q+kind+value+integers+
         r'TypedPayload::has_kind(kind,value) ==> '
         r'TypedPayload::read('+store+r',b,TypedPayload::stride(kind)*k) == value && '
         r'Heap::initialized_at('+stored_h+r',b,TypedPayload::stride(kind)*k)'),
        ('store.other_cell_frame', q+kind+value+integers+r'\forall integer observed,offset; '
         r'observed != b || offset != '+width+r'*k ==> '
         r'TypedPayload::read('+store+r',observed,offset) == TypedPayload::read(s,observed,offset) && '
         r'(Heap::initialized_at('+h+r',observed,offset) <==> Heap::initialized_at('+stored_h+r',observed,offset)) && '
         r'Heap::same_object('+h+r','+stored_h+r',observed)'),
        ('allocate.incoming_frame', q+kind+integers+
         r'Heap::well_formed('+h+r') && TypedPayload::available(s,n,address,kind) ==> '
         r'TypedPayload::incoming_frame(s,'+allocated+r')'),
        ('allocate.fresh_extent', q+kind+integers+
         r'Heap::well_formed('+h+r') && TypedPayload::available(s,n,address,kind) ==> '
         r'!Heap::issued('+h+r','+fresh+r') && Heap::well_formed('+allocated_h+r') && '
         r'Heap::freeable('+allocated_h+r','+fresh+r',0) && '
         r'Heap::bytes('+allocated_h+r','+fresh+r') == '+width+r'*n'),
        ('allocate.uninitialized', q+kind+integers+
         r'Heap::well_formed('+h+r') && TypedPayload::available(s,n,address,kind) ==> '
         r'\forall integer j; 0 <= j < n ==> !Heap::initialized_at('+allocated_h+r','+fresh+r','+width+r'*j)'),
        ('fill.empty', q+kind+value+integers+r'TypedPayload::prefix(s,b,0,kind,value)'),
        ('fill.access', q+kind+integers+region+r' && k < n ==> '
         r'Heap::typed_writes('+h+r',b,'+width+r'*k,'+width+r','+width+r')'),
        ('fill.step', q+kind+value+integers+invariant+r' && k < n ==> '
         r'TypedPayload::prefix('+store+r',b,k+1,kind,value)'),
        ('fill.exit', q+kind+value+integers+invariant+r' && k == n ==> '
         r'\forall integer j; 0 <= j < n ==> '
         r'TypedPayload::read(s,b,TypedPayload::stride(kind)*j) == value && '
         r'Heap::initialized_at('+h+r',b,TypedPayload::stride(kind)*j)'),
        ('copy.empty', copy_q+r'TypedPayload::copied(before,s,source,b,0,kind)'),
        ('copy.step', copy_q+copy_invariant+r' && k < n ==> '
         r'TypedPayload::copied(before,'+copy_store+r',source,b,k+1,kind) && '
         r'TypedPayload::source_unchanged(before,'+copy_store+r',source,n,kind)'),
        ('copy.exit', copy_q+copy_invariant+r' && k == n ==> '
         r'\forall integer j; 0 <= j < n ==> '
         r'TypedPayload::read(s,b,'+width+r'*j) == TypedPayload::read(before,source,'+width+r'*j) && '
         r'Heap::initialized_at('+h+r',b,'+width+r'*j)'),
        ('default.reflexive', kind+r'\forall TypedPayload::bits64 null_bits; '
         r'TypedPayload::c_equal(TypedPayload::zero(kind,null_bits),TypedPayload::zero(kind,null_bits))'),
        ('value.non_nan_equality_lifting', q+kind+value+integers+
         r'TypedPayload::has_kind(kind,value) && !TypedPayload::is_nan(value) && '
         r'TypedPayload::prefix(s,b,n,kind,value) ==> '
         r'\forall integer j; 0 <= j < n ==> '
         r'TypedPayload::c_equal(TypedPayload::read(s,b,TypedPayload::stride(kind)*j),value)'),
        ('copy.non_nan_equality_lifting', copy_q+
         r'TypedPayload::copied(before,s,source,b,n,kind) && TypedPayload::image(before,source,n,kind) && '
         r'TypedPayload::reflexive_image(before,source,n,kind) ==> '
         r'\forall integer j; 0 <= j < n ==> '
         r'TypedPayload::c_equal(TypedPayload::read(s,b,'+width+r'*j),TypedPayload::read(before,source,'+width+r'*j))'),
        ('nan.not_reflexive', value+r'TypedPayload::is_nan(value) ==> !TypedPayload::c_equal(value,value)'),
        ('value_copy.reflexive', kind+value+r'TypedPayload::has_kind(kind,value) ==> TypedPayload::value_copy(value,value)'),
        ('class_fill.step', q+kind+value+stored_q+integers+class_invariant+
         r' && k < n && TypedPayload::has_kind(kind,stored) && TypedPayload::value_copy(stored,value) ==> '
         r'TypedPayload::class_prefix('+class_store+r',b,k+1,kind,value)'),
        ('class_fill.exit', q+kind+value+integers+class_invariant+r' && k == n ==> '
         r'\forall integer j; 0 <= j < n ==> TypedPayload::value_copy(TypedPayload::read(s,b,'+width+r'*j),value) && '
         r'Heap::initialized_at('+h+r',b,'+width+r'*j)'),
        ('class_copy.step', copy_q+stored_q+class_copy_invariant+
         r' && k < n && TypedPayload::has_kind(kind,stored) && '
         r'TypedPayload::value_copy(stored,TypedPayload::read(s,source,'+width+r'*k)) ==> '
         r'TypedPayload::class_copied(before,'+class_store+r',source,b,k+1,kind) && '
         r'TypedPayload::source_unchanged(before,'+class_store+r',source,n,kind)'),
        ('class_copy.exit', copy_q+class_copy_invariant+r' && k == n ==> '
         r'\forall integer j; 0 <= j < n ==> '
         r'TypedPayload::value_copy(TypedPayload::read(s,b,'+width+r'*j),TypedPayload::read(before,source,'+width+r'*j)) && '
         r'Heap::initialized_at('+h+r',b,'+width+r'*j)'),
    ]
    return rows


def _source_derivation(members):
    elements = {}
    subtract = lambda a, b: [x-y for x, y in zip(a, b, strict=True)]
    for element in ELEMENTS:
        width = 4 if element == 'float' else 8
        n, k, one = [1, 1, 1], [1, 0, 0], [0, 0, 1]
        remainder = [width*x for x in subtract(subtract(n, k), one)]
        after = subtract(subtract(n, k), one)
        distance = [width*x for x in subtract([1, 1, 1], [0, 1, 0])]
        decrease = subtract(subtract(n, k), after)
        maximum = min(PTRDIFF64_MAX, UINT64_MAX//width)
        _need(width in (4, 8) and remainder == [0, width, 0] and distance == [width, 0, width]
              and after == [0, 1, 0] and decrease == [0, 0, 1]
              and all(x >= 0 for x in remainder+distance+after)
              and maximum*width <= UINT64_MAX and maximum <= PTRDIFF64_MAX,
              'unbounded typed stride/access/variant derivation failed')
        elements[element] = {'stride': width, 'maximum_count': maximum, 'maximum_bytes': maximum*width,
            'step_substitution': 'n = k + remaining + 1; k = j + distance + 1',
            'remainder_basis': ['k', 'remaining', '1'], 'distance_basis': ['distance', 'j', '1'],
            'remaining_after_store_coefficients': remainder, 'earlier_store_distance_coefficients': distance,
            'remaining_after_increment_coefficients': after, 'variant_decrease': decrease[2],
            'all_nonnegative_parameters_checked': True,
            'store_cases': ['j = k: exact typed payload and initialization',
                            'j < k: positive stride distance; map-store keeps prior element',
                            'different incoming identity: map-store keeps every typed value/init cell'],
            'alignment_rule': 'base is stride-aligned; offset is stride*k; no actual pointer integer conversion',
            'zero_case': 'no allocation, no payload read/store, no loop-counter activation; original header zeros only'}
    _need(len(members) == 9 and all(row['source_effects_checked'] for row in members),
          'complete source constructor grammar must precede interpretation')
    return {'elements': elements, 'whole_source_body_rule_checked': True,
        'mathematical_solver_acceptance_claimed': False,
        'incoming_frame': {
            'observed_allocations': 'every issued incoming identity, including dead identities and non-int objects',
            'observed_live_payloads': 'all live incoming source bytes/typed values and initialization outside the original assigns *this region',
            'new_identity_not_previously_issued': True, 'dead_physical_bytes_preserved': False,
            'metadata_rule': 'well_formed bounds every issued key below next; allocate selects next, so all old allocation/lifetime metadata is unchanged',
            'payload_rule': 'fresh backing identity differs from every incoming issued identity; finite header stores affect only original assigns *this region',
            'source_binding_still_required': True},
        'copy': {'source_read_only_preserved_at_every_step': True,
            'source_destination_disjointness': 'fresh backing identity differs from every issued incoming source identity',
            'source_header_and_backing_image_required_before_receiver_zeroing': True,
            'receiver_source_backing_separation_derived_from_source_creation': False,
            'source_read_typed_and_initialized': 'full source image and source_unchanged induction hypothesis; no pointee load for int*',
            'non_nan_condition_is_not_added_to_original_source_requires': True},
        'administrative_storage': {
            'loop_counter': 'fresh automatic size_t k, initialized zero, bounded increment and variant; scope end after loop',
            'receiver_and_parameters': 'receiver storage is original declared assigns region; initialized count/value or source pointer arguments are required source images',
            'arbitrary_incoming_administrative_separation_established': False},
        'interpretation': 'checked source effect/induction derivation into an explicitly conditional typed logical product; not physical C execution correspondence'}


def _payload_semantics(files):
    here = Path(__file__).parent
    path = 'theory/vector_typed_payload.mlw'
    raw = (here/'vector_typed_payload.mlw').read_bytes()
    _need(not any(line.lstrip().startswith((b'axiom ', b'lemma ')) for line in raw.splitlines()),
          'typed payload definitions cannot add imported project proof premises')
    files[path] = raw
    heap = (here/'heap_reallocation.mlw').read_bytes()
    _need(_sha(heap) == HEAP_SHA256, 'typed source candidate requires the reviewed unchanged Heap definitions')
    files['theory/heap_reallocation.mlw'] = heap
    return {'theory': {'path': path, 'sha256': _sha(raw)},
        'heap_theory': {'path': 'theory/heap_reallocation.mlw', 'sha256': HEAP_SHA256},
        'floating_representation': 'nominal binary32/binary64 sign, exponent and fraction bit fields',
        'integer_or_real_surrogate': False,
        'pointer_representation': 'opaque typed int-pointer value category and symbolic 64 representation bits',
        'arbitrary_pointer_bits_admitted': False, 'pointee_validity_or_liveness_implied': False,
        'float_store_preserves_physical_nan_bits_proved': False,
        'pointer_padding_or_representation_copy_proved': False,
        'payload_transport_is_C_equality': False,
        'default_pointer_representation': 'symbolic null representation, never assumed all-zero bits',
        'classification_examples': _classification(),
        'relation_examples': _relation_examples(),
        'source_typed_encoding_or_IEEE_mode_binding_established': False,
        'non_nan_lifting_is_a_new_caller_requires': False,
        'default_domain_version': 'typed-transport-1',
        'separate_equality_lifting_domain_version': 'typed-transport-non-nan-equality-1',
        'proposed_model_successor_relation': 'TypedPayload.value_copy',
        'proposed_relation_retains_same_format_nan_class_without_bit_identity': True,
        'original_FP_contract_requires_reviewed_model_successor': True,
        'non_nan_carveout_is_permanent_source_admission_policy': False,
        'pointer_value_token': 'nominal noninteger token; no address/provenance/pointee relation granted'}


def _derivation_text(plan):
    return ("""# Typed allocating constructor derivation

Date: 2026-10-16 ET.

This is a checked source grammar/effect interpretation and a candidate
mathematical derivation. It is not a physical C/Typed encoding, a solver result,
a model-body record or source/caller admission. The original nine C units,
including their clauses and logical annotations, are unchanged and retained.

The original FP count/value and copy postconditions and loop invariants use
element equality. A positive NaN fill/copy does not establish that equality.
The original contracts need a separately reviewed model successor. The exact
bit-transport candidate and the proposed value/class relation are distinct:
same-format NaNs may retain their class while their payload/sign/quiet bits
change. No relation between different FP formats is granted. Signed zero may
compare equal without bit identity. No operation converts a payload to int or
real, performs FP arithmetic, or assumes reflexive C equality for NaN.

Pointer payloads contain an abstract noninteger value token/category and a
separate symbolic representation. Same token with changed representation can
denote the same pointer value. Different tokens with the same representation
are not thereby equated. A null representation remains symbolic. These
mathematical values do not grant arbitrary raw-bit source validity or any
pointee validity, ownership, lifetime, bounds or dereference.

An arbitrary incoming source-memory component I is paired with the selected
receiver region R, fresh backing region F, and private automatic counter A.
I is not empty and is not restricted to the payload datatype. This product is
an interpretation condition to discharge from source storage and allocation;
it is not a new library caller requires or an opaque global Owners premise.
The original assigns *this region is permitted to change. Every other incoming
live byte/value/init observation and every incoming allocation identity/history
is framed if that source-domain separation is established. Dead physical
addresses may be reused; dead physical bytes are not claimed preserved.

For a positive count n and stride w in {4,8}, allocate selects logical next.
well_formed places every issued old identity strictly below next; hence no old
issued identity, live or dead, equals the new backing key. available supplies
the candidate alignment and live-range separation. The new extent is w*n,
not the existing int allocator's hard-coded 4*n. Initial payloads remain
uninitialized. Actual source allocator freshness, valid aligned writable
storage, freeability and framing are explicit unproved implementation TCB.

The exact source zero branch returns after three header stores, with no
allocation, payload access or counter lifetime. For positive n the checked
body allocates once, stores capacity, fills/copies, ends k's scope, then stores
size. No extra callee, pointer escape, free, arbitrary annotation or effect is
accepted by the full-source equality and whole-body grammar checks.

The empty prefix is vacuous. At k<n substitute n=k+remaining+1, remaining>=0.
The store ends at w*(k+1), leaving w*remaining bytes. For earlier j<k substitute
k=j+distance+1; byte distance is w*(distance+1)>0, so the exact map store keeps
every earlier cell and initialization observation. The counter increases
without size_t overflow under the conditional original max_size byte bounds;
n-k decreases by one. The exit invariant contains k=n and a whole writable
region, not a contradictory requirement to write the one-past element.

Copy additionally maintains the full unchanged source image and either an
exact copied prefix or value/class-copied prefix. Its fresh destination key
differs from the source key, so each put keeps every source cell/init entry.
The original readable/receiver-separated precondition alone is not asserted
to imply all byte bounds or receiver/source-backing separation before the
initial receiver stores. Source-created object/storage images must discharge
those conditions. No source-frame or desired sibling theorem is an opaque
premise of another mathematical leaf.

For class filling/copying, stored is quantified separately from input, has the
same scalar kind, and satisfies value_copy to the input/source element.
The step preserves the previous class prefix and adds the current relation;
it never requires stored bits equal input bits. The relation is reflexive for
NaNs by the same-format class arm, not by C equality. Exact bit transport is a
stronger candidate useful only when a selected implementation justifies it.

All emitted leaves retain their complete mathematical premises and no project
lemma dependencies. Their parsing, normal full WP/Why3 native outcome,
goal/property/CSV/task/import/support closure and actual source/mode/allocator
bindings remain pending. The source/library/allocation and representation
TCB is explicit in manifest.json; allocation success alone supplies no frame.
check_launch always refuses until separately reviewed actual evidence and
public admission exist. No historical record or model identity is rewritten.

Checked unbounded affine certificates:

"""+json.dumps(plan['checked_source_derivation']['elements'], sort_keys=True, indent=2)+'\n').encode()


def declaration(*, model_sources=None):
    _need(std_models.identity() == PARENT, 'original model change requires independent typed-source remapping')
    expected = ['std_vector_'+('int_ptr' if element == 'int *' else element)+'_'+member
                for element in ELEMENTS for member in MEMBERS]
    if model_sources is None:
        model_sources = {name: std_models.model_text(name).encode() for name in expected}
    _need(isinstance(model_sources, dict) and set(model_sources) == set(expected),
          'exactly the nine original typed allocating constructor units are required')
    files, members = {}, []
    for element in ELEMENTS:
        for member in MEMBERS:
            function = 'std_vector_'+('int_ptr' if element == 'int *' else element)+'_'+member
            row, original, view = _source(element, member, model_sources[function])
            members.append(row)
            files[row['original_path']] = original
            files[row['view_path']] = view
            problematic = element != 'int *' and member != 'ctor_count'
            row['original_equality_contract'] = {
                'original_equality_clauses_retained': True,
                'arbitrary_IEEE_domain_established': False,
                'positive_nan_counterexample_to_reflexive_equality': problematic,
                'separate_lifting_domain': ('every copied/fill payload is not NaN; distinct conditional mathematics only'
                                             if problematic else 'typed default or stable initialized pointer value'),
                'new_source_requires_added': False, 'WP_real_mode_is_IEEE_evidence': False}
    semantics = _payload_semantics(files)
    obligations = []
    for index, (name, statement) in enumerate(_mathematics()):
        goal = 't25_typed_payload_'+name.replace('.', '_')
        path = f'obligations/{index:03d}-{goal}.c'
        raw = ('//@ import \\wp::why3: heap_reallocation::Heap;\n'
               '//@ import \\wp::why3: vector_typed_payload::TypedPayload;\n'
               '/*@ check lemma '+goal+': '+statement+';\n*/\n').encode()
        files[path] = raw
        obligations.append({'id': name, 'goal': goal, 'kind': 'check_lemma', 'path': path,
                            'statement': statement, 'sha256': _sha(raw), 'dependencies': [], 'status': 'pending'})
    plan = {'created': '2026-10-16 ET', 'version': 1, 'checker': identity(),
        'parent_model': dict(PARENT), 'type_registry': _registry(), 'source_members': members,
        'typed_payload': semantics, 'mathematical_obligations': obligations,
        'checked_source_derivation': _source_derivation(members),
        'incoming_source_component': {
            'memory': 'arbitrary incoming I, except the declared receiver write region R',
            'restricted_to_payload_datatype': False, 'empty_incoming_heap_assumed': False,
            'total_Typed_memory_encoding_claimed': False, 'opaque_global_Owners_premise': False,
            'product': 'I × receiver R × fresh typed backing F × private counter A',
            'source_created_storage_separation_and_mapping_established': False},
        'allocator_library_TCB': {
            'plain_library_assumption_required': std_models.SENTENCE_LIBRARY,
            'plain_allocation_success_assumption_required': std_models.SENTENCE_ALLOCATION,
            'allocation_success_alone_establishes_frame': False,
            'explicit_conditions': [
                'actual initialized typed receiver/count/value/source objects and selected target ABI/storage layout',
                'allocation result is fresh in never-issued identity history, valid writable aligned for the selected element type, freeable, and independent of receiver/source storage',
                'allocation and eventual release frame every preexisting live source object outside declared receiver assigns; source callbacks/interposition must obey this frame',
                'selected scalar assignment and FP environment implement the checked typed value/class relation; physical exact NaN/signaling/pointer-bit transport is not generally assumed',
                'pointer values have an admitted initialized source representation and stable nominal value/category; raw arbitrary bits, pointee validity, dereference and lifetime do not follow',
                'original max_size/count/byte arithmetic, complete original clause/CFG/access/init/frame/RTE ledger and actual selected tool/model mode must be bound'],
            'physical_representation_transport_proved': False,
            'selected_FP_environment_or_pointer_ABI_bound': False,
            'free_or_release_executed_in_constructor': False,
            'source_replacement_free_inferred_from_std_allocator_name': False},
        'caller_premises_added': [], 'source_admission': False, 'current_model_records_created': [],
        'source_Heap_Typed_bridge_established': False, 'mathematical_evidence_bound': False,
        'original_contract_proved': False,
        'pending_gates': ['independent source/semantic reviews',
            'actual normal complete mathematical/native/task/hypothesis/import/support audit',
            'typed object/storage/allocator/representation correspondence and complete source ordinary obligation ledger',
            'reviewed IEEE-aware original model successor, explicit model identity and consumer rebinding',
            'actual public compiler/model/caller/framework admission']}
    derivation = _derivation_text(plan)
    files['derivation.md'] = derivation
    plan['derivation'] = {'path': 'derivation.md', 'sha256': _sha(derivation), 'bytes': len(derivation)}
    files['manifest.json'] = _json(plan)
    return plan, files


def prepare(directory, *, model_sources=None):
    plan, files = declaration(model_sources=model_sources)
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    for name, raw in files.items():
        path = directory/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return plan


def check(directory, *, model_sources=None):
    plan, files = declaration(model_sources=model_sources)
    directory = Path(directory)
    paths = list(directory.rglob('*'))
    parents = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
    _need(directory.is_dir() and not directory.is_symlink()
          and all(not path.is_symlink() and (path.is_file() or path.is_dir()) for path in paths)
          and {str(path.relative_to(directory)) for path in paths if path.is_file()} == set(files)
          and {str(path.relative_to(directory)) for path in paths if path.is_dir()} == parents,
          'typed constructor canonical membership differs')
    for name, raw in files.items():
        _need((directory/name).read_bytes() == raw, 'typed constructor canonical input differs: '+name)
    return plan


def check_launch(directory, *, model_sources=None):
    check(directory, model_sources=model_sources)
    raise Refused('actual mathematical evidence, typed source/allocator/compiler correspondence and public admission remain required')
