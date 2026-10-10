"""2026-10-08 ET: one synthetic private Git fixture; no managed or remote checkout."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

RESULT = Path('/private/tmp/lanl17-legacy-read-tree-sparse-roundtrip-fixture-result-20261008-a1.json')
assert not RESULT.exists()
root = Path(tempfile.mkdtemp(prefix='lanl17-legacy-read-tree-fixture-', dir='/private/tmp'))
repo, linked, other, raw = [root/name for name in ('repo','linked','other','raw')]
hooks=root/'empty-hooks';hooks.mkdir()
env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
env.update(GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0')
sparse_args=('-c','core.sparseCheckout=true','-c','core.sparseCheckoutCone=false','-c','index.sparse=false')
commands=[]
def git(where,*args,sparse=False):
    argv=['/usr/bin/git','-c','core.hooksPath='+str(hooks),'-c','core.fsmonitor=false',
          '-c','user.name=Synthetic Fixture','-c','user.email=synthetic@example.invalid']
    if sparse:argv.extend(sparse_args)
    argv.extend(('-C',str(where),*map(str,args)))
    r=subprocess.run(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
    assert len(r.stdout)<1024*1024 and len(r.stderr)<1024*1024
    commands.append({'argv':argv,'exit_code':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),
                     'stderr_sha256':hashlib.sha256(r.stderr).hexdigest(),'stdout_bytes':len(r.stdout),'stderr_bytes':len(r.stderr)})
    assert r.returncode==0,(argv,r.returncode,r.stderr.decode())
    return r.stdout

def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):return digest(p.read_bytes())
def stamp(p):
    s=p.lstat()
    return {k:getattr(s,k) for k in ('st_dev','st_ino','st_mode','st_uid','st_gid','st_nlink','st_size','st_mtime_ns','st_ctime_ns')}
def pin(p):return {'stat':stamp(p),'sha256':sha(p)}
def inventory(where):
    return {str(p.relative_to(where)):sha(p) for p in where.rglob('*')
            if p.is_file() and '.git' not in p.parts and p.name!='.git'}
def lib_state():
    lib=linked/'swdb-project/library'
    return {str(p.relative_to(linked)):{'stat':stamp(p),'sha256':sha(p) if p.is_file() else None}
            for p in (lib,*sorted(lib.rglob('*')))}
def links_state():return {str(p):{'stat':stamp(p),'literal':os.readlink(p)} for p in raw.glob('*/library')}
def check(condition,label):
    assert condition,label
    checks[label]=True
checks={}
repo.mkdir()
git(repo,'init','--initial-branch=fixture')
files={'README.md':b'root\n','.root-hidden':b'root hidden\n','swdb-project/AGENTS.md':b'parent\n',
       'swdb-project/library/.hidden.yaml':b'opaque hidden library\n',
       'swdb-project/library/include/a.hpp':b'library a\n','swdb-project/library/include/b.hpp':b'library b\n',
       'swdb-project/library/docs/note.md':b'library docs\n',
       'swdb-project/library-sibling/other.cpp':b'outside library\n',
       'swdb-project/swdb/module.py':b'outside module\n','other/out.txt':b'outside other\n'}
for name,body in files.items():
    p=repo/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
git(repo,'add','--all');git(repo,'commit','-m','Synthetic legacy sparse fixture')
head=git(repo,'rev-parse','HEAD').decode().strip()
git(repo,'worktree','add','--detach',linked,head)
git(repo,'worktree','add','--detach',other,head)
raw.mkdir()
for n in range(22):
    d=raw/str(n);d.mkdir();(d/'library').symlink_to(linked/'swdb-project/library',target_is_directory=True)
admin=Path(git(linked,'rev-parse','--absolute-git-dir').decode().strip())
other_admin=Path(git(other,'rev-parse','--absolute-git-dir').decode().strip())
pattern=Path(git(linked,'rev-parse','--path-format=absolute','--git-path','info/sparse-checkout').decode().strip())
check(pattern==admin/'info/sparse-checkout','pattern_resolves_only_to_linked_private_admin')
check(not pattern.exists() and not pattern.parent.exists(),'pattern_and_info_initially_absent')
configs=(repo/'.git/config.worktree',admin/'config.worktree',other_admin/'config.worktree')
check(all(not p.exists() for p in configs),'all_worktree_configs_initially_absent')
common_before=pin(repo/'.git/config')
primary_before=inventory(repo);primary_index=pin(repo/'.git/index')
other_before=inventory(other);other_index=pin(other_admin/'index')
linked_before=inventory(linked);library_before=lib_state();links_before=links_state()
pointer_before=pin(linked/'.git')
refs_before=git(repo,'show-ref');stage_before=git(linked,'ls-files','--stage');tree_before=git(linked,'write-tree')
pattern.parent.mkdir(mode=0o700)
with pattern.open('xb') as f:f.write(b'/swdb-project/library/\n')
pattern.chmod(0o600)
git(linked,'read-tree','-m','-u','HEAD',sparse=True)
check(inventory(linked)=={k:v for k,v in linked_before.items() if k.startswith('swdb-project/library/')},'exact_library_only_no_parent_root_files')
check(lib_state()==library_before,'all_library_file_directory_full_stats_and_bytes_unchanged')
check(links_state()==links_before,'all_22_raw_symlink_stats_literals_unchanged')
check(all((p/'include/a.hpp').read_bytes()==files['swdb-project/library/include/a.hpp'] for p in raw.glob('*/library')),'all_22_raw_library_resolutions_readable')
check(pin(repo/'.git/config')==common_before,'common_config_bytes_and_full_stat_exact_unchanged')
check(all(not p.exists() for p in configs),'no_config_worktree_created')
check(git(linked,'rev-parse','HEAD').decode().strip()==head and git(repo,'show-ref')==refs_before,'head_and_refs_unchanged')
check(git(linked,'write-tree')==tree_before and git(linked,'ls-files','--stage')==stage_before,'index_tree_and_full_staged_entries_unchanged')
check(git(linked,'status','--porcelain','--untracked-files=all')==b'','ordinary_selected_status_clean')
check(git(linked,'status','--porcelain','--untracked-files=all',sparse=True)==b'','explicit_sparse_selected_status_clean')
check(inventory(repo)==primary_before and pin(repo/'.git/index')==primary_index and git(repo,'status','--porcelain','--untracked-files=all')==b'','primary_files_index_and_ordinary_status_unchanged')
check(inventory(other)==other_before and pin(other_admin/'index')==other_index and git(other,'status','--porcelain','--untracked-files=all')==b'','other_worktree_files_index_and_ordinary_status_unchanged')
tagged=git(linked,'ls-files','-t').decode().splitlines()
check(all(x.startswith('H ') if x[2:].startswith('swdb-project/library/') else x.startswith('S ') for x in tagged),'skip_worktree_bitmap_matches_exact_library')
check(b'040000 ' not in git(linked,'ls-files','--sparse','--stage',sparse=True),'index_remains_full_no_sparse_directory_entries')
sparse_index_sha=sha(admin/'index')
pattern_after=pin(pattern)
# Restore using the documented all-inclusive pattern with the same command-local settings.
with pattern.open('r+b') as f:f.seek(0);f.write(b'/*\n');f.truncate()
git(linked,'read-tree','-m','-u','HEAD',sparse=True)
check(inventory(linked)==linked_before,'restoration_all_original_tracked_bytes')
check(lib_state()==library_before and links_state()==links_before,'restoration_library_and_all_raw_link_full_stats_exact')
check(git(linked,'ls-files','--stage')==stage_before and git(linked,'write-tree')==tree_before,'restoration_index_tree_and_staged_entries_exact')
check(all(x.startswith('H ') for x in git(linked,'ls-files','-t').decode().splitlines()),'restoration_clears_all_skip_worktree_bits')
pattern.unlink();pattern.parent.rmdir()
check(not pattern.exists() and not pattern.parent.exists() and all(not p.exists() for p in configs),'remove_only_new_pattern_info_no_config_residue')
check(git(linked,'status','--porcelain','--untracked-files=all')==b'' and git(linked,'status','--porcelain','--untracked-files=all',sparse=True)==b'','restored_status_clean_with_and_without_override')
check(pin(repo/'.git/config')==common_before and git(repo,'show-ref')==refs_before,'common_config_full_stat_refs_unchanged_through_roundtrip')
check(inventory(repo)==primary_before and pin(repo/'.git/index')==primary_index and inventory(other)==other_before and pin(other_admin/'index')==other_index,'primary_and_other_physical_index_unchanged_through_roundtrip')
check(pin(linked/'.git')==pointer_before,'linked_git_pointer_full_stat_bytes_unchanged')
result={'scope':'ONE local synthetic legacy read-tree fixture only; no actual source pool/storage/consumer/admission claim',
        'root':str(root),'git_version':git(repo,'--version').decode().strip(),'head':head,'checks':checks,
        'source_sha256':sha(Path(__file__)),'common_config_before_and_after':common_before,
        'pattern_after_sparse':pattern_after,'sparse_index_sha256':sparse_index_sha,
        'pattern_created_and_removed':str(pattern),'commands':commands,
        'limits':{'per_git_seconds':30,'per_stream_bytes':1024*1024},
        'restoration_limit':'All original tracked bytes restored; excluded files get new inodes; selected index administrative bytes not claimed equal.'}
with RESULT.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'path':str(RESULT),'bytes':RESULT.stat().st_size,'sha256':sha(RESULT),'root':str(root),'checks':len(checks)}))
