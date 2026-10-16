"""Source-derived no-growth caller diagnostic view; created 2026-10-16 ET.

Inlining preserves the original reserve body and adds a duty to prove its branch
false. Construction, alias capture, guarded scalar capture and cleanup remain C.
This is not a lifetime abstraction: actual Typed+Var correspondence remains open,
so no public dispatcher or launch is admitted by this module.
"""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from swdb import std_models, vector_reallocation_calls, vector_reallocation_lifetime
from swdb.vector_reallocation_caller_packets import _contract_count


class Refused(ValueError):
    pass


RUNTIME_SOURCES = [
    ('MemTyped.ml', 'ad0d3c4e8e568a09d47bb658767e5ba476cc9e957f16b14981370642c5e235b5'),
    ('MemVar.ml', '43b8979a169ccfb7c6e7183970a8d3022d27d410487f139b397073f06a7476f6'),
    ('MemLoader.ml', 'b59407d1220f7c0871bc556aaebf4748e9229053463881467ca6a3da851c9fe8'),
    ('Ctypes.ml', 'a9f2a2f05e9e4e7ecabfd1324bff52ebd74f382e0db0989dba246a5ebfee8bec'),
    ('Cint.ml', '3b2a00bb65f4c785265c2295c323459e3dce66bb6c82e3d70ff3a659a3660156'),
    ('Factory.ml', 'd2f4da6cb7b2f4a674880f4760680e84fe0a1c58ece95d0f2ff889b7902efcc5'),
]
STRUCT = 'struct std_vector_int { int *data; size_t size; size_t capacity; };'
LAYOUT_CHECKS = '''
/* Source-view ABI duties. WP Typed offsets remain logical cells, not bytes. */
_Static_assert(CHAR_BIT == 8 && sizeof(int) == 4 && _Alignof(int) == 4 && INT_MAX == 2147483647 &&
               INT_MIN == (-2147483647-1), "source-view signed32 layout");
_Static_assert(sizeof(size_t) == 8 && _Alignof(size_t) == 8 &&
               sizeof(void *) == 8 && _Alignof(void *) == 8 &&
               sizeof(std_vector_int) == 24 && _Alignof(std_vector_int) == 8 &&
               offsetof(std_vector_int, data) == 0 &&
               offsetof(std_vector_int, size) == 8 &&
               offsetof(std_vector_int, capacity) == 16, "source-view vector layout");
'''


def _sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def _digest(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(',', ':')))


def identity():
    names = ['vector_reallocation_caller_view.py', 'vector_reallocation_calls.py',
             'vector_reallocation_lifetime.py', 'vector_reallocation_capacity.py',
             'vector_reallocation_caller_packets.py']
    here = Path(__file__).parent
    return {'id': 'vector-reallocation-source-view-1', 'sha256': _digest([
        {'path': name, 'sha256': _sha((here / name).read_bytes())} for name in names])}


@dataclass(frozen=True)
class View:
    text: str
    formal_texts: tuple
    models: tuple
    certificate: dict
    pins: dict


def _span(raw, area):
    begin, end = area.get('begin'), area.get('end')
    if not isinstance(begin, int) or not isinstance(end, int) or not 0 <= begin < end <= len(raw) or \
            _sha(raw[begin:end]) != area.get('sha256'):
        raise Refused('an original/lowered source event changed')


def prepare(lowering, source, formal_texts):
    """Build a source-only diagnostic; no compiler, theorem or origin is granted."""
    source = Path(source)
    if source.is_symlink() or not source.is_file():
        raise Refused('the source view requires one regular original C++ file')
    original = source.read_bytes()
    candidate = lowering.vector_reallocation_candidate
    raw = lowering.text.encode()
    if candidate.get('verdict') != 'pending' or candidate.get('candidate_only') is not True or \
            candidate.get('checker') != vector_reallocation_calls.identity() or \
            candidate.get('source_sha256') != _sha(original) or \
            candidate.get('lowered_sha256') != _sha(raw) or lowering.source_sha256 != _sha(original):
        raise Refused('a current source-bound closed caller candidate is required')
    if candidate.get('reserve_request') != 'count' or candidate.get('observation') != 'captured alias':
        raise Refused('the first source view requires the unchanged no-growth captured-alias caller')
    try:
        count = _contract_count(formal_texts)
    except ValueError as error:
        raise Refused(str(error)) from None
    if count != candidate['count']['name'] or candidate['count']['type'] != 'int':
        raise Refused('the original nonnegative signed count contract differs')
    function = lowering.function
    receiver, alias = candidate['receiver']['name'], candidate['alias']['name']
    try:
        lifetime = vector_reallocation_lifetime.certify(
            lowering.text, function, count, receiver, alias, 'count', 'captured alias')
    except ValueError as error:
        raise Refused(str(error)) from None
    if lifetime != candidate['lowered_lifetime']:
        raise Refused('the complete lowered source/cleanup certificate changed')
    for row in candidate['call_obligations']:
        _span(original, row['source'])
    for row in lifetime['events']:
        _span(raw, row['lowered_source'])
    reserve_events = [row for row in lifetime['events'] if row['event'] == 'reserve'
                      and row['reachable_on_normal_return']]
    if len(reserve_events) != 1:
        raise Refused('one reachable source reserve call is required')
    area = reserve_events[0]['lowered_source']
    old = f'std_vector_int_reserve(&{receiver}, (unsigned long){count});'
    if raw[area['begin']:area['end']].decode() != old:
        raise Refused('the source reserve arguments changed')
    branch = 'if (n > this->capacity) std_vector_int_grow(this, n);'
    model = std_models.model_text('std_vector_int_reserve')
    definition = ('static void std_vector_int_reserve(std_vector_int *this, size_t n) {\n  '
                  + branch + '\n}')
    if model.count(branch) != 1 or model.count(definition) != 1 or not model.rstrip().endswith(definition):
        raise Refused('the original reserve branch/call body changed')
    branch_begin = len(model[:model.index(branch)].encode())
    inline = (f'/*@ assert swdb_reserve_no_growth: (unsigned long){count} <= {receiver}.capacity; */\n  '
              f'if ((unsigned long){count} > {receiver}.capacity) '
              f'std_vector_int_grow(&{receiver}, (unsigned long){count});')
    text = (raw[:area['begin']] + inline.encode() + raw[area['end']:]).decode()
    if text.count(STRUCT) != 1 or text.count('#include <stddef.h>') != 1:
        raise Refused('the original lowered vector declaration/header changed')
    text = text.replace(STRUCT, STRUCT + LAYOUT_CHECKS, 1)
    text = text.replace('#include <stddef.h>', '#include <stddef.h>\n#include <limits.h>', 1)
    inverse = text.replace('#include <stddef.h>\n#include <limits.h>', '#include <stddef.h>', 1)
    inverse = inverse.replace(STRUCT + LAYOUT_CHECKS, STRUCT, 1).replace(inline, old, 1)
    if inverse != lowering.text:
        raise Refused('source-view inverse must recover the entire original lowering')
    coordinates = {
        'receiver': {'type': 'std_vector_int', 'typed_cell_extent': 3,
                     'byte_extent': 24, 'byte_alignment': 8,
                     'fields': [{'field': field, 'typed_cell_offset': index, 'byte_offset': byte}
                                for field, index, byte in [('data', 0, 0), ('size', 1, 8), ('capacity', 2, 16)]]},
        'buffer': {'element': 'int32', 'typed_cell_stride': 1, 'byte_stride': 4, 'byte_alignment': 4},
        'address_identity_mapping': 'pending injective source-local identity relation; no address-to-integer observation',
    }
    certificate = {
        'version': 1, 'function': function, 'check': identity(),
        'original_source_sha256': _sha(original), 'original_lowering_sha256': _sha(raw),
        'view_sha256': _sha(text), 'formal_texts_sha256': _digest(list(formal_texts)),
        'source_calls': candidate['call_obligations'], 'source_lifetime': lifetime,
        'reserve_inline': {'source_call': area, 'original_call': old, 'replacement': inline,
                           'model_source_sha256': _sha(model),
                           'model_branch': {'begin': branch_begin, 'end': branch_begin + len(branch.encode()),
                                            'sha256': _sha(branch)}},
        'inverse_original_lowering_equal': True, 'address_coordinates': coordinates,
        'original_reserve_summary_imported': False, 'dependency_replacement_performed': False,
        'unreachable_fallthrough_cleanup_retained': True,
        'selected_runtime_requirements': {
            'memory_model': 'Typed', 'variable_model': 'Var', 'integer_model': 'Machine',
            'source_pins': [{'name': name, 'sha256': digest} for name, digest in RUNTIME_SOURCES],
            'status': 'prospective requirement; actual selected runtime/task binding pending'},
        'runtime_bridge_proved': False,
        'proof_admission': 'unsupported: actual Typed+Var source/lifetime correspondence and current dependencies pending',
        'caller_premises_added': [], 'current_proof_records_admitted': [],
        'pending': ['actual generated Typed+Var task-term correspondence',
                    'type-directed address identity/layout, value and separate initialization relation',
                    'constructor fill, captured alias, cleanup and final incoming-frame proof',
                    'current qualified body dependency admission and complete public ordinary/smoke proof'],
    }
    return View(text, tuple(formal_texts), tuple(lowering.models), certificate,
                {'vector_reallocation_source_view': identity(),
                 'vector_reallocation_source_view_certificate': {
                     'id': 'vector-reallocation-source-view-certificate-1', 'sha256': _digest(certificate)}})


def check(lowering, source, view, formal_texts):
    fresh = prepare(lowering, source, formal_texts)
    if fresh != view:
        raise Refused('the source view/certificate changed before use')
    return fresh


def check_launch(lowering, source, view, formal_texts):
    check(lowering, source, view, formal_texts)
    raise Refused('actual Typed+Var source/runtime and lifetime bridge remains unsupported; source hashes alone admit no launch')
