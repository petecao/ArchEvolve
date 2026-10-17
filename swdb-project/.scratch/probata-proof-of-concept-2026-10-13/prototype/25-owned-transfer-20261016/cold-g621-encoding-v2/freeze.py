"""2026-10-16 ET. Metadata-only packet assembly; never runs the observer."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
POC=HERE.parents[2]


def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def write(path,value):
    with path.open('xb') as stream:
        stream.write((json.dumps(value,indent=2,sort_keys=True)+'\n').encode())


def main():
    context=(HERE/'context.json').read_text()
    capture=POC/'evidence/t25-owned-transfer10-cold-v3-root-stdout-20261016.json'
    assert pin(capture)['sha256']=='cf62bd6a0bf73a171fc8e7ddd68f32c1bb38dcc4f7e8a055264cbc6a2f8e5f5e'
    entry='\n\n'.join([(HERE/'semantic_terms.py').read_text(),
                         (HERE/'encoding_probe.py').read_text(),
                         'CONTEXT = json.loads('+repr(context)+')',
                         (HERE/'observer.py').read_text()])
    compile(ast.parse(entry),'<inert-frozen-encoding-probe>','exec')
    with (HERE/'entry.py').open('xb') as stream:
        stream.write(entry.encode())
    command={'date':'2026-10-16 ET','schema':'ownership10-g621-bounded-encoding-probe-v2',
             'status':'INERT_REVIEW_AND_ROOT_ADMISSION_REQUIRED','actual_executed':False,
             'host':'mbit10','stdin':pin(HERE/'entry.py'),
             'argv_after_root_read_only_preflight':['/usr/bin/python3','-I','-B','-'],
             'outer_timeout_seconds':90,'outer_kill_after_seconds':5,
             'inner_alarm_seconds':60,'cpu_limit_seconds':30,'address_space_bytes':512*1024**2,
             'stdout_cap_bytes':256*1024,'max_input_bytes':1024*1024,
             'selected_aggregate_input_bytes_cap':2*1024**2,
             'closed_environment':{'PATH':'/usr/bin:/bin','HOME':'/nonexistent','LANG':'C','LC_ALL':'C'},
             'remote_filesystem_writes':False,'subprocesses_or_native_helpers':False,
             'selected_tasks':20,'expected_completed_capture_exit':2,
             'exit_scope':'Exit2 is bounded metadata only; every acceptance flag stays false. Exit1 refuses input/parser/budget boundaries. Root must independently review and admit the exact stdin bytes before invocation.'}
    write(HERE/'command.json',command)
    packet={'date':'2026-10-16 ET','classification':'FROZEN_INERT_BOUNDED_ENCODING_PROBE',
            'inputs':[pin(HERE.parent/'cold-g621-encoding-v1/source-packet.json'),
                      pin(HERE.parent/'cold-g621-encoding-v1/encoding_probe.py'),
                      pin(POC/'evidence/t25-owned-transfer10-encoding-v1-actual-stdout-20261016.json'),
                      pin(capture),pin(HERE.parent/'cold-g621-v3/semantic_terms.py'),
                      pin(HERE.parent/'cold-g621-v3/context.json'),
                      pin(POC.parents[1]/'swdb/vector_owned_state.mlw')],
            'outputs':[pin(HERE/name) for name in ('semantic_terms.py','encoding_probe.py','observer.py','context.json','pure_controls.py','pure-controls.log','freeze.py','README.md','entry.py','command.json')],
            'pure_controls':{'passed':14,'child_native_network_attempts':[]},
            'canonicalizer_delta':'No canonicalizer change from admitted V1. Only emit the first goal canonical mismatch path/operator shape and digests; exact helper inverse retained.',
            'scope':'Same exact twenty pinned tasks/source and V1 decisions; additionally one first canonical goal mismatch path/shape/hash. No raw terms or atoms serialized, no new normalization, role/support admission or proof adoption.',
            'actual_query_executed':False,'actual_tools_executed':False,
            'scientific_acceptance':False,'mathematical_acceptance':False,
            'source_body_Typed_caller_default_or_public_record_acceptance':False,
            'root_exact_admission_required':True}
    write(HERE/'source-packet.json',packet)
    print(json.dumps({'packet':pin(HERE/'source-packet.json'),'entry':pin(HERE/'entry.py'),
                      'command':pin(HERE/'command.json')},indent=2))


if __name__=='__main__':
    main()
