"""Prepare parent-approved finite metadata caps only. Updated: 2026-10-07 ET."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path('/private/tmp')
LOCAL=ROOT/'lanl14-pr-final-local-runner-20261007-a3.py'
FINAL=ROOT/'lanl14_final_reports_freeze_caps_a3.py'
ENVELOPE=ROOT/'lanl14-pr-final-local-envelope-20261007-a3.py'
EXPORTER=ROOT/'lanl14_final_export_caps_a2.py'
NEW_LOCAL=ROOT/'lanl14-pr-final-local-runner-catalog-caps-20261007-a4.py'
NEW_FINAL=ROOT/'lanl14_final_reports_catalog_caps_a4.py'
NEW_ENVELOPE=ROOT/'lanl14-pr-final-local-envelope-catalog-caps-20261007-a4.py'
NEW_EXPORTER=ROOT/'lanl14_final_export_catalog_caps_a4.py'
BASE={LOCAL:'0f4bf77738f3df5e39c28308b94dac6fac0f894955f1c7348c1a5f32c42227df',FINAL:'a877644dd08473d8eb91d8ea7fd6eb66adbf2ed82775699bc7026208ff7b9dd4',ENVELOPE:'921ca0d1c37514a69e009cf09df6abfcb3e3f0e96081e15de03ee5456e999ac9',EXPORTER:'d8e97dc6a1153c30c3c6a0e329cc091ded63d3627f8dd905de7470166b60c833'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def constants(node):return [n.value for n in ast.walk(node) if isinstance(n,ast.Constant)]
for path,pin in BASE.items():assert sha(path)==pin,str(path)

def revision(original,revised,tree,edits):
 text=original.read_text();offsets=[0]
 for line in text.splitlines(keepends=True):offsets.append(offsets[-1]+len(line))
 rows=[]
 for node,value,reason in edits:
  start=offsets[node.lineno-1]+node.col_offset;end=offsets[node.end_lineno-1]+node.end_col_offset
  old=text[start:end];new=repr(value)
  rows.append({'start':start,'end':end,'old':old,'new':new,'from':node.value,'to':value,'reason':reason,'line':node.lineno})
 assert len({row['start'] for row in rows})==len(rows)
 output=text
 for row in sorted(rows,key=lambda row:row['start'],reverse=True):output=output[:row['start']]+row['new']+output[row['end']:]
 reversed_text=output;delta=0;reversal=[]
 for row in sorted(rows,key=lambda row:row['start']):
  start=row['start']+delta;reversal.append((start,start+len(row['new']),row['old'],row['new']));delta+=len(row['new'])-(row['end']-row['start'])
 for start,end,old,new in reversed(reversal):assert reversed_text[start:end]==new;reversed_text=reversed_text[:start]+old+reversed_text[end:]
 assert reversed_text==text and hashlib.sha256(reversed_text.encode()).hexdigest()==BASE[original]
 expected=copy.deepcopy(tree);selected={(node.lineno,node.col_offset):value for node,value,_ in edits}
 class AdminOnly(ast.NodeTransformer):
  def visit_Constant(self,node):
   if (node.lineno,node.col_offset) in selected:node.value=selected[(node.lineno,node.col_offset)]
   return node
 expected=AdminOnly().visit(expected)
 assert ast.dump(expected,include_attributes=False)==ast.dump(ast.parse(output),include_attributes=False)
 compile(output,str(revised),'exec')
 if revised.exists():assert revised.read_text()==output,'Existing revision differs; preserve it'
 else:revised.write_text(output)
 return {'original':str(original),'original_sha256':BASE[original],'revision':str(revised),'revision_sha256':sha(revised),'explicit_administrative_reversal_byte_identical':True,'source_path_independent_ast_equality':True,'approved_edits':[{key:row[key] for key in ('line','from','to','reason','start','end','old','new')} for row in sorted(rows,key=lambda row:row['start'])]}

proofs=[]
tree=ast.parse(LOCAL.read_text());edits=[]
local_caps={'freeze':(1800,3600),'estimate':(1400,2400),'checker':(1000,2400)}
for node in ast.walk(tree):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='run' and isinstance(node.args[0],ast.Constant) and node.args[0].value in local_caps:
  old,new=local_caps[node.args[0].value];assert node.args[-1].value==old;edits.append((node.args[-1],new,'local '+node.args[0].value+' metadata deadline'))
assert len(edits)==3
proofs.append(revision(LOCAL,NEW_LOCAL,tree,edits))

tree=ast.parse(FINAL.read_text());edits=[]
limits={'freeze_s':(1800,6000),'estimate_s':(1400,4000),'validate_s':(1400,3600),'report_s':(1000,3600),'outer_s':(36600,108000)}
for node in ast.walk(tree):
 if isinstance(node,ast.Dict):
  for key,value in zip(node.keys,node.values):
   if isinstance(key,ast.Constant) and key.value in limits:
    old,new=limits[key.value];assert isinstance(value,ast.Constant) and value.value==old;edits.append((value,new,'manifest '+key.value))
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='invoke':
  argv=constants(node.args[0]);label=constants(node.args[1]);replacement=None
  if 'freeze-protocol' in argv:replacement=(1800,6000,'public protocol freeze metadata deadline')
  elif 'estimate' in argv:replacement=(1400,4000,'public estimate metadata deadline')
  elif 'validate' in argv:replacement=(1400,3600,'public validation metadata deadline')
  elif label==['nine-report']:replacement=(1000,3600,'public all-nine report metadata deadline')
  if replacement:
   old,new,reason=replacement;assert node.args[-1].value==old;edits.append((node.args[-1],new,reason))
 if isinstance(node,ast.List) and node.elts and isinstance(node.elts[0],ast.Constant) and node.elts[0].value=='timeout':
  deadline=node.elts[3];assert deadline.value=='36600s';edits.append((deadline,'108000s','existing wrapper outer administrative deadline'))
assert len(edits)==11,len(edits)
proofs.append(revision(FINAL,NEW_FINAL,tree,edits))

tree=ast.parse(ENVELOPE.read_text());edits=[]
for node in ast.walk(tree):
 if isinstance(node,ast.Constant) and isinstance(node.value,str):
  if node.value==str(LOCAL):edits.append((node,str(NEW_LOCAL),'distinct revised helper path'))
  elif node.value==BASE[LOCAL]:edits.append((node,sha(NEW_LOCAL),'exact revised helper hash'))
  elif node.value.startswith('4900-second local metadata envelope'):edits.append((node,'10000'+node.value[4:],'envelope bound documentation'))
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='setitimer' and len(node.args)==2 and isinstance(node.args[1],ast.Constant) and node.args[1].value==4900:
  edits.append((node.args[1],10000,'local outer administrative deadline'))
assert len(edits)==4
proofs.append(revision(ENVELOPE,NEW_ENVELOPE,tree,edits))

tree=ast.parse(EXPORTER.read_text());edits=[]
for node in ast.walk(tree):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='wait':
  for keyword in node.keywords:
   if keyword.arg=='timeout':assert keyword.value.value==1400;edits.append((keyword.value,3600,'export public validation metadata deadline'))
assert len(edits)==1
proofs.append(revision(EXPORTER,NEW_EXPORTER,tree,edits))
assert all(sha(path)==pin for path,pin in BASE.items())
proof={'format':'swdb.lanl14-complete-catalog-cap-only-proof.v1','updated':'2026-10-07 ET','scope':'Distinct unexecuted administrative ceilings for complete-catalogue custody. No narrowed catalogue, science/source C/F6/input/count/ROI/thread/target/allowlist/parameter/command/cleanup/lease/provider/native change. Explicit selected administrative reversal restores all old bytes, raw IDs and paths. No broad literal replacement.',
 'preparation_integration':'cbe99ee','source_commit':'f893fed400347ed23d92e917d8bde21b75e5375d','generic_estimator_sha256':'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3','helpers':proofs,
 'local_caps':{'freeze_s':3600,'estimate_s':2400,'checker_s':2400,'outer_s':10000,'stage_sum_s':8400,'reserve_s':1600},
 'nine_caps':{'freeze_s':6000,'estimate_s':4000,'validate_s':3600,'report_s':3600,'outer_s':108000,'stage_sum_s':100800,'reserve_s':7200,'export_validation_s':3600},
 'caps_are_predicted_runtime':False,'future_duration_bound_proven':False,'complete_catalogue_retained':True,'old_a3_controls_unchanged':True,'actual_execution':False,'native_execution':0,'provider_calls':0,'remote_actions':0}
proof['identity_sha256']=digest(proof);out=ROOT/'lanl14-complete-catalog-cap-proof-20261007-a4.json';out.write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'proof':str(out),'identity_sha256':proof['identity_sha256'],'helpers':[{'path':p['revision'],'sha256':p['revision_sha256'],'edits':len(p['approved_edits'])} for p in proofs]},indent=2))
