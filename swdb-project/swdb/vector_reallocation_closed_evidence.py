"""2026-10-16 ET. Closed source effect/observation derivation, still unadmitted.

This rule reasons about private source effects and every incoming allocation.
It does not encode arbitrary Typed memory as Heap integer/pointer cells, and
does not infer ownership or satisfiability from the modular native diagnostic.
"""
import hashlib
import json
import re
from pathlib import Path

from swdb import vector_reallocation_closed_lifetime as glue
from swdb import vector_reallocation_closed_lifetime_parts as parts


class Refused(ValueError):
    pass


CONSTRUCTOR_BODY = '''static void std_vector_int_ctor_count_value(std_vector_int *this, size_t n, int value) {
  this->data = NULL; this->size = 0; this->capacity = 0;
  if (n == 0) return;
  this->data = swdb_alloc_int(n);
  this->capacity = n;
  for (size_t k = 0; k < n; ++k) this->data[k] = value;
  this->size = n;
}'''


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2)+'\n').encode()


def identity():
    return {'id': 'vector-closed-source-observation-1',
            'sha256': _sha(_json({'source': _sha(Path(__file__).read_bytes()),
                                  'source_gluing': glue.identity(), 'conjunctions': parts.identity()}))}


def _tokens(text):
    return re.findall(r'\w+|[^\s]', re.sub(r'/\*.*?\*/|//[^\n]*', '', text, flags=re.S))


def _span(raw, needle):
    encoded = needle.encode()
    if raw.count(encoded) != 1:
        raise Refused('one exact executable source operation is required: '+needle)
    begin = raw.index(encoded)
    return {'begin': begin, 'end': begin+len(encoded), 'sha256': _sha(encoded)}


def _frame(steps, private):
    """Structural source-effect frame rule; no desired theorem is an input.

    A store/lifetime transition changes its target only. A loop preserves the
    same pointwise frame by induction when every iteration targets a private
    object. Allocation/release external effects require the explicit pinned
    allocator/deallocator model TCB. Access and termination are separate VCs.
    """
    checked = []
    for step in steps:
        operation = step['operation']
        if operation == 'loop':
            inner = _frame(step['body'], private)
            checked.append({'operation': 'loop', 'inductive_body': inner,
                            'range': step['range'], 'arbitrary_iteration': True})
        elif operation == 'release' and step['target'] == 'null':
            checked.append({'operation': 'release', 'target': 'null',
                            'pointwise_frame': 'the actual null-release transition is identity under the pinned deallocator model'})
        elif operation in {'begin_automatic', 'store', 'allocate', 'release', 'end_automatic'}:
            if step['target'] not in private:
                raise Refused('source effect could modify an incoming object')
            checked.append({'operation': operation, 'target': step['target'],
                            'pointwise_frame': 'incoming object differs from this target by source freshness'})
        else:
            raise Refused('unaccounted source effect')
    return {'all_steps_checked': True, 'protected': 'all incoming allocated objects',
            'fresh_private_targets': sorted(private), 'steps': checked,
            'induction_rule': 'composition and arbitrary-count iteration of pointwise identity on the protected allocation set'}


def _ordinary_ledger(function, requirements):
    """Account for the whole existing diagnostic using the direct source rule.

    These are source discharges to validate after complete mathematical evidence;
    none imports the native modular constructor post-state as a proof premise.
    """
    known = {
        'constructor': {row['id'] for row in requirements['constructor_dependency']['required_targets']},
        'gluing': {row['id'] for row in requirements['unchanged_gluing_dependencies']},
        'positive': {row['id'] for row in requirements['obligations']},
    }
    rows = [
        ('terminates', 'constructor', ['ctor.numeric'],
         'source finite count loop with numeric decreasing variant; normal-return allocator/library TCB'),
        ('ensures', 'positive', ['positive.cleanup.scalar'],
         'zero branch captures literal0; positive branch captures initialized value7 before actual release'),
        ('exits', 'constructor', ['ctor.numeric'],
         'exact source CFG has one unconditional scalar return and no reachable fallback cleanup; original normal-return scope'),
        ('assert_swdb_closed_data', 'constructor', ['ctor.qualified.zero_post', 'ctor.qualified.positive_post.repr'],
         'actual constructor fields/initialization imply the original data readable precondition; direct data body returns its actual field'),
        ('assert_rte_initialization', 'constructor', ['ctor.fields.initialized'],
         'constructor initializes the actual receiver data field on both branches before capture'),
        ('assert_swdb_closed_reserve', 'constructor', ['ctor.qualified.zero_post', 'ctor.qualified.positive_post.repr'],
         'exact source constructor capacity=count and initialized representation; signed32 nonnegative count meets the original maximum'),
        ('assert_swdb_reserve_no_growth', 'constructor', ['ctor.capacity.entry', 'ctor.final.post'],
         'the unchanged reserve argument equals constructor capacity on both branches, so the source growth branch is false'),
        ('assert_rte_initialization_2', 'constructor', ['ctor.fields.initialized'],
         'the local saved pointer is initialized by the exact pure data-field return, independently of pointee initialization and the later return scalar'),
        ('assert_rte_initialization_3', 'positive', ['positive.exit_image.integer.initialization'],
         'the source positive guard places index0 in the actual fully initialized int region'),
        ('assert_rte_mem_access', 'positive', ['positive.exit_image.integer.access'],
         'the actual private live int buffer has count>0 and element0 readable before release'),
        ('assert_swdb_closed_dtor_repr', 'constructor', ['ctor.qualified.zero_post', 'ctor.qualified.positive_post.repr'],
         'data and no-growth reserve preserve the complete actual constructor representation; freeability/release remain separate source duties'),
        ('assert_rte_initialization_4', 'positive', ['positive.cleanup.scalar'],
         'the copied scalar remains initialized across destruction and automatic lifetime end'),
        ('assigns_normal_part1', 'gluing', ['constructor.frame'],
         'direct source private-effect induction frames every incoming allocation and every byte, independent of incoming object type'),
        ('assigns_normal_part2', 'gluing', ['constructor.frame'],
         'same complete source frame on the other normal partition; actual allocator/deallocator framing remains explicit TCB'),
        ('assigns_normal_part3', 'gluing', ['zero.cleanup'],
         'empty constructor, actual null release and receiver scope end change no incoming object'),
        ('assigns_exit', 'positive', ['positive.cleanup.frame.objects', 'positive.cleanup.frame.contents', 'positive.cleanup.frame.initialization'],
         'actual dynamic release and receiver scope end preserve every incoming allocation by the source footprint rule'),
        ('call_std_vector_int_ctor_count_value_requires', 'gluing', ['receiver.entry'],
         'normal source automatic storage supplies valid aligned receiver; original nonnegative signed32 count widens exactly within maximum'),
    ]
    output = []
    for suffix, group, dependencies, source_rule in rows:
        if not set(dependencies) <= known[group]:
            raise Refused('source ordinary discharge cites a changed or missing mathematical target')
        output.append({'goal': 'typed_real_'+function+'_'+suffix,
            'scientific_dependency_group': group, 'required_targets': dependencies,
            'source_discharge': source_rule, 'uses_native_constructor_post_state': False,
            'native_result_role': 'supplemental conditional observation', 'status': 'pending complete evidence and source-rule review'})
    if len({row['goal'] for row in output}) != 17:
        raise Refused('the complete original ordinary source census changed')
    return output


def _original_ledger(function, projected):
    """Keep the complete original 24 ordinary / nine smoke source obligation map."""
    prefix = 'typed_real_'+function+'_'
    selected = {row['goal'].removeprefix(prefix): row for row in projected}
    mapping = [('terminates', 'terminates'), ('ensures', 'ensures'), ('exits', 'exits'),
        ('assert_rte_initialization', 'assert_rte_initialization_2'),
        ('assert_rte_initialization_2', 'assert_rte_initialization_3'),
        ('assert_rte_initialization_3', 'assert_rte_initialization_4'),
        ('assert_rte_mem_access', 'assert_rte_mem_access'),
        ('call_std_vector_int_ctor_count_value_requires', 'call_std_vector_int_ctor_count_value_requires'),
        ('call_std_vector_int_data_requires', 'assert_swdb_closed_data'),
        ('call_std_vector_int_reserve_requires', 'assert_swdb_closed_reserve')]
    ordinary = [{**selected[replacement], 'goal': prefix+original,
                 'source_mapping': 'original obligation reconstructed directly from the checked source rule'}
                for original, replacement in mapping]
    ordinary.append({'goal': prefix+'call_std_vector_int_dtor_requires',
        'source_discharge': 'actual constructor representation and capacity=count remain unchanged through data/no-growth reserve; at zero capacity the original freeable disjunction short-circuits, otherwise the actual source-fresh dynamic buffer is freeable under the checked allocator/constructor rule',
        'required_targets': ['constructor35 complete closure', 'destructor11 complete closure',
                             'positive.exit_image.buffer_freeable', 'zero.cleanup', 'all positive cleanup leaves'],
        'native_wp_freeable_supported': False, 'native_false_or_ignored_fact_changed': False,
        'uses_native_constructor_post_state': False, 'status': 'pending complete source evidence'})
    frame = selected['assigns_normal_part1']
    ordinary += [{**frame, 'goal': prefix+'assigns_normal_part'+str(index)} for index in range(1, 8)]
    ordinary += [{**frame, 'goal': prefix+'assigns_exit_part'+str(index)} for index in range(1, 7)]
    smokes = [prefix+name for name in ['wp_smoke_default_requires', 'wp_smoke_dead_code_s49',
              'wp_smoke_dead_code_s53', 'wp_smoke_dead_code_s54', 'wp_smoke_dead_code_s58']]
    smokes += ['typed_real_std_vector_int_'+name for name in [
        'ctor_count_value_wp_smoke_dead_call_s47', 'data_wp_smoke_dead_call_s48',
        'reserve_wp_smoke_dead_call_s49', 'dtor_wp_smoke_dead_call_s56']]
    if len({row['goal'] for row in ordinary}) != 24 or len(set(smokes)) != 9:
        raise Refused('the complete original obligation census changed')
    return {'ordinary': ordinary, 'ordinary_count': 24, 'frame_partitions': 13,
        'smokes': [{'goal': goal, 'proof_credit': False, 'satisfiability_claim': False} for goal in smokes],
        'smoke_count': 9, 'original_entry_refusal_preserved': True,
        'original_native_initialization_and_freeable_failures_preserved': True,
        'projection_removes_no_source_obligation': True}


def _administrative_storage(history, branch, constructor):
    """Explicit private source call frames, counter, alias and scalar storage.

    These source objects are a separate private store component, hidden by the
    observation rule. They are not silently inserted into the selected Heap
    receiver/buffer identity counter. No address of their storage escapes in the
    exact checked caller and model executable grammars.
    """
    event = {row['event']: row for row in history['events']}
    frames = [('constructor', ['ctor.this', 'ctor.n', 'ctor.value']),
              ('data capture', ['data.this', 'caller.saved']),
              ('reserve', ['reserve.this', 'reserve.n']),
              ('guarded scalar capture', ['caller.scalar']), ('destructor', ['dtor.this'])]
    objects = [{'id': name, 'source_event': event[site], 'fresh_at_caller_entry': True,
                'address_escapes': False, 'dynamically_freeable': False,
                'initialization': 'source parameter copy' if not name.startswith('caller.') else
                    'initialized pointer value from actual data field' if name == 'caller.saved' else
                    'guarded initialized scalar capture before destruction'}
               for site, names in frames for name in names]
    if branch == 'positive':
        objects.append({'id': 'ctor.k', 'source': _span(constructor, 'for (size_t k = 0; k < n; ++k) this->data[k] = value;'),
                        'fresh_at_caller_entry': True, 'address_escapes': False,
                        'dynamically_freeable': False, 'initialization': 'size_t k=0, then exact ++k per iteration'})
    steps = []
    def begin(names, initialized=True):
        for target in names:
            steps.append({'operation': 'begin_automatic', 'target': target})
            if initialized:
                steps.append({'operation': 'store', 'target': target})
    def end(names):
        steps.extend({'operation': 'end_automatic', 'target': target} for target in reversed(names))
    begin(['ctor.this', 'ctor.n', 'ctor.value'])
    if branch == 'positive':
        begin(['ctor.k'])
        steps.append({'operation': 'loop', 'range': '0 <= k < n',
                      'body': [{'operation': 'store', 'target': 'ctor.k'}]})
        end(['ctor.k'])
    end(['ctor.this', 'ctor.n', 'ctor.value'])
    begin(['caller.saved'], initialized=False)
    begin(['data.this']); end(['data.this'])
    steps.append({'operation': 'store', 'target': 'caller.saved'})
    begin(['reserve.this', 'reserve.n']); end(['reserve.this', 'reserve.n'])
    begin(['caller.scalar'])
    begin(['dtor.this']); end(['dtor.this'])
    end(['caller.saved', 'caller.scalar'])
    return {'objects': objects, 'frame_induction': _frame(steps, {row['id'] for row in objects}),
        'ordering': 'each activation/counter ends at its exact source call/for scope; caller.saved and caller.scalar remain initialized through capture/return and end at caller scope',
        'source_parameter_count': 'the caller count parameter is read-only and already exists at caller entry; it is never silently reclassified private',
        'transient_return_value': 'data() returns the initialized receiver pointer value; value transfer to saved is separate from its pointed-to bytes',
        'observation_projection': 'fresh administrative source storage is explicitly existentially hidden in a separate private store component; it does not consume Heap.next in the selected receiver/buffer projection',
        'no_total_memory_encoding_claimed': True}


def declaration(lowering, source, formal_texts):
    try:
        requirements, canonical = parts.declaration(lowering, source, formal_texts)
    except ValueError as error:
        raise Refused(str(error)) from None
    certificate = requirements['source_view']
    candidate = lowering.vector_reallocation_candidate
    history = certificate['source_view']['source_lifetime']
    order = ['automatic declaration', 'constructor', 'data capture', 'reserve',
             'guarded scalar capture', 'destructor', 'return scalar', 'automatic lifetime end']
    if history['order'] != order or not history['return_scalar_before_destruction'] or \
            certificate['cfg']['fallback_reachable'] is not False:
        raise Refused('the complete original source effect/observation order changed')
    constructor = canonical['sources/original-constructor.c']
    body = constructor.decode().split('static void std_vector_int_ctor_count_value', 1)
    if len(body) != 2 or _tokens('static void std_vector_int_ctor_count_value'+body[1]) != _tokens(CONSTRUCTOR_BODY):
        raise Refused('the complete constructor executable effect grammar changed')
    if candidate['reserve_request'] != 'count' or certificate['original_assigns'] != r'assigns \nothing;':
        raise Refused('only the exact source no-growth count and original frame are supported')
    if not (0 <= 2147483647 < 4611686018427387903 and
            4*2147483647 <= 18446744073709551615 and 2147483647+1 <= 18446744073709551615):
        raise Refused('the pinned source arithmetic bounds are inconsistent')
    source_steps = [
        {'operation': 'store', 'target': 'receiver', 'field': field,
         'value': value, 'source': _span(constructor, text)}
        for field, value, text in [('data', 'null', 'this->data = NULL;'),
                                   ('size', 0, 'this->size = 0;'),
                                   ('capacity', 0, 'this->capacity = 0;')]]
    positive_steps = [*source_steps,
        {'operation': 'allocate', 'target': 'buffer', 'count': 'n',
         'source': _span(constructor, 'this->data = swdb_alloc_int(n);'),
         'external_effects': 'pinned allocator fresh/valid/freeable/normal-return/frame TCB'},
        {'operation': 'store', 'target': 'receiver', 'field': 'data', 'value': 'buffer',
         'source': _span(constructor, 'this->data = swdb_alloc_int(n);')},
        {'operation': 'store', 'target': 'receiver', 'field': 'capacity', 'value': 'n',
         'source': _span(constructor, 'this->capacity = n;')},
        {'operation': 'loop', 'range': '0 <= k < n',
         'source': _span(constructor, 'for (size_t k = 0; k < n; ++k) this->data[k] = value;'),
         'body': [{'operation': 'store', 'target': 'buffer', 'byte_offset': '4*k', 'value': 7,
                   'source': _span(constructor, 'this->data[k] = value;')}],
         'safety_and_termination': 'complete exact constructor35 prefix/access/numeric/variant obligations'},
        {'operation': 'store', 'target': 'receiver', 'field': 'size', 'value': 'n',
         'source': _span(constructor, 'this->size = n;')}]
    branches = {}
    for branch, constructor_steps, dynamic in [('zero', source_steps, False), ('positive', positive_steps, True)]:
        steps = [{'operation': 'begin_automatic', 'target': 'receiver',
                  'source': next(row for row in history['events'] if row['event'] == 'automatic declaration')},
                 *constructor_steps,
                 {'operation': 'release', 'target': 'buffer' if dynamic else 'null',
                  'source': certificate['terminal_cleanup']['source_call'],
                  'external_effects': 'pinned deallocator releases this allocation only, null release is identity, and incoming program memory is framed'}]
        steps.append({'operation': 'end_automatic', 'target': 'receiver',
                      'source': next(row for row in history['events'] if row['event'] == 'automatic lifetime end')})
        frame = _frame(steps, {'receiver', 'buffer'} if dynamic else {'receiver'})
        administrative = _administrative_storage(history, branch, constructor)
        branches[branch] = {'condition': 'n == 0' if not dynamic else '0 < n <= INT_MAX',
            'constructor_effects': constructor_steps, 'incoming_frame_induction': frame,
            'administrative_storage': administrative,
            'count_capacity_relation': 'count == capacity',
            'data_capture': 'null' if not dynamic else 'the actual fresh buffer identity at offset zero',
            'reserve_growth_branch': False, 'buffer_read_evaluated': dynamic,
            'scalar_captured_before_release': True, 'result': 7 if dynamic else 0,
            'terminal_cleanup': {'null_release_is_inert': not dynamic,
                'dynamic_buffer_released': dynamic, 'receiver_scope_ended': True,
                'transition': 'end_automatic(release(post,'+('buffer' if dynamic else '0')+'),receiver)'},
            'caller_visible_writes': [], 'returned_pointer': False,
            'later_private_pointer_observation': False}
    ordinary = _ordinary_ledger(lowering.function, requirements)
    plan = {'created': '2026-10-16 ET', 'checker': identity(), 'function': lowering.function,
        'original_contract': list(formal_texts), 'caller_premises_added': [],
        'source_view': certificate, 'source_events': history['events'],
        'source_history': {'receiver': 'not issued at caller entry',
            'positive_buffer': 'not issued at caller entry and distinct from receiver',
            'basis': 'exact begin_automatic prefix, unchanged initialization stores preserving next, actual allocator identity, and buffer.identity source duty',
            'ownership_from_Typed_maps': False},
        'source_safety': {'signed_count_from_original_requires': '0 <= n <= INT_MAX',
            'positive_count_bound': 2147483647, 'model_maximum_count': 4611686018427387903,
            'count_conversion': 'nonnegative int to 64-bit unsigned is exact; byte multiplication and loop increment do not wrap',
            'automatic_storage_availability': 'normal source automatic-object entry provides a fresh aligned receiver extent; this is the checked source storage interpretation, not an extra caller requires clause',
            'termination_scope': 'the exact fill loop is finite; the source observation theorem is conditional on modeled normal return and does not infer allocator or hardware termination from the native terminates goal',
            'null_plus_zero_used': False, 'zero_branch': 'guard is false and no buffer pointer arithmetic or read is evaluated',
            'positive_branch': '0 < n makes element zero in bounds; exact int-cell initialization/access/range and fill7 duties discharge the read',
            'constructor_and_dtor_original_preconditions': 'derived from source-created storage, complete constructor output and original allocator/freeable TCB; no caller premise is added'},
        'branch_derivations': branches,
        'observation': {'protected_objects': 'every incoming allocated program object, live or dead',
            'preserves': ['allocation identity', 'liveness', 'extent', 'address', 'writability',
                          'contents of every byte', 'initialization of every byte'],
            'incoming_type_restriction': None, 'total_Typed_to_Heap_encoding_claimed': False,
            'coordinate_system': 'allocation identity; physical address reuse does not merge identities',
            'byte_preservation_scope': 'actual live physical storage and retained dead-identity ghost snapshots are distinct observations',
            'live_objects': 'actual incoming live program allocation identity, metadata, contents and initialization are preserved',
            'dead_objects': 'retained dead allocation identities and their ghost history snapshots remain unchanged and non-forming; freed physical bytes are not observable storage of that dead identity',
            'dead_physical_bytes_preserved': False,
            'reused_address_rule': 'new private allocation may reuse a dead allocation physical address; its new identity and bytes are distinct from the retained dead-identity history',
            'source_rule': 'all source stores and lifetime effects target identities not issued at entry; pointwise identity outside that private footprint composes and is invariant under the exact unbounded fill loop',
            'allocator_internal_effects': 'covered by the explicit pinned model framing/observation TCB, not inferred absent from standard conformance or full-TU screening'},
        'native_projected_C': {'role': 'supplemental conditional evidence only',
            'required_complete_census': {'ordinary': 17, 'external_query_goals': 7, 'internal_Qed': 10, 'smokes': 4},
            'constructor_premise_discharged_by_native': False, 'smoke_timeout_implies_satisfiable': False,
            'original_entry_refusal_and_reader_not_proven_preserved': True,
            'lifetime_facts_from_Typed': False},
        'ordinary_source_discharge_ledger': ordinary,
        'original_source_obligation_ledger': _original_ledger(lowering.function, ordinary),
        'explicit_allocator_library_TCB': requirements['explicit_allocator_library_TCB'],
        'scientific_dependencies': {
            'constructor': requirements['constructor_dependency'],
            'destructor': requirements['destructor_dependency'],
            'private_frame': requirements['private_frame_dependency'],
            'unchanged_gluing': requirements['unchanged_gluing_dependencies'],
            'positive_conjunctions': [{'id': row['id'], 'sha256': row['sha256']} for row in requirements['obligations']],
            'historical_identity_policy': 'content-identical scientific components may be reused with their complete retained hypotheses/source/runtime/solver closure and actual historical method/checker/compiler identities; no old record is relabeled current'},
        'all_scientific_dependencies_admitted': False, 'source_admission': False,
        'source_typed_bridge_established': False, 'caller_acceptance': False,
        'proof_admission': 'unsupported: complete exact scientific evidence and independent source-effect interpretation review are required; report hashes or acceptance strings alone are insufficient'}
    files = {name: canonical[name] for name in ('sources/original.cc', 'sources/original-caller.c',
        'sources/original-constructor.c', 'sources/qualified-constructor.c',
        'sources/original-destructor.c', 'sources/qualified-destructor.c', 'theory/heap_reallocation.mlw')}
    files['manifest.json'] = _json(plan)
    return plan, files


def prepare(lowering, source, formal_texts, directory):
    plan, files = declaration(lowering, source, formal_texts)
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    for name, raw in files.items():
        path = directory/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return plan


def check(lowering, source, formal_texts, directory):
    plan, files = declaration(lowering, source, formal_texts)
    directory = Path(directory)
    paths = list(directory.rglob('*'))
    parents = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
    if directory.is_symlink() or any(path.is_symlink() or not (path.is_file() or path.is_dir()) for path in paths) or \
            {str(path.relative_to(directory)) for path in paths if path.is_file()} != set(files) or \
            {str(path.relative_to(directory)) for path in paths if path.is_dir()} != parents:
        raise Refused('closed source effect/observation canonical membership differs')
    for name, raw in files.items():
        if (directory/name).read_bytes() != raw:
            raise Refused('closed source effect, observer or exact dependency differs: '+name)
    return plan


def check_launch(lowering, source, formal_texts, directory):
    check(lowering, source, formal_texts, directory)
    raise Refused('complete scientific evidence and independently reviewed source effect/observation interpretation remain required')
