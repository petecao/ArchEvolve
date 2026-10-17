"""2026-10-16 ET. Inert lossless transport successor; no compiler/controller main."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys

EVENTS=[]
def no_child(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        EVENTS.append(event);raise RuntimeError('inert capture assembly refuses '+event)
sys.addaudithook(no_child)
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'compiler-capture-v7';LOSSLESS=WHOLE/'lossless-capture-v1';POC=WHOLE.parents[1]
OLD_RAW='/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-full-tu-2baf722f-v7';NEW_RAW=OLD_RAW[:-1]+'8'
ORIGIN=POC/'evidence/t28-selected-python-zlib-origin-observation-20261016.json'
ORIGIN_SHA='bc53f66a5c159b43af8b3fbc69a0ec367c39197589e57fd8af505e5730ae4e3d'
BINDER='217cdda6ca8eaea99526010f2c379dad963ca81c18c79322ce02ab8cc9296ed8'

def pin(path,expected=None):
    path=Path(path).resolve(strict=True);data=path.read_bytes();row={'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    assert expected is None or row['sha256']==expected,(path,row['sha256']);return row

def write(name,value):
    (HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

def replace(text,old,new,edits):
    assert text.count(old)==1,(old,text.count(old));edits.append({'old':old,'new':new});return text.replace(old,new,1)

def transform(value):
    if isinstance(value,str):
        for old,new in ((OLD_RAW,NEW_RAW),(str(OLD),str(HERE)),('linux_compiler_capture_v7.py','linux_compiler_capture_v8.py'),
            ('linux_compiler_capture_policy_v7.json','linux_compiler_capture_policy_v8.json'),
            (str(WHOLE/'compiler_unit_adapter_v2.py'),str(LOSSLESS/'compiler_unit_adapter_v3.py')),
            ('compiler_unit_adapter_v2.py','compiler_unit_adapter_v3.py')):value=value.replace(old,new)
        return value
    if isinstance(value,list):return [transform(v) for v in value]
    if isinstance(value,dict):return {transform(k):transform(v) for k,v in value.items()}
    return value

def changes(before,after,path=()):
    if before==after:return []
    if isinstance(before,dict) and isinstance(after,dict):
        result=[]
        for key in sorted(set(before)|set(after)):
            if key not in before:result.append({'path':list(path+(key,)),'operation':'add','new':after[key]})
            elif key not in after:result.append({'path':list(path+(key,)),'operation':'remove','old':before[key]})
            else:result.extend(changes(before[key],after[key],path+(key,)))
        return result
    if isinstance(before,list) and isinstance(after,list) and len(before)==len(after):
        return [row for index in range(len(before)) for row in changes(before[index],after[index],path+(index,))]
    return [{'path':list(path),'old':before,'new':after}]

def main():
    origin_pin=pin(ORIGIN,ORIGIN_SHA);origin=json.loads(ORIGIN.read_bytes())
    assert origin['builtin']==1 and origin['spec_origin']=='built-in' and origin['module_file'] is None and origin['extension'] is None
    binding={key:origin[key] for key in ('interpreter','physical_interpreter','builtin','spec_origin','loader_type','module_file','extension',
        'ZLIB_VERSION','ZLIB_RUNTIME_VERSION','mapped_compression_objects')}
    codec=pin(LOSSLESS/'lossless_gzip_v1.py')
    adapter_before=pin(WHOLE/'compiler_unit_adapter_v2.py','1cf112859f976f77e8381c777c977f5cf5857d6e18f1bd0e24f9689148e80317')
    adapter=Path(adapter_before['path']).read_text();adapter_edits=[]
    adapter=replace(adapter,'Oversize evidence refuses under current 128/256-MiB retained-output caps.',
        'Retained output stays under 128/256 MiB. Lossless caller ingress has an explicit\n512-MiB expanded-memory bound; original full-TU semantics remain unchanged.',adapter_edits)
    adapter=replace(adapter,'def parse_json_roots(raw, *, full_tu=False):\n    need(type(raw) is bytes and 0 < len(raw) <= STAGE_BYTES, "compiler observation exceeds admitted per-file cap")',
        'def parse_json_roots(raw, *, full_tu=False, expanded_limit=None):\n    need(expanded_limit is None or (full_tu is True and type(expanded_limit) is int and 0 < expanded_limit <= 536870912),\n         "explicit full-TU expanded ingress bound required")\n    limit = STAGE_BYTES if expanded_limit is None else expanded_limit\n    need(type(raw) is bytes and 0 < len(raw) <= limit, "compiler observation exceeds explicit ingress cap")',adapter_edits)
    adapter=replace(adapter,'declarations, compiler_capture_pin):','declarations, compiler_capture_pin, full_tu_compressed_bytes, full_tu_expanded_limit):',adapter_edits)
    adapter=replace(adapter,'    need(len(full_tu_raw) + len(abi_raw) + len(source_bytes) + len(probe_bytes) <= TOTAL_BYTES,',
        '    need(type(full_tu_compressed_bytes) is int and 0 < full_tu_compressed_bytes <= STAGE_BYTES\n         and type(full_tu_expanded_limit) is int and full_tu_expanded_limit == 536870912\n         and type(full_tu_raw) is bytes and 0 < len(full_tu_raw) <= full_tu_expanded_limit,\n         "exact bounded lossless caller ingress required")\n    need(full_tu_compressed_bytes + len(abi_raw) + len(source_bytes) + len(probe_bytes) <= TOTAL_BYTES,',adapter_edits)
    adapter=replace(adapter,'parse_json_roots(full_tu_raw, full_tu=True)[0]','parse_json_roots(full_tu_raw, full_tu=True, expanded_limit=full_tu_expanded_limit)[0]',adapter_edits)
    (LOSSLESS/'compiler_unit_adapter_v3.py').write_text(adapter);adapter_pin=pin(LOSSLESS/'compiler_unit_adapter_v3.py')
    old_entry=pin(OLD/'linux_compiler_capture_v7.py','1dac57837a079b54d58b58cf2cf01c2b406099cff3ab9fdbc3f311463ee5a781')
    text=Path(old_entry['path']).read_text();entry_edits=[]
    fragment=(LOSSLESS/'controller_additions_v1.py').read_text();tree=ast.parse(fragment)
    additions='\n\n'.join(ast.get_source_segment(fragment,node) for node in tree.body if isinstance(node,ast.FunctionDef))
    for before,after in [
        ('import resource\n','import resource\nimport selectors\n'),
        ('RAW_NAME = "probata-resume-20261016-t28-full-tu-2baf722f-v7"','RAW_NAME = "probata-resume-20261016-t28-full-tu-2baf722f-v8"'),
        ('ADAPTER_SHA = "'+adapter_before['sha256']+'"','ADAPTER_SHA = "'+adapter_pin['sha256']+'"\nCODEC_SHA = "'+codec['sha256']+'"'),
        ('def main(argv):',additions+'\n\n\ndef main(argv):'),
        ('    adapter = module("compiler_unit_adapter_v2.py", ADAPTER_SHA)','    adapter = module("compiler_unit_adapter_v3.py", ADAPTER_SHA)\n    codec = module("lossless_gzip_v1.py", CODEC_SHA)\n    zlib_module, zlib_before = bind_zlib(policy)\n    save(raw / "capture-zlib-before.json", zlib_before)'),
        ('    recipe = adapter.capture_recipe(compiler=compiler["command"][0], project=str(project), raw=str(raw))',
         '    recipe = lossless_recipe(adapter, compiler=compiler["command"][0], project=str(project), raw=str(raw))'),
        ('        commands.append(row)\n        with stdout_path.open',
         '        commands.append(row)\n        if name == "caller-ast":\n            stream_caller_ast(item, out=out, environment=environment, remaining=remaining, bytes_used=bytes_used,\n                limit=limit, codec=codec, zlib_module=zlib_module, row=row)\n            return\n        with stdout_path.open'),
        ('            group["ast"] = pin(out / (label + ".ast.json"))',
         '            group["ast"] = pin(out / (label + (".ast.json.gz" if label == "caller" else ".ast.json")))\n            if label == "caller":\n                group["expanded_stream_receipt"] = pin(out / "caller.ast.gzip.json")'),
        ('        prepared = adapter.prepare_unit(binder.__dict__, full_tu_raw=(out / "caller.ast.json").read_bytes(),',
         '        stream_receipt = json.loads((out / "caller.ast.gzip.json").read_bytes())\n        def decode_check():\n            if time.monotonic() >= deadline - 10 or bytes_used() > TOTAL_BYTES - FINAL_METADATA_RESERVE:\n                raise ValueError("lossless decode entry deadline/output allowance exceeded")\n        with (out / "caller.ast.json.gz").open("rb") as compressed:\n            full_tu_raw = codec.decode(zlib_module, compressed, stream_receipt, expanded_limit=536870912,\n                compressed_limit=STAGE_BYTES, check=decode_check)\n        prepared = adapter.prepare_unit(binder.__dict__, full_tu_raw=full_tu_raw,'),
        ('            compiler_capture_pin=pin(out / "compiler-observation.json")["sha256"])',
         '            compiler_capture_pin=pin(out / "compiler-observation.json")["sha256"],\n            full_tu_compressed_bytes=stream_receipt["compressed_bytes"], full_tu_expanded_limit=536870912)\n        del full_tu_raw'),
        ('            recheck(original_inputs)\n            control_check()\n            for group in groups:',
         '            recheck(original_inputs)\n            control_check()\n            _zlib, zlib_after = bind_zlib(policy)\n            if zlib_after != zlib_before:\n                raise ValueError("zlib binding changed after capture")\n            save(raw / "capture-zlib-after.json", zlib_after)\n            for group in groups:'),
        ('for k in ("ast", "ast_dependency") if k in group','for k in ("ast", "ast_dependency", "expanded_stream_receipt") if k in group')]:
        text=replace(text,before,after,entry_edits)
    (HERE/'linux_compiler_capture_v8.py').write_text(text);entry=pin(HERE/'linux_compiler_capture_v8.py')
    for current,old,edits in ((text,Path(old_entry['path']).read_text(),entry_edits),(adapter,Path(adapter_before['path']).read_text(),adapter_edits)):
        restored=current
        for edit in reversed(edits):
            assert restored.count(edit['new'])==1;restored=restored.replace(edit['new'],edit['old'],1)
        assert restored==old and ast.dump(ast.parse(restored),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False)
    old_policy=json.loads((OLD/'linux_compiler_capture_policy_v7.json').read_bytes());policy=transform(old_policy)
    policy['schema']='t28-whole-source-compiler-capture-8';policy['raw_name']=Path(NEW_RAW).name;policy['entry_sha256']=entry['sha256']
    policy['zlib_binding']=binding;policy['zlib_origin_receipt_sha256']=ORIGIN_SHA
    assert policy['native_runtime']==old_policy['native_runtime'] and policy['startup_roles']==old_policy['startup_roles']
    assert binding['physical_interpreter'] in policy['native_runtime']['pins']
    assert all(row in policy['native_runtime']['pins'] for row in binding['mapped_compression_objects'])
    namespace={'__name__':'inert_adapter_recipe'};exec(compile(adapter,str(LOSSLESS/'compiler_unit_adapter_v3.py'),'exec'),namespace)
    class Adapter:pass
    selected_adapter=Adapter();selected_adapter.capture_recipe=namespace['capture_recipe']
    additions_api={'Path':Path,'STAGE_BYTES':134217728};exec(compile(additions,'inert_capture_recipe','exec'),additions_api)
    policy['capture_recipe']=additions_api['lossless_recipe'](selected_adapter,compiler=policy['compiler']['command'][0],project=policy['source_project'],raw=NEW_RAW)
    old_command=json.loads((OLD/'linux_compiler_capture_command_v7.json').read_bytes());staged=[]
    for row in old_command['controller_inputs']:
        if Path(row['path']).name=='linux_compiler_capture_policy_v7.json':continue
        staged.append(pin(transform(row['path'])))
    staged.extend((codec,origin_pin))
    policy['controller_files']={Path(row['path']).name:{k:row[k] for k in ('bytes','sha256')} for row in staged}
    write('linux_compiler_capture_policy_v8.json',policy);policy_pin=pin(HERE/'linux_compiler_capture_policy_v8.json');staged.append(policy_pin)
    command=transform(old_command);command['controller_inputs']=staged;command['argv'][-1]=policy_pin['sha256'];command['recipe']=policy['capture_recipe']
    command['expanded_caller_stream_limit_bytes']=536870912;command['lossless_full_original_TU']=True
    assert command['root_guard']==old_command['root_guard'] and command['node']==old_command['node']==1
    write('linux_compiler_capture_command_v8.json',command);command_pin=pin(HERE/'linux_compiler_capture_command_v8.json')
    write('compiler-capture-v8-inverse.json',{'date':'2026-10-16 ET','predecessor':old_entry,'successor':entry,'entry_edits':entry_edits,
        'adapter_predecessor':adapter_before,'adapter_successor':adapter_pin,'adapter_edits':adapter_edits,
        'entry_and_adapter_text_and_AST_inverse_exact':True,'policy_edits':changes(old_policy,policy),'command_edits':changes(old_command,command),
        'old_policy':pin(OLD/'linux_compiler_capture_policy_v7.json'),'old_command':pin(OLD/'linux_compiler_capture_command_v7.json'),
        'policy':policy_pin,'command':command_pin,'complete_original_TU':True,'scientific_or_public_admission':False})
    validation={'executed':False,'actual_compiler_or_controller_main':False}
    log=HERE/'pure-capture-v8-controls.log'
    if log.exists():
        report=json.loads(log.read_text().splitlines()[-1]);assert report['failures']==report['errors']==report['skips']==0 and report['child_events']==[]
        assert report['controller_sha256']==entry['sha256'] and report['adapter_sha256']==adapter_pin['sha256'] and report['codec_sha256']==codec['sha256']
        assert report['policy_sha256']==policy_pin['sha256'] and report['command_sha256']==command_pin['sha256'] and report['tests']==18
        assert report['controls_sha256']==pin(HERE/'test_capture_v8.py')['sha256']
        validation.update(executed=True,report=report,log=pin(log))
    files=[pin(LOSSLESS/name) for name in ('design.md','controller_additions_v1.py')]
    files.extend(pin(WHOLE/name) for name in ('test_compiler_unit_adapter_v2.py','test_whole_interface.py','whole_interface_v3.py'))
    packet={'date':'2026-10-16 ET','status':'SOURCE ONLY: lossless full original TU, root runtime metadata bound; no actual capture',
        'controller_inputs':staged,'command':command_pin,'inverse':pin(HERE/'compiler-capture-v8-inverse.json'),
        'preparation':pin(Path(__file__)),'controls':pin(HERE/'test_capture_v8.py'),'files':files,'validation':validation,
        'predecessor_packet':pin(OLD/'compiler-capture-source-packet-v7.json','d4806992407d16e3b2cdb3d8305af42f50fd4a5cfed54b91416465a5a406836f'),
        'V7_actual_failure_metadata':pin(POC/'evidence/t28-compiler-capture-v7-failure-metadata-20261016.json','c021c6cd2de3e060fff3581ba3772869a9184d7e26481343d58a7a35432fe745'),
        'zlib_origin_observation':origin_pin,'zlib_probe_source':pin(POC/'prototype/resume-root-20261016/observe_zlib_origin_v1.py','e91bb40d169616dc89f1c811fceb5ec0fb409f5d0701588041ff3d882fc808da'),
        'origin_scope_caption_20_bytes_is_typo_actual_fixed_literal_bytes':17,'inherited_origin_caption_not_used_as_semantic_input':True,
        'controls_bytes':sum(row['bytes'] for row in staged),'expanded_bytes':536870912,'retained_per_file_bytes':134217728,
        'retained_total_bytes':268435456,'finalization_reserve_bytes':1048576,'guard_seconds':180,'entry_seconds':165,'rss_bytes':4294967296,
        'runtime_and_startup_role_pins_unchanged':True,'all_semantic_AST_logic_unchanged':True,'actual_DOM_RSS_and_time_unmeasured':True,
        'reduced_projection_used':False,'actual_capture':False,'public_proof':False,'current_0_2':False,'full_ticket28':False}
    assert packet['controls_bytes']<1048576 and not EVENTS;write('compiler-capture-source-packet-v8.json',packet)
    print(json.dumps(pin(HERE/'compiler-capture-source-packet-v8.json'),sort_keys=True))

if __name__=='__main__':main()
