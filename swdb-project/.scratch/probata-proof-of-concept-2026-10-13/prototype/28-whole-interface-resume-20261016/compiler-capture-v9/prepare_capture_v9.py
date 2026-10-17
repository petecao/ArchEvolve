"""2026-10-16 ET. Inert full-TU token-preserving ingress assembly only."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('inert assembly refuses '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'compiler-capture-v8';INGRESS=WHOLE/'streaming-minify-v1';POC=WHOLE.parents[1]
OLD_RAW='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v8';NEW_RAW=OLD_RAW[:-1]+'9'
def pin(path,expected=None):
    path=Path(path).resolve(strict=True);data=path.read_bytes();row={'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    assert expected is None or row['sha256']==expected,(path,row['sha256']);return row
def write(name,value):(HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
def replace(text,old,new,edits):
    assert text.count(old)==1,(old,text.count(old));edits.append({'old':old,'new':new});return text.replace(old,new,1)
def transform(value):
    if isinstance(value,str):
        for before,after in ((OLD_RAW,NEW_RAW),(str(OLD),str(HERE)),('linux_compiler_capture_v8.py','linux_compiler_capture_v9.py'),
            ('linux_compiler_capture_policy_v8.json','linux_compiler_capture_policy_v9.json'),
            (str(WHOLE/'lossless-capture-v1/compiler_unit_adapter_v3.py'),str(INGRESS/'compiler_unit_adapter_v4.py')),
            (str(WHOLE/'lossless-capture-v1/lossless_gzip_v1.py'),str(INGRESS/'lossless_gzip_v2.py'))):value=value.replace(before,after)
        return value
    if isinstance(value,list):return [transform(v) for v in value]
    if isinstance(value,dict):return {transform(k):transform(v) for k,v in value.items()}
    return value
def changes(before,after,path=()):
    if before==after:return []
    if isinstance(before,dict) and isinstance(after,dict):
        rows=[]
        for key in sorted(set(before)|set(after)):
            if key not in before:rows.append({'path':list(path+(key,)),'operation':'add','new':after[key]})
            elif key not in after:rows.append({'path':list(path+(key,)),'operation':'remove','old':before[key]})
            else:rows.extend(changes(before[key],after[key],path+(key,)))
        return rows
    if isinstance(before,list) and isinstance(after,list) and len(before)==len(after):
        return [row for i in range(len(before)) for row in changes(before[i],after[i],path+(i,))]
    return [{'path':list(path),'old':before,'new':after}]
def main():
    codec=pin(INGRESS/'lossless_gzip_v2.py');mini=pin(INGRESS/'strict_minify_v1.py')
    adapter_old=pin(WHOLE/'compiler_unit_adapter_v2.py','1cf112859f976f77e8381c777c977f5cf5857d6e18f1bd0e24f9689148e80317')
    adapter=Path(adapter_old['path']).read_text();a_edits=[]
    adapter=replace(adapter,'Oversize evidence refuses under current 128/256-MiB retained-output caps.',
        'Original complete JSON tokens are retained after strict streaming whitespace\nremoval. The DOM parser still refuses above 128 MiB; gzip and minified artifacts\nboth count against the unchanged 256-MiB retained total.',a_edits)
    adapter=replace(adapter,'declarations, compiler_capture_pin):','declarations, compiler_capture_pin, full_tu_identity, full_tu_compressed_bytes):',a_edits)
    adapter=replace(adapter,'    need(len(full_tu_raw) + len(abi_raw) + len(source_bytes) + len(probe_bytes) <= TOTAL_BYTES,',
        '''    need(isinstance(full_tu_identity, dict) and set(full_tu_identity) == {
        "schema", "raw_bytes", "raw_sha256", "minified_bytes", "minified_sha256", "raw_limit", "retained_limit",
        "objects", "arrays", "values", "keys", "max_depth", "peak_live_key_charge",
        "complete_JSON_syntax_and_duplicate_key_check", "outside_string_whitespace_only_removed",
        "all_token_spellings_and_key_order_preserved", "AST_nodes_elided", "independent_filtered_parse_join",
        "downstream_complete_TU_consumer_required", "compiler_success_or_source_admission_inferred"},
         "exact complete token identity fields required")
    need(full_tu_identity.get("schema") == "full-tu-token-preserving-identity-1"
         and full_tu_identity.get("raw_limit") == 2147483648 and full_tu_identity.get("retained_limit") == STAGE_BYTES
         and type(full_tu_identity.get("raw_bytes")) is int and 0 < full_tu_identity["raw_bytes"] <= 2147483648
         and isinstance(full_tu_identity.get("raw_sha256"), str) and re.fullmatch("[0-9a-f]{64}", full_tu_identity["raw_sha256"])
         and type(full_tu_raw) is bytes and type(full_tu_identity.get("minified_bytes")) is int
         and 0 < full_tu_identity["minified_bytes"] <= full_tu_identity["raw_bytes"]
         and full_tu_identity.get("minified_bytes") == len(full_tu_raw)
         and full_tu_identity.get("minified_sha256") == sha(full_tu_raw), "exact complete raw/minified identity linkage required")
    for key, bound in {"objects": 20000000, "arrays": 20000000, "values": 20000000,
        "keys": 20000000 * 1024, "max_depth": 256, "peak_live_key_charge": 16777216}.items():
        need(type(full_tu_identity[key]) is int and 0 <= full_tu_identity[key] <= bound, "bounded token census required: " + key)
    need(full_tu_identity["values"] > 0, "nonempty complete token census required")
    for key, value in {"complete_JSON_syntax_and_duplicate_key_check": True,
        "outside_string_whitespace_only_removed": True, "all_token_spellings_and_key_order_preserved": True,
        "AST_nodes_elided": False, "independent_filtered_parse_join": False,
        "downstream_complete_TU_consumer_required": True, "compiler_success_or_source_admission_inferred": False}.items():
        need(type(full_tu_identity.get(key)) is type(value) and full_tu_identity[key] == value, "complete identity profile differs: " + key)
    need(type(full_tu_compressed_bytes) is int and 0 < full_tu_compressed_bytes <= STAGE_BYTES,
         "retained complete original gzip count required")
    need(full_tu_compressed_bytes + len(full_tu_raw) + len(abi_raw) + len(source_bytes) + len(probe_bytes) <= TOTAL_BYTES,''',a_edits)
    adapter=replace(adapter,'"schema": "whole-interface-original-tu-preparation-1"','"schema": "whole-interface-original-tu-preparation-2"',a_edits)
    adapter=replace(adapter,'"raw_full_tu_sha256": sha(full_tu_raw),',
        '"raw_full_tu_sha256": full_tu_identity["raw_sha256"], "parser_full_tu_sha256": sha(full_tu_raw),\n        "full_tu_identity": copy.deepcopy(full_tu_identity), "retained_full_tu_archive_bytes": full_tu_compressed_bytes,',a_edits)
    (INGRESS/'compiler_unit_adapter_v4.py').write_text(adapter);adapter_pin=pin(INGRESS/'compiler_unit_adapter_v4.py')
    entry_old=pin(OLD/'linux_compiler_capture_v8.py','937380eef851574e5d7c49c2cc31860c354a76258d5ff79d5813a9c76296728b')
    text=Path(entry_old['path']).read_text();e_edits=[]
    substitutions=[
      ('RAW_NAME = "probata-resume-20261016-t28-full-tu-2baf722f-v8"','RAW_NAME = "probata-resume-20261016-t28-full-tu-2baf722f-v9"'),
      ('ADAPTER_SHA = "775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c"','ADAPTER_SHA = "'+adapter_pin['sha256']+'"'),
      ('CODEC_SHA = "f93850883bdab523e59122812fa46877728127e8ba5997c567621347de739193"','CODEC_SHA = "'+codec['sha256']+'"\nMINIFIER_SHA = "'+mini['sha256']+'"'),
      ('recipe["lossless_caller_stdout"] = {"codec": "gzip-single-member", "expanded_limit": 536870912,',
       'recipe["caller_ast_phase_seconds"] = 120\n    recipe["other_phase_seconds"] = 45\n    recipe["lossless_caller_stdout"] = {"codec": "gzip-single-member", "expanded_limit": 2147483648,'),
      ('"expanded_memory_is_not_retained_disk_bytes": True}',
       '"expanded_memory_is_not_retained_disk_bytes": True,\n        "streaming_strict_token_preserving_minification": True, "minified_file_limit": STAGE_BYTES,\n        "raw_full_DOM_materialized": False, "complete_TU_parser_unchanged": True}'),
      ('capture = codec.Capture(zlib_module, stdout, expanded_limit=536870912,',
       'capture = codec.Capture(zlib_module, stdout, expanded_limit=2147483648,'),
      ('adapter = module("compiler_unit_adapter_v3.py", ADAPTER_SHA)','adapter = module("compiler_unit_adapter_v4.py", ADAPTER_SHA)'),
      ('codec = module("lossless_gzip_v1.py", CODEC_SHA)','codec = module("lossless_gzip_v2.py", CODEC_SHA)\n    minifier = module("strict_minify_v1.py", MINIFIER_SHA)'),
      ('        remaining = min(45, deadline - time.monotonic() - 10)',
       '        phase_seconds = 120 if item["phase"] == "caller-ast" else 45\n        remaining = min(phase_seconds, deadline - time.monotonic() - 10)'),
      ('''        with (out / "caller.ast.json.gz").open("rb") as compressed:
            full_tu_raw = codec.decode(zlib_module, compressed, stream_receipt, expanded_limit=536870912,
                compressed_limit=STAGE_BYTES, check=decode_check)''',
       '''        tentative = out / "caller.ast.minified.tentative"
        with (out / "caller.ast.json.gz").open("rb") as compressed, tentative.open("xb") as target:
            decoded = codec.DecodeReader(zlib_module, compressed, stream_receipt, expanded_limit=2147483648,
                compressed_limit=STAGE_BYTES, check=decode_check)
            identity = minifier.minify(decoded, target, raw_limit=2147483648,
                retained_limit=STAGE_BYTES, check=decode_check)
            if not decoded.verified or (identity["raw_bytes"], identity["raw_sha256"]) != (stream_receipt["expanded_bytes"], stream_receipt["expanded_sha256"]):
                raise ValueError("complete original gzip/minified JSON identity differs")
        decode_check()
        minified_path = out / "caller.ast.minified.json"
        os.rename(tentative, minified_path)
        minified_pin = pin(minified_path)
        if (minified_pin["bytes"], minified_pin["sha256"]) != (identity["minified_bytes"], identity["minified_sha256"]):
            raise ValueError("physical complete minified TU differs")
        save(out / "caller.ast.identity.json", identity)
        groups[0]["minified_ast"] = minified_pin
        groups[0]["token_identity"] = pin(out / "caller.ast.identity.json")
        full_tu_raw = minified_path.read_bytes()'''),
      ('full_tu_compressed_bytes=stream_receipt["compressed_bytes"], full_tu_expanded_limit=536870912)',
       'full_tu_identity=identity, full_tu_compressed_bytes=stream_receipt["compressed_bytes"])'),
      ('for k in ("ast", "ast_dependency", "expanded_stream_receipt") if k in group',
       'for k in ("ast", "ast_dependency", "expanded_stream_receipt", "minified_ast", "token_identity") if k in group')]
    for before,after in substitutions:text=replace(text,before,after,e_edits)
    (HERE/'linux_compiler_capture_v9.py').write_text(text);entry=pin(HERE/'linux_compiler_capture_v9.py')
    for current,previous,edits in ((text,Path(entry_old['path']).read_text(),e_edits),(adapter,Path(adapter_old['path']).read_text(),a_edits)):
        restored=current
        for edit in reversed(edits):assert restored.count(edit['new'])==1;restored=restored.replace(edit['new'],edit['old'],1)
        assert restored==previous and ast.dump(ast.parse(restored),include_attributes=False)==ast.dump(ast.parse(previous),include_attributes=False)
    old_policy=json.loads((OLD/'linux_compiler_capture_policy_v8.json').read_bytes());policy=transform(old_policy)
    policy['schema']='t28-whole-source-compiler-capture-9';policy['raw_name']=Path(NEW_RAW).name;policy['entry_sha256']=entry['sha256']
    api={'__name__':'inert_recipe'};exec(compile(text,'inert_recipe','exec'),api)
    aa={'__name__':'inert_adapter'};exec(compile(adapter,'inert_adapter','exec'),aa)
    class Adapter:pass
    selected=Adapter();selected.capture_recipe=aa['capture_recipe']
    policy['capture_recipe']=api['lossless_recipe'](selected,compiler=policy['compiler']['command'][0],project=policy['source_project'],raw=NEW_RAW)
    old_command=json.loads((OLD/'linux_compiler_capture_command_v8.json').read_bytes());staged=[]
    for row in old_command['controller_inputs']:
        if Path(row['path']).name=='linux_compiler_capture_policy_v8.json':continue
        staged.append(pin(transform(row['path'])))
    staged.append(mini);policy['controller_files']={Path(r['path']).name:{k:r[k] for k in ('bytes','sha256')} for r in staged}
    write('linux_compiler_capture_policy_v9.json',policy);policy_pin=pin(HERE/'linux_compiler_capture_policy_v9.json');staged.append(policy_pin)
    command=transform(old_command);command['controller_inputs']=staged;command['argv'][-1]=policy_pin['sha256'];command['recipe']=policy['capture_recipe']
    command['expanded_caller_stream_limit_bytes']=2147483648;command['caller_ast_phase_seconds']=120;command['other_phase_seconds']=45
    command['complete_TU_token_preserving_ingress']=True;command['raw_full_DOM_materialized']=False
    assert command['root_guard']==old_command['root_guard'] and command['node']==old_command['node']==1
    for key in old_policy:
        if key not in {'schema','raw_name','entry_sha256','controller_files','capture_recipe'}:assert policy[key]==old_policy[key],key
    write('linux_compiler_capture_command_v9.json',command);command_pin=pin(HERE/'linux_compiler_capture_command_v9.json')
    write('compiler-capture-v9-inverse.json',{'date':'2026-10-16 ET','predecessor':entry_old,'successor':entry,'entry_edits':e_edits,
        'adapter_predecessor':adapter_old,'adapter_successor':adapter_pin,'adapter_edits':a_edits,
        'entry_and_adapter_text_and_AST_inverse_exact':True,'policy_edits':changes(old_policy,policy),'command_edits':changes(old_command,command),
        'old_policy':pin(OLD/'linux_compiler_capture_policy_v8.json'),'old_command':pin(OLD/'linux_compiler_capture_command_v8.json'),
        'policy':policy_pin,'command':command_pin,'semantic_AST_functions_and_original_compiler_argv_unchanged':True,'actual_admission':False})
    validation={'executed':False}
    log=HERE/'pure-capture-v9-controls.log'
    if log.exists():
        report=json.loads(log.read_text().splitlines()[-1]);assert report['failures']==report['errors']==report['skips']==0 and report['child_events']==[]
        assert report['entry_sha256']==entry['sha256'] and report['adapter_sha256']==adapter_pin['sha256'] and report['controls_sha256']==pin(HERE/'test_capture_v9.py')['sha256']
        validation={'executed':True,'report':report,'log':pin(log)}
    packet={'date':'2026-10-16 ET','status':'SOURCE ONLY: complete original TU gzip plus strict token identity; no actual admission',
        'controller_inputs':staged,'command':command_pin,'inverse':pin(HERE/'compiler-capture-v9-inverse.json'),'preparation':pin(Path(__file__)),
        'controls':pin(HERE/'test_capture_v9.py'),'validation':validation,'files':[pin(INGRESS/name) for name in ('design.md','test_stream_minify_v1.py','pure-stream-minify-controls.log','author_codec_v2.py')],
        'predecessor_packet':pin(OLD/'compiler-capture-source-packet-v8.json','86f89b9513db5b74e7bcd80d766f484da6fa97ea726bec5c311fc92ae2fe6d08'),
        'V8_root_observation':pin(POC/'evidence/t28-capture-v8-root-observation-20261016t2130z.json'),
        'controls_bytes':sum(row['bytes'] for row in staged),'expanded_original_bytes':2147483648,'caller_ast_phase_seconds':120,'other_phase_seconds':45,
        'retained_per_file_bytes':134217728,'retained_total_bytes':268435456,'finalization_reserve_bytes':1048576,
        'guard_seconds':180,'entry_seconds':165,'rss_bytes':4294967296,'raw_full_DOM_materialized':False,'all_AST_tokens_nodes_fields_IDs_coordinates_retained':True,
        'semantic_projection_or_filtered_joins':False,'runtime_roles_guards_finalization_unchanged':True,'actual_time_RSS_and_file_sizes_unmeasured':True,
        'actual_capture':False,'public_proof':False,'current_0_2':False,'full_ticket28':False}
    assert packet['controls_bytes']<1048576 and not EVENTS;write('compiler-capture-source-packet-v9.json',packet)
    print(json.dumps(pin(HERE/'compiler-capture-source-packet-v9.json'),sort_keys=True))
if __name__=='__main__':main()
