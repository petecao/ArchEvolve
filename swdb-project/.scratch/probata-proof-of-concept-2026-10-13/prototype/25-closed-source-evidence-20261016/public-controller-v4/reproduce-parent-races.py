from pathlib import Path
import ast, unittest
P=Path('/Users/yanrujhou/CLionProjects/ArchEvolve/swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/25-closed-source-evidence-20261016')
p=P/'public-controller-v4/pure_controls.py'
t=ast.parse(p.read_bytes());t.body=[n for n in t.body if not isinstance(n,ast.If)]
ns={'__name__':'race_red_against_preserved_v3','__file__':str(p)};exec(compile(t,str(p),'exec'),ns)
old=P/'public-controller-v3/inert-1433b8f5-node0/entry.py';tree=ast.parse(old.read_bytes());tree.body=[n for n in tree.body if not isinstance(n,ast.If)]
subject={'__name__':'preserved_v3','__file__':str(old)};exec(compile(tree,str(old),'exec'),subject);ns['entry']=subject
suite=unittest.TestSuite(ns['RaceControls'](name) for name in ['test_exact_lock_directory_can_disappear_between_scandir_and_lstat','test_exact_lock_directory_can_disappear_before_queued_scandir'])
result=unittest.TextTestRunner(verbosity=2).run(suite)
print('PREPARED_V3_REPRODUCTION: expected 2 FileNotFoundError cases; no project/tool/native/SSH execution')
raise SystemExit(not result.wasSuccessful())
