"""2026-10-16 ET. Source-only exact semantic proposal manifest, no execution."""
import ast
import hashlib
import json
from pathlib import Path
import stat
HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
STABLE=('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns')
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(value):return hashlib.sha256(value).hexdigest()
reads={}
def pin(path):
    before=path.lstat()
    assert path.is_absolute() and path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode) and before.st_size<=1048576
    with path.open('rb') as handle:raw=handle.read(before.st_size+1)
    after=path.lstat()
    assert all(getattr(before,key)==getattr(after,key) for key in STABLE) and len(raw)==before.st_size
    result={'path':str(path),'bytes':len(raw),'sha256':sha(raw)}
    reads[str(path)]=(result,raw)
    return result
rows=[]
for name in ('base-source.py','enum_inlet.py','build_proposal_v1.py','proposed/compiler_unit_adapter_v4.py','exact-delta.json',
    'proposed.patch','test_enum_repair_v1.py','pure-controls-v1.log','pure-controls-v1-fixed.log','pure-controls-v2.log',
    'actual-offline-reader-controls-v1.json','actual-offline-reader-controls-v2.json','PLAN.md','freeze_packet_v1.py'):
    rows.append({'role':'owned/'+name,'pin':pin(HERE/name)})
for relative in ('abi-enum-diagnostic-v1/census_abi_enums_v1.py','abi-enum-diagnostic-v1/actual-complete-enum-census-v1.json',
    'abi-small-artifact-transfer-v1/verified-transfer.json','abi-small-artifact-transfer-v1/original-first-ABI.json',
    'abi-small-artifact-transfer-v1/original-memory-ABI.json','abi-small-artifact-transfer-v1/original-first-probe.cpp',
    'abi-small-artifact-transfer-v1/original-memory-probe.cpp','abi-role-transport-v2/source-packet-v2.json',
    'abi-role-transport-v2/abi_role_transport_v1.py','compiler-ABI-value-primary-v1/fetch-provenance-v1.json',
    'compiler-duplicate-census-v1/primary/fetch-provenance-v1.json','compiler-duplicate-census-v1/primary/release-commit-provenance-v1.json'):
    rows.append({'role':'basis/'+relative,'pin':pin(WHOLE/relative)})
policy_path=WHOLE/'abi-retained-replay-v1/controls/policy.json'
rows.append({'role':'exact admitted replay policy','pin':pin(policy_path)})
policy=json.loads(reads[str(policy_path)][1])
for key in ('legacy','normalizer','tokens','binder'):
    selected=policy['controls'][key]
    path=policy_path.parent/Path(selected['path']).name
    actual=pin(path)
    assert actual['bytes']==selected['bytes'] and actual['sha256']==selected['sha256']
    rows.append({'role':'exact admitted replay '+key,'pin':actual})
primary_specs=[('compiler-duplicate-census-v1/primary/JSONNodeDumper.cpp',[(235,240),(1443,1457),(1500,1503)],
    'Emits ConstantExpr own APValue/type, APValue pretty string, and castKind.'),
    ('compiler-ABI-value-primary-v1/APValue.cpp',[(703,733)],'Boolean APValue uses true/false spelling; integral APValue prints its own integer.'),
    ('compiler-ABI-value-primary-v1/OperationKinds.def',[(194,199)],'IntegralCast denotes integral conversion, not arbitrary expression evaluation.'),
    ('compiler-ABI-value-primary-v1/SemaDecl.cpp',[(20824,20890)],'Enum completion may wrap its original initializer in an integral cast and change declaration type.')]
spans=[]
for relative,ranges,claim in primary_specs:
    physical=pin(WHOLE/relative)
    lines=reads[physical['path']][1].splitlines(keepends=True)
    spans.append({'source':physical,'ranges':[{'first_line':start,'last_line':end,
        'sha256':sha(b''.join(lines[start-1:end]))} for start,end in ranges], 'supported_interpretation':claim})
evidence={'schema':'exact-primary-ABI-value-source-spans-1','date':'2026-10-16 ET','release':'llvmorg-22.1.8',
    'commit':'ca7933e47d3a3451d81e72ac174dcb5aa28b59d1','spans':spans,
    'exact_probe_source_syntax_sha256':'c0f4f37ba62992b3de117f6117b134ad0ba663484c172ffa98081952f769bf34',
    'source_to_selected_binary_attestation_remains_TCB':True,'no_network_fetch_by_this_proposal':True}
(HERE/'primary-source-evidence-v1.json').write_bytes(canonical(evidence)+b'\n')
rows.append({'role':'owned/primary-source-evidence-v1.json','pin':pin(HERE/'primary-source-evidence-v1.json')})
base=(HERE/'base-source.py').read_text();candidate=(HERE/'proposed/compiler_unit_adapter_v4.py').read_text()
changes=json.loads((HERE/'exact-delta.json').read_bytes())['changes']
assert len(changes)==5
inverse=candidate
for change in reversed(changes):
    assert inverse.count(change['new'])==1
    inverse=inverse.replace(change['new'],change['old'])
assert inverse==base and sha(base.encode())=='775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c'
def nodes(source):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
before=nodes(base);after=nodes(candidate)
unchanged=sorted(set(before)-{'observed_abi'})
assert all(before[key]==after[key] for key in unchanged)
controls=json.loads((HERE/'actual-offline-reader-controls-v2.json').read_bytes())
assert controls['tests']==11 and controls['failures']==controls['errors']==controls['skips']==0
for result,raw in list(reads.values()):assert pin(Path(result['path']))==result
packet={'schema':'closed-two-ABI-semantic-reader-proposal-1','date':'2026-10-16 ET','files':rows,
    'primary_source_spans':spans,'inverse':{'five_exact_changes_restore_full_v3_bytes':True,'unchanged_functions_and_classes':unchanged},
    'tests':{'count':11,'failures':0,'errors':0,'skips':0,'per_enum_shape_mutations':506,
        'two_complete_actual_29_root_metadata_pipelines':True,'old_direct_path_output_identical':True},
    'semantic_reader':{'path':'proposed/compiler_unit_adapter_v4.py','selected_exact_derived_streams':2,
        'original_and_role_derived_AST_bytes_mutated':False,'semantic_recovery_is_reversible_transport':False,
        'generic_strict_decoder_and_all_old_domain_gates_unchanged':True,
        'outside_exact_families_retains_original_direct_ConstantExpr_path':True,
        'actual_v3_stays_preserved':True,'enclosing_producer_must_pin_real_new_reader_module':True},
    'dependent_adapters_policies_envelopes_changed':False,'actual_scientific_or_remote_execution':False,
    'project_source_or_public_admission':False,'independent_review':'pending','actual_observer_use':'pending reviewed successor and root admission'}
(HERE/'source-packet-v1.json').write_bytes(canonical(packet)+b'\n')
print(json.dumps(pin(HERE/'source-packet-v1.json')))
