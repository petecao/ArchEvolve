"""One bounded isolated five-case execution; no author or scientific main."""
import datetime,hashlib,json,os,pathlib,re,subprocess,sys,time
P=pathlib.Path
PREP=P('/private/tmp/lanl17-parent-full-record-index-request-author-r1-source-preparation-20261007.json')
OUT=P('/private/tmp/lanl17-index-request-author-r1-tests-actual-20261007')
def sha(raw): return hashlib.sha256(raw).hexdigest()
def digest(value): return sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode())
def write(path,raw):
 fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as stream: stream.write(raw);stream.flush();os.fsync(stream.fileno())
def encoded(value): return (json.dumps(value,indent=2,ensure_ascii=True,allow_nan=False)+'\n').encode()
def pin(path):
 raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':sha(raw)}
prep_raw=PREP.read_bytes();prep=json.loads(prep_raw)
assert len(prep_raw)==4526 and sha(prep_raw)=='f1ea8ccc986bfb40e68c41fa9ef8aa1a1b3b6f1054615b0bc364ccfbef192911'
assert prep['canonical_ensure_ascii'] is True and prep['identity_sha256']=='acf228e14a566c9637ca8694588cee96bfaf8ac2ea20e29637c9d3999ef19166'
assert prep['identity_sha256']==digest({k:v for k,v in prep.items() if k!='identity_sha256'})
assert prep['actual_inputs_requests_catalogs_fixtures_sourceimports_test_bodies_mains_Store_provider_native_remote_Git_mutations_executed'] is False
pins=dict(prep['pins']);pins['original_source_preparation']=pin(PREP);pins['reviewed_execution_driver']=pin(P(__file__))
for row in pins.values(): assert pin(P(row['path']))==row
methods=prep['synthetic_test_source']['methods'];assert len(methods)==len(set(methods))==5
assert prep['synthetic_test_source']['state']=='NOT_RUN'
paths={name:P(str(OUT)+suffix) for name,suffix in [('start','.start.json'),('stdout','.stdout'),('stderr','.stderr'),('receipt','.json')]}
assert all(not p.exists() and not p.is_symlink() for p in paths.values())
started=datetime.datetime.now(datetime.timezone.utc).isoformat();opened=time.monotonic()
write(paths['start'],encoded({'format':'swdb.lanl17-index-request-author-r1-isolated-tests-start.v1','started_utc':started,'sealed':False,'preparation_identity':prep['identity_sha256'],'planned_test_bodies':5,'source_pins_sha256':digest(pins),'author_main_or_actual_inputs':False}))
stdout_fd=os.open(paths['stdout'],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600);stderr_fd=os.open(paths['stderr'],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
timed_out=False
with os.fdopen(stdout_fd,'wb') as stdout,os.fdopen(stderr_fd,'wb') as stderr:
 try:
  result=subprocess.run([sys.executable,'-B','-I',pins['isolated_test_SOURCE_NOT_RUN']['path']],stdout=stdout,stderr=stderr,timeout=120,check=False);code=result.returncode
 except subprocess.TimeoutExpired:
  timed_out=True;code=None
 stdout.flush();stderr.flush();os.fsync(stdout.fileno());os.fsync(stderr.fileno())
ended=datetime.datetime.now(datetime.timezone.utc).isoformat();elapsed=time.monotonic()-opened
body=paths['stderr'].read_text();count=re.search(r'^Ran (\d+) tests? in ',body,re.M)
passed=re.findall(r'^(test_\S+) \(__main__\.SyntheticRouteAndPrivacy\.\1\) \.\.\. ok$',body,re.M)
ok=bool(re.search(r'^OK$',body,re.M));preserved=all(pin(P(row['path']))==row for row in pins.values())
outputs={name:dict(pin(paths[name]),original_sealed=False) for name in ('start','stdout','stderr')}
receipt={'format':'swdb.lanl17-index-request-author-r1-isolated-tests-actual.v1','canonical_ensure_ascii':True,'started_utc':started,'ended_utc':ended,'actual_subprocess_returncode':code,'actual_timed_out':timed_out,'actual_reported_test_count':int(count[1]) if count else None,'actual_reported_OK':ok,'actual_successful_test_method_names':passed,'expected_method_names':methods,'elapsed_parent_seconds':elapsed,'original_preparation_identity':prep['identity_sha256'],'source_pins':pins,'outputs':outputs,'batch_invocations':1,'source_and_preparation_preserved':preserved,'actual_inputs_constructed':False,'author_main_or_Store_validate_index_writer_auditor_collector_native_provider_campaign_remote_actions':0,'scientific_admission':False,'scope':'One local five-case synthetic route/privacy batch using closed exact source AST and mocked Git. No actual catalog, request, selected main, Store, validator, remote or scientific action. Original preparation remains NOT_RUN chronology.'}
receipt['identity_sha256']=digest(receipt);write(paths['receipt'],encoded(receipt))
print(json.dumps({'receipt':pin(paths['receipt']),'identity_sha256':receipt['identity_sha256'],'returncode':code,'timeout':timed_out,'actual_reported_test_count':receipt['actual_reported_test_count'],'actual_successful_methods':passed,'OK':ok,'originals_preserved':preserved},ensure_ascii=True,allow_nan=False))
assert code==0 and not timed_out and receipt['actual_reported_test_count']==5 and ok and preserved and set(passed)==set(methods)
