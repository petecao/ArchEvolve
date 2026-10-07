import ast
import copy
import hashlib
import json
from pathlib import Path

LOCAL=Path('/private/tmp/lanl14-pr-final-local-runner-20261007-a2.py')
FINAL=Path('/private/tmp/lanl14_final_reports_caps_a2.py')
ENVELOPE=Path('/private/tmp/lanl14-pr-final-local-envelope-20261007-a2.py')
NEW_LOCAL=Path('/private/tmp/lanl14-pr-final-local-runner-20261007-a3.py')
NEW_FINAL=Path('/private/tmp/lanl14_final_reports_freeze_caps_a3.py')
NEW_ENVELOPE=Path('/private/tmp/lanl14-pr-final-local-envelope-20261007-a3.py')
EXPORTER=Path('/private/tmp/lanl14_final_export_caps_a2.py')
BASE={LOCAL:'fa99126eb9735e7aac9ab4f8dbfb1adbfabab40be8b6c9067e6904c95d7a806b',FINAL:'0c4eeb817df34d513819302c1dd7dbd469bab58eba0cfa008748596d8ff77158',ENVELOPE:'134de6899dd6c530f815defb7a4a31ad3159620310f8edf2dcdabed759682df2',EXPORTER:'d8e97dc6a1153c30c3c6a0e329cc091ded63d3627f8dd905de7470166b60c833'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
for path,pin in BASE.items():assert sha(path)==pin,str(path)

def constants(node):return [n.value for n in ast.walk(node) if isinstance(n,ast.Constant)]
def edits_for(path):
 tree=ast.parse(path.read_text());edits=[]
 for node in ast.walk(tree):
  if path==LOCAL and isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='run' and isinstance(node.args[0],ast.Constant) and node.args[0].value=='freeze':
   assert 'freeze-protocol' in constants(node.args[1]) and node.args[-1].value==1400;edits.append((node.args[-1],1800,'protocol freeze child only'))
  if path==FINAL:
   if isinstance(node,ast.Dict):
    for key,value in zip(node.keys,node.values):
     if isinstance(key,ast.Constant) and key.value=='freeze_s':assert value.value==1400;edits.append((value,1800,'manifest protocol freeze budget'))
     if isinstance(key,ast.Constant) and key.value=='outer_s':assert value.value==33000;edits.append((value,36600,'manifest outer bound: nine freeze deltas'))
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='invoke' and 'freeze-protocol' in constants(node.args[0]):
    assert node.args[-1].value==1400;edits.append((node.args[-1],1800,'protocol freeze child only'))
   if isinstance(node,ast.List) and node.elts and isinstance(node.elts[0],ast.Constant) and node.elts[0].value=='timeout':
    timeout=node.elts[3];assert timeout.value=='33000s';edits.append((timeout,'36600s','wrapper outer bound'))
 assert len(edits)==(1 if path==LOCAL else 4)
 return tree,edits

def write_revision(original,revised,tree,edits):
 assert not revised.exists(),str(revised)
 text=original.read_text();line_offsets=[0]
 for line in text.splitlines(keepends=True):line_offsets.append(line_offsets[-1]+len(line))
 replacements=[]
 for node,value,reason in edits:
  start=line_offsets[node.lineno-1]+node.col_offset;end=line_offsets[node.end_lineno-1]+node.end_col_offset
  old=text[start:end];new=old.replace('4500-second','4900-second',1) if reason=='outer-bound documentation delta' else repr(value)
  replacements.append({'start':start,'end':end,'old':old,'new':new,'old_value':node.value,'new_value':value,'reason':reason,'line':node.lineno})
 assert len({r['start'] for r in replacements})==len(replacements)
 output=text
 for row in sorted(replacements,key=lambda r:r['start'],reverse=True):output=output[:row['start']]+row['new']+output[row['end']:]
 revised.write_text(output)
 reversed_text=output;delta=0;reversal=[]
 for row in sorted(replacements,key=lambda r:r['start']):
  start=row['start']+delta;reversal.append((start,start+len(row['new']),row['old'],row['new']));delta+=len(row['new'])-(row['end']-row['start'])
 for start,end,old,new in reversed(reversal):assert reversed_text[start:end]==new;reversed_text=reversed_text[:start]+old+reversed_text[end:]
 assert reversed_text==text and hashlib.sha256(reversed_text.encode()).hexdigest()==sha(original),'Administrative reversal failed byte equality'
 expected=copy.deepcopy(tree)
 selected={(node.lineno,node.col_offset):value for node,value,_ in edits}
 class ExplicitAdminOnly(ast.NodeTransformer):
  def visit_Constant(self,node):
   if (node.lineno,node.col_offset) in selected:node.value=selected[(node.lineno,node.col_offset)]
   return node
 expected=ExplicitAdminOnly().visit(expected);actual=ast.parse(output)
 assert ast.dump(expected,include_attributes=False)==ast.dump(actual,include_attributes=False),'Unapproved AST field changed'
 # File paths are not inputs to parsed AST equality or explicit byte reversal.
 result={'original':str(original),'original_sha256':sha(original),'revision':str(revised),'revision_sha256':sha(revised),'explicit_administrative_reversal_byte_identical':True,'source_path_independent_ast_equality':True,'approved_edits':[{'line':r['line'],'from':r['old_value'],'to':r['new_value'],'reason':r['reason']} for r in sorted(replacements,key=lambda r:r['start'])]}
 return result

proofs=[]
for original,revised in ((LOCAL,NEW_LOCAL),(FINAL,NEW_FINAL)):
 tree,edits=edits_for(original);proofs.append(write_revision(original,revised,tree,edits))
# Only envelope deadline/documentation and the explicit helper pathname/hash pins change.
tree=ast.parse(ENVELOPE.read_text());edits=[]
for node in ast.walk(tree):
 if isinstance(node,ast.Constant) and isinstance(node.value,str):
  if node.value==str(LOCAL):edits.append((node,str(NEW_LOCAL),'distinct cap-only helper path'))
  elif node.value==BASE[LOCAL]:edits.append((node,sha(NEW_LOCAL),'exact revised helper SHA pin'))
  elif node.value.startswith('4500-second local metadata envelope'):
   edits.append((node,'4900'+node.value[4:],'outer-bound documentation delta'))
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='setitimer' and len(node.args)==2 and isinstance(node.args[1],ast.Constant) and node.args[1].value==4500:
  edits.append((node.args[1],4900,'local envelope delta400'))
assert len(edits)==4
proofs.append(write_revision(ENVELOPE,NEW_ENVELOPE,tree,edits))
assert sha(EXPORTER)==BASE[EXPORTER]
proof={'format':'swdb.lanl14-protocol-freeze-only-cap-proof.v1','updated':'2026-10-07 ET','scope':'Unexecuted administrative revisions only. Preserve science/C/F6, source/count/target/input/ROI/requests/allowlist/native900 and all custody/cleanup rules. Raw IDs/paths and every other original byte are restored by explicit selected administrative reversal; no broad literal replacement.',
 'source_commit':'97023167a1fa42acf903c365100ef7ae4e6ef64c','generic_estimator_sha256':'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3','observed_model_freeze_wall_s':1266.086,
 'helpers':proofs,'preserved_exporter':{'path':str(EXPORTER),'sha256':sha(EXPORTER),'reason':'Dynamic helper/manifest hashes; no static freeze/outer fields. Validation1400 unchanged.'},
 'local_caps':{'freeze_s':1800,'estimate_s':1400,'checker_s':1000,'outer_s':4900,'stage_sum_s':4200,'reserve_s':700},
 'nine_caps':{'freeze_s':1800,'estimate_s':1400,'validate_s':1400,'report_s':1000,'outer_s':36600,'stage_sum_s':32600,'reserve_s':4000},'actual_execution':False,'native_execution':0,'provider_calls':0,'remote_actions':0}
proof['identity_sha256']=digest(proof);out=Path('/private/tmp/lanl14-protocol-freeze-only-cap-proof-20261007-a3.json');out.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
