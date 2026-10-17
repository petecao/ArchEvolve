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
            'allocation_bytes_no_unsigned_wrap': maximum*width <= UINT64_MAX},
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


def _mathematics():
    q = r'\forall TypedPayload::state s; '
    kind = r'\forall TypedPayload::scalar_kind kind; '
    value = r'\forall TypedPayload::payload value; '
    integers = r'\forall integer b,n,k,address; '
    invariant = (r'Heap::well_formed(s.shape) && 0 <= k <= n && '
        r'Heap::bytes(s.shape,b) == TypedPayload::stride(kind)*n && '
        r'Heap::typed_writes(s.shape,b,TypedPayload::stride(kind)*k,TypedPayload::stride(kind),TypedPayload::stride(kind)) && '
        r'TypedPayload::has_kind(kind,value) && TypedPayload::prefix(s,b,k,kind,value)')
    store = r'TypedPayload::put(s,b,TypedPayload::stride(kind)*k,value)'
    rows = [
        ('store.exact_payload', q+kind+value+integers+
         r'TypedPayload::has_kind(kind,value) ==> '
         r'TypedPayload::read('+store+r',b,TypedPayload::stride(kind)*k) == value && '
         r'Heap::initialized_at('+store+r'.shape,b,TypedPayload::stride(kind)*k)'),
        ('allocate.incoming_frame', q+kind+integers+
         r'Heap::well_formed(s.shape) && TypedPayload::available(s,n,address,kind) ==> '
         r'TypedPayload::incoming_frame(s,TypedPayload::allocate(s,n,address,kind))'),
        ('allocate.fresh_extent', q+kind+integers+
         r'Heap::well_formed(s.shape) && TypedPayload::available(s,n,address,kind) ==> '
         r'!Heap::issued(s.shape,s.shape.next) && '
         r'Heap::well_formed(TypedPayload::allocate(s,n,address,kind).shape) && '
         r'Heap::freeable(TypedPayload::allocate(s,n,address,kind).shape,s.shape.next,0) && '
         r'Heap::bytes(TypedPayload::allocate(s,n,address,kind).shape,s.shape.next) == TypedPayload::stride(kind)*n'),
        ('fill.empty', q+kind+value+integers+r'TypedPayload::prefix(s,b,0,kind,value)'),
        ('fill.step', q+kind+value+integers+invariant+r' && k < n ==> '
         r'TypedPayload::prefix('+store+r',b,k+1,kind,value)'),
        ('fill.exit', q+kind+value+integers+invariant+r' && k == n ==> '
         r'\forall integer j; 0 <= j < n ==> '
         r'TypedPayload::read(s,b,TypedPayload::stride(kind)*j) == value && '
         r'Heap::initialized_at(s.shape,b,TypedPayload::stride(kind)*j)'),
        ('default.reflexive', kind+r'\forall TypedPayload::bits64 null_bits; '
         r'TypedPayload::c_equal(TypedPayload::zero(kind,null_bits),TypedPayload::zero(kind,null_bits))'),
        ('value.non_nan_equality_lifting', q+kind+value+integers+
         r'TypedPayload::has_kind(kind,value) && !TypedPayload::is_nan(value) && '
         r'TypedPayload::prefix(s,b,n,kind,value) ==> '
         r'\forall integer j; 0 <= j < n ==> '
         r'TypedPayload::c_equal(TypedPayload::read(s,b,TypedPayload::stride(kind)*j),value)'),
        ('nan.not_reflexive', value+r'TypedPayload::is_nan(value) ==> !TypedPayload::c_equal(value,value)'),
    ]
    return rows


def _payload_semantics(files):
    here = Path(__file__).parent
    path = 'theory/vector_typed_payload.mlw'
    raw = (here/'vector_typed_payload.mlw').read_bytes()
    _need(not any(line.lstrip().startswith((b'axiom ', b'lemma ')) for line in raw.splitlines()),
          'typed payload definitions cannot add imported project proof premises')
    files[path] = raw
    files['theory/heap_reallocation.mlw'] = (here/'heap_reallocation.mlw').read_bytes()
    return {'theory': {'path': path, 'sha256': _sha(raw)},
        'floating_representation': 'nominal binary32/binary64 sign, exponent and fraction bit fields',
        'integer_or_real_surrogate': False,
        'pointer_representation': 'opaque typed int-pointer value category and symbolic 64 representation bits',
        'arbitrary_pointer_bits_admitted': False, 'pointee_validity_or_liveness_implied': False,
        'float_store_preserves_physical_nan_bits_proved': False,
        'pointer_padding_or_representation_copy_proved': False,
        'payload_transport_is_C_equality': False,
        'default_pointer_representation': 'symbolic null representation, never assumed all-zero bits',
        'classification_examples': _classification(),
        'source_typed_encoding_or_IEEE_mode_binding_established': False,
        'non_nan_lifting_is_a_new_caller_requires': False,
        'default_domain_version': 'typed-transport-1',
        'separate_equality_lifting_domain_version': 'typed-transport-non-nan-equality-1'}


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
        'caller_premises_added': [], 'source_admission': False, 'current_model_records_created': [],
        'original_contract_proved': False}
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
