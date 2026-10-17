"""2026-10-16 ET. Local-only standalone ownership10 admission controls."""
import ast
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import zlib

HERE=Path(__file__).resolve().parent
PACKET=Path(sys.argv[1]).resolve()
sys.argv=sys.argv[:1]
attempts=[]
def deny(event,args):
    if event in {'subprocess.Popen','os.system','os.fork','os.posix_spawn','socket.connect','ctypes.dlopen'}:
        attempts.append(event);raise AssertionError('pure control rejected '+event)
sys.addaudithook(deny)
entry_bytes=(PACKET/'entry.py').read_bytes();tree=ast.parse(entry_bytes)
tree.body=[n for n in tree.body if not isinstance(n,ast.If)]
entry={'__name__':'owned10_pure_capsule','__file__':str(PACKET/'entry.py')}
exec(compile(tree,str(PACKET/'entry.py'),'exec'),entry)
expected=json.loads((PACKET/'expected.json').read_bytes())

def pin(path):
    data=path.read_bytes();return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

class LayoutControls(unittest.TestCase):
    def test_make_dependency_reader_rejects_missing_duplicate_or_expanded_inputs(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder);source=root/'source.c';source.write_text('int x;')
            header=root/'header.h';header.write_text('int y;');dep=root/'deps.d'
            dep.write_text('layout-object: '+str(source)+' '+chr(92)+chr(10)+' '+str(header)+'\n')
            self.assertEqual(entry['layout_dependencies'](dep,source),[source,header])
            for text in ('wrong: '+str(source), 'layout-object: '+str(source)+' '+str(source),
                         'layout-object: '+str(header),'layout-object: $(command)', 'layout-object: relative.h'):
                dep.write_text(text)
                with self.assertRaises(ValueError):entry['layout_dependencies'](dep,source)

    def test_physical_layout_pin_tracks_literal_alias_and_bytes(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder);header=root/'header.h';header.write_text('one')
            alias=root/'alias.h';alias.symlink_to(header)
            row=entry['layout_pin'](alias)
            self.assertEqual(row['physical'],str(header.resolve()))
            self.assertEqual(row['aliases'],[{'path':str(alias),'literal_target':str(header)}])
            header.write_text('two');self.assertNotEqual(row,entry['layout_pin'](alias))

    def layout_fixture(self,root):
        import shutil
        inputs=root/'canonical';shutil.copytree(HERE.parent/'inert-all-types-v1',inputs)
        driver=root/'driver';driver.write_text('inert never executed')
        header=root/'header.h';header.write_text('typedef int untouched;')
        want=copy.deepcopy(expected);want['layout_policy']['driver']=pin(driver)
        return inputs,driver,header,want

    def test_all_eight_complete_sources_use_dependency_then_real_syntax_flags(self):
        calls=[]
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder)/'raw';root.mkdir();inputs,driver,header,want=self.layout_fixture(root)
            def fake(argv,directory,env,policy,timeout,watch,out):
                calls.append(argv)
                self.assertEqual(argv[0],str(driver));self.assertIn('-std=c11',argv);self.assertIn('-x',argv)
                self.assertEqual(argv[argv.index('-x')+1],'c');self.assertFalse(any(x in argv for x in ('-c','-o','-emit-llvm')))
                dep=Path(argv[argv.index('-MF')+1]);source=Path(argv[-1]);dep.write_text('layout-object: '+str(source)+' '+str(header)+'\n')
                return {'exit_code':0,'timed_out':False,'out_of_memory':False,'output_limit':False}
            with mock.patch.dict(entry,guarded_generation=fake):
                result=entry['layout_checks'](inputs,want['canonical_manifest'],want,root,want['resource_policy'],lambda:30,None)
            self.assertEqual(len(calls),16)
            for i in range(0,16,2):
                self.assertIn('-M',calls[i]);self.assertIn('-fsyntax-only',calls[i+1]);self.assertIn('-MD',calls[i+1]);self.assertEqual(calls[i][-1],calls[i+1][-1])
            self.assertEqual(result['units'],8);self.assertFalse(result['source_or_Typed_or_caller_admission'])

    def test_dependency_change_between_precheck_and_syntax_refuses(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder)/'raw';root.mkdir();inputs,driver,header,want=self.layout_fixture(root)
            def fake(argv,directory,env,policy,timeout,watch,out):
                dep=Path(argv[argv.index('-MF')+1]);dep.write_text('layout-object: '+argv[-1]+' '+str(header)+'\n')
                if '-fsyntax-only' in argv:header.write_text('changed before successful syntax result')
                return {'exit_code':0,'timed_out':False,'out_of_memory':False,'output_limit':False}
            with mock.patch.dict(entry,guarded_generation=fake),self.assertRaisesRegex(ValueError,'dependencies differ'):
                entry['layout_checks'](inputs,want['canonical_manifest'],want,root,want['resource_policy'],lambda:30,None)

    def test_failed_layout_phase_cannot_be_promoted(self):
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            root=Path(folder)/'raw';root.mkdir();inputs,driver,header,want=self.layout_fixture(root)
            def fake(*args):return {'exit_code':1,'timed_out':False,'out_of_memory':False,'output_limit':False}
            with mock.patch.dict(entry,guarded_generation=fake),self.assertRaisesRegex(ValueError,'layout phase failed'):
                entry['layout_checks'](inputs,want['canonical_manifest'],want,root,want['resource_policy'],lambda:30,None)

class Controls(LayoutControls):
    def test_prospective_packet_matches_complete_actual_target_input_and_root_census(self):
        packet=json.loads((PACKET/'packet.json').read_bytes())
        self.assertEqual({key:packet[key]for key in ('complete_targets','check_lemmas','canonical_files','root_kind')},
            {'complete_targets':len(expected['target_ids']),'check_lemmas':len(expected['target_ids']),
             'canonical_files':len(expected['canonical_files']),'root_kind':'t25-owned-swap13-public-v1'})
    def test_math_only_main_cannot_dispatch_layout_or_adopt_prior_layout(self):
        self.assertEqual(expected['proof_policy']['C_layout_only_units'],0)
        packet=json.loads((PACKET/'packet.json').read_bytes())
        self.assertEqual(packet['C_layout_only_units'],0)
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
        self.assertFalse(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='layout_checks' for n in ast.walk(main)))
        self.assertIn('C_layout_assertions_adopted',ast.unparse(main))

    def setUp(self):entry['ACTIVE_LEAF'].clear()
    def tearDown(self):entry['ACTIVE_LEAF'].clear()
    def test_thirteen_same_antecedent_targets_and_complete_forty_two_inputs(self):
        self.assertEqual(len(expected['target_ids']),13)
        self.assertEqual(len(set(expected['target_ids'])),13)
        self.assertEqual(len(expected['canonical_files']),42)
        self.assertEqual(expected['elements'],['int','float','double','int *'])
        self.assertEqual(len(expected['canonical_manifest']['source_members']),8)
        for row in expected['canonical_manifest']['obligations']:
            self.assertEqual((row['kind'],row['status'],row['dependencies']),('check_lemma','pending',[]))
        self.assertFalse(expected['canonical_manifest']['source_typed_bridge_established'])
        self.assertEqual(expected['canonical_manifest']['current_model_records_admitted'],[])

    def test_canonical_byte_mutation_and_extras_cannot_be_accepted(self):
        canonical=HERE.parent/'inert-all-types-v1'
        import shutil
        class Checker:
            @staticmethod
            def check(directory,**kwargs):
                self.assertEqual(kwargs,{'elements':tuple(expected['elements'])})
                return expected['canonical_manifest']
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            directory=Path(folder)/'packet';shutil.copytree(canonical,directory)
            entry['canonical_check'](Checker,expected,directory)
            target=directory/expected['canonical_manifest']['obligations'][0]['path']
            target.write_bytes(target.read_bytes()+b'\n')
            with self.assertRaisesRegex(ValueError,'canonical packet differs'):entry['canonical_check'](Checker,expected,directory)
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            directory=Path(folder)/'packet';shutil.copytree(canonical,directory);(directory/'extra').write_text('x')
            with self.assertRaisesRegex(ValueError,'canonical packet differs'):entry['canonical_check'](Checker,expected,directory)

    def test_command_embeds_exact_entry_and_expected_roundtrip(self):
        command=json.loads((PACKET/'root-command.json').read_bytes())
        found={}
        for node in ast.parse(command[6]).body:
            if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
                if node.targets[0].id in {'ENTRY_SHA256','EXPECTED_SHA256','ENTRY_COMPRESSED_BASE64','EXPECTED_COMPRESSED_BASE64'}:found[node.targets[0].id]=ast.literal_eval(node.value)
        self.assertEqual(zlib.decompress(base64.b64decode(found['ENTRY_COMPRESSED_BASE64'],validate=True)),entry_bytes)
        data=(PACKET/'expected.json').read_bytes()
        self.assertEqual(zlib.decompress(base64.b64decode(found['EXPECTED_COMPRESSED_BASE64'],validate=True)),data)
        self.assertEqual(found['ENTRY_SHA256'],hashlib.sha256(entry_bytes).hexdigest())
        self.assertEqual(found['EXPECTED_SHA256'],hashlib.sha256(data).hexdigest())
        self.assertLess(len(command[6].encode()),120000)
        self.assertEqual(command[-2:],['{SOURCE}/swdb-project','{OUTPUT}'])

    def test_normal_complete_census_and_normal_engine_are_preserved(self):
        previous=HERE.parents[1]/'25-private-lifetime-frame-20261016/entry-template-public-v1.py'
        def definition(source,name):
            return ast.dump(next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name==name),include_attributes=False)
        self.assertEqual(definition(entry_bytes,'normal_task_census'),definition(previous.read_bytes(),'normal_task_census'))
        self.assertEqual(expected['proof_policy']['solver_portfolio'],['alt-ergo','z3','cvc5'])
        self.assertEqual(expected['proof_policy']['solver_seconds'],30)
        self.assertFalse(expected['proof_policy']['public_proof_record_created'])
        self.assertFalse(expected['proof_policy']['universal_proof_setup_attested'])
        for name in ('-wp-prop','-wp-fct','-wp-gen','-wp-no-why3-detect'):
            self.assertNotIn(name,expected['explicit_method_binding']['wp_model_flags'])

    def test_no_test_module_builder_or_catalog_seed_is_imported(self):
        imports=[alias.name for node in ast.walk(ast.parse(entry_bytes))if isinstance(node,ast.Import)for alias in node.names]
        imports += [node.module for node in ast.walk(ast.parse(entry_bytes))if isinstance(node,ast.ImportFrom)]
        self.assertFalse(any(name and(name.startswith('test_')or name.startswith('tests.'))for name in imports))
        self.assertNotIn('initialize_workspace',entry)
        self.assertEqual(set(expected['source_consumer_trees']),{'swdb','schemas','vocab','library/methods/probata-draft-1.yaml','tests/fixtures/proof/methods/contract-fixture-1.yaml'})

    def active_leaf(self,root):
        target='move.transfer';leaf=root/('leaf-'+target);leaf.mkdir();(leaf/'tmp').mkdir()
        data=b'check lemma actual;';(leaf/'wp_input.c').write_bytes(data)
        digest=hashlib.sha256(data).hexdigest()
        (leaf/'command.json').write_text(json.dumps({'cwd':str(leaf),'selected_id':target,'input':{'sha256':digest}}))
        entry['ACTIVE_LEAF'].update(directory=leaf,target=target,input_sha256=digest)
        return leaf

    def test_only_active_exact_attributed_leaf_tmp_socket_name_is_eligible(self):
        with tempfile.TemporaryDirectory(dir=HERE)as folder:
            root=Path(folder);leaf=self.active_leaf(root)
            path=leaf/'tmp/why3serverabcdefsock'
            self.assertTrue(entry['active_ipc_path'](root,path))
            self.assertFalse(entry['active_ipc_path'](root,leaf/'tmp/other.sock'))
            self.assertFalse(entry['active_ipc_path'](root,leaf/'tmp/why3serverABCDEFsock'))
            self.assertFalse(entry['active_ipc_path'](root,leaf/'why3serverabcdefsock'))
            (leaf/'wp_input.c').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'canonical invocation'):entry['active_ipc_path'](root,path)
            entry['ACTIVE_LEAF'].clear();self.assertFalse(entry['active_ipc_path'](root,path))

    def socket_walk(self,root,*,active=True,count=1,wrong_owner=False,wrong_size=False,wrong_device=False):
        leaf=self.active_leaf(root)
        paths=[]
        for i in range(count):
            path=leaf/('tmp/why3server'+format(i,'06x')+'sock');path.write_bytes(b'');paths.append(path)
        if not active:entry['ACTIVE_LEAF'].clear()
        real=os.scandir
        class Item:
            def __init__(self,item):self.item=item;self.path=item.path
            def stat(self,**kwargs):
                old=self.item.stat(**kwargs)
                if Path(self.path)not in paths:return old
                return SimpleNamespace(st_mode=stat.S_IFSOCK|0o600,st_size=1 if wrong_size else 0,
                   st_uid=os.geteuid()+1 if wrong_owner else os.geteuid(),st_dev=old.st_dev+1 if wrong_device else old.st_dev)
        class Scan:
            def __init__(self,path):self.inner=real(path)
            def __enter__(self):return self
            def __exit__(self,*a):self.inner.close()
            def __iter__(self):
                for item in self.inner:yield Item(item)
        with mock.patch.object(entry['os'],'scandir',side_effect=lambda p:Scan(p)):
            return entry['raw_bytes'](root)

    def test_one_live_owned_zero_size_socket_is_metadata_only_and_not_counted_as_file(self):
        with tempfile.TemporaryDirectory(dir=HERE)as folder:
            root=Path(folder);self.assertGreater(self.socket_walk(root),0)

    def test_settled_extra_foreign_owner_nonzero_or_other_device_sockets_refuse(self):
        for options in ({'active':False},{'count':2},{'wrong_owner':True},{'wrong_size':True},{'wrong_device':True}):
            with self.subTest(options=options),tempfile.TemporaryDirectory(dir=HERE)as folder:
                with self.assertRaises(ValueError):self.socket_walk(Path(folder),**options)

    def test_output_symlinks_and_unrelated_specials_are_not_ignored(self):
        with tempfile.TemporaryDirectory(dir=HERE)as folder:
            root=Path(folder);(root/'regular').write_bytes(b'123');(root/'alias').symlink_to(root/'regular')
            with self.assertRaisesRegex(ValueError,'links and special'):entry['raw_bytes'](root)

    def test_metadata_projection_reserve_and_post_fsync_extent_are_bounded(self):
        policy={'per_file_bytes':4096,'metadata_reserve_bytes':2048,'output_budget_bytes':8192,'root_headroom_bytes':0}
        with tempfile.TemporaryDirectory(dir=HERE)as folder:
            root=Path(folder);path=root/'value.json'
            entry['bounded_json'](path,{'value':1},root,policy)
            self.assertEqual(json.loads(path.read_bytes()),{'value':1})
            (root/'payload').write_bytes(b'x'*6144)
            with self.assertRaisesRegex(ValueError,'projected aggregate'):entry['bounded_json'](root/'another.json',{'value':2},root,policy)
            self.assertFalse((root/'another.json').exists())
            with self.assertRaisesRegex(ValueError,'per-file'):entry['bounded_bytes'](path,b'x'*4097,root,policy)

    def test_metadata_refuses_replacing_link_before_write(self):
        with tempfile.TemporaryDirectory(dir=HERE)as folder:
            root=Path(folder);(root/'target').write_bytes(b'old');link=root/'alias';link.symlink_to(root/'target')
            with self.assertRaisesRegex(ValueError,'regular file'):entry['bounded_bytes'](link,b'new',root,{'per_file_bytes':100,'metadata_reserve_bytes':1,'output_budget_bytes':100,'root_headroom_bytes':0})
            self.assertEqual((root/'target').read_bytes(),b'old')

    def test_primary_error_is_bounded_first_failure_and_never_accepts(self):
        with tempfile.TemporaryDirectory(dir=HERE)as folder:
            root=Path(folder);policy={'metadata_reserve_bytes':65536,'output_budget_bytes':131072,'root_headroom_bytes':0}
            first=entry['preserve_primary_error'](root,ValueError('original failure'),policy)
            entry['preserve_primary_error'](root,RuntimeError('later postcheck'),policy)
            value=json.loads((root/'primary-error.json').read_bytes())
            self.assertEqual(value['error'],'original failure')
            self.assertFalse(value['producer_complete']);self.assertFalse(value['proof_acceptance'])
            self.assertEqual(first,pin(root/'primary-error.json'))

    def test_final_profile_writes_keep_real_staged_root_sibling_headroom(self):
        with tempfile.TemporaryDirectory(dir=HERE)as folder:
            root=Path(folder);profile=root/'owned-transfer10-public-v2-profile';profile.mkdir()
            # Actual prospective entry/context/bootstrap metadata bytes, never
            # an installed runtime or scientific result surrogate.
            for name,data in [('owned-transfer10-public-v2-entry.py',entry_bytes),
                              ('owned-transfer10-public-v2-expected.json',(PACKET/'expected.json').read_bytes()),
                              ('launch.json',(PACKET/'root-command.json').read_bytes())]:
                (root/name).write_bytes(data)
            policy={'per_file_bytes':134217728,'metadata_reserve_bytes':1024,
                    'root_headroom_bytes':4194304,'root_post_exit_reserve_bytes':524288,
                    'output_budget_bytes':4194304+8192}
            (profile/'payload').write_bytes(b'x'*6192)
            entry['bounded_bytes'](profile/'result.json',b'r'*1000,profile,policy,reserve=False)
            entry['bounded_bytes'](profile/'artifact-manifest.json',b'm'*1000,profile,policy,reserve=False)
            self.assertEqual(entry['raw_bytes'](profile),8192)
            # V1 erroneously admitted this because reserve=False consumed the
            # root allowance; V2 must refuse before writing even one more byte.
            with self.assertRaisesRegex(ValueError,'projected aggregate'):
                entry['bounded_bytes'](profile/'overflow.json',b'x',profile,policy,reserve=False)
            self.assertFalse((profile/'overflow.json').exists())
            census=entry['root_sibling_census'](profile,policy)
            self.assertEqual(census['bytes'],sum(p.stat().st_size for p in root.iterdir()if p.is_file()))
            self.assertLessEqual(census['bytes']+8192+524288,policy['output_budget_bytes'])
            extra=policy['root_headroom_bytes']-policy['root_post_exit_reserve_bytes']-census['bytes']+1
            (root/'too-much-late-metadata').write_bytes(b'x'*extra)
            with self.assertRaisesRegex(ValueError,'fixed headroom'):
                entry['root_sibling_census'](profile,policy)

    def test_fresh_why3_package_membership_and_elf_alias_candidate_closure_are_present(self):
        snap=json.loads((HERE/'why3-runtime-snapshot.json').read_bytes())
        self.assertEqual(len(snap['why3_runtime_extension']['inventories']),9)
        files={row['path']:row for row in snap['why3_elf_candidate_files']}
        server='/data1/yanruj/probata-verifiers/opam/framac-33/lib/why3/why3server'
        self.assertEqual(files[server]['bytes'],96944)
        self.assertTrue(files[server]['sha256'].startswith('0792d33b'))
        self.assertEqual(len(files),152)
        self.assertEqual(len(snap['why3_elf_candidate_aliases']),3)
        self.assertFalse(snap['historical_runtime_identity_rewritten'])
        self.assertEqual(attempts,[])

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','pure_controls':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'child_native_network_attempts':attempts,'actual_profile_executed':False},sort_keys=True))
    raise SystemExit(not result.wasSuccessful())
