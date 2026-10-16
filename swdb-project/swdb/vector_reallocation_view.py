"""Qualified standalone int reallocation proof view; created 2026-10-16 ET.

The original v2 contract is never its subject. Generic caller admission remains
closed; typed source-image qualification and the selected runtime are explicit.
"""
import hashlib
from pathlib import Path

from swdb import heap_model_view as engine
from swdb import vector_reallocation_model as model
from swdb import vector_reallocation_vcs as packets

MEMBERS=tuple(model.MEMBERS)
HERE=Path(__file__).parent


def identity():
    names=('vector_reallocation_view.py','vector_reallocation_model.py',
           'vector_reallocation_vcs.py','vector_reallocation_inventory.py',
           'heap_reallocation.mlw','heap_model_vcs.py','heap_model_view.py')
    return {'id':'qualified-vector-heap-view-1','sha256':engine._digest([
        {'path':name,'sha256':engine._sha((HERE/name).read_bytes())} for name in names])}


def view(member,manifest):
    qualification=model.certificate(member)
    groups={g for row in manifest['obligations'] for g in row['source_groups']}
    if member.endswith('_ctor_count_value'):
        required={f'C{i}' for i in range(1,10)}|{'QC1','QC2','D7'}
    elif member.endswith('_dtor'):required={f'D{i}' for i in range(1,8)}
    else:required={f'G{i}' for i in range(1,10)}|({'R1','R2','R3'} if member.endswith('_reserve') else set())
    rows=manifest['obligations'];ids={r['id'] for r in rows}
    inventory=manifest['source_inventory']
    if groups!=required or not rows or len(ids)!=len(rows) or any(
            row['expected']!='proven' or row['dependencies'] for row in rows):
        raise engine.Refused('the qualified source/target coverage or isolated hypothesis inventory changed')
    if not inventory['events'] or any(not e['obligations'] or not set(e['obligations'])<=ids
                                     for e in inventory['events']):
        raise engine.Refused('a qualified executable event has no target owner')
    cert={'version':1,'member':member,'original_source':manifest['sources']['qualified.c'],
          'parent_source':manifest['sources']['original.c'],'model':model.identity(),
          'qualification':qualification,'source_events':inventory['events'],
          'source_inventory':inventory,'source_groups':sorted(groups),
          'required_source_groups':sorted(required),'obligations':rows,
          'logical_obligations':manifest['logical_obligations'],
          'semantics':manifest['semantics'],'translation_components':manifest['translation_components'],
          'original_caller_premises_added':[],'generic_caller_composition':'unsupported',
          'has_allocation':not member.endswith('_dtor'),
          'standalone_scope':('broad pointer/free domain; no buffer element load or int image restriction'
                              if member.endswith('_dtor') else
                              'explicit qualified v3 typed-source-image domain; never the original raw contract'),
          'proof_rule':'all current source targets require fresh normal-reader ordinary/smoke proof',
          'pending':['actual WP import/task closure and all target proofs','source-derived caller discharge/composition']}
    return engine.View(member,cert,{'vector_reallocation_model':model.identity(),
        'heap_model_view_check':identity(),'heap_model_view_certificate':{
            'id':'qualified-vector-heap-certificate-1','sha256':engine._digest(cert)}})


def prepare(member,directory):
    try:return view(member,packets.prepare(member,directory))
    except (ValueError,KeyError) as exc:raise engine.Refused(str(exc)) from None


def check(member,old,directory):
    try:fresh=view(member,packets.check(member,directory))
    except (ValueError,KeyError) as exc:raise engine.Refused(str(exc)) from None
    if fresh!=old:raise engine.Refused('qualified heap source/view/checker changed before launch')
    return fresh


def typed_runtime(foundation,flags):
    """Pin the selected packages, not an unrelated local WP installation."""
    core=Path(foundation['ocaml_package_paths']['wp_core'])
    values=[]
    for i,flag in enumerate(flags):
        if flag=='-wp-model':values.append(flags[i+1] if i+1<len(flags) else None)
        elif flag.startswith('-wp-model='):values.append(flag.split('=',1)[1])
    # proof_setup independently enforces the same only-+real policy at launch.
    # Pinned Factory defaults are Typed/Fits and Cint.Machine; +real only changes floats.
    if not values or any(v!='+real' for v in values):
        raise engine.Refused('the qualified int image requires the pinned Typed/Machine model')
    pins=[]
    for want in model.TYPE_IMAGE['required_source_files']:
        path=core/want['name']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=want['sha256']:
            raise engine.Refused('the selected typed-int source semantics changed: '+want['name'])
        pins.append({'path':str(path.resolve()),'sha256':want['sha256']})
    return {'heap_model':'Typed','integer_model':'Machine','sources':pins,
            'source_image_role':'explicit qualified typed-int domain; caller construction discharge remains required',
            'raw_effective_type_safety_proved':False}
