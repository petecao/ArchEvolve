import ast,hashlib,json,pathlib,subprocess,sys,datetime
P=pathlib.Path;sys.dont_write_bytecode=True
sys.path.insert(0,'/Users/yanrujhou/.codex/worktrees/lanl-analytic-eval/ArchEvolve/swdb-project')
from swdb.artifacts import digest
receipt=P('/private/tmp/lanl17-cleanup60-source-preparation-20261007-a4.json')
d=json.loads(receipt.read_bytes());assert d['identity_sha256']==digest({k:v for k,v in d.items() if k!='identity_sha256'})=='a54a5bd80926276cba55ee689f91e665d3dc199a6832cdce0948c654d612009d'
for row in d['snapshots'].values():
 b=P(row['path']).read_bytes();assert len(b)==row['size_bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
helper=P('/private/tmp/lanl17_parent_helpers_cleanup60_a4.py');old=P('/private/tmp/lanl17_parent_helpers_caps_a3.py')
assert helper.read_bytes().count(b'--kill-after=60s')==1
assert helper.read_bytes().replace(b'--kill-after=60s',b'--kill-after=40s')==old.read_bytes()
sup=P('/private/tmp/lanl17_metadata_supervisor_cleanup60_a4.py');old_sup=P('/private/tmp/lanl17_metadata_supervisor_caps_a3.py')
assert sup.read_bytes().replace(b'28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414',b'69dcfe546d3042228ccca4fb29e8409da88443ba15680f30bfdc929ea12ae2b9')==old_sup.read_bytes()
portable=P('/private/tmp/lanl17_metadata_supervisor_cleanup60_a4_portable_controls.py')
assert portable.read_bytes().replace(b'lanl17_metadata_supervisor_cleanup60_a4.py',b'lanl17_metadata_supervisor_caps_a3.py').replace(b'lanl17_parent_helpers_cleanup60_a4.py',b'lanl17_parent_helpers_caps_a3.py')==P('/private/tmp/lanl17_metadata_supervisor_caps_a3_portable_controls.py').read_bytes()
fixture=P('/private/tmp/lanl17_metadata_supervisor_cleanup60_a4_linux_fixture.py')
assert fixture.read_bytes()==P('/private/tmp/lanl17_metadata_supervisor_caps_a3_linux_fixture.py').read_bytes()
for f in (helper,sup,portable,fixture):ast.parse(f.read_bytes())
run=subprocess.run([sys.executable,'-B',str(portable)],capture_output=True,text=True,timeout=60)
assert run.returncode==0,run.stderr
assert 'Ran 9 tests' in run.stderr and run.stderr.rstrip().endswith('OK')
out={'format':'swdb.parent17-cleanup60-portable-admission.v1','checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_preparation_identity':d['identity_sha256'],'exact_helper_one_literal_reversal':True,'exact_supervisor_pin_only_reversal':True,'portable_two_paths_only_reversal':True,'four_AST_parses':True,'portable_control_returncode':run.returncode,'portable_control_output':run.stderr,'full_F6_and_scientific_bytes_unchanged':True,'actual_linux_checks':'pending new full-helper-hash cleanup proof and supervisor fixture; no native overlap','not_population_or_campaign_admission':True}
out['identity_sha256']=digest(out);target=P('/private/tmp/lanl17-cleanup60-parent-portable-actual-20261007-a4.json');assert not target.exists();target.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'proof':str(target),'identity_sha256':out['identity_sha256'],'portable_cases':9,'byte_reversals':4,'actual_linux_pending':True}))
