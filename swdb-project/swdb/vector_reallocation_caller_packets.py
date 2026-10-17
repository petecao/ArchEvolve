"""Canonical closed caller preparation; created 2026-10-16 ET.

A supplied prospective contract is never a public proof-contract identity.
All source/body/local targets remain pending. No dispatcher admits this packet.
"""
import hashlib
import json
from pathlib import Path
import re

from swdb import vector_reallocation_vcs as bodies

HERE=Path(__file__).parent
CONTRACT_ERROR=('the closed caller contract clause tokens require its explicit nonnegative count, '
                'scalar result and incoming frame; no premise is inferred or added')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json(value):
    return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()


def identity():
    names=('vector_reallocation_caller_packets.py','vector_reallocation_calls.py',
           'vector_reallocation_caller_vcs.py','vector_reallocation_lifetime.py',
           'vector_reallocation_capacity.py','vector_reallocation_composition.py','vector_reallocation_vcs.py',
           'vector_reallocation_model.py','vector_reallocation_inventory.py',
           'heap_model_vcs.py','heap_reallocation.mlw')
    return {'id':'vector-reallocation-caller-packets-1','sha256':_sha(_json([
        {'path':name,'sha256':_sha((HERE/name).read_bytes())}for name in names]))}


def _contract_count(formal_texts):
    if not isinstance(formal_texts,(list,tuple)) or not formal_texts or \
            not all(isinstance(text,str) and text.strip() and text.rstrip().endswith(';') for text in formal_texts):
        raise ValueError(CONTRACT_ERROR)
    # Each supplied annotation must contain whole clauses. Concatenating blocks
    # or deleting whitespace could turn malformed tokens into a different clause.
    clauses=[part for text in formal_texts for part in text.rstrip().split(';')[:-1]]
    if len(clauses)!=3:raise ValueError(CONTRACT_ERROR)
    first=re.fullmatch(r'\s*requires\s+0\s*<=\s*([A-Za-z_]\w*)\s*',clauses[0])
    if first is None:raise ValueError(CONTRACT_ERROR)
    count=first.group(1)
    if re.fullmatch(r'\s*assigns\s+\\nothing\s*',clauses[1]) is None or \
            re.fullmatch(r'\s*ensures\s+\\result\s*==\s*\(\s*'+re.escape(count)+
                         r'\s*>\s*0\s*\?\s*7\s*:\s*0\s*\)\s*',clauses[2]) is None:
        raise ValueError(CONTRACT_ERROR)
    return count


def declaration(source,function,formal_texts):
    """Reparse physical source and regenerate every payload, never trust a manifest."""
    from swdb import c_lowering, vector_reallocation_model as model
    source=Path(source)
    if source.is_symlink() or not source.is_file():
        raise ValueError('one regular physical C++ caller source is required')
    count=_contract_count(formal_texts)
    lowering=c_lowering.lower(source,function)
    candidate=lowering.vector_reallocation_candidate
    if candidate.get('verdict')!='pending' or not candidate.get('candidate_only'):
        raise ValueError('the source has no checked closed caller candidate')
    if candidate['source_sha256']!=_sha(source.read_bytes()) or candidate['lowered_sha256']!=lowering.sha256:
        raise ValueError('the source/candidate/lowering identity differs')
    if count!=candidate['count']['name']:raise ValueError(CONTRACT_ERROR)
    contract={'clauses':list(formal_texts),'sha256':_sha(_json(list(formal_texts))),
              'entry_discharge':'matching prospective nonnegative-count clause; public contract binding pending',
              'ordinary_contract_identity':'pending: bind original library entry/content and proof placement at public setup'}
    files={'original.cc':source.read_bytes(),'lowering.c':lowering.text.encode(),
           'anchors.json':lowering.anchors_json.encode(),'contract.json':_json(contract),
           'theory/heap_reallocation.mlw':(HERE/'heap_reallocation.mlw').read_bytes()}
    local=candidate['heap_lifetime_plan'];rows=[]
    for index,row in enumerate(local['obligations']):
        goal='t25v3_caller_'+row['id'].replace('.','_')
        text=('//@ import \\wp::why3: heap_reallocation::Heap;\n'+bodies.PRELUDE+
              '/*@ check lemma '+goal+': '+row['statement']+';\n*/\n').encode()
        path=f'local/{index:03d}-{goal}.c';files[path]=text
        rows.append({**row,'goal':goal,'path':path,'kind':'check_lemma','sha256':_sha(text)})
    numeric=local['numeric_kernel'];path='local/caller-count-numeric.c'
    files[path]=numeric['c_source'].encode()
    rows.append({**numeric,'path':path})
    from swdb.vector_reallocation_composition import constructor_entry
    application,application_receipt=constructor_entry(candidate,contract)
    goal='t25v3_caller_'+application['id'].replace('.','_')
    text=('//@ import \\wp::why3: heap_reallocation::Heap;\n'+bodies.PRELUDE+
          '/*@ check lemma '+goal+': '+application['statement']+';\n*/\n').encode()
    path='applications/000-'+goal+'.c';files[path]=text
    rows.append({**application,'goal':goal,'path':path,'kind':'check_lemma','sha256':_sha(text)})
    from swdb.vector_reallocation_composition import zero_constructor
    zero_application,zero_receipt=zero_constructor(candidate)
    zero_goal='t25v3_caller_'+zero_application['id'].replace('.','_')
    zero_text=('//@ import \\wp::why3: heap_reallocation::Heap;\n'+bodies.PRELUDE+
               '/*@ check lemma '+zero_goal+': '+zero_application['statement']+';\n*/\n').encode()
    zero_path='applications/001-'+zero_goal+'.c';files[zero_path]=zero_text
    rows.append({**zero_application,'goal':zero_goal,'path':zero_path,'kind':'check_lemma','sha256':_sha(zero_text)})
    from swdb.vector_reallocation_composition import positive_constructor_entry
    positive,positive_receipt=positive_constructor_entry(candidate)
    positive_goal='t25v3_caller_'+positive['id'].replace('.','_')
    positive_text=('//@ import \\wp::why3: heap_reallocation::Heap;\n'+bodies.PRELUDE+
                   '/*@ check lemma '+positive_goal+': '+positive['statement']+';\n*/\n').encode()
    positive_path='applications/002-'+positive_goal+'.c';files[positive_path]=positive_text
    rows.append({**positive,'goal':positive_goal,'path':positive_path,'kind':'check_lemma','sha256':_sha(positive_text)})
    from swdb.vector_reallocation_composition import reserve_entry
    reserve,reserve_receipt=reserve_entry(candidate)
    reserve_goal='t25v3_caller_'+reserve['id'].replace('.','_')
    reserve_text=('//@ import \\wp::why3: heap_reallocation::Heap;\n'+bodies.PRELUDE+
                  '/*@ check lemma '+reserve_goal+': '+reserve['statement']+';\n*/\n').encode()
    reserve_path='applications/003-'+reserve_goal+'.c';files[reserve_path]=reserve_text
    rows.append({**reserve,'goal':reserve_goal,'path':reserve_path,'kind':'check_lemma','sha256':_sha(reserve_text)})
    calls={row['call']:row['source']for row in candidate['call_obligations']}
    events={row['event']:row for row in candidate['lowered_lifetime']['events']
            if row['reachable_on_normal_return']}
    required=[]
    # Complete canonical body duties are regenerated, not imported as axioms.
    # Until composition is complete these are only target payloads, not proof.
    for member,event in [('ctor_count_value','constructor'),('reserve','reserve'),('dtor','destructor')]:
        name='std_vector_int_realloc_v3_'+member
        plan,body_files=bodies.declaration(name)
        prefix='bodies/'+member+'/'
        for filename,data in body_files.items():files[prefix+filename]=data
        required.append({'id':name,'sha256':plan['source_sha256'],'proof_record':None,
                         'role':'current ordinary qualified body dependency required; no record admitted'})
        for row in plan['obligations']:
            rows.append({**row,'id':'body.'+member+'.'+row['id'],'path':prefix+row['path'],
                         'source_call':calls[member],'lowered_events':[events[event]],
                         'model_source':prefix+'qualified.c','status':'pending'})
    for member in ('data','operator_index'):
        if member not in calls:continue
        name='std_vector_int_'+member;data=c_lowering.model_text(name).encode()
        path='observations/'+member+'.c';files[path]=data
        required.append({'id':name,'sha256':_sha(data),'path':path,'proof_record':None,
                         'role':'current observation body dependency/application proof pending'})
    plan={'version':1,'preparation_only':True,
          'proof_admission':'unsupported: complete caller composition remains pending',
          'function':function,'checker':identity(),'source':{'path':'original.cc','sha256':_sha(files['original.cc'])},
          'lowering':{'path':'lowering.c','sha256':lowering.sha256,'tool':lowering.tool},
          'contract':contract,'candidate':candidate,'composition':{'constructor_entry':application_receipt,'zero_constructor':zero_receipt,'positive_constructor_entry':positive_receipt,'reserve_entry':reserve_receipt},'model':model.identity(),
          'semantics':{'path':'theory/heap_reallocation.mlw','sha256':_sha(files['theory/heap_reallocation.mlw'])},
          'caller_premises_added':[],'incoming_pointer_maps_restricted':False,
          'required_models':required,'current_proof_records_admitted':[],
          'obligations':rows,
          'missing':['ordinary public contract identity/placement and current dependency admission',
                     'full source-local branch/state/typed-image/observation/cleanup/final incoming-frame composition',
                     'source-runtime automatic placement and target layout binding',
                     'fresh normal ordinary/smoke proofs and complete task/import/hypothesis audit']}
    files['manifest.json']=_json(plan)
    return plan,files


def prepare(source,function,formal_texts,directory):
    plan,files=declaration(source,function,formal_texts)
    directory=Path(directory);directory.mkdir(exist_ok=False)
    for name,data in files.items():
        path=directory/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    return plan


def check(source,function,formal_texts,directory):
    plan,files=declaration(source,function,formal_texts)
    directory=Path(directory);paths=list(directory.rglob('*'))
    if directory.is_symlink() or any(p.is_symlink() or not(p.is_file() or p.is_dir()) for p in paths):
        raise ValueError('caller source/packet/import path is redirected or special')
    expected_dirs={str(parent)for name in files for parent in Path(name).parents if str(parent)!='.'}
    if {str(p.relative_to(directory))for p in paths if p.is_file()}!=set(files) or \
            {str(p.relative_to(directory))for p in paths if p.is_dir()}!=expected_dirs:
        raise ValueError('caller source/packet/import membership differs')
    for name,data in files.items():
        if (directory/name).read_bytes()!=data:raise ValueError('canonical caller source/contract/VC differs: '+name)
    return plan
