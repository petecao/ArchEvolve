"""Execute the unchanged selected exporter only after full phase/lane/cleanup completion."""
import hashlib,json,os,pathlib,socket,subprocess,sys
P=pathlib.Path
phase=sys.argv[1]
assert phase in ('holdout','report') and socket.gethostname().split('.')[0]=='mbit10' and os.getuid()!=0
C='f893fed400347ed23d92e917d8bde21b75e5375d'
source=P('/data1/yanruj/ArchEvolve-lanl-cpu-model-validation-20261006-a1')
controls=P('/data1/yanruj/lanl-cpu-controls-20261007-a1')
raw=P('/data/yanruj/EvolveSWDB_runs/lanl-analytic-cpu-'+('band-report' if phase=='report' else phase)+('-20261007-a4' if phase=='report' else '-20261006-a3'))
def git(*args):return subprocess.check_output(['git','-C',str(source),*args],text=True,timeout=120).strip()
assert git('rev-parse','HEAD')==C and not git('status','--porcelain')
leases={name:json.loads((P('/data1/yanruj/lact-host-lease')/(name+'.meta.json')).read_bytes()) for name in ('mbit10-evaluation-node0','mbit10-evaluation-node1','mbit10-evaluation')}
assert all(d['state']=='released' for d in leases.values())
assert (raw/'runner-exit-code.txt').read_text().strip()==(raw/'exit-code.txt').read_text().strip()=='0'
assert (raw/'completed.txt').is_file() and (raw/'acceptance.json').is_file() and not (raw/'runner-error.txt').exists()
lane=json.loads((raw/'lane.json').read_bytes())['socket_lane']
assert lane['node']==0 and lane['numa_memory_policy']=='bind:0' and lane['exit_code']==0 and lane['ended_utc']
cleanup=json.loads((raw/'final-cleanup.json').read_bytes())
assert cleanup['subreaper'] is True and cleanup['survivors']=={}
if phase=='holdout':
 exporter=controls/'lanl-export-cpu-model-validation-a3.py'
 expected='2d59a2d5f6ce54d4692fc962dbc9e38dab4f86076f1873ab78a1484522c681f6'
 args=['holdout',C]
else:
 exporter=controls/'lanl-export-cpu-band-report-a4.py'
 expected='1d1251baeba12c65c40a7a616060e5ff236197ce73f77335534d4a4d83fe32a6'
 args=[C]
assert hashlib.sha256(exporter.read_bytes()).hexdigest()==expected
# The original exporter performs receipt seals, records, clean source and all-free checks again.
os.environ['PYTHONDONTWRITEBYTECODE']='1'
os.execv(sys.executable,[sys.executable,str(exporter),*args])
