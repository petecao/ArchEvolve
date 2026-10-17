"""Static source/receipt custody proof; never import or execute guarded actions."""
import ast
import datetime
import hashlib
import json
from pathlib import Path

TMP=Path('/private/tmp')
GUARD=TMP/'lanl17_metadata_dispatch_guard_cleanup60_a4_20261007.py'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
module=ast.parse(GUARD.read_text())
constants={}
for node in module.body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
  try:constants[node.targets[0].id]=ast.literal_eval(node.value)
  except ValueError:pass
assert constants['HELPER_SHA']=='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414'
assert constants['SUPERVISOR_SHA']=='fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0'
assert constants['LIMITS']=={'prepare':{'wait':18000,'term':18120,'kill':60,'parent':18300},'finalize':{'wait':78000,'term':78120,'kill':60,'parent':78300}}
imports=[n for n in ast.walk(module) if isinstance(n,(ast.Import,ast.ImportFrom))]
assert not any((isinstance(n,ast.ImportFrom) and (n.module or '').startswith('swdb')) or (isinstance(n,ast.Import) and any(x.name.startswith('swdb') or x.name=='importlib' for x in n.names)) for n in imports)
execs=[n for n in ast.walk(module) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='os' and n.func.attr.startswith('exec')]
assert len(execs)==1 and execs[0].func.attr=='execv'
text=GUARD.read_text()
for flag in ('--final-source-sha','--cleanup-proof','--cleanup-proof-identity','--supervisor-proof','--supervisor-proof-identity','--guard-sha256'):
 assert flag in text
assert '--kill-after=60s' in text and "choices=sorted(LIMITS)" in text
assert "'dispatch'" not in text and "'run-campaign'" not in text
assert "*tail]" in text and 'os.execv(timeout,argv)' in text
parent_proof=TMP/'lanl17-cleanup60-parent-portable-actual-20261007-a4.json'
portable=json.loads(parent_proof.read_text())
assert portable['identity_sha256']==dig({k:v for k,v in portable.items() if k!='identity_sha256'})=='fd9a7a48ddacbd0dfa1f3ae49a1ab5fefae043b23332be02905a09e54155b05e'
preparation=TMP/'lanl17-cleanup60-source-preparation-20261007-a4.json'
prep=json.loads(preparation.read_text());assert prep['identity_sha256']==dig({k:v for k,v in prep.items() if k!='identity_sha256'})=='a54a5bd80926276cba55ee689f91e665d3dc199a6832cdce0948c654d612009d'
assert prep['portable_wiring_cases_run']==0 and prep['fresh_original4d_smoke']==prep['fresh_a848_fixture']=='not_run'
for row in prep['snapshots'].values():assert sha(row['path'])==row['sha256']
guard_sha=sha(GUARD)
remote='/data1/yanruj/lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py'
readme='''# Parent metadata dispatch guard, cleanup60 a4

2026-10-07 ET. Source-only prospective preparation. No action, Store construction, control import, test rerun, population freeze, provider or SSH execution. Parent selected helper28d116 and supervisorfa703; fresh exact-full-hash actual original4d smoke and a848 fixture remain required before this guard can execute. Earlier69/166 actual receipts are immutable history and deliberately refused here. Final11/14 catalogue admission and parent-selected finalR are still prerequisites.

The helper differs from69dc only at campaign dispatch's outer `--kill-after=40s`→`60s`; its six selected metadata caps and all scientific/campaign/provider/defaultHOME/input/ROI bytes remain exact. Supervisor differs from1666 only in HELPER_SHA. New portable binding sources change only two paths; parent ran the nine cases once0.256s, retained separately from preparation's original NOTRUN chronology. Parameterizeda848 fixture is byte-identical. New original4d/a848 actual Linux checks have not yet run at this preparation.

The guard requires explicit full finalR, reviewed guard SHA, actual fresh a4 proof paths and parent-reviewed receipt identities. It checks live helper/supervisor hashes, clean cleanup source with exact185-moduleF6/processesbcc9, finalR Git object and equality of every Python Git blob with that source. Prepare's original tail must name the sameR/proof and fresh dedicated source/raw; finalize requires the retained canonical manifest'sR/helper/F6/proof and exact frozen source project. A control project can be clean immutableC or finalR because cleanup/model code is exactlyF6; finalR must already exist in that repository's Git object database. Parent delivers/fetchesR first, without changing liveC. This does not certify final catalogue scientific admission; parent choosesR only after those gates.

Metadata executes outside socket wrappers: both socket and legacy leases must be released before and immediately before exec. No lease is acquired and no all_free check is weakened. Existing helper rechecks capacity, current wrapper, official provider entry/native/version, live SG/baseline/model/runtime/config pins and full catalogue admission. Guard preserves its raw argument tail and inherited environment. Parent restores the verified originalCODEX_HOME through the existing task token before invocation; accountHOME stays unchanged, auth existence only is checked, credential bytes remain unread. No native/provider/scientific/campaign routine is called by the guard.

The guard refuses invocation without a direct GNUtimeout parent using the exact prescribed envelope. It writes only a fresh separate preregistration (source/pins/limits/argv hashes, no full argv/environment/auth) then execs inner GNUtimeout with the pinned supervisor. The tested supervisor owns the actual metadata child and all descendant cleanup; this adds no new process cleanup implementation. Prepare waits18000, enclosingTERM18120/KILL60, parent18300; finalize78000/78120/KILL60/78300. Allowances are finite administrative policy, not duration or scaling guarantees. Nested public exports only; there is no standalone export action. Failure preserves existing partial publication and raw receipts; no blind replay or invented completion.

Remote guard path: `GUARD_REMOTE`. SHA256: `GUARD_SHA`.
New helper: `/data1/yanruj/lanl17-control-cleanup60-20261007-a4.py`, SHA28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414.
New supervisor: `/data1/yanruj/lanl17-metadata-supervisor-cleanup60-20261007-a4.py`, SHAfa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0.

The following are unexecuted command shapes. Parent supplies actual reviewed a4 receipt identities and exact finalR after admission. Example fresh names below are prospective placeholders; preserve any occupied prior path and use a new attempt identity. All three source/raw/control paths are distinct. The prepare cleanup project below is the cleanF6 primary; parent can choose another cleanF6 checkout containing the finalR object. Finalize must use the actual detachedR source created by prepare.

```sh
lanl17_final_r=REQUIRED_FULL_FINAL_DATA_COMMIT_AFTER_11_AND_14
lanl17_primitive_seal=REQUIRED_ACTUAL_A4_ORIGINAL4D_RECEIPT_IDENTITY
lanl17_supervisor_seal=REQUIRED_ACTUAL_A4_A848_RECEIPT_IDENTITY
lanl17_original_codex_home=/data1/yanruj/.codex
env SWDB_LANL17_ORIGINAL_CODEX_HOME="$lanl17_original_codex_home" \\
  CODEX_HOME="$lanl17_original_codex_home" \\
  timeout --signal=TERM --kill-after=60s 18300s python3 GUARD_REMOTE \\
  --action prepare --final-source-sha "$lanl17_final_r" \\
  --guard-sha256 GUARD_SHA --project /data1/yanruj/ArchEvolve/swdb-project \\
  --control /data/yanruj/EvolveSWDB_runs/lanl17-metadata-prepare-20261007-a4 \\
  --cleanup-proof /data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a4/receipt.json \\
  --cleanup-proof-identity "$lanl17_primitive_seal" \\
  --supervisor-proof /data/yanruj/EvolveSWDB_runs/lanl17-metadata-supervisor-fixture-20261007-a4/receipt.json \\
  --supervisor-proof-identity "$lanl17_supervisor_seal" -- \\
  --source-sha "$lanl17_final_r" \\
  --cleanup-proof /data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a4/receipt.json \\
  --source-ref codex/lanl-analytic-eval \\
  --source /data1/yanruj/ArchEvolve-lanl17-source-20261007-a4 \\
  --raw /data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a4 \\
  --tag 20261007-a4

# After four actual stopped/completed stores under the same frozenR/policy:
env SWDB_LANL17_ORIGINAL_CODEX_HOME="$lanl17_original_codex_home" \\
  CODEX_HOME="$lanl17_original_codex_home" \\
  timeout --signal=TERM --kill-after=60s 78300s python3 GUARD_REMOTE \\
  --action finalize --final-source-sha "$lanl17_final_r" \\
  --guard-sha256 GUARD_SHA \\
  --project /data1/yanruj/ArchEvolve-lanl17-source-20261007-a4/swdb-project \\
  --control /data/yanruj/EvolveSWDB_runs/lanl17-metadata-finalize-20261007-a4 \\
  --cleanup-proof /data/yanruj/EvolveSWDB_runs/lanl17-cleanup-smoke-20261007-a4/receipt.json \\
  --cleanup-proof-identity "$lanl17_primitive_seal" \\
  --supervisor-proof /data/yanruj/EvolveSWDB_runs/lanl17-metadata-supervisor-fixture-20261007-a4/receipt.json \\
  --supervisor-proof-identity "$lanl17_supervisor_seal" -- \\
  --manifest /data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a4/manifest.json
```

Parent retains guard preregistration, supervisor receipt/log hashes and outer exit state. A successful supervisor child/cleanup receipt is administrative completion only; admit the public frozen policy/export or four validated campaign stores/report separately. Four genuine campaigns remain required even when current SG/FUNC→MMIO bridge gives0eligible pairs and an unsupported/no-switchD30 report. Nothing changes default timing-only selection or plateau.
'''.replace('GUARD_REMOTE',remote).replace('GUARD_SHA',guard_sha)
readme_path=TMP/'lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.md';readme_path.write_text(readme)
proof={'format':'swdb.lanl17-metadata-dispatch-guard-static-preparation.v1','updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'guard':{'path':str(GUARD),'remote_path':remote,'sha256':guard_sha,'bytes':GUARD.stat().st_size},
 'readme':{'path':str(readme_path),'sha256':sha(readme_path),'bytes':readme_path.stat().st_size},
 'cleanup60_preparation':{'path':str(preparation),'identity_sha256':prep['identity_sha256'],'file_sha256':sha(preparation)},
 'parent_portable_actual':{'path':str(parent_proof),'identity_sha256':portable['identity_sha256'],'file_sha256':sha(parent_proof),'cases':9,'elapsed_s':0.256,'new_run_by_guard_author':False},
 'helper_sha256':constants['HELPER_SHA'],'supervisor_sha256':constants['SUPERVISOR_SHA'],'limits':constants['LIMITS'],
 'required_explicit_execution_checked_finalR':True,'required_new_actual4d_and_a848_proof_paths_and_parent_identities':True,
 'required_clean185_module_F6_and_exact_finalR_python_Git_blobs':True,'all_free_checks_preserved_no_measurement_lease_acquisition':True,
 'original_helper_tail_and_environment_preserved':True,'no_credential_content_or_full_argv_export':True,
 'exact_parent_timeout_ancestry_required_before_exec':True,'exec_pinned_existing_supervisor_no_new_cleanup_implementation':True,
 'syntax':'passed_static_AST','guard_import_or_execution':'not_run','host_test_reruns':0,'Store_constructions':0,
 'population_actions':0,'provider_calls':0,'SSH_dispatches':0,'fresh_original4d_smoke':'not_run','fresh_a848_fixture':'not_run',
 'integration_untouched':True,'source_C_F6_and_existing_controls_proofs_unchanged':True,
 'scope':'Source-only prospective parent dispatch guards; parent full review/actual new cleanup and final catalogue/source admission still required.'}
proof['identity_sha256']=dig(proof)
p=TMP/'lanl17-metadata-dispatch-guard-static-preparation-20261007-a4.json';p.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'guard_sha256':guard_sha,'guard_bytes':GUARD.stat().st_size,'readme_sha256':sha(readme_path),'proof_identity_sha256':proof['identity_sha256'],'proof_file_sha256':sha(p),'guard_executed':False,'new_tests_run':0},indent=2))
