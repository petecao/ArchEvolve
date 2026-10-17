"""Source-only passive budget successor. Never run actual census or bootstrap."""
import ast
import hashlib
import json
from pathlib import Path
import shlex
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;OLD=WHOLE/'compiler-duplicate-census-v2'
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(name,value):(HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
source=(OLD/'complete_duplicate_census_v2.py').read_text();before="time.monotonic()-started<90,'bounded metadata diagnostic deadline exceeded'";after=before.replace('<90,','<600,')
assert source.count(before)==1;source=source.replace(before,after,1);(HERE/'complete_duplicate_census_v3.py').write_text(source)
assert source.replace(after,before,1)==(OLD/'complete_duplicate_census_v2.py').read_text()
payload=pin(HERE/'complete_duplicate_census_v3.py');boot=(OLD/'readonly_bootstrap_v3.py').read_text();edits=[]
for old,new in [('resource.RLIMIT_CPU, (100, 100)','resource.RLIMIT_CPU, (650, 650)'),('read(22966)',f"read({payload['bytes']+1})"),('len(payload) != 22965',f"len(payload) != {payload['bytes']}"),('d265c49485057cbd43cfd913cfc905683090866174b45d863f22121331d997b3',payload['sha256'])]:
    assert boot.count(old)==1;edits.append({'before':old,'after':new});boot=boot.replace(old,new,1)
(HERE/'readonly_bootstrap_v4.py').write_text(boot)
restored=boot
for e in reversed(edits):assert restored.count(e['after'])==1;restored=restored.replace(e['after'],e['before'],1)
assert restored==(OLD/'readonly_bootstrap_v3.py').read_text()
prior=json.loads((OLD/'complete-census-command-v2.json').read_bytes());command=dict(prior);argv=list(prior['python_argv']);argv[4]=boot
remote=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','660s','/usr/bin/env','-i',*[k+'='+v for k,v in prior['closed_environment'].items()],*argv]
command.update(CPU_seconds=650,internal_wall_seconds=600,outer_timeout_seconds=660,local_transport_timeout_seconds=700,
    bootstrap=pin(HERE/'readonly_bootstrap_v4.py'),stdin=payload,python_argv=argv,remote_argv=remote,remote_shell_command=shlex.join(remote),
    predecessor_command=pin(OLD/'complete-census-command-v2.json'),scope='SOURCE ONLY: V3 passive complete census budget successor; new root admission required')
save('complete-census-command-v3.json',command)
oldtree=ast.parse((OLD/'complete_duplicate_census_v2.py').read_bytes());newtree=ast.parse(source)
old_inspect=next(n for n in oldtree.body if getattr(n,'name',None)=='inspect');new_inspect=next(n for n in newtree.body if getattr(n,'name',None)=='inspect')
replaced=0
for n in ast.walk(new_inspect):
    if isinstance(n,ast.Constant) and type(n.value) is int and n.value==600:n.value=90;replaced+=1
assert replaced==1 and ast.dump(oldtree,include_attributes=False)==ast.dump(newtree,include_attributes=False)
save('budget-v3-exact-inverse.json',{'source_predecessor':pin(OLD/'complete_duplicate_census_v2.py'),'source_successor':payload,
    'source_edits':[{'before':before,'after':after}],'whole_module_AST_inverse':True,'bootstrap_edits':edits,'bootstrap_exact_inverse':True,
    'unchanged':{'address_space_bytes':536870912,'stdout_bytes_including_newline':32768,'capture_per_file_bytes':134217728,'capture_total_bytes':268435456,
        'capture_tree_bytes':4294967296,'capture_entry_seconds':165,'capture_outer_seconds':180},'actual_executed':False})
test=(OLD/'test_complete_census_v2.py').read_text().replace('complete_duplicate_census_v2.py','complete_duplicate_census_v3.py')
(HERE/'test_complete_census_v3.py').write_text(test)
test=(OLD/'test_readonly_bootstrap_v3.py').read_text().replace('readonly_bootstrap_v3.py','readonly_bootstrap_v4.py').replace('complete_duplicate_census_v2.py','complete_duplicate_census_v3.py')
assert test.count('22965')==1 and test.count('22966')==1
test=test.replace('len(script),22965',f"len(script),{payload['bytes']}").replace('read(22966)',f"read({payload['bytes']+1})")
(HERE/'test_readonly_bootstrap_v4.py').write_text(test)
print(json.dumps({'source':payload,'bootstrap':pin(HERE/'readonly_bootstrap_v4.py'),'command':pin(HERE/'complete-census-command-v3.json')}))
