"""No-child source controls; no C execution or public registry emulation."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('finite_owned_fixtures',HERE/'build_fixtures_v1.py')
b=importlib.util.module_from_spec(spec);sys.modules[spec.name]=b;spec.loader.exec_module(b);m=b.bridge

class Controls(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=HERE,prefix='pure-owned-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def selected(self):return b.assemble(self.root/'case')
    def prepare(self,row):return m.prepare(m.OwnedSelection(m.Pin.parse(row['selection'])))
    def resolve_inputs(self,row):
        policy=json.loads(Path(row['selection']['path']).read_bytes());source=json.loads(Path(policy['prepared']['policy']['path']).read_bytes())
        entry=json.loads(Path(source['entry']['path']).read_bytes());context=json.loads(Path(source['context']['path']).read_bytes())
        certificate=json.loads(Path(row['outputs']['composition-certificate.json']['path']).read_bytes())
        return policy,source,entry,context,certificate['owned_facts']
    def test_resolved_composition_keeps_exact_body_and_profile(self):
        row=self.selected();prepared=self.prepare(row);cert=json.loads(prepared.certificate_json)
        source=(b.FINITE/'prepared-corpus-v1/history_latest_positive/trace.c').read_text()
        self.assertTrue(prepared.c_text.startswith(source))
        self.assertEqual(cert['closure_nodes_required'],0)
        integration=json.loads(prepared.integration_json)
        self.assertEqual(integration['resource_profile']['node_limit'],256)
        self.assertEqual(integration['resource_profile']['nodes_required'],129)
        self.assertFalse(cert['ownership_or_payload_grant']);self.assertTrue(cert['static_scope_representation_only'])
        self.assertTrue(cert['public_library_selection_and_entry_validation_required'])
    def test_exact_entry_fragments_hashes_and_owner_sentences(self):
        row=self.selected();prepared=self.prepare(row);cert=json.loads(prepared.certificate_json)
        self.assertEqual(len(cert['record_assumptions']),6)
        for item in cert['record_assumptions']:
            self.assertEqual(item['kind'],'proof_semantics')
            self.assertTrue(item['reference']['id'].startswith('semantics.dx100_bfs_0_2#finite_context_'))
            self.assertEqual(item['reference']['sha256'],cert['same_entry']['sha256'])
            self.assertIn(cert['owned_facts_sha256'],item['sentence'])
    def test_old_unruled_v1_entry_refuses_instead_of_granting_state(self):
        row=self.selected();policy,source,entry,context,facts=self.resolve_inputs(row)
        old_policy=json.loads((b.FINITE/'prepared-corpus-v1/history_latest_positive/policy.json').read_bytes())
        old_entry=json.loads(Path(old_policy['entry']['path']).read_bytes())
        old_context=json.loads(Path(old_policy['context']['path']).read_bytes())
        with self.assertRaises(m.Refused):m.resolve_rules(old_entry,old_policy['entry'],old_policy['entry_id'],old_context,facts,policy['premise_owner'])
        unruled=dict(entry,rules=[])
        with self.assertRaisesRegex(m.Refused,'unresolved'):m.resolve_rules(unruled,source['entry'],policy['entry_id'],context,facts,policy['premise_owner'])
    def test_additional_recorded_base_rules_are_preserved_in_entry_order(self):
        row=self.selected();policy,source,entry,context,facts=self.resolve_inputs(row)
        entry['rules'].insert(0,dict(id='mmio_ordering',statement='An additional owned base rule.',assumed=dict(owner='Eric'),record_assumption=True))
        assumptions=m.resolve_rules(entry,source['entry'],policy['entry_id'],context,facts,policy['premise_owner'])
        self.assertEqual(len(assumptions),7)
        self.assertEqual(assumptions[0],dict(kind='proof_semantics',reference=dict(id=policy['entry_id']+'#mmio_ordering',sha256=source['entry']['sha256']),sentence='An additional owned base rule.'))
    def test_wrong_owner_statement_rule_and_entry_refuse(self):
        row=self.selected();policy,source,entry,context,facts=self.resolve_inputs(row)
        mutations=[lambda e,c:e['rules'][0]['assumed'].update(owner='other-owner'),
            lambda e,c:e['rules'][0].update(statement='different owned statement'),
            lambda e,c:e['rules'][0].update(record_assumption=False),lambda e,c:e['rules'].append(deepcopy(e['rules'][0])),
            lambda e,c:c['owned_premises'][0].update(rule='other_rule'),lambda e,c:c['owned_premises'][0]['owner'].update(id='other_entry'),
            lambda e,c:e.update(version='0.1')]
        for mutate in mutations:
            changed=deepcopy(entry);ctx=deepcopy(context);mutate(changed,ctx)
            with self.subTest(changed=changed.get('version')),self.assertRaises(m.Refused):m.resolve_rules(changed,source['entry'],policy['entry_id'],ctx,facts,policy['premise_owner'])
    def test_changed_owned_facts_need_their_exact_rule(self):
        row=self.selected();policy,source,entry,context,facts=self.resolve_inputs(row)
        for change in [lambda f:f['context']['tile_owners'].__setitem__(0,1),lambda f:f['context']['register_owners'].__setitem__(0,1),
            lambda f:f['context']['regions'][0].update(begin=0),lambda f:f['numeric_flags'].update(ieee_binary_rn=0),
            lambda f:f.update(resource_profile_sha256='0'*64)]:
            changed=deepcopy(facts);change(changed)
            with self.assertRaisesRegex(m.Refused,'unresolved'):m.resolve_rules(entry,source['entry'],policy['entry_id'],context,changed,policy['premise_owner'])
    def test_repinned_resource_or_readset_changes_do_not_compose(self):
        for key in ('profile','certificate','draws','anchors','c_text'):
            with self.subTest(key=key):
                directory=self.root/key;row=b.assemble(directory);policy=json.loads(Path(row['selection']['path']).read_bytes())
                artifact=policy['prepared'][key];path=Path(artifact['path']);raw=path.read_bytes()
                if key=='profile':doc=json.loads(raw);doc['node_limit']=128;raw=m.canonical(doc)
                elif key=='certificate':doc=json.loads(raw);doc['physical_inputs']=doc['physical_inputs'][:-1];raw=m.canonical(doc)
                else:raw+=b' '
                path.write_bytes(raw);policy['prepared'][key]=b.pin(path);row['selection']=b.save(Path(row['selection']['path']),policy)
                with self.assertRaisesRegex(m.Refused,'prepared '+key+' differs'):self.prepare(row)
    def test_prestate_is_one_shot_representation_without_reset_wait_payload_or_count_rewrite(self):
        prepared=self.prepare(self.selected());text=prepared.receiver_c_text
        self.assertIn('dwe_owned_receiver_entered==0',text);self.assertIn('dwe_owned_receiver_entered=1',text)
        self.assertIn('dxz_sizes[i]=UINT_MAX',text);self.assertIn('dxm_tile_owner[4]=1;',text)
        self.assertIn('dxr_regions[6].begin=UINT64_C(4096)',text)
        for banned in ('reset(', 'claim_', 'dwi_wait', 'dxc_cover(', 'SWDB_ASSUME(', 'dxm_count=', 'dxm_event_count=', 'dxc_count=', 'dxm_memory['):
            # Equality checks are allowed; assignments to counters are not.
            if banned.endswith('='):self.assertNotIn(banned+'0;',text)
            else:self.assertNotIn(banned,text)
        self.assertEqual(text.count('dwe_prepare_owned_receiver();'),1)
        self.assertEqual(text.count('return dwe_trace_program();'),1)
    def test_full_u32_draw_order_is_exact_and_not_assumed(self):
        prepared=self.prepare(self.selected());draws=json.loads(prepared.draw_binding_json)
        self.assertEqual(draws['count'],4);self.assertEqual(draws['domain'],[0,2**32-1])
        self.assertEqual([r['c_lvalue'] for r in draws['rows']],['dws_choice_table[%d]'%i for i in range(4)])
        self.assertIn('dws_choice_table[i]=(uint32_t)swdb_next();',prepared.receiver_c_text)
        self.assertFalse(draws['actual_draws_or_native_replay_supplied'])
    def test_oversized_and_changed_physical_input_refuse_before_use(self):
        path=self.root/'file';path.write_bytes(b'large');selected=m.Pin(str(path),1,m.sha(b'l'))
        with patch.object(Path,'open',side_effect=AssertionError('oversized file opened')):
            with self.assertRaises(m.Refused):m.Inputs().read(selected)
        selected=b.pin(path);reads=m.Inputs();reads.read(selected);path.write_bytes(b'other')
        with self.assertRaises(m.Refused):reads.recheck()
    def test_unknown_composer_field_and_arbitrary_initializer_refuse(self):
        row=self.selected();policy=json.loads(Path(row['selection']['path']).read_bytes());policy['initializer']='dxm_reset();'
        row['selection']=b.save(Path(row['selection']['path']),policy)
        with self.assertRaises(m.Refused):self.prepare(row)

if __name__=='__main__':unittest.main()
