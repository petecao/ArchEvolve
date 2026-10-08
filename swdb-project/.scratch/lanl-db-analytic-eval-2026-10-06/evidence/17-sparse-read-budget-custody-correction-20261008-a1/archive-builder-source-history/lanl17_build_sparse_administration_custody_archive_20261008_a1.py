"""2026-10-08 ET: prospective local archive-only builder. SOURCE ONLY / NOT RUN."""
import argparse
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import time
import zlib

WORKTREE=Path('/Users/yanrujhou/.codex/worktrees/lanl-ticket17/ArchEvolve')
BRANCH='codex/lanl17-storage-guard-cost'
BASE40='5e12a9796432654d88def24ecea617d16ca605b2'
REL=PurePosixPath('swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-library-preserving-sparse-retirement-custody-20261008-a1')
FORMAT='swdb.parent-sparse-administration-archive-input-materials.v1'
MAX_FILE=64*1024*1024
MAX_TOTAL=128*1024*1024
MAX_LEDGER=2*1024*1024
THRESHOLD=256*1024
CHUNK=1024*1024
class Refused(Exception):pass
def require(ok,code):
    if not ok:raise Refused(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def stamp(s):return {k:getattr(s,'st_'+k) for k in ('dev','ino','mode','uid','gid','nlink','size','mtime_ns','ctime_ns')}
def tick():require(time.monotonic()<DEADLINE,'archive_deadline')
def canonical(p):
    require(p.is_absolute() and p.resolve(strict=True)==p and not any(q.is_symlink() for q in (p,*p.parents)),'noncanonical_route')
def file_stat(p,cap):
    canonical(p);s=p.lstat()
    require(stat.S_ISREG(s.st_mode) and s.st_uid==os.geteuid() and s.st_nlink==1 and not s.st_mode&0o7000 and s.st_size<=cap,'original_file_identity_or_cap')
    return stamp(s)
def opened(p,cap,expected=None):
    before=file_stat(p,cap)
    if expected is not None:require(before==expected,'original_stat_drift')
    fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    f=os.fdopen(fd,'rb');require(stamp(os.fstat(f.fileno()))==before,'opened_stat_drift')
    return f,before
def final_read_check(p,f,before):require(stamp(os.fstat(f.fileno()))==before==file_stat(p,MAX_FILE),'closed_or_path_stat_drift')
def hash_file(p,cap,expected=None):
    f,before=opened(p,cap,expected);h=hashlib.sha256();count=0
    with f:
        while True:
            tick();b=f.read(CHUNK)
            if not b:break
            count+=len(b);require(count<=cap,'original_read_cap');h.update(b)
        require(count==before['size'],'original_size_drift');final_read_check(p,f,before)
    return {'bytes':count,'sha256':h.hexdigest(),'stat':before}
def read_small(p,cap):
    f,before=opened(p,cap)
    with f:
        b=f.read(cap+1);require(len(b)==before['size']<=cap,'metadata_returned_bytes');final_read_check(p,f,before)
    return b,before
def strict_json(b):
    def pairs(items):
        d={}
        for k,v in items:require(k not in d,'duplicate_json_key');d[k]=v
        return d
    def bad(v):raise Refused('nonfinite_json')
    return json.loads(b,object_pairs_hook=pairs,parse_constant=bad)
def git(*args):
    tick();env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1',GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_NO_LAZY_FETCH='1')
    r=subprocess.run(['/usr/bin/git','--no-replace-objects','--no-pager','-c','core.fsmonitor=false','-C',str(WORKTREE),*args],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
    require(r.returncode==0 and not r.stderr and len(r.stdout)<=16*1024*1024,'readonly_git_refused_warning_or_cap')
    return r.stdout
def repository_state():
    canonical(WORKTREE);s=WORKTREE.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==os.geteuid(),'worktree_owner')
    require(git('rev-parse','HEAD').strip().decode()==BASE40 and git('symbolic-ref','--short','HEAD').strip().decode()==BRANCH,'fixed_archive_worktree_head_branch')
    require(not git('diff','--name-only') and not git('diff','--cached','--name-only'),'tracked_or_cached_change')
    return {'head':BASE40,'branch':BRANCH,'tree':git('rev-parse','HEAD^{tree}').strip().decode(),
            'scientific_source_tree':git('rev-parse','HEAD:swdb-project/swdb').strip().decode(),
            'canonical_records_tree':git('rev-parse','HEAD:swdb-project/records').strip().decode(),
            'ref_inventory_sha256':sha(git('for-each-ref','--format=%(refname) %(objectname)')),
            'status':git('status','--porcelain=v1','--untracked-files=all')}
def safe_relative(text):
    require(isinstance(text,str) and text and len(text)<=300 and '\\' not in text and '\x00' not in text,'archive_relative_route')
    p=PurePosixPath(text)
    require(not p.is_absolute() and str(p)==text and all(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,180}',x) and x not in ('.','..') for x in p.parts),'archive_relative_component')
    require(p.parts[0] not in ('README.md','manifest.json'),'reserved_archive_name')
    return p
def mkdir_parents(p,root):
    require(p.is_relative_to(root),'archive_parent_escape')
    for q in reversed([p,*p.parents]):
        if not q.is_relative_to(root):continue
        if not os.path.lexists(q):os.mkdir(q,0o700)
        canonical(q);s=q.lstat();require(stat.S_ISDIR(s.st_mode) and s.st_uid==os.geteuid() and stat.S_IMODE(s.st_mode)==0o700,'archive_directory_identity')
def exclusive(p):
    return os.fdopen(os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600),'wb')
def copy_original(row,p,compressed):
    f,before=opened(Path(row['original_path']),MAX_FILE,row['_observed']['stat']);h=hashlib.sha256();count=0
    with f,exclusive(p) as out:
        if compressed:
            destination=gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0)
        else:destination=out
        try:
            while True:
                tick();b=f.read(CHUNK)
                if not b:break
                count+=len(b);require(count<=MAX_FILE,'copy_original_cap');h.update(b);require(destination.write(b)==len(b),'short_archive_write')
        finally:
            if compressed:destination.close()
        require(count==row['bytes'] and h.hexdigest()==row['sha256'],'copy_original_byte_pin')
        final_read_check(Path(row['original_path']),f,before)
        out.flush();os.fsync(out.fileno())
    return hash_file(p,MAX_FILE)
def decode_pin(p,compressed,expected,original_path,original_stat):
    f,before=opened(p,MAX_FILE);original,original_before=opened(original_path,MAX_FILE,original_stat);h=hashlib.sha256();count=0
    with f,original:
        source=gzip.GzipFile(mode='rb',fileobj=f) if compressed else f
        try:
            while True:
                tick();b=source.read(CHUNK)
                if not b:break
                count+=len(b);require(count<=MAX_FILE and count<=expected['bytes'],'decoded_archive_cap');require(original.read(len(b))==b,'decoded_original_whole_byte_difference');h.update(b)
        finally:
            if compressed:source.close()
        final_read_check(p,f,before);require(original.read(1)==b'','original_trailing_bytes');final_read_check(original_path,original,original_before)
    require(count==expected['bytes'] and h.hexdigest()==expected['sha256'],'decoded_original_equivalence')
    return {'bytes':count,'sha256':h.hexdigest()}
def write_metadata(p,b):
    require(len(b)<=MAX_LEDGER,'authored_metadata_cap')
    with exclusive(p) as f:require(f.write(b)==len(b),'short_metadata_write');f.flush();os.fsync(f.fileno())
    require(read_small(p,MAX_LEDGER)[0]==b,'authored_metadata_final_bytes')
def main():
    global DEADLINE
    a=argparse.ArgumentParser();a.add_argument('--input-ledger',required=True);a.add_argument('--input-ledger-sha256',required=True);a.add_argument('--builder-source-sha256',required=True)
    args=a.parse_args();os.umask(0o077);DEADLINE=time.monotonic()+900
    require(os.getuid()==os.geteuid() and re.fullmatch('[a-f0-9]{64}',args.input_ledger_sha256) and re.fullmatch('[a-f0-9]{64}',args.builder_source_sha256),'actual_source_ledger_pins')
    ledger_path=Path(args.input_ledger);require(str(ledger_path).startswith('/private/tmp/'),'explicit_private_ledger_route')
    self_path=Path(__file__).absolute();self_pin=hash_file(self_path,256*1024);require(self_pin['sha256']==args.builder_source_sha256,'builder_source_pin')
    b,ledger_stat=read_small(ledger_path,MAX_LEDGER);require(sha(b)==args.input_ledger_sha256,'ledger_returned_byte_pin');ledger=strict_json(b)
    require(isinstance(ledger,dict) and ledger.get('format')==FORMAT and ledger.get('sealed') is False and ledger.get('archive_relative_prefix')==str(REL) and ledger.get('branch')==BRANCH and ledger.get('expected_base')==BASE40,'ledger_exact_archive_contract')
    require(ledger.get('archive_builder_or_project_write_performed') is False and ledger.get('new_selected_control_and_copier_sources_still_pending') is False,'final_not_pending_ledger_required')
    rows=ledger.get('rows');require(isinstance(rows,list) and 1<=len(rows)<=192,'ledger_original_cardinality')
    root=WORKTREE/str(REL);require(not os.path.lexists(root),'absent_exact_archive_prefix')
    before=repository_state();require(before['status']==b'','initial_clean_worktree')
    routes=set();origins=set();prepared=[];total=0
    for original in rows:
        tick();require(isinstance(original,dict),'original_row_object')
        row=dict(original);require(type(row.get('bytes')) is int and 0<=row['bytes']<=MAX_FILE and isinstance(row.get('sha256'),str) and re.fullmatch('[a-f0-9]{64}',row['sha256']),'original_row_byte_pin')
        require(isinstance(row.get('original_path'),str) and isinstance(row.get('scope'),str) and isinstance(row.get('execution_or_evidence_boundary'),str),'original_row_metadata')
        source=Path(row['original_path']);require(str(source).startswith('/private/tmp/') and not source.is_relative_to(root),'explicit_original_private_route')
        relative=safe_relative(row.get('relative_archive_path'))
        compressed=row['bytes']>=THRESHOLD and (relative.name.lower().endswith('.json') or relative.name.lower().endswith('.stdout'))
        target=PurePosixPath(str(relative)+'.gz') if compressed else relative
        require(str(target) not in routes and str(source) not in origins,'duplicate_original_or_target_route');routes.add(str(target));origins.add(str(source))
        total+=row['bytes'];require(total<=MAX_TOTAL,'unique_original_total_cap')
        observed=hash_file(source,MAX_FILE);require(observed['bytes']==row['bytes'] and observed['sha256']==row['sha256'],'all_original_pins_before_publication')
        prepared.append((row,relative,target,compressed,observed))
    require(type(ledger.get('original_bytes_total')) is int and total==ledger['original_bytes_total'],'exact_ledger_total')
    # Refuse file/directory collisions before any prefix exists.
    for route in routes:
        require(not any(str(parent) in routes for parent in PurePosixPath(route).parents if str(parent)!='.'),'target_file_parent_collision')
    require(repository_state()==before and hash_file(self_path,256*1024)==self_pin and read_small(ledger_path,MAX_LEDGER)==(b,ledger_stat),'prepublication_full_recheck')
    for row,_,_,_,observed in prepared:require(hash_file(Path(row['original_path']),MAX_FILE,observed['stat'])==observed,'last_original_prepublication_recheck')
    # Existing evidence ancestors are traversed, never chmodded/created by this builder.
    canonical(root.parent);require(stat.S_ISDIR(root.parent.lstat().st_mode) and root.parent.lstat().st_uid==os.geteuid(),'owned_existing_evidence_parent')
    os.mkdir(root,0o700);manifest_rows=[]
    for row,relative,target,compressed,observed in prepared:
        out=root/str(target);mkdir_parents(out.parent,root)
        internal={**row,'_observed':observed};encoded=copy_original(internal,out,compressed);decoded=decode_pin(out,compressed,row,Path(row['original_path']),observed['stat'])
        require(stat.S_IMODE(out.lstat().st_mode)==0o600,'exclusive_archive_file_mode')
        manifest_rows.append({'original_claims':row,'relative_archive_path':str(target),'original_relative_archive_path':str(relative),
          'representation':'gzip-original-bytes' if compressed else 'original-bytes','encoded_bytes':encoded['bytes'],'encoded_sha256':encoded['sha256'],
          'original_bytes':decoded['bytes'],'original_sha256':decoded['sha256'],'original_stat':observed['stat'],'archive_stat':encoded['stat'],
          'original_json_seals_recomputed':False})
    note=('''# Library-preserving sparse retirement custody — 2026-10-08 ET\n\nThis additive archive preserves exact original source, preparation, observations and review bytes from the explicit parent-reviewed ledger. Gzip rows decode to those complete original bytes; no JSON fields or original seal/canonical-policy claims are rewritten. Earlier NOT RUN source histories remain creation-time facts. Any genuine synthetic or administrative execution is described only by its separate original custody.\n\nThe archive does not invoke selected guard/wrapper/control mains, authorize retirement or removal, assert consumer visibility or reserve, or supply scientific/campaign admission. Parent owns actual selection and execution.\n\nBuilder and input ledger remain separately pinned original files outside this archive unless explicitly named ledger rows. No circular manifest selfproof is asserted. All files here are newly created; prior tracked source, records, refs and current source tree remain unchanged.\n''').encode()
    write_metadata(root/'README.md',note)
    manifest={'format':'swdb.lanl17-library-preserving-sparse-retirement-archival-custody.v1','canonical_ensure_ascii':True,'created_date_ET':'2026-10-08',
      'source_base40':BASE40,'source_branch':BRANCH,'source_tree':before['tree'],'archive_relative_prefix':str(REL),
      'builder_original':{'path':str(self_path),'bytes':self_pin['bytes'],'sha256':self_pin['sha256']},
      'input_ledger_original':{'path':str(ledger_path),'bytes':len(b),'sha256':sha(b)},'original_rows':manifest_rows,'original_bytes_total':total,
      'readme':{'bytes':len(note),'sha256':sha(note)},'original_seal_policies_preserved_without_recomputation':True,
      'selected_control_mains_invoked':False,'cleanup_capacity_consumer_or_scientific_admission':False}
    manifest['identity_sha256']=sha(json.dumps(manifest,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
    mb=(json.dumps(manifest,sort_keys=True,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode();write_metadata(root/'manifest.json',mb)
    expected=routes|{'README.md','manifest.json'};actual=set()
    def walk_error(error):raise Refused('incomplete_archive_visibility') from error
    for directory,dirs,files in os.walk(root,followlinks=False,onerror=walk_error):
        for name in dirs:
            p=Path(directory)/name;canonical(p);require(stat.S_ISDIR(p.lstat().st_mode) and stat.S_IMODE(p.lstat().st_mode)==0o700,'archive_directory_final')
        for name in files:actual.add(str((Path(directory)/name).relative_to(root)))
    require(actual==expected,'exact_archive_file_inventory')
    for row in manifest_rows:
        out=root/row['relative_archive_path'];encoded=hash_file(out,MAX_FILE)
        require(encoded['bytes']==row['encoded_bytes'] and encoded['sha256']==row['encoded_sha256'] and encoded['stat']==row['archive_stat'],'final_archive_encoded_byte_stat')
        decode_pin(out,row['representation']=='gzip-original-bytes',{'bytes':row['original_bytes'],'sha256':row['original_sha256']},Path(row['original_claims']['original_path']),row['original_stat'])
        original=hash_file(Path(row['original_claims']['original_path']),MAX_FILE,row['original_stat'])
        require(original['bytes']==row['original_bytes'] and original['sha256']==row['original_sha256'],'final_all_original_byte_stats')
    require(read_small(root/'README.md',MAX_LEDGER)[0]==note and read_small(root/'manifest.json',MAX_LEDGER)[0]==mb,'final_authored_bytes')
    for directory,_,_ in os.walk(root,followlinks=False,onerror=walk_error):
        fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
        try:os.fsync(fd)
        finally:os.close(fd)
    after=repository_state();require({k:v for k,v in after.items() if k!='status'}=={k:v for k,v in before.items() if k!='status'},'prior_tree_refs_or_tracked_changes')
    status_lines=after['status'].splitlines()
    require(len(status_lines)==len(expected) and all(x.startswith(b'?? '+str(REL).encode()+b'/') for x in status_lines),'only_exact_archive_untracked_additions')
    require(hash_file(self_path,256*1024)==self_pin and read_small(ledger_path,MAX_LEDGER)==(b,ledger_stat),'final_builder_ledger_originals')
    print(json.dumps({'format':'swdb.sparse-administration-archive-only-builder-original.v1','sealed':False,'archive_relative_prefix':str(REL),'base40':BASE40,
      'original_rows':len(rows),'original_bytes':total,'added_files':len(expected),'manifest_file_sha256':sha(mb),'manifest_identity_sha256':manifest['identity_sha256'],
      'prior_tracked_tree_refs_preserved':True,'selected_mains_invoked':False,'cleanup_capacity_or_scientific_admission':False},sort_keys=True))
if __name__=='__main__':
    try:main()
    except (Refused,OSError,ValueError,TypeError,UnicodeError,EOFError,zlib.error,subprocess.SubprocessError) as e:
        print(json.dumps({'format':'swdb.sparse-administration-archive-builder-refusal.v1','sealed':False,'error_class':type(e).__name__,'error_digest':sha(str(e).encode()),'partial_archive_preserved':True}));raise SystemExit(1)
