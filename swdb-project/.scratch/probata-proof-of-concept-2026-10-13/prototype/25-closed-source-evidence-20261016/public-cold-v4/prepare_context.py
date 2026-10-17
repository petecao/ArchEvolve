"""2026-10-16 ET. Local stdlib/read-only Git cold-context author; no raw read."""
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
PROJECT = POC.parents[1]
REPO = PROJECT.parent
PACKET = HERE.parent/'public-controller-v4/inert-1433b8f5-node0'
COMMIT = '1433b8f58baa63538d1e8aa8a33d9ce566826407'


def h(raw): return hashlib.sha256(raw).hexdigest()
def j(value): return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def compact(value): return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def read(path): return json.loads(path.read_bytes())
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':h(raw)}
def git(*args):
    return subprocess.check_output(['/usr/bin/git','--no-optional-locks','--no-replace-objects',
        '-c','core.preloadIndex=false','-c','core.fsmonitor=false','-c','index.threads=1','-C',str(REPO),*args],timeout=180)
def source(relative): return git('show',COMMIT+':swdb-project/'+relative)

def main():
    policy=read(PACKET/'policy.json');command=read(PACKET/'command.json')
    assert policy['source_commit']==COMMIT and command['node']==0
    canonical=HERE.parent/'inert-reviewed-working-source-v3'
    rule=read(canonical/'manifest.json')
    portable=copy.deepcopy(rule)
    portable['source_view']['library_allocator_binding'].pop('certificate_sha256')
    bundle=HERE.parent/'scientific-bundle-v3'
    catalog=read(bundle/'catalog.json')
    assert h((bundle/'catalog.json').read_bytes())=='42100d4ecb63de8718f6d16071f179ba3fb173cd94511730b195106426a1cb60'
    nodes=ast.parse(source('swdb/vector_reallocation_closed_binding.py'))
    historical=ast.literal_eval(next(n.value for n in nodes.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='HISTORICAL_SOURCES' for t in n.targets)))
    components=[]
    for c in catalog['components']:
        targets=[{k:t[k] for k in ('id','goal','kind','statement','input_sha256','observation')} for t in c['targets']]
        components.append({'id':c['id'],'targets':targets,'historical_identity':c['historical_identity'],
            'historical_source_commit':historical[c['id']],'historical_identity_preserved':True,
            'accepted_decision':c['accepted_decision'],'complete_cold_context':c['context'],
            'cold_evidence':c['cold_evidence'],'accepted_subset':c['accepted_subset']})
    # Independently compute the universal checker identity from immutable source.
    setup=ast.parse(source('swdb/proof_setup.py')); names=[]
    for node in setup.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CHECK_SOURCES' for t in node.targets): names=list(ast.literal_eval(node.value))
        elif isinstance(node,ast.AugAssign) and isinstance(node.target,ast.Name) and node.target.id=='CHECK_SOURCES': names+=list(ast.literal_eval(node.value))
    check_names=['swdb/'+n for n in names]+['vocab/proof_failure_classes.yaml','vocab/proof_subject_kinds.yaml']
    check_rows=[{'path':n,'sha256':h(source(n))} for n in check_names]
    setup_sha=h(compact(check_rows))
    rule_identity=rule['checker']
    binding_identity={'id':'vector-closed-scientific-binding-1','sha256':h(j({'source':h(source('swdb/vector_reallocation_closed_binding.py')),
        'source_rule':rule_identity,'reviewed_catalog':h((bundle/'catalog.json').read_bytes())}))}
    route_identity={'id':'vector-closed-source-route-1','sha256':h(j({'source':h(source('swdb/vector_reallocation_closed_route.py')),'scientific_binding':binding_identity}))}
    roots=sorted(policy['source_consumer_trees'])
    tree=git('ls-tree','-r','-l','-z',COMMIT,'--',*['swdb-project/'+n for n in roots])
    consumers=[]
    for line in tree.split(b'\0'):
        if not line:continue
        meta,name=line.decode().split('\t',1);mode,kind,oid,size=meta.split()
        assert mode in ('100644','100755') and kind=='blob'
        relative=name.removeprefix('swdb-project/')
        consumers.append({'relative':relative,'git_blob':oid,'bytes':int(size)})
    assert len(consumers)==len({c['relative'] for c in consumers})
    source_files={name:policy['source_files'][name] for name in policy['source_files']}
    source_rule_files={str(path.relative_to(canonical)):pin(path) for path in canonical.rglob('*') if path.is_file() and path.name!='manifest.json'}
    assert len(source_rule_files)==7
    expected={'created':'2026-10-16 ET','source_commit':COMMIT,'project':command['source'],'raw_root':command['raw_root'],
        'node':0,'entry':pin(PACKET/'entry.py'),'policy':pin(PACKET/'policy.json'),'command':command,
        'source_files':source_files,'consumer_roots':policy['source_consumer_trees'],'consumer_files':consumers,
        'source_rule_portable':portable,'source_rule_files':source_rule_files,'components':components,
        'catalog':pin(bundle/'catalog.json'),'catalog_documents':catalog['documents'],
        'proof_setup_identity':{'version':'1','sha256':setup_sha},'proof_setup_sources':check_rows,
        'source_pins':{'vector_closed_source_rule':rule_identity,'vector_closed_scientific_binding':binding_identity,
            'vector_closed_scientific_bundle':{'id':'vector-closed-scientific-bundle-1','sha256':h((bundle/'catalog.json').read_bytes())},
            'vector_closed_source_route':route_identity},
        'expected_contract':['requires 0 <= n;',r'assigns \nothing;',r'ensures \result == (n > 0 ? 7 : 0);'],
        'compiler_native_proof_requested':False,'source_or_caller_admission':False,
        'prior_failure':'Public V2 all5 before-record method-selection failure and actual V3 lock-race refusal after three records remain preserved. Root reports V4 complete; this observer has not inspected it.'}
    root_observation=POC/'evidence/t25-public-v4-root-observation-20261016t2130z.json'
    observed=read(root_observation)
    assert observed['raw_root']==expected['raw_root']
    lane=observed['actual']['lane.json']['socket_lane']
    assert lane['node']==0 and lane['lease_generation']==619 and lane['ended_utc']=='2026-10-16T21:28:57Z' and lane['exit_code']==0
    expected['root_observation']=pin(root_observation)
    expected['settlement']={'generation':619,'ended_utc':lane['ended_utc'],'metadata_pins':observed['metadata_pins']}
    out=HERE/'expected.json';assert not out.exists();out.write_bytes(j(expected))
    print(json.dumps(pin(out)))

if __name__=='__main__':main()
