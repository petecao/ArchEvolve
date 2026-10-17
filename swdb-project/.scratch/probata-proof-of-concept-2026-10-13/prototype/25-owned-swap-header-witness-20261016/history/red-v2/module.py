"""2026-10-16 ET. Stronger explicit witnesses for the pending swap header duty.

Original complete premises and overlapping self-swap guards remain intact.
Only conclusion existential introduction changes; no scientific/source admission.
"""
import hashlib
import json
from pathlib import Path

from swdb import vector_owned_swap_header_cases as previous


WITNESSES = (('left', 'nr', 'cr'), ('right', 'nl', 'cl'),
             ('other', 'OwnedEffects::size(h,observed)', 'OwnedEffects::capacity(h,observed)'))
HEADER = ('OwnedEffects::header(OwnedEffects::swap(h,l,r,a),observed,'
          'Owners::buffer(Owners::swap(owners,l,r),observed),')
EXISTENTIAL = r'(\exists integer size,capacity; '+HEADER+'size,capacity))'


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()


def identity():
    return {'id': 'vector-owned-swap-header-witness-1',
            'sha256': _sha(_json({'source': _sha(Path(__file__).read_bytes()),
                                  'previous': previous.identity()}))}


def declaration(*, elements=('int',)):
    old, previous_files = previous.declaration(elements=elements)
    if old['original_statement'] != previous.HEADER_STATEMENT or len(old['obligations']) != 3:
        raise ValueError('the exact original header and three complete cases are required')
    files = {name: raw for name, raw in previous_files.items()
             if not name.startswith('obligations/') and name != 'manifest.json'}
    obligations = []
    for original, (case, size, capacity) in zip(old['obligations'], WITNESSES, strict=True):
        if original['case'] != case or original['statement'].count(EXISTENTIAL) != 1:
            raise ValueError('exact original inner existential or owner case changed')
        explicit = HEADER+size+','+capacity+')'
        statement = original['statement'].replace(EXISTENTIAL, explicit)
        goal = 't25_owned_swap_header_witness_'+case
        path = f'obligations/{len(obligations):03d}-{goal}.c'
        reference = 'reference-cases/'+original['path']
        files[reference] = previous_files[original['path']]
        imports = previous_files[original['path']].decode().split('/*@ check lemma ', 1)[0]
        raw = (imports+'/*@ check lemma '+goal+': '+statement+';\n*/\n').encode()
        files[path] = raw
        obligations.append({**original, 'id': original['id']+'.witness', 'goal': goal,
            'path': path, 'statement': statement, 'explicit_header': explicit,
            'witness': {'size': size, 'capacity': capacity}, 'sha256': _sha(raw),
            'existential_reference': {'path': reference, 'sha256': original['sha256'],
                'statement': original['statement'], 'role': 'unproved original case; never a theorem premise'}})
    plan = {**old, 'checker': identity(), 'previous_checker': old['checker'],
        'obligations': obligations,
        'reconstruction': {'direction': 'three stronger cases imply the unchanged original universal by existential introduction and exhaustive original guards',
            'previous_partition': old['reconstruction'], 'added_premises': [], 'axioms_added': [],
            'self_swap_excluded': False, 'reverse_implication_claimed': False},
        'source_admission': 'unsupported: all three stronger proofs, complete cold interpretation and source/lifetime correspondence remain required'}
    files['manifest.json'] = _json(plan)
    return plan, files


def prepare(directory, *, elements=('int',)):
    plan, files = declaration(elements=elements)
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    for name, raw in files.items():
        path = directory/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return plan


def check(directory, *, elements=('int',)):
    plan, files = declaration(elements=elements)
    directory = Path(directory)
    paths = list(directory.rglob('*'))
    parents = {str(parent) for name in files for parent in Path(name).parents if str(parent) != '.'}
    if not directory.is_dir() or directory.is_symlink() or \
            any(path.is_symlink() or not (path.is_file() or path.is_dir()) for path in paths) or \
            {str(path.relative_to(directory)) for path in paths if path.is_file()} != set(files) or \
            {str(path.relative_to(directory)) for path in paths if path.is_dir()} != parents:
        raise ValueError('constructive header witness canonical membership differs')
    for name, raw in files.items():
        if (directory/name).read_bytes() != raw:
            raise ValueError('constructive header witness, complete source or reference differs: '+name)
    return plan
