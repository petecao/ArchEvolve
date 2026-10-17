"""2026-10-16 ET. Synthetic protocol controls only; no actual compiler output."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest


def deny(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        raise RuntimeError('staging controls refuse '+event)


sys.addaudithook(deny)
HERE=Path(__file__).resolve().parent


def own(name):
    path=HERE/name;ns={'__file__':str(path),'__name__':'inert_staging_fixture'}
    exec(compile(ast.parse(path.read_bytes()),str(path),'exec'),ns)
    return ns


API=own('whole_interface_v3.py');DISPATCH=own('source_dispatch_v2.py');STAGE=own('source_argument_staging_v1.py')
BASE=own('test_whole_interface.py');BASE['API']=API
ABI=BASE['ABI']


def literal(value=0,typ='int'):
    return {'kind':'IntegerLiteral','type':{'qualType':typ},'value':str(value)}


def ref(ident,typ):
    return {'kind':'DeclRefExpr','type':{'qualType':typ},'referencedDecl':{'kind':'VarDecl','id':ident}}


def conversion(node,typ,cast='LValueToRValue'):
    return {'kind':'ImplicitCastExpr','castKind':cast,'type':{'qualType':typ},'inner':[node]}


def decl(ident,typ,source):
    return {'kind':'VarDecl','id':ident,'name':ident,'type':{'qualType':typ},'loc':{'_file':str(source)},
            'range':{'begin':{'offset':0},'end':{'offset':0,'tokLen':1}}}


class Controls(BASE['Controls']):
    def stager(self,row=None,dtype=0,explicit=None):
        row=row or next(row for row in self.declarations if row['name']=='get_new_tile')
        tu,kw=self.fixture(row,dtype,explicit=explicit)
        call=tu['inner'][1]['inner'][0]['inner'][0]
        locals_=[]
        for index,(node,parameter) in enumerate(zip(call['inner'][1:],row['parameters'])):
            if node['kind']=='CXXDefaultArgExpr': continue
            typ=parameter['type'].replace('T1',ABI['canonical_types'][API['TYPE_KEYS'][dtype]])
            localtyp='unsigned int *' if typ=='void *' else typ
            name='local'+str(index);locals_.append(decl(name,localtyp,self.source))
            value=conversion(ref(name,localtyp),localtyp)
            if typ=='void *':value=conversion(value,typ,'BitCast')
            call['inner'][index+1]=value
        tu['inner'][1]['inner'][0]['inner'][:0]=[{'kind':'DeclStmt','inner':[item]} for item in locals_]
        atlas=DISPATCH['prepare_atlas']([{'object_id':'unselected','guest_base':4096,'physical_base':65536,'extent':2,'dtype':0,'source_pin':'a'*64}])
        stages=STAGE['Stager'](API,DISPATCH,tu,atlas=atlas,live_local_ids={item['id'] for item in locals_},**{k:v for k,v in kw.items() if k!='call_range'})
        for item in locals_:stages.register_local(item['id'])
        return stages,tu,kw,call

    def test_07_all_132_instances_render_once_from_actual_local_identity_protocol(self):
        count=0
        for row in self.declarations:
            for dtype in range(6) if row['template'] else (0,):
                stage,tu,kw,call=self.stager(row,dtype)
                binding=API['bind_call'](tu,**kw);out=stage.call(binding)
                self.assertEqual(len(out['staging_statements']),row['formal_arity'])
                self.assertEqual(len(out['staged_arguments']),row['formal_arity'])
                self.assertEqual(out['model_expression'].count('dws_'+binding['c_name']+'('),1)
                self.assertTrue(out['receiver_state_binding_required'])
                self.assertTrue(out['source_RTE_and_local_lifetime_checks_required'])
                self.assertTrue(out['harness_draw_plan_required'])
                self.assertFalse(out['public_admission']);count+=1
        self.assertEqual(count,132)

    def test_08_defaults_and_pointer_offset_conversion_are_closed(self):
        row=next(row for row in self.declarations if row['name']=='maa_indirect_load')
        stage,tu,kw,call=self.stager(row,explicit=row['minimum_arity'])
        out=stage.call(API['bind_call'](tu,**kw))
        self.assertIn('-1',out['model_expression'])
        pointer=call['inner'][1]
        offset={'kind':'BinaryOperator','opcode':'+','type':{'qualType':'unsigned int *'},'inner':[pointer,literal(2)]}
        result=stage.expression(offset)
        self.assertEqual(result['category'],'pointer-descriptor')
        self.assertIn('dws_pointer_offset(',result['expression'])
        for changed in (dict(offset,opcode='*'),dict(offset,type={'qualType':'int *'}),
                        dict(offset,inner=[pointer,literal(2,'unsigned long long')])):
            with self.assertRaises(STAGE['Refused']):stage.expression(changed)

    def test_09_closed_effect_volatile_scope_and_pointer_forgery_refusals(self):
        row=next(row for row in self.declarations if row['name']=='maa_stream_load')
        stage,tu,kw,call=self.stager(row)
        node=call['inner'][2]['inner'][0]
        broken=[dict(node,referencedDecl={'kind':'VarDecl','id':'not-live'}),
                dict(node,type={'qualType':'int','desugaredQualType':'volatile int'}),
                {'kind':'CallExpr','type':{'qualType':'int'},'inner':[]},
                {'kind':'CXXNewExpr','type':{'qualType':'int *'},'inner':[]},
                {'kind':'StmtExpr','type':{'qualType':'int'},'inner':[]},
                {'kind':'UnaryExprOrTypeTraitExpr','type':{'qualType':'unsigned long'},'argType':{'qualType':'int[effect()]'}},
                {'kind':'UnaryOperator','opcode':'++','type':{'qualType':'int'},'inner':[node]},
                conversion(literal(0),'unsigned int *','IntegralToPointer')]
        for mutation in broken:
            with self.assertRaises(STAGE['Refused']):stage.expression(mutation)
        stage.live.remove('local1')
        with self.assertRaisesRegex(STAGE['Refused'],'live'):stage.expression(node)
        with self.assertRaises(STAGE['Refused']):stage.register_local('local1')

    def test_10_cpu_load_store_share_typed_descriptor_and_rhs_first(self):
        row=next(row for row in self.declarations if row['name']=='maa_stream_load')
        stage,tu,kw,call=self.stager(row)
        access={'kind':'ArraySubscriptExpr','type':{'qualType':'unsigned int'},'inner':[call['inner'][1],literal(1)],
                'range':{'begin':{'offset':0,'_file':str(self.source)},'end':{'offset':0,'tokLen':1,'_file':str(self.source)}}}
        rhs=conversion(literal(7),'unsigned int','IntegralCast')
        assignment={'kind':'BinaryOperator','opcode':'=','type':{'qualType':'unsigned int'},'inner':[access,rhs],
                    'range':{'begin':{'offset':0},'end':{'offset':0,'tokLen':1}}}
        # This synthetic full TU owns each projected node once, just as an actual
        # compiler tree must; a separate fabricated root must never suffice.
        read_access=copy.deepcopy(access)
        tu['inner'][1]['inner'][0]['inner'] += [read_access,assignment]
        stage=STAGE['Stager'](API,DISPATCH,tu,atlas=stage.atlas,live_local_ids=set(stage.live),
            **{k:v for k,v in kw.items() if k!='call_range'})
        for ident in sorted(stage.live):stage.register_local(ident)
        read=stage.cpu_load(read_access)
        self.assertIn('dws_cpu_load_u32(owned_thread,',read['expression']);self.assertTrue(read['one_event'])
        write=stage.cpu_store(assignment,discarded_statement=True)
        self.assertTrue(write['statements'][0].startswith('unsigned int src_store_'))
        self.assertTrue(write['statements'][1].startswith('struct dws_pointer src_base_'))
        self.assertIn('dws_cpu_store_u32(owned_thread,',write['statements'][-1])
        self.assertEqual(sum('dws_cpu_store_' in item for item in write['statements']),1)
        with self.assertRaisesRegex(STAGE['Refused'],'actual same-caller'):stage.cpu_load(copy.deepcopy(read_access))
        for mutation in (dict(access,type={'qualType':'int'}),dict(access,inner=[literal(0),literal(1)]),
                         dict(access,inner=[call['inner'][1],literal(1,'unsigned long long')])):
            with self.assertRaises(STAGE['Refused']):stage.cpu_load(mutation)
        with self.assertRaises(STAGE['Refused']):stage.cpu_store(assignment,discarded_statement=False)
        with self.assertRaises(STAGE['Refused']):stage.expression(access)

    def test_11_ordinary_array_requires_exact_source_declaration_certificate(self):
        row=next(row for row in self.declarations if row['name']=='get_new_tile')
        tu,kw=self.fixture(row);node=decl('array','unsigned int[2]',self.source)
        tu['inner'][1]['inner'][0]['inner'].insert(0,{'kind':'DeclStmt','inner':[node]})
        pin=STAGE['digest']({'source_sha256':hashlib.sha256(self.source.read_bytes()).hexdigest(),
            'caller':kw['caller'],'local_id':'array','declaration_sha256':STAGE['digest'](node)})
        obj={'object_id':'array','guest_base':4096,'physical_base':65536,'extent':2,'dtype':0,'source_pin':pin}
        options={k:v for k,v in kw.items() if k!='call_range'}
        stage=STAGE['Stager'](API,DISPATCH,tu,atlas=DISPATCH['prepare_atlas']([obj]),live_local_ids={'array'},**options)
        local=stage.register_local('array',ordinary_object='array')
        self.assertEqual(local['ordinary_descriptor_initializer'],'dws_object_pointer(0)')
        self.assertFalse(stage.atlas['initialization_granted'])
        for key,value in (('source_pin','b'*64),('extent',3),('dtype',1)):
            mutated=dict(obj);mutated[key]=value
            stage=STAGE['Stager'](API,DISPATCH,tu,atlas=DISPATCH['prepare_atlas']([mutated]),live_local_ids={'array'},**options)
            with self.assertRaisesRegex(STAGE['Refused'],'certificate'):stage.register_local('array',ordinary_object='array')

    def test_12_original_enum_constants_require_full_header_span_and_same_tu_identity(self):
        row=next(row for row in self.declarations if row['name']=='get_new_tile')
        tu,kw=self.fixture(row)
        header=Path(next(row for row in self.declarations if Path(row['header_path']).name=='MAA.hpp')['header_path'])
        text=header.read_text();match=re.search(r'enum class Operation_t\s*\{[^}]*\}',text)
        enum={'kind':'EnumDecl','name':'Operation_t','loc':{'_file':str(header)},
              'range':{'begin':{'offset':match.start()},'end':{'offset':match.end()-1,'tokLen':1}},'inner':[]}
        for number,name in enumerate(('ADD_OP','SUB_OP','MUL_OP','DIV_OP','MIN_OP','MAX_OP','AND_OP','OR_OP','XOR_OP',
                                     'SHL_OP','SHR_OP','GT_OP','GTE_OP','LT_OP','LTE_OP','EQ_OP','NE_OP','MAX')):
            enum['inner'].append({'kind':'EnumConstantDecl','name':name,'id':'enum'+str(number),
                'inner':[{'kind':'ConstantExpr','value':str(number)}] if number<17 else []})
        tu['inner'].insert(0,enum)
        atlas=DISPATCH['prepare_atlas']([{'object_id':'unselected','guest_base':4096,'physical_base':65536,'extent':2,'dtype':0,'source_pin':'a'*64}])
        options={k:v for k,v in kw.items() if k!='call_range'}
        stage=STAGE['Stager'](API,DISPATCH,tu,atlas=atlas,live_local_ids=set(),**options)
        node={'kind':'DeclRefExpr','type':{'qualType':'Operation_t'},'referencedDecl':{'kind':'EnumConstantDecl','id':'enum1'}}
        self.assertEqual(stage.expression(node)['expression'],'((int)1)')
        with self.assertRaises(STAGE['Refused']):stage.expression(dict(node,referencedDecl={'kind':'EnumConstantDecl','id':'foreign'}))
        mutated=copy.deepcopy(tu);mutated['inner'][0]['inner'][0]['inner'][0]['value']='99'
        with self.assertRaises(STAGE['Refused']):STAGE['Stager'](API,DISPATCH,mutated,atlas=atlas,live_local_ids=set(),**options)

    def test_13_aggregate_prefix_and_zero_fill_are_original_cpu_writes_only(self):
        row=next(row for row in self.declarations if row['name']=='get_new_tile')
        tu,kw=self.fixture(row);node=decl('array','unsigned int[2]',self.source)
        node['inner']=[{'kind':'InitListExpr','type':{'qualType':'unsigned int[2]'},'array_filler':[
            {'kind':'ImplicitValueInitExpr','type':{'qualType':'unsigned int'}},conversion(literal(9),'unsigned int','IntegralCast')]}]
        tu['inner'][1]['inner'][0]['inner'].insert(0,{'kind':'DeclStmt','inner':[node]})
        pin=STAGE['digest']({'source_sha256':hashlib.sha256(self.source.read_bytes()).hexdigest(),
            'caller':kw['caller'],'local_id':'array','declaration_sha256':STAGE['digest'](node)})
        obj={'object_id':'array','guest_base':4096,'physical_base':65536,'extent':2,'dtype':0,'source_pin':pin}
        stage=STAGE['Stager'](API,DISPATCH,tu,atlas=DISPATCH['prepare_atlas']([obj]),live_local_ids={'array'},
            **{k:v for k,v in kw.items() if k!='call_range'})
        stage.register_local('array',ordinary_object='array');out=stage.array_initializer('array')
        self.assertEqual(len(out['statements']),2)
        self.assertIn('UINT64_C(9)',out['statements'][0]);self.assertIn('((unsigned int)0)',out['statements'][1])
        self.assertTrue(out['ordinary_allocation_ownership_binding_required']);self.assertFalse(out['model_reset_called'])
        node['inner'][0]['array_filler'][0]['kind']='CallExpr'
        with self.assertRaises(STAGE['Refused']):stage.array_initializer('array')


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'skips':len(result.skipped),'actual_compiler_or_project_child':False},sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
