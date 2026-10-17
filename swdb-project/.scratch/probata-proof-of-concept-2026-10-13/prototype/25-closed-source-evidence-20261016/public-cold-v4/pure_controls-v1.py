"""2026-10-16 ET. Owned stdlib metadata controls; never execute observer main."""
import ast
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
POC=HERE.parents[2]
ATTEMPTS=[]
def no_child(event,values):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in ('os.system','ctypes.dlopen'):
        ATTEMPTS.append(event)
        raise RuntimeError('owned metadata controls forbid every child/tool/network call')
sys.addaudithook(no_child)
source=(HERE/'observer.py').read_bytes();tree=ast.parse(source)
# Remove the only entry invocation. Definitions/imports and embedded immutable
# metadata are evaluated; no project module or observer main is called.
tree.body=[n for n in tree.body if not isinstance(n,ast.If)]
ns={'__name__':'owned_metadata_controls','__file__':str(HERE/'observer.py')}
exec(compile(tree,str(HERE/'observer.py'),'exec'),ns)
expected=json.loads((HERE/'expected.json').read_bytes())
y={};exec(compile((HERE/'record_yaml_subset.py').read_bytes(),'record_yaml_subset.py','exec'),y)

class Controls(unittest.TestCase):
    def test_embedded_context_and_reader_are_exact(self):
        self.assertEqual(ns['EXPECTED_BYTES'],(HERE/'expected.json').read_bytes())
        self.assertEqual(ns['YAML_BYTES'],(HERE/'record_yaml_subset.py').read_bytes())
        for data,key in ((ns['EXPECTED_BYTES'],'EXPECTED_SHA'),(ns['YAML_BYTES'],'YAML_SHA')):
            self.assertEqual(hashlib.sha256(data).hexdigest(),ns[key])
        self.assertEqual(expected['settlement']['generation'],619)
        self.assertEqual(expected['settlement']['ended_utc'],'2026-10-16T21:28:57Z')
        self.assertEqual(len(expected['source_files']),597)
        self.assertEqual(len(expected['consumer_roots']),13)
        self.assertEqual(sum(len(c['targets']) for c in expected['components']),82)
        self.assertEqual(len(expected['catalog_documents']),91)

    def test_context_science_is_unchanged_from_preserved_v3_draft(self):
        prior=json.loads((HERE.with_name('public-cold-v3')/'expected.json').read_bytes())
        changes={'command','entry','policy','raw_root','prior_failure','root_observation','settlement'}
        self.assertEqual({k:v for k,v in expected.items() if k not in changes},
                         {k:v for k,v in prior.items() if k not in changes})
        self.assertNotEqual(prior['raw_root'],expected['raw_root'])
        self.assertEqual(expected['command']['argv'][-1],expected['policy']['sha256'])

    def test_yaml_nested_flow_literal_and_quoted_values(self):
        raw=b'''id: proof.fixture
checks:
  check: {version: '1', sha256: 0123abcd}
items:
- id: first
  flags: [true, false, null, 0, -1, 2.5, "quoted: text", 'it''s']
  source: |-
    first line
      inner indentation
    third line
- id: second
  text: a long
    folded scalar
  empty: []
  mapping: {}
created: '2026-10-16'
'''
        self.assertEqual(y['loads'](raw),{'id':'proof.fixture','checks':{'check':{'version':'1','sha256':'0123abcd'}},
            'items':[{'id':'first','flags':[True,False,None,0,-1,2.5,'quoted: text',"it's"],
                      'source':'first line\n  inner indentation\nthird line'},
                     {'id':'second','text':'a long folded scalar','empty':[],'mapping':{}}],
            'created':'2026-10-16'})

    def test_yaml_unknown_implicit_or_executable_syntax_refuses(self):
        for raw in (b'a: 1\na: 2\n',b'a: &anchor value\n',b'a: *anchor\n',b'a: !!python/object:thing {}\n',
                    b'a: yes\n',b'a: .NaN\n',b'a: 0xFF\n',b'a: 1_000\n',b'a: +12\n',
                    b'a: 1\n---\nb: 2\n',b'a: {id: x, id: y}\n',b'a:\n\tb: 1\n'):
            with self.subTest(raw=raw),self.assertRaises((ValueError,TypeError,IndexError)):
                y['loads'](raw)

    def test_ten_retained_original_record_yamls_match_primary_metadata(self):
        prep=json.loads((POC/'evidence/t25-explicit-method-selection-repair-preparation-v2-20261016.json').read_bytes())
        rows=prep['retained_record_observations'];self.assertEqual(len(rows),10)
        for row in rows:
            path=Path(row['path']);raw=path.read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
            record=y['loads'](raw)
            self.assertEqual(record['pins']['method_version'],row['method'])
            self.assertEqual(record['proof_setup_check']['method_version'],row['setup_method'])
            self.assertEqual(record['subject'],row['subject'])
            self.assertEqual(record['verdict'],row['verdict'])
            self.assertIs(record['settings']['verifier_launched'],False)
            entry=y['loads']((path.parents[2]/'library/rewrite_contracts/fixture_vector_closed_no_growth.yaml').read_bytes())
            self.assertEqual(entry,ns['expected_contract_entry'](expected,'safe'))

    def test_full_contract_and_wrong_result_are_separate_content(self):
        good=ns['expected_contract_entry'](expected,'safe');bad=ns['expected_contract_entry'](expected,'wrong_result')
        self.assertEqual(good['clauses'][0:2],bad['clauses'][0:2])
        self.assertEqual(bad['clauses'][2]['acsl']['text'],r'ensures \result == 123;')
        self.assertNotEqual(ns['digest'](good),ns['digest'](bad))
        self.assertEqual([x['acsl']['text'] for x in good['clauses']],expected['expected_contract'])

    def test_strict_json_duplicates_and_nonfinite_refuse(self):
        for raw in (b'{"a":1,"a":2}',b'{"n":NaN}',b'{"n":Infinity}'):
            with self.assertRaises(ValueError):ns['strict_json'](raw)
        self.assertEqual(ns['strict_json'](b'{"a":[1,null,true]}'),{'a':[1,None,True]})

    def test_physical_pins_use_content_and_retained_nine_fields(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            path=Path(folder)/'value.json';path.write_bytes(b'{}')
            physical=ns['Physical']();row=physical.pin(path)
            self.assertEqual(row['sha256'],hashlib.sha256(b'{}').hexdigest())
            self.assertEqual(len(ns['stable'](path.lstat())),9)
            physical.unchanged()
            path.write_bytes(b'[]')
            with self.assertRaises(ValueError):physical.pin(path)
            alias=Path(folder)/'alias';alias.symlink_to(path)
            with self.assertRaises(ValueError):ns['Physical']().pin(alias)

    def make_raw(self,root,index=4):
        base=root/'closed-source-profile/pytest';base.mkdir(parents=True)
        for i in range(5):(base/(ns['PREFIX']+str(i))).mkdir()
        (base/(ns['PREFIX']+'current')).symlink_to(base/(ns['PREFIX']+str(index)))
        return base

    def test_full_five_alias_and_membership_are_mandatory(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder);base=self.make_raw(root)
            row=ns['raw_snapshot'](root);self.assertEqual(len(row['aliases']),1)
            self.assertTrue(row['aliases'][0]['literal_target'].endswith(ns['PREFIX']+'4'))
            alias=base/(ns['PREFIX']+'current');alias.unlink();alias.symlink_to(base/(ns['PREFIX']+'3'))
            with self.assertRaises(ValueError):ns['raw_snapshot'](root)
            alias.unlink();alias.symlink_to(base/(ns['PREFIX']+'4'))
            (base/(ns['PREFIX']+'2')).rmdir()
            with self.assertRaises(ValueError):ns['raw_snapshot'](root)

    def test_unknown_relative_alias_refuses(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder);base=self.make_raw(root)
            unknown=root/'other';unknown.symlink_to(base)
            with self.assertRaises(ValueError):ns['raw_snapshot'](root)
            unknown.unlink();alias=base/(ns['PREFIX']+'current');alias.unlink();alias.symlink_to(ns['PREFIX']+'4')
            with self.assertRaises(ValueError):ns['raw_snapshot'](root)

    def test_all82_catalog_targets_and_document_pointers_close(self):
        old=ns['P'];ns['P']=ns['Physical']()
        try:
            result=ns['bundle_check'](POC/'prototype/25-closed-source-evidence-20261016/scientific-bundle-v3',expected)
            self.assertEqual(result['targets'],82);self.assertEqual(result['objects'],91)
            ns['P'].unchanged()
            changed=copy.deepcopy(expected);changed['catalog']['sha256']='0'*64
            with self.assertRaises(ValueError):ns['bundle_check'](POC/'prototype/25-closed-source-evidence-20261016/scientific-bundle-v3',changed)
        finally:ns['P']=old

    def test_private9_verdict_attribution_and_original_two_timeouts_remain(self):
        components={c['id']:c for c in expected['components']}
        for target in components['private_frame']['targets']:
            obs=target['observation'];self.assertNotIn('normal_verdict',obs)
            self.assertEqual(obs['reconstructed_normal_verdict'],'proven')
            self.assertEqual(obs['normal_verdict_basis']['kind'],'reviewed-passive-observer-assertion')
        glue=components['gluing'];self.assertEqual(len(glue['targets']),4)
        # The complete gluing cold context retains all six original outcomes;
        # accepted_subset grants only the four unchanged proven statements.
        self.assertEqual(len(glue['accepted_subset']['preserved_unaccepted_historical_outcomes']),2)
        self.assertTrue(all(row['normal_verdict']=='not_proven' for row in glue['accepted_subset']['preserved_unaccepted_historical_outcomes']))
        self.assertEqual({row['id'] for row in glue['accepted_subset']['preserved_unaccepted_historical_outcomes']},
                         {'positive.exit_image','positive.cleanup'})

    def test_readonly_audit_denies_tools_network_imports_and_mutation_flags(self):
        main=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='main')
        audit=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='audit')
        test={**ns};exec(compile(ast.fix_missing_locations(ast.Module(body=[audit],type_ignores=[])),'audit_control','exec'),test)
        fun=test['audit']
        for event,values in [('subprocess.Popen',()),('socket.connect',()),('ctypes.dlopen',()),
                             ('import',('swdb',)),('import',('yaml',)),('os.rename',()),
                             ('open',('/a','w',os.O_WRONLY)),('open',('/a',None,os.O_RDONLY|os.O_CREAT)),
                             ('open',('/a',None,os.O_RDONLY|os.O_TRUNC)),('open',('/a',None,os.O_RDONLY|os.O_APPEND))]:
            with self.subTest(event=event,values=values),self.assertRaises(RuntimeError):fun(event,values)
        fun('open',('/a','rb',os.O_RDONLY))

    def test_exact_reviewed_helpers_have_only_allowed_imports_and_no_main(self):
        command=expected['command'];names=('closed_python_surface.py','reviewed_wp_gates.py','reviewed_native_gates.py','python_startup_roles_v2.py')
        old=ns['P'];ns['P']=ns['Physical']()
        try:
            for name in names:
                row=next(x for x in command['controller_inputs'] if x['name']==name)
                value=ns['safe_module'](Path(row['path']),row['sha256'])
                self.assertNotEqual(value['__name__'],'__main__')
        finally:ns['P']=old

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','tests':result.testsRun,'failures':len(result.failures),
                     'errors':len(result.errors),'skips':len(result.skipped),'child_tool_native_network_attempts':ATTEMPTS,
                     'observer_main_executed':False,'remote_raw_inspected':False},sort_keys=True))
    raise SystemExit(not result.wasSuccessful())
