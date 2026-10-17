"""2026-10-16 ET. No-child actual-small-input RED/GREEN and source inverses."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest

HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
DIAGNOSTIC=WHOLE/'abi-enum-diagnostic-v1/census_abi_enums_v1.py'
namespace={'__file__':str(DIAGNOSTIC),'__name__':'offline_census_library'}
exec(compile(DIAGNOSTIC.read_bytes(),str(DIAGNOSTIC),'exec'),namespace)
need=namespace['need'];read_pin=namespace['read_pin'];sha=namespace['sha'];strict=namespace['strict']
REPLAY=WHOLE/'abi-retained-replay-v1/controls'
policy=strict(read_pin({'path':str(REPLAY/'policy.json'),'bytes':438152,
    'sha256':'3f20967eaeaa7a3469ef4a4b249c2ce2161ae0ec9a9eda41be80c6d950919ad4'},1048576))
def local_control(name):
    row=policy['controls'][name]
    return {**row,'path':str(REPLAY/Path(row['path']).name)}
namespace['local_control']=local_control
helper,legacy,binder=namespace['primitives']()
proposal_path=HERE/'proposed/compiler_unit_adapter_v4.py'
proposal=namespace['source_module']('candidate',{'path':str(proposal_path),'bytes':proposal_path.stat().st_size,
    'sha256':sha(proposal_path.read_bytes())})
transfer=strict(read_pin({'path':str(WHOLE/'abi-small-artifact-transfer-v1/verified-transfer.json'),'bytes':9292,
    'sha256':'fb4a5d46a64b8e439da569f1264cf70c752d1625f866668ff11b2146fc30b276'}))
ACTUAL=[]
for artifact in policy['artifacts']:
    chosen={role:next(row for row in transfer['files'] if row['remote']==artifact[role]) for role in ('ABI','probe')}
    need(all(row['before']==row['after'] and row['remote']['sha256']==row['local']['sha256']
        and row['remote']['bytes']==row['local']['bytes'] for row in chosen.values()),'exact transfer closure')
    raw=read_pin(chosen['ABI']['local']); probe=read_pin(chosen['probe']['local'])
    derived,receipt=helper.normalize_abi(raw)
    ACTUAL.append({'raw':raw,'derived':derived,'probe':probe,'path':artifact['probe']['path'],
        'receipt':receipt,'roots':proposal.parse_json_roots(derived)})


def run_reader(module,raw,row):
    class BoundProbe:
        def __init__(self,path):need(str(path)==row['path'],'only exact original probe coordinate rebound')
        def __str__(self):return row['path']
        def resolve(self):return self
        def read_bytes(self):return row['probe']
    original=module.Path
    try:
        module.Path=BoundProbe
        return module.observed_abi(raw,probe_path=row['path'],api=binder.__dict__)
    finally:module.Path=original


def enum(row,key):return copy.deepcopy(next(root for root in row['roots'] if root.get('name')=='dws_probe_'+key))
def value(root,key,row):return proposal._enum_source_value(proposal.resolve_locations(root,row['path']),key,row['path'],row['probe'])
def ast_nodes(raw):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}


class Controls(unittest.TestCase):
    def test_complete_actual_pipelines_old_red_new_green(self):
        records=[]
        for row in ACTUAL:
            for module in (legacy,proposal):
                with self.assertRaisesRegex(module.Refused,'malformed compiler JSON stream'):
                    run_reader(module,row['raw'],row)
            with self.assertRaisesRegex(legacy.Refused,'one observed integer ConstantExpr required'):
                run_reader(legacy,row['derived'],row)
            result=run_reader(proposal,row['derived'],row)
            self.assertEqual(result['root_count'],29)
            self.assertEqual(len(result['constants']),23)
            self.assertEqual(result['constants']['little_endian'],1)
            self.assertEqual(result['constants']['int_bits'],32)
            self.assertEqual(result['constants']['pointer_bits'],64)
            self.assertEqual(result['abi']['sizes'],[4,4,4,8,8,8])
            self.assertEqual(binder.validate_abi(result['abi']),result['abi'])
            self.assertEqual(result['raw_probe_sha256'],sha(row['derived']))
            self.assertIs(result['public_admission'],False)
            records.append({'family':row['receipt']['selected_family'],'derived':{'bytes':len(row['derived']),'sha256':sha(row['derived'])},
                'observation':result,'old_original_refused':True,'new_original_refused':True,'old_derived_refused':True,
                'diagnostic_only_exact_probe_read_adapter':True})
        self.assertEqual(records[0]['observation']['abi'],records[1]['observation']['abi'])
        self.assertEqual(records[0]['observation']['constants'],records[1]['observation']['constants'])
        self.__class__.actual=records

    def test_all_23_exact_enum_nodes(self):
        for row in ACTUAL:
            observed=run_reader(proposal,row['derived'],row)
            for key in proposal.ABI_INTS:
                self.assertEqual(value(enum(row,key),key,row),observed['constants'][key])

    def test_endian_selects_own_typed_apvalue_never_operand(self):
        for row in ACTUAL:
            root=enum(row,'little_endian');constant=root['inner'][0]['inner'][0]
            operand_values=[node.get('value') for node in self.walk(constant['inner'][0]) if node.get('kind')=='IntegerLiteral']
            self.assertEqual(operand_values,['1234','1234'])
            self.assertEqual(value(root,'little_endian',row),1)
            for wrong in ('1234','1','0','TRUE','false ',True,1,None):
                changed=copy.deepcopy(root);changed['inner'][0]['inner'][0]['value']=wrong
                with self.assertRaises(proposal.Refused):value(changed,'little_endian',row)
            changed=copy.deepcopy(root);changed['inner'][0]['inner'][0]['value']='false'
            self.assertEqual(value(changed,'little_endian',row),0)
            # unchanged source domain remains exactly little_endian == 1.
            expression=next(n.args[0] for n in ast.walk(ast.parse((HERE/'base-source.py').read_bytes()))
                if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='need'
                and len(n.args)==2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=='source byte/endianness domain')
            self.assertFalse(eval(compile(ast.Expression(expression),'<unchanged-endian-domain>','eval'),{'integers':{'char_bit':8,'little_endian':0}}))

    @staticmethod
    def walk(root):
        yield root
        for node in root.get('inner',[]):yield from Controls.walk(node)

    def test_wrong_shape_type_cast_value_and_extra_expression_refuse(self):
        for row in ACTUAL:
            for key in proposal.ABI_INTS:
                root=enum(row,key)
                changes=[lambda n:n.update(name='dws_probe_other'),lambda n:n.update(type={'qualType':'int'}),
                    lambda n:n['inner'][0].update(castKind='IntegralToBoolean'),
                    lambda n:n['inner'][0].update(type={'qualType':'unsigned long'}),
                    lambda n:n['inner'][0].update(valueCategory='lvalue'),
                    lambda n:n['inner'][0]['inner'][0].update(type={'qualType':'float'}),
                    lambda n:n['inner'][0]['inner'][0].update(value='-1'),
                    lambda n:n['inner'][0]['inner'][0].update(value=True),
                    lambda n:n['inner'][0]['inner'][0]['inner'].append({'kind':'CallExpr'}),
                    lambda n:n['inner'][0]['inner'][0]['inner'][0].update(inner=[{'kind':'ConstantExpr','value':'1'}]),
                    lambda n:n['inner'].append(copy.deepcopy(n['inner'][0]))]
                for change in changes:
                    changed=copy.deepcopy(root);change(changed)
                    with self.assertRaises(proposal.Refused):value(changed,key,row)

    def test_integral_range_and_source_coordinate_refusals(self):
        for row in ACTUAL:
            root=enum(row,'int_bits')
            for wrong in ('4294967296','999999999999999999999','1.0','true','+32',' 32','-32'):
                changed=copy.deepcopy(root);changed['inner'][0]['inner'][0]['value']=wrong
                with self.assertRaises(proposal.Refused):value(changed,'int_bits',row)
            for role in ('loc','range'):
                changed=copy.deepcopy(root)
                if role=='loc':changed['loc']['offset']+=1
                else:
                    point=changed['inner'][0]['inner'][0]['range']['end']
                    point.get('expansionLoc',point)['offset']+=1
                with self.assertRaises(proposal.Refused):value(changed,'int_bits',row)
            with self.assertRaises(proposal.Refused):proposal._enum_source_value(root,'int_bits','/other/probe.cpp',row['probe'])
            with self.assertRaises(proposal.Refused):proposal._enum_source_value(root,'int_bits',row['path'],row['probe']+b' ')

    def test_exact_stream_and_probe_selection_refuse_changes(self):
        for row in ACTUAL:
            self.assertIsNone(proposal._enum_profile(row['derived']+b' ',row['path']))
            self.assertIsNone(proposal._enum_profile(row['derived'].replace(b'"value":"32"',b'"value":"33"',1),row['path']))
            with self.assertRaises(proposal.Refused):proposal._enum_profile(row['derived'],'/other/compiler_abi_probe_v1.cpp')
            changed=copy.deepcopy(row['roots']);changed[6],changed[7]=changed[7],changed[6]
            raw=b'\n'.join(json.dumps(n,separators=(',',':')).encode() for n in changed)
            with self.assertRaises(proposal.Refused):run_reader(proposal,raw,row)
            deleted=b'\n'.join(json.dumps(n,separators=(',',':')).encode() for n in row['roots'][:-1])
            with self.assertRaises(proposal.Refused):run_reader(proposal,deleted,row)

    def test_old_literal_pipeline_is_byte_behavior_unchanged(self):
        for row in ACTUAL:
            integers=run_reader(proposal,row['derived'],row)['constants']
            roots=copy.deepcopy(row['roots'])
            for root in roots:
                if root.get('kind')=='EnumConstantDecl':
                    key=root['name'][len('dws_probe_'):]
                    root['inner']=[{'kind':'ConstantExpr','value':str(integers[key])}]
            oldstyle=b'\n'.join(json.dumps(root,separators=(',',':')).encode() for root in roots)
            self.assertEqual(run_reader(legacy,oldstyle,row),run_reader(proposal,oldstyle,row))

    def test_full_source_inverse_and_unchanged_nodes(self):
        candidate=proposal_path.read_text();base=(HERE/'base-source.py').read_text()
        changes=json.loads((HERE/'exact-delta.json').read_bytes())['changes']
        for change in reversed(changes):
            self.assertEqual(candidate.count(change['new']),1)
            candidate=candidate.replace(change['new'],change['old'])
        self.assertEqual(candidate,base)
        before=ast_nodes(base);after=ast_nodes(proposal_path.read_bytes())
        for name in before:
            if name!='observed_abi':self.assertEqual(before[name],after[name],name)
        self.assertEqual(sha((HERE/'base-source.py').read_bytes()),'775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c')

    def test_semantic_receipt_distinguishes_all_identities(self):
        for row in ACTUAL:
            result=run_reader(proposal,row['derived'],row)
            receipt=result['semantic_enum_interpretation']
            self.assertEqual(receipt['role_derived_strict_ABI'],{'bytes':len(row['derived']),'sha256':sha(row['derived'])})
            self.assertEqual(receipt['selected_original_ABI'],{'bytes':len(row['raw']),'sha256':sha(row['raw'])})
            self.assertEqual(receipt['original_probe'],{'path':row['path'],'bytes':1588,'sha256':sha(row['probe'])})
            self.assertEqual(receipt['interpreted_constants_canonical_sha256'],sha(namespace['canonical'](result['constants'])))
            self.assertIs(receipt['input_AST_mutated'],False)
            self.assertIs(receipt['interpretation_is_reversible_AST_transport'],False)
            self.assertIs(receipt['physical_reader_pin_required_from_enclosing_producer_manifest'],True)
            self.assertNotEqual(receipt['interpreted_constants_canonical_sha256'],sha(row['derived']))

    def test_primary_source_bindings_and_probe_syntax(self):
        root=WHOLE/'compiler-ABI-value-primary-v1'
        expected={'APValue.cpp':(38301,'6f06288f8c55beb1f0da0501aa88d62f655cecc5d58e615b0dc1b30f26497132'),
            'OperationKinds.def':(16203,'f6336db9e60d2d1216a142d00b1c75dcc06109f95f2478ccf6489a28a463423d'),
            'SemaDecl.cpp':(849847,'73871a91bb6d5348e5ec42dbec031890f7c38ce64bd82c647a2a7893e9cffdcc')}
        texts={}
        for name,(size,digest) in expected.items():texts[name]=read_pin({'path':str(root/name),'bytes':size,'sha256':digest},1048576).decode()
        self.assertIn('Out << (getInt().getBoolValue() ? "true" : "false");',texts['APValue.cpp'])
        self.assertIn('CAST_OPERATION(IntegralCast)',texts['OperationKinds.def'])
        self.assertIn('Context, NewTy, CK_IntegralCast, ECD->getInitExpr(),',texts['SemaDecl.cpp'])
        for row in ACTUAL:
            syntax=namespace['syntax'](row['probe'],proposal.ABI_INTS)
            self.assertEqual({key:syntax['dws_probe_'+key]['expression'] for key in proposal.ABI_INTS},
                {key:entry[0] for key,entry in proposal.ENUM_EXPRESSIONS.items()})

    def test_complete_physical_before_after(self):
        for row in list(namespace['READS'].values()):read_pin(row['pin'],1048576)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    outcome=unittest.TextTestRunner(verbosity=2).run(suite)
    if outcome.wasSuccessful():
        output={'schema':'offline-exact-two-ABI-enum-repair-controls-2','date':'2026-10-16 ET','tests':outcome.testsRun,
            'failures':len(outcome.failures),'errors':len(outcome.errors),'skips':len(outcome.skipped),
            'actual_small_metadata_results':Controls.actual,'remote_or_compiler_or_scientific_execution':False,
            'source_or_public_admission':False}
        destination=HERE/'actual-offline-reader-controls-v2.json'
        data=namespace['canonical'](output)+b'\n'
        if destination.exists():need(destination.read_bytes()==data,'retained offline result differs')
        else:
            with destination.open('xb') as handle:handle.write(data)
    sys.exit(not outcome.wasSuccessful())
