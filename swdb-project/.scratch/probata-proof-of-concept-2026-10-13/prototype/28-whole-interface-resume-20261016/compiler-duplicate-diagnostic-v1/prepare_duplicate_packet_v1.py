"""Pure physical source/test/metadata pins; no actual diagnostic/capture main."""
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;POC=WHOLE.parents[1]
def pin(path):
 raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
report=json.loads((HERE/'pure-duplicate-controls.log').read_text().splitlines()[-1]);assert report['tests']==11 and report['failures']==report['errors']==report['skips']==0 and report['child_events']==[]
assert report['source_sha256']==pin(HERE/'duplicate_metadata_v1.py')['sha256']
files=[pin(HERE/name) for name in ('duplicate_metadata_v1.py','test_duplicate_metadata_v1.py','pure-duplicate-controls.log','PLAN.md','prepare_duplicate_packet_v1.py')]
inputs=[pin(WHOLE/'compiler-capture-v10'/name) for name in ('linux_compiler_capture_v10.py','linux_compiler_capture_policy_v10.json','linux_compiler_capture_command_v10.json','compiler-capture-source-packet-v10.json')]
inputs+=[pin(WHOLE/'streaming-minify-v1'/name) for name in ('strict_minify_v2.py','lossless_gzip_v2.py')]
settled=pin(POC/'evidence/t28-capture-v10-root-settled-observation-20261016.json');assert settled['sha256']=='c26b83e206f2ce68c97bddbb6b817c48afdb3f9afb6323a7ed2c4d1fd4551f24'
value={'date':'2026-10-16 ET','status':'SOURCE ONLY; exact first duplicate metadata, no JSON repair/admission','files':files,'inputs':inputs,'V10_preserved_root_settled_observation':settled,'validation':report,
 'prospective_outer_seconds':120,'internal_seconds':90,'prospective_RSS_bytes':536870912,'stdout_limit_bytes':32768,'retained_artifact_writes':False,
 'decoder_full_raw_limit_bytes':2147483648,'gzip_limit_bytes':134217728,'strict_refusal_preserved':True,'policy_relaxation':False,'actual_diagnostic_or_compiler_run':False,'public_source_or_proof_admission':False}
out=HERE/'duplicate-diagnostic-source-packet-v1.json';out.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n');print(json.dumps(pin(out),sort_keys=True))
