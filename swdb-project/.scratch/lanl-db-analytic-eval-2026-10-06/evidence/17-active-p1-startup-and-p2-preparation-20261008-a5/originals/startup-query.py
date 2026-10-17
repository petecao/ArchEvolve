"""Source-only bounded metadata query; no scientific imports or campaign-body reads.

This file is a prospective -c payload. Creating it does not execute it remotely.
"""
import datetime,json,os,re,stat
from pathlib import Path

OWNER=114316761
RAW=Path('/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5')
CID='extensa-gem5-bfs-20261006-p1'
FOLDER=RAW/'campaign-runs/extensa'/CID
HELPER=b'/data1/yanruj/lanl17-control-cleanup60-20261007-a4.py'
ATTEMPT=(str(RAW/'attempts'/CID/'attempt-1')).encode()
INLANE_HELPER=(str(RAW/'attempts'/CID/'attempt-1/helper.py')).encode()
MAX_PROC=32768
MAX_OWNED=4096
MAX_ROWS=128
MAX_FDS=128
warnings=[]

def read_proc(path,limit):
 with path.open('rb') as stream:
  b=stream.read(limit+1)
 if len(b)>limit:raise ValueError('proc_field_bound')
 return b

def file_stat(path):
 try:
  if any(p.is_symlink() for p in (path,*path.parents)):return {'state':'symlink_refused'}
  s=path.lstat()
  if s.st_uid!=OWNER:return {'state':'owner_refused'}
  if not (stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode)):return {'state':'type_refused'}
  return {'state':'present','kind':'file' if stat.S_ISREG(s.st_mode) else 'directory',
          'bytes':s.st_size if stat.S_ISREG(s.st_mode) else None,'mtime_ns':s.st_mtime_ns,
          'inode':s.st_ino,'device':s.st_dev}
 except FileNotFoundError:return {'state':'absent'}
 except OSError:return {'state':'unavailable'}

def process_class(comm,argv):
 tokens=argv.split(b'\0')
 if INLANE_HELPER in tokens and ATTEMPT in tokens:return 'helper28_p1'
 if HELPER in tokens and (CID.encode() in tokens or ATTEMPT in tokens):return 'helper28_p1'
 for command in (b'campaign',b'freeze-protocol',b'dx100-compile',b'dx100-execute',
                 b'aggregate-evaluations',b'compare-evaluations'):
  if b'swdb' in tokens and command in tokens:return 'public_'+command.decode()
 names={'python3.12':'python','python3':'python','python':'python','codex':'codex',
        'node':'node','g++':'compiler_driver','c++':'compiler_driver','gcc':'compiler_driver',
        'cc1plus':'compiler_frontend','cc1':'compiler_frontend','collect2':'compiler_link',
        'ld':'compiler_link','gem5.opt':'gem5','timeout':'gnu_timeout','bash':'bash'}
 return names.get(comm,'other_owned_descendant')

def numeric_io(path):
 try:
  result={}
  for line in read_proc(path,4096).decode('ascii').splitlines():
   k,sep,v=line.partition(':')
   if sep and k in ('rchar','wchar','syscr','syscw','read_bytes','write_bytes'):
    result[k]=int(v.strip())
  return result
 except (OSError,ValueError,UnicodeError):return None

proc={};helpers=[];seen=0
for p in Path('/proc').iterdir():
 seen+=1
 if seen>MAX_PROC:raise ValueError('proc_inventory_bound')
 if not p.name.isdecimal():continue
 try:
  if p.stat().st_uid!=OWNER:continue
  if len(proc)>=MAX_OWNED:raise ValueError('owned_process_bound')
  s=read_proc(p/'stat',8192);tail=s.rsplit(b')',1)[1].split()
  argv=read_proc(p/'cmdline',32768)
  comm=read_proc(p/'comm',256).decode('utf-8','replace').strip()
  pid=int(p.name);row={'pid':pid,'parent_pid':int(tail[1]),'state':tail[0].decode('ascii'),
   'process_group':int(tail[2]),'session':int(tail[3]),'start_ticks':int(tail[19]),
   'user_cpu_ticks':int(tail[11]),'kernel_cpu_ticks':int(tail[12]),
   'rss_bytes':int(tail[21])*os.sysconf('SC_PAGE_SIZE'),'process_class':process_class(comm,argv)}
  proc[pid]=row
  if row['process_class']=='helper28_p1':helpers.append(pid)
 except (OSError,IndexError,UnicodeError):continue

selected=set(helpers)
for _ in range(MAX_ROWS):
 new={pid for pid,row in proc.items() if row['parent_pid'] in selected}-selected
 if not new:break
 selected|=new
 if len(selected)>MAX_ROWS:raise ValueError('descendant_bound')
else:raise ValueError('descendant_depth_bound')
rows=[]
for pid in sorted(selected):
 p=Path('/proc')/str(pid);row=dict(proc[pid]);row['io']=numeric_io(p/'io')
 try:
  w=read_proc(p/'wchan',256).decode('ascii').strip()
  row['wait_class']=w if w in ('do_wait','pipe_read','futex_wait_queue','hrtimer_nanosleep','0') else 'other'
 except (OSError,ValueError,UnicodeError):row['wait_class']='unavailable'
 counts={'team_record_fds':0,'campaign_record_fds':0,'site_finder_database_fds':0,'other_fds':0};n=0
 try:
  for fd in (p/'fd').iterdir():
   n+=1
   if n>MAX_FDS:counts['truncated']=True;break
   try:t=os.readlink(fd)
   except OSError:continue
   if t.startswith(str(RAW/'catalogs'/CID/'records')+'/'):counts['team_record_fds']+=1
   elif t.startswith(str(FOLDER/'records')+'/'):counts['campaign_record_fds']+=1
   elif t.startswith(str(FOLDER/'site-finder.sqlite')) or t.startswith(str(FOLDER/'.site-finder.sqlite.')):
    counts['site_finder_database_fds']+=1
   else:counts['other_fds']+=1
 except OSError:counts['unavailable']=True
 row['fd_classes']=counts;rows.append(row)

fixed={
 'campaign_directory':FOLDER,'records_directory':FOLDER/'records','state':FOLDER/'state.json',
 'state_temporary':FOLDER/'state.tmp','summary':FOLDER/'records/campaign_summaries'/(CID+'.summary.yaml'),
 'pairing_policy':FOLDER/'pairing/policy.json','base_source_directory':FOLDER/'base/source',
 'freeze_request':FOLDER/'jobs/freeze.request.json','freeze_output':FOLDER/'jobs/freeze.json',
 'freeze_command_receipt':FOLDER/'jobs/freeze.command.json','freeze_stderr':FOLDER/'jobs/freeze.stderr.txt',
 'site_finder_database':FOLDER/'site-finder.sqlite','site_finder_journal':FOLDER/'site-finder.sqlite-journal',
 'site_finder_wal':FOLDER/'site-finder.sqlite-wal','site_finder_shm':FOLDER/'site-finder.sqlite-shm',
 'campaign_database':FOLDER/'campaign.sqlite',
 'public_campaign_argv':RAW/'attempts'/CID/'attempt-1/campaign.argv.json',
 'runner_exit':RAW/'attempts'/CID/'attempt-1/runner.exit-code.txt',
 'wrapper_exit':RAW/'attempts'/CID/'attempt-1/wrapper.exit-code.txt',
 'stopped_receipt':RAW/'attempts'/CID/'attempt-1/stopped-receipt.json'}
metadata={label:file_stat(path) for label,path in fixed.items()}
temporary_databases=[]
if file_stat(FOLDER).get('state')=='present':
 count=0
 for p in FOLDER.iterdir():
  count+=1
  if count>512:raise ValueError('top_level_directory_bound')
  match=re.fullmatch(r'\.(site-finder|campaign)\.sqlite\.([1-9][0-9]{0,9})\.tmp(?:-(journal|wal|shm))?',p.name)
  if match:
   temporary_databases.append({'family':match.group(1),'writer_pid':int(match.group(2)),
                              'suffix':match.group(3) or 'database','stat':file_stat(p)})
calls=[];provider=FOLDER/'provider'
if file_stat(provider).get('state')=='present':
 count=0
 for p in provider.iterdir():
  count+=1
  if count>64:raise ValueError('provider_directory_bound')
  match=re.fullmatch(re.escape(CID)+r'\.call([1-9][0-9]{0,3})',p.name)
  if not match:continue
  calls.append({'call_number':int(match.group(1)),'directory':file_stat(p),
                'workspace':file_stat(p/'workspace'),'receipt':file_stat(p/'provider.json')})

result={'format':'swdb.lanl17-p1-startup-metadata-only.v1',
 'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'campaign':CID,
 'helper_anchor_count':len(helpers),'owned_process_tree':rows,'file_stats':metadata,
 'anchor_status':'matched_owned_p1_helper' if helpers else 'unknown_anchor_absent_not_idle',
 'temporary_database_stats':temporary_databases,
 'provider_call_stats':sorted(calls,key=lambda r:r['call_number']),
 'campaign_state_or_database_bodies_read':False,'argv_or_comm_bodies_returned':False,
 'bounded_owned_proc_metadata_and_cmdline_read':True,
 'raw_log_or_auth_or_prompt_reads':False,
 'scientific_commands_run':False,'scientific_admission':False,
 'scope':'Advisory live filesystem and owned-process metadata only; stage existence is not completion.'}
b=(json.dumps(result,sort_keys=True,allow_nan=False)+'\n').encode()
if len(b)>131072:raise ValueError('structured_return_bound')
os.write(1,b)
