"""Prepared context3 contracts, 2026-09-27 ET; no provider calls."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
from decimal import Decimal
import pytest
from swdb import artifacts,rewrite,yamlio
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('context3',HERE/'bfs-provider-context3-20260927.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

def test_actual_three_predecessors_and_request_scope():
 line=json.loads((r.PREP/'lineage-and-budget.json').read_text())
 total=Decimal(0)
 for row in line['ancestors']:
  p=ROOT/'records/proposals'/(row['id']+'.yaml');old=yamlio.load(p)
  assert artifacts.digest(old)==row['record_canonical_sha256'] and artifacts.file_hash(p)==row['record_file_sha256']
  assert old['repair_budget']['used_seconds']==row['used_seconds'];total+=Decimal(str(row['used_seconds']))
  assert not old.get('candidate') and len(old['attempts'])==1 and old['repair_budget']['repairs']==0
 assert float(total)==r.PREVIOUS_SECONDS==767.2889378825203
 assert int(Decimal(1632)-Decimal(str(line['budget']['context2_used_seconds'])))==r.CONFIG['total_seconds']==1031
 expected=copy.deepcopy(old['request']);expected['id']=r.RID
 expected['parameters']['predecessor_proposal']=r.PREVIOUS_ID
 expected['parameters']['prompt_projection']='omit_unselected_strategy_catalog.v1'
 assert expected==json.loads((r.PREP/'upstream-annotated-context3.proposal.json').read_text())

def test_actual_prompt_projection_and_exact_pins():
 raw=(HERE.parent/'provider-context2/prepared/upstream-annotated-context2.prompt.txt').read_text();task=json.loads(raw[raw.index('{"proposal":'):])
 request=json.loads((r.PREP/'upstream-annotated-context3.proposal.json').read_text())
 source={'artifact':artifacts.identify(ROOT/'apps/gapbs'),'context':task['source_context'],'protections':task['protected_inputs']}
 actual=rewrite.prompt_for(request,source,task['profile_package']).encode()
 assert actual==(r.PREP/'upstream-annotated-context3.prompt.txt').read_bytes()
 new=json.loads(actual[actual.index(b'{"proposal":'):]);projection=new['prompt_projection']
 assert len(projection['omitted_strategy_matches'])==130 and not new['profile_package_context']['strategies']
 assert projection['full_package']['record_sha256']==artifacts.digest(task['profile_package'])
 for row in projection['omitted_strategy_matches']:assert row['sha256']==artifacts.digest(task['profile_package']['strategies'][row['index']])
 for key in ('source_files','source_context','protected_inputs'):assert new[key]==task[key]
 for key,suffix in [('PROMPT','prompt.txt'),('REQUEST','proposal.json'),('CONFIG','provider.json')]:assert r.sha(r.PREP/('upstream-annotated-context3.'+suffix))==getattr(r,key+'_SHA')
 assert r.sha(r.PREP/'lineage-and-budget.json')==r.LINEAGE_SHA
 compile(r.PREFLIGHT,'preflight','exec')

def test_exact_git_runtime_manifest_and_single_submit():
 manifest=json.loads(r.RUNTIME_MANIFEST.read_text());assert r.sha(r.RUNTIME_MANIFEST)==r.RUNTIME_MANIFEST_SHA
 names=subprocess.check_output(['git','ls-tree','-r','--name-only',r.SUP_COMMIT],cwd=ROOT,text=True).splitlines()
 expected={p for p in names if any(p==v or p.startswith(v+'/') for v in manifest['runtime_paths'])}
 assert set(manifest['files'])==expected and len(expected)==376
 for p in expected:
  raw=subprocess.check_output(['git','show',r.SUP_COMMIT+':'+p],cwd=ROOT)
  assert manifest['files'][p]=={'bytes':len(raw),'sha256':r.hashlib.sha256(raw).hexdigest()}
 tree=ast.parse((HERE/'bfs-provider-context3-20260927.py').read_text())
 cmds=[x.args[1].value for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='public' and len(x.args)>1 and isinstance(x.args[1],ast.Constant)]
 assert cmds.count('submit')==1 and not {'repair','evaluate','build'}&set(cmds)
 assert r.BOUNDS['outer_seconds']==750 and r.BOUNDS['cleanup_seconds']==30 and r.CONFIG['timeout_s']==600 and r.CONFIG['budget_usd']==10

@pytest.mark.parametrize('bad',[True,None,-1,float('nan'),float('inf'),1031.01])
def test_invalid_debit_rejected(bad):
 with pytest.raises(ValueError):r.debit(bad)

def test_failed_provider_does_not_parse_stdout_and_unknown_cost(tmp_path):
 p=tmp_path/'missing'
 assert r.provider_reporting({'state':'failed'},p)['reported_cost_usd'] is None
 p.write_text('')
 assert r.provider_reporting({'state':'completed'},p)['reported_cost_usd'] is None
 p.write_text('{"total_cost_usd":0.25,"usage":{"input_tokens":12}}')
 assert r.provider_reporting({'state':'completed'},p)['reported_cost_usd']==0.25
 assert r.debit(600)['remaining_provider_seconds']==431
