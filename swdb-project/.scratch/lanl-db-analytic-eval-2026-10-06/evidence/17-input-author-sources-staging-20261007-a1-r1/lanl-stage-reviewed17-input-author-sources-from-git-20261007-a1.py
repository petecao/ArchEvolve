"""NOT RUN: reviewed source-copy staging, requiring a parent supplied deliveredRevision.

Future invocation copies three exact Git source blobs only. It does not import or
execute those sources, read a research catalog, construct inputs, or run tests.
All earlier source stages stay unopened. Parent review and SSH ownership remain
required. Failures retain partial output and expose only exception class/hash.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys

SOURCE_C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
ESTIMATOR_F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
OUTPUT = Path('/private/tmp/lanl17-reviewed-input-author-sources-staging-actual-20261007-a1.json')
CONFIG = [{'target': 'publication_author.py',
  'source': {'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-first-publication-request-author-controls-20261007-r1/lanl17_author_first_publication_request_r1_20261007.py',
             'bytes': 28419,
             'sha256': '791f95b5f53c23740ce8b2bdd72fc8dcd625494a60f5399f30b5ed704347fb1a'},
  'review': {'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-first-publication-request-author-controls-20261007-r1/lanl17-first-publication-request-author-parent-review-20261007.json',
             'bytes': 5706,
             'sha256': 'a6f4574017f8b3879448319630691fb61b7a7476c09bf4d216c4bd9c187d9a4b',
             'format': 'swdb.lanl17-first-publication-request-author-parent-source-review.v1',
             'identity_sha256': '55d73e22fe4eb42a68a8582bc2bfb7e5630ef0168c89c57ff81c428377f64e28'},
  'manifest': {'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-first-publication-request-author-controls-20261007-r1/manifest.json',
               'bytes': 6332,
               'sha256': '1f6548fae8020b98ed64d0ba05c630e381ab1f432cbfc8137d857ade3d2d5915',
               'format': 'swdb.lanl17-first-publication-request-author-controls-archival-custody.v1',
               'identity_sha256': 'fde1fa2af039149728ffb593395c3792096fc7ad56d095e90ec8409a714c4b65'}},
 {'target': 'index_request_author.py',
  'source': {'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-parent-index-request-author-controls-20261007-r1/lanl17_author_parent_full_record_index_request_r1_20261007.py',
             'bytes': 38266,
             'sha256': 'a2e69aef10deb6186ac49401516ffba9a165b2f3cc94c8001646b6ac9a5b701d'},
  'review': {'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-parent-index-request-author-controls-20261007-r1/lanl17-index-request-author-r1-parent-review-20261007.json',
             'bytes': 4493,
             'sha256': 'dfeb44d5380b39ccb429f2069482ef9b11ff1f48614d590439781d2133cfc22e',
             'format': 'swdb.lanl17-index-request-author-r1-parent-source-review.v1',
             'identity_sha256': '8ee0b630581889aacca633bd0f067cad03410095fac88978c9c4a5e81fca2cf3'},
  'manifest': {'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-parent-index-request-author-controls-20261007-r1/manifest.json',
               'bytes': 10452,
               'sha256': '0e2bb2ddbb94be542bf172ba03230649f25bb6c405ceaf0be02273541e8cc52d',
               'format': 'swdb.lanl17-parent-index-request-author-controls-retention.v1',
               'identity_sha256': '8043407506aa0d65107f37e2a9d95a3c9abcc077a0738c3efeccc076f8140f84'}},
 {'target': 'passive_inventory.py',
  'source': {'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-passive-one-catalog-inventory-controls-20261007/lanl17_read_passive_one_catalog_inventory_20261007.py',
             'bytes': 29653,
             'sha256': '76b86959ceca7a162a34b7a2d1e633ee9523d0b9cc7f629e9fbeeb4e101aa176'},
  'review': {'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-passive-one-catalog-inventory-controls-20261007/lanl17-passive-inventory-parent-review-20261007.json',
             'bytes': 5062,
             'sha256': '44bc9076f5cc1451112c5b01dccd467fcdfde0d2dfe01525c04e56f25d97058f',
             'format': 'swdb.lanl17-passive-inventory-parent-source-review.v1',
             'identity_sha256': '2845ba8c4d085c6d03b41bb5332fd144eb930b25f6bfd08801c16301de80dc21'},
  'manifest': {'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-passive-one-catalog-inventory-controls-20261007/manifest.json',
               'bytes': 8931,
               'sha256': '58602bce973ef6b7c9162128e4d288a5f36b257454bfae84ab683f4d30745e47',
               'format': 'swdb.lanl17-passive-one-catalog-inventory-archive.v1',
               'identity_sha256': '3494b0fa965fc6bfc1f0425f5b3630f76f1723d72e7a979a4e90ac83824f143e'}}]

REMOTE = r'''
import datetime,hashlib,json,os,pathlib,pwd,signal,socket,stat,subprocess,sys,time
P=pathlib.Path
CONFIG=json.loads('__CONFIG_JSON__')
REVISION='__DELIVERED_REVISION__'
DRIVER_SHA='__LOCAL_DRIVER_SHA__'
SOURCE_C='f893fed400347ed23d92e917d8bde21b75e5375d'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
RECEIPT_FORMAT='swdb.lanl17-reviewed-input-author-sources-staging.v1'
KEYS=('st_dev','st_ino','st_uid','st_mode','st_size','st_mtime_ns','st_ctime_ns')

def sha(raw):return hashlib.sha256(raw).hexdigest()
def digest(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
def strict_json(raw):
 def pairs(rows):
  result={}
  for key,value in rows:
   assert key not in result
   result[key]=value
  return result
 def nonfinite(value):raise ValueError('Nonfinite JSON refused')
 return json.loads(raw,object_pairs_hook=pairs,parse_constant=nonfinite)
def alarm(signum,frame):raise TimeoutError('Source-copy remote deadline')

def perform():
 assert sys.platform=='linux' and socket.gethostname()=='mbit10'
 assert os.getuid()==os.geteuid()==114316761 and pwd.getpwuid(os.getuid()).pw_name=='yanruj'
 signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,60)
 deadline=time.monotonic()+60
 def remaining():
  left=deadline-time.monotonic();assert left>0
  return left
 def checked(path,directory=False):
  p=P(path)
  assert p.is_absolute() and '..' not in p.parts
  assert not any(v.is_symlink() for v in (p,*p.parents))
  assert p.resolve(strict=True)==p
  s=p.stat();assert s.st_uid==os.getuid()
  assert stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode)
  assert not s.st_mode&0o022
  return p
 base=checked('/data1/yanruj',True);repo=checked(base/'ArchEvolve',True)
 def git(*args):
  env={'PATH':'/usr/bin:/bin','LANG':'C','GIT_NO_LAZY_FETCH':'1','GIT_TERMINAL_PROMPT':'0',
       'GIT_OPTIONAL_LOCKS':'0','GIT_PAGER':'cat','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':'/dev/null'}
  result=subprocess.run(['/usr/bin/git','-c','protocol.allow=never','-c','core.fsmonitor=false',
                         '-C',str(repo),*args],capture_output=True,timeout=min(15,remaining()),env=env,check=False)
  if result.returncode!=0:raise RuntimeError('Read-only Git refused')
  assert result.stderr==b''
  return result.stdout
 def source_gate():
  assert git('rev-parse','--show-toplevel').decode().strip()==str(repo)
  assert git('rev-parse','HEAD').decode().strip()==REVISION
  assert git('branch','--show-current').decode().strip()=='yanrujhou_main'
  assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
 def python_tree(revision):
  rows=[r for r in git('ls-tree','-r','-z',revision,'--','swdb-project/swdb').split(b'\0') if r]
  selected={}
  for row in rows:
   meta,name=row.split(b'\t',1)
   if name.endswith(b'.py'):
    assert meta.split()[:2]==[b'100644',b'blob'] and name not in selected
    selected[name]=meta
  assert len(selected)==185
  return selected
 def original_blob(pin):
  path=pin['path'];rows=[r for r in git('ls-tree','-z',REVISION,'--',path).split(b'\0') if r]
  assert len(rows)==1
  meta,name=rows[0].split(b'\t',1)
  assert name.decode()==path and meta.split()[:2]==[b'100644',b'blob']
  raw=git('cat-file','blob',REVISION+':'+path)
  assert len(raw)==pin['bytes'] and sha(raw)==pin['sha256']
  return raw
 def sealed(raw,pin):
  doc=strict_json(raw)
  assert doc['format']==pin['format'] and doc['canonical_ensure_ascii'] is True
  assert doc['identity_sha256']==pin['identity_sha256']==digest({k:v for k,v in doc.items() if k!='identity_sha256'})
  return doc
 def exact_pin(row,pin):
  assert row['sha256']==pin['sha256'] and row['bytes']==pin['bytes']
 def entry(manifest,role,pin,name_key='snapshot',seal_key=None):
  rows=[r for r in manifest['entries'] if r['role']==role]
  assert len(rows)==1
  row=rows[0];assert row[name_key]==P(pin['path']).name
  exact_pin(row,pin)
  if seal_key:
   assert row[seal_key]==pin['identity_sha256'] and row['original_canonical_ensure_ascii'] is True
  return row
 def custody(config,source,review_raw,manifest_raw):
  review=sealed(review_raw,config['review']);manifest=sealed(manifest_raw,config['manifest'])
  assert manifest['source_C']==SOURCE_C and manifest['estimator_sha256']==F6
  assert review['scientific_admission'] is False
  target=config['target'];pin=config['source']
  if target=='publication_author.py':
   assert review['selected_author_sha256']==pin['sha256']
   assert review['parent_full_original_source_and_complete_R1_patch_review'] is True
   assert review['independent_agent02_full_source_and_R1_recheck'] is True and review['remaining_concrete_source_blockers']==0
   assert review['actual_author_main_executed'] is False
   assert review['actual_specification_request_capture_or_observations_constructed'] is False
   assert review['actual_metadata_campaign_or_scientific_execution'] is False
   assert review['source_C']==SOURCE_C and review['estimator_sha256']==F6
   rows=[v for v in review['source_pins_verified'] if v['sha256']==pin['sha256']]
   assert len(rows)==1;exact_pin(rows[0],pin)
   row=entry(manifest,'selected_R1_source_only_author',pin);assert row['original_bytes_preserved'] is True
   row=entry(manifest,'parent_complete_source_review_proof',config['review'],seal_key='identity_sha256')
   assert row['original_bytes_preserved'] is True and manifest['Python_modules_exact_C']==185
  elif target=='index_request_author.py':
   assert review['selected_author_sha256']==pin['sha256']
   assert review['full_parent_and_independent_source_reviews_completed'] is True and review['exact_original_byte_reversal_verified'] is True
   assert review['actual_synthetic_test_bodies_passed']==5 and review['batch_invocations']==1
   assert review['actual_author_main_executed'] is False and review['actual_inputs_constructed'] is False
   assert review['remote_staging_or_campaign_executed'] is False
   assert review['future_use_requires_separate_explicit_real_input_parent_review'] is True
   assert review['original7a_actual_execution_requires_private_remote_stderr_envelope'] is True
   exact_pin(review['pins']['r1_author'],pin)
   entry(manifest,'r1_author',pin,'path')
   entry(manifest,'parent_complete_review_receipt',config['review'],'path','original_identity_sha256')
   assert manifest['unchanged7a_requires_reviewed_outer_private_remote_stderr_envelope'] is True
  elif target=='passive_inventory.py':
   assert review['selected_reader_sha256']==pin['sha256']
   assert review['full_parent_and_independent_source_and_harness_reviews_completed'] is True
   assert review['actual_synthetic_test_bodies_passed']==4 and review['batch_invocations']==1
   assert review['actual_reader_main_executed'] is False and review['actual_inventory_or_summary_constructed'] is False
   assert review['remote_staging_or_campaign_executed'] is False
   assert review['future_use_requires_separate_real_input_parent_review'] is True
   exact_pin(review['pins']['reviewed_reader_source_pin'],pin)
   for role,p in (('reviewed_reader_source_pin',pin),('parent_review_json',config['review'])):
    row=manifest['snapshots'][P(p['path']).name]
    assert row['role']==role and row['size_bytes']==p['bytes'] and row['sha256']==p['sha256']
   rows=[v for v in manifest['sealed_snapshot_objects'] if v['path']==P(config['review']['path']).name]
   assert len(rows)==1 and rows[0]['identity_sha256']==config['review']['identity_sha256'] and rows[0]['canonical_ensure_ascii'] is True
   assert manifest['python_modules']==185
  else:raise ValueError('Unexpected staging target')
  assert len(source)==pin['bytes'] and sha(source)==pin['sha256']
  return review,manifest
 source_gate();assert python_tree(SOURCE_C)==python_tree(REVISION)
 assert {v['target'] for v in CONFIG}=={'publication_author.py','index_request_author.py','passive_inventory.py'} and len(CONFIG)==3
 originals={}
 for config in CONFIG:
  raws={role:original_blob(config[role]) for role in ('source','review','manifest')}
  custody(config,raws['source'],raws['review'],raws['manifest'])
  originals[config['target']]=raws
 destination=base/'lanl17-input-author-source-20261007-a1'
 assert not destination.exists() and not destination.is_symlink()
 source_gate();remaining();destination.mkdir(mode=0o700)
 assert checked(destination,True)==destination and destination.stat().st_mode&0o777==0o700
 directory_fd=os.open(destination,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:
  for config in CONFIG:
   remaining();raw=originals[config['target']]['source'];target=destination/config['target']
   fd=os.open(target,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
   with os.fdopen(fd,'wb') as stream:
    stream.write(raw);stream.flush();os.fsync(stream.fileno())
  os.fsync(directory_fd)
 finally:os.close(directory_fd)
 stats={}
 def target_checked(config,expected_stat=None):
  remaining();target=checked(destination/config['target']);before=target.stat()
  assert before.st_mode&0o777==0o600 and before.st_nlink==1
  fd=os.open(target,os.O_RDONLY|os.O_NOFOLLOW)
  with os.fdopen(fd,'rb') as stream:
   fd_before=os.fstat(stream.fileno());returned=stream.read(config['source']['bytes']+1);fd_after=os.fstat(stream.fileno())
  after=checked(target).stat()
  assert all(getattr(before,k)==getattr(fd_before,k)==getattr(fd_after,k)==getattr(after,k) for k in KEYS)
  current=tuple(getattr(after,k) for k in KEYS)
  if expected_stat is not None:assert current==expected_stat
  assert returned==originals[config['target']]['source'] and sha(returned)==config['source']['sha256']
  return current
 for config in CONFIG:stats[config['target']]=target_checked(config)
 # Recheck every original source/review/manifest, not only the copied sources.
 source_gate();assert python_tree(SOURCE_C)==python_tree(REVISION)
 for config in CONFIG:
  for role in ('source','review','manifest'):
   assert original_blob(config[role])==originals[config['target']][role]
  target_checked(config,stats[config['target']])
 assert checked(destination,True).stat().st_mode&0o777==0o700
 assert set(os.listdir(destination))=={v['target'] for v in CONFIG}
 row={'format':RECEIPT_FORMAT,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'canonical_ensure_ascii':True,'host':'mbit10','uid':os.getuid(),'user':'yanruj',
      'source_git_revision':REVISION,'source_git_branch':'yanrujhou_main','source_git_tracked_clean':True,
      'scientific_source_C':SOURCE_C,'scientific_python_modules_Git_blob_equal_C':185,
      'estimator_F6_from_exact_original_reviewed_custody':F6,'live_estimator_imported_or_computed':False,
      'destination':str(destination),'directory_mode':'0700','staging_driver_sha256':DRIVER_SHA,
      'sources':[{'target':str(destination/v['target']),'mode':'0600','source_git_pin':v['source'],
                  'original_review_git_pin':dict(v['review'],canonical_ensure_ascii=True),
                  'original_manifest_git_pin':dict(v['manifest'],canonical_ensure_ascii=True)} for v in CONFIG],
      'receipt_written_on_remote':False,'remote_destination_contains_only_three_source_files':True,
      'source_imports_or_selected_mains_executed':False,'actual_inputs_or_catalog_read_or_constructed':False,
      'Store_validate_campaign_native_provider_collector_auditor_tests_executed':False,
      'scientific_admission':False,'environment_or_authentication_contents_read':False,
      'earlier_stages_including_original7a_opened_or_modified':False,
      'untracked_files_cleaned_or_modified':False,'remote_seconds_limit':60,'SSH_seconds_limit':120,
      'scope':'Fresh source copies only; exact original reviews and NOTRUN/later synthetic chronology retained. Actual input review and executions require separate parent approval; original7a execution still requires its reviewed private remote stderr envelope.'}
 row['identity_sha256']=digest(row)
 encoded=(json.dumps(row,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode();assert len(encoded)<=16384
 source_gate();remaining();sys.stdout.buffer.write(encoded);sys.stdout.buffer.flush()

try:perform()
except BaseException as error:
 diagnostic={'error_class':type(error).__name__,'diagnostic_sha256':sha(str(error).encode('utf-8','replace'))}
 sys.stderr.write(json.dumps(diagnostic,sort_keys=True)+'\n');sys.exit(1)
'''

KEYS = ('st_dev', 'st_ino', 'st_uid', 'st_mode', 'st_size', 'st_mtime_ns', 'st_ctime_ns')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=True, allow_nan=False).encode())


def strict_json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            assert key not in result
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError('Nonfinite JSON refused')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def checked_file(path, maximum):
    assert path.is_absolute() and '..' not in path.parts
    assert not any(p.is_symlink() for p in (path, *path.parents))
    assert path.resolve(strict=True) == path
    before = path.stat()
    assert stat.S_ISREG(before.st_mode) and before.st_uid == os.getuid()
    assert not before.st_mode & 0o022 and before.st_size <= maximum
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        fd_before = os.fstat(stream.fileno())
        raw = stream.read(maximum + 1)
        fd_after = os.fstat(stream.fileno())
    after = path.stat()
    assert all(getattr(before, key) == getattr(fd_before, key) ==
               getattr(fd_after, key) == getattr(after, key) for key in KEYS)
    assert len(raw) == after.st_size <= maximum
    return raw, tuple(getattr(after, key) for key in KEYS)


def main():
    if len(sys.argv) != 2 or re.fullmatch(r'[0-9a-f]{40}', sys.argv[1]) is None:
        raise ValueError('One exact deliveredRevision is required')
    revision = sys.argv[1]
    own = Path(__file__)
    own_raw, own_stat = checked_file(own, 131072)
    own_sha = sha(own_raw)
    assert OUTPUT.parent == Path('/private/tmp')
    assert not any(p.is_symlink() for p in (OUTPUT, *OUTPUT.parents))
    assert OUTPUT.parent.resolve(strict=True) == OUTPUT.parent
    assert not OUTPUT.exists() and not OUTPUT.is_symlink()
    assert stat.S_ISDIR(OUTPUT.parent.stat().st_mode)
    values = {'__CONFIG_JSON__': json.dumps(CONFIG, separators=(',', ':'), ensure_ascii=True),
              '__DELIVERED_REVISION__': revision, '__LOCAL_DRIVER_SHA__': own_sha}
    remote = REMOTE
    for token, value in values.items():
        assert remote.count(token) == 1
        remote = remote.replace(token, value)
    assert checked_file(own, 131072) == (own_raw, own_stat)
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=20',
                             'mbit10', 'python3 -c ' + shlex.quote(remote)],
                            capture_output=True, timeout=120, check=False)
    if result.returncode != 0:
        # Raw SSH/Git stdout/stderr never becomes a diagnostic or durable output.
        raise RuntimeError('SSH source copy refused; stdout_sha256=' + sha(result.stdout) +
                           ';stderr_sha256=' + sha(result.stderr))
    assert len(result.stdout) <= 16384 and result.stderr == b''
    row = strict_json(result.stdout)
    assert row['format'] == 'swdb.lanl17-reviewed-input-author-sources-staging.v1'
    assert row['canonical_ensure_ascii'] is True
    assert row['identity_sha256'] == digest({k: v for k, v in row.items() if k != 'identity_sha256'})
    assert row['source_git_revision'] == revision and row['source_git_branch'] == 'yanrujhou_main'
    assert row['source_git_tracked_clean'] is True and row['staging_driver_sha256'] == own_sha
    assert row['host'] == 'mbit10' and row['uid'] == 114316761 and row['user'] == 'yanruj'
    assert row['scientific_source_C'] == SOURCE_C
    assert row['scientific_python_modules_Git_blob_equal_C'] == 185
    assert row['estimator_F6_from_exact_original_reviewed_custody'] == ESTIMATOR_F6
    assert row['destination'] == '/data1/yanruj/lanl17-input-author-source-20261007-a1'
    assert row['directory_mode'] == '0700' and row['remote_destination_contains_only_three_source_files'] is True
    assert row['receipt_written_on_remote'] is False and len(row['sources']) == 3
    for config, saved in zip(CONFIG, row['sources']):
        assert saved['target'] == row['destination'] + '/' + config['target'] and saved['mode'] == '0600'
        assert saved['source_git_pin'] == config['source']
        assert saved['original_review_git_pin'] == dict(config['review'], canonical_ensure_ascii=True)
        assert saved['original_manifest_git_pin'] == dict(config['manifest'], canonical_ensure_ascii=True)
    for key in ('live_estimator_imported_or_computed', 'source_imports_or_selected_mains_executed',
                'actual_inputs_or_catalog_read_or_constructed',
                'Store_validate_campaign_native_provider_collector_auditor_tests_executed',
                'scientific_admission', 'environment_or_authentication_contents_read',
                'earlier_stages_including_original7a_opened_or_modified', 'untracked_files_cleaned_or_modified'):
        assert row[key] is False
    assert row['remote_seconds_limit'] == 60 and row['SSH_seconds_limit'] == 120
    assert checked_file(own, 131072) == (own_raw, own_stat)
    fd = os.open(OUTPUT, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(result.stdout)
        stream.flush()
        os.fsync(stream.fileno())
    directory_fd = os.open(OUTPUT.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    saved, saved_stat = checked_file(OUTPUT, 16384)
    assert saved == result.stdout and OUTPUT.stat().st_mode & 0o777 == 0o600 and OUTPUT.stat().st_nlink == 1
    assert checked_file(own, 131072) == (own_raw, own_stat)
    print(json.dumps({'path': str(OUTPUT), 'bytes': len(saved), 'sha256': sha(saved),
                      'identity_sha256': row['identity_sha256'],
                      'source_imports_or_selected_mains_executed': False}, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        print(json.dumps({'error_class': type(error).__name__,
                          'diagnostic_sha256': sha(str(error).encode('utf-8', 'replace'))}, sort_keys=True),
              file=sys.stderr)
        sys.exit(1)
