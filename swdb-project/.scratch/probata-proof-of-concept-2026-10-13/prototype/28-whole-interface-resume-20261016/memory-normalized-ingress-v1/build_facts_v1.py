"""Offline facts from retained compact G642/transform metadata, no execution."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
OUT = HERE / 'proposed'
OUT.mkdir(exist_ok=True)


def pin(path):
    raw = path.read_bytes()
    return {'path':str(path), 'bytes':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}


closure_path = WHOLE / 'compiler-memory-capture-v1-actual/closure-stdout-v1.json'
post_path = WHOLE / 'memory-role-gzip-v1-actual/postflight-stdout-v2.json'
closure = json.loads(closure_path.read_bytes()); post = json.loads(post_path.read_bytes())
original = closure['raw_root']; root = post['transform_output_root']
original_rows = {row['relative']:{k:row[k] for k in ('path','bytes','sha256')} for row in closure['rows']}
outputs = {name:{'path':root+'/'+name, **row} for name,row in post['transform_file_pins'].items()}
roles = {'policy':'control/linux_memory_capture_policy_v1.json','result':'component/result.json',
    'observation':'component/compiler-observation.json','runtime_before':'capture-runtime-before.json',
    'runtime_after':'capture-runtime-after.json','zlib_before':'capture-zlib-before.json','zlib_after':'capture-zlib-after.json',
    'gzip_receipt':'component/caller.ast.gzip.json','compressed_tu':'component/caller.ast.json.gz','abi':'component/abi.ast.json',
    'probe':'control/compiler_abi_probe_v1.cpp','source':'control/same_thread_memory_v1.cpp','source_after':'source-after.json'}
original_pins = {name:original_rows[relative] for name,relative in roles.items()}
assert original_pins['source']['bytes'] == 3258 and original_pins['source']['sha256'] == '55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'
root_adoption = WHOLE.parents[1] / 'evidence/t28-memory-role-gzip-v1-root-scoped-acceptance-20261016.json'
assert pin(root_adoption)['sha256'] == 'efbe8ae05f7b30a6cc01043adf35c919d332eb4d3656396124d60f7bfe5f529c'
facts = {'schema':'exact-memory-source-capture-facts-1', 'source_commit':'2baf722fdaa6cba24b859eae3172a6f597417d72',
    'kind':'complete-memory-original-tu-paired-type-gzip-1', 'original_root':original, 'transform_root':root,
    'original':original_pins, 'transform_outputs':outputs,
    'root_adoption':pin(root_adoption), 'reconciliation':pin(WHOLE / 'memory-role-gzip-v1-actual/actual-reconciliation-v1.json'),
    'capture_execution':pin(WHOLE / 'compiler-memory-capture-v1-actual/actual-observation-reconciliation-v2.json'),
    'postflight':pin(post_path), 'invocation':pin(WHOLE / 'memory-role-gzip-v1-actual/actual-transform-invocation-v1.json'),
    'stdout':pin(WHOLE / 'memory-role-gzip-v1-actual/actual-transform-stdout-v1.json'),
    'stderr':pin(WHOLE / 'memory-role-gzip-v1-actual/actual-transform-stderr-v1.log'),
    'controller':pin(WHOLE / 'memory-role-gzip-v1/memory_role_controller_v1.py'),
    'command':pin(WHOLE / 'memory-role-gzip-v1/command_v1.json'),
    'bootstrap':pin(WHOLE / 'memory-role-gzip-v1/bootstrap_v1.py'),
    'input_count':911, 'input_map_sha256':post['known_input_map_sha256'],
    'original_wire':closure['metadata']['component/caller.ast.gzip.json'],
    'normalization':post['transport']['normalization'], 'codec':post['transport']['normalized_gzip_codec'],
    'case_calls':[12,14,14]}
raw=(json.dumps(facts,sort_keys=True,indent=2)+'\n').encode()
(OUT / 'memory_capture_facts_v1.json').write_bytes(raw)
(HERE / 'facts-provenance-v1.json').write_text(json.dumps({'facts':pin(OUT / 'memory_capture_facts_v1.json'),
    'sources':[pin(closure_path),pin(post_path),pin(root_adoption)],
    'no_AST_payload_ownership_or_new_observation_created':True},sort_keys=True,indent=2)+'\n')
print(json.dumps(pin(OUT / 'memory_capture_facts_v1.json'),sort_keys=True))
