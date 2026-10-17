"""2026-10-16 ET. Pure finite owned-context representation; not authority.

The public caller must select/validate the same actual Library entry. This
module resolves its six physical entry#rule references and records assumptions;
it cannot authorize an owner or turn a context receipt into a device fact.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import types

FINITE_SHA='d50ed0afe5861ceb4cacfd070f40fceebfb3475d51ea98fc28d111cc54341ec4'
RECEIVER_BASIS_SHA='f6c19464a6587b4fbd4a6278dc66be97f1c4ab16d46b2db8cd6b804d41608a5f'
RULE_SCOPE_BYTES=9371
RULE_SCOPE_SHA='23d5e4480c67557c201fc506fc3e25a23cdd9dd9eb63ff66cf1db14881b9e05b'
MODEL_KIND='dx100-whole-interface-checked-body-1'
FLAGS=('signed_shift_cpp17_arithmetic','ieee_binary_rn','alu_minmax_unordered_first')
RULE_STATEMENTS={
    'software-tile-register-ownership':'The selected finite facts give the separately established complete software tile/register ownership state at trace entry; representing it is not an allocation or new ownership grant.',
    'ordinary-object-cell-mapping':'The selected finite facts bind every ordinary object, cell, guest address, physical envelope, dtype and region consistently; no other alias or ordinary/MMIO overlap is admitted.',
    'ordinary-live-allocation':'The selected finite facts identify live ordinary allocations at entry; lifetime is separate from tile/register ownership and from the thread permitted to access ordinary memory.',
    'fresh-exclusive-quiescent-receiver':'This finite model scope exclusively represents a fresh uninitialized payload and quiescent entry with zero nodes, memory events, commands and actions; no prior activity is cleared or omitted from the selected trace.',
    'owned-MMIO-value-semantics':'The pinned concrete model bodies implement the selected owned DX100 MMIO value and ordering semantics for this finite trace; no original C++ or hardware-body equivalence is inferred.',
    'numeric-ABI-profile':'The selected finite facts bind the fixed numeric ABI/runtime profile; all original checked numeric domains remain properties rather than assumptions.',
}

class Refused(ValueError):pass

def need(ok,message):
    if not ok:raise Refused(message)
def exact(value,keys,message):need(type(value) is dict and set(value)==set(keys),message)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def stable(value):return tuple(getattr(value,key) for key in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns'))

@dataclass(frozen=True)
class Pin:
    path:str
    bytes:int
    sha256:str
    @classmethod
    def parse(cls,row):
        exact(row,{'path','bytes','sha256'},'physical pin fields required')
        need(type(row['path']) is str and Path(row['path']).is_absolute(),'absolute physical path required')
        need(type(row['bytes']) is int and 0<=row['bytes']<=8*1024*1024,'bounded exact byte count required')
        need(type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['sha256']),'full SHA256 required')
        return cls(**row)
    def row(self):return dict(path=self.path,bytes=self.bytes,sha256=self.sha256)

@dataclass(frozen=True)
class OwnedSelection:
    policy:Pin

@dataclass(frozen=True)
class PreparedOwnedTrace:
    c_text:str
    receiver_c_text:str
    certificate_json:bytes
    draw_binding_json:bytes
    integration_json:bytes

class Inputs:
    def __init__(self):self.rows={}
    def read(self,selection):
        row=selection.row() if type(selection) is Pin else selection;pin=Pin.parse(row)
        path=Path(pin.path);before=path.lstat()
        need(path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode),'canonical physical regular input required')
        need(before.st_size==pin.bytes,'actual input extent differs before read')
        with path.open('rb') as stream:raw=stream.read(pin.bytes+1)
        need(stable(path.lstat())==stable(before) and len(raw)==pin.bytes and sha(raw)==pin.sha256,'physical input changed or hash differs')
        previous=self.rows.get(pin.path);need(previous is None or previous==row,'conflicting selected physical identity')
        self.rows[pin.path]=row;return raw
    def document(self,row):
        def pairs(items):
            result={}
            for key,value in items:need(key not in result,'duplicate JSON key refused');result[key]=value
            return result
        return json.loads(self.read(row),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(Refused('nonfinite JSON refused')))
    def recheck(self):
        for row in list(self.rows.values()):self.read(row)


def captured_finite(raw,path):
    need(sha(raw)==FINITE_SHA,'exact reviewed finite producer required')
    # Execute captured, already pinned pure bytes; never reopen via an importer.
    name='_owned_finite_exact_d50ed0af';module=types.ModuleType(name);module.__file__=path
    sys.modules[name]=module
    exec(compile(raw,path,'exec'),module.__dict__)
    return module


def facts_for(plan,context,profile,draws,entry_id):
    fields=('schema','source_plan_sha256','entry_nodes','entry_events','quiescent','fresh_payload','tile_owners','register_owners','regions','live_objects')
    return dict(schema='finite-owned-prestate-facts-1',entry_id=entry_id,context={key:context[key] for key in fields},
        ordinary_objects=plan['objects'],tile_views=plan['tiles'],register_views=plan['registers'],
        numeric_flags={name:1 for name in FLAGS},resource_profile_sha256=sha(canonical(profile)),draw_plan_sha256=sha(canonical(draws)))


def rule_rows(owner):
    need(type(owner) is str and owner.strip()==owner and owner and len(owner)<=200,'named selected premise owner required')
    return [dict(id='finite_context_'+role.replace('-','_'),statement=statement+' Owner: '+owner+'.',
        assumed=dict(owner=owner),record_assumption=True) for role,statement in sorted(RULE_STATEMENTS.items())]

def rule_scope_pin():
    return dict(path=str(Path(__file__).resolve().with_name('context_rule_scope_v1.py')),bytes=RULE_SCOPE_BYTES,sha256=RULE_SCOPE_SHA)

def captured_rule_scope():
    selected=rule_scope_pin();raw=Inputs().read(selected)
    module=types.ModuleType('_finite_exact_rule_scope_'+RULE_SCOPE_SHA[:8]);module.__file__=selected['path']
    exec(compile(raw,selected['path'],'exec'),module.__dict__)
    return module


def resolve_rules(entry,entry_pin,entry_id,context,owner):
    need(type(entry_id) is str and re.fullmatch('[a-z][a-z0-9_.-]{0,127}',entry_id),'unambiguous selected entry identifier required')
    need(type(entry) is dict and entry.get('id')==entry_id and entry.get('version')=='0.2'
        and entry.get('kind')=='proof_semantics' and entry.get('target')=='dx100-mmio' and entry.get('contract_form')==MODEL_KIND,
        'same selected new0.2 checked-body entry required')
    rows=entry.get('rules')
    need(type(rows) is list and all(type(row) is dict and type(row.get('id')) is str and row['id'] and '#' not in row['id'] for row in rows)
        and len({row['id'] for row in rows})==len(rows),'unique physical entry rules required')
    by_id={row['id']:row for row in rows};wanted=rule_rows(owner)
    expected_roles=set(RULE_STATEMENTS)
    premises=context['owned_premises']
    need(type(premises) is list and len(premises)==len(expected_roles)
        and {row.get('role') for row in premises if type(row) is dict}==expected_roles,'complete resolved finite premise role set required')
    identity=dict(id=entry_id,sha256=entry_pin['sha256'])
    for premise in premises:
        role=premise['role'];ident='finite_context_'+role.replace('-','_')
        need(premise==dict(role=role,owner=identity,rule=ident),'context rule must name its same physical entry and exact fragment')
    for row in wanted:need(by_id.get(row['id'])==row,'unresolved or different recorded same-entry premise rule: '+row['id'])
    recorded=[]
    for row in rows:
        if row.get('record_assumption') is True:
            need(type(row.get('statement')) is str and row['statement'].strip(),'recorded entry rule needs its exact statement')
            recorded.append(dict(kind='proof_semantics',reference=dict(id=entry_id+'#'+row['id'],sha256=entry_pin['sha256']),sentence=row['statement']))
    # Validate the full normal producer output before choosing the fixed typed
    # family. All common trust and additional recorded noncontext rows remain.
    selected,scope=captured_rule_scope().finite(entry,recorded,entry_id,entry_pin['sha256'])
    return dict(assumptions=selected,rule_scope=scope)


def owned_selection_metadata(source_policy,prepared,identity,facts,owner):
    """Pinned selection identity, never Boolean authority for its truth."""
    return dict(schema='finite-owned-selection-2',owner=owner,same_entry=identity,
        source_plan=source_policy['source_plan'],context=source_policy['context'],receiver=source_policy['receiver'],
        trace_policy=prepared['policy'],trace_certificate=prepared['certificate'],resource_profile=prepared['profile'],
        draw_plan=prepared['draws'],owned_facts_sha256=sha(canonical(facts)),
        scope='externally selected owned finite-entry representation only')


def receiver_text(context,profile):
    budget=profile['draw_count']
    lines=['/* Fixed owned abstract-prestate representation; not a source/device operation or ownership grant. */',
        'static unsigned dwe_owned_receiver_entered;',
        'static void dwe_prepare_owned_receiver(void) {',
        '  SWDB_CHECK(dwe_owned_receiver_entered==0,"finite-receiver-single-entry");',
        '  SWDB_CHECK(DXM_NODES==%du && DXM_CELLS==64 && DXM_EVENTS==%du && DXM_HISTORY==%du && DXC_COMMANDS==%du && DXA_ACTIONS==%du,"finite-receiver-bound-profile");'%(profile['node_limit'],profile['event_limit'],profile['history_limit'],profile['command_limit'],profile['action_limit']),
        '  SWDB_CHECK(DXM_TILES==32 && DXG_REGS==32 && DXC_REGIONS==256 && DXP_VALUE_BOUND==2 && DXP_TILE_WORDS==16384,"finite-receiver-fixed-geometry");',
        '  SWDB_CHECK(dxm_count==0 && dxm_event_count==0 && dxc_count==0 && dxc_constructing==0 && dxa_count==0 && dxp_count==0 && dws_choice_used==0,"finite-receiver-untouched-bookkeeping");',
        '  for(unsigned i=0;i<DXM_CELLS;++i) SWDB_CHECK(!dxm_initialized[i],"finite-receiver-uninitialized-memory");',
        '  for(unsigned i=0;i<DXG_REGS*4;++i) SWDB_CHECK(!dxg_image[i].initialized,"finite-receiver-uninitialized-register");',
        '  for(unsigned i=0;i<DXC_COMMANDS;++i) SWDB_CHECK(!dxg_roles[i].bound,"finite-receiver-untouched-register-roles");',
        '  for(unsigned i=0;i<DXM_TILES;++i) SWDB_CHECK(dxm_tile_owner[i]==0 && dxz_sizes[i]==0,"finite-receiver-fresh-static-tile-ghosts");',
        '  for(unsigned i=0;i<DXG_REGS;++i) SWDB_CHECK(dxg_owner[i]==0,"finite-receiver-fresh-static-register-ghosts");',
        '  for(unsigned i=0;i<DXC_REGIONS;++i) SWDB_CHECK(!dxr_regions[i].begin && !dxr_regions[i].end,"finite-receiver-fresh-static-regions");',
        '  for(unsigned i=0;i<%du;++i) SWDB_CHECK(dws_choice_table[i]==0,"finite-receiver-fresh-static-draw-table");'%budget]
    lines+=['  SWDB_CHECK(dxt_runtime.%s==0,"finite-receiver-fresh-static-numeric-profile");'%flag for flag in FLAGS]
    lines+=['  dwe_owned_receiver_entered=1;',
        '  /* Materialize only the separately resolved owned prestate. No event calls or counter resets. */',
        '  for(unsigned i=0;i<DXM_TILES;++i) dxz_sizes[i]=UINT_MAX;']
    lines+=['  dxm_tile_owner[%d]=%d;'%(i,value) for i,value in enumerate(context['tile_owners'])]
    lines+=['  dxg_owner[%d]=%d;'%(i,value) for i,value in enumerate(context['register_owners'])]
    for region in sorted(context['regions'],key=lambda row:row['id']):
        lines+=['  dxr_regions[%d].begin=UINT64_C(%d); dxr_regions[%d].end=UINT64_C(%d);'%(region['id'],region['begin'],region['id'],region['end'])]
    lines+=['  dxt_runtime.%s=1u;'%flag for flag in FLAGS]
    lines+=['  for(unsigned i=0;i<%du;++i) dws_choice_table[i]=(uint32_t)swdb_next();'%budget,'}',
        'static uint64_t dwe_execute_owned_trace(void) {',
        '  dwe_prepare_owned_receiver();',
        '  return dwe_trace_program();','}']
    return '\n'.join(lines)+'\n'


def prepare(selection):
    need(type(selection) is OwnedSelection and type(selection.policy) is Pin,'typed selected composition policy required')
    reads=Inputs();reads.read(rule_scope_pin());policy=reads.document(selection.policy)
    exact(policy,{'schema','composer','producer','receiver_basis','prepared','entry_id','premise_owner','owned_selection'},'closed finite receiver composition policy')
    need(policy['schema']=='finite-owned-receiver-selection-2','distinct owned finite composition policy required')
    need(policy['composer']['path']==str(Path(__file__).resolve()),'executing owned composer physical identity required')
    reads.read(policy['composer'])
    raw=reads.read(policy['producer']);need(sha(raw)==FINITE_SHA,'frozen finite source producer differs')
    need(sha(reads.read(policy['receiver_basis']))==RECEIVER_BASIS_SHA,'reviewed one-shot receiver basis differs')
    prepared=policy['prepared'];exact(prepared,{'policy','c_text','certificate','draws','profile','anchors'},'exact five-artifact finite prepared surface required')
    expected={name:reads.read(row) for name,row in prepared.items() if name!='policy'}
    finite=captured_finite(raw,policy['producer']['path'])
    regenerated=finite.prepare(finite.OwnedSelection(finite.Pin.parse(prepared['policy'])))
    actual=dict(c_text=regenerated.c_text.encode(),certificate=regenerated.certificate_json,draws=regenerated.draw_plan_json,
        profile=regenerated.resource_profile_json,anchors=regenerated.anchors_json)
    for name in actual:need(expected[name]==actual[name],'prepared '+name+' differs from exact frozen regeneration')
    cert=json.loads(actual['certificate']);profile=json.loads(actual['profile']);draws=json.loads(actual['draws'])
    for row in cert['physical_inputs']:reads.read(row)
    source_policy=reads.document(prepared['policy']);plan=reads.document(source_policy['source_plan']);context=reads.document(source_policy['context']);entry=reads.document(source_policy['entry'])
    need(source_policy['producer']==policy['producer'],'executing producer/trace producer pin differs')
    need(policy['entry_id']==source_policy['entry_id'] and context['entry_identity']==cert['same_entry'],'same finite entry selection required')
    need(cert['receiver_state_composition_required'] is True and cert['ownership_or_initialization_granted'] is False
        and cert['actual_compiler_native_solver_or_public_admission'] is False,'retained precursor composition boundary differs')
    facts=facts_for(plan,context,profile,draws,policy['entry_id'])
    resolution=resolve_rules(entry,source_policy['entry'],policy['entry_id'],context,policy['premise_owner'])
    assumptions=resolution['assumptions']
    selected_facts=reads.document(policy['owned_selection'])
    need(canonical(selected_facts)==canonical(owned_selection_metadata(source_policy,prepared,cert['same_entry'],facts,policy['premise_owner'])),
        'exact externally owned selection/context/receiver/facts binding differs')
    code=receiver_text(context,profile);complete=regenerated.c_text+'\n'+code
    draw_binding=dict(schema='finite-owned-trace-draw-binding-1',count=draws['count'],domain=draws['domain'],scalar_type='uint32_t',
        independent=True,rows=draws['rows'],source='one distinct swdb_next oracle slot cast to uint32 per row',
        order=['one-shot static-scope checks','owned prestate representation','all ordered independent draws','one finite trace invocation'],
        draw_plan_sha256=sha(actual['draws']),fatal_capacity_retained=True,actual_draws_or_native_replay_supplied=False)
    integration=dict(schema='finite-owned-trace-integration-3',unit_kind='TraceUnit',original_CPP_SourceUnit=False,
        entry_id=policy['entry_id'],before_trace='dwe_prepare_owned_receiver();',combined_entry='dwe_execute_owned_trace()',
        unchanged_trace_c_sha256=sha(actual['c_text']),receiver_c_sha256=sha(code.encode()),resource_profile=profile,
        registry='The actual public Library must validate/select this same physical new0.2 entry and retain every emitted entry#rule assumption; this module does not establish registry authority.',
        harness='Bind these full-u32 Plan rows, checked failure semantics, method/replay and one fresh process per invocation before public/native use.',
        receiver_scope='Representation of separately owned abstract prestate, not actual MMIO actions; unused source-host allocation counters are outside this closed event fragment.',
        source_lifetime='The exact frozen finite producer admits only fixed live object IDs and refuses all subsequent uses after lifetime_end; no original C++ local lifetime claim.',
        actual_public_compiler_native_solver_admission=False)
    reads.recheck()
    certificate=dict(schema='finite-owned-trace-composition-certificate-3',date='2026-10-16 ET',composition_policy=selection.policy.row(),rule_scope=resolution['rule_scope'],
        trace_certificate=prepared['certificate'],trace_policy=prepared['policy'],same_entry=cert['same_entry'],
        owned_facts=facts,owned_facts_sha256=sha(canonical(facts)),owned_selection=policy['owned_selection'],
        selected_owner=policy['premise_owner'],selected_metadata=selected_facts,record_assumptions=assumptions,
        source_body_headers_and_hook_preserved=True,source_c_sha256=sha(actual['c_text']),receiver_c_sha256=sha(code.encode()),
        combined_c_sha256=sha(complete.encode()),resource_profile_sha256=sha(actual['profile']),closure_nodes_required=0,
        draw_binding_sha256=sha(canonical(draw_binding)),integration_sha256=sha(canonical(integration)),physical_inputs=list(reads.rows.values()),
        static_scope_representation_only=True,ownership_or_payload_grant=False,reset_hidden_wait_assumption_or_event_call=False,
        public_library_selection_and_entry_validation_required=True,actual_native_CPP_or_hardware_correspondence=False,
        actual_compiler_solver_public_admission=False)
    return PreparedOwnedTrace(complete,code,canonical(certificate),canonical(draw_binding),canonical(integration))
