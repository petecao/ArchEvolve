"""2026-10-09 ET: local actual metadata author; no remote execution or default approval."""
import json,hashlib,os,secrets,datetime,sys
from pathlib import Path
SHA='be2f68c21a72b4de5deee05f17f48a8cd09342cf3a6e7e17280ff72414dc3fd4'
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def save(p,b):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
peer=Path(sys.argv[1]);assert peer==Path('/private/tmp/lanl17-finalize-completion-originals-independent-semantic-review-20261009-a5-r1.json')
peerraw=peer.read_bytes();assert len(peerraw)==65805 and digest(peerraw)=='4c42d7e1657c7ff65541e211d38c9a630bcd25606161c07a871fd2359c8bec86'
pv=json.loads(peerraw);assert pv['format']=='swdb.lanl17-finalize-completion-independent-semantic-review.v1' and pv['verdict']=='PASS_ORIGINAL_FINALIZE_COMPLETION_METADATA_WITH_SCIENTIFIC_GATES' and pv['scientific_admission'] is False
expected_packet='/private/tmp/lanl17-finalize-completion-capture-20261009-0000-a5-a1/completion-original.json'
packet_pins=[v for v in pv['reviewed_local_original_pins_all9stat'] if v['path']==expected_packet]
assert len(packet_pins)==1 and packet_pins[0]['bytes']==744321 and packet_pins[0]['sha256']=='34fd38e927a95a916a80247748e9c3cc776e4676e722b26d88c4ce2e9758716f'
root=Path('/private/tmp/lanl17-finalize-completion-root-semantic-review-20261009-0003-a5.json');rr=root.read_bytes();assert digest(rr)=='8a7e36dfb1fde14fc69f48dcd5d702d43a0fbcfebe7ec3f6eba606689b6f5f2c'
packet=Path('/private/tmp/lanl17-finalize-completion-capture-20261009-0000-a5-a1/completion-original.json');raw=packet.read_bytes();assert len(raw)==744321 and digest(raw)=='34fd38e927a95a916a80247748e9c3cc776e4676e722b26d88c4ce2e9758716f';d=json.loads(raw);assert d['completion_metadata_ready'] is True
pins={k:{x:y for x,y in v.items() if x!='base64'} for k,v in d['files'].items()};pins.update(d['metadata_only_original_pins'])
B='/data1/yanruj';RAW='/data/yanruj/EvolveSWDB_runs/lanl17-actual-campaigns-20261007-a5';FINAL='/data/yanruj/EvolveSWDB_runs/lanl17-metadata-finalize-20261007-a5';ER=B+'/ArchEvolve-lanl17-actual-report-evidence-20261007-a5'
roles={'guard_preregistration':FINAL+'/preregistration.json','supervisor_receipt':FINAL+'/supervisor-receipt.json','helper_stdout':FINAL+'/helper.stdout','final_export':RAW+'/final-export.json','agreement_receipt':ER+'/swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/17-actual-report-mbit10-20261007-a5.json','manifest_M2':RAW+'/manifest.json','helper_source':B+'/lanl17-control-cleanup60-20261007-a4.py','guard_source':B+'/lanl17-metadata-dispatch-guard-cleanup60-20261007-a4.py','supervisor_source':B+'/lanl17-metadata-supervisor-cleanup60-20261007-a4.py'}
for name in ['validate-extensa-gem5-bfs-20261006-p'+str(i) for i in range(1,5)]+['validate-final-export']:
 for role,suffix in [('argv','argv.json'),('exit','exit-code.txt'),('stdout','stdout'),('stderr','stderr')]:roles[name+':'+role]=RAW+'/'+name+'.'+suffix
originals={k:pins[v] for k,v in roles.items()};assert len(originals)==29 and all(set(v)=={'path','bytes','sha256','stat'} for v in originals.values())
payload={'format':'swdb.lanl17-pre-full-index-host-observation-input.v1','campaign':'extensa-gem5-bfs-20261006-p1','nonce':secrets.token_hex(16),'completion_originals':originals,'expected_ER_commit':d['observations']['ER']['commit'],'fresh_routes':{'inventory_output':B+'/lanl17-p1-full-catalog-inventory-20261009-a5-a1'}}
now=datetime.datetime.now(datetime.timezone.utc);payload['parent_review']={'basis':'explicit_parent_review_of_genuine_completed_FINALIZE_and_next_full_index_metadata_routes','source_sha256':SHA,'payload_sha256':digest(canonical(payload)),'completion_packet_sha256':digest(raw),'completion_root_review_sha256':digest(rr),'completion_peer_review_sha256':digest(peerraw),'actual_completion_originals_reviewed':True,'fixtures':False,'checked_utc':now.isoformat(),'valid_until_utc':(now+datetime.timedelta(seconds=300)).isoformat()}
b=(json.dumps(payload,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();local=Path('/private/tmp/lanl17-p1-pre-full-index-host-input-actual-20261009-a5-a2.json');save(local,b)
action=Path('/private/tmp/lanl17-pre-full-index-host-action-SOURCE-ONLY-draft-r7-20261008-a5.json');ar=action.read_bytes();assert len(ar)==38106 and digest(ar)=='3ebd67b8b1691c45fa40739d95f9d913d30a77b34f750eabb18a628f5ce3dfd7'
c=json.loads(ar)['config_template'];source=Path('/private/tmp/lanl17_pre_full_index_host_observation_20261008_a5_r5.py').read_bytes();assert len(source)==36052 and digest(source)==SHA and c['argv'][4]==source.decode()
remote=B+'/lanl17-p1-pre-full-index-host-input-20261009-a5-a2.json';c['argv'][6]=remote;c['argv'][8]=digest(b)
import base64
c['stage']=[{'path':remote,'bytes':len(b),'sha256':digest(b),'base64':base64.b64encode(b).decode()}]
config=Path('/private/tmp/lanl17-p1-pre-full-index-host-action-actual-20261009-a5-a2.json');cb=(json.dumps(c,sort_keys=True,indent=2,allow_nan=False)+'\n').encode();save(config,cb)
print(json.dumps({'input':str(local),'input_bytes':len(b),'input_sha256':digest(b),'config':str(config),'config_bytes':len(cb),'config_sha256':digest(cb),'review_expires_utc':payload['parent_review']['valid_until_utc'],'source_and_pins_unmodified':True,'remote_stage_only_actual_metadata_input':remote}))
