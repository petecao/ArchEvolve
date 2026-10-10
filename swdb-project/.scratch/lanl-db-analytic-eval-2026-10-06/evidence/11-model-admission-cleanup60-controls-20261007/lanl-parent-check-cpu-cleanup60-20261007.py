import ast,hashlib,json,pathlib
P=pathlib.Path
variants=[
 ('/private/tmp/lanl-dispatch-cpu-model-validation-a3-metadata2400.py','/private/tmp/lanl-dispatch-cpu-model-validation-a3-metadata2400-cleanup60.py','804fb08298bf1469c6098dfcd1a50710f2cc941f9478895482c1fe7d901e6ecb'),
 ('/private/tmp/lanl-dispatch-cpu-band-report-a3-metadata2400.py','/private/tmp/lanl-dispatch-cpu-band-report-a3-metadata2400-cleanup60.py','dd74dbbe238c1d0c8222d894acd94ef1d344049da257d2a0d744afefb3d2b120')]
for old,new,expected in variants:
 a,b=P(old).read_bytes(),P(new).read_bytes()
 assert hashlib.sha256(b).hexdigest()==expected
 assert a.count(b'--kill-after=20s')==b.count(b'--kill-after=60s')==1
 assert b.replace(b'--kill-after=60s',b'--kill-after=20s')==a
 ast.parse(b)
 # Since the sole raw-byte change lies outside RUNNER_TEMPLATE,
 # its scientific/control code and all native900 argv are unchanged.
 for data in (a,b):
  templates=[n.value.value for n in ast.parse(data).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='RUNNER_TEMPLATE' for t in n.targets)]
  assert len(templates)==1
  if data is a:original=templates[0]
  else:assert templates[0]==original
guard=P('/private/tmp/lanl-admit-cpu-future-phase-cleanup60-20261007.py').read_bytes()
assert hashlib.sha256(guard).hexdigest()=='b406d3d06b3bddb2cd433cf8f3c47fa80f03314b23795a4b40c045a9120a1e93'
for old,new in [
 (b'lanl-dispatch-cpu-band-report-a3-metadata2400-cleanup60.py',b'lanl-dispatch-cpu-band-report-a3-metadata2400.py'),
 (b'lanl-dispatch-cpu-model-validation-a3-metadata2400-cleanup60.py',b'lanl-dispatch-cpu-model-validation-a3-metadata2400.py'),
 (b'dd74dbbe238c1d0c8222d894acd94ef1d344049da257d2a0d744afefb3d2b120',b'83b2683b5bb21534d7dbd962555770842b8dd24748ba5119abec9339d53b0ad2'),
 (b'804fb08298bf1469c6098dfcd1a50710f2cc941f9478895482c1fe7d901e6ecb',b'f1ddb874189abb28fecb7ef4431f6382d3c09442ae1a75afd0164f4562f276bc')]:
 assert guard.count(old)==1
 guard=guard.replace(old,new)
assert guard==P('/private/tmp/lanl-admit-cpu-future-phase-20261007.py').read_bytes()
ast.parse(guard)
print(json.dumps({'two_launchers_one_external_cleanup_change_each':True,'decoded_scientific_runners_byte_identical':True,'guard_only_selected_paths_hashes_changed':True,'native_deadline_s':900,'external_kill_after_s':60,'original_31e_actual_cleanup_evidence_reused':True,'no_actual_command_execution':True}))
