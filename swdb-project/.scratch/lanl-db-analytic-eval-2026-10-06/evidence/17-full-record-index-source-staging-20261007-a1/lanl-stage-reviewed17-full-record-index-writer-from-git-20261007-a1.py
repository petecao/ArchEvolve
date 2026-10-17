"""NOT RUN: parent source-copy-only staging of reviewed index writer7a67.

Future invocation requires parent review and parent-owned SSH. This program
copies only one exact delivered Git blob, never imports/executes the writer,
constructs actual inputs, reads a catalog, or runs tests/scientific commands.
No environment/authentication contents are inspected. Earlier staged controls
are neither opened nor modified. Original review/manifest True seals are kept.
"""
import hashlib
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess


REVISION = 'f8ef24f61063e52f3f41402e5babdfcdf218a09e'
WRITER_SHA = '7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b'
WRITER_BYTES = 33445
REVIEW_SHA = 'a6a91057706d6fba2987c5614ee9e0e44ef93ecdc8eea30e66b05e9f12efda41'
REVIEW_ID = '7b3b5a02b14ce8fa16c86539869897f8bd8bf7fb8a2578cde3a3b97f166d8f39'
MANIFEST_SHA = '94a9195570b997603742ea14eeb2008a55707c9ea72ba12f45ec7fd87d8dfac3'
MANIFEST_ID = '68419007c6408735ba039365a8543373820eaf89bce5d3bf3535515d8f3acbf3'
OUTPUT = Path('/private/tmp/lanl17-reviewed-full-record-index-source-staging-actual-20261007-a1.json')

REMOTE = r'''
import datetime,hashlib,json,os,pathlib,pwd,socket,stat,subprocess,sys,time
P=pathlib.Path
assert sys.platform=='linux' and socket.gethostname()=='mbit10'
assert os.getuid()==os.geteuid()==114316761 and pwd.getpwuid(os.getuid()).pw_name=='yanruj'
deadline=time.monotonic()+45
revision='f8ef24f61063e52f3f41402e5babdfcdf218a09e'
writer_sha='7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b'
folder='swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-parent-full-record-index-controls-20261007/'
writer_path=folder+'lanl17_write_parent_full_record_index_20261007.py'
review_path=folder+'lanl17-parent-full-record-index-parent-review-20261007.json'
manifest_path=folder+'manifest.json'
def remaining():
 value=deadline-time.monotonic();assert value>0,'Bounded source-copy deadline exceeded';return value
def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
def strict_json(raw):
 def pairs(rows):
  result={}
  for key,value in rows:assert key not in result,'Duplicate original custody key';result[key]=value
  return result
 def nonfinite(value):raise AssertionError('Nonfinite original custody value')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=nonfinite)
def path_checked(path,directory=False):
 p=P(path);assert p.is_absolute() and '..' not in p.parts and all(not v.is_symlink() for v in (p,*p.parents))
 p=p.resolve(strict=True);s=p.stat();assert s.st_uid==os.getuid()
 assert stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode)
 return p
base=path_checked('/data1/yanruj',True);repo=path_checked(base/'ArchEvolve',True)
def git(*args):
 # Literal inert Git environment; do not read inherited environment or auth.
 env={'PATH':'/usr/bin:/bin','LANG':'C','GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0',
      'GIT_OPTIONAL_LOCKS':'0','GIT_PAGER':'cat','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
 return subprocess.check_output(['/usr/bin/git','-c','protocol.allow=never','-c','core.fsmonitor=false',
                                 '-C',str(repo),*args],timeout=min(15,remaining()),env=env)
def source_gate():
 assert git('rev-parse','--show-toplevel').decode().strip()==str(repo)
 assert git('rev-parse','HEAD').decode().strip()==revision
 assert git('branch','--show-current').decode().strip()=='yanrujhou_main'
 assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
def original_blob(path,size,expected):
 rows=[r for r in git('ls-tree','-z',revision,'--',path).split(b'\0') if r]
 assert len(rows)==1
 meta,name=rows[0].split(b'\t',1);assert name.decode()==path and meta.split()[:2]==[b'100644',b'blob']
 raw=git('cat-file','blob',revision+':'+path)
 assert len(raw)==size and sha(raw)==expected
 return raw
def sealed(raw,identity,format):
 value=strict_json(raw);assert value['format']==format and value['canonical_ensure_ascii'] is True
 assert value['identity_sha256']==identity==digest({k:v for k,v in value.items() if k!='identity_sha256'})
 return value
source_gate()
raw=original_blob(writer_path,33445,writer_sha)
review_raw=original_blob(review_path,5432,'a6a91057706d6fba2987c5614ee9e0e44ef93ecdc8eea30e66b05e9f12efda41')
review=sealed(review_raw,'7b3b5a02b14ce8fa16c86539869897f8bd8bf7fb8a2578cde3a3b97f166d8f39','swdb.lanl17-parent-record-index-parent-review.v1')
assert review['packet_pins_verified']['writer_source']['sha256']==writer_sha and review['packet_pins_verified']['writer_source']['bytes']==33445
assert review['actual_writer_main_executed'] is False and review['actual_inputs_constructed'] is False and review['scientific_admission'] is False
manifest_raw=original_blob(manifest_path,8044,'94a9195570b997603742ea14eeb2008a55707c9ea72ba12f45ec7fd87d8dfac3')
manifest=sealed(manifest_raw,'68419007c6408735ba039365a8543373820eaf89bce5d3bf3535515d8f3acbf3','swdb.lanl17-parent-full-record-index-controls-archival-custody.v1')
entry=[row for row in manifest['entries'] if row['role']=='prospective_writer_source']
assert len(entry)==1 and entry[0]['snapshot']==P(writer_path).name and entry[0]['bytes']==33445 and entry[0]['sha256']==writer_sha and entry[0]['original_bytes_preserved'] is True
review_entry=[row for row in manifest['entries'] if row['role']=='parent_review_receipt']
assert len(review_entry)==1 and review_entry[0]['sha256']==sha(review_raw) and review_entry[0]['identity_sha256']==review['identity_sha256'] and review_entry[0]['original_canonical_ensure_ascii'] is True
destination=base/'lanl17-index-source-20261007-a1'
assert not destination.exists() and not destination.is_symlink()
source_gate();remaining();destination.mkdir(mode=0o700)
assert path_checked(destination,True)==destination and destination.stat().st_mode&0o777==0o700
target=destination/'writer.py'
fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
target=path_checked(target);before=target.stat()
with target.open('rb') as stream:
 fd_before=os.fstat(stream.fileno());returned=stream.read(33446);fd_after=os.fstat(stream.fileno())
after=path_checked(target).stat()
keys=('st_dev','st_ino','st_uid','st_mode','st_size','st_mtime_ns','st_ctime_ns')
assert all(getattr(before,k)==getattr(fd_before,k)==getattr(fd_after,k)==getattr(after,k) for k in keys)
assert len(returned)==33445 and sha(returned)==writer_sha and returned==raw and after.st_mode&0o777==0o600
source_gate();assert original_blob(writer_path,33445,writer_sha)==raw
assert original_blob(review_path,5432,sha(review_raw))==review_raw and original_blob(manifest_path,8044,sha(manifest_raw))==manifest_raw
remaining()
row={'format':'swdb.lanl17-reviewed-full-record-index-writer-source-staging.v1',
 'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonical_ensure_ascii':True,
 'host':'mbit10','uid':os.getuid(),'user':'yanruj','source_git_revision':revision,'source_git_branch':'yanrujhou_main',
 'source_git_tracked_clean':True,'untracked_files_cleaned_or_changed':False,
 'destination':str(destination),'directory_mode':'0700',
 'writer':{'path':str(target),'origin_git_path':writer_path,'bytes':33445,'sha256':writer_sha,'mode':'0600'},
 'staging_driver_sha256':'__LOCAL_DRIVER_SHA__',
 'parent_review':{'origin_git_path':review_path,'bytes':len(review_raw),'sha256':sha(review_raw),'identity_sha256':review['identity_sha256'],'original_canonical_ensure_ascii':True},
 'archive_manifest':{'origin_git_path':manifest_path,'bytes':len(manifest_raw),'sha256':sha(manifest_raw),'identity_sha256':manifest['identity_sha256'],'original_canonical_ensure_ascii':True},
 'writer_imported_or_main_executed':False,'actual_requests_inventory_catalog_index_constructed_or_read':False,
 'Store_validate_campaign_native_provider_collector_auditor_tests_executed':False,
 'scientific_admission':False,'authentication_or_environment_contents_read':False,
 'earlier_staged_a2r1_a3_controls_opened_or_modified':False,
 'scope':'One fresh owned source-only copy from an exact delivered Git blob and original reviewed archival custody. Original a2r1/a3 stages, every prior file and scientific source remain untouched. Writer execution and actual inputs require separate parent review.'}
row['identity_sha256']=digest(row)
encoded=(json.dumps(row,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
assert len(encoded)<=16384
fd=os.open(destination/'staging.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as stream:stream.write(encoded);stream.flush();os.fsync(stream.fileno())
receipt=path_checked(destination/'staging.json');assert receipt.stat().st_mode&0o777==0o600 and receipt.read_bytes()==encoded
assert path_checked(target).read_bytes()==raw and target.stat().st_mode&0o777==0o600
source_gate();remaining();sys.stdout.buffer.write(encoded)
'''


def main():
    own = Path(__file__)
    assert own.is_absolute() and all(not part.is_symlink() for part in (own, *own.parents))
    own_raw = own.read_bytes()
    own_sha = hashlib.sha256(own_raw).hexdigest()
    assert OUTPUT.parent == Path('/private/tmp') and not OUTPUT.exists() and not OUTPUT.is_symlink()
    parent = OUTPUT.parent.resolve(strict=True)
    assert parent == OUTPUT.parent and not any(part.is_symlink() for part in (parent, *parent.parents))
    review_path = Path('/private/tmp/lanl17-parent-full-record-index-parent-review-20261007.json')
    assert not any(part.is_symlink() for part in (review_path, *review_path.parents))
    review_raw = review_path.read_bytes()
    assert len(review_raw) == 5432 and hashlib.sha256(review_raw).hexdigest() == REVIEW_SHA
    remote = REMOTE.replace('__LOCAL_DRIVER_SHA__', own_sha)
    result = subprocess.run(['ssh', 'mbit10', 'python3 -c ' + shlex.quote(remote)],
                            capture_output=True, timeout=120, check=False)
    if result.returncode != 0:
        raise RuntimeError('Source staging refused; SSH exit=' + str(result.returncode) +
                           ', stderr_sha256=' + hashlib.sha256(result.stderr).hexdigest())
    assert len(result.stdout) <= 16384 and result.stderr == b''
    row = json.loads(result.stdout)
    assert row['identity_sha256'] == hashlib.sha256(json.dumps(
        {key: value for key, value in row.items() if key != 'identity_sha256'},
        sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    assert row['canonical_ensure_ascii'] is True and row['source_git_revision'] == REVISION
    assert row['writer']['bytes'] == WRITER_BYTES and row['writer']['sha256'] == WRITER_SHA
    assert row['parent_review']['identity_sha256'] == REVIEW_ID and row['parent_review']['sha256'] == REVIEW_SHA
    assert row['archive_manifest']['identity_sha256'] == MANIFEST_ID and row['archive_manifest']['sha256'] == MANIFEST_SHA
    assert row['writer_imported_or_main_executed'] is False and row['scientific_admission'] is False
    assert own.read_bytes() == own_raw and review_path.read_bytes() == review_raw
    fd = os.open(OUTPUT, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(result.stdout)
        stream.flush()
        os.fsync(stream.fileno())
    assert stat.S_ISREG(OUTPUT.stat().st_mode) and OUTPUT.stat().st_uid == os.getuid() and OUTPUT.stat().st_mode & 0o777 == 0o600
    assert OUTPUT.read_bytes() == result.stdout and own.read_bytes() == own_raw
    print(json.dumps({'path': str(OUTPUT), 'bytes': len(result.stdout),
                      'sha256': hashlib.sha256(result.stdout).hexdigest(),
                      'identity_sha256': row['identity_sha256'], 'writer_imported_or_main_executed': False}))


if __name__ == '__main__':
    main()
