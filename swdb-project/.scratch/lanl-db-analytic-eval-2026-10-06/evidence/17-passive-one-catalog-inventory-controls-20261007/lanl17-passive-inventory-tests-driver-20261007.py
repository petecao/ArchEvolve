"""One bounded isolated four-case passive observer execution; no reader or scientific main."""
import datetime,hashlib,json,os,pathlib,re,subprocess,sys,time
P=pathlib.Path
PREP=P('/private/tmp/lanl17-passive-one-catalog-inventory-isolated-test-source-preparation-20261007.json')
OUT=P('/private/tmp/lanl17-passive-inventory-tests-actual-20261007')
def sha(raw): return hashlib.sha256(raw).hexdigest()
def digest(value): return sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
def write(path,raw):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as stream: stream.write(raw);stream.flush();os.fsync(stream.fileno())
def encoded(value): return (json.dumps(value,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
def pin(path):
 raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':sha(raw)}
prep_raw=PREP.read_bytes();prep=json.loads(prep_raw)
assert len(prep_raw)==3690 and sha(prep_raw)=='d7f046280e51efa53e99305e4830b165b8fe86dd7d486506f96a1b2d792526cc'
assert prep['identity_sha256']=='5c80086a95a3e8cd8ca5123d9ca5cfe4a02dc69a1cd91f82d404f90ff43deac7'
assert prep['identity_sha256']==digest({k:v for k,v in prep.items() if k!='identity_sha256'})
assert all(v==0 for v in prep['actions_executed'].values())
pins={k:prep[k] for k in ('test_source_pin','handoff_pin','reviewed_reader_source_pin','immutable_reader_handoff_pin','immutable_reader_preparation_pin')}
reader_prep=json.loads(P(pins['immutable_reader_preparation_pin']['path']).read_bytes())
assert reader_prep['identity_sha256']=='ebd42ae1579b4aeaa439f97fd1d14edec598afff5941371e1f704585058da5b6' and reader_prep['identity_sha256']==digest({k:v for k,v in reader_prep.items() if k!='identity_sha256'})
for i,row in enumerate(reader_prep['original_supplier_pins']):pins['original_supplier_'+str(i)]=row
pins['original_test_source_preparation']=pin(PREP);pins['reviewed_execution_driver']=pin(P(__file__))
for row in pins.values(): assert pin(P(row['path']))==row
methods=prep['closed_AST_source_inspection']['unittest_method_names'];assert len(methods)==len(set(methods))==4
assert prep['state']=='source_only_NOT_RUN'
paths={name:P(str(OUT)+suffix) for name,suffix in [('start','.start.json'),('stdout','.stdout'),('stderr','.stderr'),('receipt','.json')]}
assert all(not p.exists() and not p.is_symlink() for p in paths.values())
started=datetime.datetime.now(datetime.timezone.utc).isoformat();opened=time.monotonic()
write(paths['start'],encoded({'format':'swdb.lanl17-passive-inventory-isolated-tests-start.v1','started_utc':started,'sealed':False,'preparation_identity':prep['identity_sha256'],'planned_test_bodies':4,'source_pins_sha256':digest(pins),'reader_main_or_actual_inputs':False}))
stdout_fd=os.open(paths['stdout'],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);stderr_fd=os.open(paths['stderr'],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
timed_out=False
with os.fdopen(stdout_fd,'wb') as stdout,os.fdopen(stderr_fd,'wb') as stderr:
 try:
  result=subprocess.run([sys.executable,'-B','-I',pins['test_source_pin']['path']],stdout=stdout,stderr=stderr,timeout=120,check=False);code=result.returncode
 except subprocess.TimeoutExpired:
  timed_out=True;code=None
 stdout.flush();stderr.flush();os.fsync(stdout.fileno());os.fsync(stderr.fileno())
ended=datetime.datetime.now(datetime.timezone.utc).isoformat();elapsed=time.monotonic()-opened
body=paths['stderr'].read_text();count=re.search(r'^Ran (\d+) tests? in ',body,re.M)
passed=re.findall(r'^(test_\S+) \(__main__\.PassiveObservationSyntheticCases\.\1\) \.\.\. ok$',body,re.M)
ok=bool(re.search(r'^OK$',body,re.M));preserved=all(pin(P(row['path']))==row for row in pins.values())
outputs={name:dict(pin(paths[name]),original_sealed=False) for name in ('start','stdout','stderr')}
receipt={'format':'swdb.lanl17-passive-inventory-isolated-tests-actual.v1','canonical_ensure_ascii':True,'started_utc':started,'ended_utc':ended,'actual_subprocess_returncode':code,'actual_timed_out':timed_out,'actual_reported_test_count':int(count[1]) if count else None,'actual_reported_OK':ok,'actual_successful_test_method_names':passed,'expected_method_names':methods,'elapsed_parent_seconds':elapsed,'original_preparation_identity':prep['identity_sha256'],'source_pins':pins,'outputs':outputs,'batch_invocations':1,'source_and_preparation_preserved':preserved,'actual_inputs_constructed':False,'reader_main_or_Store_validate_index_writer_auditor_collector_native_provider_campaign_remote_actions':0,'scientific_admission':False,'scope':'One local four-case synthetic passive inventory/summary batch using closed exact source AST and fresh opaque/summary sentinels. No actual catalog, M2, request, selected main, source or Git inspection, Store, validator, remote or scientific action. Both original preparations remain NOT_RUN chronology.'}
receipt['identity_sha256']=digest(receipt);write(paths['receipt'],encoded(receipt))
print(json.dumps({'receipt':pin(paths['receipt']),'identity_sha256':receipt['identity_sha256'],'returncode':code,'timeout':timed_out,'actual_reported_test_count':receipt['actual_reported_test_count'],'actual_successful_methods':passed,'OK':ok,'originals_preserved':preserved},ensure_ascii=True,allow_nan=False))
assert code==0 and not timed_out and receipt['actual_reported_test_count']==4 and ok and preserved and set(passed)==set(methods)
