"""2026-10-16 ET. Inert until root admission: exact Git-blob syntax/type gate.

No WP, solver, version/config query, model proof or project package import.
The coordinator supplies an external 8 GiB / one-worker watchdog.
"""
import hashlib,json,os,pathlib,re,subprocess,sys
EXPECTED={'source_commit': '304e03ac097352e78c3d3a637e13e951bef51dd0', 'theory_path': 'swdb-project/swdb/heap_reallocation.mlw', 'theory_blob': 'af3f31aefa824f6f407a5124b9acf5a21e4d0b09', 'theory_sha256': 'a8f89e41decdbd2890f72e7725590c62134650fde84a18a6ec7fd9d5bd9abbc5', 'runtime_metadata_sha256': 'cd29ea964b4b50c6ead2090a265ee30c6e147a2728152d885edcffec85767028', 'runtime': {'actual_tools_executed': [], 'created': '2026-10-16 ET', 'fresh_config': {'bytes_utf8': '[main]\nmagic = 14\n', 'sha256': '25ddc07c274efd06de243a94fd0bc259f55d7bcb687f184c6ef89b94ed13bf48'}, 'logical_project_imports': ['int.Int', 'map.Map'], 'native_binary_closure': [{'load_commands': {'cpu_type': 16777228, 'dependencies': ['/usr/lib/libz.1.dylib', '/opt/homebrew/opt/gmp/lib/libgmp.10.dylib', '/usr/lib/libSystem.B.dylib'], 'rpaths': []}, 'path': '/Users/yanrujhou/.opam/framac-33/bin/why3', 'sha256': 'e90d62b3883a4c2f90c5260ff410ef019803eb08b5f72f3d3ade77d4ce6f0555'}, {'load_commands': {'cpu_type': 16777228, 'dependencies': ['/usr/lib/libSystem.B.dylib'], 'rpaths': []}, 'path': '/opt/homebrew/Cellar/gmp/6.3.0/lib/libgmp.10.dylib', 'sha256': 'bc6145edbeca608b4fecd4440dbbd7b27cacd55cbfd2b552b8bc333febe43b35'}], 'scope': 'static selected-file and Mach-O load-command metadata only; no actual executable queried', 'scope_limits': ['type-only will establish syntax/types only', 'OS dyld shared-cache dependencies are trusted host runtime, not file-hash claims', 'no model-body, imported-proof-task closure, typed-source-image/caller admission, solver or WP result'], 'stdlib': {'count': 57, 'files': [{'path': 'algebra.mlw', 'sha256': '39d64b3f351a3a08a391d6d26467e427d9ad61799a0ea93ad9cf85d0acbc4fb4'}, {'path': 'array.mlw', 'sha256': '5e1abb583bb14cc1821612859b94568a586419d0dbe0d6752f8835ac098362b6'}, {'path': 'bag.mlw', 'sha256': 'b5e8f1b8b7a6d4de57571d26ad356a161197fedc7cfd3e104a877a1e12c1bca5'}, {'path': 'bintree.mlw', 'sha256': 'b651b0989affbee0364a58daa48d77f94ec5a7acaff86f09cd4536d0472dcaf9'}, {'path': 'bool.mlw', 'sha256': 'b7072fdd8dd5004d0627b82a66b054518ee54eb4dd66f0883988e363bed251fa'}, {'path': 'bv.mlw', 'sha256': '1c62539b31bfb75042a0b31559ffca9f87429fcfdccc8ed1772b65f0f4131110'}, {'path': 'byte_string.mlw', 'sha256': '75480d65a76ed317e88be7d50f593a314b6b94f8eac9f39a1af73adc0a49178f'}, {'path': 'cursor.mlw', 'sha256': '5e6554c0e39cba91c92c59d6b7318364f032a6adbb17ca98bdcb2c08d16de701'}, {'path': 'debug.mlw', 'sha256': 'c79c4fa42774dd4c92000c2fb40f2c66029630f65cd8a3262fa9881579167cdb'}, {'path': 'exn.mlw', 'sha256': '5aa489183cfcc45d081c9cf0af98b3636ebdde5860fd5a6d9222aa8bbb9d63f1'}, {'path': 'floating_point.mlw', 'sha256': '0fc1c5bcdb2812e9fd173199de8f767b8a27f5dbcc8072ca4fd543b04071aa8f'}, {'path': 'fmap.mlw', 'sha256': 'fbda0657de5bb9813aa279daed748fb384d8ba827cd8987fb130f25c703faa15'}, {'path': 'for_drivers.mlw', 'sha256': 'e892ad394b50de0da1a2ed0e514d82632f3d79e57ac61294ad2d586b68883179'}, {'path': 'function.mlw', 'sha256': 'f1ddf9c3ce7b8fcda55d05f7b4b41612afd739256ccf131a6dce444a80f5a87f'}, {'path': 'graph.mlw', 'sha256': 'c9fdd8de698c4899486056d37999a819d9258fd6b3782a23dbf0eb32f9a5ccb4'}, {'path': 'hashtbl.mlw', 'sha256': '348c2084411cfb5fa5bf4babaa90ee34ee55f9303487141d7f30856aa3720b20'}, {'path': 'ieee_float.mlw', 'sha256': '57a096bcb20309ab323405fabfeb67699037289dc0223368526adab32fa9d6a7'}, {'path': 'int.mlw', 'sha256': 'eb5bc9d4a46e1b6a298d24fd36dcf9dfb8f35cbc75b2f44007cfe1a24550ce8d'}, {'path': 'io.mlw', 'sha256': 'e46fde974c5cc062222fad6f2f9813fc2f1e0d1c09bdcb6d701fe41d0ea1d6ae'}, {'path': 'list.mlw', 'sha256': '29b8f5925862ce3c4fb47bae171247b247b450cfcd56f6fc49db3c5b4b162ee9'}, {'path': 'mach/array.mlw', 'sha256': 'b27c51c8cc0e4de11f0b4acbec05e4ea17de77dfc3af789bd5237f504b1c9861'}, {'path': 'mach/bv.mlw', 'sha256': '5e5c6bc76cbc55aec6d6ed5588fcc047dcce74c88e0394b3aa94ac1fa3ef0b94'}, {'path': 'mach/c.mlw', 'sha256': '7c847a149a2759820689b6e8229f4399698c14b2f850691c3d8f343d05ad08f4'}, {'path': 'mach/float.mlw', 'sha256': 'f83ca3bedf58a5064b8947400248d79997e83e202fac0bc6796699442888bb44'}, {'path': 'mach/fxp.mlw', 'sha256': '43c4ab90b6ebcf835194e50d2a18cef6864281e32c71d3a446cf9a48a74c5ea1'}, {'path': 'mach/int.mlw', 'sha256': '8b15e61d54e9fa0e86e28ba552a13a50afdc752c75c183b5fec483b2f0ae20de'}, {'path': 'mach/java/io.mlw', 'sha256': '3f15f978b231cbbfbcac8708d082b7b5be486f50d4c10666a14f28152bd11416'}, {'path': 'mach/java/lang.mlw', 'sha256': '355faf72f66a6ab0effc7d178f28fe78b69731add875a42975fbc4e837f5a0ca'}, {'path': 'mach/java/util.mlw', 'sha256': '407c1895c9b5a1311ac601c179dadf39c0f8343840b09823cfb72b579d437797'}, {'path': 'mach/list.mlw', 'sha256': '6618c9c030120189006f2a48b14d14b0baa9ffb6e6446e07e2f1997b27b25e2c'}, {'path': 'mach/matrix.mlw', 'sha256': '3a72bf9c0dc6751943ebdd647a362719f9cd360af2d954c714acd639510f1950'}, {'path': 'mach/onetime.mlw', 'sha256': '8e45739bcfc995055086a57d4fcfbb836252334c65a855c9dcd299a59801a6d1'}, {'path': 'mach/peano.mlw', 'sha256': '210c67ce2ab36aff9764537f4e884db02ae4b0d8463b92460848d8183bf6d0aa'}, {'path': 'mach/tagset.mlw', 'sha256': '58a641b42a874f8e63228a4d0be57d6ee8b6340508d31746dde339a7da574c5b'}, {'path': 'map.mlw', 'sha256': 'c4cd7b90e39f8407fd714d0e46ce4c6496a98afd32bd69c71237b35a4b7c08a0'}, {'path': 'matrix.mlw', 'sha256': '0ceeed3e742e47de3ef4bf01042a69dcf501b119010b1de6b0fc2b0d2266efde'}, {'path': 'microc.mlw', 'sha256': 'd7322664cc4d419d6d7101fcdab0587896353eca9df3aa41be1effb0c3891eed'}, {'path': 'number.mlw', 'sha256': '4d0d83a9718774a342234ff8ef67e4545840629ffb0ee508f900d8fd67f83911'}, {'path': 'ocaml.mlw', 'sha256': '1777a1f306b54d3cd73afb45d9330eccbcb673d0287c7ee8a6ba0c282578db51'}, {'path': 'option.mlw', 'sha256': 'ba5607ebfa8fb060cede3798d21241b43de090046724084a3efc1f90a308a6df'}, {'path': 'pigeon.mlw', 'sha256': '584baeb86de6831ac02d2a379aaa9a16fde47495603acb78c5796b334cdcd0e3'}, {'path': 'pqueue.mlw', 'sha256': 'edad87a86e411409aa8b5be43993022066f05e951217b12b37ed7b0b45888420'}, {'path': 'python.mlw', 'sha256': '5e44344331a4deb815b92bf800bef051be2764b18e5ed889d2e7f77613f951f7'}, {'path': 'queue.mlw', 'sha256': '28c577b16c6ddb2be23273f764c70936164842e7f7b2ef3b4125e2fcfc7a0463'}, {'path': 'random.mlw', 'sha256': '39371d90d75a70bde82c2a0a8340d414d22eab8197983e77b27ff8bf75f5dd9b'}, {'path': 'real.mlw', 'sha256': '50940038bba54f6bd57501e5af6439af8c4f081274eb79a19d888a4cd419b8a2'}, {'path': 'ref.mlw', 'sha256': 'f54413bf62b69bbfb996bd7d6a8098c18e4663f95f788623f729dd8eb5a60bea'}, {'path': 'regexp.mlw', 'sha256': '0eaf9277c63569edf20606d3de5fc96522348b5a4c37e9b83fdfca2b011ec8c0'}, {'path': 'relations.mlw', 'sha256': '0a367aecd2cd627de87d5f4011ddbf930bf49283e0b94b792a338faf921b2cae'}, {'path': 'seq.mlw', 'sha256': '9acfebda1e49dd3b6090f77e6c9ac518e05a3e61a25c4efaaa63cd9090444eb8'}, {'path': 'set.mlw', 'sha256': 'c5dca5e35ca7198ed7c732b22ec5686cb40c0a7edc9f4ecde783f4ebef744498'}, {'path': 'stack.mlw', 'sha256': 'ef10f41813802ad069ab1bf7444a4e271570439f568c6f24fb0ec119588b1f30'}, {'path': 'string.mlw', 'sha256': 'ea9e41823b857ebbe08fe5ba71687f3894946efd21748703d89a83df6b99e3ec'}, {'path': 'tptp.mlw', 'sha256': 'b095a34e17d52bd10837aec0cd5db3090cbb6f86918707402eebadafab4dc97d'}, {'path': 'tree.mlw', 'sha256': '9871c40b442266715678814a1f80298f99af054e8be70abc58826e04e91cefd7'}, {'path': 'ufloat.mlw', 'sha256': 'cd4a4f4c0d73b895f6735a8d5501be56b0cb9db19ccc80715b792c5e001dc7c3'}, {'path': 'witness.mlw', 'sha256': '74098a4e80908fb5719b04e741a36cac977f180d837b6ffc0238fe1d915d609a'}], 'path': '/Users/yanrujhou/.opam/framac-33/share/why3/stdlib', 'sha256': '520d9875983b41da80b89d7809cff4c76370e8445f8b49147f1423cfb7404c31'}, 'trusted_OS_dependencies': [{'binding': 'host OS dyld shared-cache trust; file bytes not claimed pinned', 'install_name': '/usr/lib/libz.1.dylib', 'loader': '/Users/yanrujhou/.opam/framac-33/bin/why3'}, {'binding': 'host OS dyld shared-cache trust; file bytes not claimed pinned', 'install_name': '/usr/lib/libSystem.B.dylib', 'loader': '/opt/homebrew/Cellar/gmp/6.3.0/lib/libgmp.10.dylib'}, {'binding': 'host OS dyld shared-cache trust; file bytes not claimed pinned', 'install_name': '/usr/lib/libSystem.B.dylib', 'loader': '/Users/yanrujhou/.opam/framac-33/bin/why3'}], 'why3': {'path': '/Users/yanrujhou/.opam/framac-33/bin/why3', 'sha256': 'e90d62b3883a4c2f90c5260ff410ef019803eb08b5f72f3d3ade77d4ce6f0555'}}}

repo=pathlib.Path(sys.argv[1]).resolve()
raw=pathlib.Path(sys.argv[2]).resolve()
if raw.is_relative_to(repo) or not raw.is_dir():
    raise SystemExit('existing external raw directory required')
out=raw/'typecheck';out.mkdir(exist_ok=False)
def digest(data): return hashlib.sha256(data).hexdigest()
def save(name,value): (out/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
def git(*args):
    return subprocess.check_output(['/usr/bin/git','--no-replace-objects','-C',str(repo),*args],timeout=30)
def pin(path):
    p=pathlib.Path(path)
    return {'path':str(p.resolve(strict=True)),'sha256':digest(p.read_bytes())}
def parse_warnings(text, staged):
    # Capture every warning-bearing line and any continuation, including Why3's
    # comma/file form. Unknown formats/text fail closed rather than disappearing.
    starts=list(re.finditer(r'(?im)^.*\bwarning\b[^\n]*',text))
    records=[text[m.start():(starts[i+1].start() if i+1<len(starts) else len(text))].strip()
             for i,m in enumerate(starts)]
    plain=r'Warning:\s*unused variable dummy'
    located=(r'Warning,\s*file\s+"'+re.escape(str(staged))+
             r'",\s*line\s+25,\s*characters\s+18-23:\s*unused variable dummy')
    unknown=[w for w in records if not (re.fullmatch(plain,w) or re.fullmatch(located,w))]
    return records,unknown

def runtime_check():
    m=EXPECTED['runtime']; binary=[]
    for want in m['native_binary_closure']:
        got=pin(want['path'])
        if got['path']!=want['path'] or got['sha256']!=want['sha256']:
            raise SystemExit('selected native binary drift')
        binary.append(got)
    if pathlib.Path('/opt/homebrew/opt/gmp/lib/libgmp.10.dylib').resolve(strict=True)!=pathlib.Path(binary[1]['path']):
        raise SystemExit('GMP loader install-name target drift')
    root=pathlib.Path(m['stdlib']['path'])
    paths=list(root.rglob('*'))
    if root.is_symlink() or any(p.is_symlink() for p in paths):
        raise SystemExit('unexpected stdlib symlink')
    files=sorted(p for p in paths if p.is_file())
    if any(p.suffix!='.mlw' for p in files):
        raise SystemExit('unexpected non-mlw standard-library file')
    if any(not p.is_file() and not p.is_dir() for p in paths):
        raise SystemExit('unexpected special standard-library entry')
    rows=[{'path':str(p.relative_to(root)),'sha256':digest(p.read_bytes())} for p in files]
    tree=digest(json.dumps(rows,sort_keys=True,separators=(',',':')).encode())
    if rows!=m['stdlib']['files'] or tree!=m['stdlib']['sha256']:
        raise SystemExit('selected standard library drift')
    return {'native_binary_closure':binary,'stdlib':{'path':str(root),'count':len(rows),'sha256':tree,'files':rows},'trusted_OS_dependencies':m['trusted_OS_dependencies']}
forbidden=sorted(k for k in os.environ if k.startswith(('DYLD_','WHY3')) or k=='CAML_LD_LIBRARY_PATH')
if forbidden:
    save('ambient-refusal.json',{'forbidden_present_names':forbidden})
    raise SystemExit('unreviewed Why3/native runtime overlay')
commit=git('rev-parse','--verify',EXPECTED['source_commit']+'^{commit}').decode().strip()
if commit!=EXPECTED['source_commit']: raise SystemExit('source commit mismatch')
ref=commit+':'+EXPECTED['theory_path']
blob=git('rev-parse','--verify',ref).decode().strip()
data=git('cat-file','blob',ref)
if blob!=EXPECTED['theory_blob'] or digest(data)!=EXPECTED['theory_sha256']:
    raise SystemExit('theory Git blob mismatch')
pre=runtime_check()
theory=out/'heap_reallocation.mlw';theory.write_bytes(data)
config=out/'minimal-why3.conf';config.write_bytes(EXPECTED['runtime']['fresh_config']['bytes_utf8'].encode())
if digest(config.read_bytes())!=EXPECTED['runtime']['fresh_config']['sha256']:
    raise SystemExit('fresh minimal config mismatch')
cmd=[EXPECTED['runtime']['why3']['path'],'prove','--type-only','--no-stdlib','--no-load-default-plugins','--config',str(config),'-L',EXPECTED['runtime']['stdlib']['path'],str(theory)]
receipt={'created':'2026-10-16 ET','source_commit':commit,'theory_path':EXPECTED['theory_path'],'theory_git_blob':blob,'theory':pin(theory),'entry':pin(__file__),'runtime_metadata_sha256':EXPECTED['runtime_metadata_sha256'],'runtime_before':pre,'config':pin(config),'command':cmd,'forbidden_ambient_present_names':forbidden,'scope':'Why3 syntax/typecheck only. No WP import/task, solver, model-body or caller proof acceptance. Host OS dyld shared cache is explicitly trusted.','version_or_config_query_launched':False,'wp_launched':False,'solver_launched':False,'model_proof_records_created':0,'expected_warnings':['unused variable dummy'],'syntax_typecheck_passed':False}
save('receipt.json',receipt)
try:
    proc=subprocess.run(cmd,cwd=out,env=dict(os.environ),capture_output=True,timeout=60)
    stdout,stderr=proc.stdout,proc.stderr
    receipt['exit_code']=proc.returncode
    receipt['timed_out']=False
except subprocess.TimeoutExpired as exc:
    stdout,stderr=exc.stdout or b'',exc.stderr or b''
    receipt['exit_code']=None;receipt['timed_out']=True
(out/'stdout.txt').write_bytes(stdout);(out/'stderr.txt').write_bytes(stderr)
receipt['outputs']=[pin(out/'stdout.txt'),pin(out/'stderr.txt')]
receipt['runtime_after']=runtime_check()
if theory.read_bytes()!=data or config.read_bytes()!=EXPECTED['runtime']['fresh_config']['bytes_utf8'].encode():
    save('receipt.json',receipt);raise SystemExit('staged input drift')
text=(stdout+b'\n'+stderr).decode('utf-8',errors='replace')
warnings,unknown=parse_warnings(text,theory)
receipt['warnings']=warnings
receipt['unexpected_warnings']=unknown
receipt['syntax_typecheck_passed']=bool(receipt['exit_code']==0 and not receipt['timed_out'] and not receipt['unexpected_warnings'])
save('receipt.json',receipt)
raise SystemExit(0 if receipt['syntax_typecheck_passed'] else 1)
