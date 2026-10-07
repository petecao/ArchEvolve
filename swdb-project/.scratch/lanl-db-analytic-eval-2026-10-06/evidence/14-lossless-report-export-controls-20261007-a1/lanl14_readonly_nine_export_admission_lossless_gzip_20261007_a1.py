#!/usr/bin/env python3
"""Selected-record custody reader, prepared 2026-10-07 ET.

Execute only after the parent accepts an actual complete-catalogue export.
This read-only disclosure check never replaces its full Store/team/schema gates.
No Store construction, validation/estimate/compiler/provider/native command,
network, raw IR/count/log stream, filesystem write or catalogue narrowing.
The compact receipt inherits runner/wrapper zero from the reviewed lossless exporter derived from bf5
preconditions; it does not serialize those raw exit-code files directly.
"""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import gzip,stat,time,zlib

# Lossless report-transfer codec; source-only prospective administration.
MAX_GIT_REPORT_BYTES = 100 * 1024 * 1024
MAX_ORIGINAL_REPORT_BYTES = 1024 * 1024 * 1024
REPORT_CODEC_SECONDS = 3600
REPORT_TRANSFER_POLICY = 'swdb.lanl14-lossless-report-transfer.v1'
REPORT_STAT_KEYS = ('st_dev','st_ino','st_uid','st_mode','st_size','st_mtime_ns','st_ctime_ns')

def _report_require(condition, reason):
 if not condition: raise ValueError(reason)

def _report_deadline():
 return time.monotonic() + REPORT_CODEC_SECONDS

def _report_remaining(deadline):
 _report_require(time.monotonic() < deadline, 'Report codec administrative deadline exceeded')

def _report_stamp(path):
 path=Path(path)
 _report_require(path.is_absolute() and '..' not in path.parts, 'Report path must be absolute')
 _report_require(not any(p.is_symlink() for p in (path,*path.parents)), 'Report symlink refused')
 _report_require(path.resolve(strict=True)==path, 'Report path resolution differs')
 current=path.stat()
 _report_require(stat.S_ISREG(current.st_mode) and current.st_uid==os.getuid(), 'Report regular owned file required')
 _report_require(current.st_nlink==1 and not current.st_mode&0o022, 'Report link or writable file refused')
 return {k:getattr(current,k) for k in REPORT_STAT_KEYS}

def _report_chunks(path, maximum, deadline, expected=None):
 _report_remaining(deadline);path=Path(path);before=_report_stamp(path)
 _report_require(0<before['st_size']<=maximum, 'Report file byte bound exceeded')
 if expected is not None:
  _report_require(before['st_size']==expected['bytes'], 'Report pinned byte size differs')
  if 'stat' in expected: _report_require(before==expected['stat'], 'Report pinned stat differs')
 fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
 count=0;hasher=hashlib.sha256()
 with os.fdopen(fd,'rb') as stream:
  opened_stat=os.fstat(stream.fileno());opened={k:getattr(opened_stat,k) for k in REPORT_STAT_KEYS}
  _report_require(opened==before, 'Report opened stat differs')
  while True:
   _report_remaining(deadline);block=stream.read(min(1024*1024,maximum-count+1))
   if not block: break
   count+=len(block);_report_require(count<=maximum, 'Report read byte bound exceeded')
   hasher.update(block);yield block
  closed_stat=os.fstat(stream.fileno());closed={k:getattr(closed_stat,k) for k in REPORT_STAT_KEYS}
 _report_require(closed==before==_report_stamp(path), 'Report source changed during read')
 _report_require(count==before['st_size'], 'Report returned bytes differ from stat')
 if expected is not None:
  _report_require(hasher.hexdigest()==expected['sha256'], 'Report pinned returned-byte hash differs')

def _report_file_pin(path, maximum, deadline=None, expected=None):
 deadline=_report_deadline() if deadline is None else deadline
 before=_report_stamp(path);hasher=hashlib.sha256();count=0
 for block in _report_chunks(path,maximum,deadline,expected):hasher.update(block);count+=len(block)
 _report_require(before==_report_stamp(path), 'Report source changed while pinned')
 return {'bytes':count,'sha256':hasher.hexdigest(),'stat':before}

class _ReportCappedWriter:
 def __init__(self, stream, maximum, deadline):
  self.stream=stream;self.maximum=maximum;self.deadline=deadline;self.total=0
 def write(self, value):
  _report_remaining(self.deadline)
  _report_require(self.total+len(value)<=self.maximum, 'Compressed report exceeds Git blob bound')
  written=self.stream.write(value)
  _report_require(written==len(value), 'Compressed report short write')
  self.total+=written;return written
 def flush(self):
  _report_remaining(self.deadline);self.stream.flush()

def _report_transfer_contract(transfer):
 expected={'format','encoding','original','exported','report_identity_sha256','Git_blob_max_bytes',
           'original_report_max_bytes','gzip','original_remote_report_unchanged',
           'decoded_original_bytes_equal','JSON_reserialized'}
 _report_require(set(transfer)==expected, 'Report transfer fields differ')
 _report_require(transfer['format']==REPORT_TRANSFER_POLICY, 'Report transfer policy differs')
 _report_require(transfer['Git_blob_max_bytes']==MAX_GIT_REPORT_BYTES and transfer['original_report_max_bytes']==MAX_ORIGINAL_REPORT_BYTES, 'Report transfer administrative bounds differ')
 for name in ('original','exported'):
  pin=transfer[name]
  _report_require(set(pin)==({'bytes','sha256','path'} if name=='exported' else {'bytes','sha256'}), 'Report transfer pin fields differ')
  _report_require(type(pin['bytes']) is int and 0<pin['bytes']<=(MAX_GIT_REPORT_BYTES if name=='exported' else MAX_ORIGINAL_REPORT_BYTES), 'Report transfer size refused')
  _report_require(type(pin['sha256']) is str and re.fullmatch('[a-f0-9]{64}',pin['sha256']) is not None, 'Report transfer SHA refused')
 _report_require(type(transfer['report_identity_sha256']) is str and re.fullmatch('[a-f0-9]{64}',transfer['report_identity_sha256']) is not None, 'Report semantic identity refused')
 _report_require(transfer['original_remote_report_unchanged'] is True and transfer['decoded_original_bytes_equal'] is True and transfer['JSON_reserialized'] is False, 'Lossless report custody differs')
 if transfer['original']['bytes']>MAX_GIT_REPORT_BYTES:
  _report_require(transfer['encoding']=='gzip' and transfer['gzip']=={'filename':'','mtime':0,'compresslevel':9,'members':1}, 'Conditional deterministic gzip policy differs')
 else:
  _report_require(transfer['encoding']=='identity' and transfer['gzip'] is None, 'Small report must retain original representation')
  _report_require({k:v for k,v in transfer['exported'].items() if k!='path'}==transfer['original'], 'Original uncompressed report pin differs')
 _report_require(type(transfer['exported']['path']) is str, 'Report transfer pathname refused')


def _report_decoded_chunks(path, transfer, deadline):
 _report_transfer_contract(transfer)
 original=transfer['original'];expected=transfer['exported'];total=0;hasher=hashlib.sha256()
 if transfer['encoding']=='identity':
  pieces=_report_chunks(path,MAX_GIT_REPORT_BYTES,deadline,expected)
  for block in pieces:
   total+=len(block);_report_require(total<=original['bytes'], 'Decoded original byte bound exceeded')
   hasher.update(block);yield block
 else:
  decoder=zlib.decompressobj(31);first=True
  for block in _report_chunks(path,MAX_GIT_REPORT_BYTES,deadline,expected):
   _report_require(not decoder.eof, 'Trailing or concatenated gzip report refused')
   if first:
    _report_require(block[:10]==b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff', 'Deterministic gzip header differs')
    first=False
   pending=block
   while pending:
    _report_remaining(deadline);previous=len(pending)
    output=decoder.decompress(pending,min(1024*1024,original['bytes']-total+1))
    total+=len(output);_report_require(total<=original['bytes'], 'Decoded original byte bound exceeded')
    hasher.update(output)
    if output:yield output
    pending=decoder.unconsumed_tail
    _report_require(not decoder.unused_data, 'Trailing or concatenated gzip report refused')
    _report_require(not pending or len(pending)<previous or output, 'Gzip decoder made no progress')
  _report_require(not first and decoder.eof and not decoder.unconsumed_tail and not decoder.unused_data, 'Incomplete gzip report refused')
 _report_require(total==original['bytes'] and hasher.hexdigest()==original['sha256'], 'Decoded original report bytes/hash differ')


def read_report_transfer(path, transfer):
 """Read one exact pinned original byte sequence; no JSON interpretation."""
 return b''.join(_report_decoded_chunks(Path(path),transfer,_report_deadline()))


def _report_compare_original(source, transfer_path, transfer, original_pin, deadline):
 decoded=iter(_report_decoded_chunks(transfer_path,transfer,deadline));buffer=bytearray()
 for original in _report_chunks(source,MAX_ORIGINAL_REPORT_BYTES,deadline,original_pin):
  while len(buffer)<len(original):
   try:buffer.extend(next(decoded))
   except StopIteration:raise ValueError('Decoded report omitted original bytes') from None
  _report_require(bytes(buffer[:len(original)])==original, 'Decoded report differs byte-for-byte')
  del buffer[:len(original)]
 _report_require(not buffer, 'Decoded report contains extra bytes')
 for extra in decoded:_report_require(not extra, 'Decoded report contains extra bytes')


def prepare_report_transfer(source, gzip_path, report_identity_sha256):
 """Prepare conditional lossless transfer before any mutable Git operation."""
 source=Path(source);gzip_path=Path(gzip_path);deadline=_report_deadline()
 original=_report_file_pin(source,MAX_ORIGINAL_REPORT_BYTES,deadline)
 _report_require(type(report_identity_sha256) is str and re.fullmatch('[a-f0-9]{64}',report_identity_sha256) is not None, 'Report semantic identity refused')
 compressed=original['bytes']>MAX_GIT_REPORT_BYTES
 selected=source
 if compressed:
  _report_require(gzip_path.is_absolute() and '..' not in gzip_path.parts and not any(p.is_symlink() for p in (gzip_path,*gzip_path.parents)), 'Fresh gzip path refused')
  parent=gzip_path.parent;parent_stat=parent.stat()
  _report_require(parent.resolve(strict=True)==parent and stat.S_ISDIR(parent_stat.st_mode) and parent_stat.st_uid==os.getuid() and not parent_stat.st_mode&0o022, 'Gzip parent custody refused')
  _report_require(not gzip_path.exists(), 'Existing gzip report preserved; replay refused')
  fd=os.open(gzip_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
  with os.fdopen(fd,'wb') as stream:
   writer=_ReportCappedWriter(stream,MAX_GIT_REPORT_BYTES,deadline)
   with gzip.GzipFile(filename='',mode='wb',compresslevel=9,fileobj=writer,mtime=0) as archive:
    for block in _report_chunks(source,MAX_ORIGINAL_REPORT_BYTES,deadline,original):archive.write(block)
   stream.flush();os.fsync(stream.fileno())
  directory_fd=os.open(parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
  try:os.fsync(directory_fd)
  finally:os.close(directory_fd)
  selected=gzip_path
 exported=_report_file_pin(selected,MAX_GIT_REPORT_BYTES,deadline)
 transfer={'format':REPORT_TRANSFER_POLICY,'encoding':'gzip' if compressed else 'identity',
           'original':{k:original[k] for k in ('bytes','sha256')},
           'exported':{'path':selected.name,**{k:exported[k] for k in ('bytes','sha256')}},
           'report_identity_sha256':report_identity_sha256,'Git_blob_max_bytes':MAX_GIT_REPORT_BYTES,
           'original_report_max_bytes':MAX_ORIGINAL_REPORT_BYTES,
           'gzip':{'filename':'','mtime':0,'compresslevel':9,'members':1} if compressed else None,
           'original_remote_report_unchanged':True,'decoded_original_bytes_equal':True,'JSON_reserialized':False}
 _report_compare_original(source,selected,transfer,original,deadline)
 _report_require(_report_file_pin(source,MAX_ORIGINAL_REPORT_BYTES,deadline)==original and _report_file_pin(selected,MAX_GIT_REPORT_BYTES,deadline)==exported, 'Report transfer changed after exact comparison')
 return selected,transfer,original,exported


F6='f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
C='f893fed400347ed23d92e917d8bde21b75e5375d'
HELPER='e79e4b2e295f07967a1f4f67e7501c35d9d402101330ac9347f98cfb282bf63a'
EXPORTER='928af82facd9f36dfdbca6595d2c2e9d1091dd0064c9fe53fc41c163879e026e'
BASE_EXPORTER='bf5add9eb35daa5402a0359f6ace5c542a289f9b60b14cbd00aa763097a9645d'
REPORTER='26f6d803d17381a70241e77bed5a28a3340f03549135100e475f550c4e252303'
CHARS={('bfs','dx100'):'bfs.functional.kron-g16.t4.characterization.objects.a2',
 ('bfs','cpu'):'bfs.kron-g16.t1.characterization.objects.a1',('bc','cpu'):'bc.kron-g16.t1.characterization.objects.a1',
 ('pagerank','cpu'):'pagerank.jacobi.kron-g16.cpu.t1.characterization.generality.a1',
 ('pagerank','dx100'):'pagerank.jacobi.kron-g16.dx100.t4.characterization.generality.a1',
 ('pagerank','maple'):'pagerank.jacobi.kron-g16.maple.t2.characterization.generality.a1',
 ('bfs','maple'):'bfs.kron-g16.bfs-maple.t2.characterization.generality.a1',
 ('bc','maple'):'bc.kron-g16.bc-maple.t2.characterization.generality.a1',
 ('bc','dx100'):'bc.kron-g16.bc-dx100.t4.characterization.generality.a1'}
OLD_FILES={'bfs.kron-g16.t1.characterization.objects.a1':'cda2c51423c167249fd760f359ee0ead180bcb2e2d4db2c722c9b724120458ba',
 'bc.kron-g16.t1.characterization.objects.a1':'d12b5f57c61007219d367942ee554db1d27ee1d8614e2c1279e1164230f534e8',
 'bfs.functional.kron-g16.t4.characterization.objects.a2':'dfbb5791ebe8bf63b544a548541fd8b5a7eeb8e033fe3aef2316c4c7467e325a'}
THREADS={'cpu':1,'dx100':4,'maple':2}
TARGETS={'cpu':('mbit10.cpu.lanl20261006.t1.services.v1','mbit10'),
 'dx100':('dx100-e4fc4af-functional-analytic-v1.t4.estimated.a2','dx100-e4fc4af-functional-analytic-v1'),
 'maple':('maple-isca2022.fpga-reference.t2','maple-isca2022')}
ALLOWED={f'{k}.kron-g{s}.t1.characterization.objects.a1' for k in ('bfs','bc') for s in (16,17)}
MISSING={'memory_scenario.characterization_allowlist','service_scope.characterization_allowlist'}
JACOBI='ea1e58b6957b0bcc1e76f4fde54131aa52bdefd2014dae604a9b7d9d1a5dae70'

def require(value,message):
 if not value:raise ValueError(message)
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def relative(value):
 p=Path(value);require(not p.is_absolute() and '..' not in p.parts,'Relative in-checkout path required');return p
def missing(regions):
 return {x for r in regions for b in r.get('bounds',[])+r.get('overheads',[]) for x in b.get('missing',[])}
def same_regions(actual,expected,scope):
 require(len(actual)==len(expected),'Per-region report row omitted or added')
 for a,b in zip(actual,expected):
  require(a.get('inputs_scope')==scope and {k:v for k,v in a.items() if k!='inputs_scope'}==b,'Exact region formula/count/missing inputs differ')

def main():
 own_source_pin=_report_file_pin(Path(__file__).absolute(),MAX_GIT_REPORT_BYTES)
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--checkout',type=Path,required=True)
 for name in ('export-commit','source-commit','manifest-sha256','receipt-sha256','receipt-identity-sha256','count-receipt-sha256','tag','target-pins'):
  p.add_argument('--'+name,required=True)
 for name in ('receipt','report','request','markdown','count-receipt'):p.add_argument('--'+name,type=relative,required=True)
 a=p.parse_args();root=a.checkout.resolve();cwd=root/'swdb-project'
 for path in (a.receipt,a.report,a.request,a.markdown,a.count_receipt):
  resolved=(cwd/path).resolve();require(resolved.is_relative_to(cwd) and not (cwd/path).is_symlink() and path.parts[:3]==('.scratch','lanl-db-analytic-eval-2026-10-06','evidence'),'Explicit non-symlink SWDB evidence path required')
 for name in ('export_commit','source_commit'):require(re.fullmatch('[a-f0-9]{40}',getattr(a,name)),name+' must be an exact full SHA')
 for name in ('manifest_sha256','receipt_sha256','receipt_identity_sha256','count_receipt_sha256'):require(re.fullmatch('[a-f0-9]{64}',getattr(a,name)),name+' must be exact')
 require(re.fullmatch('[a-z0-9][a-z0-9-]{0,40}',a.tag),'Exact prospective report tag required')
 target_pins=json.loads(a.target_pins);require(set(target_pins)==set(TARGETS),'Three explicit target pins required')
 for key,pin in target_pins.items():require(set(pin)=={'id','sha256'} and pin['id']==TARGETS[key][0] and re.fullmatch('[a-f0-9]{64}',pin['sha256']),'Target identity/pin differs')
 require(target_pins['cpu']['sha256']=='9fec46b1ab4c8ac2e8e501e61cf137c075ec40b6eef128a247cf28dd54fca76b','Actual final CPU services target differs')
 def git(*argv):return subprocess.check_output(['git','-C',str(root),*argv],text=True,timeout=120,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0'}).strip()
 require(git('rev-parse','HEAD')==a.export_commit and not git('status','--porcelain'),'Exact clean pure export checkout required')
 require(git('rev-list','--parents','-n','1',a.export_commit).split()==[a.export_commit,a.source_commit],'Pure export must have exactly the final source as its sole parent')
 require(git('merge-base',C,a.source_commit)==C,'Final C is not an ancestor of supplied source R')
 modules={v.relative_to(cwd/'swdb').as_posix():sha(v) for v in sorted((cwd/'swdb').rglob('*.py'))}
 digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 require(len(modules)==185 and digest(modules)==F6,'Exact complete 185-module F6 source required before imports')
 require(sha(cwd/'scripts/generality_report.py')==REPORTER,'Exact public region reporter source differs')
 sys.dont_write_bytecode=True;sys.path.insert(0,str(cwd))
 from swdb import access,artifacts,analytic_binding,analytic_count_reuse,bfs_protocol
 require(artifacts.digest(modules)==F6,'Public digest differs')
 def checked(path):
  d=json.loads((cwd/path).read_text());require(d['identity_sha256']==artifacts.digest({k:v for k,v in d.items() if k!='identity_sha256'}),'Metadata self-seal differs: '+str(path));return d
 receipt=checked(a.receipt)
 require(sha(cwd/a.receipt)==a.receipt_sha256 and receipt['identity_sha256']==a.receipt_identity_sha256,'Actual receipt must be pinned before report decoding')
 transfer=receipt['report_transfer'];require(transfer['exported']['path']==str(a.report),'Actual report representation path differs')
 expected_suffix='-report.json.gz' if transfer['encoding']=='gzip' else '-report.json'
 require(a.report.name=='14-generality-final-'+a.tag+expected_suffix,'Conditional report filename differs')
 report=json.loads(read_report_transfer(cwd/a.report,transfer))
 require(report['identity_sha256']==transfer['report_identity_sha256']==artifacts.digest({k:v for k,v in report.items() if k!='identity_sha256'}),'Original lossless report semantic seal differs')
 request=checked(a.request);count=checked(a.count_receipt)
 require(sha(cwd/a.receipt)==a.receipt_sha256 and receipt['identity_sha256']==a.receipt_identity_sha256,'Actual export receipt file/semantic identity differs')
 require(receipt['format']=='swdb.lanl14-final-report-export.v1' and receipt['source_commit']==a.source_commit and receipt['source_clean'] is True,'Final clean source receipt differs')
 require(receipt['helper_sha256']==HELPER and receipt['exporter_sha256']==EXPORTER and receipt['layout_exporter_base_sha256']==BASE_EXPORTER and receipt['manifest_sha256']==a.manifest_sha256,'Selected exact a5/lossless-exporter/manifest custody differs')
 require(receipt['provider_calls']==receipt['application_timings']==0 and receipt['raw_transferred'] is False and receipt['cleanup_survivors']=={},'Exporter transfer/execution/cleanup scope differs')
 require(receipt['prior_record_library_app_bytes_preserved'] is True and str(receipt['validation']).startswith('OK: '),'Full exported catalogue validation/preservation missing')
 accept=receipt['acceptance'];require(accept['identity_sha256']==artifacts.digest({k:v for k,v in accept.items() if k!='identity_sha256'}),'Runner acceptance seal differs')
 require(accept['source_commit']==a.source_commit and accept['source_clean'] is True and accept['manifest_sha256']==a.manifest_sha256 and accept['final_estimator_sha256']==F6,'Actual runner source/manifest/F6 differs')
 require(accept['all_nine_public_estimates'] is True and accept['provider_calls']==accept['application_timings']==0 and accept['raw_transferred'] is False and accept['prior_record_library_app_bytes_preserved'] is True and str(accept['validation']).startswith('OK: '),'Complete remote public catalogue admission missing')
 require('(verified:' in accept['verified_lane'],'Verified runner lane missing')
 lane=receipt['lane'];node=lane['node'];require(type(node)is int and node in (0,1),'Owned lane node differs')
 require(lane['exit_code']==0 and lane['ended_utc'] and lane['lease_name']==f'mbit10-evaluation-node{node}' and lane['numa_memory_policy']==f'bind:{node}' and lane['job']=='swdb-lanl14-reports-'+a.tag,'Released successful confined report lane required')
 command=lane['command'];require(len(command)==5 and command[0]=='python3' and Path(command[1]).name=='helper.py' and command[2:4]==['run','--manifest'] and Path(command[4]).name=='manifest.json','Pinned report runner command differs')
 require(report['format']=='swdb.generality-report.v1' and request['format']=='swdb.generality-report-request.v1' and report['reference']==request['reference']=={'kernel':'bfs','target':'dx100'},'Nine-report format/reference differs')
 code={'estimator_sha256':F6,'module_hashes':modules,'estimator_and_mechanism_diff':[]};require(report['code_equality']==receipt['code_equality']==code,'Complete estimator/mechanism source equality differs')
 require(receipt['nine_report_sha256']==accept['report_sha256']==report['identity_sha256'] and accept['request_sha256']==report['request_sha256']==request['identity_sha256'],'Report/request pins differ')
 require(report['whole_call_scope']=='Median of complete trial totals; aggregate region diagnostics are never summed.','Whole-trial aggregation scope differs')
 pairs=request['pairs'];require(len(pairs)==len(report['pairs'])==9 and [(q['kernel'],q['target']) for q in pairs]==list(CHARS),'Exact nine pairs/order including DX BFS FIRST required')
 require(pairs[0]['estimate']==accept['fresh_dx_bfs_reference'],'Fresh DX BFS reference pin differs')
 closure=receipt['new_records'];require(receipt['new_canonical_records']==len(closure)==18 and len({r['id'] for r in closure})==len({r['path'] for r in closure})==18,'Exact 18-record unique closure required')
 require(sum(r['kind']=='protocol' for r in closure)==sum(r['kind']=='estimate' for r in closure)==9,'Nine protocols plus nine estimates required')
 pins={r['id']:r for r in closure}
 changed=[v.split('\t') for v in git('diff','--name-status',a.source_commit,a.export_commit).splitlines()]
 expected_paths={'swdb-project/records/'+r['path'] for r in closure}|{'swdb-project/'+str(v) for v in (a.receipt,a.report,a.request,a.markdown)}
 require(len(changed)==22 and all(v[0]=='A' for v in changed) and {v[1] for v in changed}==expected_paths,'Pure export must add only exact 18 canonical +4 compact report files; all prior bytes unchanged')
 require(set(accept['added_record_paths'])=={r['path'] for r in closure},'Runner-added canonical closure differs')
 require(sha(cwd/a.count_receipt)==a.count_receipt_sha256==receipt['fresh_count_receipt']['file_sha256'] and count['identity_sha256']==receipt['fresh_count_receipt']['identity_sha256'],'Immutable actual six-count receipt differs')
 require(count['raw_transferred'] is False and count['cleanup_survivors']=={} and count['application_timings']==count['provider_calls']==0 and len(count['new_records'])==10,'Original outcome-free count closure differs')
 records=cwd/'records';record_paths=[Path(v) for v in git('ls-tree','-r','--name-only',a.export_commit,'--','swdb-project/records').splitlines() if v.endswith(('.yaml','.yml'))]
 class SelectedRecords:
  """Lazy pin reader only; no global Store/schema/team/default-selection gate."""
  def __init__(self):self.dir=records;self.paths={};self.read_ids=set()
  def path(self,rid):
   if rid not in self.paths:
    found=[v for v in record_paths if v.stem==rid];require(len(found)==1,'Selected dependency path is missing/ambiguous: '+str(rid));self.paths[rid]=root/found[0]
   return self.paths[rid]
  def get(self,rid,kind=None):
   if rid is None:return None
   path=self.path(rid);require(not path.is_symlink() and path.resolve().is_relative_to(records),'Selected record leaves authoritative record root')
   data=access.read_record(path);require(data['id']==rid and (kind is None or data['kind']==kind),'Selected dependency ID/kind differs');self.read_ids.add(rid);return data
  def application_of(self,data):
   if data['kind']=='application':return data
   if data['kind']=='kernel':return self.get(data['application'],'application')
   if data['kind']=='implementation':return self.get(data['application'],'application') if 'application' in data else self.application_of(self.get(data['kernel'],'kernel'))
   return None
  def pinned(self,pin,kind):
   data=self.get(pin['id'],kind);require(self.path(pin['id']).relative_to(records).as_posix()==pin['path'] and artifacts.digest(data)==pin['sha256'] and sha(self.path(pin['id']))==pin['file_sha256'],'Selected semantic/file/path pin differs');return data
 catalog=SelectedRecords();fresh={r['id']:r for r in count['new_records']};summaries=[]
 for pair,row in zip(pairs,report['pairs']):
  kernel,target=pair['kernel'],pair['target'];threads=THREADS[target];key=(kernel,target)
  require(row['kernel']==kernel and row['target']==target and row['references']=={k:pair[k] for k in ('subject','implementation','characterization','protocol','estimate')},'Report selected references/order differ')
  for name,kind in (('protocol','protocol'),('estimate','estimate')):
   pin=pair[name];require(pin['id'] in pins and {k:v for k,v in pins[pin['id']].items() if k!='bytes'}==pin,'Request/receipt closure pin differs');require(catalog.path(pin['id']).stat().st_size==pins[pin['id']]['bytes'],'Exported canonical size differs')
  char=catalog.pinned(pair['characterization'],'workload_characterization');protocol=catalog.pinned(pair['protocol'],'protocol');estimate=catalog.pinned(pair['estimate'],'estimate')
  subject=catalog.pinned(pair['subject'],char['subject']['kind']);implementation=catalog.pinned(pair['implementation'],'implementation')
  require(char['id']==CHARS[key] and char['binding']['state']=='verified' and char['evidence_kind']=='execution' and char['coverage']['whole_timed_call'] is True,'Exact registered whole-call count required')
  require(not analytic_binding.verify_binding(char,catalog,require_available=False),'Registered source/configuration/build macro/backend binding proof differs')
  if char['id'] in OLD_FILES:require(sha(catalog.path(char['id']))==OLD_FILES[char['id']],'Historic immutable count YAML differs')
  else:require(char['id'] in fresh and fresh[char['id']]['sha256']==pair['characterization']['sha256'] and fresh[char['id']]['file_sha256']==pair['characterization']['file_sha256'],'Fresh count export pin differs')
  obs=char['observation_contract'];receipt_count=char['binding']['execution_receipt'];llvm=cwd/'swdb/llvm'
  require(receipt_count['plugin_source_sha256']==sha(llvm/'Characterize.cpp') and receipt_count['runtime_source_sha256']==sha(llvm/'CountingRuntime.cpp'),'Compiler/runtime observer differs')
  require(receipt_count['pipeline_version']=='source-normalized-v2' and receipt_count['passes']==['function(sroa,mem2reg),cgscc(inline),function(loop-simplify)'],'Source counting pipeline differs')
  require(obs['runtime_bundle_sha256']==artifacts.digest({n:sha(llvm/n) for n in ('CountingRuntime.cpp','LiveObjects.hpp','LogicalCommands.hpp')}),'Runtime bundle differs')
  require(obs['object_scope_contract']['observer_sha256']==sha(llvm/'ObjectScopes.hpp') and obs['object_scope_contract']['runtime_sha256']==sha(llvm/'ObjectScopeRuntime.hpp'),'Object observer contract differs')
  if 'observer_bundle_sha256' in obs:require(obs['observer_bundle_sha256']==artifacts.digest({n:sha(llvm/n) for n in ('Characterize.cpp','SemanticCommands.hpp')}),'Command observer bundle differs')
  td=catalog.get(target_pins[target]['id'],'target_description');td_sha=artifacts.digest(td);settings=protocol['settings'];bfs_protocol.verify_immutable(protocol)
  require(td_sha==target_pins[target]['sha256']==estimate['target_description_sha256'] and estimate['target_description']==td['id'] and estimate['target_description_snapshot']==td,'Actual target snapshot differs')
  require(settings['target_description']=={'id':td['id'],'sha256':td_sha,'snapshot':td} and settings['mode']=='estimated' and protocol['state']=='frozen' and settings['estimator_sha256']==estimate['estimator_sha256']==F6,'Frozen estimated F6/target differs')
  require(estimate['basis']=='estimated' and estimate['evidence_kind']=='execution' and estimate['characterization']==char['id'] and estimate['characterization_sha256']==artifacts.digest(char) and estimate['binding']==char['binding'],'Immutable characterization/receipt binding differs')
  require(estimate['protocol']==protocol['id'] and estimate['protocol_sha256']==protocol['identity_sha256'],'Frozen protocol identity differs')
  require(protocol['requested_id']==f'generality.{kernel}.{target}.kron-g16.t{threads}.protocol.{a.tag}' and estimate['id']==f'generality.{kernel}.{target}.kron-g16.t{threads}.estimate.{a.tag}','Fresh final report IDs/tag differ')
  require(char['subject']==estimate['subject'] and char['subject']['id']==subject['id'] and implementation['kernel']=='gapbs-'+('pr' if kernel=='pagerank' else kernel),'Subject/implementation/kernel differs')
  require((subject['kind']=='candidate' and subject['implementation']==implementation['id']) or (subject['kind']=='implementation' and subject['id']==implementation['id']),'Registered subject implementation differs')
  argv=['-g','16','-k','16','-n','5']+(['-i','1'] if kernel=='bc' and target in {'cpu','maple'} else [])
  roi='gapbs.functional_trial_lambda.v1' if target=='dx100' or kernel=='pagerank' else 'gapbs.trial_lambda.v1'
  require(char['source']['run_arguments']==argv and settings['input_run_arguments']=={char['input']:argv} and settings['inputs']==[char['input']] and char['binding']['roi']==settings['roi']==row['roi']==roi,'Exact original argv/input/ROI differs')
  require(all(t==threads for t in (char['binding']['threads'],settings['threads'],td['threads'],estimate['threads'],row['threads'])) and td['target']==estimate['target']==TARGETS[target][1] and row['input']==estimate['input']==char['input'],'Target-specific T/input scope differs')
  require(protocol['input_identities'][char['input']]==char['binding']['input_record_sha256']==artifacts.digest(catalog.get(char['input'])),'Frozen original input differs')
  require(set(protocol['source_identities'])==set(settings['sources']),'Frozen source identity set differs')
  for field in (protocol['source_identities'],settings['dependency_identities']):
   for rid,value in field.items():require(artifacts.digest(catalog.get(rid))==value,'Selected frozen transitive/source dependency differs: '+rid)
  reuse=analytic_count_reuse.resolve(char,td);require(estimate.get('count_reuse')==reuse,'Complete source/backend/layout/window/placement observation policy reuse differs')
  if key in {('bfs','dx100'),('bc','dx100')}:require(reuse is not None,'DX functional target observation policy is unavailable')
  if kernel=='pagerank':require(implementation['id']=='gapbs-pr-jacobi-analytic-v1' and char['source']['sha256']==row['source_sha256']==JACOBI and all(t['sources']==[] for t in char['trials']),'Actual original source-free Jacobi differs')
  require(estimate['ratio'] is estimate['baseline'] is None and row['ratio'] is None and row['seconds']==estimate['seconds'] and row['error_band']==estimate['error_band'],'No paired/native ratio transfer allowed')
  require(row['estimate_only']==(target=='maple') and row['accuracy_validation'] is False and row['paired_timing'] is None and row['unmapped_loops']==char['unmapped_loops'],'Reported scope/unmapped loops differ')
  identities=[(t['position'],t['sources']) for t in char['trials']];require(len(identities)==5 and [x[0] for x in identities]==list(range(5)) and [(t['position'],t['sources']) for t in estimate['trials']]==[(t['position'],t['sources']) for t in row['trials']]==identities,'Five exact whole-trial identities differ')
  same_regions(row['regions'],estimate['regions'],'diagnostic aggregate; exact inputs are in trials')
  for actual,expected,original in zip(row['trials'],estimate['trials'],char['trials']):
   require({k:v for k,v in actual.items() if k!='regions'}=={k:v for k,v in expected.items() if k!='regions'},'Exact whole-trial totals/missing context differs')
   same_regions(actual['regions'],expected['regions'],'this exact trial')
   require([r['id'] for r in expected['regions']]==[r['id'] for r in original['regions']],'Observed trial regions omitted/reordered')
  if target=='cpu':
   allow=td['extensions']['cpu_services_binding']['characterization_allowlist'];require(len(allow)==4 and {v['id'] for v in allow}==ALLOWED,'Exact four-scope CPU model changed')
   for v in allow:require(artifacts.digest(catalog.get(v['id'],'workload_characterization'))==v['sha256'],'CPU scope source identity differs')
   for mechanism in td['mechanisms']:
    selected=mechanism.get('selector',{}).get('characterization_allowlist');require(selected is None or sorted(selected,key=lambda v:v['id'])==sorted(allow,key=lambda v:v['id']),'Mechanism allowlist differs')
  if key==('pagerank','cpu'):
   require(all(estimate[k] is None for k in ('seconds','ratio','baseline','error_band')) and MISSING<=missing(estimate['regions']) and all(t['seconds'] is None and MISSING<=missing(t['regions']) for t in estimate['trials']),'PR exact unsupported transfer gaps/nulls lost')
  if target=='maple':
   ext=td['extensions'];require(ext['estimate_only'] is True and ext['accuracy_validation'] is False and ext['paired_timing'] is None and estimate['seconds'] is estimate['error_band'] is None and all(t['seconds'] is None for t in estimate['trials']),'MAPLE estimate-only/null boundary differs')
  if key in {('bfs','cpu'),('bc','cpu')}:
   proofs=estimate['extensions']['legacy_trial_scope_reconciliations'];require(len(proofs)==5 and [v['position'] for v in proofs]==list(range(5)) and all(v['characterization_sha256']==artifacts.digest(char) and v['counted_payload_sha256']==receipt_count['counted_payload_sha256'] and v['runtime_source_sha256']==receipt_count['runtime_source_sha256'] and v['scope']=='per_trial' for v in proofs),'Immutable CPU legacy reconciliation differs')
  summaries.append({'kernel':kernel,'target':target,'threads':threads,'trials':5,'aggregate_regions':len(row['regions']),'trial_regions':[len(t['regions']) for t in row['trials']],'seconds':estimate['seconds'],'ratio':None,'error_band':estimate['error_band'],'estimate_only':target=='maple',
   'configuration_pins':{'characterization_sha256':pair['characterization']['sha256'],'counted_payload_sha256':receipt_count['counted_payload_sha256'],'source_ir_sha256':receipt_count['source_ir_sha256'],'observation_contract_sha256':artifacts.digest(obs),'build_flags_sha256':artifacts.digest(char['source']['build_flags']),'source_identity_sha256':artifacts.digest(char['binding']['subject_source_identity']),'target_description_sha256':td_sha,'observation_policy_sha256':obs.get('target_observation_policy_sha256'),'roi':roi,'run_arguments_sha256':char['binding']['run_arguments_sha256']}})
  del char,protocol,estimate;gc.collect()
 require(git('rev-parse','HEAD')==a.export_commit and not git('status','--porcelain') and {v.relative_to(cwd/'swdb').as_posix():sha(v) for v in sorted((cwd/'swdb').rglob('*.py'))}==modules,'Input checkout/source changed during read-only admission')
 require(_report_file_pin(Path(__file__).absolute(),MAX_GIT_REPORT_BYTES)==own_source_pin,'Selected reader source changed')
 result={'format':'swdb.lanl14-selected-nine-export-admission.v1','updated':'2026-10-07 ET','scope':'Selected-record disclosure/custody check only; Full catalogue public validation and team/schema/default-selection admission are inherited from the reviewed lossless exporter preserving bf5 gates, never replaced.',
  'export_commit':a.export_commit,'final_source_commit':a.source_commit,'estimator_sha256':F6,'receipt_file_sha256':a.receipt_sha256,'receipt_identity_sha256':receipt['identity_sha256'],'report_identity_sha256':report['identity_sha256'],
  'new_canonical_records':18,'prior_tracked_blobs_unchanged':True,'source_clean':True,'pairs':summaries,'selected_dependency_records_read':len(catalog.read_ids),'full_catalogue_validation':receipt['validation'],
  'direct_observations':{'lane_exit_code':0,'cleanup_survivors':{},'runner_acceptance_identity_sha256':accept['identity_sha256']},
  'inherited_pinned_export_preconditions':{'runner_exit_code':0,'wrapper_exit_code':0,'source':'Exact reviewed lossless exporter preserves bf5 success() checks immutable raw exit files before sealed export commit; raw files are not serialized here.','new_native_or_compiler_execution':0,'basis':'Exact a5 dispatch/run source invokes only public metadata validation/freeze/estimate/report commands; no new process audit is invented.'},
  'provider_calls':0,'application_timings':0,'reader_native_compiler_provider_remote_actions':0,'reporter_sha256':REPORTER,'reader_sha256':own_source_pin['sha256']}
 result['report_transfer']=transfer
 result['identity_sha256']=artifacts.digest(result)
 require(_report_file_pin(Path(__file__).absolute(),MAX_GIT_REPORT_BYTES)==own_source_pin,'Selected reader source changed before success')
 print(json.dumps(result,indent=2,allow_nan=False))

if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,OSError,TypeError,subprocess.SubprocessError,zlib.error,EOFError) as exc:
  print(str(exc),file=sys.stderr);raise SystemExit(2)
