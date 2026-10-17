"""Narrow source-only settled-publication repair; V1 remains unexecuted."""
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'role-normalization-controller-v1'
source=(OLD/'controller_template.py').read_text();edits=[]
def edit(before,after):
    global source
    assert source.count(before)==1;source=source.replace(before,after,1);edits.append({'before':before,'after':after})
edit('t28-role-gzip-2baf722f-v1','t28-role-gzip-2baf722f-v2')
edit('def main():', '''def settled_success(result_pin):
    need(pin(OUT/'result.json')==result_pin,'final result identity changed after close/publication')
    extent()
    need(time.monotonic()-START<900,'settled passive publication deadline reached')

def main():''')
edit("'schema':'passive-paired-type-gzip-transform-result-1','normalization_complete':True", "'schema':'passive-paired-type-gzip-transform-result-2','completion_requires_controller_zero_exit_and_settled_publication':True,'normalization_complete':True")
edit("    print(json.dumps({'normalization_complete':True,'result':pin(OUT/'result.json'),'source_call_ABI_or_public_admission':False},sort_keys=True))", "    result_pin=pin(OUT/'result.json')\n    settled_success(result_pin)\n    print(json.dumps({'normalization_complete':True,'result':result_pin,'source_call_ABI_or_public_admission':False},sort_keys=True),flush=True)\n    settled_success(result_pin)")
(HERE/'controller_template.py').write_text(source)
restored=source
for row in reversed(edits):assert restored.count(row['after'])==1;restored=restored.replace(row['after'],row['before'],1)
assert restored==(OLD/'controller_template.py').read_text()
(HERE/'settled-v2-inverse.json').write_text(json.dumps({'edits':edits,'exact_template_inverse':True,'V1_unchanged':True,
    'late_failure_retained_complete_result_requires_nonzero_exit_refusal':True,'actual_executed':False},sort_keys=True,indent=2)+'\n')
prep=(OLD/'prepare_controller_v1.py').read_text()
for before,after in [('normalization_controller_v1.py','normalization_controller_v2.py'),('source_policy_v1.json','source_policy_v2.json'),('bootstrap_v1.py','bootstrap_v2.py'),('command_v1.json','command_v2.json'),('t28-role-gzip-2baf722f-v1','t28-role-gzip-2baf722f-v2')]:prep=prep.replace(before,after)
(HERE/'prepare_controller_v2.py').write_text(prep)
test=(OLD/'test_controller_v1.py').read_text()
for before,after in [('normalization_controller_v1.py','normalization_controller_v2.py'),('source_policy_v1.json','source_policy_v2.json'),('bootstrap_v1.py','bootstrap_v2.py'),('command_v1.json','command_v2.json')]:test=test.replace(before,after)
extra='''    def test_delayed_final_close_and_pin_refuse_settled_success(self):
        for delayed in ('close','pin','extent'):
            clock={'now':899.9};expected={'bytes':10,'sha256':'a'*64}
            class FakeSink:
                def __init__(self,*args):pass
                def write(self,value):return len(value)
                def close(self):
                    if delayed=='close':clock['now']=901
            def final_pin(path):
                if delayed=='pin':clock['now']=901
                return expected
            def final_extent():
                if delayed=='extent':clock['now']=901
            ns={'Sink':FakeSink,'canonical':lambda value:b'{}','RESERVE':1048576,'OUT':Path('/inert'),
                'START':0,'time':SimpleNamespace(monotonic=lambda:clock['now']),'pin':final_pin,'extent':final_extent}
            extract({'Refused','need','save','settled_success'},ns)
            ns['save']('result.json',{},True)
            with self.assertRaises(ns['Refused']):ns['settled_success'](expected)
    def test_settled_publication_has_checks_before_and_after_flush(self):
        main=next(n for n in TREE.body if getattr(n,'name',None)=='main')
        calls=[n for n in main.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)]
        names=[n.value.func.id if isinstance(n.value.func,ast.Name) else None for n in calls]
        self.assertEqual(names[-4:],['save','settled_success','print','settled_success'])
        printing=calls[-2].value;self.assertTrue(any(k.arg=='flush' and isinstance(k.value,ast.Constant) and k.value.value is True for k in printing.keywords))
        self.assertIn('completion_requires_controller_zero_exit_and_settled_publication',SOURCE.decode())
'''
assert test.count("if __name__=='__main__':")==1;test=test.replace("if __name__=='__main__':",extra+"if __name__=='__main__':")
(HERE/'test_controller_v2.py').write_text(test)
print('Authored source/template/test repair only.')
