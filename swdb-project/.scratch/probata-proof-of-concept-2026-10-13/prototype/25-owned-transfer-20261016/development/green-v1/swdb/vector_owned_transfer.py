"""2026-10-16 ET. Original move/swap source and a versioned ownership protocol.

This component proves no source contract by construction. It binds the unchanged
original member bodies to pending unbounded registry obligations. Source-created
registration, complete owners, field safety and physical lifetime/effect rules
must be checked before a public member or caller can consume those obligations.
"""
import ast
import hashlib
import json
from pathlib import Path
import re

from swdb import std_models

PARENT = {'id': 'swdb-std-models-2',
          'sha256': 'cf708cf2debd8abc525bd97c8fd30c6117ebff98dddd24978f97d34cbf2ad9c2'}
PRELUDE = r'''/* Ownership state records source-established registrations, not all pointers.
   Every goal keeps its complete original antecedent and has no sibling premise.
   This registry alone supplies no source field, allocation or freeability fact. */
'''


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def identity():
    here = Path(__file__).parent
    return {'id': 'vector-owned-transfer-1',
            'sha256': _sha((here/'vector_owned_transfer.py').read_bytes()
                           + (here/'vector_owned_state.mlw').read_bytes()+PARENT['sha256'].encode())}


def _elements(elements):
    if not isinstance(elements, tuple) or not elements or len(set(elements)) != len(elements):
        raise ValueError('a nonempty tuple of distinct canonical modeled scalar types is required')
    # Read only literal declarations. Importing the lowering/compiler stack is
    # unnecessary for the public pure preparation seam.
    source = Path(__file__).with_name('c_lowering.py').read_bytes()
    names = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in {'INTEGER_TYPES', 'FLOAT_TYPES', 'INTERNAL_TYPES'}:
            names[node.targets[0].id] = ast.literal_eval(node.value)
    if set(names) != {'INTEGER_TYPES', 'FLOAT_TYPES', 'INTERNAL_TYPES'}:
        raise ValueError('modeled scalar type registry declarations changed')
    scalars = (names['INTEGER_TYPES'] | names['FLOAT_TYPES'] | set(names['INTERNAL_TYPES'].values()))-{'bool'}
    accepted = scalars | {scalar+' *' for scalar in scalars}
    if any(not isinstance(element, str) or element not in accepted for element in elements):
        raise ValueError('only canonical modeled scalar/pointer element types, excluding bool, are supported')
    return elements


def _source(element, member):
    vector = 'std_vector_'+std_models._mangle(element)
    function = vector+'_'+member
    fragments = std_models.vector_member(vector, element, member)
    if len(fragments) != 1 or fragments[0][0] != function:
        raise ValueError('original transfer member has unexpected helper/effect structure')
    piece = fragments[0][1]
    expected = ('{\n  *this = *other;\n  other->data = NULL; other->size = 0; other->capacity = 0;\n}'
                if member == 'move_ctor' else '{ '+vector+' t = *this; *this = *other; *other = t; }')
    signature = f'static void {function}({vector} *this, {vector} *other) '
    if piece.count(signature) != 1 or piece.split(signature, 1)[1] != expected:
        raise ValueError('complete original struct assignment/reset body differs from the checked source rule')
    source = std_models._vector_types(vector, element)+'\n'+piece
    entry = {'member': member, 'function': function, 'element': element,
             'path': 'source/'+function+'.c', 'sha256': _sha(source.encode()),
             'original_fragment_sha256': _sha(piece.encode()), 'original_body': expected,
             'original_body_sha256': _sha(expected.encode()), 'body_changed': False,
             'old_contract_proved': False, 'element_memory_accessed': False,
             'source_read_effects': ['source/destination vector struct values; no buffer element load'],
             'source_write_effects': ['destination receiver fields', 'source receiver fields'],
             'source_relation_requires': (['distinct source/destination receiver identities',
                 'source established active owners', 'fresh empty destination ownership binding']
                 if member == 'move_ctor' else ['source established active owners']),
             'self_swap_registry_identity': member == 'swap',
             'physical_padding_observation': 'not established by the registry; full source layout/effect rule required'}
    return entry, source.encode()


def declaration(*, elements=('int',)):
    elements = _elements(elements)
    if std_models.identity() != PARENT:
        raise ValueError('original version2 source requires a new independent transfer audit after any model change')
    rows = [
        ('empty.valid', r'\forall integer frontier; 0 < frontier ==> Owners::valid(Owners::empty(0),frontier)'),
        ('receiver.fresh', r'\forall Owners::state s; \forall integer frontier; Owners::valid(s,frontier) ==> '
         r'Owners::valid(Owners::begin_owner(s,frontier),frontier+1) && '
         r'Owners::begin_owner(s,frontier).active[frontier] && '
         r'Owners::begin_owner(s,frontier).backing[frontier] == 0'),
        ('buffer.fresh', r'\forall Owners::state s; \forall integer frontier,r; '
         r'Owners::valid(s,frontier) && s.active[r] && s.backing[r] == 0 ==> '
         r'Owners::valid(Owners::bind(s,r,frontier),frontier+1) && '
         r'Owners::bind(s,r,frontier).backing[r] == frontier'),
        ('move.transfer', r'\forall Owners::state s; \forall integer frontier,destination,source; '
         r'Owners::valid(s,frontier) && s.active[destination] && s.active[source] && '
         r'destination != source && s.backing[destination] == 0 ==> '
         r'Owners::valid(Owners::move(s,destination,source),frontier) && '
         r'Owners::move(s,destination,source).backing[destination] == s.backing[source] && '
         r'Owners::move(s,destination,source).backing[source] == 0'),
        ('move.frame', r'\forall Owners::state s; \forall integer destination,source,q; '
         r'q != destination && q != source ==> '
         r'Owners::move(s,destination,source).active[q] == s.active[q] && '
         r'Owners::move(s,destination,source).backing[q] == s.backing[q]'),
        ('swap.exchange', r'\forall Owners::state s; \forall integer frontier,left,right; '
         r'Owners::valid(s,frontier) && s.active[left] && s.active[right] ==> '
         r'Owners::valid(Owners::swap(s,left,right),frontier) && '
         r'Owners::swap(s,left,right).backing[left] == s.backing[right] && '
         r'Owners::swap(s,left,right).backing[right] == s.backing[left]'),
        ('swap.frame', r'\forall Owners::state s; \forall integer left,right,q; '
         r'q != left && q != right ==> Owners::swap(s,left,right).active[q] == s.active[q] && '
         r'Owners::swap(s,left,right).backing[q] == s.backing[q]'),
        ('swap.self', r'\forall Owners::state s; \forall integer r; Owners::swap(s,r,r) == s'),
        ('retire.frame', r'\forall Owners::state s; \forall integer frontier,r,q; '
         r'Owners::valid(s,frontier) && s.active[r] && q != r ==> '
         r'Owners::valid(Owners::retire(s,r),frontier) && !Owners::retire(s,r).active[r] && '
         r'Owners::retire(s,r).backing[r] == 0 && '
         r'Owners::retire(s,r).active[q] == s.active[q] && '
         r'Owners::retire(s,r).backing[q] == s.backing[q] && '
         r'(s.active[q] && s.backing[r] != 0 ==> s.backing[q] != s.backing[r] && q != s.backing[r])'),
        ('shared_backing.rejected', r'\forall Owners::state s; \forall integer r,q; '
         r's.active[r] && s.active[q] && r != q && s.backing[r] != 0 && '
         r's.backing[r] == s.backing[q] ==> !Owners::exclusive(s)'),
    ]
    files = {'prelude.acsl': PRELUDE.encode(),
             'theory/vector_owned_state.mlw': Path(__file__).with_name('vector_owned_state.mlw').read_bytes()}
    obligations = []
    for index, (name, statement) in enumerate(rows):
        goal = 't25_owned_'+name.replace('.', '_')
        data = ('//@ import \\wp::why3: vector_owned_state::Owners;\n'+PRELUDE+
                '/*@ check lemma '+goal+': '+statement+';\n*/\n').encode()
        path = f'obligations/{index:03d}-{goal}.c';files[path] = data
        obligations.append({'id': name, 'goal': goal, 'path': path, 'kind': 'check_lemma',
            'status': 'pending', 'statement': statement, 'dependencies': [], 'sha256': _sha(data)})
    members = []
    for element in elements:
        for member in ('move_ctor', 'swap'):
            entry, source = _source(element, member);files[entry['path']] = source;members.append(entry)
    plan = {'created': '2026-10-16 ET', 'version': 1, 'checker': identity(), 'parent_model': dict(PARENT),
        'elements': list(elements), 'source_members': members, 'obligations': obligations,
        'source_admission': 'unsupported: ownership protocol requires fresh mathematical proofs and a complete checked source/Heap transition rule',
        'current_model_records_admitted': [], 'caller_premises_added': [], 'source_typed_bridge_established': False,
        'domain': {'id': 'source-owned-vector-registry-1', 'exclusive_backing': True,
            'raw_aliases_are_owners': False, 'identities': 'unbounded mathematical allocation identities; zero is no backing',
            'frontier': 'arbitrary positive integer; active receivers/backings predate fresh allocation identities',
            'physical_heap_relation_established': False,
            'cross_owner_receiver_backing_overlap': 'forbidden in the source-established ownership relation'},
        'theory': {'path': 'theory/vector_owned_state.mlw', 'sha256': _sha(files['theory/vector_owned_state.mlw'])},
        'pending_source_duties': ['fresh complete unbounded proof and full task/hypothesis/import closure',
            'source-derived ownership registration and complete existing owner set',
            'actual original field reads/writes, layout and initializedness',
            'source-to-registry move/swap update and fresh automatic temporary correspondence',
            'physical receiver/backing allocation identity, separation, validity, type and lifetime correspondence',
            'all original contracts/RTE/init/assigns and incoming live observation duties',
            'actual release and automatic lifetime end: retire is not Heap.release',
            'library/allocator correspondence including freshness, freeability, frame, release and permitted replacement effects'],
        'unsupported': ['generic incoming ownership from unary validity/freeability', 'shared backing owners',
            'overlapping receiver/backing identities', 'move construction into a nonfresh owned destination',
            'self move construction', 'source proof or default model adoption based on registry evidence alone'],
    }
    files['manifest.json'] = _json(plan)
    return plan, files


def prepare(directory, *, elements=('int',)):
    plan, files = declaration(elements=elements)
    directory = Path(directory);directory.mkdir(exist_ok=False)
    for name, data in files.items():
        path = directory/name;path.parent.mkdir(parents=True, exist_ok=True);path.write_bytes(data)
    return plan


def check(directory, *, elements=('int',)):
    plan, files = declaration(elements=elements)
    directory = Path(directory);paths = list(directory.rglob('*'))
    if directory.is_symlink() or any(path.is_symlink() or not (path.is_file() or path.is_dir()) for path in paths):
        raise ValueError('owned transfer packet has a redirected or special path')
    expected_dirs = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
    if {str(path.relative_to(directory)) for path in paths if path.is_file()} != set(files) or \
            {str(path.relative_to(directory)) for path in paths if path.is_dir()} != expected_dirs:
        raise ValueError('owned transfer packet membership differs')
    for name, data in files.items():
        if (directory/name).read_bytes() != data:
            raise ValueError('canonical original source/ownership transition differs: '+name)
    return plan


def check_launch(directory, *, elements=('int',)):
    check(directory, elements=elements)
    raise ValueError('ownership protocol has no admitted complete source transition or public member route')
