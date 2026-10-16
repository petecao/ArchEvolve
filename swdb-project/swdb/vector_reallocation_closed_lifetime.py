"""Source-bound constructor/private-cleanup gluing duties; created 2026-10-16 ET.

These independent mathematical duties connect current constructor body outputs
to the incoming-live observer and real release/scope-end transition. They do
not create a Typed/source correspondence or admit a constructor/caller proof.
"""
import hashlib
import json
from pathlib import Path

from swdb import vector_reallocation_closed_view as closed
from swdb import vector_reallocation_model as model
from swdb import vector_reallocation_private_frame as private
from swdb import vector_reallocation_vcs as constructor
from swdb import std_models


class Refused(ValueError):
    pass


CTOR = 'std_vector_int_realloc_v3_ctor_count_value'
DTOR = 'std_vector_int_realloc_v3_dtor'
POSITIVE = 't25_closed_positive(loop,r,n)'
PREMISE = (
    r'Heap::well_formed(before) && 0 < n <= 2147483647 && t25_private_frame(entry,before) && '
    r'!Heap::live(entry,r) && Heap::typed_writes(before,r,0,24,8) && '
    r'!Heap::freeable(before,r,0) && b == Heap::fresh_id(before) && '
    r't25_frame(before,loop,r,0) && t25v3_ctor_inv(loop,r,0,b,n,n,7)')


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()


def identity():
    here = Path(__file__).parent
    names = ['vector_reallocation_closed_lifetime.py', 'vector_reallocation_closed_view.py',
             'vector_reallocation_composition.py', 'vector_reallocation_vcs.py',
             'vector_reallocation_model.py', 'vector_reallocation_private_frame.py',
             'heap_model_vcs.py', 'heap_reallocation.mlw']
    return {'id': 'vector-closed-lifetime-glue-1',
            'sha256': _sha(_json([{'path': name, 'sha256': _sha((here/name).read_bytes())}
                                  for name in names]))}


def declaration(lowering, source, formal_texts):
    view = closed.prepare(lowering, source, formal_texts)
    qualification = model.certificate(CTOR)
    ctor, _ = constructor.declaration(CTOR)
    dtor, _ = constructor.declaration(DTOR)
    destructor = model.certificate(DTOR)
    frame, _ = private.declaration()
    if len(ctor['obligations']) != 35 or len(dtor['obligations']) != 11 or len(frame['obligations']) != 9 or \
            qualification['original_source_sha256'] != view.certificate['constructor']['model_sha256'] or \
            qualification['inverse_qualified_source_sha256'] != qualification['original_source_sha256'] or \
            destructor['original_source_sha256'] != view.certificate['terminal_cleanup']['model_sha256'] or \
            destructor['inverse_qualified_source_sha256'] != destructor['original_source_sha256'] or \
            view.certificate['cfg']['fallback_reachable'] is not False:
        raise Refused('the exact constructor/body inverse or closed cleanup predecessors changed')
    events = {row['event']: row for row in lowering.vector_reallocation_candidate['lowered_lifetime']['events']}
    prelude = (constructor.PRELUDE + private.PRELUDE + r'''
/*@ logic Heap::heap t25_closed_positive(Heap::heap loop, integer r, integer n) =
      Heap::put_integer(loop,r,8,n);
*/
''')
    begin = 'Heap::begin_automatic(entry,24,a)'
    receiver = 'Heap::fresh_id(entry)'
    rows = [
        ('receiver.entry', ['automatic declaration'],
         r'\forall Heap::heap entry; \forall integer a; Heap::well_formed(entry) && '
         r'Heap::automatic_available(entry,24,8,a) ==> '
         'Heap::well_formed('+begin+') && t25_private_frame(entry,'+begin+') && !Heap::live(entry,'+receiver+') && '
         'Heap::typed_writes('+begin+','+receiver+',0,24,8) && '
         '!Heap::freeable('+begin+','+receiver+',0)',
         'source automatic storage and arbitrary incoming heap are interpreted by the existing fresh stack-allocation primitive; no caller requires clause'),
        ('constructor.frame', ['constructor'],
         r'\forall Heap::heap entry,before,after; \forall integer r; '
         r't25_private_frame(entry,before) && !Heap::live(entry,r) && '
         r't25_frame(before,after,r,0) ==> t25_private_frame(entry,after)',
         'receiver.entry plus the current complete constructor zero/positive/loop/final frame proof; frame is never an opaque caller premise'),
        ('buffer.identity', ['automatic declaration', 'constructor'],
         r'\forall Heap::heap entry; \forall integer a; Heap::well_formed(entry) && '
         r'Heap::automatic_available(entry,24,8,a) ==> '
         'Heap::fresh_id('+begin+') == Heap::fresh_id(entry)+1 && '
         '!Heap::issued(entry,'+receiver+') && '
         '!Heap::issued(entry,Heap::fresh_id('+begin+')) && '
         '!Heap::live(entry,Heap::fresh_id('+begin+')) && '
         'Heap::fresh_id('+begin+') != '+receiver+' && '
         'Heap::fresh_id(t25_initial('+begin+','+receiver+',0)) == Heap::fresh_id('+begin+')',
         'canonical before=begin_automatic(entry,24,a), receiver=fresh_id(entry); actual initial stores preserve next; the allocator uses that source-fresh identity under its explicit freshness/freeability/frame TCB'),
        ('zero.cleanup', ['constructor', 'guarded scalar capture', 'destructor', 'automatic lifetime end'],
         r'\forall Heap::heap entry,before; \forall integer r; '
         r't25_private_frame(entry,before) && !Heap::live(entry,r) && '
         r'Heap::typed_writes(before,r,0,24,8) && !Heap::freeable(before,r,0) ==> '
         r'\exists Heap::heap final; final == '
         r'Heap::end_automatic(Heap::release(t25_initial(before,r,0),0),r) && '
         r't25_private_frame(entry,final) && !Heap::forms(final,r,0)',
         'actual constructor initial stores and n==0 branch; scalar capture is literal zero, no buffer load, release(null) and scope end remain explicit'),
        ('positive.exit_image', ['constructor', 'data capture', 'reserve', 'guarded scalar capture'],
         r'\forall Heap::heap entry,before,loop; \forall integer r,b,n; '+PREMISE+' ==> '
         't25_private_frame(entry,'+POSITIVE+') && t25_private_ids(entry,r,b) && '
         'Heap::typed_writes('+POSITIVE+',r,0,24,8) && !Heap::freeable('+POSITIVE+',r,0) && '
         'Heap::freeable('+POSITIVE+',b,0) && Heap::int32_region('+POSITIVE+',b,0,n) && '
         'Heap::filled_prefix('+POSITIVE+',b,n,7)',
         'complete current constructor35 loop exit and frame; source constant7/signed count and actual fresh allocation identity; no strengthened callee summary is imported without that body proof'),
        ('positive.cleanup', ['constructor', 'guarded scalar capture', 'destructor', 'return scalar', 'automatic lifetime end'],
         r'\forall Heap::heap entry,before,loop; \forall integer r,b,n; '+PREMISE+' ==> '
         r'\exists Heap::heap final; \exists integer scalar; '
         'final == Heap::end_automatic(Heap::release('+POSITIVE+',b),r) && '
         'scalar == (n > 0 ? Heap::load_int('+POSITIVE+',b,0) : 0) && '
         'scalar == (n > 0 ? 7 : 0) && t25_private_frame(entry,final) && '
         't25_private_observes(entry,'+POSITIVE+',final) && '
         '!Heap::forms(final,r,0) && !Heap::forms(final,b,0)',
         'same full source constructor antecedent as exit_image; no sibling conclusion is assumed. Capture precedes the original terminal free and scope end; actual constructor/body/source dependencies and all9 private-frame duties remain mandatory'),
    ]
    original = std_models.model_text(model.MEMBERS[CTOR])
    files = {'prelude.acsl': prelude.encode(),
             'theory/heap_reallocation.mlw': Path(__file__).with_name('heap_reallocation.mlw').read_bytes(),
             'sources/original-constructor.c': original.encode(),
             'sources/qualified-constructor.c': model.model_text(CTOR).encode(),
             'sources/original-destructor.c': std_models.model_text(model.MEMBERS[DTOR]).encode(),
             'sources/qualified-destructor.c': model.model_text(DTOR).encode(),
             'sources/original-caller.c': lowering.text.encode(),
             'sources/projected-caller.c': view.text.encode(),
             'sources/original.cc': Path(source).read_bytes()}
    obligations = []
    for index, (name, event_names, statement, discharge) in enumerate(rows):
        goal = 't25_closed_'+name.replace('.', '_')
        raw = ('//@ import \\wp::why3: heap_reallocation::Heap;\n'+prelude+
               '/*@ check lemma '+goal+': '+statement+';\n*/\n').encode()
        path = f'obligations/{index:03d}-{goal}.c'
        files[path] = raw
        obligations.append({'id': name, 'goal': goal, 'path': path, 'kind': 'check_lemma',
                            'statement': statement, 'status': 'pending', 'dependencies': [],
                            'source_events': [events[event] for event in event_names],
                            'local_antecedent_discharge': discharge, 'sha256': _sha(raw)})
    plan = {'created': '2026-10-16 ET', 'version': 1, 'checker': identity(),
            'source_view': view.certificate, 'original_contract': list(formal_texts),
            'caller_premises_added': [], 'current_proof_records_admitted': [],
            'source_typed_bridge_established': False, 'preparation_only': True,
            'proof_admission': 'unsupported: fresh complete constructor/gluing/private-frame proofs, allocator/source/Typed correspondence and original ordinary diagnostic remain required',
            'constructor_dependency': {'member': CTOR, **qualification,
                'required_targets': [{'id': row['id'], 'sha256': row['sha256']} for row in ctor['obligations']],
                'current_body_record_admitted': False},
            'private_frame_dependency': {'checker': frame['checker'],
                'required_targets': [{'id': row['id'], 'sha256': row['sha256']} for row in frame['obligations']],
                'current_proof_record_admitted': False},
            'destructor_dependency': {'member': DTOR, **destructor,
                'required_targets': [{'id': row['id'], 'sha256': row['sha256']} for row in dtor['obligations']],
                'current_body_record_admitted': False},
            'obligations': obligations,
            'source_files': [{'path': name, 'sha256': _sha(raw)} for name, raw in files.items() if name.startswith('sources/')],
            'semantics': {'path': 'theory/heap_reallocation.mlw',
                          'sha256': _sha(files['theory/heap_reallocation.mlw'])},
            'semantic_interpretation': 'alternate checked closed source-to-VC interpretation under the existing allocator/library/translation TCB; not a native Typed proof of fresh/freeable/dangling',
            'explicit_allocator_library_TCB': {
                'allocation': 'normal allocation succeeds with a fresh, valid, freeable result and preserves incoming caller memory, as specified by the pinned allocator model',
                'release': 'null release is inert; valid dynamic release ends only the specified allocation and preserves all other incoming memory, as specified by the pinned deallocator model',
                'library': 'the pinned standard-library members correspond to their complete pinned model contracts and executable bodies',
                'environment': 'full-TU screening and default allocator spelling do not establish absence of separately linked global allocation replacements or interposition; their effects are covered only by the explicit model TCB',
                'future_record_policy': 'any admitted source-facing method/record must name and pin allocator freshness, validity, framing and release correspondence explicitly; allocation success alone is insufficient',
            },
            'private_observation': frame['observation'],
            'canonical_source_prefix': {'before': 'Heap.begin_automatic(entry,24,a)',
                'receiver': 'Heap.fresh_id(entry)', 'positive_buffer': 'Heap.fresh_id(before)',
                'initial_stores': 't25_initial(before,receiver,0); preserves the next identity',
                'history_role': 'buffer.identity separately proves not-issued history for this exact prefix; the generic private observer/positive gluing premises alone do not establish source history'},
            'source_requirements_pending': [
                'source-created automatic/allocation interpretation, successful allocator TCB and current constructor proof dependency',
                'source and Typed scalar/field/value/init correspondence at the projected-C observation boundary',
                'complete independent gluing task/hypothesis proof and dependency-source closure',
                'complete original ordinary/RTE/init/frame/smoke diagnostic and source observer composition',
            ]}
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
        raise Refused('closed lifetime canonical source/target membership differs')
    for name, raw in files.items():
        if (directory/name).read_bytes() != raw:
            raise Refused('closed lifetime source/frame/transition/dependency differs: '+name)
    return plan


def check_launch(lowering, source, formal_texts, directory):
    check(lowering, source, formal_texts, directory)
    raise Refused('actual source/Typed bridge and current complete constructor/gluing/private-frame/ordinary dependencies remain pending')
