"""Pure source fixtures. Predicted verdicts are separate from producer inputs."""
from copy import deepcopy


def event(kind, thread=0, **fields):
    return dict(kind=kind, thread=thread, **fields)


def common(name, dtype=0, separate_regions=False):
    plan = dict(schema='owned-finite-dx100-event-plan-1', id=name,
        objects=[dict(id=key, guest_base=guest, physical_base=physical, dtype=dtype, extent=2, base_cell=cell)
                 for key,guest,physical,cell in [('a',4096,12288,0),('b',4352,16384,2)]],
        tiles=[dict(id=key,index=index,dtype=dt) for key,index,dt in
               [('t0',0,0),('t2',2,0),('t4',4,0),('half1',1,0),('pair0',0,3),('pair4',4,3)]],
        registers=[dict(id=key,index=index) for key,index in
                   [('min0',0),('max0',1),('stride0',2),('min1',3),('max1',4),('stride1',5)]],events=[])
    # Prospective prestate data only. No allocator/claim/reset is emitted.
    regions = ([dict(id=6,begin=4096,end=4096+2*(4 if dtype==0 else 8)),
                dict(id=7,begin=4352,end=4352+2*(4 if dtype==0 else 8))]
               if separate_regions else [dict(id=6,begin=4096,end=4608)])
    mmio=(17179869184,17181966336,17184063488,17184063552,17184063616,17184063744,17184063768)
    regions=[dict(id=i,begin=mmio[i],end=mmio[i+1]) for i in range(6)]+regions
    context = dict(schema='owned-finite-model-context-1',source_plan_sha256=None,entry_identity=None,
        entry_nodes=0,entry_events=0,quiescent=True,fresh_payload=True,
        tile_owners=[0]*4+[1]*4+[-1]*24,register_owners=[0]*3+[1]*3+[-1]*26,
        regions=regions,live_objects=['a','b'],owned_premises=[])
    return plan,context


def regs(thread=0):
    return [event('reg_write',thread,register=key+str(thread),value=value)
            for key,value in [('min',0),('max',1),('stride',1)]]


def stream(kind, command, thread=0, obj='a', tile='t0'):
    return event(kind,thread,object=obj,tile=tile,min='min'+str(thread),max='max'+str(thread),
                 stride='stride'+str(thread),command=command)


def cases():
    out=[]
    def add(plan,context,prediction,reason,pair):
        out.append(dict(plan=plan,context=context,prediction=prediction,reason=reason,pair=pair))
    begin=event('critical_begin');end=event('critical_end')
    p,c=common('history_latest_positive')
    p['events']=[begin,event('cpu_write',object='a',lane=0,value=1),
        event('cpu_write',1,object='a',lane=0,value=2),*regs(),stream('stream_load','first'),
        event('cpu_cas',1,object='a',lane=0,expected=2,desired=3,out='success',expected_out='expected'),
        event('assert_eq',result='success',value=1),event('wait_tile',tile='t0'),event('tile_read',tile='t0',lane=0,out='history'),
        event('assert_in',result='history',values=[2,3]),stream('stream_load','second',tile='t2'),
        event('wait_tile',tile='t2'),event('tile_read',tile='t2',lane=0,out='latest'),event('assert_eq',result='latest',value=3),end]
    add(p,c,'predicted_valid','Other-thread CAS extends first read history; second issue sees latest value3.','history')
    q=deepcopy(p);q['id']='history_exact_issue_negative';q['events'][11]=event('assert_eq',result='history',value=2)
    add(q,deepcopy(c),'predicted_invalid','History choice3 refutes exact-at-issue2.','history')

    p,c=common('other_thread_cpu_read_positive')
    p['events']=[begin,event('cpu_write',object='a',lane=0,value=7),*regs(),stream('stream_load','load'),
        event('cpu_read',1,object='a',lane=0,out='read'),event('assert_eq',result='read',value=7),event('wait_tile',tile='t0'),end]
    add(p,c,'predicted_valid','Pending device read permits other-thread ordinary CPU read.','cpu_access')
    p,c=common('pending_store_cpu_read_negative')
    p['events']=[begin,event('tile_write',tile='t0',lane=0,value=7),*regs(),stream('stream_store','store'),
        event('cpu_read',1,object='a',lane=0,out='read'),event('wait_tile',tile='t0'),end]
    add(p,c,'predicted_invalid','Pending device store forbids CPU read from either thread.','cpu_access')

    for name,separate,first_kind,prediction,reason in [
        ('same_region_write_cover_positive',False,'stream_store','predicted_valid','Same-region writing conflict covers the earlier other-thread store.'),
        ('same_region_read_read_noncover_negative',False,'stream_load','predicted_invalid','Read/read in the same region does not cover the earlier command.'),
        ('different_region_noncover_negative',True,'stream_store','predicted_invalid','Different-region commands with disjoint memory and tiles do not cover.')]:
        p,c=common(name,separate_regions=separate)
        prefix=[event('tile_write',tile='t0',lane=0,value=7)] if first_kind=='stream_store' else [event('cpu_write',object='a',lane=0,value=7)]
        p['events']=[begin,*prefix,event('cpu_write',1,object='b',lane=0,value=9),*regs(),*regs(1),stream(first_kind,'old'),
            stream('stream_load','new',1,'b','t4'),event('assert_pending',command='old',value=0),
            event('wait_tile',tile='t0'),event('wait_tile',1,tile='t4'),end]
        add(p,c,prediction,reason,'region_cover')

    p,c=common('owned_tile_positive');p['events']=[event('tile_write',tile='t0',lane=0,value=9),event('tile_read',tile='t0',lane=0,out='x'),event('assert_eq',result='x',value=9)]
    add(p,c,'predicted_valid','Tile0 is separately owned by thread0 in the receiver premise.','ownership')
    p,c=common('wrong_owner_negative');p['events']=[event('tile_write',1,tile='t0',lane=0,value=9)]
    add(p,c,'predicted_invalid','Thread1 tile0 access retains the model ownership check.','ownership')
    p,c=common('disjoint_owned_tiles_positive');p['events']=[event('tile_write',tile='t0',lane=0,value=9),event('tile_write',1,tile='t4',lane=0,value=11),event('tile_read',tile='t0',lane=0,out='x'),event('assert_eq',result='x',value=9)]
    add(p,c,'predicted_valid','Disjoint tiles retain independent thread ownership.','ownership')

    for name,dtype,tile,prediction in [('u64_second_half_conflict_negative',3,'pair0','predicted_invalid'),('u32_disjoint_half_positive',0,'t0','predicted_valid')]:
        p,c=common(name,dtype=dtype);p['events']=[begin,event('cpu_write',object='a',lane=0,value=7),*regs(),stream('stream_load','load',tile=tile),
            event('tile_write',tile='half1',lane=0,value=11),event('tile_read',tile='half1',lane=0,out='half'),event('assert_eq',result='half',value=11),event('wait_tile',tile=tile),end]
        add(p,c,prediction,'An8-byte counted destination covers physical half1; a4-byte destination does not.','physical_half')

    p,c=common('prior_cpu_store_visible_positive');p['events']=[begin,event('cpu_write',object='a',lane=0,value=1),event('cpu_write',1,object='a',lane=0,value=2),*regs(),stream('stream_load','load'),event('wait_tile',tile='t0'),event('tile_read',tile='t0',lane=0,out='x'),event('assert_eq',result='x',value=2),end]
    add(p,c,'predicted_valid','Writes completed before issue supply the latest issue snapshot.','visibility')
    p,c=common('covered_store_next_thread_load_positive');p['events']=[begin,event('tile_write',tile='t0',lane=0,value=7),*regs(),*regs(1),stream('stream_store','store'),stream('stream_load','load',1,'a','t4'),event('assert_pending',command='store',value=0),event('wait_tile',1,tile='t4'),event('tile_read',1,tile='t4',lane=0,out='x'),event('assert_eq',1,result='x',value=7),end]
    add(p,c,'predicted_valid','Same-region cover publishes the store before next-thread issue snapshot.','visibility')

    for name,wait,prediction in [('critical_end_wait_positive',True,'predicted_valid'),('critical_end_without_wait_negative',False,'predicted_invalid')]:
        p,c=common(name);p['events']=[begin,event('tile_write',tile='t0',lane=0,value=7),*regs(),stream('stream_store','store'),*([event('wait_tile',tile='t0')] if wait else []),end]
        add(p,c,prediction,'Critical-end requires completion of stores issued since its explicit frontier.','critical_end')
    p,c=common('outside_critical_store_positive');p['events']=[event('tile_write',tile='t0',lane=0,value=7),*regs(),stream('stream_store','outside'),event('critical_begin',1),event('critical_end',1),event('assert_pending',command='outside',value=1),event('wait_tile',tile='t0')]
    add(p,c,'predicted_valid','The scoped critical-end check excludes an unrelated preexisting store.','critical_end')
    p,c=common('pending_read_lifetime_end_negative');p['events']=[event('cpu_write',object='a',lane=0,value=7),*regs(),stream('stream_load','load'),event('lifetime_end',object='a'),event('wait_tile',tile='t0')]
    add(p,c,'predicted_invalid','Pending read footprint prevents lifetime end independently of critical stores.','lifetime')
    return out
