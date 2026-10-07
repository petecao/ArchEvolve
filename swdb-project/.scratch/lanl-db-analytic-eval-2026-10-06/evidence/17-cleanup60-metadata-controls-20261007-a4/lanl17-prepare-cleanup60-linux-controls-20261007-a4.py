"""Prepare fresh exact-hash cleanup controls only; never dispatch or import them."""
import ast,datetime,hashlib,json,pathlib
P=pathlib.Path;tmp=P('/private/tmp')
H='28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414';SUP='fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0'
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
block="""development=P('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-development-20261006-a3')
assert (development/'runner-exit-code.txt').read_text().strip()=='0' and (development/'exit-code.txt').read_text().strip()=='0'
accepted=json.loads((development/'acceptance.json').read_text())
assert accepted['identity_sha256']==hashlib.sha256(json.dumps({k:v for k,v in accepted.items() if k!='identity_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
assert accepted['phase']=='development' and accepted['source_commit']=='f893fed400347ed23d92e917d8bde21b75e5375d' and accepted['source_clean'] is True and accepted['ready_for_holdout'] is True
assert json.loads((development/'final-cleanup.json').read_text())['survivors']=={}
development_lane=json.loads((development/'lane.json').read_text())['socket_lane']
assert development_lane['node']==0 and development_lane['numa_memory_policy']=='bind:0' and development_lane['exit_code']==0 and development_lane['ended_utc']
for phase in ('holdout','band-report'):
 assert not P('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-'+phase+'-20261006-a3').exists()
"""
oldblock="for phase in ('development','holdout','band-report'):\n assert not P('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-'+phase+'-20261006-a3').exists()\n"
snapshots={}
for kind in ('cleanup-caps-smoke','metadata-supervisor-fixture'):
 old=tmp/('lanl17-dispatch-'+kind+'-20261007-a3.py');new=tmp/('lanl17-dispatch-'+kind+'-20261007-a4.py')
 text=old.read_text();assert oldblock in text
 text=text.replace('lanl17-control-caps-20261007-a3.py','lanl17-control-cleanup60-20261007-a4.py').replace('69dcfe546d3042228ccca4fb29e8409da88443ba15680f30bfdc929ea12ae2b9',H)
 text=text.replace('lanl17-metadata-supervisor-caps-20261007-a3.py','lanl17-metadata-supervisor-cleanup60-20261007-a4.py').replace('16661d7a9347e328a5263b06d807f3632c5abcfcf41a0bd97655a6bba302176b',SUP)
 text=text.replace('20261007-a3','20261007-a4').replace(oldblock,block)
 text=text.replace("'other_elapsed_cpu_phases_absent':True","'prior_development_completed':True,'holdout_report_absent':True")
 ast.parse(text);assert not new.exists();new.write_text(text)
 data=new.read_bytes();snapshots[new.name]={'path':str(new),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'baseline':str(old)}
out={'format':'swdb.parent17-cleanup60-linux-dispatch-preparation.v1','prepared_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'snapshots':snapshots,'selected_helper_sha256':H,'selected_supervisor_sha256':SUP,'only_changes':'Fresh a4 paths/full-helper pins and stronger after-development acceptance gate; existing wrapper/capacity/all-free/sourceC/outer180/KILL60 and original4d/a848 unchanged.','actual_linux_checks_run':False,'raw_transferred':False,'scope':'Parent source preparation only; two fresh exact-hash Linux cleanup tests wait for development0/cleanup/release before holdout.'};out['identity_sha256']=digest(out)
path=tmp/'lanl17-cleanup60-linux-dispatch-preparation-20261007-a4.json';assert not path.exists();path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
