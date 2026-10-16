"""2026-10-16 ET. Pending original move/swap field and lifetime interpretation.

Public materialization binds complete unchanged original C, layout assertions,
source events and independent conditional header/registry duties. It establishes
no physical source/Heap bridge, source ownership or actual cleanup by itself.
"""
import hashlib
import json
from pathlib import Path

from swdb import vector_owned_transfer


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(value):
    return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def identity():
    here=Path(__file__).parent
    dependencies=[{'path':name,'sha256':_sha((here/name).read_bytes())} for name in
                  ('vector_owned_source_view.py','vector_owned_effects.mlw','heap_reallocation.mlw')]
    return {'id':'vector-owned-source-view-1',
            'sha256':_sha(_json({'dependencies':dependencies,'transfer':vector_owned_transfer.identity()}))}


def _layout(vector):
    return ('\n/* Target checks are pending execution; logical offsets do not assert a native C++ ABI. */\n'
            '_Static_assert(CHAR_BIT == 8 && sizeof(size_t) == 8 && _Alignof(size_t) == 8 &&\n'
            '               sizeof(void *) == 8 && _Alignof(void *) == 8 &&\n'
            f'               sizeof({vector}) == 24 && _Alignof({vector}) == 8 &&\n'
            f'               offsetof({vector}, data) == 0 && offsetof({vector}, size) == 8 &&\n'
            f'               offsetof({vector}, capacity) == 16, "owned header layout");\n').encode()


def _events(member):
    if member=='move_ctor':
        return [{'operation':'header_copy','destination':'this','source':'other','snapshot_before_destination_write':True}]+[
            {'operation':'zero_field','receiver':'other','field':field,'value':'NULL' if field=='data' else '0'}
            for field in ('data','size','capacity')]
    return [{'operation':'begin_automatic','receiver':'t','fresh_identity':'Heap.next','vector_owner':False},
            {'operation':'header_copy','destination':'t','source':'this','snapshot_before_destination_write':True},
            {'operation':'header_copy','destination':'this','source':'other','snapshot_before_destination_write':True},
            {'operation':'header_copy','destination':'other','source':'t','snapshot_before_destination_write':True},
            {'operation':'end_automatic','receiver':'t','primitive':'Heap.end_automatic','registry_retire_is_substitute':False}]


def _obligations():
    # Each member's leaves retain one complete source-world antecedent. No
    # successful sibling theorem is an opaque premise of another leaf.
    quantifiers=(r'\forall Heap::heap h; \forall Owners::state owners; '
                 r'\forall OwnedEffects::phases ready; ')
    move=(quantifiers+r'\forall integer d,s,b,n,c; '
          r'OwnedEffects::world(h,owners,ready) && OwnedEffects::reserved(h,owners,ready,d) && '
          r'Owners::active_owner(owners,s) && OwnedEffects::is_ready(ready,s) && d != s && '
          r'OwnedEffects::header(h,s,b,n,c) ==> ')
    swap=(quantifiers+r'\forall integer l,r,a,bl,nl,cl,br,nr,cr; '
          r'OwnedEffects::world(h,owners,ready) && Owners::active_owner(owners,l) && '
          r'Owners::active_owner(owners,r) && OwnedEffects::is_ready(ready,l) && '
          r'OwnedEffects::is_ready(ready,r) && OwnedEffects::header(h,l,bl,nl,cl) && '
          r'OwnedEffects::header(h,r,br,nr,cr) && Heap::automatic_available(h,24,8,a) ==> ')
    return [
        ('move.destination_header',move+r'OwnedEffects::header(OwnedEffects::move(h,d,s),d,b,n,c)'),
        ('move.source_empty',move+r'OwnedEffects::header(OwnedEffects::move(h,d,s),s,0,0,0)'),
        ('move.incoming_frame',move+r'OwnedEffects::incoming_frame(h,OwnedEffects::move(h,d,s),d,s)'),
        ('move.owner_correspondence',move+r'OwnedEffects::world(OwnedEffects::move(h,d,s),'
         r'Owners::move(owners,d,s),OwnedEffects::moved_phases(ready,d,s))'),
        ('swap.left_header',swap+r'OwnedEffects::header(OwnedEffects::swap(h,l,r,a),l,br,nr,cr)'),
        ('swap.right_header',swap+r'OwnedEffects::header(OwnedEffects::swap(h,l,r,a),r,bl,nl,cl)'),
        ('swap.temporary_lifetime',swap+r'!Heap::live(OwnedEffects::swap(h,l,r,a),Heap::fresh_id(h)) && '
         r'Heap::issued(OwnedEffects::swap(h,l,r,a),Heap::fresh_id(h))'),
        ('swap.incoming_frame',swap+r'OwnedEffects::incoming_frame(h,OwnedEffects::swap(h,l,r,a),l,r)'),
        ('swap.owner_correspondence',swap+r'OwnedEffects::world(OwnedEffects::swap(h,l,r,a),Owners::swap(owners,l,r),ready)'),
    ]


def declaration(*,elements=('int',)):
    transfer,base_files=vector_owned_transfer.declaration(elements=elements)
    here=Path(__file__).parent
    files={'theory/'+name:(here/name).read_bytes() for name in
           ('heap_reallocation.mlw','vector_owned_state.mlw','vector_owned_effects.mlw')}
    members=[]
    for source in transfer['source_members']:
        raw=base_files[source['path']]
        vector=source['function'].removesuffix('_'+source['member'])
        prefix=b'#include <stddef.h>\n#include <limits.h>\n'
        view=prefix+raw+b'\n'+_layout(vector)
        original_path='original/'+Path(source['path']).name
        view_path='views/'+Path(source['path']).name
        files[original_path]=raw;files[view_path]=view
        members.append({**source,'original_path':original_path,'original_sha256':_sha(raw),
            'view_path':view_path,'view_sha256':_sha(view),'original_range':[len(prefix),len(prefix)+len(raw)],
            'source_body_changed':False,'layout_assertions_executed':False,'old_contract_proved':False,
            'events':_events(source['member']),'self_swap_old_contract_relaxed':False})
    obligations=[]
    imports='//@ import \\wp::why3: heap_reallocation::Heap;\n//@ import \\wp::why3: vector_owned_state::Owners;\n//@ import \\wp::why3: vector_owned_effects::OwnedEffects;\n'
    for index,(name,statement) in enumerate(_obligations()):
        goal='t25_owned_effect_'+name.replace('.','_')
        path=f'obligations/{index:03d}-{goal}.c'
        data=(imports+'/*@ check lemma '+goal+': '+statement+';\n*/\n').encode();files[path]=data
        obligations.append({'id':name,'goal':goal,'statement':statement,'path':path,'sha256':_sha(data),
                            'kind':'check_lemma','dependencies':[],'status':'pending'})
    plan={'created':'2026-10-16 ET','version':1,'checker':identity(),'transfer':transfer['checker'],
        'parent_model':transfer['parent_model'],'type_registry':transfer['type_registry'],'elements':list(elements),
        'source_members':members,'obligations':obligations,
        'source_admission':'unsupported: original source/Heap layout, phase, padding, complete ownership and cleanup correspondence is not established',
        'source_heap_bridge_established':False,'source_typed_bridge_established':False,
        'current_model_records_admitted':[],'caller_premises_added':[],
        'phases':{'reserved':{'physical_field_values_established':False,'source_fresh_automatic_placement_required':True},
                  'live':{'initialized_header_required':True,'source_constructed_object_required':True}},
        'ownership':{'frontier':'Heap.next; never-issued allocation identity, not live-owner count',
                     'complete_source_owner_set_required':True,'raw_aliases_are_owners':False,
                     'registry_validity_does_not_establish_heap_ownership':True},
        'frame':{'receiver_padding_unchanged_claimed':False,'written_receiver_entire_footprint_excluded':True,
                 'buffer_payload_interpreted':False,'incoming_issued_object_metadata_preserved':True,
                 'physical_field_and_padding_projection_established':False},
        'cleanup':{'retire_replaces_release':False,'source_cleanup_established':False,
                   'swap_temporary':'fresh automatic trivial C struct temporary; no second owning vector',
                   'actual_vector_destruction':'Existing real release and automatic end required for each actual source owner; no omitted feasible cleanup'},
        'pending':['fresh full native task/hypothesis/import proofs for all nine conditional duties',
                   'actual emitted C layout/assertion and full original source/contract/event inverse audit',
                   'source-to-Heap typed field and arbitrary receiver padding correspondence',
                   'source-created complete ownership, phase, fresh receiver and temporary lifetime derivation',
                   'actual original scalar/assigns/cleanup and incoming allocated observation preservation',
                   'default library/allocator freshness, valid results, freeability, framing, release and replacement-effects TCB'],
        'unsupported':['old universal version2 contract adoption','generic incoming owners from unary validity',
                       'shared backing owners','self move','nonfresh destination move construction',
                       'old separated swap contract widened to self swap','element payload type/value proof from header transfer alone']}
    files['manifest.json']=_json(plan)
    return plan,files


def prepare(directory,*,elements=('int',)):
    plan,files=declaration(elements=elements);directory=Path(directory);directory.mkdir(exist_ok=False)
    for name,data in files.items():
        path=directory/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    return plan


def check(directory,*,elements=('int',)):
    plan,files=declaration(elements=elements);directory=Path(directory);paths=list(directory.rglob('*'))
    if directory.is_symlink()or any(p.is_symlink()or not(p.is_file()or p.is_dir())for p in paths):
        raise ValueError('owned source/Heap packet redirected or special path')
    directories={str(parent)for name in files for parent in Path(name).parents if str(parent)!='.'}
    if {str(p.relative_to(directory))for p in paths if p.is_file()}!=set(files)or \
            {str(p.relative_to(directory))for p in paths if p.is_dir()}!=directories:
        raise ValueError('owned source/Heap packet membership differs')
    if any((directory/name).read_bytes()!=data for name,data in files.items()):
        raise ValueError('owned source/Heap canonical source, domain or claim differs')
    return plan


def check_launch(directory,*,elements=('int',)):
    check(directory,elements=elements)
    raise ValueError('original move/swap source/Heap route remains unsupported before complete source and lifetime proofs')
