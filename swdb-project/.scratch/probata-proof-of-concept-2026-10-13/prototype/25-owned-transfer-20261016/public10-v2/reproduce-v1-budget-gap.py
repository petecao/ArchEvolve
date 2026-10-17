"""2026-10-16 ET. Deterministic V1 budget refusal control; no observer main."""
from pathlib import Path
import ast,unittest
HERE=Path(__file__).resolve().parent
p=HERE/'pure_controls.py';tree=ast.parse(p.read_bytes());tree.body=[n for n in tree.body if not isinstance(n,ast.If)]
ns={'__name__':'owned10_v1_budget_reproduction','__file__':str(p)};exec(compile(tree,str(p),'exec'),ns)
prior=HERE.with_name('public10-v1')/'inert-d7f685c6-public10-v1/entry.py'
tree=ast.parse(prior.read_bytes());tree.body=[n for n in tree.body if not isinstance(n,ast.If)]
subject={'__name__':'preserved_owned10_v1','__file__':str(prior)};exec(compile(tree,str(prior),'exec'),subject);ns['entry']=subject
suite=unittest.TestSuite([ns['Controls']('test_final_profile_writes_keep_real_staged_root_sibling_headroom')])
result=unittest.TextTestRunner(verbosity=2).run(suite)
print('The unchanged V1 incorrectly admits one byte beyond its intended profile cap, consuming root headroom. No scientific/native run occurred.')
raise SystemExit(not result.wasSuccessful())
