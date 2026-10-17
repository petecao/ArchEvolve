"""2026-10-16 ET. Source/synthetic assembly only, never compiler or actual audit."""
import ast
import hashlib
import json
from pathlib import Path
import sys

EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('source-only preparation refuses '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
PROJECT=WHOLE.parents[3]

def pin(path,expected=None):
    path=Path(path).resolve(strict=True);data=path.read_bytes();row={'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    assert expected is None or row['sha256']==expected,(path,row['sha256'])
    return row

def write(name,value):
    (HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

def main():
    spec={'__name__':'inert_synthetic_stream_fixture','__file__':str(HERE/'test_stream_projection_v1.py')}
    exec(compile((HERE/'test_stream_projection_v1.py').read_bytes(),str(HERE/'test_stream_projection_v1.py'),'exec'),spec)
    data,result,checked=spec['project']()
    (HERE/'synthetic-original-tu-stream.json').write_bytes(data)
    write('synthetic-policy.json',spec['policy']())
    write('synthetic-projection.json',result['projection'])
    write('synthetic-certificate.json',result['certificate'])
    write('synthetic-passive-check.json',checked)
    names=sorted(json.loads((WHOLE/'contracts.json').read_bytes())['contracts'])
    assert len(names)==26
    tree=ast.parse((WHOLE/'source_program_globals_v1.py').read_bytes())
    node=next(node for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='GLOBALS' for t in node.targets))
    globals=sorted(ast.literal_eval(node.value));assert len(globals)==12
    write('prospective-stream-profile.json',{'schema':'unadmitted-original-tu-stream-profile-1','date':'2026-10-16 ET',
        'status':'SOURCE PROPOSAL ONLY; actual caller mangled identity and source/compiler receipt require root binding',
        'proposed_complete_input_stream_bytes':536870912,'existing_retained_file_bytes':134217728,'existing_retained_total_bytes':268435456,
        'proposed_allocated_pair_bytes':100663296,'existing_finalization_reserve_bytes':1048576,
        'existing_entry_seconds':165,'existing_guard_seconds':180,'existing_guard_rss_bytes':4294967296,
        'proposed_max_work_bytes':201326592,'proposed_max_nodes':1000000,'proposed_max_ids':200000,'proposed_max_census_rows':100000,
        'api_names':names,'source_host_global_names':globals,'source_enums':['Operation_t','OpcodeType','DataType'],
        'assertion_candidates':['__assert_fail','__assert_rtn'],'all_named_typedef_alias_enum_subtrees_retained':True,
        'input_stream_allowance_is_existing_V7_policy':False,'root_future_stream_profile_admission_required':True,
        'future_controller_must_allocate_from_actual_remaining_retained_total':True,
        'old_raw_TU_consumer_compatible':False,'actual_compiler_observation':False,'public_admission':False})
    files=[pin(HERE/name) for name in ('stream_projection_v1.py','test_stream_projection_v1.py','README.md','prepare_stream_proposal_v1.py',
        'synthetic-original-tu-stream.json','synthetic-policy.json','synthetic-projection.json','synthetic-certificate.json','synthetic-passive-check.json',
        'prospective-stream-profile.json','pure-stream-controls-red.log','pure-stream-controls-green.log')]
    report=json.loads((HERE/'pure-stream-controls-green.log').read_text().splitlines()[-1])
    assert report['tests']==13 and report['failures']==report['errors']==report['skips']==0 and report['child_events']==[]
    assert report['source_sha256']==pin(HERE/'stream_projection_v1.py')['sha256'] and report['tests_sha256']==pin(HERE/'test_stream_projection_v1.py')['sha256']
    basis=[pin(WHOLE/'compiler_unit_adapter_v2.py','1cf112859f976f77e8381c777c977f5cf5857d6e18f1bd0e24f9689148e80317'),
        pin(WHOLE/'whole_interface_v4.py','217cdda6ca8eaea99526010f2c379dad963ca81c18c18c79322ce02ab8cc9296ed8'.replace('18c18c','18c')),
        pin(WHOLE/'source_program_globals_v1.py','17bc9b0aefc7cadd5762f630b28c3ab97496f3cac17eb40bbd89deda1fe8cc77'),
        pin(WHOLE/'contracts.json'),pin(WHOLE/'compiler-capture-v7/compiler-capture-source-packet-v7.json',
            'd4806992407d16e3b2cdb3d8305af42f50fd4a5cfed54b91416465a5a406836f'),
        pin(PROJECT/'apps/dx100/benchmarks/API/MAA.hpp','4b71fc8503392878065000d75264e4612e2102f4f54a15178c0e2ed5e9d32bfd'),
        pin(PROJECT/'apps/dx100/benchmarks/API/MAA_gem5.hpp','5102335292a6ef1c3a7d7638d6d0791eb4bfd8c4cc8befe61afcd267f203c174')]
    write('streaming-proposal-source-packet-v1.json',{'date':'2026-10-16 ET','status':'INERT SOURCE PROPOSAL; synthetic controls only',
        'files':files,'unchanged_source_basis':basis,'pure_validation':report,
        'synthetic_only':True,'actual_clang_metadata_compatibility_established':False,'actual_streaming_runtime_controller_authored':False,
        'new_projected_TU_source_consumer_implemented':False,'producer_parser_classifier_and_compiler_observation_TCB':True,
        'discarded_source_reconstructable_from_hash':False,'actual_or_public_admission':False,
        'production_edits':False,'old_raw_TU_consumer_compatible':False,'child_events':EVENTS})
    print(json.dumps(pin(HERE/'streaming-proposal-source-packet-v1.json'),sort_keys=True))

if __name__=='__main__':main()
