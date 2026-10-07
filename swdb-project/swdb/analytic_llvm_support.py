"""Native stateless LLVM support for static opt distributions. 2026-10-06 ET.
Only SHA256.cpp.o is linked; LLVM registries and whole archives are never duplicated.
"""
import subprocess
from pathlib import Path
from swdb import artifacts
from swdb.cli import Failure


def source_sha256_object(llvm,output,run,timeout):
    archive=Path(run([llvm/'llvm-config','--libdir']).stdout.strip())/'libLLVMSupport.a'
    if not archive.is_file():raise Failure('static LLVM source hashing requires native libLLVMSupport.a')
    for tool in ('llvm-ar','llvm-nm'):
        if not (llvm/tool).is_file():raise Failure('static LLVM source hashing requires native '+tool)
    member='SHA256.cpp.o'
    members=run([llvm/'llvm-ar','t',archive],timeout=timeout).stdout.splitlines()
    if members.count(member)!=1:raise Failure('native LLVM archive needs exactly one stateless SHA256.cpp.o member')
    archive_sha=artifacts.file_hash(archive)
    try:extracted=subprocess.run([str(llvm/'llvm-ar'),'p',str(archive),member],capture_output=True,timeout=timeout)
    except (OSError,subprocess.TimeoutExpired) as exc:raise Failure('native SHA256 extraction failed: '+str(exc)) from None
    if extracted.returncode or not extracted.stdout:raise Failure('native SHA256 extraction failed: '+extracted.stderr.decode(errors='replace')[-4000:])
    if artifacts.file_hash(archive)!=archive_sha:raise Failure('native LLVM support archive changed during extraction')
    obj=output/'llvm-sha256.o';obj.write_bytes(extracted.stdout)
    defined=run([llvm/'llvm-nm','--defined-only','--demangle',obj],timeout=timeout).stdout
    undefined=run([llvm/'llvm-nm','--undefined-only','--demangle',obj],timeout=timeout).stdout
    abi=('llvm::VerifyDisableABIBreakingChecks','llvm::VerifyEnableABIBreakingChecks')
    allowed_undefined=('llvm::DisableABIBreakingChecks','llvm::EnableABIBreakingChecks')
    if ('llvm::SHA256::hash' not in defined or any(token in defined for token in ('__cxx_global_var_init','_GLOBAL__sub_I'))
        or any('llvm::' in line and 'llvm::SHA256::' not in line and not any(name in line for name in abi) for line in defined.splitlines())
        or any('llvm::' in line and not any(name in line for name in allowed_undefined) for line in undefined.splitlines())):
        raise Failure('native SHA256 member is not isolated stateless hash support')
    return obj,{'format':'swdb.stateless-llvm-support.v1','archive':str(archive.resolve()),
        'archive_sha256':archive_sha,'member':member,'object_sha256':artifacts.file_hash(obj),
        'verification':'sha256_methods_and_abi_anchor_only_no_global_initializers'}
