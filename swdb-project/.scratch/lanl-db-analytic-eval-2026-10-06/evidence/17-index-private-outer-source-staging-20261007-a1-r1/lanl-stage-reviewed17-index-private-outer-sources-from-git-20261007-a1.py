"""NOT RUN: reviewed source-copy staging, requiring a parent supplied deliveredRevision.

Future invocation copies two exact Git Python/Bash source blobs only. It does not import or
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
OUTPUT = Path('/private/tmp/lanl17-reviewed-index-private-outer-source-staging-actual-20261007-a1.json')
CONFIG = {'sources': [{'target': 'outer_capture.py',
              'source': {'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-original-index-writer-private-outer-capture-controls-20261007/lanl17_remote_original_index_writer_private_outer_capture_20261007.py',
                         'bytes': 34658,
                         'sha256': '59c06dd5ea606414827a85d6e27f4aff1bc381827624590b2449415198399544'}},
             {'target': 'bootstrap.sh',
              'source': {'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-original-index-writer-private-outer-capture-controls-20261007/lanl17_original_index_writer_outermost_private_bootstrap_20261007.sh',
                         'bytes': 6549,
                         'sha256': '0d1eb650d1bcb1a9f491d5fb790f083e371875ddd20fe0bf1f42d5fce05a9217'}}],
 'review': {'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-original-index-writer-private-outer-capture-controls-20261007/lanl17-original-index-writer-private-outer-capture-parent-review-20261007.json',
            'bytes': 6493,
            'sha256': 'a9ab95d10d8e26a0a4b170f7184c31970d88c3b8f04f9dea6d02d38c3079e262',
            'format': 'swdb.lanl17-original-index-writer-private-outer-capture-parent-source-review.v1',
            'identity_sha256': 'b471b2d9e12fd4d54c3e74b25ed56782c6e319a4df59e271b5ddacde7befa687'},
 'preparation': {'path': 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-original-index-writer-private-outer-capture-controls-20261007/lanl17-original-index-writer-private-outer-capture-source-preparation-20261007.json',
                 'bytes': 7504,
                 'sha256': '568c866abc6cff7197d7b487ad59ff6361eb37f259ee8c66bdbbe8ba1f3dd7f5',
                 'format': 'swdb.lanl17-original-index-writer-private-outer-capture-source-preparation.v1',
                 'identity_sha256': 'e94cc1d15c7e9f9b4b3fb766063a4329bbe56cadd1f4f14715f9923a6d9866e7'}}

REMOTE = r'''
import datetime,hashlib,json,os,pathlib,pwd,signal,socket,stat,subprocess,sys,time
P=pathlib.Path
CONFIG=json.loads('__CONFIG_JSON__')
REVISION='__DELIVERED_REVISION__'
DRIVER_SHA='__LOCAL_DRIVER_SHA__'
SOURCE_C='f893fed400347ed23d92e917d8bde21b75e5375d'
F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
RECEIPT_FORMAT='swdb.lanl17-reviewed-index-private-outer-source-staging.v1'
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
  assert not s.st_mode&0o022 or (p == P('/data1/yanruj/ArchEvolve') and p.parent.stat().st_uid==os.getuid() and stat.S_IMODE(p.parent.stat().st_mode)==0o700)
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
 def custody(originals,review_raw,preparation_raw):
  review=sealed(review_raw,CONFIG['review']);preparation=sealed(preparation_raw,CONFIG['preparation'])
  assert review['complete_parent_packet_read'] is True and review['complete_independent_ticket04_packet_read'] is True
  assert review['concrete_source_blockers_found']==[] and review['actual_invocation_reviewed'] is False
  assert review['source_preservation_and_prospective_staging_reviewed'] is True
  assert review['original_ordered_fourteen_flags_unchanged'] is True
  assert review['no_new_execution_or_scientific_evidence'] is True
  assert all(value==0 for value in review['not_performed'].values())
  assert all(value==0 for value in preparation['not_performed'].values())
  assert len(review['independently_verified_function_class_AST_names'])==27
  assert len(review['independently_verified_constant_Assign_AST_names'])==24
  assert preparation['static_source_checks']['copied_reviewed1ee_function_class_AST_count']==27
  assert preparation['static_source_checks']['copied_function_class_AST_exact'] is True
  assert preparation['static_source_checks']['copied_reviewed1ee_constant_Assign_count']==24
  assert preparation['static_source_checks']['copied_constant_Assign_AST_exact'] is True
  assert len(review['future_actual_parent_prerequisites'])==8
  assert review['future_actual_parent_prerequisites']==preparation['future_mandatory_real_parent_review']
  assert review['verified_original_True_seals']['preparation']==CONFIG['preparation']['identity_sha256']
  exact_pin(review['prepared_packet_pins']['preparation'],CONFIG['preparation'])
  scope=preparation['unchanged_scientific_bounds']
  assert scope['C']==SOURCE_C and scope['F6']==F6 and scope['module_count']==185
  assert scope['original_writer_six_flags_and_values_changed'] is False
  assert scope['catalog_source_file_bytes']==134217728 and scope['unique_one_catalog_bytes']==2147483648
  assert scope['records']==16384 and scope['metadata_bytes']==8388608
  roles={'outer_capture.py':('outer_source','outer_source'),
         'bootstrap.sh':('bootstrap_source','outermost_Bash_bootstrap_source')}
  for config in CONFIG['sources']:
   review_role,preparation_role=roles[config['target']]
   exact_pin(review['prepared_packet_pins'][review_role],config['source'])
   exact_pin(preparation['prepared_file_pins'][preparation_role],config['source'])
   source=originals[config['target']]['source']
   assert len(source)==config['source']['bytes'] and sha(source)==config['source']['sha256']
  return review,preparation
 source_gate();assert python_tree(SOURCE_C)==python_tree(REVISION)
 assert set(CONFIG)=={'sources','review','preparation'}
 assert {v['target'] for v in CONFIG['sources']}=={'outer_capture.py','bootstrap.sh'} and len(CONFIG['sources'])==2
 review_raw=original_blob(CONFIG['review']);preparation_raw=original_blob(CONFIG['preparation'])
 originals={}
 for config in CONFIG['sources']:
  originals[config['target']]={'source':original_blob(config['source']),'review':review_raw,'preparation':preparation_raw}
 custody(originals,review_raw,preparation_raw)
 destination=base/'lanl17-index-private-outer-source-20261007-a1'
 assert not destination.exists() and not destination.is_symlink()
 source_gate();remaining();destination.mkdir(mode=0o700)
 assert checked(destination,True)==destination and destination.stat().st_mode&0o777==0o700
 directory_fd=os.open(destination,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 try:
  for config in CONFIG['sources']:
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
 for config in CONFIG['sources']:stats[config['target']]=target_checked(config)
 # Recheck both original sources and the one shared exact review/preparation group.
 source_gate();assert python_tree(SOURCE_C)==python_tree(REVISION)
 assert original_blob(CONFIG['review'])==review_raw and original_blob(CONFIG['preparation'])==preparation_raw
 for config in CONFIG['sources']:
  assert original_blob(config['source'])==originals[config['target']]['source']
  target_checked(config,stats[config['target']])
 assert checked(destination,True).stat().st_mode&0o777==0o700
 assert set(os.listdir(destination))=={v['target'] for v in CONFIG['sources']}
 row={'format':RECEIPT_FORMAT,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'canonical_ensure_ascii':True,'host':'mbit10','uid':os.getuid(),'user':'yanruj',
      'source_git_revision':REVISION,'source_git_branch':'yanrujhou_main','source_git_tracked_clean':True,
      'scientific_source_C':SOURCE_C,'scientific_python_modules_Git_blob_equal_C':185,
      'estimator_F6_from_exact_original_reviewed_custody':F6,'live_estimator_imported_or_computed':False,
      'destination':str(destination),'directory_mode':'0700','staging_driver_sha256':DRIVER_SHA,
      'sources':[{'target':str(destination/v['target']),'mode':'0600','source_git_pin':v['source']} for v in CONFIG['sources']],
      'original_group_review_git_pin':dict(CONFIG['review'],canonical_ensure_ascii=True),
      'original_group_preparation_git_pin':dict(CONFIG['preparation'],canonical_ensure_ascii=True),
      'receipt_written_on_remote':False,'remote_destination_contains_only_two_source_files':True,
      'source_imports_or_selected_mains_executed':False,'actual_inputs_or_catalog_read_or_constructed':False,
      'Store_validate_campaign_native_provider_collector_auditor_tests_executed':False,
      'scientific_admission':False,'environment_or_authentication_contents_read':False,
      'earlier_stages_including_original7a_opened_or_modified':False,
      'untracked_files_cleaned_or_modified':False,'remote_seconds_limit':60,'SSH_seconds_limit':120,
      'scope':'Two exact private-outer Python/Bash source byte copies only; one original preparation/parent-review group retained. No copied source/envelope/original7a main or actual inputs. Real input/native/runtime/full56argv and outer supervision review remain required before execution.'}
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
    assert row['format'] == 'swdb.lanl17-reviewed-index-private-outer-source-staging.v1'
    assert row['canonical_ensure_ascii'] is True
    assert row['identity_sha256'] == digest({k: v for k, v in row.items() if k != 'identity_sha256'})
    assert row['source_git_revision'] == revision and row['source_git_branch'] == 'yanrujhou_main'
    assert row['source_git_tracked_clean'] is True and row['staging_driver_sha256'] == own_sha
    assert row['host'] == 'mbit10' and row['uid'] == 114316761 and row['user'] == 'yanruj'
    assert row['scientific_source_C'] == SOURCE_C
    assert row['scientific_python_modules_Git_blob_equal_C'] == 185
    assert row['estimator_F6_from_exact_original_reviewed_custody'] == ESTIMATOR_F6
    assert row['destination'] == '/data1/yanruj/lanl17-index-private-outer-source-20261007-a1'
    assert row['directory_mode'] == '0700' and row['remote_destination_contains_only_two_source_files'] is True
    assert row['receipt_written_on_remote'] is False and len(row['sources']) == 2
    assert row['original_group_review_git_pin'] == dict(CONFIG['review'], canonical_ensure_ascii=True)
    assert row['original_group_preparation_git_pin'] == dict(CONFIG['preparation'], canonical_ensure_ascii=True)
    for config, saved in zip(CONFIG['sources'], row['sources']):
        assert saved['target'] == row['destination'] + '/' + config['target'] and saved['mode'] == '0600'
        assert saved['source_git_pin'] == config['source']
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
