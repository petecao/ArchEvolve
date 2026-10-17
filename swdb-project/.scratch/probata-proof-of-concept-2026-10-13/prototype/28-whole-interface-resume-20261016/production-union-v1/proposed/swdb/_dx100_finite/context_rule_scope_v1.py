"""2026-10-16 Eastern. Fixed typed-route rule applicability; no authority.

Generic proof_semantics.record_assumptions remains unchanged. Callers must first
validate an exact SourceUnit/TraceUnit and its physical new0.2 entry. This module
checks the full normal record list and excludes only the opposing closed family.
"""
import hashlib
import json
import re

OWNER = 'ticket28 synthetic fixture harness'
TRUST = {'mmio_ordering': 'The pinned MMIO implements call semantics including ordering; its wait fence lacks a memory clobber, a portability note independent of candidate artifacts.', 'cross_core_filter': 'A DX100 store remains visible if the snoop filter drops its line before the write reaches L3.', 'cross_core_write_buffer': 'A DX100 store remains visible when L3 passes a write below it because no block can be allocated.', 'no_stale_cpu_copy': 'No stale CPU copy survives a DX100 store (owner Eric).', 'one_instance': 'All commands belong to one DX100 instance.'}
OWNED = {'compiler_source_projection': 'The selected compiler and complete original translation-unit observation support the admitted source, ABI, expression and CPU-memory projection under their exact pinned configuration.', 'numeric_runtime_profile': 'The selected signed-shift, IEEE rounding and unordered min/max runtime policies apply; every operation retains its ordinary numeric-domain checks.'}
SOURCE_CONTEXT = {'fresh-host': 'A fresh C++ program supplies the twelve observed static globals, with no intervening mutation before source entry.', 'exclusive-model-instance': 'This modeled trace exclusively controls the selected DX100 instance; all CPU/device interference is represented by the complete admitted trace.', 'quiescent-entry': 'The modeled trace starts quiescent, with no prior pending command, construction, history, software tile/register owner, or registered region; no device payload value is asserted.', 'valid-entry-metadata': 'Initial tile size/status metadata is in the selected valid/quiescent domain: Finished with an unknown size in 0..16384. No particular size, payload value, or payload initializedness is asserted.', 'ordinary-allocation': 'Ordinary local storage comes from the exact checked original automatic declaration and live scope; allocation origin is not exclusive ordinary-memory access ownership.', 'physical-runtime': 'The selected physical mapping, device configuration, compiler ABI, and numeric runtime policies apply to this trace under their exact pinned inputs.'}
FINITE_CONTEXT = {'software-tile-register-ownership': 'The selected finite facts give the separately established complete software tile/register ownership state at trace entry; representing it is not an allocation or new ownership grant.', 'ordinary-object-cell-mapping': 'The selected finite facts bind every ordinary object, cell, guest address, physical envelope, dtype and region consistently; no other alias or ordinary/MMIO overlap is admitted.', 'ordinary-live-allocation': 'The selected finite facts identify live ordinary allocations at entry; lifetime is separate from tile/register ownership and from the thread permitted to access ordinary memory.', 'fresh-exclusive-quiescent-receiver': 'This finite model scope exclusively represents a fresh uninitialized payload and quiescent entry with zero nodes, memory events, commands and actions; no prior activity is cleared or omitted from the selected trace.', 'owned-MMIO-value-semantics': 'The pinned concrete model bodies implement the selected owned DX100 MMIO value and ordering semantics for this finite trace; no original C++ or hardware-body equivalence is inferred.', 'numeric-ABI-profile': 'The selected finite facts bind the fixed numeric ABI/runtime profile; all original checked numeric domains remain properties rather than assumptions.'}
LOGICAL_RULE = 'finite_logical_ready'
LOGICAL_STATEMENT = 'The finite TraceUnit logical readiness query is absent the original header: zero may leave a counted command pending and one covers the counted tile commands. Neither answer is forced and no fairness or termination is assumed.'

SOURCE_IDS=frozenset('whole_context_'+name.replace('-','_') for name in SOURCE_CONTEXT)
FINITE_IDS=frozenset(['finite_context_'+name.replace('-','_') for name in FINITE_CONTEXT]+[LOGICAL_RULE])
COMMON_IDS=frozenset(TRUST)|frozenset(OWNED)
class Refused(ValueError):pass
def need(ok,message):
    if not ok:raise Refused(message)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(value):return hashlib.sha256(canonical(value)).hexdigest()

def _select(entry,normal_records,entry_id,entry_sha,route):
    need(type(entry) is dict and entry.get('id')==entry_id and entry.get('kind')=='proof_semantics'
        and entry.get('target')=='dx100-mmio' and entry.get('version')=='0.2'
        and entry.get('contract_form')=='dx100-whole-interface-checked-body-1', 'typed route requires its exact checked new 0.2 entry')
    need(type(entry_id) is str and re.fullmatch(r'semantics\.[a-z0-9_.-]+',entry_id)
        and type(entry_sha) is str and re.fullmatch('[0-9a-f]{64}',entry_sha),'full physical same-entry rule reference required')
    rows=entry.get('rules')
    need(type(rows) is list and all(type(row) is dict and type(row.get('id')) is str and row['id'] and '#' not in row['id'] for row in rows)
        and len({row['id'] for row in rows})==len(rows),'unique physical entry rules required')
    by_id={row['id']:row for row in rows}
    for name,statement in {**TRUST,**OWNED}.items():
        row=by_id.get(name)
        need(type(row) is dict and set(row)=={'id','statement','assumed','record_assumption'} and row['statement']==statement
            and row['record_assumption'] is True and type(row['assumed']) is dict and set(row['assumed'])=={'owner'}
            and type(row['assumed']['owner']) is str and row['assumed']['owner'].strip(), 'common MMIO/compiler/numeric trust must remain exact and recorded: '+name)
        if name in TRUST:need(row['assumed']['owner']=='Eric','common MMIO/visibility owner must remain Eric')
    for name,statement in SOURCE_CONTEXT.items():
        ident='whole_context_'+name.replace('-','_');row=by_id.get(ident)
        need(type(row) is dict and type(row.get('assumed')) is dict and type(row['assumed'].get('owner')) is str,'complete source context family required')
        owner=row['assumed']['owner']
        need(owner.strip() and canonical(row)==canonical(dict(id=ident,statement=statement+' Owner: '+owner+'.',assumed=dict(owner=owner),record_assumption=True)),'exact source context row differs: '+ident)
    present=FINITE_IDS&set(by_id)
    need(not present or present==FINITE_IDS,'partial finite family cannot be hidden from another route')
    if present:
        for name,statement in FINITE_CONTEXT.items():
            ident='finite_context_'+name.replace('-','_')
            need(canonical(by_id[ident])==canonical(dict(id=ident,statement=statement+' Owner: '+OWNER+'.',assumed=dict(owner=OWNER),record_assumption=True)),'exact fixed-owner finite row differs: '+ident)
        need(canonical(by_id[LOGICAL_RULE])==canonical(dict(id=LOGICAL_RULE,statement=LOGICAL_STATEMENT+' Owner: '+OWNER,assumed=dict(owner=OWNER),record_assumption=True)),'exact logical readiness row differs')
    need(not any((ident.startswith('whole_context_') and ident not in SOURCE_IDS)
        or (ident.startswith('finite_context_') and ident not in FINITE_IDS) or (ident.startswith('finite_logical_') and ident!=LOGICAL_RULE) for ident in by_id),'unknown conflicting context rule ID refuses')
    need(route in ('SourceUnit','TraceUnit') and (route!='TraceUnit' or present==FINITE_IDS),'closed typed route and complete applicable finite family required')
    expected=[dict(kind='proof_semantics',reference=dict(id=entry_id+'#'+row['id'],sha256=entry_sha),sentence=row['statement']) for row in rows if row.get('record_assumption') is True]
    need(type(normal_records) is list and canonical(normal_records)==canonical(expected),'complete unchanged normal entry#rule/full-SHA records required before selection')
    excluded=FINITE_IDS if route=='SourceUnit' else SOURCE_IDS
    selected=[record for row,record in zip([row for row in rows if row.get('record_assumption') is True],normal_records) if row['id'] not in excluded]
    retained={record['reference']['id'].split('#',1)[1] for record in selected}
    need(COMMON_IDS<=retained and (SOURCE_IDS if route=='SourceUnit' else FINITE_IDS)<=retained,'all shared trust and exact applicable context rules must remain')
    receipt=dict(schema='checked-typed-rule-scope-1',unit_kind=route,entry=dict(id=entry_id,sha256=entry_sha),
        selected_rule_ids=[record['reference']['id'].split('#',1)[1] for record in selected],excluded_rule_ids=[row['id'] for row in rows if row['id'] in excluded],
        normal_records_sha256=sha(normal_records),selected_records_sha256=sha(selected),common_rule_ids=sorted(COMMON_IDS),
        fixed_scope_only=True,owned_selection_and_physical_Library_validation_still_required=True,truth_granted=False)
    return selected,receipt

def source(entry,normal_records,entry_id,entry_sha):
    return _select(entry,normal_records,entry_id,entry_sha,'SourceUnit')

def finite(entry,normal_records,entry_id,entry_sha):
    return _select(entry,normal_records,entry_id,entry_sha,'TraceUnit')
