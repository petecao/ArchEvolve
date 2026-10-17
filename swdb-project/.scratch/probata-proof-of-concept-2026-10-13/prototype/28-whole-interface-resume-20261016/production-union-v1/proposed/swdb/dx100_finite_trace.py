"""Closed finite event-Plan public boundary; never an original-C++ SourceUnit."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import stat

from swdb import dx100_whole_checked as contracts, proof_semantics
from swdb._dx100_finite import event_plan_v2 as events, finite_owned_receiver_v4 as receiver, context_rule_scope_v1 as context_scope

KIND='dx100-whole-interface-finite-trace-1'
METHOD='method.dx100-finite-whole-trace-v1'
FUNCTION='dwe_finite_trace'
REACH='swdb_reach.finite_owned_entry'
NORMAL='finite.trace.normal_return'
MANIFEST='swdb-dx100-finite-trace-producers-1'
LOGICAL_RULE='finite_logical_ready'
LOGICAL_STATEMENT='The finite TraceUnit logical readiness query is absent the original header: zero may leave a counted command pending and one covers the counted tile commands. Neither answer is forced and no fairness or termination is assumed.'

def logical_rule(owner):
    need(type(owner) is str and bool(owner.strip()),'named logical-query premise owner required')
    return dict(id=LOGICAL_RULE,statement=LOGICAL_STATEMENT+' Owner: '+owner,assumed=dict(owner=owner),record_assumption=True)
# These literals are emitted only from the closed30-Plan source packet.
PLAN_DIGESTS = {
  "command_wrong_owner_negative": "296b0f74683772d2f267b7291e960c01105d3e139cd354c19f12323b416e9155",
  "covered_store_next_thread_load_positive": "d1ccefdb9fd8a54bf772bd7f17e7b7a2a86855749be61aa0f02a34c3b034928f",
  "critical_end_wait_positive": "68d5528cfc7f44adf5d02b99239c759f6a59d876642ce87e057b9f566f1da385",
  "critical_end_without_wait_negative": "b73ecb7ef9a9f8ab7da3087fbc61951bd2e812724dba5aabc39ba81057ad1c19",
  "different_region_noncover_negative": "efc0a2700fe81ad59b7fd75c2fefcacf84c0c8e720835908d6bbd0227eb151d6",
  "disjoint_owned_tiles_positive": "ae36f616b513a5a677661bd4a619a4ac286f101aa5795017d275b1685fb510b6",
  "history_exact_issue_negative": "84cb370c71aa617368228a7c05df3b6da603354f1e10da7fb4b4dd99e56f6403",
  "history_latest_positive": "0ad27216e1ca58439d3029af6c88da4ffd2ec20cd7931c81870314a327adb473",
  "other_thread_cpu_read_positive": "926b1bf35c7f96c8571803486d2f2de6a7a8e519f640340a49f87ed1a6745d3a",
  "outside_critical_store_positive": "b2687d59f5fc17752fea57d22c330c37654b54e8df9e8e6a5bebd17cba3968ed",
  "owned_tile_positive": "40d735c4f7883956a77f3dce5ec407908e479f14224cfed1a896002f50928974",
  "pair_command_half_negative": "f893dac430f7d8bbe698b194c7623a47c8b35c0696b94cbc062de4b238f2d8c1",
  "pair_cpu_half_read_negative": "742e68a82c0476ad3b04ddb6752253c7c980c4e29434278b1a018898bfc635ce",
  "pair_owned_positive": "aa9d3f1514827d93c5e001e3b64864b246ea993c55cc500c1b00012d0362e883",
  "pair_wrong_owner_negative": "7eeaf604657379cf02e3b306add00d3295b3c14d7c51988dc367b01cebe307bc",
  "pending_read_lifetime_end_negative": "e65b89c7fbbd48c70859c5ee7b03f711c08d77ba62122adfb46e3628d04b57e4",
  "pending_store_cpu_read_negative": "590dc6da6ccdff8f1b749aa5e402df5f8b74a547ea9344d9283f7b6498225b6c",
  "prior_cpu_store_old_value_negative": "c9002aa0a7d323ab48775428029f5a2b39e234852ca0cfcc4c1dae70e1024933",
  "prior_cpu_store_visible_positive": "3f4b0e2610af0d54b0aca992af025e31040d5fdb2af63ed0d1208a2ba4905126",
  "ready_always_one_negative": "68555608a25956d342769dd1726c67658348186ead36407ba55256d3d7f16495",
  "ready_always_zero_negative": "12ed75b658642517cbc5f68e641a07b758b6802dd86f9fed022c283e1c2c0cb5",
  "ready_cpu_read_negative": "28dace0fb7e154efc863fcc1ba121c2c03b7e46a6c1fabb221fadadb736d565a",
  "ready_relation_positive": "3aa45a8ca048dcf75860e323e214f989f7d085e5a87dd4bedd76a82a62c11a3f",
  "same_region_read_read_noncover_negative": "22515382071c46e9bb359d38c694cae7397e3f2798891281fcf4f3116a6fe129",
  "same_region_write_cover_positive": "ed855b3a6bf8dddc1b1974bc41b431b608e831a6cf95783bd26d64e1275623da",
  "u32_command_half_positive": "d57f50574cd91de01174c992b0ece694dafca1fb969c8cab7444029f0ae40840",
  "u32_cpu_half_read_positive": "6c9e0750689f2f33b6fbc75909ffcf0e5388592364369f8b7d97a21330a227b6",
  "u32_disjoint_half_positive": "883a041ac88d5ffe2ee40e645c8232678c79ffa7bf56922943fe4dac597ea110",
  "u64_second_half_conflict_negative": "624e14836cf42ea6e001faf64eff84464e36c8b82793c45a22e916a43a255b21",
  "wrong_owner_negative": "a6e7ffc3847c1cf6564a7efc66ae28fd76128169678521347a48cc2b71c8f816"
}
NATIVE_FAILURES={'finite-event-property','finite-pending-property','finite-critical-pending-store',
    'finite-ready-relation','finite-ready-visible','finite-object-lifetime-pending','tile-ownership','pending-tile-write','store-footprint-cpu-access'}
RESOURCE_FAILURES={'node-capacity','node-capacity-domain','evaluation-step-capacity','evaluation-stack-capacity',
    'memory-event-capacity','history-capacity','command-history-capacity','action-capacity','tile-image-capacity',
    'tile-image-capacity-domain','whole-choice-capacity','whole-choice-domain','swdb.oracle_capacity'}

class Refused(ValueError):pass

def need(ok,message):
    if not ok:raise Refused(message)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def strict(raw):
    def pairs(items):
        result={}
        for key,value in items:need(key not in result,'duplicate finite JSON key');result[key]=value
        return result
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(Refused('nonfinite finite JSON')))

def opaque_pin(row):
    """Physical compiler executables are streamed, never loaded as small JSON."""
    need(type(row) is dict and set(row)=={'path','bytes','sha256'} and type(row['bytes']) is int and 0<=row['bytes']<=2**30,'bounded opaque runtime pin required')
    path=Path(row['path']);before=path.lstat()
    need(path.is_absolute() and path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode) and before.st_size==row['bytes'],'canonical opaque runtime input differs')
    digest=hashlib.sha256();count=0
    with path.open('rb') as stream:
        while True:
            chunk=stream.read(min(1024*1024,row['bytes']-count+1))
            if not chunk:break
            count+=len(chunk);need(count<=row['bytes'],'opaque runtime input grew');digest.update(chunk)
    need(receiver.stable(path.lstat())==receiver.stable(before) and count==row['bytes'] and digest.hexdigest()==row['sha256'],'opaque runtime input changed')

@dataclass(frozen=True)
class Selection:
    library:object
    entry_id:str
    contract_id:str
    contract_sha256:str
    method_id:str

@dataclass(frozen=True)
class TraceUnit:
    selection:Selection
    case_id:str
    function:str
    model_text:str
    source_text:str
    certificate_json:bytes
    draw_rows_json:bytes
    profile_json:bytes
    input_pins:tuple
    @property
    def certificate(self):return strict(self.certificate_json)


def producer_paths():
    from swdb import dx100_finite_trace_adapter as adapter, cbmc_adapter, proof_setup, formal_frame, yamlio, cbmc_translator, c_lowering, rss_watchdog, stdlib_provenance, library, proof, level_rule, dx100_checked_source
    here=Path(__file__).resolve();package=here.parent/'_dx100_finite'
    modules=[here,Path(adapter.__file__),Path(events.__file__),Path(receiver.__file__),Path(proof_semantics.__file__),
        Path(contracts.__file__),Path(context_scope.__file__),Path(cbmc_adapter.__file__),Path(proof_setup.__file__),Path(formal_frame.__file__),Path(yamlio.__file__),
        Path(cbmc_translator.__file__),Path(c_lowering.__file__),Path(rss_watchdog.__file__),Path(stdlib_provenance.__file__),Path(library.__file__),Path(proof.__file__),Path(level_rule.__file__),package/'finite_checks_v1.py']
    modules += [package/'__init__.py',here.parent/'__init__.py',package/'whole_model_v3.py',package/'receiver_state_draws_basis_v2.py']
    own={('package/' if path.name=='__init__.py' and path.parent==here.parent else 'finite/' if path.name=='__init__.py' else '')+path.name:path for path in modules}
    # model_for imports the ordinary checked route even for this disjoint kind.
    # Bind that entire existing surface without executing its SourceUnit path.
    inherited={'checked-package/'+name:path for name,path in dx100_checked_source.producer_paths().items()}
    return {**inherited,**own}


def select_baseline(library,contract_id,data):
    unit=data.get('proof_unit') if type(data) is dict else None
    if type(unit) is not dict or unit.get('function')!=FUNCTION:
        need(not(type(data) is dict and 'finite_trace_selection' in data),'finite discriminator cannot fall back to original-source dispatch')
        return None
    need(set(unit)=={'source','function'} and type(unit['source']) is dict,'exact finite proof_unit required')
    need(type(data.get('finite_trace_selection')) is dict,'finite public contract lacks its selected composition policy')
    current=[(ident,row) for ident,row in proof_semantics.current(library).items() if row.get('target')=='dx100-mmio']
    need(len(current)==1 and contracts.checked(current[0][1]),'one current same new0.2 checked entry required')
    need(unit['source'].get('sha256') in PLAN_DIGESTS.values(),'unregistered finite Plan source')
    return Selection(library,current[0][0],contract_id,library.content_sha256(contract_id),METHOD)


def contract_check(library,data,unit=None):
    proof=data.get('proof_unit');need(type(proof) is dict and set(proof)=={'source','function'} and proof['function']==FUNCTION,'closed finite contract source/function required')
    need(not data.get('knobs') and not proof.get('array_domains'),'finite source has no arbitrary knobs or arrays')
    clauses=data.get('clauses');need(type(clauses) is list and len(clauses)==2,'one frame and one checked finite return clause required')
    for clause,ident,text in zip(clauses,('frame','result'),(r'assigns \everything;',r'ensures \result == 0;')):
        need(type(clause) is dict and clause.get('id')==ident and clause.get('proof_placement')=={'once':'self'}
            and clause.get('discharge_mode')=='runtime_guard' and clause.get('acsl')=={'text':text,'uses':[]},'finite contract cannot add assumptions or weaken its checked safety/return')
    if unit is not None:need(proof['source']['sha256']==unit.certificate['source_plan']['sha256'],'contract/source Plan differs')


def compose(selection):
    from swdb.library import Library
    from swdb import yamlio
    need(type(selection) is Selection and isinstance(selection.library,Library) and selection.method_id==METHOD,'actual Library selection and finite method required')
    library=selection.library;fresh=Library(library.root)
    need(not fresh.problems and canonical(fresh.get(selection.entry_id))==canonical(library.get(selection.entry_id))
        and canonical(fresh.get(selection.contract_id))==canonical(library.get(selection.contract_id)), 'current physical Library selection changed')
    candidates=[(key,row) for key,row in fresh.entries.items() if row.get('kind')=='proof_semantics' and row.get('target')=='dx100-mmio']
    maximum=max((row.get('sequence',0) for key,row in candidates),default=0)
    need([key for key,row in candidates if row.get('sequence',0)==maximum]==[selection.entry_id],'selected finite entry is no longer uniquely current')
    library=fresh;reads=receiver.Inputs()
    def physical(path):
        path=Path(path);before=path.lstat()
        need(path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode) and 0<=before.st_size<=8*1024*1024,'bounded canonical physical Library input required')
        with path.open('rb') as stream:raw=stream.read(before.st_size+1)
        need(receiver.stable(path.lstat())==receiver.stable(before) and len(raw)==before.st_size,'Library input changed while hashing')
        row=dict(path=str(path),bytes=before.st_size,sha256=sha(raw))
        return row,reads.read(row)
    entry=library.get(selection.entry_id);need(type(entry) is dict,'selected current entry disappeared');contracts.policy(library,entry)
    entry_pin,entry_raw=physical(library.files[selection.entry_id])
    need(canonical(strict(entry_raw))==canonical(entry),'finite profile requires the same physical JSON-subset Library entry, not a fixture snapshot')
    for row in [entry['checked_body']['design'],entry['checked_body']['source_policy'],*entry['checked_body']['components'],*entry['declaration_inventory']['sources']]:
        expected=contracts.pinned(library,row);selected,actual=physical(library.resolve(row))
        need(expected==actual,'same-entry design/interface/body/source-policy input changed')
    contract=library.get(selection.contract_id);contract_pin,contract_raw=physical(library.files[selection.contract_id])
    need(library.content_sha256(selection.contract_id)==selection.contract_sha256 and canonical(yamlio.load(Path(contract_pin['path'])))==canonical(contract),'selected public contract changed')
    contract_check(library,contract)
    policy_row=contract['finite_trace_selection'];policy_raw=contracts.pinned(library,policy_row)
    policy_pin,actual_policy=physical(library.resolve(policy_row));need(actual_policy==policy_raw,'finite policy physical resolution changed')
    policy=strict(policy_raw);need(type(policy) is dict and set(policy)=={'kind','composition','producers','runtime','owned_manifest'},'closed finite public selection required')
    need(policy['kind']==KIND,'source/TraceUnit kind differs')
    closure=producer_paths();manifest_raw=contracts.pinned(library,policy['producers'])
    manifest_pin,actual_manifest=physical(library.resolve(policy['producers']));need(manifest_raw==actual_manifest,'producer manifest changed while binding')
    manifest=strict(manifest_raw)
    need(type(manifest) is dict and set(manifest)=={'schema','files'} and manifest['schema']==MANIFEST and set(manifest['files'])==set(closure),'complete actual finite producer closure required')
    for name,path in closure.items():
        row=manifest['files'][name];need(row['path']==str(path.resolve()),'producer must pin its actual physical consumer');reads.read(row)
    composition_row=policy['composition'];need(type(composition_row) is dict,'exact owned composition pin required')
    composition_raw=reads.read(composition_row);composition=strict(composition_raw)
    package=Path(receiver.__file__).resolve().parent
    need(composition['composer']['path']==str(Path(receiver.__file__).resolve()) and composition['producer']['path']==str(Path(events.__file__).resolve()),'fixed promoted finite producer/composer only')
    need(composition['receiver_basis']['path']==str(package/'receiver_state_draws_basis_v2.py'),'fixed one-shot receiver basis required')
    prepared=receiver.prepare(receiver.OwnedSelection(receiver.Pin.parse(composition_row)))
    binding=strict(prepared.certificate_json)
    for row in binding['physical_inputs']:reads.read(row)
    trace_policy=strict(reads.read(binding['trace_policy']));plan=strict(reads.read(trace_policy['source_plan']))
    need(plan['id'] in PLAN_DIGESTS and trace_policy['source_plan']['sha256']==PLAN_DIGESTS[plan['id']],'exact registered finite Plan bytes required')
    if plan['schema']=='owned-finite-dx100-event-plan-2':
        matches=[row for row in entry['rules'] if row.get('id')==LOGICAL_RULE]
        need(len(matches)==1 and canonical(matches[0])==canonical(logical_rule(binding['selected_owner'])), 'logical query requires its exact same-entry named owned rule')
    source=contract['proof_unit']['source'];source_raw=contracts.pinned(library,source)
    source_pin,actual_source=physical(library.resolve(source))
    need(source_raw==actual_source==reads.read(trace_policy['source_plan']) and source_pin==trace_policy['source_plan'], 'same canonical physical contract Plan bytes required')
    need(trace_policy['entry']==entry_pin and binding['same_entry']==dict(id=selection.entry_id,sha256=entry_pin['sha256']),'composition cannot replace real selected Library entry')
    owned_raw=contracts.pinned(library,policy['owned_manifest']);owned_pin,actual_owned=physical(library.resolve(policy['owned_manifest']))
    need(owned_raw==actual_owned,'physical owned selection receipt differs');owned=strict(owned_raw)
    need(type(owned) is dict and set(owned)=={'schema','owner','same_entry','contexts'} and owned['schema']=='finite-public-owned-contexts-1'
        and owned['owner']==binding['selected_owner'] and canonical(owned['same_entry'])==canonical(binding['same_entry'])
        and type(owned['contexts']) is dict and set(owned['contexts'])==set(PLAN_DIGESTS),'complete external selected owner/context manifest required')
    need(canonical(owned['contexts'][plan['id']])==canonical(dict(source_plan_sha256=trace_policy['source_plan']['sha256'],
        context_sha256=trace_policy['context']['sha256'],facts_sha256=binding['owned_facts_sha256'])),'exact selected context/facts identity differs from owned manifest')
    need(trace_policy['hook_producer']['path']==str(package/'whole_model_v3.py'),'exact promoted choice-hook input required')
    by_name={Path(row['path']).name:row for row in entry['checked_body']['components']}
    for name,row in trace_policy['headers'].items():
        target=by_name[name];need(row['path']==str(Path(library.resolve(target)).resolve()) and row['sha256']==target['sha256'],'finite bodies differ from same checked-entry components')
    normal_assumptions=proof_semantics.record_assumptions(library,selection.entry_id,entry_pin['sha256'])
    expected_assumptions,rule_scope=context_scope.finite(entry,normal_assumptions,selection.entry_id,entry_pin['sha256'])
    need(canonical(binding['record_assumptions'])==canonical(expected_assumptions),'finite assumptions differ from normal physical entry#rule producer')
    need(canonical(binding['rule_scope'])==canonical(rule_scope),'owned composer and public TraceUnit rule applicability differ')
    profile=strict(reads.read(composition['prepared']['profile']));draws=strict(prepared.draw_binding_json)
    rows=[dict(name='finite_choice_'+str(row['index']),role='finite-model-choice',ctype='uint32_t',c_lvalue=row['c_lvalue']) for row in draws['rows']]
    source_text=wrapper(profile['draw_count'])
    runtime_raw=contracts.pinned(library,policy['runtime']);runtime_pin,actual_runtime=physical(library.resolve(policy['runtime']))
    need(runtime_raw==actual_runtime,'runtime selector changed while binding')
    runtime=strict(runtime_raw);need(type(runtime) is dict and set(runtime)=={'compiler_wrapper','compiler_driver','numeric_runtime_receipt'},'closed selected runtime roles required')
    for row in runtime.values():opaque_pin(row)
    reads.recheck()
    for row in runtime.values():opaque_pin(row)
    cert=dict(kind=KIND,case_id=plan['id'],source_plan=trace_policy['source_plan'],entry=entry_pin,contract=contract_pin,public_policy=policy_pin,
        composition=composition_row,composition_certificate_sha256=sha(prepared.certificate_json),owned_selection=binding['owned_selection'],owned_manifest=owned_pin,
        record_assumptions=expected_assumptions,rule_scope=rule_scope,model_digest=sha(prepared.c_text.encode()),source_digest=sha(source_text.encode()),
        draw_rows_sha256=sha(canonical(rows)),resource_profile_sha256=sha(canonical(profile)),runtime=runtime,producer_manifest=policy['producers'],
        reachability='owned receiver and all independent draws before Plan events; no end/fairness or original C++ claim',
        native_scope='exact generated abstract model execution/replay, not independent source-C++ equivalence',actual_runtime_or_public_admission=False)
    return TraceUnit(selection,plan['id'],FUNCTION,prepared.c_text,source_text,canonical(cert),canonical(rows),canonical(profile),tuple(reads.rows.values())+tuple(runtime.values()))


def wrapper(draw_count):
    need(type(draw_count) is int and 1<=draw_count<=256,'closed full-u32 draw count')
    return ('static uint64_t '+FUNCTION+'(void) {\n  dwe_prepare_owned_receiver();\n#if defined(SWDB_NATIVE)\n'
        '  for(unsigned i=0;i<%du;++i) printf(" input finite_choice_%%u=%%llu",i,(unsigned long long)dws_choice_table[i]);\n'%draw_count+
        '#endif\n  SWDB_REACH("'+REACH+'");\n  return dwe_trace_program();\n}\n')


def recheck(unit):
    need(type(unit) is TraceUnit,'finite descriptor required; SourceUnit cannot be substituted')
    fresh=compose(unit.selection)
    need(fresh==unit,'finite selected inputs/model/draw/profile changed after preparation')
    return fresh


def record_assumptions(unit):
    recheck(unit)
    normal=proof_semantics.record_assumptions(unit.selection.library,unit.selection.entry_id,unit.certificate['entry']['sha256'])
    selected,scope=context_scope.finite(unit.selection.library.get(unit.selection.entry_id),normal,unit.selection.entry_id,unit.certificate['entry']['sha256'])
    need(canonical(scope)==canonical(unit.certificate['rule_scope']),'typed finite rule scope changed after preparation')
    return selected


def checked_unit_format(library,contract_id,data):
    try:
        selected=select_baseline(library,contract_id,data)
        if selected is None:return None
        contract_check(library,data);compose(selected);return []
    except (ValueError,OSError,TypeError,KeyError,AttributeError) as error:return [str(error)]

def lowering_for(library,unit):
    if type(unit) is not dict or unit.get('function')!=FUNCTION:return None
    from swdb import c_lowering
    matches=[(ident,row) for ident,row in library.entries.items() if canonical(row.get('proof_unit'))==canonical(unit)]
    need(len(matches)==1,'one exact finite public contract owns this source Plan')
    ident,row=matches[0]
    return c_lowering.Lowering(**lowering_fields(compose(select_baseline(library,ident,row))))


def lowering_fields(unit):
    recheck(unit)
    return dict(function=FUNCTION,text=unit.source_text,anchors=(),declaration='#include <stdint.h>\nuint64_t '+FUNCTION+'(void);\n',parameters=(),
        source_sha256=unit.certificate['source_plan']['sha256'],tool=dict(kind=KIND),whole_source=unit)


def model_fields(unit):
    recheck(unit);functions=tuple(sorted(set(re.findall(r'^(?:static\s+)?[A-Za-z_][\w\s\*]*?\b([A-Za-z_]\w*)\s*\([^;{]*\)\s*\{',unit.model_text,re.M))))
    need(FUNCTION not in functions and {'dwe_trace_program','dwe_prepare_owned_receiver','dxm_cover','dxm_cpu_write','dxm_device_write'}<=set(functions),'exact finite/model function closure required')
    return dict(entry=unit.selection.entry_id,sha256=unit.certificate['entry']['sha256'],calls=(),queries=(),c_text=unit.model_text,
        functions=functions,unwind=20*strict(unit.profile_json)['node_limit']+1,tile_objects=())
