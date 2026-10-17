"""2026-10-16 ET. Pure closed-registry controls over explicitly synthetic inputs."""
import copy
import hashlib
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import unittest

HERE=Path(__file__).resolve().parent


def deny(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        raise AssertionError('registry controls forbid child/native/network')
    if event=='import' and str(args[0]).split('.')[0]=='swdb':
        raise AssertionError('registry controls forbid project imports')


sys.addaudithook(deny)
M=SimpleNamespace(**runpy.run_path(str(HERE/'unit_policy_registry_v1.py')))


def fixture():
    policies,contracts,refs={}, {}, []
    for index,(function,source_sha,expected) in enumerate(M.FUNCTIONS):
        source={'root':'library','path':'proof_units/'+('first.cpp' if index==0 else 'memory.cpp'),'sha256':source_sha}
        rows=[]
        for result,name in expected:
            value={'id':name,'kind':'rewrite_contract','proof_unit':{'source':source,'function':function},
                'concurrency_frame':[],'clauses':[{'id':'frame','acsl':{'text':r'assigns \everything;','uses':[]}},
                    {'id':'result','acsl':{'text':r'ensures \result == '+str(result)+';','uses':[]}}]}
            contracts[name]=M.canonical(value)
            rows.append({'id':name,'sha256':M.digest(value),'expected_result':result})
        first=index==0
        policy={'kind':M.KIND,'schema':'dx100-whole-fixed-source-policy-1' if first else 'dx100-whole-exact-memory-source-policy-1',
            'function':function,'caller_mangled':'_Z'+str(len(function))+function+'v',
            'defines':['NUM_CORES=4','TILE_SIZE=16384'],'choice_budget':256,'thread':0,
            'buffer_projection':'fixed-fixture-identical-buffer-with-captured-diagnostic-origin-v1' if first else 'exact-three-root-cxx-view-with-captured-origin-v1',
            'proof_source':source,'capture':{'synthetic':'not an accepted capture'},
            'receiver_selection':{'root':'library','path':'receivers/'+str(index)+'.json','sha256':'a'*64},
            'expected':{'synthetic':'not a source/body certificate'},
            'producer_manifest':{'root':'library','path':'producers/'+str(index)+'.json','sha256':'b'*64},
            'native_projection':{'synthetic':'not a native projection'},'frame':r'assigns \everything;',
            'unit_contracts':rows,'source_loop_bound':1,'helper_loop_bound':513}
        # The legacy policy deliberately is not canonically serialized. The
        # registry must reference its original bytes, never silently rewrite.
        raw=(json.dumps(policy,indent=2)+'\n').encode() if first else M.canonical(policy)
        sha=hashlib.sha256(raw).hexdigest();policies[sha]=raw
        refs.append({'root':'library','path':'policies/'+str(index)+'.json','sha256':sha})
    output=M.assemble(refs,policies,contracts)
    return output,policies,contracts


class Controls(unittest.TestCase):
    def test_one_registry_all_four_units_five_contracts_and_opaque_legacy(self):
        output,policies,contracts=fixture();value=json.loads(output['registry_bytes'])
        checked=M.validate(output['registry_bytes'],policies,contracts)
        self.assertEqual((len(value['units']),len(checked.contract_content_identities)),(4,5))
        self.assertFalse(output['owned_receipts_emitted']);self.assertFalse(output['scientific_acceptance'])
        self.assertEqual(output['registry_sha256'],M.sha(output['registry_bytes']))
        first=value['units'][0];raw=policies[first['policy']['sha256']]
        self.assertNotEqual(raw,M.canonical(json.loads(raw)))
        self.assertEqual(M.sha(raw),first['policy']['sha256'])
        for unit in value['units']:
            for contract in unit['contracts']:
                selected=M.lookup(checked,source=unit['source'],function=unit['function'],
                    contract_id=contract['id'],contract_sha256=contract['sha256'])
                self.assertEqual(selected['policy'],unit['policy'])
                self.assertFalse(selected['source_or_runtime_admission_granted'])

    def test_lookup_requires_entire_source_function_contract_tuple(self):
        output,policies,contracts=fixture();checked=M.validate(output['registry_bytes'],policies,contracts)
        unit=json.loads(output['registry_bytes'])['units'][0];row=unit['contracts'][0]
        original={'source':unit['source'],'function':unit['function'],'contract_id':row['id'],'contract_sha256':row['sha256']}
        for field,value in (('source',{**unit['source'],'sha256':'0'*64}),('source',{**unit['source'],'path':'other.cpp'}),
                            ('function',M.FUNCTIONS[1][0]),('contract_id','unregistered'),('contract_sha256','0'*64)):
            with self.assertRaises(M.Refused):M.lookup(checked,**{**original,field:value})
        other=unit['contracts'][1]
        with self.assertRaises(M.Refused):M.lookup(checked,**{**original,'contract_id':other['id']})

    def test_79_80_share_one_source_model_policy_structural_view_only(self):
        output,policies,contracts=fixture();checked=M.validate(output['registry_bytes'],policies,contracts)
        unit=json.loads(output['registry_bytes'])['units'][0];first,second=unit['contracts']
        rows=[M.lookup(checked,source=unit['source'],function=unit['function'],contract_id=row['id'],contract_sha256=row['sha256'])
              for row in (first,second)]
        self.assertEqual(rows[0]['policy'],rows[1]['policy'])
        view=M.baseline_policy(checked,{'source':unit['source'],'function':unit['function']})
        self.assertEqual(view['policy'],rows[0]['policy']);self.assertTrue(view['structural_view_only'])
        self.assertFalse(view['contract_or_source_admission_granted'])
        with self.assertRaises(M.Refused):M.baseline_policy(checked,{'source':unit['source'],'function':'unknown'})

    def test_missing_duplicate_or_reordered_profiles_refuse(self):
        output,policies,contracts=fixture();base=json.loads(output['registry_bytes'])
        for change in ('delete','duplicate','reverse','extra'):
            value=copy.deepcopy(base)
            if change=='delete':value['units'].pop()
            if change=='duplicate':value['units'][1]=value['units'][0]
            if change=='reverse':value['units'].reverse()
            if change=='extra':value['units'].append(value['units'][0])
            with self.assertRaises(M.Refused):M.validate(M.canonical(value),policies,contracts)

    def test_policy_and_contract_hash_changes_and_extra_documents_refuse(self):
        output,policies,contracts=fixture();registry=output['registry_bytes']
        first=next(iter(policies));changed={**policies,first:policies[first]+b' '}
        with self.assertRaises(M.Refused):M.validate(registry,changed,contracts)
        with self.assertRaises(M.Refused):M.validate(registry,{**policies,'c'*64:b'{}'},contracts)
        name=next(iter(contracts));value=json.loads(contracts[name]);value['proof_unit']['function']='wrong'
        with self.assertRaises(M.Refused):M.validate(registry,policies,{**contracts,name:M.canonical(value)})
        with self.assertRaises(M.Refused):M.validate(registry,policies,{**contracts,'extra':b'{}'})

    def test_source_buffer_one_TU_thread_budget_and_frame_must_match(self):
        for field,value in (('proof_source',{'root':'library','path':'different-memory.cpp','sha256':M.MEMORY_SHA}),
                            ('thread',1),('choice_budget',128),('frame',r'assigns \nothing;'),('helper_loop_bound',512)):
            output,policies,contracts=fixture();registry=json.loads(output['registry_bytes']);unit=registry['units'][1]
            old=unit['policy']['sha256'];policy=json.loads(policies.pop(old));policy[field]=value
            raw=M.canonical(policy);new=M.sha(raw);policies[new]=raw;unit['policy']['sha256']=new
            with self.assertRaises(M.Refused):M.validate(M.canonical(registry),policies,contracts)

    def test_source_policy_contract_selection_cannot_inject_premise(self):
        output,policies,contracts=fixture();registry=json.loads(output['registry_bytes']);unit=registry['units'][1]
        row=unit['contracts'][0];value=json.loads(contracts[row['id']]);value['clauses'][0]['acsl']['text']=r'requires 0;'
        changed=M.canonical(value);row['sha256']=M.digest(value);contracts[row['id']]=changed
        old=unit['policy']['sha256'];policy=json.loads(policies.pop(old));policy['unit_contracts']=unit['contracts']
        raw=M.canonical(policy);new=M.sha(raw);policies[new]=raw;unit['policy']['sha256']=new
        with self.assertRaises(M.Refused):M.validate(M.canonical(registry),policies,contracts)

    def test_rebinding_all_documents_cannot_split_the_memory_TU(self):
        output,policies,contracts=fixture();registry=json.loads(output['registry_bytes']);unit=registry['units'][1]
        unit['source']={**unit['source'],'path':'proof_units/separately-parsed-memory.cpp'}
        row=unit['contracts'][0];contract=json.loads(contracts[row['id']]);contract['proof_unit']['source']=unit['source']
        contracts[row['id']]=M.canonical(contract);row['sha256']=M.digest(contract)
        old=unit['policy']['sha256'];policy=json.loads(policies.pop(old));policy['proof_source']=unit['source'];policy['unit_contracts']=unit['contracts']
        raw=M.canonical(policy);new=M.sha(raw);policies[new]=raw;unit['policy']['sha256']=new
        with self.assertRaisesRegex(M.Refused,'share one complete original source/TU buffer'):
            M.validate(M.canonical(registry),policies,contracts)

    def test_full_registry_requires_the_closed_256_slot_profile(self):
        output,policies,contracts=fixture();registry=json.loads(output['registry_bytes']);registry['choice_budget']=128
        for unit in registry['units']:
            old=unit['policy']['sha256'];policy=json.loads(policies.pop(old));policy['choice_budget']=128
            raw=M.canonical(policy);new=M.sha(raw);policies[new]=raw;unit['policy']['sha256']=new
        with self.assertRaisesRegex(M.Refused,'common draw budget'):
            M.validate(M.canonical(registry),policies,contracts)

    def test_independently_parsed_memory_capture_refuses(self):
        output,policies,contracts=fixture();registry=json.loads(output['registry_bytes']);unit=registry['units'][1]
        old=unit['policy']['sha256'];policy=json.loads(policies.pop(old));policy['capture']={'synthetic':'a different complete parse'}
        raw=M.canonical(policy);new=M.sha(raw);policies[new]=raw;unit['policy']['sha256']=new
        with self.assertRaisesRegex(M.Refused,'one exact complete-TU capture/ABI transport'):
            M.validate(M.canonical(registry),policies,contracts)

    def test_strict_json_and_portable_refs(self):
        for raw in (b'{"kind":1,"kind":2}',b'{"n":NaN}',b'{"n":Infinity}'):
            with self.assertRaises(M.Refused):M.document(raw)
        for path in ('../escape','a//b','a/./b','/absolute','a\\b','__pycache__/x'):
            with self.assertRaises(M.Refused):M.portable({'root':'library','path':path,'sha256':'0'*64})
        with self.assertRaises(M.Refused):M.portable({'root':'repository','path':'a','sha256':'0'*64})


if __name__=='__main__':unittest.main(verbosity=2)
