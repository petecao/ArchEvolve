"""2026-10-16 ET. Passive retained-output warning addendum; no tools run."""
import ast, hashlib, json, pathlib, re

BASE=pathlib.Path('/private/tmp')
raw=BASE/'probata-t25-mac-typecheck-v2-304e03ac-20261016'
entry=BASE/'probata-t25-mac-typecheck-entry-v3-304e03ac-20261016.py'
receipt_path=raw/'typecheck/receipt.json'
def pin(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert pin(entry)['sha256']=='80a8839eb92a3cc5ea304f1f70c5f5fc9097e93aabf7be91df4adb5456e6e663'
assert pin(receipt_path)['sha256']=='f458c60a83e184ab015b6ac7f4ab81ceac1d12356a5183fa3832129e708c00e8'
receipt=json.loads(receipt_path.read_text())
metadata=BASE/'probata-t25-mac-why3-type-runtime-v1-20261016.json'
assert pin(metadata)['sha256']=='cd29ea964b4b50c6ead2090a265ee30c6e147a2728152d885edcffec85767028'
m=json.loads(metadata.read_text())
assert receipt['source_commit']=='304e03ac097352e78c3d3a637e13e951bef51dd0'
assert receipt['theory_git_blob']=='af3f31aefa824f6f407a5124b9acf5a21e4d0b09'
assert receipt['exit_code']==0 and not receipt['timed_out']
assert receipt['wp_launched'] is False and receipt['solver_launched'] is False
assert receipt['version_or_config_query_launched'] is False
assert receipt['model_proof_records_created']==0
for expected in [receipt['entry'],receipt['theory'],receipt['config'],*receipt['outputs']]:
    assert pin(pathlib.Path(expected['path']))==expected
assert receipt['theory']['sha256']=='a8f89e41decdbd2890f72e7725590c62134650fde84a18a6ec7fd9d5bd9abbc5'
assert receipt['config']['sha256']==m['fresh_config']['sha256']
assert receipt['runtime_before']==receipt['runtime_after']
for phase in ('runtime_before','runtime_after'):
    r=receipt[phase]
    assert r['stdlib']['files']==m['stdlib']['files'] and r['stdlib']['count']==57
    assert r['stdlib']['sha256']==m['stdlib']['sha256']
    assert r['native_binary_closure']==[{k:v for k,v in p.items() if k!='load_commands'}
                                        for p in m['native_binary_closure']]
guard_path=raw/'guard.log.summary.json';guard=json.loads(guard_path.read_text())
assert guard['exit_code']==0 and not guard['timed_out'] and not guard['killed_by_watchdog']
assert not guard['inspection_events'] and not guard['inspection_failure'] and not guard['unconfirmed_children']
tree=ast.parse(entry.read_text())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='parse_warnings')
env={'re':re};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(entry),'exec'),env)
stdout=(raw/'typecheck/stdout.txt').read_text()
stderr=(raw/'typecheck/stderr.txt').read_text()
warnings,unknown=env['parse_warnings'](stdout+'\n'+stderr,pathlib.Path(receipt['theory']['path']))
assert len(warnings)==1 and not unknown and stdout==''
out={'created':'2026-10-16 ET','reader':pin(pathlib.Path(__file__)),'actual_receipt':pin(receipt_path),
     'future_parser_entry_not_executed':pin(entry),'runtime_metadata':pin(metadata),
     'actual_output_pins':receipt['outputs'],'actual_guard':pin(guard_path),
     'source_commit':receipt['source_commit'],'theory':receipt['theory'],
     'theory_git_blob':receipt['theory_git_blob'],'actual_exit_code':receipt['exit_code'],
     'actual_v2_reader_warning_inventory':receipt['warnings'],
     'corrected_passive_warning_inventory':warnings,'unexpected_warnings':unknown,
     'status':'PASS syntax/types with exactly the known unused dummy warning',
     'actual_rerun':False,'scope':'Passive output classification only. Original v2/raw/receipt remain unchanged. Syntax/types do not certify WP import/task closure, models, typed-source image or caller composition.',
     'warning_reader_limit':'v2 colon-only regex silently omitted the actual comma-form warning; this separate pinned parser closes the retained actual output classification only',
     'native_runtime_limit':'producer pre/post file pins checked; OS dyld shared cache remains explicitly trusted',
     'guard_resources':{'wall_seconds':guard['wall_s'],'peak_rss_mib':guard['peak_rss_mb'],
                        'no_timeout_oom_or_inspection_failure':True}}
path=BASE/'probata-t25-mac-typecheck-passive-warning-audit-v1-304e03ac-20261016.json'
with path.open('x') as f:f.write(json.dumps(out,sort_keys=True,indent=2)+'\n')
print(json.dumps({'path':str(path),'sha256':pin(path)['sha256'],'warning_count':len(warnings),'unexpected':len(unknown)}))
