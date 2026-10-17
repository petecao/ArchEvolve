"""2026-10-16 ET. Read-only source review; no actual observer or project import."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys

HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent

def audit(event,args):
    if event.startswith(('subprocess.','socket.','ctypes.','os.exec','os.spawn','os.fork','os.posix_spawn')) or event=='os.system':
        raise RuntimeError('independent source review forbids children/native/network')
    if event=='import' and str(args[0]).split('.')[0]=='swdb':raise RuntimeError('no installed project import')
sys.addaudithook(audit)

def obj(path):return json.loads(path.read_bytes())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pin(path):
    raw=path.read_bytes();return dict(path=str(path),bytes=len(raw),sha256=sha(raw))
def write(name,value):(HERE/name).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')

ingress=WHOLE/'memory-normalized-ingress-v3';envelope=WHOLE/'memory-unit-envelope-v2'
packets=[ingress/'source-packet-v3.json',envelope/'source-packet-v2.json']
expected=('4563434cedfabd310b8846bb692b82b24ba37d01562b6d816f38437f1a453fcb','cb552c8c')
rows=[]
for packet,identity in zip(packets,expected):
    assert sha(packet.read_bytes()).startswith(identity)
    selected=obj(packet)
    for row in selected['files']+selected['basis']:
        assert pin(Path(row['path']))==row;rows.append(row)

inverses=[]
for relative,current in [('exact-envelope-inverse-v2.json','linux_memory_observation_envelope_v2.py')]:
    selected=obj(envelope/relative);raw=(envelope/current).read_bytes();text=raw.decode()
    for edit in reversed(selected['replacements']):
        assert text.count(edit['new'])==edit['count'];text=text.replace(edit['new'],edit['old'])
    assert text.encode()==Path(selected['basis']['path']).read_bytes()
    inverses.append(dict(current=pin(envelope/current),basis=selected['basis'],exact=True))
for relative,selected in obj(ingress/'exact-inverses-v3.json')['files'].items():
    text=(ingress/relative).read_text()
    for edit in reversed(selected['replacements']):
        assert text.count(edit['new'])==edit['count'];text=text.replace(edit['new'],edit['old'])
    assert text.encode()==Path(selected['basis']['path']).read_bytes()
    inverses.append(dict(current=pin(ingress/relative),basis=selected['basis'],exact=True))

builder=obj(envelope/'builder-inverse-v2.json');basis=Path(builder['basis']);current=envelope/'prepare_envelope_v2.py'
text=basis.read_text()
for edit in builder['replacements']:
    assert text.count(edit['old'])==edit['count'];text=text.replace(edit['old'],edit['new'])
assert text.encode()==current.read_bytes()
reverse=current.read_text();bad=[]
for index,edit in reversed(list(enumerate(builder['replacements']))):
    if reverse.count(edit['new'])!=edit['count']:bad.append(dict(index=index,new=edit['new'],advertised=edit['count'],observed=reverse.count(edit['new'])))
    reverse=reverse.replace(edit['new'],edit['old'])
assert reverse.encode()!=basis.read_bytes() and len(bad)==2
# Independently supply a checked nonoverlapping inverse without editing V2.
old=basis.read_bytes().splitlines(keepends=True);new=current.read_bytes().splitlines(keepends=True)
edits=[]
for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new,autojunk=False).get_opcodes():
    if tag!='equal':edits.append(dict(start=sum(map(len,new[:c])),end=sum(map(len,new[:d])),
        current=b''.join(new[c:d]).decode(),basis=b''.join(old[a:b]).decode()))
reconstructed=current.read_bytes();previous=len(reconstructed)
for edit in reversed(edits):
    assert edit['end']<=previous and reconstructed[edit['start']:edit['end']]==edit['current'].encode()
    reconstructed=reconstructed[:edit['start']]+edit['basis'].encode()+reconstructed[edit['end']:];previous=edit['start']
assert reconstructed==basis.read_bytes()
write('independent-builder-offset-inverse.json',dict(date='2026-10-16 ET',basis=pin(basis),current=pin(current),
    direction='replace current byte spans descending to reconstruct basis',edits=edits,exact_reconstruction=True,
    frozen_author_inverse_remains_invalid=True))

manifest=obj(ingress/'observer/fixed-memory-modules-v2.json');modules=ingress/'observer/modules'
policy=obj(envelope/'envelope-policy-v2.json');observer_policy=obj(envelope/'observation-policy-v1.json');command=obj(envelope/'command-v2.json')
assert len(manifest['modules'])==15 and len(observer_policy['controls'])==18
for row in manifest['modules']:
    selected=pin(modules/row['file']);assert (selected['bytes'],selected['sha256'])==(row['bytes'],row['sha256'])
    assert observer_policy['controls'][row['file']]['bytes']==row['bytes']
    assert observer_policy['controls'][row['file']]['sha256']==row['sha256']
for name in ('compiler_unit_adapter_v3.py','compiler_unit_adapter_v4.py','memory_normalized_capture_ingress_v1.py','memory_normalized_compiler_adapter_v1.py'):
    assert (modules/name).read_bytes()==(WHOLE/'production-union-v1/proposed/swdb/_dx100_whole'/name).read_bytes()
assert observer_policy['capture']['prepared'] is None and policy['node'] is None and policy['guard_files'] is None
assert command['actual_executed'] is False and command['root_metadata_complete'] is False
assert obj(envelope/'root-argv-inert-v2.json')==command['argv']
assert set(command['stage_sources'])==set(policy['controls']) and len(policy['controls'])==36
for name,row in command['stage_sources'].items():
    assert pin(Path(row['path']))==row
    assert (row['bytes'],row['sha256'])==(policy['controls'][name]['bytes'],policy['controls'][name]['sha256'])
assert sum(row['bytes'] for row in policy['controls'].values())+(envelope/'envelope-policy-v2.json').stat().st_size==736053
assert policy['budgets']==dict(whole_seconds=1200,entry_seconds=1180,rss_bytes=4294967296,total_bytes=268435456,file_bytes=4194304,control_bytes=1048576)
assert policy['disk_floor_bytes']==21474836480
first=obj(WHOLE/'normalized-unit-envelope-v5/command-v5.json')
for name in ('root_launcher','guard','root_launch_requirements'):assert command[name]==first[name]
memory_runtime=obj(WHOLE/'compiler-memory-capture-v1/linux_memory_capture_policy_v1.json')
first_runtime=obj(WHOLE/'compiler-capture-v10/linux_compiler_capture_policy_v10.json')
runtime_fields=('python','path','home','runtime_files','python_surface_binding','startup_roles','linux_header_surfaces','native_runtime')
for name in runtime_fields:assert memory_runtime[name]==first_runtime[name]
stale=obj(ingress/'observer-staging-plan-v3.json');selected=obj(ingress/'observer/observation-policy-template-v2.json')
missing=sorted(set(selected['controls'])-set(stale['controls']));obsolete=sorted(set(stale['controls'])-set(selected['controls']))
changed=sorted(name for name in set(selected['controls'])&set(stale['controls'])
    if (selected['controls'][name]['bytes'],selected['controls'][name]['sha256'])!=(stale['controls'][name]['bytes'],stale['controls'][name]['sha256']))
assert len(stale['controls'])==17 and len(missing)==2 and len(obsolete)==1 and len(changed)==4

logs=[];counts=[]
for name,count in [('ingress-semantic-controls.log',5),('envelope-controls.log',13),('real-staging-controls.log',2),('root-environment-controls.log',5)]:
    raw=(HERE/name).read_text();assert re.search(r'Ran '+str(count)+r' tests? in ',raw) and raw.rstrip().endswith('OK')
    logs.append(pin(HERE/name));counts.append(count)
receipt=dict(schema='independent-memory-observer-source-spec-review-1',date='2026-10-16 ET',verdict='HOLD_METADATA_CORRECTION',
    packets=[pin(path) for path in packets],packet_file_and_basis_pin_occurrences=len(rows),
    findings=[dict(id='builder-inverse-overlap',file=str(envelope/'builder-inverse-v2.json'),
        boundary='author inverse metadata only; exact current builder behavior is reconstructible',bad_reverse_counts=bad,
        ordered_forward_reconstruction_exact=True,independent_nonoverlapping_inverse=pin(HERE/'independent-builder-offset-inverse.json')),
        dict(id='stale-staging-plan',file=str(ingress/'observer-staging-plan-v3.json'),advertised_controls=17,required_controls=18,
            missing=missing,obsolete=obsolete,stale_hashes=changed,stale_policy=stale['policy'],
            actual_envelope_stage_sources_and_policy_are_correct=True)],
    source_observer_semantic_or_resource_blocker_found=False,exact_source_inverses=inverses,exact_union_modules=4,
    verified=['distinct physical generic775ab2ec and semanticb5bd7293 readers; explicit consumer identity and before/after pin gates',
        'complete18 inner controls/15 fixed modules;36 flat payloads plus policy;736053B',
        'G642 successful four-phase observation/source55b9/genuine normalized memory transport remain separate from first3148 and V10 refusal',
        'whole original TU/40 calls/three12-14-14 roots and pending body/CPU/lifetime/mapping/receiver gates preserved',
        'exact inherited Linux runtime/startup/source/4GiB1200s1180s/256MiB4MiB1MiB/20GiB/finalization logic',
        'prepared/node/guard null, root_metadata_complete false and actual_executed false; argv remains inert'],
    pure_tests=dict(count=sum(counts),failures=0,logs=logs,no_child_native_network_audit=True),
    execution_boundary=dict(observer_main=False,full_actual_TU_consumed=False,project_import=False,compiler_native_verifier_SSH_Git=False),
    pending=['version metadata correction with root-selected lane/guard and exact filled policy/command pins',
        'fresh root runtime/source/reader/lane preflight and once-only actual admission',
        'actual complete DOM/resource/source preparation; no inference from pure controls',
        'owned ordinary mapping/body CPU lifetime/receiver/draw and public proof acceptance remain separate'])
write('independent-memory-observer-source-spec-review-20261016.json',receipt)
print(json.dumps(dict(receipt=pin(HERE/'independent-memory-observer-source-spec-review-20261016.json'),verdict=receipt['verdict'],pure_tests=sum(counts),pins=len(rows)),sort_keys=True))
