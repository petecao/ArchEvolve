"""Reproduce fresh source/configuration records, never importing execution records. 2026-10-06 ET.
Run from swdb-project: python .scratch/lanl-db-analytic-eval-2026-10-06/evidence/09_generate_functional_target.py
The configuration SHA/line pins were independently read at the upstream revision.
"""
import hashlib
import json
from pathlib import Path
import yaml

HOME=Path(__file__).resolve().parents[3]
REV='e4fc4afdf894f295442cef3604667a469fab8e62'
TARGET='dx100-e4fc4af-functional-analytic-v1'
INTERFACE={'id':'dx100-functional-source','version':'1.0-e4fc4af'}
HEADER='dx100/dxc_lowering.hpp'
API='apps/dx100/benchmarks/API/MAA_functional.hpp'
SHA=lambda p:hashlib.sha256((HOME/p).read_bytes()).hexdigest()
DIGEST=lambda d:hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
HSHA=SHA('library/'+HEADER);ASHA=SHA(API)
REF={'root':'library','path':'dx100/reference.hpp','sha256':SHA('library/dx100/reference.hpp')}
DRIVER={'root':'library','path':'dx100/drivers/differential.cc','sha256':SHA('library/dx100/drivers/differential.cc')}
# Exact C declarations in the shipped normalized wrapper. Counts are source operand slots,
# not observed physical allocation, throughput, completion latency or execution evidence.
COMMANDS=[
 ('session_begin','void __dxc_session_begin()',21,26,'none',None,0,0,None),
 ('thread_context','dxc_context __dxc_thread_context()',27,38,'none',None,8,8,None),
 ('const_i32','void __dxc_const_i32(int32_t value,int reg)',39,39,'none',None,0,1,None),
 ('wait','void __dxc_wait(int tile)',40,40,'none',None,1,0,None),
 ('gather','template<class T> void __dxc_gather(T*base,int index,int dst)',41,41,'gather','single_valued_indirect',2,0,'maa_indirect_load<int>'),
 ('stream_load','template<class T> void __dxc_stream_load(T*base,int minimum,int maximum,int stride,int dst)',42,42,'load','stream',1,3,'maa_stream_load<int>'),
 ('range_loop','void __dxc_range_loop(int last_i,int last_j,int lower,int upper,int stride,int rows,int columns)',43,43,'none',None,4,3,None),
 ('tile_size','uint16_t __dxc_tile_size(int tile)',44,44,'none',None,1,0,None),
 ('tile_pointer','template<class T> T* __dxc_tile_pointer(int tile)',45,50,'none',None,1,0,None),
 ('alu_scalar','void __dxc_alu_scalar(int src,int reg,int dst,Operation_t op)',51,51,'none',None,2,1,None)]


def save(path,data):
    path=HOME/path;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(yaml.safe_dump(data,sort_keys=False))


def base(kind,rid):
    return {'kind':kind,'schema_version':'0.4','id':rid,'status':'draft','created':'2026-10-06','updated':'2026-10-06',
        'provenance':[{'id':'functional-source','kind':'source_code',
            'description':'Fresh functional-source/configuration identity; no output, calibration, build-readiness or performance evidence imported.',
            'uri':'https://github.com/arkhadem/DX100/tree/'+REV}]}


def evidence(path,sha,first,last,uri=None):
    return {'uri':uri or 'https://github.com/arkhadem/DX100/blob/'+REV+'/'+path,
        'path':path,'sha256':sha,'lines':[first,last]}


def param(value,basis,source,unit):return {'value':value,'basis':basis,'source':source,'unit':unit}


def main():
    operations=[];commands=[]
    for name,signature,first,last,memory,shape,tiles,regs,backend in COMMANDS:
        intrinsic='dxc_'+name+'.functional-v1';op='dx100.functional.v1.'+name
        entry='intrinsic.'+intrinsic;lower='lowering.'+intrinsic+'.dx100-functional-source.1.0-e4fc4af'
        source={'root':'library','path':HEADER,'sha256':HSHA}
        pin=evidence('library/'+HEADER,HSHA,first,last,'project-file:library/'+HEADER)
        operation=base('operation',op)
        operation.update(name='__dxc_'+name,interface=INTERFACE,model={'id':'dx100-source-configuration','revision':REV},
            backend='functional-source',support='source_supported',signature=signature,types=['int32_t' if memory!='none' else 'declared wrapper operands'],
            memory_effects='Read application values into private staging tiles.' if memory!='none' else 'No application-memory load/store; private functional state and control only.',
            masks='Normalized wrapper has no condition-mask operand.',repeated_indices='Permitted read repetitions; source observer retains dynamic multiplicity.' if memory=='gather' else 'Not a scatter or atomic application-memory update.',
            ordering='Preserve normalized caller order and waits; no physical scheduling or cross-worker ordering is established.',
            completion='Functional-source semantics only; target completion latency and overlap remain unknown.',
            resources={'tiles':tiles,'scalar_registers':regs,'allocation':'Declared operand slots per wrapper; source sharing and runtime lifetimes are counted separately.'},
            build={'headers':['library/'+HEADER,'benchmarks/API/MAA_functional.hpp'],'defines':['FUNC'],
                'dependencies':['Pinned functional API source at '+REV,'OpenMP runtime for the functional execution']},
            semantics={'reads_application_memory':{'state':'supported','value':memory!='none','basis':'code_reading',
                'description':'Shipped wrapper delegates to the selected functional source; private emulator work is not CPU target work.'}},
            declaration_evidence=[pin],implementation_evidence=[evidence('benchmarks/API/MAA_functional.hpp',ASHA,1,774)])
        save('records/operations/'+op+'.yaml',operation);operations.append(op)
        clause={'id':'source-semantics','role':'postcondition',
            'statement':'The FUNC-selected wrapper delegates to the pinned functional API; this entry declares no executed certification or hardware visibility.',
            'discharge_mode':'open','negative_control':{'id':'none','reason':'This source-only entry has no newly discharged execution claim.'},
            'formal':{'language':'reference','reference':{**REF,'symbol':name}},'formal_label':'stated'}
        library_entry={'kind':'intrinsic','id':entry,'intrinsic_record':intrinsic,
            'provenance':{'origin':{'source_configuration':'Pinned source-only functional view, created 2026-10-06 ET'},
                'normalized_wrapper':source,'functional_api':{'root':'project','path':API,'sha256':ASHA}},
            'signature':signature,'intent':'Source-pinned functional semantic event for analytic observation.',
            'reference_semantics':{**REF,'symbol':name},'hardware_operations':[op],
            'memory_footprint':{'reads':['active application values'] if memory!='none' else [],
                'private_state':'Emulator register/tile accesses are bookkeeping, not additional application DRAM requests.'},
            'completion':{'mode':'functional_source_semantics','host_concurrency':'unknown'},'lowerings':[lower],'clauses':[clause]}
        save('library/intrinsics/'+intrinsic+'.yaml',library_entry)
        lowering={'kind':'lowering','id':lower,'intrinsic':entry,
            'provenance':library_entry['provenance'],'interface':INTERFACE,
            'location':{'root':'library','path':HEADER,'symbol':'__dxc_'+name},'code_sha256':HSHA,
            'build_defines':{'required':['FUNC'],'forbidden':['GEM5','SWDB_STRICT','SWDB_DXC_DIAGNOSTIC']},
            'differential_test':DRIVER,'clauses':[clause]}
        save('library/lowerings/dx100-functional-source/1.0-e4fc4af/'+name+'.yaml',lowering)
        data=base('intrinsic',intrinsic)
        data.update(name='__dxc_'+name,interface=INTERFACE,hardware_operations=[op],memory_kind=memory,
            address_shape=shape,element_bits=32 if memory!='none' else None,lanes=None,
            library_entry={'id':entry,'path':'library/intrinsics/'+intrinsic+'.yaml','content_sha256':DIGEST(library_entry)},
            source_view={'format':'swdb.intrinsic-source-view.v1','variant':'functional-v1','source':source,
                'backend':'functional_source','compile_defines':['FUNC'],
                'compile_undefines':['GEM5','SWDB_STRICT','SWDB_DXC_DIAGNOSTIC'],'evidence_scope':'functional_source_semantics'})
        save('records/intrinsics/'+intrinsic+'.yaml',data)
        debug='__dxc_'+name+('<int>' if name in ('gather','stream_load','tile_pointer') else '')
        alias={'debug_name':debug,'source':source,'source_sha256':HSHA,'memory_base_argument':0 if memory!='none' else None,'role':'command'}
        aliases=[alias];producers=[]
        if backend:
            api={'root':'project','path':API,'sha256':ASHA}
            aliases.append({'debug_name':backend,'source':api,'source_sha256':ASHA,'memory_base_argument':0,'role':'backend_alias'})
            producers=[{'debug_name':backend,'source':api,'source_sha256':ASHA}]
        bookkeeping=[{'debug_name':helper,'source':{'root':'project','path':API,'sha256':ASHA},'source_sha256':ASHA}
            for helper in ('get_region','check_region')] if memory!='none' else []
        command={'event':'dx100.functional.'+name,'intrinsic':intrinsic,'hardware_operations':[op],
            'aliases':aliases,'target_access_sources':producers,'bookkeeping_access_sources':bookkeeping,
            'memory_effect':'read' if memory!='none' else 'none',
            'active_elements_policy':'observed_target_reads' if memory!='none' else 'not_applicable'}
        if memory!='none':command['target_reads_per_active_element']=1
        commands.append(command)
    target=base('hardware_target',TARGET)
    target.update(name='DX100 pinned configuration and FUNC source-only analytic identity',
        model={'id':'dx100-source-configuration','revision':REV},interface=INTERFACE,
        backend={'id':'functional-source','readiness':'source_supported','build_evidence':[]},execution_host=None,
        configuration={'evidence_scope':'configuration_declarations_only','cores':4,'clock_hz':3200000000,
            'tile_elements':16384,'memory_channels':2,'transaction_bytes':64,'memory_ranks':1,
            'bank_groups':4,'banks_per_group':4,'row_bits':16,'column_bits':7,
            'controller_queue_entries':32,'cpu_model_declaration':'X86O3CPU',
            'native_physical_placement':None,'effective_memory_parallelism':None,'host_instruction_rates':None},
        operations=operations,source_evidence=[
            evidence('scripts/sim.py','82c8d78e4339f1be9249c0e92db8a8d5f9654310f1fe4dc91680da6a9e0f7681',90,235),
            evidence('configs/common/Options.py','91e2f35957b62b2d331d490c76858b36c6d779886dc20fa3b11f17226b80916c',173,177),
            evidence('configs/common/MemConfig.py','b86a10d1e42bed8558f78fc928f499b141995d269a45e0f157da34c6e791f352',155,264),
            evidence('ext/ramulator2/ramulator2/src/addr_mapper/impl/linear_mappers.cpp','50b81367aeaa0e1c2df92f5d05586018d0d457db9dc807823fb74de6339d2339',25,93),
            evidence('ext/ramulator2/ramulator2/src/dram/impl/DDR4.cpp','b85f67de5bc9495f91ea51112c0ce5b9396c4e35473e219b6f06821e9d9aa5cc',25,49),
            evidence('ext/ramulator2/ramulator2/example_gem5_config.yaml','aca6e27b58afdfbfd80b7ec41c3f0e7e574a1fc7355a3512981ead823f68731b',1,60),
            evidence('ext/ramulator2/ramulator2/src/memory_system/impl/generic_DRAM_system.cpp','f6e0b562be75766e2c48d45346e794f5c48b3d4e1c59b32e90596fe95a90374e',159,175),
            evidence('src/mem/MAA/MAA.cc','058395cbd171ccf3746fb524967d2d205cb8d622d4aa06e8eef530b00dc21299',261,339),
            evidence('src/mem/MAA/MAA.py','347f0e08124bf9d951fb3ee24654074b5d681b71bc6168538c82dbd0b35856f2',26,75)])
    save('records/hardware_targets/'+TARGET+'.yaml',target)
    input_record=base('input','dx100-functional-kron-g16-k16')
    input_record['schema_version']='0.2'
    input_record.update(name='DX100 registered built-in Kronecker scale16 degree16 source-only input',
        generator={'application':'dx100-gapbs','tool':'Pinned built-in Generator and Builder in the protected source artifact','arguments':'-g 16 -k 16'},
        properties={name:{'value':value,'basis':'code_reading','evidence_refs':['functional-source']} for name,value in
            [('scale',16),('requested_degree',16),('directed',False),('weighted',False)]},
        notes=['Source-defined input identity; new execution receipts retain actual graph sizes and trial-source sequence.',
            'The same generator tuple has historical native profiles. A new ID does not establish campaign baseline blindness.'])
    save('records/inputs/'+input_record['id']+'.yaml',input_record)
    layout={name:([{'lsb':bit,'bits':width}] if width else []) for name,bit,width in
        [('channel',6,1),('rank',0,0),('bank_group',14,2),('bank',16,2),('row',18,16)]}
    for threads in (1,4):
        description=base('target_description',TARGET+'.t'+str(threads))
        unknown=lambda unit: param(None,'unknown','Required target service premise is not established by source configuration.',unit)
        description.update(format='swdb.target-description.v1',version='1',target=TARGET,threads=threads,
            estimator_variant='team',calibration_sources=[],dram_address_layout=layout,
            functional_observation={'format':'swdb.functional-observation.v1',
                # This observation view binds the canonical read-offload artifact, which does not call alu_scalar.
                'commands':[c for c in commands if c['event']!='dx100.functional.alu_scalar'],
                'request_policy':{'transaction_bytes':64,'read_coalescing':'window_unique_lines'},
                'placement':{'policy':'isolated_row_aligned_allocations','basis':'inferred','physical_placement_known':False},
                'window':{'policy':'logical_fixed_requests_per_command_worker','requests':16384,'basis':'inferred',
                    'source':'Pinned scripts/sim.py tile capacity16384 motivates a declared logical request-window scenario; it is not a hardware queue, physical placement, or row-hit observation.'}},
            mechanisms=[
                {'model':'compute_throughput','parameters':{name+'_ops_per_s':unknown('operations/s') for name in ('integer','floating_point','branch','atomic')}},
                {'model':'reorder_window_rows','selector':{'domain':'offload'},'parameters':{
                    'row_miss_service_s':param(37.5e-9,'inferred','DDR4_3200W nRP+nRCD+nCL at625ps; serialized closed-row service scenario.','seconds/request'),
                    'row_hit_service_s':param(12.5e-9,'inferred','DDR4_3200W nCL20 at625ps; declared latency scenario, not physical row-hit measurement.','seconds/request'),
                    'effective_memory_parallelism':unknown('requests')}},
                {'model':'fetch_queue','selector':{'domain':'offload'},'parameters':{
                    'queue_entries':param(32,'code_reading','Pinned example controller queue_size32; an ideal capacity bound only.','entries'),
                    'fetch_latency_s':unknown('seconds/request'),'admission_requests_per_s':unknown('requests/s')}},
                {'model':'tile_staging','selector':{'domain':'offload'},'parameters':{'staging_bytes_per_s':unknown('bytes/s')}},
                {'model':'offload_setup','accounting':'additive_overhead','selector':{'event_ids':[c['event'] for c in commands if c['event']!='dx100.functional.alu_scalar']},
                    'parameters':{'seconds_per_event':unknown('seconds/event')}}])
        save('records/target_descriptions/'+description['id']+'.yaml',description)

if __name__=='__main__':main()
