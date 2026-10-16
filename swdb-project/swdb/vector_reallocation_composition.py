"""Pending source-local call applications; created 2026-10-16 ET.

These are duties, not an admitted caller state or a theorem-import mechanism.
Automatic-storage and signed-int embedding still require their source/runtime
proof; no new premise is placed on the public caller contract.
"""
import hashlib


def constructor_entry(candidate, contract):
    from swdb import vector_reallocation_model as model
    if candidate['count']['type'] != 'int':
        raise ValueError('constructor entry application requires its checked signed-int parameter')
    callee='std_vector_int_realloc_v3_ctor_count_value'
    source=model.model_text(callee)
    precondition=(r'requires \valid(this) && n <= ((size_t)PTRDIFF_MAX < SIZE_MAX / sizeof(int) ? '
                  r'(size_t)PTRDIFF_MAX : SIZE_MAX / sizeof(int));')
    if source.count(precondition)!=1:
        raise ValueError('the original constructor precondition application changed')
    start=source.index(precondition);raw=precondition.encode()
    call=next(row['source']for row in candidate['call_obligations']if row['call']=='ctor_count_value')
    events={row['event']:row for row in candidate['lowered_lifetime']['events']
            if row['reachable_on_normal_return']}
    statement=(r'\forall Heap::heap h; \forall integer a,n; Heap::well_formed(h) && '
               r'Heap::automatic_available(h,24,8,a) && 0 <= n <= 2147483647 ==> '
               r'Heap::typed_writes(Heap::begin_automatic(h,24,a),Heap::fresh_id(h),0,24,8) && '
               r'!Heap::freeable(Heap::begin_automatic(h,24,a),Heap::fresh_id(h),0) && '
               r'0 <= n <= 4611686018427387903')
    row={'id':'apply.ctor.entry','status':'pending','dependencies':[],
         'source_groups':['L1','C1'],'source':call,
         'lowered_events':[events['automatic declaration'],events['constructor']],
         'statement':statement}
    receipt={'callee':callee,'source_parameter':candidate['count'],'source_call':call,
             'contract_clause':contract['clauses'][0],
             'contract_identity':contract['ordinary_contract_identity'],
             'model_arguments':{'this':'Heap::fresh_id(h), offset0',
                                'n':'source signed int converted to size_t','value':7},
             'callee_precondition':{'begin':len(source[:start].encode()),
                                   'end':len(source[:start].encode())+len(raw),
                                   'sha256':hashlib.sha256(raw).hexdigest(),
                                   'source_sha256':hashlib.sha256(source.encode()).hexdigest()},
             'automatic_storage_embedding':'pending source-runtime discharge; not a caller assumption',
             'source_type_range':'pending signed32 source image; separate numeric kernel asserts actual C ABI',
             'max_size_application':'pending selected ABI/numeric target and actual callee precondition correspondence',
             'entry_heap':'arbitrary well-formed incoming heap; no global pointer-map restriction',
             'proof_status':'unexecuted call-entry duty only; no complete caller or callee theorem granted'}
    return row,receipt


def zero_constructor(candidate):
    from swdb import vector_reallocation_model as model
    source=model.model_text('std_vector_int_realloc_v3_ctor_count_value')
    def span(text):
        if source.count(text)!=1:raise ValueError('the source zero-constructor path changed')
        begin=len(source[:source.index(text)].encode());raw=text.encode()
        return {'begin':begin,'end':begin+len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    stores=span('this->data = NULL; this->size = 0; this->capacity = 0;')
    returned=span('if (n == 0) return;')
    if stores['end']>=returned['begin']:
        raise ValueError('the source constructor zero return precedes its initial stores')
    entry='Heap::begin_automatic(h,24,a)'
    state='t25_initial('+entry+',Heap::fresh_id(h),0)'
    call=next(row['source']for row in candidate['call_obligations']if row['call']=='ctor_count_value')
    events={row['event']:row for row in candidate['lowered_lifetime']['events']
            if row['reachable_on_normal_return']}
    statement=(r'\forall Heap::heap h; \forall integer a; Heap::well_formed(h) && '
               r'Heap::automatic_available(h,24,8,a) ==> '
               't25v3_eligible('+state+',Heap::fresh_id(h),0,0,0,0,0) && '
               'Heap::pointer_at('+state+',Heap::fresh_id(h),0,0,0)')
    row={'id':'apply.ctor.zero','status':'pending','dependencies':[],
         'source_groups':['L1','C1','C2'],'source':call,
         'lowered_events':[events['automatic declaration'],events['constructor']],
         'source_path_condition':'source count == 0; the zero branch does not restrict caller entry',
         'statement':statement}
    receipt={'state_before':entry,'state_after':state,'initial_stores':stores,'zero_return':returned,
             'source_path_condition':row['source_path_condition'],'allocation_executed':False,'buffer_loads':0,
             'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
             'source_call':call,'source_parameter':candidate['count'],
             'proof_rule':'pending exact zero-branch store translation and source-runtime automatic embedding; no callee postcondition imported',
             'positive_path':'unproved; this zero state grants no positive-path result',
             'caller_entry_restricted':False}
    return row,receipt


def positive_constructor_entry(candidate):
    """Pending normal-return path application, never an allocator premise at entry."""
    from swdb import vector_reallocation_model as model
    source=model.model_text('std_vector_int_realloc_v3_ctor_count_value')
    def span(text):
        if source.count(text)!=1:
            raise ValueError('the source positive-constructor prefix changed')
        begin=len(source[:source.index(text)].encode());raw=text.encode()
        return {'begin':begin,'end':begin+len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    fragments={name:span(text) for name,text in [
        ('initial_stores','this->data = NULL; this->size = 0; this->capacity = 0;'),
        ('zero_return','if (n == 0) return;'),
        ('allocation','this->data = swdb_alloc_int(n);'),
        ('capacity_store','this->capacity = n;'),
        ('loop_entry','for (size_t k = 0; k < n; ++k)')]}
    ordered=list(fragments.values())
    if any(left['end']>=right['begin']for left,right in zip(ordered,ordered[1:])):
        raise ValueError('the source positive-constructor allocation/loop order changed')
    begin,end=ordered[0]['begin'],ordered[-1]['end']
    prefix={'begin':begin,'end':end,'sha256':hashlib.sha256(source.encode()[begin:end]).hexdigest()}
    entry='Heap::begin_automatic(h,24,a)';receiver='Heap::fresh_id(h)'
    initial='t25_initial('+entry+','+receiver+',0)'
    allocated='t25_allocated('+entry+','+receiver+',0,n,q)'
    available='Heap::available('+initial+',n,q)'
    call=next(row['source']for row in candidate['call_obligations']if row['call']=='ctor_count_value')
    events={row['event']:row for row in candidate['lowered_lifetime']['events']
            if row['reachable_on_normal_return']}
    condition='source count > 0; allocation returns normally'
    statement=(r'\forall Heap::heap h; \forall integer a,q,n; Heap::well_formed(h) && '
               r'Heap::automatic_available(h,24,8,a) && 0 < n <= 2147483647 && '+
               available+' ==> t25v3_ctor_inv('+allocated+','+receiver+
               ',0,Heap::fresh_id('+entry+'),n,0,7)')
    row={'id':'apply.ctor.positive_entry','status':'pending','dependencies':[],
         'source_groups':['L1','C1','C2','C3','C4','C5','QC2'],'source':call,
         'lowered_events':[events['automatic declaration'],events['constructor']],
         'source_path_condition':condition,'statement':statement}
    receipt={**fragments,'source_prefix':prefix,'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
             'source_call':call,'source_parameter':candidate['count'],
             'source_path_condition':condition,'state_before':entry,'state_after':allocated,
             'receiver_identity':receiver,'buffer_identity':'Heap::fresh_id('+entry+')',
             'initial_prefix_length':0,'fill_value':7,
             'allocation_relation':{'statement':available,
                 'discharge':'pending source allocator normal-return embedding; never a caller-entry premise',
                 'role':'existing uniform fresh-allocation output relation; no initialized buffer or desired constructor result'},
             'proof_rule':'pending source-local prefix application and initial loop invariant, with no callee postcondition imported',
             'caller_entry_restricted':False,
             'remaining':'fill establishment/step/exit, postcondition, frame, source-runtime embedding and current body-record eligibility remain pending'}
    return row,receipt


def reserve_entry(candidate):
    """Derive the source request/branch under a pending constructor post-state.

    The local antecedent must be discharged by the completed constructor and
    source-runtime relation. It is never appended to the public caller contract.
    This duty grants no reserve post-state, alias liveness or scalar result.
    """
    from swdb import vector_reallocation_model as model
    if candidate.get('count', {}).get('type') != 'int':
        raise ValueError('reserve application requires the checked signed-int count')
    request = candidate.get('reserve_request')
    if request not in {'count', 'count+1'}:
        raise ValueError('reserve application requires exact count or widened count+1')
    capacity = candidate.get('capacity_qualification', {})
    if capacity.get('id') != 'vector-cpp17-capacity-1' or \
            capacity.get('model_postcondition_to_prove') != 'capacity == count':
        raise ValueError('reserve branch requires the pending exact constructor capacity predecessor')
    callee = 'std_vector_int_realloc_v3_reserve'
    source = model.model_text(callee)
    constructor = model.model_text('std_vector_int_realloc_v3_ctor_count_value')

    def span(text, whole):
        if whole.count(text) != 1:
            raise ValueError('the source reserve precondition/branch or constructor capacity changed')
        begin = len(whole[:whole.index(text)].encode())
        raw = text.encode()
        return {'begin': begin, 'end': begin + len(raw),
                'sha256': hashlib.sha256(raw).hexdigest(),
                'source_sha256': hashlib.sha256(whole.encode()).hexdigest()}

    precondition = span(
        'requires std_vector_int_reallocatable_v3(this) && n <= '
        '((size_t)PTRDIFF_MAX < SIZE_MAX / sizeof(int) ? '
        '(size_t)PTRDIFF_MAX : SIZE_MAX / sizeof(int));', source)
    branch = span('if (n > this->capacity) std_vector_int_realloc_v3_grow(this, n);', source)
    exact_capacity = span('ensures this->capacity == n;', constructor)
    calls = [row['source'] for row in candidate['call_obligations'] if row['call'] == 'reserve']
    events = [row for row in candidate['lowered_lifetime']['events']
              if row['event'] == 'reserve' and row['reachable_on_normal_return']]
    if len(calls) != 1 or len(events) != 1:
        raise ValueError('reserve application needs one checked source call and lowered event')
    growing = request == 'count+1'
    term = '(n+1)' if growing else 'n'
    comparison = term + ' > n' if growing else 'n <= n'
    predicate = 't25v3_eligible(h,r,o,b,bo,n,n)'
    statement = (r'\forall Heap::heap h; \forall integer r,o,b,bo,n; '
                 + predicate + ' && 0 <= n <= 2147483647 ==> '
                 + predicate + ' && 0 <= ' + term + ' <= 4611686018427387903 && '
                 + comparison)
    row = {'id': 'apply.reserve.entry', 'status': 'pending', 'dependencies': [],
           'source_groups': ['QC2', 'R1', 'R2'], 'source': calls[0],
           'lowered_events': events, 'statement': statement}
    receipt = {
        'callee': callee, 'source_parameter': candidate['count'], 'source_call': calls[0],
        'source_request': request, 'request_term': term, 'growth_branch': growing,
        'callee_precondition': precondition, 'branch_and_call': branch,
        'constructor_exact_capacity': exact_capacity,
        'predecessor_discharge': 'pending completed constructor state, exact capacity and typed-source relation; not a caller-entry premise',
        'callee_precondition_correspondence': 'pending selected Typed source image, automatic placement and model layout',
        'state_before': 'h',
        'state_after': 'pending current qualified grow application' if growing else 'h',
        'source_effect': ('branch true; current grow call still requires discharge' if growing
                          else 'branch false; no body store or call'),
        'buffer_element_loads': 0, 'caller_premises_added': [],
        'current_proof_records_admitted': [],
        'proof_status': 'unexecuted source-local entry/branch duty; no reserve or caller theorem granted',
        'remaining': [
            'completed constructor state/capacity/typed-image source-runtime discharge',
            'current reserve/grow body-record admission and branch application',
            'observation, stale-alias liveness, cleanup and final incoming frame',
        ],
    }
    return row, receipt
