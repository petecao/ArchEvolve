"""Canonical original-source heap VC preparation. Created: 2026-10-15 ET.

Promoted from the independently accepted exact first-pair capability mapping.
The original count constructor uses an explicit universal-value specialization
at zero, with separately pinned source, events and isolated target names.
Preparing/checking packets executes no tool and is never a proof verdict.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

from swdb import c_lowering, std_models
from swdb.heap_model_vcs import PRELUDE, NUMERIC, specs

HERE = Path(__file__).resolve().parent
MEMBERS = ('std_vector_int_ctor_count_value', 'std_vector_int_dtor', 'std_vector_int_ctor_count')
sha = lambda data: hashlib.sha256(data).hexdigest()
REVIEWED_MODEL = {'id': 'swdb-std-models-2',
                 'sha256': 'cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2'}
REVIEWED_SOURCES = {
    'std_vector_int_ctor_count_value': '57cf2a6f3f9049f8edf41633f9ef60d0bb7c804e5ee937af796217a2a018c594',
    'std_vector_int_dtor': '1056f4f83c59a30941ec9417c36aada8eab4b62160087ae10315cd2ac9778317',
    'std_vector_int_ctor_count': 'bc6c76c9fe74a568bd81973eafba48e24b9f2f42604ad3c9994f742572c11358',
}


def original_sources(directory=None):
    if std_models.identity() != REVIEWED_MODEL:
        raise ValueError('reviewed source model changed; independent remapping required')
    sources = {name: ((directory / (name + '.original.c')).read_text() if directory
                      else c_lowering.model_text(name)) for name in MEMBERS}
    for name, text in sources.items():
        if sha(text.encode()) != REVIEWED_SOURCES[name]:
            raise ValueError('reviewed source shape changed; independent remapping required: ' + name)
    return sources


def span(source, needle):
    start = source.index(needle)
    return {'start': start, 'end': start + len(needle), 'text_sha256': sha(needle.encode())}


def store_transition(source):
    if re.search(r'for \(size_t k = 0; k < n; \+\+k\) this->data\[k\] = value;', source):
        return 'Heap::put_integer(h,b,4*k,v)'
    if re.search(r'for \(size_t k = 0; k < n; \+\+k\) \(void\)value;', source):
        return 'h'
    if re.search(r'for \(size_t k = 0; k < n; \+\+k\) this->data\[k\] = \(int\)0;', source):
        return 'Heap::put_integer(h,b,4*k,0)'
    if re.search(r'for \(size_t k = 0; k < n; \+\+k\) \(void\)0;', source):
        return 'h'
    raise ValueError('unmapped source loop transition')


def release_transition(source):
    calls = re.findall(r'\{\s*swdb_free\((this->data|NULL)\);\s*\}', source)
    if len(calls) != 1:
        raise ValueError('unmapped source release transition')
    return 'Heap::release(h,' + ('b' if calls[0] == 'this->data' else '0') + ')'


def count_id(name):
    """Distinct source targets; existing first-pair packet names stay unchanged."""
    return name.replace('ctor.', 'count.', 1) if 'ctor.' in name else 'control.count.' + name.removeprefix('control.')


def mapped_specs():
    original = specs()
    # Universal value theorems specialize to the source's literal zero. Remove
    # the bound value variable before token substitution; never substitute an
    # identifier substring or introduce a desired-result premise.
    count = []
    for name, member, needle, groups, statement in original:
        if member != MEMBERS[0]:
            continue
        if statement is not None:
            statement = re.sub(r'\bv\b', '0', statement.replace(',v;', ';'))
        count.append((count_id(name), MEMBERS[2], needle.replace('= value;', '= (int)0;'),
                      groups, statement))
    return original + count


def obligations(sources):
    result = []
    for name, member, needle, groups, statement in mapped_specs():
        goal = {'id': name, 'member': member, 'statement': statement,
                'source_spans': [span(sources[member], needle)], 'source_groups': groups,
                'dependencies': [], 'kind': 'c_kernel' if statement is None else 'check_lemma',
                'expected': 'not_proven' if name in {'control.omitted_store','control.count.omitted_store','control.wrong_release',
                                                     'control.stale_read','control.double_release'} else 'proven'}
        zero = member == MEMBERS[2]
        if name in {'control.omitted_store', 'control.count.omitted_store'}:
            goal['source_mutation'] = {'before': 'this->data[k] = (int)0;' if zero else 'this->data[k] = value;',
                                       'after': '(void)0;' if zero else '(void)value;'}
            mutant = sources[member].replace(goal['source_mutation']['before'], goal['source_mutation']['after'])
            transition = store_transition(mutant)
            value = '0' if zero else 'v'
            variables = 'r,o,b,n,k' if zero else 'r,o,b,n,k,v'
            goal['statement'] = (r'\forall Heap::heap h; \forall integer ' + variables + '; '
                                 f't25_inv(h,r,o,b,n,k,{value}) && k < n ==> '
                                 f't25_inv({transition},r,o,b,n,k+1,{value})')
            goal['source_transition'] = transition
        elif name == 'control.wrong_release':
            goal['source_mutation'] = {'before': 'swdb_free(this->data);', 'after': 'swdb_free(NULL);'}
            mutant = sources[member].replace('swdb_free(this->data);', 'swdb_free(NULL);')
            transition = release_transition(mutant)
            goal['statement'] = (r'\forall Heap::heap h; \forall integer r,o,b,bo,s,c; '
                                 r'Heap::well_formed(h) && t25_repr(h,r,o,b,bo,s,c) && '
                                 r'(c == 0 || Heap::freeable(h,b,bo)) && c > 0 ==> '
                                 f'!Heap::can_read({transition},b,bo,4)')
            goal['source_transition'] = transition
        elif name in {'ctor.prefix.step', 'count.prefix.step'}:
            transition = store_transition(sources[member])
            value = '0' if zero else 'v'
            variables = 'r,o,b,n,k' if zero else 'r,o,b,n,k,v'
            goal['statement'] = (r'\forall Heap::heap h; \forall integer ' + variables + '; '
                                 f't25_inv(h,r,o,b,n,k,{value}) && k < n ==> '
                                 f't25_inv({transition},r,o,b,n,k+1,{value})')
            goal['source_transition'] = transition
        elif name == 'dtor.post.old_invalid':
            transition = release_transition(sources[member])
            goal['source_transition'] = transition
        result.append(goal)
    return result


def source_events(sources):
    ctor, dtor, count = MEMBERS
    rows = [
        ('ctor.zero.data', ctor, 'this->data = NULL;', ['ctor.rte.zero_data','ctor.fields.initialized']),
        ('ctor.zero.size', ctor, 'this->size = 0;', ['ctor.rte.zero_size','ctor.fields.initialized']),
        ('ctor.zero.capacity', ctor, 'this->capacity = 0;', ['ctor.rte.zero_capacity','ctor.fields.initialized']),
        ('ctor.zero.return', ctor, 'if (n == 0) return;', ['ctor.zero.post','ctor.zero.frame']),
        ('ctor.allocated.data', ctor, 'this->data = swdb_alloc_int(n);',
         ['ctor.rte.allocated_data','ctor.alloc.identity','ctor.alloc.extent','ctor.alloc.uninitialized','ctor.alloc.separation','ctor.alloc.well_formed','ctor.frame.preexisting']),
        ('ctor.allocated.capacity', ctor, 'this->capacity = n;', ['ctor.rte.allocated_capacity','ctor.capacity.entry']),
        ('ctor.loop.init', ctor, 'size_t k = 0;', ['ctor.capacity.entry','ctor.prefix.establish','ctor.numeric']),
        ('ctor.loop.test', ctor, 'k < n;', ['ctor.store.access','ctor.prefix.exit','ctor.numeric']),
        ('ctor.fill', ctor, 'this->data[k] = value;', ['ctor.store.access','ctor.prefix.step','ctor.frame.loop_step']),
        ('ctor.loop.increment', ctor, '++k)', ['ctor.numeric','ctor.prefix.step']),
        ('ctor.final.size', ctor, 'this->size = n;', ['ctor.rte.final_size','ctor.final.post','ctor.frame.final']),
        ('dtor.load_and_release', dtor, 'swdb_free(this->data);',
         ['dtor.data.read','dtor.free.argument','dtor.null.no_op','dtor.alias.invalidated',
          'dtor.post.old_invalid','dtor.frame.surviving','dtor.frame.other_live','dtor.receiver.overlap']),
    ]
    rows += [(count_id(name), count, needle.replace('= value;', '= (int)0;'),
              [count_id(goal) for goal in goals])
             for name, member, needle, goals in rows if member == ctor]
    return [{'id': name, 'member': member, 'source_spans': [span(sources[member], needle)],
             'obligations': goals} for name, member, needle, goals in rows]


def payload(index, goal):
    name = 't25_' + goal['id'].replace('.', '_')
    if goal['kind'] == 'c_kernel':
        text = NUMERIC
        name = 't25_ctor_numeric'
    else:
        text = '//@ import \\wp::why3: heap_bridge::Heap;\n' + PRELUDE
        text += '/*@ check lemma ' + name + ': ' + goal['statement'] + ';\n*/\n'
    filename = f'{index:03d}-{name}.c'
    return name, filename, text


def declaration(sources, goals, theory):
    source_pins = {name: {'path': name + '.original.c', 'sha256': sha(text.encode())}
                   for name, text in sources.items()}
    return {
        'created': '2026-10-15 ET', 'preparation_only': True,
        'original_members': list(MEMBERS), 'sources': source_pins,
        'model': std_models.identity(), 'obligations': goals,
        'source_events': source_events(sources),
        'semantics': {'path': 'theory/heap_bridge.mlw', 'sha256': sha(theory)},
        'original_caller_premises_added': [], 'verifier_launched': False,
        'semantic_relations': {
            'premise_witnesses': 'concrete feasibility controls only; never restrictions on arbitrary incoming heaps',
            'incoming_heap': 'arbitrary well-formed heap, including issued dead identities and escaped aliases',
            'allocator_output': 'fresh identity, exact extent, available address, uninitialized cells, prior-object frame',
            'allocation_policy': 'existing allocation-success/freshness/frame trust; allocator address is an output, not a caller premise',
            'generic_caller_composition': 'unsupported',
            'typed_memory': 'int and receiver typed cells only; byte casts/partial writes require another checked translation',
            'typed_layout': 'int: size4 align4; receiver: size24 align8, fields0/8/16; original typed validity includes alignment',
        },
        'scope': 'Canonical original-source VC preparation; production proof requires fresh checked execution of all selected member targets.',
        'pending_source_inventory': [],
        'pending_validation': ['fresh execution of all selected original-source positive obligations',
                               'current standard-support and emitted task hypothesis checks'],
        'translation_components': {p.name: sha(p.read_bytes()) for p in (Path(__file__), HERE / 'heap_model_vcs.py')},
        'trusted_translation': 'Explicit source/event/VC mapping and uniform heap semantics under project trusted-lowerer TCB.',
    }


def prepare(output, source_directory=None):
    sources = original_sources(source_directory)
    output.mkdir(exist_ok=False, parents=True)
    (output / 'theory').mkdir()
    theory = HERE.joinpath('heap_bridge.mlw').read_bytes()
    (output / 'theory/heap_bridge.mlw').write_bytes(theory)
    source_pins = {}
    for member, source in sources.items():
        name = member + '.original.c'
        (output / name).write_text(source)
        source_pins[member] = {'path': name, 'sha256': sha(source.encode())}
    goals = obligations(sources)
    for index, goal in enumerate(goals):
        name, filename, text = payload(index, goal)
        (output / filename).write_text(text)
        goal.update(path=filename, sha256=sha(text.encode()), goal=name)
        if 'source_mutation' in goal:
            mutation = goal['source_mutation']
            source = sources[goal['member']]
            assert source.count(mutation['before']) == 1
            changed = source.replace(mutation['before'], mutation['after'])
            path = goal['id'] + '.mutant.c'
            (output / path).write_text(changed)
            goal['control_source'] = {'path': path, 'sha256': sha(changed.encode())}
    manifest = declaration(sources, goals, theory)
    (output / 'manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
    return manifest


def check(directory):
    manifest = json.loads((directory / 'manifest.json').read_text())
    sources = original_sources()
    if manifest.get('original_members') != list(MEMBERS) or manifest.get('model') != std_models.identity():
        raise ValueError('original source/model inventory changed')
    for member, source in sources.items():
        pin = {'path': member + '.original.c', 'sha256': sha(source.encode())}
        if manifest.get('sources', {}).get(member) != pin or (directory / pin['path']).read_text() != source:
            raise ValueError('original source inventory changed: ' + member)
    theory = (directory / 'theory/heap_bridge.mlw').read_bytes()
    if theory != HERE.joinpath('heap_bridge.mlw').read_bytes():
        raise ValueError('semantic import inventory changed')
    if manifest.get('semantics') != {'path': 'theory/heap_bridge.mlw', 'sha256': sha(theory)}:
        raise ValueError('semantic import pin changed')
    components = {p.name: sha(p.read_bytes()) for p in (Path(__file__), HERE / 'heap_model_vcs.py')}
    if manifest.get('translation_components') != components:
        raise ValueError('source/VC translator pin changed')
    expected = obligations(sources)
    if manifest.get('source_events') != source_events(sources):
        raise ValueError('source event/VC inventory changed')
    controls = set()
    for index, goal in enumerate(expected):
        name, filename, text = payload(index, goal)
        if (directory / filename).read_text() != text:
            raise ValueError('isolated target/hypothesis inventory changed: ' + name)
        goal.update(path=filename, sha256=sha(text.encode()), goal=name)
        if 'source_mutation' in goal:
            mutation = goal['source_mutation']
            changed = sources[goal['member']].replace(mutation['before'], mutation['after'])
            path = goal['id'] + '.mutant.c'
            if (directory / path).read_text() != changed:
                raise ValueError('source negative mutation inventory changed: ' + goal['id'])
            goal['control_source'] = {'path': path, 'sha256': sha(changed.encode())}
            controls.add(path)
    if manifest.get('obligations') != expected:
        raise ValueError('source obligation inventory changed')
    if manifest != declaration(sources, expected, theory):
        raise ValueError('packet declaration changed; preparation cannot become a proof claim')
    if manifest.get('original_caller_premises_added') != [] or manifest.get('verifier_launched') is not False:
        raise ValueError('unexpected caller premise or execution claim')
    allowed = {'manifest.json', 'theory/heap_bridge.mlw', *controls, *[p['path'] for p in manifest['sources'].values()],
               *[g['path'] for g in expected]}
    actual = {str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()}
    if actual != allowed:
        raise ValueError('unexpected packet/import inventory')
    return manifest

