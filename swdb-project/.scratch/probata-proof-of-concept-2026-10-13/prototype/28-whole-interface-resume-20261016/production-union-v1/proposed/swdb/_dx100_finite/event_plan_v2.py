"""2026-10-16 ET. Inert finite TraceUnit precursor, never original-C++ admission.

Closed source-Plan events compose exact concrete model bodies. Input selection
and receiver premise receipts are not authority tokens. A future public registry
must independently resolve those owners against the same new0.2 entry.
"""
import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import stat

HEADERS=(('whole_value_backend_v1.h','c37481e56517d29729ffc83f2eb538cc5b5cb8ce5ab831babae3287cb332956f'),
    ('whole_adapters.h','e8efe60182d7fbd0d7c9f54c8fc6f70c235a91bd613cabd3be6ac893105c4a1a'),
    ('whole_value_builders_v1.h','88f6bd0d310e8a2a6ad522ae15fec32b9f32b4ed6d792a314e8a365e0118824e'),
    ('whole_closed_routes_v1.h','0168b2f78e0d5a6a6d42c8955ba45304533b8a0c63b92bebcabd50fd730969c7'))
HOOK_SHA='2de83f722c439c5a834f9b17549b979e24b3716d79170377bf8cbeafd7b07b50'
MMIO=(17179869184,17184063768)
MMIO_BOUNDARIES=(17179869184,17181966336,17184063488,17184063552,17184063616,17184063744,17184063768)
PREMISES=('software-tile-register-ownership','ordinary-object-cell-mapping','ordinary-live-allocation',
    'fresh-exclusive-quiescent-receiver','owned-MMIO-value-semantics','numeric-ABI-profile')
EVENTS={'critical_begin','critical_end','cpu_write','cpu_read','cpu_cas','tile_write','tile_read','reg_write',
    'stream_load','stream_store','wait_tile','assert_eq','assert_in','assert_pending','lifetime_end','logical_ready_query','observe_ready_store'}
U64=2**64-1

class Refused(ValueError):pass
def need(ok,message):
    if not ok:raise Refused(message)
def exact(value,keys,message):need(type(value) is dict and set(value)==set(keys),message)
def integer(value,low,high,message):need(type(value) is int and low<=value<=high,message);return value
def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def identifier(value):need(type(value) is str and re.fullmatch('[a-z][a-z0-9_]{0,47}',value),'closed finite identifier required');return value
def stable(value):return tuple(getattr(value,name) for name in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns'))

@dataclass(frozen=True)
class Pin:
    path:str
    bytes:int
    sha256:str
    @classmethod
    def parse(cls,value):
        exact(value,{'path','bytes','sha256'},'physical pin required')
        need(type(value['path']) is str and Path(value['path']).is_absolute(),'absolute physical path required')
        integer(value['bytes'],0,8*1024*1024,'bounded input required')
        need(type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['sha256']),'full physical SHA required')
        return cls(**value)
    def row(self):return {'path':self.path,'bytes':self.bytes,'sha256':self.sha256}

@dataclass(frozen=True)
class OwnedSelection:
    policy:Pin

@dataclass(frozen=True)
class PreparedTrace:
    c_text:str
    certificate_json:bytes
    draw_plan_json:bytes
    resource_profile_json:bytes
    anchors_json:bytes

class Inputs:
    def __init__(self):self.rows={}
    def read(self,row):
        selected=row if type(row) is Pin else Pin.parse(row)
        need(type(selected) is Pin,'typed physical input required')
        # Reparse typed selections too; construction alone grants no validation.
        Pin.parse(selected.row());path=Path(selected.path);before=path.lstat()
        need(path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode),'canonical physical regular input required')
        need(before.st_size==selected.bytes,'actual input extent differs from bounded selected extent')
        with path.open('rb') as stream:raw=stream.read(selected.bytes+1)
        need(stable(path.lstat())==stable(before) and len(raw)==selected.bytes and digest(raw)==selected.sha256,'input changed or hash differs')
        old=self.rows.get(selected.path);need(old is None or old==selected.row(),'conflicting physical identity')
        self.rows[selected.path]=selected.row();return raw
    def document(self,row):
        def pairs(items):
            out={}
            for key,value in items:need(key not in out,'duplicate Plan JSON key');out[key]=value
            return out
        return json.loads(self.read(row),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(Refused('nonfinite Plan JSON')))
    def recheck(self):
        for row in list(self.rows.values()):self.read(row)

def width(dtype):integer(dtype,0,3,'finite dtype domain');need(dtype in (0,3),'first finite profile is u32/u64 only');return 4 if dtype==0 else 8
def c64(value):integer(value,0,U64,'unsigned literal domain');return 'UINT64_C(%d)'%value

def preflight(plan,context):
    exact(plan,{'schema','id','objects','tiles','registers','events'},'closed finite Plan required')
    need(plan['schema'] in ('owned-finite-dx100-event-plan-1','owned-finite-dx100-event-plan-2'),'distinct finite Plan kind required');identifier(plan['id'])
    exact(context,{'schema','source_plan_sha256','entry_identity','entry_nodes','entry_events','quiescent','fresh_payload',
        'tile_owners','register_owners','regions','live_objects','owned_premises'},'closed owned receiver context required')
    need(context['schema']=='owned-finite-model-context-1' and context['quiescent'] is True and context['fresh_payload'] is True
        and type(context['entry_nodes']) is int and context['entry_nodes']==0 and type(context['entry_events']) is int and context['entry_events']==0,
        'explicit fresh/quiescent bookkeeping and payload premise required; no reset is emitted')
    for field in ('tile_owners','register_owners'):
        need(type(context[field]) is list and len(context[field])==32 and all(type(x) is int and x in (-1,0,1) for x in context[field]),'complete two-thread owner image required')
    objects={};spans=[];cells=set()
    need(type(plan['objects']) is list and 1<=len(plan['objects'])<=8,'bounded ordinary mapping required')
    for obj in plan['objects']:
        exact(obj,{'id','guest_base','physical_base','dtype','extent','base_cell'},'closed object mapping required');key=identifier(obj['id'])
        need(key not in objects,'duplicate object ID');w=width(obj['dtype']);extent=integer(obj['extent'],1,2,'fixed value-prefix extent')
        base=integer(obj['base_cell'],0,63,'ordinary cell ID');need(base+extent<=64,'ordinary capacity obligation')
        for field in ('guest_base','physical_base'):
            address=integer(obj[field],0,U64-w*extent,'nonwrapping object span');need(address%w==0,'aligned typed span required')
            need(address+w*extent<=MMIO[0] or address>=MMIO[1],'ordinary/MMIO alias refused')
            if field=='physical_base':
                line_begin=address//64*64;line_end=((address+w*extent+63)//64)*64
                need(line_end<=U64 and (line_end<=MMIO[0] or line_begin>=MMIO[1]),'ordinary full-line/MMIO alias refused')
            need(all(field!=oldfield or address+w*extent<=begin or address>=end for oldfield,begin,end in spans),'object alias/reuse needs a successor profile')
            spans.append((field,address,address+w*extent))
        new=set(range(base,base+extent));need(not cells&new,'ordinary cell identities overlap');cells|=new;objects[key]=obj
    need(type(context['live_objects']) is list and sorted(context['live_objects'])==sorted(objects),'separately owned entry lifetimes required')
    tiles={};registers={}
    need(type(plan['tiles']) is list and 1<=len(plan['tiles'])<=16,'bounded typed tile views required')
    need(type(plan['registers']) is list and 1<=len(plan['registers'])<=16,'bounded register views required')
    need(type(context['regions']) is list and 1<=len(context['regions'])<=256,'bounded region image required')
    for row in plan['tiles']:
        exact(row,{'id','index','dtype'},'closed typed tile view required');key=identifier(row['id']);w=width(row['dtype'])
        integer(row['index'],0,32-w//4,'typed physical tile domain');need(key not in tiles,'duplicate tile ID');tiles[key]=row
    for row in plan['registers']:
        exact(row,{'id','index'},'closed stream register view required');key=identifier(row['id']);integer(row['index'],0,31,'register ID')
        need(key not in registers,'duplicate register ID');registers[key]=row
    regions={}
    for region in context['regions']:
        exact(region,{'id','begin','end'},'closed region row required');rid=integer(region['id'],0,255,'region ID')
        need(rid not in regions and type(region['begin']) is int and type(region['end']) is int and 0<=region['begin']<region['end']<=U64,'valid unique region required')
        regions[rid]=region
    for rid in range(6):
        need(regions.get(rid)=={'id':rid,'begin':MMIO_BOUNDARIES[rid],'end':MMIO_BOUNDARIES[rid+1]},'owned source six-region MMIO image required')
    for obj in objects.values():
        begin=obj['guest_base'];end=begin+obj['extent']*width(obj['dtype'])
        found=[rid for rid,row in regions.items() if row['begin']<=begin<row['end']]
        need(found,'ordinary object base is unregistered');selected=min(found)
        need(regions[selected]['begin']<=begin and end<=regions[selected]['end'] and
            all(not(begin<row['end'] and row['begin']<end) for rid,row in regions.items() if rid<selected),'first-ID/F2 object envelope refused')
    need(type(plan['events']) is list and 1<=len(plan['events'])<=64,'closed finite event count')
    return objects,tiles,registers,regions,max(cells)+1

def render(plan,context):
    objects,tiles,registers,regions,cells=preflight(plan,context)
    lines=[];anchors=[];results={};commands={};query_results=set();live=set(objects);critical=None
    nodes=0;writes=0;loads=0;stores=0;issues=0;queries=0;costs=[]
    def emit(text):lines.append('  '+text)
    def result(key):
        identifier(key);need(key not in results,'result ID reused');name='dwe_value_%d'%len(results);results[key]=name;return name
    def ordinary(event):
        obj=objects[event['object']];need(obj['id'] in live,'ordinary use after lifetime end')
        lane=integer(event['lane'],0,obj['extent']-1,'typed ordinary element index');w=width(obj['dtype'])
        return obj,obj['base_cell']+lane,obj['physical_base']+lane*w,obj['physical_base']+(lane+1)*w
    def value(value,dtype=None):
        integer(value,0,(2**(width(dtype)*8)-1) if dtype is not None else U64,'typed scalar literal');return c64(value)
    for serial,event in enumerate(plan['events']):
        need(type(event) is dict and event.get('kind') in EVENTS,'unknown event/C/callback/query/claim/reset/assumption refused')
        kind=event['kind'];thread=integer(event.get('thread'),0,1,'literal thread0/1 required');cost=0
        anchor='finite.%s.event.%03d'%(plan['id'],serial);anchors.append({'id':anchor,'event_index':serial,'thread':thread,'kind':kind})
        emit('/* swdb-anchor '+anchor+'.before */')
        if kind=='critical_begin':
            exact(event,{'kind','thread'},'critical marker shape');need(critical is None,'nested critical block refused')
            critical=('dwe_frontier_%d'%serial,thread);emit('unsigned '+critical[0]+'=dxc_count;')
        elif kind=='critical_end':
            exact(event,{'kind','thread'},'critical marker shape');need(critical is not None and critical[1]==thread,'critical end without matching begin thread')
            emit('for(unsigned i=%s;i<dxc_count;++i) DXM_CHECK(!dxc_commands[i].pending || dxc_commands[i].access!=2,"finite-critical-pending-store");'%critical[0]);critical=None
        elif kind in ('cpu_write','cpu_read','cpu_cas'):
            extra={'value'} if kind=='cpu_write' else {'out'} if kind=='cpu_read' else {'expected','desired','out','expected_out'}
            exact(event,{'kind','thread','object','lane'}|extra,'closed ordinary event');obj,cell,begin,end=ordinary(event)
            args='%du,%du,%s,%s'%(thread,cell,c64(begin),c64(end))
            if kind=='cpu_write':emit('dxc_cpu_write(%s,%s);'%(args,value(event['value'],obj['dtype'])));writes+=1
            elif kind=='cpu_read':emit('uint64_t %s=dxc_cpu_read(%s);'%(result(event['out']),args))
            else:
                expected=result(event['expected_out']);emit('uint64_t %s=%s;'%(expected,value(event['expected'],obj['dtype'])))
                emit('uint64_t %s=dxc_cpu_cas(%s,&%s,%s);'%(result(event['out']),args,expected,value(event['desired'],obj['dtype'])));writes+=1
        elif kind in ('tile_write','tile_read'):
            exact(event,{'kind','thread','tile','lane'}|({'value'} if kind=='tile_write' else {'out'}),'closed tile event')
            tile=tiles[event['tile']];lane=integer(event['lane'],0,1,'fixed tile-prefix lane')
            args='%du,%du,%du,%du'%(thread,tile['index'],lane,tile['dtype'])
            if kind=='tile_write':emit('dxp_cpu_write_bits(%s,%s);'%(args,value(event['value'],tile['dtype'])));cost=1
            else:emit('uint64_t %s=dxp_cpu_read_bits(%s);'%(result(event['out']),args));cost=2
        elif kind=='reg_write':
            exact(event,{'kind','thread','register','value'},'closed int32 register write');reg=registers[event['register']]
            emit('dwi_set_reg(%du,1u,%du,%s);'%(thread,reg['index'],value(event['value'],0)));cost=1
        elif kind in ('stream_load','stream_store'):
            exact(event,{'kind','thread','object','tile','min','max','stride','command'},'closed typed stream event')
            obj=objects[event['object']];need(obj['id'] in live,'device ordinary use after lifetime end');tile=tiles[event['tile']]
            need(obj['dtype']==tile['dtype'],'typed route/object view mismatch');identifier(event['command']);need(event['command'] not in commands,'command ID reused')
            ids=[registers[event[key]]['index'] for key in ('min','max','stride')];need(len(set(ids))==3,'stream register roles must be distinct')
            footprint='dwe_fp_%d'%serial;mapping='dwe_map_%d'%serial;w=width(obj['dtype']);span=obj['extent']*w
            emit('struct dwi_footprint %s={%s,%s,%s,%s,%s,64u};'%(footprint,c64(obj['guest_base']),c64(obj['guest_base']),c64(obj['guest_base']+span),c64(obj['physical_base']),c64(obj['physical_base']+span)))
            emit('struct dxw_memory %s={%du,%du,%s,4096u};'%(mapping,obj['base_cell'],obj['extent'],c64(obj['guest_base'])))
            name='dwe_command_%d'%issues;commands[event['command']]=name
            emit('unsigned %s=dxw_call_maa_stream_%s(%du,%du,%s,%du,%du,%du,%du,-1,&%s,&%s);'%(name,
                'load' if kind=='stream_load' else 'store',thread,obj['dtype'],c64(obj['guest_base']),*ids,tile['index'],footprint,mapping))
            issues+=1
            if kind=='stream_load':loads+=1;cost=33+2*(w+10)
            else:stores+=1;cost=33+2*12
        elif kind=='logical_ready_query':
            need(plan['schema']=='owned-finite-dx100-event-plan-2','logical query requires explicit V2 Plan kind')
            exact(event,{'kind','thread','tile','out'},'closed logical query, absent original header')
            emit('uint64_t %s=dxc_get_tile_ready(%du);'%(result(event['out']),tiles[event['tile']]['index']));query_results.add(event['out']);queries+=1
        elif kind=='observe_ready_store':
            need(plan['schema']=='owned-finite-dx100-event-plan-2','logical observation requires explicit V2 Plan kind')
            exact(event,{'kind','thread','ready','command','object','lane','value'},'closed ready-result store observation')
            need(event['ready'] in query_results,'ready observation requires a preceding logical query result')
            obj,cell,begin,end=ordinary(event);ready=results[event['ready']];command=commands[event['command']]
            emit('DXM_CHECK(%s<=1u,"finite-ready-relation");'%ready)
            emit('if(%s) { DXM_CHECK(!dxc_commands[%s].pending,"finite-ready-relation"); DXM_CHECK(dxc_cpu_read(%du,%du,%s,%s)==%s,"finite-ready-visible"); } else DXM_CHECK(dxc_commands[%s].pending,"finite-ready-relation");'%(ready,command,thread,cell,c64(begin),c64(end),value(event['value'],obj['dtype']),command))
        elif kind=='wait_tile':
            exact(event,{'kind','thread','tile'},'closed explicit wait');emit('dwi_wait_ready(%du);'%tiles[event['tile']]['index'])
        elif kind in ('assert_eq','assert_in'):
            exact(event,{'kind','thread','result'}|({'value'} if kind=='assert_eq' else {'values'}),'closed property event')
            name=results[event['result']];values=[event['value']] if kind=='assert_eq' else event['values']
            need(type(values) is list and 1<=len(values)<=4,'bounded finite value-set property')
            emit('DXM_CHECK(%s,"finite-event-property");'%' || '.join('(%s==%s)'%(name,value(item)) for item in values))
        elif kind=='assert_pending':
            exact(event,{'kind','thread','command','value'},'closed pending property');want=integer(event['value'],0,1,'pending bit')
            emit('DXM_CHECK(dxc_commands[%s].pending==%du,"finite-pending-property");'%(commands[event['command']],want))
        elif kind=='lifetime_end':
            exact(event,{'kind','thread','object'},'closed lifetime end');obj=objects[event['object']];need(obj['id'] in live,'ordinary lifetime already ended')
            begin=obj['physical_base'];end=begin+obj['extent']*width(obj['dtype'])
            emit('for(unsigned i=0;i<dxc_count;++i) DXM_CHECK(!(dxc_commands[i].pending && dxc_commands[i].access && %s<dxc_commands[i].end && dxc_commands[i].begin<%s),"finite-object-lifetime-pending");'%(c64(begin),c64(end)));live.remove(obj['id'])
        emit('/* swdb-anchor '+anchor+'.after */');nodes+=cost;costs.append({'event_index':serial,'kind':kind,'node_upper_bound':cost})
    need(critical is None,'unclosed critical block');need(issues<=8,'finite command profile bound')
    events=writes+2*stores;need(events<=63,'bounded history/event profile');draws=max(1,2*loads+stores+queries)
    profile={'schema':'finite-whole-model-resource-profile-1','nodes_required':nodes,'node_limit':max(16,1<<nodes.bit_length()),
        'closure_nodes_required':0,'allocation_rule':'smallest power of two strictly above static nodes plus closure; minimum16',
        'entry_nodes':0,'ordinary_cells_required':cells,'ordinary_cell_capacity':64,'commands_required':issues,'command_limit':max(1,issues),
        'actions_required':2*stores,'action_limit':max(1,2*stores),'memory_events_upper_bound':events,'event_limit':max(1,events),
        'history_candidates_upper_bound':1+events,'history_limit':1+events,'draw_count':draws,'logical_query_count':queries,'per_event_node_obligations':costs,
        'cost_basis':'exact pinned stream builders with prefix2/condition=-1; register and tile byte capture<=2 nodes; no entry unsettled versions',
        'actual_compiler_size_or_RSS_claim':False}
    need(profile['node_limit']<=512 and draws<=256,'explicit finite node/draw profile exceeded')
    checks=['DXM_CHECK(dws_choice_used==0,"finite-owned-fresh-draw-cursor");',
        'DXM_CHECK(dxm_count==0 && dxm_event_count==0 && dxc_count==0 && !dxc_constructing && dxa_count==0,"finite-owned-quiescence");',
        'DXM_CHECK(dxp_count==0,"finite-owned-fresh-image");',
        'for(unsigned i=0;i<DXM_CELLS;++i) DXM_CHECK(!dxm_initialized[i],"finite-owned-uninitialized-memory");',
        'for(unsigned i=0;i<DXG_REGS*4;++i) DXM_CHECK(!dxg_image[i].initialized,"finite-owned-uninitialized-register");',
        'for(unsigned i=0;i<DXM_TILES;++i) DXM_CHECK(dxz_sizes[i]==UINT_MAX,"finite-owned-initial-size");']
    checks += ['DXM_CHECK(dxm_tile_owner[%d]==%d,"finite-owned-tile-owner");'%(i,x) for i,x in enumerate(context['tile_owners'])]
    checks += ['DXM_CHECK(dxg_owner[%d]==%d,"finite-owned-register-owner");'%(i,x) for i,x in enumerate(context['register_owners'])]
    for rid in range(256):
        row=regions.get(rid,{'begin':0,'end':0});checks.append('DXM_CHECK(dxr_regions[%d].begin==%s && dxr_regions[%d].end==%s,"finite-owned-region-image");'%(rid,c64(row['begin']),rid,c64(row['end'])))
    function='static uint64_t dwe_trace_program(void) {\n'+'\n'.join('  '+line for line in checks)+'\n'+'\n'.join(lines)+'\n  return UINT64_C(0);\n}\n'
    return function,profile,anchors

def prepare(selection):
    need(type(selection) is OwnedSelection,'typed externally owned selection required');reads=Inputs();policy=reads.document(selection.policy)
    exact(policy,{'schema','source_plan','context','receiver','entry','entry_id','headers','hook_producer','producer'},'closed finite selection policy')
    need(policy['schema']=='finite-trace-source-policy-1','distinct finite TraceUnit policy required')
    need(policy['producer']['path']==str(Path(__file__).resolve()),'executing finite producer physical identity required')
    reads.read(policy['producer'])
    plan=reads.document(policy['source_plan']);context=reads.document(policy['context']);receiver=reads.document(policy['receiver'])
    entry=reads.document(policy['entry']);need(type(policy['entry_id']) is str and policy['entry_id'],'future same-entry identity required')
    identity={'id':policy['entry_id'],'sha256':policy['entry']['sha256']}
    need(entry.get('kind')=='proof_semantics' and entry.get('target')=='dx100-mmio' and entry.get('contract_form')=='dx100-whole-interface-checked-body-1',
        'same checked-body entry snapshot required; public registry resolution remains mandatory')
    need(context['source_plan_sha256']==policy['source_plan']['sha256'] and context['entry_identity']==identity,'context belongs to another Plan/entry')
    premises=context['owned_premises'];need(type(premises) is list and len(premises)==len(PREMISES),'complete owned premise roles required')
    need({row.get('role') for row in premises}==set(PREMISES),'owned premise role census')
    for row in premises:
        exact(row,{'role','owner','rule'},'physical entry premise reference');need(row['owner']==identity and type(row['rule']) is str and row['rule'],'same-entry owned premise owner required')
    exact(receiver,{'schema','source_plan_sha256','context_sha256','entry_identity','owned_premises_sha256'},'separate receiver premise receipt')
    need(receiver=={'schema':'owned-finite-model-receiver-1','source_plan_sha256':policy['source_plan']['sha256'],
        'context_sha256':policy['context']['sha256'],'entry_identity':identity,'owned_premises_sha256':digest(canonical(premises))},'receiver/context/Plan binding differs')
    function,profile,anchors=render(plan,context)
    need(type(policy['headers']) is dict and set(policy['headers'])=={name for name,_ in HEADERS},'exact concrete body header membership')
    header_text=[]
    for name,sha in HEADERS:
        row=policy['headers'][name];need(row['sha256']==sha,'exact concrete body bytes required');raw=reads.read(row)
        need(not re.search(rb'^\s*#\s*include\s*"',raw,re.M),'unbound local include refused');header_text.append(raw.decode())
    hook_raw=reads.read(policy['hook_producer']);need(digest(hook_raw)==HOOK_SHA,'exact checked hook producer required')
    node=next(n for n in ast.parse(hook_raw).body if isinstance(n,ast.FunctionDef) and n.name=='hook_text')
    namespace={'need':need};exec(compile(ast.Module([node],type_ignores=[]),'<exact-owned-choice-hook>','exec'),namespace)
    prefix='\n'.join('#define %s %du'%(name,value) for name,value in [('DXM_NODES',profile['node_limit']),('DXM_CELLS',64),
        ('DXM_EVENTS',profile['event_limit']),('DXM_HISTORY',profile['history_limit']),('DXC_COMMANDS',profile['command_limit']),('DXA_ACTIONS',profile['action_limit'])])+'\n'
    text=prefix+namespace['hook_text'](profile['draw_count'])+'\n'.join(header_text)+'\n'+function
    draws={'schema':'finite-full-u32-draw-plan-1','count':profile['draw_count'],'scalar_type':'uint32_t','domain':[0,2**32-1],
        'independent':True,'draw_before_trace':True,'rows':[{'index':i,'c_lvalue':'dws_choice_table[%d]'%i,'anchor':'finite.draw.%03d'%i} for i in range(profile['draw_count'])],
        'budget_failure':'checked property; no assume/truncate/reset','actual_draws_supplied':False}
    reads.recheck()
    certificate={'date':'2026-10-16 ET','kind':'prospective-finite-whole-model-trace-unit-1','source_plan':policy['source_plan'],
        'context':policy['context'],'receiver':policy['receiver'],'same_entry':identity,'owned_premises':premises,
        'c_text_sha256':digest(text.encode()),'resource_profile_sha256':digest(canonical(profile)),'draw_plan_sha256':digest(canonical(draws)),
        'anchors_sha256':digest(canonical(anchors)),'physical_inputs':list(reads.rows.values()),
        'source_order':'literal finite sequential events with explicit thread0/1 tags','original_CPP_TU_or_native_correspondence':False,
        'ownership_or_initialization_granted':False,'reset_or_hidden_wait_or_assumption_emitted':False,
        'receiver_state_composition_required':True,'standalone_C_static_initialization_satisfies_context':False,
        'predicted_verdicts_conditional_on_resolved_owned_receiver':True,
        'future_receiver_prefix_node_event_and_draw_closure_required':True,
        'public_registry_premise_owner_resolution_required':True,'same_new_0_2_registry_TraceUnit_branch_required':True,
        'actual_compiler_native_solver_or_public_admission':False}
    return PreparedTrace(text,canonical(certificate),canonical(draws),canonical(profile),canonical(anchors))
