"""Prepare separately reviewed runner for the harness-only repair."""
import ast,hashlib,pathlib
P=pathlib.Path;p=P('/private/tmp/lanl17-run-reviewed-isolated-custody-regression-20261007-a3.py');raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='d40290b3e1be602a6392e65a55851d333bfac1e6849cafdb5f6485ffc94fa349'
s=raw.decode()
def change(old,new):
    global s
    assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new)
change('lanl17_parent_capture_custody_isolated_regression_a3_20261007.py','lanl17_parent_capture_custody_isolated_regression_a3r1_20261007.py')
change('lanl17-parent-capture-custody-regression-source-proof-20261007-a3.json','lanl17-parent-capture-custody-regression-source-proof-20261007-a3r1.json')
change('lanl17-parent-capture-custody-regression-source-handoff-20261007-a3.md','lanl17-parent-capture-custody-regression-source-handoff-20261007-a3r1.md')
change('e1fbd54de38492f1706002f6755b8d5d09c5ad5fb21a7f2a3b3ca3ca132048f7\',14003','1a37ac92f7415607479c46945de00cddb27de4013f12abd17dcbd2637b4f29d2\',14382')
change('97c55556a10e7836dc4c2ed9da8533dbad3fad7a00edfc359bf0f148c9a26634','576f91e5e1d56025cd2f5a4b863313b290c0c407d121095141399c3037046915')
change('7ac9e87f563311422760d91439ad3731a8eb5ac1a5858aa7da93a9be28a830c5','7b5719069d32b14f519fad2e2dc607c32bee4776912b22e3ddcf8b9b93ab3f06')
change("d['execution']['tests_run']","d['execution']['a3r1_tests_run']")
change("d['exact_AST_fragment_sha256'][name]","d['AST_invariance']['selected_source_and_guard_fragment_pins_unchanged'][name]")
change('lanl17-parent-capture-custody-regression-actual-20261007-a3.','lanl17-parent-capture-custody-regression-actual-20261007-a3r1.')
change("'source_and_preparation_preserved':True,'batch_invocations':1,","'source_and_preparation_preserved':True,'batch_invocations':1,'original_failed_attempt':{'identity_sha256':'b5f71558d42a6338c2397ec4998e497767f40c1a0f2950c6ef4bec632edeb9fa','reported_methods':12,'setup_errors':12,'test_bodies_executed':0,'preserved_unchanged':True},")
out=P('/private/tmp/lanl17-run-reviewed-isolated-custody-regression-20261007-a3r1.py');assert not out.exists();ast.parse(s);out.write_text(s)
print({'path':str(out),'bytes':len(s.encode()),'sha256':hashlib.sha256(s.encode()).hexdigest(),'state':'corrected runner source prepared; NOT RUN'})
