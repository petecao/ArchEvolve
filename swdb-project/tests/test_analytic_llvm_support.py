"""Static LLVM pass support without duplicated registries. Updated: 2026-10-06 ET."""
import subprocess
import hashlib
from pathlib import Path
import sys
from testkit.analytic import characterize_command,llvm22,digest


def static_proxy(tmp_path,llvm22):
    proxy=tmp_path/'llvm-static-bin';proxy.mkdir()
    for name in ('opt','clang++','llvm-ar','llvm-nm'):(proxy/name).symlink_to(llvm22/name)
    config=proxy/'llvm-config'
    config.write_text(f'#!{sys.executable}\nimport subprocess,sys\n'+
        "if '--link-shared' in sys.argv:\n    print('error: libLLVM-22.so is missing',file=sys.stderr)\n    sys.exit(1)\n"+
        'sys.exit(subprocess.call(['+repr(str(llvm22/'llvm-config'))+',*sys.argv[1:]]))\n')
    config.chmod(0o755)
    return proxy


def test_static_pass_resolves_exact_sha256_without_full_static_llvm(records,tmp_path,llvm22):
    proxy=static_proxy(tmp_path,llvm22)
    data,pin=characterize_command(records,tmp_path,proxy)
    plugin=tmp_path/'counted/Characterize.so'
    unresolved=subprocess.run([llvm22/'llvm-nm','--undefined-only','--demangle',plugin],capture_output=True,text=True,check=True).stdout
    assert 'llvm::SHA256' not in unresolved
    defined=subprocess.run([llvm22/'llvm-nm','--defined-only','--demangle',plugin],capture_output=True,text=True,check=True).stdout
    assert 'llvm::SHA256::hash' in defined
    assert '__cxx_global_var_init' not in subprocess.run([llvm22/'llvm-nm','--defined-only','--demangle',tmp_path/'counted/llvm-sha256.o'],capture_output=True,text=True,check=True).stdout
    support=data['toolchain']['plugin_support_objects']
    assert len(support)==1 and support[0]['member']=='SHA256.cpp.o'
    assert support[0]['archive_sha256']==hashlib.sha256(Path(support[0]['archive']).read_bytes()).hexdigest()
    assert support[0]['object_sha256']==hashlib.sha256((tmp_path/'counted/llvm-sha256.o').read_bytes()).hexdigest()
    assert data['observation_contract']['plugin_support_objects_sha256']==digest(support)
    assert data['toolchain']['plugin_linkage']=='host_symbols'
    assert data['observation_contract']['semantic_commands']['complete'] is True
    assert sum(r['address_stream_counts'][pin]['line_requests']['value'] or 0 for r in data['regions'])==6
    valid=records.validate();assert valid.returncode==0,valid.stdout+valid.stderr

    # Re-signing the outer fixture identity cannot silently replace support code.
    support[0]['object_sha256']='0'*64
    data.pop('identity_sha256');data['identity_sha256']=digest(data)
    records.write('workload_characterizations/fixture.command.yaml',data)
    refused=records.validate()
    assert refused.returncode==1
    assert 'native stateless support differs from sealed observation metadata' in refused.stdout+refused.stderr
