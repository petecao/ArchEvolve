"""Closed qualified source event/clause ownership; created 2026-10-16 ET.

This is a trusted exact-source map, not a generic C completeness parser. The
parent catalog digest and inverse qualification bind the whole source first.
All named obligations remain pending; source coverage alone admits no proof.
"""
import hashlib
import re

from swdb import std_models, vector_reallocation_model as model


GROW = [
    ('grow.allocate', 'int *fresh = swdb_alloc_int(cap);',
     ['grow.alloc.identity', 'grow.alloc.output', 'grow.alloc.frame', 'grow.numeric']),
    ('grow.loop.init', 'size_t k = 0;', ['grow.copy.establish', 'grow.numeric']),
    ('grow.loop.test', 'k < this->size;', ['grow.entry.reads', 'grow.copy.read', 'grow.copy.exit']),
    ('grow.copy', 'fresh[k] = this->data[k];',
     ['grow.entry.reads', 'grow.copy.read', 'grow.copy.write', 'grow.copy.step']),
    ('grow.loop.increment', '++k)', ['grow.numeric', 'grow.copy.step']),
    ('grow.release', 'swdb_free(this->data);',
     ['grow.entry.reads', 'grow.free.argument', 'grow.free.survival', 'grow.free.aliases']),
    ('grow.data.store', 'this->data = fresh;', ['grow.free.survival', 'grow.post.eligibility']),
    ('grow.capacity.store', 'this->capacity = cap;',
     ['grow.store.capacity', 'grow.post.eligibility', 'grow.post.values',
      'grow.post.old_invalid', 'grow.post.frame']),
]
CTOR = [
    ('ctor.zero.data', 'this->data = NULL;', ['ctor.rte.zero_data', 'ctor.fields.initialized']),
    ('ctor.zero.size', 'this->size = 0;', ['ctor.rte.zero_size', 'ctor.fields.initialized']),
    ('ctor.zero.capacity', 'this->capacity = 0;', ['ctor.rte.zero_capacity', 'ctor.fields.initialized']),
    ('ctor.zero.return', 'if (n == 0) return;',
     ['ctor.zero.post', 'ctor.zero.frame', 'ctor.qualified.zero_post']),
    ('ctor.allocated.data', 'this->data = swdb_alloc_int(n);',
     ['ctor.alloc.identity', 'ctor.alloc.well_formed', 'ctor.alloc.separation',
      'ctor.alloc.extent', 'ctor.alloc.uninitialized', 'ctor.rte.allocated_data', 'ctor.frame.preexisting']),
    ('ctor.allocated.capacity', 'this->capacity = n;', ['ctor.rte.allocated_capacity', 'ctor.capacity.entry']),
    ('ctor.loop.init', 'size_t k = 0;', ['ctor.prefix.establish', 'ctor.capacity.entry', 'ctor.numeric']),
    ('ctor.loop.test', 'k < n;', ['ctor.store.access', 'ctor.prefix.exit', 'ctor.numeric']),
    ('ctor.fill', 'this->data[k] = value;', ['ctor.store.access', 'ctor.prefix.step', 'ctor.frame.loop_step']),
    ('ctor.loop.increment', '++k)', ['ctor.numeric', 'ctor.prefix.step']),
    ('ctor.final.size', 'this->size = n;',
     ['ctor.rte.final_size', 'ctor.final.post', 'ctor.frame.final', 'ctor.qualified.positive_post']),
]


def build(member, source, obligations, logical_obligations=()):
    # certificate() checks both the parent identity and exact inverse restoration
    # of every helper/body, rather than admitting a source with familiar needles.
    cert = model.certificate(member)
    if hashlib.sha256(source.encode()).hexdigest() != cert['qualified_source_sha256']:
        raise ValueError('the source inventory requires the exact qualified source')
    ids = {row['id'] for row in obligations}
    expansions = {row['id']: row['parts'] for row in logical_obligations}
    def span(text, offset=0):
        return {'begin': offset, 'end': offset+len(text.encode()),
                'sha256': hashlib.sha256(text.encode()).hexdigest()}
    events, clauses, helpers = [], [], []
    original = model.MEMBERS[member]
    pieces = std_models._vector_unit(re.fullmatch(r'(std_vector_int)_(\w+)', original))
    for function, fragment in pieces:
        if function.endswith('_types'):
            continue
        qualified = model._qualify(fragment, original)
        if source.count(qualified) != 1:
            raise ValueError('a complete source/helper fragment is absent or ambiguous')
        start = source.index(qualified)
        trusted = function in {'swdb_alloc_int', 'swdb_free'}
        if trusted:
            helpers.append({'name':function, 'source':span(qualified, start),
                'role':'existing allocator policy; not a proved model body',
                'body_correspondence':next(row for row in cert['executable_bodies']
                                           if row['original_function'] == function)})
        elif function.endswith('_grow'):
            table = GROW
        elif function.endswith('_ctor_count_value'):
            table = CTOR
        elif function.endswith('_reserve'):
            table = [('reserve.branch_and_call',
                'if (n > this->capacity) std_vector_int_realloc_v3_grow(this, n);',
                ['reserve.entry.capacity', 'reserve.no_growth', 'reserve.growing.pre',
                 'reserve.growing.post', 'reserve.growing.old_invalid', 'reserve.growing.frame'])]
        elif function.endswith('_dtor'):
            table = [('dtor.load_and_release', 'swdb_free(this->data);',
                ['dtor.data.read', 'dtor.free.argument', 'dtor.null.no_op',
                 'dtor.alias.invalidated', 'dtor.post.old_invalid', 'dtor.frame.surviving',
                 'dtor.frame.other_live', 'dtor.receiver.overlap'])]
        else:
            raise ValueError('an executable helper has no closed event inventory')
        if not trusted:
            for name, needle, owners in table:
                owners = [part for owner in owners for part in expansions.get(owner, [owner])]
                if qualified.count(needle) != 1 or not set(owners) <= ids:
                    raise ValueError('an executable source event has no unique complete obligation ownership')
                events.append({'id':name, 'function':function,
                    'source':span(needle, start+qualified.index(needle)), 'obligations':owners})
        # Clause boundaries use the controlled source's line-oriented ACSL
        # clauses; quantified-variable semicolons remain inside their clause.
        for block in re.finditer(r'/\*@(?P<body>.*?)\*/', qualified, re.S):
            body = block.group('body')
            matches = list(re.finditer(r'(?m)(?:^|\n)\s*(loop invariant|loop assigns|loop variant|requires|ensures|assigns|allocates|frees)\b', body))
            for index, match in enumerate(matches):
                begin = match.start(1)
                end = matches[index+1].start() if index+1 < len(matches) else len(body)
                text = body[begin:end].rstrip()
                kind = match.group(1)
                owners = [] if trusted or kind == 'requires' else sorted({
                    goal for event in events if event['function'] == function for goal in event['obligations']})
                clauses.append({'function':function, 'kind':kind,
                    'source':span(text, start+block.start('body')+begin),
                    'role':('existing allocator policy' if trusted else
                            'entry domain; caller discharge required' if kind == 'requires' else
                            'pending source-mapped body obligation'), 'obligations':owners})
    return {'role':'closed exact-source map; no proof admission',
            'source_sha256':cert['qualified_source_sha256'], 'events':events, 'clauses':clauses,
            'trusted_helpers':helpers, 'unmapped_executable_events':[], 'unmapped_contract_clauses':[],
            'pending':['independent completeness review', 'selected typed-source image and caller discharge',
                       'fresh complete ordinary/smoke proofs and import/task closure']}
