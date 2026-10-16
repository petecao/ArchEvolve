"""Pending private lifetime frame duties; created 2026-10-16 ET.

These conditional mathematical goals retain release and automatic scope end.
They do not establish source ownership, allocator effects or Typed correspondence,
and are not integrated into caller admission or the current body packet counts.
"""
import hashlib
import json
from pathlib import Path


PRELUDE = r'''/*@ predicate t25_private_observes(Heap::heap entry, Heap::heap left,
                                     Heap::heap right) =
      (\forall integer b; Heap::live(entry,b) ==>
        Heap::same_object(left,right,b)) &&
      (\forall integer b,p; Heap::live(entry,b) ==>
        Heap::contents(left,b,p) == Heap::contents(right,b,p) &&
        (Heap::initialized_at(left,b,p) <==> Heap::initialized_at(right,b,p)));
    predicate t25_private_frame(Heap::heap entry, Heap::heap now) =
      t25_private_observes(entry,entry,now);
    predicate t25_private_ids(Heap::heap entry, integer r, integer b) =
      !Heap::live(entry,r) && (b == 0 || (!Heap::live(entry,b) && b != r));
    logic Heap::heap t25_private_cleanup(Heap::heap now, integer r, integer b) =
      Heap::end_automatic(Heap::release(now,b),r);
*/
'''


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def identity():
    here = Path(__file__).parent
    return {'id': 'vector-private-lifetime-frame-1',
            'sha256': _sha((here / 'vector_reallocation_private_frame.py').read_bytes()
                          + (here / 'heap_reallocation.mlw').read_bytes())}


def declaration():
    """Canonical unexecuted goals; no compiler, source premise or record import."""
    rows = [
        ('entry.reflexive',
         r'\forall Heap::heap h; t25_private_frame(h,h)'),
        ('automatic.frame',
         r'\forall Heap::heap h; \forall integer width,a; Heap::well_formed(h) ==> '
         r't25_private_frame(h,Heap::begin_automatic(h,width,a)) && '
         r'!Heap::live(h,Heap::fresh_id(h))'),
        ('allocation.frame',
         r'\forall Heap::heap entry,now; \forall integer n,a; '
         r'Heap::well_formed(now) && t25_private_frame(entry,now) ==> '
         r't25_private_frame(entry,Heap::allocate(now,n,a)) && '
         r'!Heap::live(entry,Heap::fresh_id(now))'),
        ('integer_store.frame',
         r'\forall Heap::heap entry,now; \forall integer b,o,v; '
         r't25_private_frame(entry,now) && !Heap::live(entry,b) ==> '
         r't25_private_frame(entry,Heap::put_integer(now,b,o,v))'),
        ('pointer_store.frame',
         r'\forall Heap::heap entry,now; \forall integer b,o,target,offset; '
         r't25_private_frame(entry,now) && !Heap::live(entry,b) ==> '
         r't25_private_frame(entry,Heap::put_pointer(now,b,o,target,offset))'),
        ('release.frame',
         r'\forall Heap::heap entry,now; \forall integer b; '
         r't25_private_frame(entry,now) && !Heap::live(entry,b) ==> '
         r't25_private_frame(entry,Heap::release(now,b))'),
        ('automatic_end.frame',
         r'\forall Heap::heap entry,now; \forall integer r; '
         r't25_private_frame(entry,now) && !Heap::live(entry,r) ==> '
         r't25_private_frame(entry,Heap::end_automatic(now,r))'),
        ('cleanup.observation',
         r'\forall Heap::heap entry,now; \forall integer r,b; '
         r't25_private_frame(entry,now) && t25_private_ids(entry,r,b) ==> '
         r't25_private_frame(entry,t25_private_cleanup(now,r,b)) && '
         r't25_private_observes(entry,now,t25_private_cleanup(now,r,b))'),
        ('cleanup.exists_scalar',
         r'\forall Heap::heap entry,now; \forall integer r,b,n; '
         r't25_private_frame(entry,now) && t25_private_ids(entry,r,b) && '
         r'Heap::typed_writes(now,r,0,24,8) && !Heap::freeable(now,r,0) && 0 <= n && '
         r'(n == 0 ? b == 0 : Heap::freeable(now,b,0) && '
         r'Heap::int32_region(now,b,0,n) && Heap::filled_prefix(now,b,n,7)) ==> '
         r'\exists Heap::heap final; \exists integer scalar; '
         r'final == t25_private_cleanup(now,r,b) && '
         r'scalar == (n > 0 ? Heap::load_int(now,b,0) : 0) && '
         r'scalar == (n > 0 ? 7 : 0) && t25_private_frame(entry,final) && '
         r't25_private_observes(entry,now,final)'),
    ]
    files = {'prelude.acsl': PRELUDE.encode(),
             'theory/heap_reallocation.mlw': Path(__file__).with_name('heap_reallocation.mlw').read_bytes()}
    obligations = []
    for index, (name, statement) in enumerate(rows):
        goal = 't25_private_' + name.replace('.', '_')
        data = ('//@ import \\wp::why3: heap_reallocation::Heap;\n' + PRELUDE
                + '/*@ check lemma ' + goal + ': ' + statement + ';\n*/\n').encode()
        path = f'obligations/{index:03d}-{goal}.c'
        files[path] = data
        obligations.append({'id': name, 'goal': goal, 'path': path, 'kind': 'check_lemma',
                            'status': 'pending', 'statement': statement,
                            'dependencies': [], 'sha256': _sha(data)})
    plan = {
        'created': '2026-10-16 ET', 'version': 1, 'checker': identity(),
        'proof_admission': 'unsupported: conditional private-frame duties require fresh proofs and an actual source/Typed bridge',
        'preparation_only': True, 'source_typed_bridge_established': False,
        'caller_premises_added': [], 'current_proof_records_admitted': [],
        'obligations': obligations,
        'semantics': {'path': 'theory/heap_reallocation.mlw',
                      'sha256': _sha(files['theory/heap_reallocation.mlw'])},
        'observation': 'complete identity, contents and initialization of every incoming live object',
        'hidden': ['fresh private object identities and their dead contents',
                   'private allocation history and next identity counter'],
        'cleanup': 'end_automatic(release(now,buffer),receiver); scalar captured from now before cleanup',
        'source_requirements_pending': [
            'exact original contract, source AST, lowering and scalar-before-destructor order',
            'default allocator and original standard substitution provenance; no custom allocator or source replacement hooks',
            'explicit existing allocator/library TCB including internal effects; this frame relation erases none of them by itself',
            'actual source-created fresh automatic receiver and backing allocation identities',
            'no private pointer or global escape and no pointer/lifetime observation after cleanup',
            'actual Typed+Var allocation, value/init chunk and cleanup correspondence',
            'completed constructor/fill/reserve/observation/destructor dependencies and local branch states',
            'complete fresh ordinary/RTE/init/frame/smoke results and task/import/hypothesis audit',
        ],
    }
    files['manifest.json'] = _json(plan)
    return plan, files


def prepare(directory):
    plan, files = declaration()
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    for name, data in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return plan


def check(directory):
    plan, files = declaration()
    directory = Path(directory)
    paths = list(directory.rglob('*'))
    if directory.is_symlink() or any(path.is_symlink() or not (path.is_file() or path.is_dir())
                                     for path in paths):
        raise ValueError('private-frame packet contains a redirected or special path')
    expected_dirs = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
    if {str(path.relative_to(directory)) for path in paths if path.is_file()} != set(files) or \
            {str(path.relative_to(directory)) for path in paths if path.is_dir()} != expected_dirs:
        raise ValueError('private-frame packet membership differs')
    for name, data in files.items():
        if (directory / name).read_bytes() != data:
            raise ValueError('canonical private-frame transition/observation differs: ' + name)
    return plan
