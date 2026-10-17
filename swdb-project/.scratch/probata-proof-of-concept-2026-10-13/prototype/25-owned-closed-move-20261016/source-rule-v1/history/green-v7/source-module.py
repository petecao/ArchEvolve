"""2026-10-16 ET. Closed int move source effects and scalar observation.

This exact-source rule derives private construction, transfer and reverse
cleanup. Complete mathematical evidence/source composition remains a separate
launch gate. It grants no universal move contract or Typed-memory ownership.
"""
import hashlib
import json
from pathlib import Path
import re

from swdb import std_models
from swdb import vector_reallocation_model as model
from swdb import vector_reallocation_private_frame as private
from swdb import vector_reallocation_vcs as mathematical
from swdb import vector_owned_source_view as source_view


class Refused(ValueError):
    pass


MODEL = {'id': 'swdb-std-models-2', 'sha256': 'cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2'}
SOURCE_SHA = 'a0dc043284f96a5b7c052963b51188318ae4abc6a85ee347fea78b6ab392d3a2'
FUNCTION = 'vector_owned_move_capture'
CONTRACT = [r'requires 0 <= n;', r'assigns \nothing;', r'ensures \result == (n > 0 ? 7 : 0);']
SOURCE = '''#include <utility>
#include <vector>
int vector_owned_move_capture(int n) {
  std::vector<int> source(n, 7);
  int *saved = source.data();
  std::vector<int> destination(std::move(source));
  int value = n > 0 ? saved[0] : 0;
  return value;
}'''
BODY = '''std_vector_int source;
std_vector_int_ctor_count_value(&source, n, 7);
int *saved = std_vector_int_data(&source);
std_vector_int destination;
std_vector_int_move_ctor(&destination, &source);
int value = (n > 0) ? saved[0] : 0;
{
int swdb_return = value;
std_vector_int_dtor(&destination);
std_vector_int_dtor(&source);
return swdb_return;
}
std_vector_int_dtor(&destination);
std_vector_int_dtor(&source);'''
MODEL_BODIES = {
    'ctor_count_value': '''static void std_vector_int_ctor_count_value(std_vector_int *this, size_t n, int value) {
this->data = NULL; this->size = 0; this->capacity = 0;
if (n == 0) return;
this->data = swdb_alloc_int(n);
this->capacity = n;
for (size_t k = 0; k < n; ++k) this->data[k] = value;
this->size = n;
}''',
    'data': 'static int *std_vector_int_data(const std_vector_int *this) { return this->data; }',
    'move_ctor': '''static void std_vector_int_move_ctor(std_vector_int *this, std_vector_int *other) {
*this = *other;
other->data = NULL; other->size = 0; other->capacity = 0;
}''',
    'dtor': 'static void std_vector_int_dtor(std_vector_int *this) { swdb_free(this->data); }',
}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def _need(value, reason):
    if not value:
        raise Refused(reason)


def _uncomment(text):
    return re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S)


def _tokens(text):
    return re.findall(r'\w+|[^\s]', _uncomment(text))


def _token_offsets(text):
    masked = re.sub(r'/\*.*?\*/|//[^\n]*', lambda match: ' '*len(match[0]), text, flags=re.S)
    return [(match[0], match.start(), match.end()) for match in re.finditer(r'\w+|[^\s]', masked)]


def identity():
    here = Path(__file__).parent
    names = ('vector_owned_move_source.py', 'std_models.py', 'c_lowering.py',
             'vector_reallocation_model.py', 'vector_reallocation_vcs.py',
             'vector_reallocation_inventory.py', 'heap_model_vcs.py',
             'vector_reallocation_private_frame.py', 'vector_reallocation_closed_evidence.py',
             'vector_owned_source_view.py', 'vector_owned_transfer.py',
             'heap_reallocation.mlw', 'vector_owned_state.mlw', 'vector_owned_effects.mlw')
    return {'id': 'vector-owned-closed-move-source-1',
            'sha256': _sha(_json([{'path': name, 'sha256': _sha((here/name).read_bytes())} for name in names]))}


def _models():
    _need(std_models.identity() == MODEL, 'the complete original model version requires a new source audit')
    pieces = [('SWDB_MODEL_FAIL', std_models.MACROS),
              ('std_vector_int_valid', std_models.vector_logic('std_vector_int', 'int'))]
    originals = {}
    for member in ('ctor_count_value', 'dtor', 'data', 'move_ctor'):
        unit = std_models.vector_member('std_vector_int', 'int', member)
        body = unit[-1][1]
        declaration = 'static '+MODEL_BODIES[member].split('static ', 1)[1].split('{', 1)[0]
        _need(body.count(declaration) == 1 and
              _tokens(declaration+body.split(declaration, 1)[1]) == _tokens(MODEL_BODIES[member]),
              'one complete checked model executable effect grammar is required')
        originals[member] = std_models.model_text('std_vector_int_'+member).encode()
        for name, text in unit:
            if name not in {key for key, _ in pieces}:
                pieces.append((name, text))
    return pieces, originals


def _source(lowering, source, formal_texts, pieces):
    source = Path(source)
    _need(source.is_file() and not source.is_symlink(), 'one original regular closed C++ source is required')
    original = source.read_bytes()
    _need(_sha(original) == SOURCE_SHA == lowering.source_sha256 and
          _tokens(original.decode()) == _tokens(SOURCE), 'the complete original closed C++ source grammar differs')
    _need(list(formal_texts) == CONTRACT and lowering.function == FUNCTION and
          _json(lowering.parameters) == _json([['n', 'int', False]]), 'the original count/frame/scalar contract or signature differs')
    expected_models = tuple(name for name, _ in pieces if name != 'SWDB_MODEL_FAIL' and not name.endswith('_valid'))
    _need(tuple(lowering.models) == expected_models and tuple(lowering.std_models) == ('std_vector_int',) and
          lowering.allocation is True and not lowering.defines and not lowering.summaries and not lowering.probes and
          not lowering.vector_reallocation_candidate and not lowering.terminal_release,
          'only the complete closed int-move unit with no additional effects is supported')
    provenance = lowering.stdlib_provenance
    _need(provenance.get('verdict') == 'passed' and provenance.get('library', {}).get('id') == 'libc++-22.1.8' and
          provenance.get('models') == sorted(set((*expected_models, 'std_vector_int'))) and
          provenance.get('substitution_requests') == list(lowering.stdlib_substitutions),
          'the original whole-TU library/default allocator binding differs')
    tool = lowering.tool
    _need(all(tool.get(key) == value for key, value in
              [('id', 'swdb-c-lowering'), ('version', '9'), ('naming_rules', 'kept-names.3'), ('clang', '22.1.8')]),
          'the selected original lowering tool version differs')
    headers = '#include <stdbool.h>\n#include <stddef.h>\n#include <stdint.h>\n#include <stdlib.h>\n'
    struct = 'typedef struct std_vector_int std_vector_int;\nstruct std_vector_int { int *data; size_t size; size_t capacity; };\n'
    prototype = 'int '+FUNCTION+'(int n)'
    declaration = headers+struct+prototype+';\n'
    _need(lowering.declaration == declaration, 'the complete formal declaration has extra TU constructs')
    lead = (f'/* C lowering of {FUNCTION} from {source.name} (sha256 {SOURCE_SHA}) by swdb-c-lowering 9 '
            '(kept-names.3), clang 22.1.8. Generated: do not edit. */\n')
    prefix = lead+headers+struct+'/* swdb-anchor ghost.globals */\n'+'\n'.join(text for _, text in pieces)
    prefix += '\n'+prototype+';\n/* swdb-anchor '+FUNCTION+'.contract */\n'+prototype+' {\n'
    text = lowering.text
    _need(isinstance(text, str) and text.startswith(prefix) and text.endswith('\n}\n'),
          'the entire original TU/model/contract prefix differs')
    body = text[len(prefix):-3]
    _need(_tokens(body) == _tokens(BODY), 'unaccounted executable source/call/CFG/escape effect')
    observed_anchors = []
    for line, value in enumerate(text.splitlines(), 1):
        found = re.fullmatch(r'\s*/\* swdb-anchor ([\w.]+) \*/', value)
        if found:
            ident = found[1]
            observed_anchors.append({'id': ident, 'kind': 'ghost_globals' if ident == 'ghost.globals' else
                                     'contract' if ident.endswith('.contract') else ident.rsplit('.', 1)[-1],
                                     'function': None if ident == 'ghost.globals' else FUNCTION, 'line': line})
    expected_ids = ['ghost.globals', FUNCTION+'.contract', FUNCTION+'.entry']+[
        FUNCTION+'.s'+str(index)+'.'+side for index in range(1, 8) for side in ('before', 'after')]
    _need([row['id'] for row in observed_anchors] == expected_ids and
          _json(lowering.anchors) == _json(observed_anchors), 'the complete original anchor inventory or exact line binding differs')
    offsets = _token_offsets(body)
    tail = _tokens('std_vector_int_dtor(&destination); std_vector_int_dtor(&source);')
    _need([row[0] for row in offsets[-len(tail):]] == tail and offsets[-len(tail)-1][0] == '}',
          'the complete unconditional-return fallback CFG differs')
    count = len(_tokens('std_vector_int_dtor(&destination);'))
    calls = [offsets[-len(tail):-count], offsets[-count:]]
    replacement = '/* checked unreachable cleanup after unconditional captured-scalar return */'
    reduced, edits = text, []
    for call in reversed(calls):
        begin, end = len(prefix)+call[0][1], len(prefix)+call[-1][2]
        old = reduced[begin:end]
        reduced = reduced[:begin]+replacement+reduced[end:]
        edits.append({'begin': begin, 'end': end, 'old': old, 'replacement': replacement})
    restored = reduced
    for edit in reversed(edits):
        begin = edit['begin']
        _need(restored[begin:begin+len(replacement)] == replacement, 'the exact fallback edit changed')
        restored = restored[:begin]+edit['old']+restored[begin+len(replacement):]
    _need(restored == text, 'the full-source fallback reduction inverse differs')
    roles = ['declare source', 'construct source', 'capture saved pointer', 'declare destination',
             'move construct destination', 'capture guarded scalar', 'copy return scalar',
             'destroy destination', 'destroy source', 'return copied scalar',
             'unreachable destination destructor', 'unreachable source destructor']
    statements = [' '.join(part.split()) for part in _uncomment(body).split(';') if part.strip()]
    _need(len(statements) == len(roles), 'the complete semicolon source-effect census differs')
    lowered_events = [{'ordinal': index, 'role': role, 'normalized_bytes': len(statement.encode()),
                       'normalized_sha256': _sha(statement.encode())}
                      for index, (role, statement) in enumerate(zip(roles, statements, strict=True))]
    source_events = []
    for role, statement in [('construct source', 'std::vector<int> source(n, 7);'),
                             ('capture saved pointer', 'int *saved = source.data();'),
                             ('move construct destination', 'std::vector<int> destination(std::move(source));'),
                             ('capture guarded scalar', 'int value = n > 0 ? saved[0] : 0;'),
                             ('return scalar', 'return value;')]:
        raw = statement.encode()
        _need(original.count(raw) == 1, 'the complete original source operation is ambiguous')
        source_begin = original.index(raw)
        source_events.append({'role': role, 'begin': source_begin, 'end': source_begin+len(raw),
                              'line': original[:source_begin].count(b'\n')+1, 'sha256': _sha(raw)})
    return original, reduced.encode(), {'original': source_events, 'lowered': lowered_events}, {
        'fallback_reachable': False, 'basis': 'complete exact body: one unconditional scalar-return compound precedes both fallback destructors',
        'whole_lowering_inverse_equal': True, 'original_sha256': _sha(text.encode()), 'view_sha256': _sha(reduced.encode()),
        'edits': edits, 'original_anchors': observed_anchors,
        'reachable_destructor_order': ['destination', 'source'], 'capture_before_both_destructors': True,
    }


def _frame(steps, private_targets):
    """Pointwise identity outside source-fresh targets, composed structurally."""
    checked = []
    for step in steps:
        operation = step['operation']
        if operation == 'loop':
            checked.append({**step, 'body': _frame(step['body'], private_targets), 'arbitrary_count_induction': True})
        elif operation == 'release' and step['target'] == 'null':
            checked.append({**step, 'pointwise_frame': 'null release is identity under the explicit deallocator model'})
        else:
            _need(operation in {'begin_automatic', 'store', 'allocate', 'release', 'end_automatic', 'header_copy'} and
                  step.get('target') in private_targets, 'source effect could modify an incoming allocation')
            checked.append({**step, 'pointwise_frame': 'target identity was not issued at entry; all incoming identities differ'})
    return {'all_steps_checked': True, 'protected': 'all incoming allocated identities',
            'private_targets': sorted(private_targets), 'steps': checked,
            'rule': 'pointwise identity composes over sequence and every iteration of the exact private fill loop'}


def _administrative(positive):
    """Checked disjoint private-store product in actual activation/capture order."""
    steps, objects = [], []
    def begin(target, initialize=True):
        _need(target not in objects, 'administrative source activation is duplicated')
        objects.append(target)
        steps.append({'operation': 'begin_automatic', 'target': target})
        if initialize:
            steps.append({'operation': 'store', 'target': target})
    def end(target):
        steps.append({'operation': 'end_automatic', 'target': target})
    for target in ('ctor.this', 'ctor.n', 'ctor.value'):
        begin(target)
    if positive:
        begin('ctor.k')
        steps.append({'operation': 'loop', 'range': '0 <= k < n',
                      'body': [{'operation': 'store', 'target': 'ctor.k'}]})
        end('ctor.k')
    for target in ('ctor.value', 'ctor.n', 'ctor.this'):
        end(target)
    begin('caller.saved', initialize=False)
    begin('data.this'); end('data.this')
    steps.append({'operation': 'store', 'target': 'caller.saved'})
    begin('move.this'); begin('move.other'); end('move.other'); end('move.this')
    begin('caller.value'); begin('caller.swdb_return')
    for owner in ('destination', 'source'):
        begin('dtor.'+owner+'.this'); end('dtor.'+owner+'.this')
    for target in ('caller.swdb_return', 'caller.value', 'caller.saved'):
        end(target)
    live = set()
    for step in steps:
        operation, target = step['operation'], step.get('target')
        if operation == 'begin_automatic':
            _need(target not in live, 'administrative storage is already active')
            live.add(target)
        elif operation == 'end_automatic':
            _need(target in live, 'administrative source scope ends before activation')
            live.remove(target)
        elif operation == 'store':
            _need(target in live, 'administrative scalar/pointer store occurs after lifetime end')
        else:
            _need(operation == 'loop' and 'ctor.k' in live, 'unaccounted administrative source effect')
    _need(not live, 'administrative source storage escapes its scope')
    return {'fresh_private_objects': objects, 'incoming_frame': _frame(steps, set(objects)),
            'address_escapes': False, 'caller_n_is_entry_parameter': True,
            'no_admin_identity_consumes_selected_Heap_frontier': True,
            'saved_initialization': 'actual initialized data field value copied into local pointer; independent of pointee initialization',
            'value_initialization': 'guarded buffer load at positive count, literal zero otherwise',
            'return_initialization': 'value copied to swdb_return before either destructor',
            'projection': 'private call parameters, loop counter and scalar/pointer local storage form a separate hidden product component; they do not silently consume the selected Heap receiver/buffer frontier'}


def _branch(positive):
    """Evaluate the checked source field/effect grammar with symbolic count n."""
    empty = {'data': 'null', 'size': 0, 'capacity': 0}
    headers = {'source': dict(empty)}
    steps = [{'operation': 'begin_automatic', 'target': 'source'}]
    steps += [{'operation': 'store', 'target': 'source', 'field': field, 'value': value} for field, value in empty.items()]
    if positive:
        steps += [{'operation': 'allocate', 'target': 'buffer', 'count': 'n'},
                  {'operation': 'store', 'target': 'source', 'field': 'data', 'value': 'buffer'},
                  {'operation': 'store', 'target': 'source', 'field': 'capacity', 'value': 'n'},
                  {'operation': 'loop', 'range': '0 <= k < n',
                   'body': [{'operation': 'store', 'target': 'buffer', 'offset': '4*k', 'value': 7}]},
                  {'operation': 'store', 'target': 'source', 'field': 'size', 'value': 'n'}]
        headers['source'] = {'data': 'buffer', 'size': 'n', 'capacity': 'n'}
    before = dict(headers['source'])
    saved = before['data']
    steps.append({'operation': 'begin_automatic', 'target': 'destination'})
    headers['destination'] = dict(headers['source'])
    steps.append({'operation': 'header_copy', 'target': 'destination', 'from': 'source', 'complete_fields': ['data', 'size', 'capacity']})
    for field, value in empty.items():
        headers['source'][field] = value
        steps.append({'operation': 'store', 'target': 'source', 'field': field, 'value': value})
    _need(headers['destination'] == before and headers['source'] == empty and saved == before['data'],
          'the checked source transfer did not preserve the captured buffer identity')
    local_owners = {'source': headers['source']['data'], 'destination': headers['destination']['data']}
    nonnull = [value for value in local_owners.values() if value != 'null']
    _need(len(nonnull) == len(set(nonnull)), 'the participating lexical owners share a backing allocation')
    # Exact constructor fill induction supplies element0 == 7 at n>0; the
    # zero branch never evaluates a pointer expression or buffer load.
    scalar = 7 if positive else 0
    releases = []
    after_move = {name: dict(value) for name, value in headers.items()}
    for owner in ('destination', 'source'):
        backing = headers[owner]['data']
        _need(backing == 'null' or backing == saved and positive and backing not in releases,
              'source cleanup is not a single freeable private buffer release')
        steps.append({'operation': 'release', 'target': backing, 'owner': owner})
        if backing != 'null':
            releases.append(backing)
        local_owners.pop(owner)
        steps.append({'operation': 'end_automatic', 'target': owner})
    _need(not local_owners and len(releases) == int(positive), 'actual source reverse cleanup remains incomplete')
    return {'condition': '0 < n <= INT_MAX' if positive else 'n == 0',
            'source_before_move': before, 'source_after_move': after_move['source'],
            'destination_after_move': after_move['destination'], 'saved': saved,
            'source_identity': 'Heap.next(entry)',
            'buffer_identity': 'Heap.next(entry)+1' if positive else 'null',
            'destination_identity': 'Heap.next(entry)+2' if positive else 'Heap.next(entry)+1',
            'source_identity_history': 'source automatic begins before constructor; exact initial stores preserve next; positive allocator is fresh; destination automatic begins after constructor and is never-issued',
            'scalar': scalar, 'scalar_captured_before_cleanup': True, 'returned_pointer': False,
            'incoming_frame': _frame(steps, {'source', 'destination', 'buffer'} if positive else {'source', 'destination'}),
            'administrative_storage': _administrative(positive),
            'cleanup': {'destructor_order': ['destination', 'source'], 'buffer_release_count': len(releases),
                'automatic_ends': ['destination', 'source'], 'registry_retire_is_release': False,
                'transition': 'end_automatic(release(end_automatic(release(post,destination.data),destination),source.data),source)',
                'source_data_used': 'null', 'no_private_pointer_observation_after_release': True}}


def _dependencies():
    files, result = {}, {}
    for name, member, count in [('constructor', 'std_vector_int_realloc_v3_ctor_count_value', 35),
                                ('destructor', 'std_vector_int_realloc_v3_dtor', 11)]:
        plan, canonical = mathematical.declaration(member)
        _need(len(plan['obligations']) == count, 'the complete constructor/destructor dependency target set differs')
        certificate = model.certificate(member)
        _need(certificate['original_source_sha256'] == certificate['inverse_qualified_source_sha256'],
              'the entire original/qualified dependency source inverse differs')
        result[name] = {'member': member, 'source_inverse': certificate,
            'targets': [{key: row[key] for key in ('id', 'goal', 'kind', 'statement', 'sha256')} for row in plan['obligations']],
            'current_record_admitted': False, 'retained_evidence_role': 'conditionally reusable exact model mathematics only; complete historical evidence/context binding still required'}
        for row in plan['obligations']:
            files['dependencies/'+name+'/'+row['path']] = canonical[row['path']]
        for source in ('original.c', 'qualified.c'):
            files['dependencies/'+name+'/'+source] = canonical[source]
    frame, canonical = private.declaration()
    _need(len(frame['obligations']) == 9, 'the exact private-frame dependency target set differs')
    result['private_frame'] = {'checker': frame['checker'], 'targets': frame['obligations'],
        'current_record_admitted': False, 'retained_evidence_role': 'conditional private math only; actual incoming all-identity source frame is separate'}
    for row in frame['obligations']:
        files['dependencies/private_frame/'+row['path']] = canonical[row['path']]
    view, canonical = source_view.declaration(elements=('int',))
    moves = [row for row in view['obligations'] if row['id'].startswith('move.')]
    _need(len(moves) == 4, 'the four exact original move source/Heap goal identities differ')
    result['move_source'] = {'checker': view['checker'], 'targets': moves,
        'mathematically_admitted': False, 'old_eight_native_Valid_or_registry10_is_admission': False,
        'source_local_discharge': 'the two participating lexical owners are constructed here; no opaque incoming Owners.valid or OwnedEffects.world premise is assumed',
        'remaining': 'complete exact source-to-Heap/phase/header composition and independent task encoding closure'}
    for row in moves:
        files['dependencies/move_source/'+row['path']] = canonical[row['path']]
    here = Path(__file__).parent
    for name in ('heap_reallocation.mlw', 'vector_owned_state.mlw', 'vector_owned_effects.mlw'):
        files['theory/'+name] = (here/name).read_bytes()
    return result, files


def declaration(lowering, source, formal_texts):
    pieces, originals = _models()
    original, reduced, events, cfg = _source(lowering, source, formal_texts, pieces)
    dependencies, files = _dependencies()
    _need(4*2147483647 <= 18446744073709551615 and 2147483647 < 4611686018427387903,
          'the original signed32 count/64-bit allocation arithmetic differs')
    branches = {'zero': _branch(False), 'positive': _branch(True)}
    plan = {'created': '2026-10-16 ET', 'checker': identity(), 'function': FUNCTION,
        'original_contract': list(formal_texts), 'caller_premises_added': [],
        'source_grammar': {'source_sha256': _sha(original), 'lowering_sha256': _sha(lowering.text.encode()),
            'whole_original_source_checked': True, 'all_statements_accounted': True,
            'extra_TU_constructs': [], 'complete_model_and_contract_inverse_checked': True},
        'cfg': cfg, 'source_events': events, 'original_library_provenance': lowering.stdlib_provenance,
        'original_substitution_requests': list(lowering.stdlib_substitutions),
        'source_tool': lowering.tool, 'parent_model': MODEL, 'branches': branches,
        'ownership': {'complete_participating_lexical_owners': ['source', 'destination'],
            'incoming_owners_assumed_valid': False, 'raw_saved_pointer_is_owner': False,
            'complete_global_registry_claimed': False, 'source_rule': 'source fresh construction creates the only initial backing owner; fresh writable destination receives it; resetting source removes its backing ownership before cleanup',
            'frontier': 'never-issued Heap.next history; not live owner cardinality or physical address'},
        'source_safety': {'original_count_upper_bound': 2147483647,
            'model_maximum_count': 4611686018427387903, 'count_conversion': 'original nonnegative signed32 n widens exactly to unsigned64',
            'null_pointer_arithmetic_evaluated': False, 'positive_read': '0 < n implies 0 <= 0 < n; exact constructor fill initializes int element0 to 7 before move; header transfer never touches payload',
            'source_size_observed_after_move': False,
            'loop_induction': {'base': 'empty initialized/filled prefix at k=0', 'step': 'write private element k with literal7, preserve every j<k, increment k',
                'exit': 'k=n, hence each 0<=j<n is initialized int7', 'variant': 'n-k decreases and is nonnegative',
                'complete_dependency': 'all35 constructor targets; no native callee desired postcondition used as a premise'},
            'field_reads': 'source constructor initializes all source fields; data returns that initialized pointer; complete move copies initialized fields to fresh writable destination before source resets',
            'padding': 'struct assignment may change any private receiver byte; no preservation or initialized value of padding is claimed',
            'termination': 'normal-return source/library/allocator scope, finite exact count loop; no hardware or allocator termination inferred'},
        'observation': {'protected': 'every incoming allocated identity, live or dead, with arbitrary element/payload type',
            'incoming_type_restriction': None, 'preserves': ['allocation metadata', 'live storage contents and initialization', 'dead-identity ghost history'],
            'dead_physical_bytes_preserved': False,
            'address_reuse': 'a fresh identity may reuse a dead identity physical address; it does not modify that dead identity ghost snapshot',
            'source_rule': 'pointwise private-effect induction from never-issued source-created receiver/buffer identities; no typed map ownership inference',
            'hidden': 'private source/destination/buffer and administrative storage, their histories and frontier increments'},
        'source_model_TCB': {
            'plain_library_assumption': std_models.SENTENCE_LIBRARY.format(
                clang=lowering.tool['clang'], types='std_vector_int', standard=std_models.STANDARD, model=MODEL['id']),
            'plain_allocation_assumption': std_models.SENTENCE_ALLOCATION,
            'moved_from_empty_is_portable_Cpp17_postcondition': False,
            'moved_from_empty': 'the complete selected model resets source fields; this source/library correspondence is explicit TCB, not the portable C++17 valid-but-unspecified postcondition',
            'allocation': 'successful allocation returns a fresh, valid, suitably aligned, freeable buffer of n int objects and frames all incoming caller-visible allocation metadata/contents/initialization',
            'release': 'valid dynamic release ends that allocation only; null release is inert; all other incoming allocation observations are framed',
            'environment': 'default std::allocator spelling and TU screening do not prove replacement/interposition-free behavior; any linked allocator/deallocator observable effects are covered only by the explicit model correspondence TCB',
            'source_storage': 'normal lexical automatic entry provides fresh distinct writable source/destination/administrative objects; full layout/Heap/source correspondence must be checked before adoption'},
        'scientific_dependencies': dependencies, 'source_derivation_checked': True,
        'derivation_scope': 'exact conditional source grammar/effect/scalar rule, not completed scientific dependency or physical memory translation',
        'all_scientific_dependencies_admitted': False, 'source_admission': False,
        'source_heap_bridge_established': False, 'source_typed_bridge_established': False,
        'caller_acceptance': False, 'current_records_admitted': [],
        'required_before_launch': ['complete exact historical/current mathematical context binding including pending move4 encoding',
            'actual source-created Heap header/phase/layout/cleanup composition under explicit allocator/library/storage TCB',
            'fresh complete original ordinary/RTE/init/frame/smoke diagnostic and current generated-input preflight'],
    }
    files.update({'sources/original.cc': original, 'sources/original-caller.c': lowering.text.encode(),
                  'views/unreachable-fallback-eliminated.c': reduced})
    files.update({'sources/original-'+name+'.c': raw for name, raw in originals.items()})
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
    _need(not directory.is_symlink() and not any(p.is_symlink() or not (p.is_file() or p.is_dir()) for p in paths) and
          {str(p.relative_to(directory)) for p in paths if p.is_file()} == set(files) and
          {str(p.relative_to(directory)) for p in paths if p.is_dir()} == parents,
          'closed move canonical packet membership or path differs')
    _need(all((directory/name).read_bytes() == raw for name, raw in files.items()),
          'closed move canonical source/effect/dependency/claim differs')
    return plan


def check_launch(lowering, source, formal_texts, directory):
    check(lowering, source, formal_texts, directory)
    raise Refused('complete exact evidence, source/Heap composition and original diagnostic remain required')
