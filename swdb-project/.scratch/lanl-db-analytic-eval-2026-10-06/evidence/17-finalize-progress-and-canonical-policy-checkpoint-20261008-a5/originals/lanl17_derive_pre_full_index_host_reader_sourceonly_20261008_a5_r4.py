import ast,datetime,difflib,hashlib,json,os
from pathlib import Path
from zoneinfo import ZoneInfo
T=Path('/private/tmp')
old=T/'lanl17_pre_full_index_host_observation_20261008_a5_r3.py'
ancestor=T/'lanl17_finalize_parent_host_readonly_20261008_a5_r2.py'
s=old.read_text(); assert hashlib.sha256(s.encode()).hexdigest()=='a83803d1098e9d43d85119fc4c242a3cba696cedfa7a44420c2711c003c2a3da'
changes=[("    return pins\n\ndef current_sources():", "    reviewed_stops=receipt['stopped_attempts'];need(type(reviewed_stops) is list and len(reviewed_stops)==4 and all(type(v) is dict and v.get('campaign')==cid for cid,v in zip(CIDS,reviewed_stops)),'reviewed_ER_four_original_stops')\n    return pins,reviewed_stops\n\ndef current_sources():"),
("            if not command:\n                proof=inactive_owned_identity(p,ps);need(owned_cmdline(p,ps)==b'','inactive_cmdline_byte_continuity');continue\n            argv=command[:-1].split(b'\\0')", "            argv=command[:-1].split(b'\\0') if command else []\n            if not argv or not argv[0]:\n                proof=inactive_owned_identity(p,ps);need(owned_cmdline(p,ps)==command,'inactive_cmdline_byte_continuity');continue"),
("transport=transport_identity();completion=completion_originals(INPUT['completion_originals']);", "transport=transport_identity();completion,reviewed_stops=completion_originals(INPUT['completion_originals']);"),
("    for cid in CIDS:\n        p=RAW/'attempts'/cid/'attempt-1/stopped-receipt.json';b,pin=original(p,65536);v=strict(b);need", "    for cid,reviewed_stop in zip(CIDS,reviewed_stops):\n        p=RAW/'attempts'/cid/'attempt-1/stopped-receipt.json';b,pin=original(p,65536);v=strict(b);need(v==reviewed_stop,'original_stop_matches_reviewed_ER_chain');utc(v['ended_utc']);need"),
("completion_originals(INPUT['completion_originals'])==completion", "completion_originals(INPUT['completion_originals'])==(completion,reviewed_stops)")]
for a,b in changes: assert s.count(a)==1,(a,s.count(a)); s=s.replace(a,b)
ast.parse(s)
source=T/'lanl17_pre_full_index_host_observation_20261008_a5_r4.py'
def write(p,b):
 if isinstance(b,str): b=b.encode()
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b)
 return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def js(p,v):return write(p,json.dumps(v,indent=2,sort_keys=True)+'\n')
pins=[write(source,s)]
for label,path,prior in [('r3',old,old.read_text()),('host-r2',ancestor,ancestor.read_text())]:
 pins.append(write(T/f'lanl17-pre-full-index-host-observation-r4-complete-{label}-derivation-20261008-a5.diff',''.join(difflib.unified_diff(prior.splitlines(True),s.splitlines(True),fromfile=str(path),tofile=str(source)))))
inverse=s
for a,b in reversed(changes):assert inverse.count(b)==1;inverse=inverse.replace(b,a)
assert inverse==old.read_text()
functions=('need','tick','digest','stamp','strict','original','kernel_bytes','locks','daemon','process_identity','native_projection','selected_lease_identity','daemon_ready')
def defs(text):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a,b=defs(ancestor.read_text()),defs(s);assert all(a[k]==b[k] for k in functions)
RAW='/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5';BASE='/data1/yanruj';FINAL='/data/yanruj/EvolveSWDB_runs/lanl17-metadata-finalize-20261007-a5';ER=BASE+'/ArchEvolve-lanl17-actual-report-evidence-20261007-a5/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-actual-report-mbit10-20261007-a5.json'
fixed={'helper_source':(BASE+'/lanl17-control-cleanup60-20261007-a4.py',38195,'28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'),'guard_source':(BASE+'/lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py',14577,'9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6'),'supervisor_source':(BASE+'/lanl17-metadata-supervisor-cleanup60-20261007-a4.py',8014,'fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0')}
roles={'guard_preregistration':FINAL+'/preregistration.json','supervisor_receipt':FINAL+'/supervisor-receipt.json','helper_stdout':FINAL+'/helper.stdout','final_export':RAW+'/final-export.json','agreement_receipt':ER,'manifest_M2':RAW+'/manifest.json',**{k:v[0] for k,v in fixed.items()}}
CIDS=['extensa-gem5-bfs-20261006-p'+str(i) for i in range(1,5)]
for name in ['validate-'+cid for cid in CIDS]+['validate-final-export']:
 for key,suffix in [('argv','argv.json'),('exit','exit-code.txt'),('stdout','stdout'),('stderr','stderr')]:roles[name+':'+key]=RAW+'/'+name+'.'+suffix
assert len(roles)==29
fields=('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')
def future(t,meaning):return {'future_type':t,'required_actual_fact':meaning,'state':'FUTURE_NOT_SUPPLIED'}
sha=pins[0]['sha256'];now=datetime.datetime.now(datetime.timezone.utc)
for cid in CIDS:
 template={'format':'swdb.lanl17-pre-full-index-host-observation-input.v1','campaign':cid,'nonce':future('lowercase_hex_32_to_64','fresh parent-owned nonce'),'completion_originals':{k:{'path':v,'bytes':future('nonnegative_integer','exact actual original byte count'),'sha256':future('sha256_hex64','exact actual original SHA256'),'stat':{field:future('nonnegative_integer','actual original st_'+field) for field in fields}} for k,v in roles.items()},'expected_ER_commit':future('git_hex40','genuine reviewed completed ER commit'),'fresh_routes':{'inventory_output':future('canonical_remote_path','fresh external next-stage output route; explicit nonempty whitelist subset only')},'parent_review':{'basis':'explicit_parent_review_of_genuine_completed_FINALIZE_and_next_full_index_metadata_routes','source_sha256':sha,'payload_sha256':future('sha256_hex64','canonical True input digest excluding parent_review'),'completion_packet_sha256':future('sha256_hex64','genuine reviewed FINALIZE completion packet'),'completion_root_review_sha256':future('sha256_hex64','actual root completion review original'),'completion_peer_review_sha256':future('sha256_hex64','actual independent completion review original'),'actual_completion_originals_reviewed':future('boolean_true','explicit actual parent review; never default approval'),'fixtures':False,'checked_utc':future('UTC_timestamp','genuine actual review UTC'),'valid_until_utc':future('UTC_timestamp','actual expiry within 300 seconds')}}
 pins.append(js(T/f'lanl17-p{cid[-1]}-pre-full-index-host-input-SOURCE-ONLY-draft-r4-20261008-a5.json',{'format':'swdb.source-only-typed-future-input-draft.v1','executable':False,'source_only_not_run':True,'scientific_admission':False,'source':pins[0],'input_template':template}))
config={'argv':['/usr/bin/python3.12','-I','-B','-c',s,'--input',future('canonical_remote_path','fresh own0600 closed actual input original route'),'--input-sha256',future('sha256_hex64','exact original actual input bytes'),'--source-sha256',sha],'source_pins':[{'path':path,'bytes':n,'sha256':h} for path,n,h in fixed.values()]+[{'path':RAW+'/manifest.json','bytes':292401,'sha256':'b86d78bac1d0a09e176114d1c23491ede098c4fcf5af5ab96f318ceabc29b8d1'}],'collect':[],'remote_timeout_seconds':60,'local_timeout_seconds':180}
pins.append(js(T/'lanl17-pre-full-index-host-action-SOURCE-ONLY-draft-r4-20261008-a5.json',{'format':'swdb.source-only-action-draft.v1','executable':False,'source_only_not_run':True,'scientific_admission':False,'config_template':config,'actual_input_stage_and_parent_review_required':True}))
checks={'format':'swdb.lanl17-pre-full-index-host-source-static-checks.v1','prepared_ET':now.astimezone(ZoneInfo('America/Detroit')).strftime('%Y-%m-%d %H:%M ET'),'prepared_utc':now.isoformat(),'source_only_not_run':True,'scientific_admission':False,'ancestor':{'path':str(ancestor),'bytes':len(ancestor.read_bytes()),'sha256':hashlib.sha256(ancestor.read_bytes()).hexdigest()},'selected_source':pins[0],'checks':{'AST_parse':True,'thirteen_inherited_function_ASTs_identical':list(functions),'five_narrow_R3_inverse_substitutions_restore_exact_bytes':True,'completion_role_count':29,'explicit_next_stage_subset_not_all_pipeline_routes':True,'empty_or_missing_argv0_requires_stable_inactive_identity':True,'fresh_stop_equals_pinned_ER_original_stop':True,'stop_UTC_checked_before_projection':True,'input_drafts_NONEXECUTABLE_typed_FUTURE_no_actual_approval':True,'action_inline_source_exact':True,'alarm_remote_local_seconds':[45,60,180],'sources_not_imported_or_executed':True},'pins':pins}
pins.append(js(T/'lanl17-pre-full-index-host-source-static-checks-r4-20261008-a5.json',checks))
text=f'''Prepared {checks['prepared_ET']} ({checks['prepared_utc']}).

SOURCE ONLY, NOT RUN. R4 supersedes preserved R1/R2/R3 source for prospective parent/peer review only. No frozen controls, repository, remote host, scientific commands or original metadata changed.

This actual-input query requires genuine completed FINALIZE originals and explicit root/peer completion review before use. The 29 fixed roles include 9c/fa/H stdout/final-export/ER/M2/H/G/SUP and five public validation quartets. Each input requires actual byte/SHA/nine-stat facts, actual ER commit, fresh nonce, genuine review and a UTC interval no longer than 300 seconds. All four per-CID input drafts and action draft are NONEXECUTABLE typed FUTURE wrappers. No actual ER commit, current clearance or approval supplied.

R4 adds exact equality between each fresh normal stop and the already pinned ER stopped_attempts, validates ended_utc before projection, and rejects empty argv0 unless strict stable Z/X identity proves inactivity. R3 allowed explicit next-stage output subsets rather than demanding all eight pipeline output routes remain absent. Completed RAW stores are required present. All previous source bytes are preserved.

Native facts retain exact released hostlock lease schema, node0 generation 514, inode-keyed kernel lock and FD9 guards, before/after continuity, only exact immediate GNU timeout parent exclusion, physical 185-module F6 and six tool pins, source/PRIMARY/origin R and unchanged serial floors. Unreadable/ambiguous matching or owned cmdline, races or malformed facts are unknown and cannot establish absence. Auth contents are never read; startup/HOME auth existence/stat only. Report/stdout/provider/log bodies are not returned. ER compact metadata inherently contains original report but is read only to verify its seal/linkage and stop equality; no report body export.

Packet/root/peer hashes are explicit parent provenance facts, not independent live proof. Historical catalog byte continuity, exclusive ownership and all-four custody approval remain separate parent review. Bash 1024-byte units are not observed. A point-in-time ready result is neither scientific admission nor a reservation; genuine continuity through the next index operation still requires parent review. Preserve failed/expired/unknown observations and never retry scientific controls from this query.

Action envelope uses exact isolated inline source, 45-second internal alarm, remote GNU 60 seconds and local 180 seconds. Parent must concretize the actual input, review bytes/routes/expiry, stage its own exact input, unwrap the actual config only after source+actual-input peer review, and retain transport originals. This source-only authoring and AST checks do not demonstrate runtime behavior.

Pins:\n'''
for pin in pins:text+=f"- {pin['path']}: {pin['bytes']} B, SHA256 {pin['sha256']}\n"
pins.append(write(T/'lanl17-pre-full-index-host-source-handoff-r4-20261008-a5.md',text))
print(json.dumps(pins,indent=2))
