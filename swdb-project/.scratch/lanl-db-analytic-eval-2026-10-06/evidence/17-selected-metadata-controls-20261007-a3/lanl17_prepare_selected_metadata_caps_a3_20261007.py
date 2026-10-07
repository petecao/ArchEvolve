"""2026-10-07 ET: exact selected external-control literal edits; no action imports."""
import ast,datetime,difflib,hashlib,json
from pathlib import Path
ROOT=Path('/private/tmp')
original=ROOT/'lanl17_parent_helpers_caps_a2.py';text=original.read_text();assert hashlib.sha256(original.read_bytes()).hexdigest()=='09136ee553984b2c0cf929a6746f037aa4e1874f863aa2e83e0e0842a8b65ed9'
lines=text.splitlines(keepends=True);tree=ast.parse(text);edits=[];caps=[3600,6000,3600,6000,14400,3600]
for function in tree.body:
 if isinstance(function,ast.FunctionDef) and function.name in ('prepare','finalize'):
  calls=sorted((n for n in ast.walk(function) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='run_cli'),key=lambda n:n.lineno)
  for call in calls:
   node=call.args[4];assert isinstance(node,ast.Constant) and node.lineno==node.end_lineno
   line=lines[node.lineno-1];old=line[node.col_offset:node.end_col_offset];new=str(caps[len(edits)])
   assert old==str(node.value)
   edits.append({'action':function.name,'line':node.lineno,'column':node.col_offset,'old':old,'new':new})
assert len(edits)==6 and [e['old'] for e in edits]==['1400','1400','1400','900','1200','1400']
for edit in edits:
 i=edit['line']-1;start=edit['column'];end=start+len(edit['old']);assert lines[i][start:end]==edit['old'];lines[i]=lines[i][:start]+edit['new']+lines[i][end:]
changed=''.join(lines);restore=changed.splitlines(keepends=True)
for edit in edits:
 i=edit['line']-1;start=edit['column'];end=start+len(edit['new']);assert restore[i][start:end]==edit['new'];restore[i]=restore[i][:start]+edit['old']+restore[i][end:]
assert ''.join(restore).encode()==original.read_bytes()
helper=ROOT/'lanl17_parent_helpers_caps_a3.py';assert not helper.exists();helper.write_text(changed)
helper_sha=hashlib.sha256(helper.read_bytes()).hexdigest()
sup_old=ROOT/'lanl17_metadata_supervisor.py';sup=ROOT/'lanl17_metadata_supervisor_caps_a3.py'
assert hashlib.sha256(sup_old.read_bytes()).hexdigest()=='32a0211aaaf093338aad469ef5a8b794358c95cff6c76ca2448f3e80c815f174'
old="HELPER_SHA='09136ee553984b2c0cf929a6746f037aa4e1874f863aa2e83e0e0842a8b65ed9'";new="HELPER_SHA='"+helper_sha+"'"
sup_text=sup_old.read_text();assert sup_text.count(old)==1;assert not sup.exists();sup.write_text(sup_text.replace(old,new));assert sup.read_text().replace(new,old)==sup_text
control_old=ROOT/'lanl17_metadata_supervisor_portable_controls.py';control=ROOT/'lanl17_metadata_supervisor_caps_a3_portable_controls.py'
control_text=control_old.read_text();pairs=[('lanl17_metadata_supervisor.py','lanl17_metadata_supervisor_caps_a3.py'),('lanl17_parent_helpers_caps_a2.py','lanl17_parent_helpers_caps_a3.py')]
for before,after in pairs:assert control_text.count(before)==1;control_text=control_text.replace(before,after)
assert not control.exists();control.write_text(control_text)
reverse=control.read_text()
for before,after in pairs:reverse=reverse.replace(after,before)
assert reverse==control_old.read_text()
fixture_old=ROOT/'lanl17_metadata_supervisor_linux_fixture.py';fixture=ROOT/'lanl17_metadata_supervisor_caps_a3_linux_fixture.py'
assert hashlib.sha256(fixture_old.read_bytes()).hexdigest()=='a848ef2d5c6dba58e6814bf80d8bdf24edeb33812bda343ecf25ff6f28745b0f'
assert not fixture.exists();fixture.write_bytes(fixture_old.read_bytes());assert fixture.read_bytes()==fixture_old.read_bytes()
for path in (helper,sup,control,fixture):ast.parse(path.read_text())
patch=''.join(difflib.unified_diff(text.splitlines(keepends=True),changed.splitlines(keepends=True),fromfile=original.name,tofile=helper.name))
(ROOT/'lanl17-selected-metadata-caps-a3-20261007.patch').write_text(patch)
files={path.name:{'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size_bytes':path.stat().st_size} for path in (helper,sup,control,fixture)}
proposal=json.loads((ROOT/'lanl17-metadata-cap-proposal-20261007.json').read_text())
assert proposal['identity_sha256']=='83c0b4f1ba1c1fe66fe80a0151452358db95a54b99b8e2b1d1cf01c8eb0fcb39'
value={'format':'swdb.lanl17-selected-metadata-caps-exact-proof.v1','updated':'2026-10-07 ET','parent_selected':True,'proposal_identity_sha256':proposal['identity_sha256'],
 'files':files,'six_literal_edits':edits,'helper_full_byte_reversal_to_09136':True,'all_other_helper_bytes_unchanged':True,
 'supervisor_only_HELPER_SHA_changed':True,'portable_controls_only_two_paths_changed':True,'linux_fixture_bytes_unchanged_a848':True,
 'whole_action_policy':proposal['whole_actions'],'original_linux_smoke_sha256':'4d0bdf1d4c8d2ce96d948085a785cde15c389a4c50413962bc7db14df57cf9d6',
 'existing091_31e_controls_proofs_preserved':True,'source_C_F6_unchanged':True,'portable_gate':'pending','actual_original4d_new_helper_smoke':'not_run','actual_new_supervisor_linux_fixture':'not_run',
 'no_metadata_action_or_control_science_function_import':True,'no_cli_or_ssh_or_provider':True,'actual17campaigns':0,'population_frozen':False,
 'scope':'Selected finite administrative processing allowances; not duration prediction or scientific budget change.'}
value['identity_sha256']=hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
(ROOT/'lanl17-selected-metadata-caps-a3-exact-proof-20261007.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'files':files,'exact_proof_identity_sha256':value['identity_sha256']},indent=2))
