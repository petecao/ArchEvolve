"""Source-only narrow V1 successor; no actual retained reader/bootstrap run."""
import ast
import hashlib
import json
from pathlib import Path
import shlex

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'compiler-duplicate-census-v1'
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def save(name,value):(HERE/name).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
source=(OLD/'complete_duplicate_census_v1.py').read_text();edits=[]
def edit(before,after):
    global source
    assert source.count(before)==1,(before,source.count(before));source=source.replace(before,after,1);edits.append({'before':before,'after':after})
edit("event={'node_kind':node_kind,'node_id':fields.get('id',{}).get('scalar',{}).get('text'),", "kind_value=fields.get('kind',{});kind_identity={'value_kind':kind_value.get('kind','missing-or-ambiguous'),\n                            'ordered_merkle_sha256':kind_value.get('ordered_merkle_sha256'),\n                            'decoded_string_sha256':kind_value.get('scalar',{}).get('sha256')}\n                        event={'node_kind':node_kind,'node_kind_identity':kind_identity,'node_id':fields.get('id',{}).get('scalar',{}).get('text'),")
edit("group=json.dumps([node_kind,item['key'][:256],item['ordinal'],reason],separators=(',',':'));self.groups[group]=self.groups.get(group,0)+1;need(len(self.groups)<=256,'bounded distinct duplicate role census')", "group=json.dumps({'node_kind_identity':kind_identity,'key_sha256':event['key_sha256'],'ordinal':item['ordinal'],'reason':reason},sort_keys=True,separators=(',',':'));self.groups[group]=self.groups.get(group,0)+1;need(len(self.groups)<=256,'bounded distinct duplicate role census')")
publication='''def publication(value,limit=32768):
    """Keep complete census hashes; omit display rows to fit the entire line."""
    def encode(item):return json.dumps(item,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)
    complete=encode(value);result=dict(value);report=dict(value['census']);result['census']=report
    report['samples']=list(report['samples']);report['duplicate_groups']=list(report['duplicate_groups'])
    result['publication']={'schema':'bounded-complete-census-publication-2','stdout_limit_bytes':limit,
        'complete_report_bytes':len(complete.encode()),'complete_report_sha256':hashlib.sha256(complete.encode()).hexdigest(),
        'omitted_event_display_rows':0,'omitted_group_display_rows':0,'complete_census_digests_preserved':True}
    while True:
        text=encode(result)
        if len(text.encode())+1<=limit:return text
        if report['duplicate_groups']:
            report['duplicate_groups'].pop();result['publication']['omitted_group_display_rows']+=1
        elif report['samples']:
            report['samples'].pop();result['publication']['omitted_event_display_rows']+=1
        else:raise Refused('fixed compact census metadata exceeds output cap')

'''
edit("if __name__=='__main__':",publication+"if __name__=='__main__':")
edit("value=json.dumps(inspect(sys.argv[1]),sort_keys=True,allow_nan=False);need(len(value.encode())<=32768,'compact metadata output cap exceeded');print(value)","print(publication(inspect(sys.argv[1])))")
path=HERE/'complete_duplicate_census_v2.py';path.write_text(source)
inverse=source
for row in reversed(edits):assert inverse.count(row['after'])==1;inverse=inverse.replace(row['after'],row['before'],1)
assert inverse==(OLD/'complete_duplicate_census_v1.py').read_text()
old_tree=ast.parse(inverse);new_tree=ast.parse(source)
unchanged=[]
for node in old_tree.body:
    if isinstance(node,(ast.FunctionDef,ast.ClassDef)) and node.name!='census':
        other=next(n for n in new_tree.body if type(n)==type(node) and n.name==node.name)
        assert ast.dump(node,include_attributes=False)==ast.dump(other,include_attributes=False);unchanged.append(node.name)
save('census-v2-inverse.json',{'predecessor':pin(OLD/'complete_duplicate_census_v1.py'),'successor':pin(path),'edits':edits,'exact_text_inverse':True,'unchanged_top_level_AST':unchanged,'actual_executed':False})
payload=pin(path);boot=(OLD/'readonly_bootstrap_v2.py').read_text();boot_edits=[]
for before,after in [('21434',str(payload['bytes']+1)),('21433',str(payload['bytes'])),('ff5e7424155960f2f5425d5f942fe99aa69b27f43e740ac4c8620c3590aadd49',payload['sha256'])]:
    assert boot.count(before)==1;boot=boot.replace(before,after,1);boot_edits.append({'before':before,'after':after})
(HERE/'readonly_bootstrap_v3.py').write_text(boot)
prior=json.loads((OLD/'complete-census-command-v1.json').read_bytes());python_argv=list(prior['python_argv']);python_argv[4]=boot
env=prior['closed_environment'];remote=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','120s','/usr/bin/env','-i',*[k+'='+v for k,v in env.items()],*python_argv]
command=dict(prior);command.update(bootstrap=pin(HERE/'readonly_bootstrap_v3.py'),stdin=payload,python_argv=python_argv,remote_argv=remote,remote_shell_command=shlex.join(remote),
    predecessor_command=pin(OLD/'complete-census-command-v1.json'),scope='SOURCE ONLY: V2 complete retained-TU duplicate census; new root admission required')
save('complete-census-command-v2.json',command)
save('bootstrap-v3-inverse.json',{'predecessor':pin(OLD/'readonly_bootstrap_v2.py'),'successor':pin(HERE/'readonly_bootstrap_v3.py'),'edits':boot_edits,'exact_text_inverse':True,'caps_audit_environment_unchanged':True})
print(json.dumps({'source':payload,'command':pin(HERE/'complete-census-command-v2.json')}))
