#!/usr/bin/env python3
"""Generate pinned DX100 definitions from reviewed specification inputs.

Created: 2026-10-03 ET. This writes normative definitions only, never certification
or review receipts. A header change changes every lowering pin and needs recertification.
"""
from pathlib import Path
import sys
import hashlib
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from swdb import artifacts

OPS = {
    'gather': ('gather','single_valued_indirect',['dx100.mmio.v1.indirect-load.i32'],'dxc-gather'),
    'session_begin': ('none',None,[],None),
    'thread_context': ('none',None,[],None),
    'const_i32': ('none',None,['dx100.mmio.v1.const.i32'],None),
    'wait': ('none',None,['dx100.mmio.v1.wait-ready'],'dxc-wait'),
    'range_loop': ('none',None,['dx100.mmio.v1.range-loop.i32'],'dxc-ranged-gather'),
    'stream_load': ('load','stream',['dx100.mmio.v1.stream-load.i32'],'dxc-stream_load'),
    'tile_size': ('none',None,[],None),
    'tile_pointer': ('none',None,[],None),
    'alu_scalar': ('none',None,['dx100.mmio.v1.alu-scalar-lt.i32'],None),
}
SIGNATURES = {
 'gather':'template<class T> void __dxc_gather(T* base, int index_tile, int dst_tile)',
 'session_begin':'void __dxc_session_begin()',
 'thread_context':'dxc_context __dxc_thread_context() // context owns tile[8] and reg[8]',
 'const_i32':'void __dxc_const_i32(int32_t value, int reg)',
 'wait':'void __dxc_wait(int tile)',
 'range_loop':'void __dxc_range_loop(int last_i_reg, int last_j_reg, int lower_tile, int upper_tile, int stride_reg, int rows_tile, int cols_tile)',
 'stream_load':'template<class T> void __dxc_stream_load(T* base, int min_reg, int max_reg, int stride_reg, int dst_tile)',
 'tile_size':'uint16_t __dxc_tile_size(int tile)',
 'tile_pointer':'template<class T> T* __dxc_tile_pointer(int tile)',
 'alu_scalar':'void __dxc_alu_scalar(int src_tile, int reg, int dst_tile, Operation_t op)',
}
PRIMARY_CONTROLS = {
 'gather':('dropped_wait','read_before_wait'), 'session_begin':('second_session_begin','session_begin_twice'),
 'thread_context':('shared_context','thread_ownership_tile'), 'const_i32':('constant_uncovered','constant_uncovered_register'),
 'wait':('dropped_wait','read_before_wait'), 'range_loop':('dropped_continuation','range_continuation'),
 'stream_load':('truncation','tile_truncation'), 'tile_size':('dropped_wait','read_before_wait'),
 'tile_pointer':('read_before_wait','reference_semantics'), 'alu_scalar':('dropped_wait','read_before_wait'),
}
FOOTPRINTS = {
 'gather':{'reads':['base[index_tile[k]] for produced lanes','index_tile'],'writes':['dst_tile']},
 'session_begin':{'reads':['existing allocation/initialization state'],'writes':['session metadata and instrumentation counters']},
 'thread_context':{'reads':['configured core count and allocator'],'writes':['8 allocated tiles and 8 allocated registers for this thread']},
 'const_i32':{'reads':['CPU scalar value'],'writes':['allocated destination register']},
 'wait':{'reads':['held ready status for the named tile'],'writes':[]},
 'range_loop':{'reads':['lower/upper bound tiles','stride and continuation registers'],'writes':['rows/columns output tiles','continuation registers']},
 'stream_load':{'reads':['base values within registered memory','min/max/stride registers'],'writes':['dst_tile']},
 'tile_size':{'reads':['tile size bookkeeping'],'writes':[]},
 'tile_pointer':{'reads':['cacheable tile pointer metadata'],'writes':[]},
 'alu_scalar':{'reads':['src_tile and scalar register'],'writes':['dst_tile']},
}
INTERFACE={'id':'dx100-mmio','version':'1.0-e4fc4af'}

def pin(path,root='library',symbol=None):
    base=ROOT/'library' if root=='library' else ROOT.parent
    result={'path':path,'sha256':artifacts.file_hash(base/path),'root':root}
    if symbol:result['symbol']=symbol
    return result

def clause(cid,role,text,mode,control=None,reference=None,owner=None,evidence=None):
    data={'id':cid,'role':role,'statement':text,'discharge_mode':mode,
          'negative_control':control or {'id':'none','reason':'Target observation or named assumption, not a local test discharge.'}}
    if reference:
        data.update(formal={'language':'reference','reference':reference},formal_label='stated')
    else:data['natural_language_only']='Ownership, memory order or application obligations exceed the closed predicate alphabet.'
    if owner:data['owner']=owner
    if evidence:data['evidence']=evidence
    return data

def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(yaml.safe_dump(data,sort_keys=False))

def main():
    library=ROOT/'library'
    provenance={'origin':{'intrinsic_specification':'Peter v1.1'},
        'intrinsic_specification':{**pin('docs/bfs-intrinsics-spec-yanru.md','repository'),'version':'1.1','commit':'0b56895','section':'3'},
        'hardware_candidate':{**pin('runs/bfs-maple-comparison-v0.1/case-01/handoffs/candidate-02/intrinsic-draft.yaml','repository'),'id':'gapbs_bfs_top_down_step--dx100-artifact-e4fc4af--read_execute','catalog_sha256':'adf17f3e114878ed0edbe55abb8ea219445fa2aef3c97e6c369230b796872fb0'},
        'catalog':{**pin('catalog/hardware-v0.1.yaml','repository'),'design':'dx100-artifact-e4fc4af','revision':'e4fc4afdf894f295442cef3604667a469fab8e62','claim_ids':['dxc-gather','dxc-range','dxc-stream','dxc-completion','dxc-byte-offset-domain']}}
    for operation,(memory,shape,hardware,package_op) in OPS.items():
        iid='intrinsic.dxc_'+operation
        lid='lowering.dxc_'+operation+'.dx100-mmio.1.0-e4fc4af'
        ref=pin('dx100/reference.hpp',symbol=operation)
        origin={**provenance,'operation_ids':[package_op] if package_op else [],'requirement_ids':['dxc-observer','dxc-reuse','dxc-capacity']}
        intrinsic={'kind':'intrinsic','id':iid,'intrinsic_record':'dxc_'+operation,'provenance':origin,
            'signature':SIGNATURES[operation],
            'intent':'Realize '+operation.replace('_',' ')+' over the pinned DX100 hardware interface.',
            'caveats':['Functional-model certification is pre-check evidence only; it does not establish target visibility.'],
            'reference_semantics':ref,'hardware_operations':hardware,
            'memory_footprint':FOOTPRINTS[operation],
            'completion':{'mode':'asynchronous_until_covering_wait','host_concurrency':'unknown','owner':'Eric',
                'assumptions':['A tile wait covers its producer and transitive dependencies, not unrelated operations or a store source.','CPU tile size/pointer reads do not wait.']},
            'lowerings':[lid],
            'clauses':[clause('result','postcondition','The lowering matches the pinned reference semantics on its declared inputs.','differential_test',{'id':PRIMARY_CONTROLS[operation][0],'check':PRIMARY_CONTROLS[operation][1]},ref)]}
        lower={'kind':'lowering','id':lid,'intrinsic':iid,'provenance':origin,'interface':INTERFACE,
            'location':{'path':'dx100/dxc_lowering.hpp','symbol':'__dxc_'+operation},
            'code_sha256':artifacts.file_hash(library/'dx100/dxc_lowering.hpp'),
            'build_defines':{'strict':['FUNC','GEM5','SWDB_STRICT'],'tile_sizes':[16384,1024],'core_count':4},
            'differential_test':{**pin('dx100/drivers/differential.cc'),'input_set':{'operation':operation,'seeds':[0],'tile_sizes':[16384,1024],'threads':4,'indices':['repeated','zero','tail'],'long_rows':operation=='range_loop'}},
            'clauses':intrinsic['clauses']}
        save(library/'intrinsics'/('dxc_'+operation+'.yaml'),intrinsic)
        save(library/'lowerings'/'dx100-mmio'/'1.0-e4fc4af'/('dxc_'+operation+'.yaml'),lower)
        record={'kind':'intrinsic','schema_version':'0.4','id':'dxc_'+operation,'name':'__dxc_'+operation,
            'status':'draft','created':'2026-10-03','updated':'2026-10-03','interface':INTERFACE,
            'hardware_operations':hardware,'memory_kind':memory,'address_shape':shape,'element_bits':32 if memory!='none' else None,'lanes':None,
            'library_entry':{'id':iid,'path':str((library/'intrinsics'/('dxc_'+operation+'.yaml')).relative_to(ROOT)),'content_sha256':artifacts.digest(intrinsic)},
            'provenance':[{'id':'dx100-source','kind':'source_code','description':'Pinned DX100 e4fc4af interface and independent reference semantics; no performance claim.','uri':'https://github.com/arkhadem/DX100/blob/e4fc4afdf894f295442cef3604667a469fab8e62/benchmarks/API/MAA_gem5.hpp'}]}
        save(ROOT/'records/intrinsics'/('dxc_'+operation+'.yaml'),record)
    clauses=[
        clause('L1','legality','Continuation emits exactly the nested CSR loop vertex pairs.','differential_test',{'id':'dropped_continuation','check':'frontier_size_equality'},pin('dx100/reference.hpp',symbol='range_loop')),
        clause('L2','legality','Within TDStep each parent changes at most once from its initial negative value to a vertex ID.','differential_test',{'id':'skipped_cas_recheck','check':'duplicate_frontier'}),
        clause('L3','legality','DX100 parent gathers return no value older than parent initialization.','assumed',owner='Eric',evidence='Pinned specification L3; parent-gather race case tests this assumption on each target run.'),
        clause('L4','legality','The CPU retains CAS, the labeled redundant parent store and queue push; frontier vertex and hint come from the same chunk.','structural',{'id':'skipped_cas_recheck','check':'duplicate_frontier'}),
        clause('L5','legality','DX100 reads of CPU-written queue, offsets and parent see stores preceding descriptor issue.','assumed',owner='Eric',evidence='Pinned specification L5; no target coherence guarantee is asserted.'),
        clause('frontier_threshold','legality','Frontier threshold is an integer of at least one.','runtime_guard',{'id':'chunk_off_by_one','check':'knob_range'}),
        clause('chunk_size','legality','Chunk size is positive and never exceeds the actual build tile capacity.','static_assertion',{'id':'chunk_off_by_one','check':'tile_truncation'}),
        clause('schedule','legality','Schedule is static or dynamic, with positive granularity.','structural',{'id':'shared_context','check':'schedule_range'}),
        clause('once_enqueue','preservation','Each discovered vertex is enqueued exactly once; trustworthy per-depth counts must match.','differential_test',{'id':'forged_frontier','check':'duplicate_frontier'}),
    ]
    kinds={'shared_context':'overlapping_pointer','skipped_cas_recheck':'double_claim','dropped_continuation':'dropped_operand','chunk_off_by_one':'dropped_operand','dropped_wait':'dropped_operand','read_before_wait':'dropped_operand','index_wrap':'dropped_operand','forged_frontier':'double_claim'}
    requirement_modes={'dxc-region-binding':'runtime_guard','dxc-widths':'static_assertion','dxc-validity':'differential_test','dxc-observer':'assumed','dxc-numerical':'not_applicable','dxc-reuse':'assumed','dxc-old-destination':'not_applicable','dxc-byte-offset':'runtime_guard','dxc-capacity':'static_assertion'}
    used=[i for i in OPS if i!='alu_scalar']
    contract={'kind':'rewrite_contract','id':'contract.bfs_read_offload','provenance':{**provenance,'intrinsic_specification':{**provenance['intrinsic_specification'],'section':'5'}},
        'pattern_key':[{'roles':['target'],'address_shapes':['stream'],'update_kind':'read'},
                       {'roles':['index','target'],'address_shapes':['stream','single_valued_indirect'],'update_kind':'read'},
                       {'roles':['index','offsets','target'],'address_shapes':['stream','single_valued_indirect','ranged_indirect'],'update_kind':'read'},
                       {'roles':['index','offsets','index','target'],'address_shapes':['stream','single_valued_indirect','ranged_indirect','single_valued_indirect'],'update_kind':'read'}],
        'strategies':['dx100_read_offload'],'uses_intrinsics':['intrinsic.dxc_'+op for op in used],'uses_library_operations':[],
        'clauses':clauses,'runtime_guards':[{'condition':'num_vertices <= 1073741823 && directed_edges <= 1073741823','fallback':'whole_pre_rewrite_BFS_call'},{'condition':'omp_threads <= build.core_count','fallback':'whole_pre_rewrite_BFS_call'}],
        'knobs':[{'name':'frontier_threshold','default':64,'range':{'min':1,'max':2147483647},'origin':'Peter v1.1 section 5','legality_clause':'frontier_threshold'},
                 {'name':'chunk_size','default':'build.tile_size','range':{'min':1,'max':65535,'upper_bound':'build.tile_size'},'origin':'Peter v1.1 section 5 with E4','legality_clause':'chunk_size'},
                 {'name':'schedule','default':'dynamic','range':{'choices':['dynamic','static']},'origin':'Peter v1.1 section 5','legality_clause':'schedule'},
                 {'name':'schedule_granularity','default':1,'range':{'min':1,'max':2147483647},'origin':'Peter v1.1 section 5','legality_clause':'schedule'}],
        'preservation_obligations':['once_enqueue'],'correctness_check':{'kernel':'gapbs-bfs','application':'dx100-gapbs','symbol':'BFSVerifier','scope':'full BFS call; target-bound check remains gem5'},
        'execution_witness':{'functional':'accelerated_chunks > 0 whenever scalar frontier reaches frontier_threshold','gem5':{'case':'read_only_executed','stream_min':1,'range_min':1,'indirect_min':1,'alu':0,'indirect_stores':0,'equation':'indirect = 3 * range - stream'}},
        'negative_controls':[{'id':n,'kind':k,'check':'named BFS correctness, preservation or strict-layer check'} for n,k in kinds.items()],
        'requirement_map':[{'hardware_candidate':provenance['hardware_candidate']['id'],'operation_ids':['dxc-gather','dxc-ranged-gather','dxc-stream_load'],'requirement_id':n,'discharge_mode':m,'reason':'RMW and returned old values are not used.' if m=='not_applicable' else 'Bound to contract clauses and certified strict-layer checks; target assumptions remain assumed.'} for n,m in requirement_modes.items()],
        'l3_outcome':{'observed':'negative-hint CAS failures > 0 and l3_violations = 0; design stays assumed','refuted':'l3_violations > 0; separate CPU-parent-load contract required','inconclusive':'verifier failed without violation, or race count zero; diagnose before timed runs'},
        'fixes':['E1 per-thread context','E2 register handles','E3 session and region lifecycle','E4 chunk capacity','E5 covering wait and barriers'],
        'specification_notes':['Both count guards include 1073741823, one more than Peter section 5 code; this agrees with section 4 and Josh byte-offset requirement.','Parent store after successful CPU CAS is intentionally retained and redundant.']}
    save(library/'rewrite_contracts'/'bfs_read_offload.yaml',contract)
    (library/'library_operations').mkdir(exist_ok=True)
    print('Wrote 10 intrinsic/lowering pairs and the BFS contract; no certification or promotion implied.')
if __name__=='__main__':main()
