"""2026-10-16 Eastern. Metadata-only invariant rule superset; no authority.

Existing SourceUnit rules retain their original statements and owners. Appended
finite rules are invariant and apply to selected finite TraceUnit contexts.
The public route must resolve applicability; this module grants no receiver
truth, hardware refinement, Library selection or scientific acceptance.
"""
from dataclasses import dataclass
import hashlib
import json
import re

OWNER = 'ticket28 synthetic fixture harness'
SOURCE_PINS = {'source_validator': {'path': '/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/swdb/dx100_whole_checked.py', 'bytes': 13395, 'sha256': '0c8e0fb429a4a497821d20436d777870bc0608ec3dbe79d42eb5201ad5d23105'}, 'source_receiver': {'path': '/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/swdb/_dx100_whole/receiver_state_draws_v2.py', 'bytes': 34554, 'sha256': 'f6c19464a6587b4fbd4a6278dc66be97f1c4ab16d46b2db8cd6b804d41608a5f'}, 'finite_receiver': {'path': '/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/28-whole-interface-resume-20261016/finite-trace-public-v2/proposed/swdb/_dx100_finite/finite_owned_receiver_v4.py', 'bytes': 17678, 'sha256': '5c81a0940f61bf31bda5e7e12c5446bb98789592ca49452584fc0d7bf13b6408'}, 'finite_core': {'path': '/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/28-whole-interface-resume-20261016/finite-trace-public-v2/proposed/swdb/dx100_finite_trace.py', 'bytes': 21974, 'sha256': 'f3f0e05961f72214aac487d85514ce1963faff092b9c51d8b34a0d5fbbe4ca3c'}}
TRUST = {'mmio_ordering': 'The pinned MMIO implements call semantics including ordering; its wait fence lacks a memory clobber, a portability note independent of candidate artifacts.', 'cross_core_filter': 'A DX100 store remains visible if the snoop filter drops its line before the write reaches L3.', 'cross_core_write_buffer': 'A DX100 store remains visible when L3 passes a write below it because no block can be allocated.', 'no_stale_cpu_copy': 'No stale CPU copy survives a DX100 store (owner Eric).', 'one_instance': 'All commands belong to one DX100 instance.'}
OWNED = {'compiler_source_projection': 'The selected compiler and complete original translation-unit observation support the admitted source, ABI, expression and CPU-memory projection under their exact pinned configuration.', 'numeric_runtime_profile': 'The selected signed-shift, IEEE rounding and unordered min/max runtime policies apply; every operation retains its ordinary numeric-domain checks.'}
SOURCE_CONTEXT = {'fresh-host': 'A fresh C++ program supplies the twelve observed static globals, with no intervening mutation before source entry.', 'exclusive-model-instance': 'This modeled trace exclusively controls the selected DX100 instance; all CPU/device interference is represented by the complete admitted trace.', 'quiescent-entry': 'The modeled trace starts quiescent, with no prior pending command, construction, history, software tile/register owner, or registered region; no device payload value is asserted.', 'valid-entry-metadata': 'Initial tile size/status metadata is in the selected valid/quiescent domain: Finished with an unknown size in 0..16384. No particular size, payload value, or payload initializedness is asserted.', 'ordinary-allocation': 'Ordinary local storage comes from the exact checked original automatic declaration and live scope; allocation origin is not exclusive ordinary-memory access ownership.', 'physical-runtime': 'The selected physical mapping, device configuration, compiler ABI, and numeric runtime policies apply to this trace under their exact pinned inputs.'}
FINITE_CONTEXT = {'software-tile-register-ownership': 'The selected finite facts give the separately established complete software tile/register ownership state at trace entry; representing it is not an allocation or new ownership grant.', 'ordinary-object-cell-mapping': 'The selected finite facts bind every ordinary object, cell, guest address, physical envelope, dtype and region consistently; no other alias or ordinary/MMIO overlap is admitted.', 'ordinary-live-allocation': 'The selected finite facts identify live ordinary allocations at entry; lifetime is separate from tile/register ownership and from the thread permitted to access ordinary memory.', 'fresh-exclusive-quiescent-receiver': 'This finite model scope exclusively represents a fresh uninitialized payload and quiescent entry with zero nodes, memory events, commands and actions; no prior activity is cleared or omitted from the selected trace.', 'owned-MMIO-value-semantics': 'The pinned concrete model bodies implement the selected owned DX100 MMIO value and ordering semantics for this finite trace; no original C++ or hardware-body equivalence is inferred.', 'numeric-ABI-profile': 'The selected finite facts bind the fixed numeric ABI/runtime profile; all original checked numeric domains remain properties rather than assumptions.'}
LOGICAL_RULE = 'finite_logical_ready'
LOGICAL_STATEMENT = 'The finite TraceUnit logical readiness query is absent the original header: zero may leave a counted command pending and one covers the counted tile commands. Neither answer is forced and no fairness or termination is assumed.'

class Refused(ValueError):pass
def need(ok,message):
    if not ok:raise Refused(message)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def strict(raw):
    def pairs(items):
        out={}
        for key,value in items:need(key not in out,'duplicate entry JSON key');out[key]=value
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(Refused('nonfinite entry metadata')))

@dataclass(frozen=True)
class Assembly:
    entry_json:bytes
    certificate_json:bytes

def appended_rules():
    rows=[dict(id='finite_context_'+name.replace('-','_'),statement=statement+' Owner: '+OWNER+'.',
        assumed=dict(owner=OWNER),record_assumption=True) for name,statement in sorted(FINITE_CONTEXT.items())]
    rows.append(dict(id=LOGICAL_RULE,statement=LOGICAL_STATEMENT+' Owner: '+OWNER,assumed=dict(owner=OWNER),record_assumption=True))
    return rows

def prepare(original_entry):
    need(type(original_entry) is bytes and 0<len(original_entry)<=8388608,'bounded original physical entry bytes required')
    entry=strict(original_entry)
    need(type(entry) is dict and entry.get('kind')=='proof_semantics' and entry.get('target')=='dx100-mmio'
        and entry.get('version')=='0.2' and entry.get('contract_form')=='dx100-whole-interface-checked-body-1'
        and type(entry.get('formal_frame')) is int and entry['formal_frame']==1
        and type(entry.get('sequence')) is int and entry['sequence']==2
        and type(entry.get('id')) is str and re.fullmatch(r'semantics\.[a-z0-9_.-]+',entry['id']), 'existing checked new 0.2 entry required')
    rules=entry.get('rules')
    need(type(rules) is list and all(type(row) is dict and type(row.get('id')) is str and row['id'] and '#' not in row['id'] for row in rules)
        and len({row['id'] for row in rules})==len(rules),'unique original physical entry rule IDs required')
    need(not any(row['id'].startswith('finite_context_') or row['id']==LOGICAL_RULE for row in rules),'finite rule family already present; no replacement or duplicate append')
    by_id={row['id']:row for row in rules}
    for name,statement in {**TRUST,**OWNED}.items():
        row=by_id.get(name)
        need(type(row) is dict and set(row)=={'id','statement','assumed','record_assumption'} and row['statement']==statement
            and row['record_assumption'] is True and type(row['assumed']) is dict and set(row['assumed'])=={'owner'}
            and type(row['assumed']['owner']) is str and bool(row['assumed']['owner'].strip()),'complete existing source trust/owned rules required: '+name)
        if name in TRUST:need(row['assumed']['owner']=='Eric','preserved MMIO/visibility owner must remain Eric')
    for name,statement in SOURCE_CONTEXT.items():
        ident='whole_context_'+name.replace('-','_');row=by_id.get(ident)
        need(type(row) is dict and type(row.get('assumed')) is dict and type(row['assumed'].get('owner')) is str,'existing source context rule required: '+ident)
        owner=row['assumed']['owner'];need(bool(owner.strip()) and row==dict(id=ident,statement=statement+' Owner: '+owner+'.',assumed=dict(owner=owner),record_assumption=True),'exact original source context rule required: '+ident)
    appended=appended_rules();assembled=dict(entry,rules=rules+appended)
    encoded=canonical(assembled)+b'\n'
    # This is a canonical metadata inverse; the caller retains the original raw
    # bytes/hash separately, rather than pretending formatting was unchanged.
    inverse=dict(assembled,rules=assembled['rules'][:-len(appended)])
    need(canonical(inverse)==canonical(entry),'append-only entry metadata inverse failed')
    certificate=dict(schema='finite-entry-invariant-superset-1',date='2026-10-16 Eastern',entry_id=entry['id'],
        original=dict(bytes=len(original_entry),sha256=sha(original_entry),canonical_sha256=sha(canonical(entry))),
        assembled=dict(bytes=len(encoded),sha256=sha(encoded)),preserved_rule_count=len(rules),appended_rule_count=len(appended),
        preserved_rules_sha256=sha(canonical(rules)),appended_rules=appended,source_pins=SOURCE_PINS,
        original_other_fields_canonical_sha256=sha(canonical({key:value for key,value in entry.items() if key!='rules'})),
        canonical_append_inverse=True,existing_rules_and_owners_unchanged=True,
        finite_generic_owner=OWNER,construct_before_any_source_or_finite_context_receiver_hash=True,
        route_scopes={'whole_context_*':'selected original C++ SourceUnit receiver scope',
                     'finite_context_*':'selected finite TraceUnit owned prestate scope',LOGICAL_RULE:'finite absent-header logical query only; no fairness'},
        source_and_finite_scopes_must_not_be_read_as_unqualified_same_prestate=True,
        applicability_resolution_owned_selection_and_Library_selection_required=True,
        receiver_truth_or_ownership_grant=False,hardware_or_fairness_premise_added=False,actual_Library_or_public_acceptance=False)
    return Assembly(encoded,canonical(certificate)+b'\n')
