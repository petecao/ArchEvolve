"""Prospective exact OpenMP ABI classes; no measured/application costs.2026-10-06 ET.

Versioned 2026-10-12 ET: set a1 (22 classes, receipt group openmp_v1) is frozen for
service.openmp.a1 and services.v1; set a2 appends class 22 (__kmpc_for_static_init_8u)
and is collected as receipt group openmp_v2. a1 is the exact prefix of a2."""

def _profile(name, flags, argc, constants=(), outcome=None):
    return {'name':name,'ident_flags':flags,'argument_count':argc,
        'integer_constants':[{'index':i,'bits':b,'signed_decimal':str(v)} for i,b,v in constants],
        'constructed_outcome':outcome}

PROFILES=[_profile('__kmpc_fork_call',2,3+n,[(1,32,n)]) for n in (2,3,4,5,7,8)]+[
    _profile('__kmpc_barrier',34,2),_profile('__kmpc_barrier',322,2),
    _profile('__kmpc_for_static_init_4',514,9,[(2,32,34),(7,32,1),(8,32,1)]),
    _profile('__kmpc_for_static_init_8',514,9,[(2,32,34),(7,64,1),(8,64,1)]),
    _profile('__kmpc_for_static_fini',514,2),
    _profile('__kmpc_reduce_nowait',18,7,[(2,32,1),(3,64,8)],1),
    _profile('__kmpc_end_reduce_nowait',18,3),_profile('__kmpc_single',2,2,outcome=1),
    _profile('__kmpc_end_single',2,2),
    _profile('__kmpc_dispatch_init_4',2,7,[(2,32,1073741859),(3,32,0),(5,32,1),(6,32,1024)]),
    _profile('__kmpc_dispatch_init_8',2,7,[(2,32,1073741859),(3,64,0),(5,64,1),(6,64,64)]),
    _profile('__kmpc_dispatch_next_4',2,6,outcome=1),_profile('__kmpc_dispatch_next_4',2,6,outcome=0),
    _profile('__kmpc_dispatch_next_8',2,6,outcome=1),_profile('__kmpc_dispatch_next_8',2,6,outcome=0),
    _profile('__kmpc_dispatch_deinit',2,2)]
PROFILES.append(_profile('__kmpc_for_static_init_8u',514,9,[(2,32,34),(7,64,1),(8,64,1)]))
for index,p in enumerate(PROFILES):p.update(index=index,id='openmp.'+str(index),context='caller' if index<6 else 'serialized_team')
PROFILES_A1=PROFILES[:22]
PROFILES_A2=PROFILES[:23]
PROFILE_SETS={'a1':PROFILES_A1,'a2':PROFILES_A2}
GROUPS={'a1':'openmp_v1','a2':'openmp_v2'}
SETS_BY_GROUP={group:name for name,group in GROUPS.items()}
PROBE='per_event_steady_clock_empty_window'
STATE='prepared_legal_serialized_T1_sequences'
EVENT_CAP=16777216
