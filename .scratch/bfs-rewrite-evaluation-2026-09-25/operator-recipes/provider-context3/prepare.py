"""Regenerate prospective context3 from retained evidence; 2026-09-27 ET. Run at repo root. No execution or transfers."""
import copy,hashlib,json,subprocess,sys
from pathlib import Path
from decimal import Decimal
root=Path.cwd();sys.path.insert(0,str(root))
from swdb import yamlio,artifacts,rewrite
base=root/'.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes';old=base/'provider-context2';out=base/'provider-context3';prep=out/'prepared';prep.mkdir(parents=True,exist_ok=True)
commit='5750522705dd1f76d56382779427d2dbb48252b9';runtime='/data1/yanruj/EvolveSWDB_provider_context3_runtime_20260927_a1'
id0='bfs-campaign-preparation-20260925-a1.upstream-annotated';ids=[id0,id0+'-context1',id0+'-context2'];newid=id0+'-context3'
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(b):return hashlib.sha256(b).hexdigest()
records=[yamlio.load(root/'records/proposals'/(i+'.yaml')) for i in ids]
used=[Decimal(str(r['repair_budget']['used_seconds'])) for r in records]
assert used==list(map(Decimal,['62.419636563397944','104.55376222543418','600.3155390936881']))
assert [r['outcome']['state'] for r in records]==['unresolved','unresolved','failed']
assert all(len(r['attempts'])==1 and not r.get('candidate') and r['repair_budget']['repairs']==0 for r in records)
prior=records[-1];req=copy.deepcopy(prior['request']);req['id']=newid;req['parameters']['predecessor_proposal']=ids[-1];req['parameters']['prompt_projection']='omit_unselected_strategy_catalog.v1'
assert prior['request']==json.loads((old/'prepared/upstream-annotated-context2.proposal.json').read_text())
config=json.loads((old/'prepared/upstream-annotated-context2.provider.json').read_text());config['total_seconds']=1031
budget=json.loads((old/'prepared/budget.json').read_text());budget.update(context2_used_seconds=float(used[-1]),context2_floor_allowance_seconds=1632,cumulative_used_seconds=float(sum(used)),remaining_after_prior_floor_seconds=float(Decimal(1632)-used[-1]),next_allowance_seconds=1031,third_discarded_fraction_seconds=str(Decimal(1632)-used[-1]-1031),budget_policy='Fresh single submission, not a repair or retry of a closed job. All predecessor charges and floor losses retained. Context3 and any later eligible build/correctness repairs share 1031 seconds; 600 seconds and USD 10 per call. Unknown historical USD cost remains unknown.')
raw=(old/'prepared/upstream-annotated-context2.prompt.txt').read_text();task=json.loads(raw[raw.index('{"proposal":'):]);source={'artifact':artifacts.identify(root/'apps/gapbs'),'context':task['source_context'],'protections':task['protected_inputs']};prompt=rewrite.prompt_for(req,source,task['profile_package']);projection=json.loads(prompt[prompt.index('{"proposal":'):])['prompt_projection']
for suffix,value in [('proposal.json',req),('provider.json',config)]:dump(prep/('upstream-annotated-context3.'+suffix),value)
(prep/'upstream-annotated-context3.prompt.txt').write_text(prompt);dump(prep/'budget.json',budget)
line=json.loads((old/'prepared/lineage-and-budget.json').read_text());line.update(id=newid,budget=budget)
line['ancestors']=[{'id':r['id'],'record_canonical_sha256':artifacts.digest(r),'record_file_sha256':sha((root/'records/proposals'/(r['id']+'.yaml')).read_bytes()),'state':r['outcome']['state'],'used_seconds':float(u),'attempts':1,'candidate':None,'repairs':0} for r,u in zip(records,used)]
line['predecessor']={'id':ids[-1],'record_canonical_sha256':artifacts.digest(prior),'git_commit':'5ab428ad62f0b55816e185a37c4196cfecc56020','record':{'path':'/data/yanruj/EvolveSWDB_runs/bfs-provider-context2-20260927-a1/record-view/records/proposals/'+ids[-1]+'.yaml','bytes':133569,'sha256':sha((root/'records/proposals'/(ids[-1]+'.yaml')).read_bytes())},'original_envelope':{'path':'/data1/yanruj/EvolveSWDB_provider_context2_operator_20260927_a1/.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/provider-context2/prepared/upstream-annotated-context2.proposal.json','bytes':123401,'sha256':sha((old/'prepared/upstream-annotated-context2.proposal.json').read_bytes())},'provider_receipt':{'path':'/data/yanruj/EvolveSWDB_runs/bfs-provider-context2-20260927-a1/provider/'+ids[-1]+'/provider-1/provider.json','bytes':1163,'sha256':'f2bd0e1621b74c12e93d6d94315c9bfeb9e414bc3d10bffcc2bc511241077d12'}}
line['supplement']={'additive_parameters':['prompt_projection'],'updated_parameters':['predecessor_proposal'],'prompt':{'bytes':len(prompt.encode()),'sha256':sha(prompt.encode())},'projection':projection};dump(prep/'lineage-and-budget.json',line)
manifest=json.loads((old/'bfs-provider-context2-runtime-20260926.json').read_text());manifest.update(root=runtime,commit=commit);manifest['files']={}
rows=subprocess.check_output(['git','ls-tree','-r','--name-only',commit],text=True).splitlines();manifest['root_entries']=sorted({x.split('/')[0] for x in rows})
for p in rows:
 if any(p==v or p.startswith(v+'/') for v in manifest['runtime_paths']):
  b=subprocess.check_output(['git','show',commit+':'+p]);manifest['files'][p]={'sha256':sha(b),'bytes':len(b)}
mp=out/'bfs-provider-context3-runtime-20260927.json';dump(mp,manifest)
s=(old/'bfs-provider-context2-20260927.py').read_text()
s=s.replace('def debit(', 'def provider_reporting(meta, stdout):\n    """Optional usage telemetry cannot replace the canonical proposal outcome."""\n    unavailable = {\'reported_cost_usd\': None, \'usage\': None,\n                   \'provider_output_reporting\': {\'state\': \'unavailable\', \'provider_state\': meta.get(\'state\')}}\n    if meta.get(\'state\') != \'completed\':\n        return unavailable\n    try:\n        with stdout.open(\'rb\') as stream:\n            raw = stream.read(10 * 1024**2 + 1)\n        if len(raw) > 10 * 1024**2:\n            raise ValueError(\'provider telemetry exceeds retained output bound\')\n        value = json.loads(raw)\n        if not isinstance(value, dict):\n            raise ValueError(\'provider telemetry is not a JSON object\')\n    except (OSError, ValueError) as exc:\n        unavailable[\'provider_output_reporting\'][\'reason\'] = type(exc).__name__\n        return unavailable\n    return {\'reported_cost_usd\': value.get(\'total_cost_usd\'), \'usage\': value.get(\'usage\'),\n            \'provider_output_reporting\': {\'state\': \'available\', \'provider_state\': meta[\'state\']}}\n\n\n'+'def debit(',1)
s=s.replace("            provider_result=json.loads((meta_path.parent/'stdout.txt').read_text())\n            receipt['reported_cost_usd']=provider_result.get('total_cost_usd');receipt['usage']=provider_result.get('usage')","            receipt.update(provider_reporting(meta, meta_path.parent/'stdout.txt'))")
s=s.replace('context2','context3')
s=s.replace("PREVIOUS_ID = '"+newid+"'","PREVIOUS_ID = '"+ids[-1]+"'") # original was context1
s=s.replace("PREVIOUS_ID = '"+ids[1]+"'","PREVIOUS_ID = '"+ids[-1]+"'")
s=s.replace('/data1/yanruj/EvolveSWDB_supervision_recovery_runtime_20260927_a1',runtime).replace('8cbfee600f23416a8e9578fa8d3ce3f0e19fced8',commit).replace('1b2250670077a2f48c7dd8b28333685c4f757982','5ab428ad62f0b55816e185a37c4196cfecc56020').replace('bfs-provider-context3-runtime-20260926.json',mp.name).replace('166.97339878883213',str(float(sum(used)))).replace('1632','1031')
for key,file in [('RUNTIME_MANIFEST_SHA',mp),('PROMPT_SHA',prep/'upstream-annotated-context3.prompt.txt'),('CONFIG_SHA',prep/'upstream-annotated-context3.provider.json'),('REQUEST_SHA',prep/'upstream-annotated-context3.proposal.json'),('LINEAGE_SHA',prep/'lineage-and-budget.json')]:
 import re
 s=re.sub(r"^"+key+r" = '[^']+'",key+" = '"+sha(file.read_bytes())+"'",s,flags=re.M)
s=s.replace("'context1_provider_used_seconds':104.55376222543418,","'context1_provider_used_seconds':104.55376222543418,\n            'context2_provider_used_seconds':600.3155390936881,")
a=s.index("assert old['outcome']['state']=='unresolved'");b=s.index("clarification=r['parameters']",a)
s=s[:a]+'''assert old['outcome']['state']=='failed' and len(old['attempts'])==1 and not old.get('candidate')
assert old['repair_budget']['used_seconds']==line['budget']['context2_used_seconds']
for ancestor in line['ancestors']:
 record=store.get(ancestor['id'],'proposal')
 assert artifacts.digest(record)==ancestor['record_canonical_sha256']
 assert artifacts.file_hash(Path(sys.argv[2])/'proposals'/(ancestor['id']+'.yaml'))==ancestor['record_file_sha256']
 assert record['outcome']['state']==ancestor['state'] and record['repair_budget']['used_seconds']==ancestor['used_seconds']
 assert len(record['attempts'])==1 and record['repair_budget']['repairs']==0 and not record.get('candidate')
original=json.loads(Path(line['predecessor']['original_envelope']['path']).read_text())
assert original==old['request']
expected=json.loads(json.dumps(original));expected['id']=r['id']
expected['parameters']['predecessor_proposal']=old['id']
expected['parameters']['prompt_projection']='omit_unselected_strategy_catalog.v1'
assert r==expected
''' +s[b:]
s=s.replace('len(prompt)==523066','len(prompt)=='+str(len(prompt.encode())))
s=s.replace("assert line['budget']['initial_used_seconds']==62.419636563397944","assert line['budget']['initial_used_seconds']==62.419636563397944\nassert line['budget']['context2_used_seconds']==600.3155390936881\nassert line['budget']['cumulative_used_seconds']==767.2889378825203")
(out/'bfs-provider-context3-20260927.py').write_text(s)
(out/'bfs-provider-context3-launch-20260927.sh').write_text((old/'bfs-provider-context2-launch-20260927.sh').read_text().replace('context2','context3'))
print(json.dumps({'runtime_files':len(manifest['files']),'prompt_bytes':len(prompt.encode()),'prompt_sha':sha(prompt.encode()),'output':str(out)}))
