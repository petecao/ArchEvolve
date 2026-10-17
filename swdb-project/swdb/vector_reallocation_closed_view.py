"""Closed no-growth source-to-VC projection; created 2026-10-16 ET.

Data reads and a false reserve branch are checked source reductions. The
constructor stays modular so its private writes do not widen the caller frame.
Only terminal cleanup uses the separate private lifetime/frame interpretation.
Current source/model/Typed/lifetime proof admission remains deliberately closed.
"""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from swdb import std_models, vector_reallocation_caller_view, vector_reallocation_private_frame


class Refused(ValueError):
    pass


MODEL = {'id': 'swdb-std-models-2',
         'sha256': 'cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2'}
MAX_COUNT = '((size_t)PTRDIFF_MAX < SIZE_MAX / sizeof(int) ? (size_t)PTRDIFF_MAX : SIZE_MAX / sizeof(int))'


def _sha(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()


def _digest(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(',', ':')))


def identity():
    here = Path(__file__).parent
    names = ['vector_reallocation_closed_view.py', 'vector_reallocation_caller_view.py',
             'vector_reallocation_private_frame.py', 'vector_reallocation_calls.py',
             'vector_reallocation_lifetime.py', 'std_models.py', 'heap_reallocation.mlw']
    return {'id': 'vector-closed-no-growth-view-1',
            'sha256': _digest([{'path': name, 'sha256': _sha((here / name).read_bytes())}
                               for name in names])}


@dataclass(frozen=True)
class View:
    text: str
    formal_texts: tuple
    models: tuple
    certificate: dict
    pins: dict


def _binding(lowering, candidate):
    provenance = lowering.stdlib_provenance
    if lowering.defines or lowering.summaries or lowering.probes or \
            tuple(lowering.std_models) != ('std_vector_int',):
        raise Refused('the closed caller admits no preprocessing, opaque effects or other modeled types')
    if provenance.get('verdict') != 'passed' or provenance.get('library', {}).get('id') != 'libc++-22.1.8' or \
            candidate.get('stdlib_binding_sha256') != _sha(json.dumps(provenance, sort_keys=True)) or \
            provenance.get('models') != sorted(set((*lowering.models, *lowering.std_models))) or \
            provenance.get('substitution_requests') != list(lowering.stdlib_substitutions):
        raise Refused('the complete original-TU/default allocator model binding differs')
    return {'certificate_sha256': _digest(provenance),
            'model': std_models.identity(), 'original_substitutions': list(lowering.stdlib_substitutions),
            'default_allocator': 'source checker accepts only std::vector<int[,std::allocator<int>]>; canonical full-TU bindings',
            'existing_trusted_policy': [
                'pinned standard library implements the modeled members as stated by the pinned model',
                'allocation succeeds; existing allocator/deallocator fresh/freeable and frame contracts are trusted',
            ],
            'environment_boundary': 'TU provenance does not attest a linked replacement-free allocator environment; no new absence-of-effects premise is inferred',
            'required_before_launch': 'fresh original-TU/header/compiler recheck and explicit existing allocator/library TCB scope'}


def prepare(lowering, source, formal_texts):
    """Prepare executable projected C and all pending bridge duties, never a proof."""
    try:
        base = vector_reallocation_caller_view.prepare(lowering, source, formal_texts)
    except ValueError as error:
        raise Refused(str(error)) from None
    if std_models.identity() != MODEL:
        raise Refused('the exact original model bodies require a new closed-caller audit')
    candidate = lowering.vector_reallocation_candidate
    binding = _binding(lowering, candidate)
    count = candidate['count']['name']
    receiver, alias = candidate['receiver']['name'], candidate['alias']['name']
    lifetime = candidate['lowered_lifetime']
    events = {row['event']: row for row in lifetime['events']}
    if lifetime['normal_return_cleanup_count'] != 1 or lifetime['unreachable_fallthrough_cleanup_count'] != 1 or \
            lifetime['return_scalar_before_destruction'] is not True or \
            events['unreachable fallthrough destructor']['reachable_on_normal_return'] is not False:
        raise Refused('the exact unconditional-return/cleanup CFG certificate differs')
    # The whole canonical lowered body has already been checked by prepare:
    # declarations/calls followed by {scalar; destructor; return scalar;} and
    # one later fallback destructor. There is no normal edge past that return.
    text = base.text
    edits = []

    def replace(old, new, *, count_expected=1, last=False):
        nonlocal text
        if text.count(old) != count_expected:
            raise Refused('a complete source-derived caller edit has ambiguous occurrence')
        offset = text.rindex(old) if last else text.index(old)
        text = text[:offset] + new + text[offset + len(old):]
        edits.append({'old': old, 'new': new, 'offset_in_preceding_view': offset})

    data_model = std_models.model_text('std_vector_int_data')
    data_definition = 'static int *std_vector_int_data(const std_vector_int *this) { return this->data; }'
    if not data_model.rstrip().endswith(data_definition) or data_model.count(data_definition) != 1 or \
            data_model.count(r'requires std_vector_int_readable(this);') != 1:
        raise Refused('the original pure data body/precondition changed')
    old_data = f'int *{alias} = std_vector_int_data(&{receiver});'
    data_inline = (f'/*@ assert swdb_closed_data_requires: std_vector_int_readable(&{receiver}); */\n  '
                   f'int *{alias} = {receiver}.data;')
    replace(old_data, data_inline)
    reserve_inline = base.certificate['reserve_inline']['replacement']
    reserve_reduced = (
        f'/*@ assert swdb_closed_reserve_requires: std_vector_int_valid(&{receiver}) && '
        f'(unsigned long){count} <= {MAX_COUNT}; */\n  '
        f'/*@ assert swdb_reserve_no_growth: (unsigned long){count} <= {receiver}.capacity; */\n  '
        '/* checked false reserve branch: the preceding ordinary assertion must be proved */')
    replace(reserve_inline, reserve_reduced)
    dtor_model = std_models.model_text('std_vector_int_dtor')
    dtor_definition = 'static void std_vector_int_dtor(std_vector_int *this) { swdb_free(this->data); }'
    dtor_precondition = r'requires std_vector_int_valid(this) && (this->capacity == 0 || \freeable(this->data));'
    if not dtor_model.rstrip().endswith(dtor_definition) or dtor_model.count(dtor_definition) != 1 or \
            dtor_model.count(dtor_precondition) != 1:
        raise Refused('the original terminal destructor body/precondition changed')
    dtor_call = f'std_vector_int_dtor(&{receiver});'
    terminal = (
        f'/*@ assert swdb_closed_dtor_repr_requires: std_vector_int_valid(&{receiver}); */\n    '
        '/* checked private terminal cleanup: release/freeable/frame duties remain in the source bridge */')
    replace(dtor_call, terminal, count_expected=2)
    fallback = '/* certified unreachable fallback cleanup after unconditional scalar return */'
    replace(dtor_call, fallback)
    inverse = text
    for edit in reversed(edits):
        offset = edit['offset_in_preceding_view']
        if inverse[offset:offset + len(edit['new'])] != edit['new']:
            raise Refused('closed source edit inverse has changed bytes')
        inverse = inverse[:offset] + edit['old'] + inverse[offset + len(edit['new']):]
    if inverse != base.text or base.certificate['inverse_original_lowering_equal'] is not True:
        raise Refused('closed view must inverse-restore the entire original lowering')
    constructor = std_models.model_text('std_vector_int_ctor_count_value')
    private_plan, _ = vector_reallocation_private_frame.declaration()
    certificate = {
        'created': '2026-10-16 ET', 'version': 1, 'checker': identity(),
        'function': lowering.function, 'source_view': base.certificate,
        'original_lowering_sha256': _sha(lowering.text), 'view_sha256': _sha(text),
        'formal_texts_sha256': _digest(list(formal_texts)), 'caller_premises_added': [],
        'original_assigns': r'assigns \nothing;', 'original_lowering_inverse_equal': True,
        'edits': edits, 'library_allocator_binding': binding,
        'cfg': {'reason': 'exact canonical compound ends in unconditional scalar return',
                'complete_lowered_body': lifetime['lowered_function_body'],
                'scalar_capture': events['guarded scalar capture'], 'return': events['return scalar'],
                'terminal_destructor': events['destructor'],
                'fallback': events['unreachable fallthrough destructor'], 'fallback_reachable': False},
        'data': {'model_sha256': _sha(data_model), 'original_precondition_retained_as_assertion': True,
                 'body': data_definition, 'source_call': events['data capture']},
        'reserve': {'model_sha256': base.certificate['reserve_inline']['model_source_sha256'],
                    'source_call': events['reserve'], 'ordinary_false_branch_assertion': 'swdb_reserve_no_growth',
                    'branch_elimination_requires_fresh_valid_assertion': True},
        'constructor': {'model_sha256': _sha(constructor), 'source_call': events['constructor'],
                        'call_retained': True, 'current_body_proof_dependency_required': True,
                        'fresh_private_output': 'pending source-defined allocation/fill/frame correspondence under the existing allocator TCB'},
        'terminal_cleanup': {
            'model_sha256': _sha(dtor_model), 'source_call': events['destructor'],
            'body': dtor_definition, 'original_precondition': dtor_precondition,
            'transition': 'Heap.end_automatic(Heap.release(now,buffer),receiver)',
            'freeable_duty': {'status': 'pending source-allocation/lifetime bridge',
                              'origin': 'existing successful fresh allocator; automatic receiver is not dynamically freeable',
                              'native_wp_status': 'WP33 does not implement freeable/fresh/dangling; no native proof claimed'},
            'private_frame': private_plan['checker'],
            'required_mathematical_goals': [row['goal'] for row in private_plan['obligations']],
            'incoming_observation': private_plan['observation'], 'scalar_capture_before_cleanup': True,
            'noescape_duty': 'closed source AST and complete lowering order; source-created identities still require the model/allocator bridge',
        },
        'proof_admission': 'unsupported: source allocation/Typed/lifetime bridge, current constructor dependency and fresh complete ordinary proofs required',
        'source_typed_bridge_established': False, 'current_proof_records_admitted': [],
    }
    return View(text, tuple(formal_texts), ('swdb_alloc_int', 'std_vector_int_ctor_count_value'),
                certificate, {'closed_no_growth_check': identity(),
                              'closed_no_growth_certificate': {'id': lowering.function + '.closed-no-growth',
                                                              'sha256': _digest(certificate)}})


def check(lowering, source, view, formal_texts):
    if prepare(lowering, source, formal_texts) != view:
        raise Refused('the closed source view, effect/CFG map or lifetime duties changed')
    return view


def check_launch(lowering, source, view, formal_texts):
    check(lowering, source, view, formal_texts)
    raise Refused('actual source-allocation/Typed/lifetime bridge and complete proof admission remain pending')
