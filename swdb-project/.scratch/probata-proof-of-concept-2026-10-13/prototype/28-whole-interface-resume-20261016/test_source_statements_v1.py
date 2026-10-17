"""2026-10-16 ET. Hand-authored AST protocol controls, never actual source admission."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest


def deny(event,args):
    if event.startswith(('subprocess.','os.exec','os.spawn','os.posix_spawn','os.fork','socket.')) or event in {'os.system','ctypes.dlopen'}:
        raise RuntimeError('source statement controls refuse '+event)


sys.addaudithook(deny)
HERE=Path(__file__).resolve().parent


def own(name):
    path=HERE/name;ns={'__file__':str(path),'__name__':'inert_statement_fixture'}
    exec(compile(ast.parse(path.read_bytes()),str(path),'exec'),ns)
    return ns


API=own('whole_interface_v4.py');DISPATCH=own('source_dispatch_v3.py')
STAGE=own('source_argument_staging_v2.py');STATEMENTS=own('source_statements_v1.py')
BASE=own('test_whole_interface.py');BASE['API']=API
ABI=BASE['ABI']


def lit(number,typ='int'):
    return {'kind':'IntegerLiteral','type':{'qualType':typ},'value':str(number)}


def ref(ident,typ):
    return {'kind':'DeclRefExpr','type':{'qualType':typ},'referencedDecl':{'kind':'VarDecl','id':ident}}


def cast(node,typ,kind='LValueToRValue'):
    return {'kind':'ImplicitCastExpr','castKind':kind,'type':{'qualType':typ},'inner':[node]}


class Controls(BASE['Controls']):
    def make(self,mutate=None,builtin=False):
        row=next(row for row in self.declarations if row['name']=='get_new_tile')
        tu,_=self.fixture(row)
        source='''unsigned int staged() {
  unsigned int data[2] = {1, 2};
  int tile = get_new_tile<unsigned int>();
  data[0] = 7;
  unsigned int got = data[0];
  assert(got == 7);
  return got;
}
'''
        self.source.write_text(source)
        header=self.source.parent/'selected-assert.h'
        header.write_text('#define assert(expr) (static_cast <bool> (expr) ? void (0) : __assert_fail (#expr, '+('__builtin_FILE (), __builtin_LINE ()' if builtin else '__FILE__, __LINE__')+', __ASSERT_FUNCTION))\n')
        pin={'path':str(header),'bytes':header.stat().st_size,'sha256':hashlib.sha256(header.read_bytes()).hexdigest()}
        def span(begin,end,macro=False):
            left={'offset':begin,'_file':str(self.source)};right={'offset':end-1,'tokLen':1,'_file':str(self.source)}
            return {'begin':{'spellingLoc':left} if macro else left,'end':{'spellingLoc':right} if macro else right}
        def locnode(ident,typ,spelling,init):
            start=source.index(spelling)
            return {'kind':'VarDecl','id':ident,'name':ident,'type':{'qualType':typ},'loc':{'_file':str(self.source)},
                    'range':span(start,start+len(spelling)),'inner':[init]}
        data=locnode('data','unsigned int[2]','unsigned int data[2] = {1, 2}',
            {'kind':'InitListExpr','type':{'qualType':'unsigned int[2]'},'inner':[cast(lit(1),'unsigned int','IntegralCast'),cast(lit(2),'unsigned int','IntegralCast')]})
        call=tu['inner'][1]['inner'][0]['inner'][0]
        calltext='get_new_tile<unsigned int>()';at=source.index(calltext);call['range']=span(at,at+len(calltext))
        tile=locnode('tile','int','int tile = '+calltext,call)
        def access(at):
            return {'kind':'ArraySubscriptExpr','type':{'qualType':'unsigned int'},'range':span(at,at+len('data[0]')),
                    'inner':[cast(ref('data','unsigned int[2]'),'unsigned int *','ArrayToPointerDecay'),lit(0)]}
        store_at=source.index('data[0] = 7')
        store={'kind':'BinaryOperator','opcode':'=','type':{'qualType':'unsigned int'},'range':span(store_at,store_at+len('data[0] = 7')),
               'inner':[access(store_at),cast(lit(7),'unsigned int','IntegralCast')]}
        load_at=source.index('data[0]',source.index('unsigned int got'))
        got=locnode('got','unsigned int','unsigned int got = data[0]',cast(access(load_at),'unsigned int'))
        assertion_at=source.index('assert(');pred_at=source.index('got == 7')
        pred={'kind':'BinaryOperator','opcode':'==','type':{'qualType':'bool'},'range':span(pred_at,pred_at+len('got == 7'),True),
              'inner':[cast(ref('got','unsigned int'),'unsigned int'),cast(lit(7),'unsigned int','IntegralCast')]}
        callee={'kind':'ImplicitCastExpr','castKind':'FunctionToPointerDecay','inner':[{'kind':'DeclRefExpr','referencedDecl':{'kind':'FunctionDecl','name':'__assert_fail','id':'assert-fail'}}]}
        def string(value):return {'kind':'StringLiteral','type':{'qualType':'const char['+str(len(value)+1)+']'},'value':json.dumps(value)}
        failure={'kind':'CallExpr','range':{'begin':{'expansionLoc':{'offset':assertion_at}},'end':{'expansionLoc':{'offset':assertion_at,'tokLen':6}}},'inner':[callee,string('got == 7'),string(str(self.source)),lit(6),
            {'kind':'PredefinedExpr','name':'__PRETTY_FUNCTION__','inner':[string('unsigned int staged()')]}]}
        if builtin:
            for index,(name,typ) in enumerate((('__builtin_FILE','const char *'),('__builtin_LINE','unsigned int')),2):
                htext=header.read_text();start=htext.index(name);end=htext.index(')',start)
                failure['inner'][index]={'id':'0xa'+str(index),'kind':'SourceLocExpr','valueCategory':'prvalue','type':{'qualType':typ},
                    'range':{'begin':{'spellingLoc':{'offset':start,'_file':str(header)},'expansionLoc':{'offset':assertion_at,'_file':str(self.source)}},
                             'end':{'spellingLoc':{'offset':end,'tokLen':1,'_file':str(header)},'expansionLoc':{'offset':assertion_at,'_file':str(self.source)}}}}
        assertion={'kind':'ParenExpr','range':{'begin':{'expansionLoc':{'offset':assertion_at,'_file':str(self.source)}},
                                              'end':{'expansionLoc':{'offset':assertion_at,'tokLen':6,'_file':str(self.source)}}},
            'inner':[{'kind':'ConditionalOperator','inner':[{'kind':'CXXStaticCastExpr','castKind':'NoOp','type':{'qualType':'bool'},'inner':[pred]},
                {'kind':'CXXFunctionalCastExpr','castKind':'ToVoid','inner':[lit(0)]},failure]}]}
        nodes=[{'kind':'DeclStmt','inner':[data]},{'kind':'DeclStmt','inner':[tile]},store,{'kind':'DeclStmt','inner':[got]},assertion,
               {'kind':'ReturnStmt','inner':[cast(ref('got','unsigned int'),'unsigned int')]}]
        owner=tu['inner'][1];owner.update(name='staged',mangledName='_Z6stagedv',loc={'_file':str(self.source)},
            type={'qualType':'unsigned int ()'},range=span(0,len(source)-1),inner=[{'kind':'CompoundStmt','range':span(source.index('{'),source.rindex('}')+1),'inner':nodes}])
        tu['inner'].append({'kind':'FunctionDecl','id':'assert-fail','name':'__assert_fail','loc':{'_file':str(header)},'inner':[{'kind':'NoReturnAttr'}]})
        data_info={'data':data,'tile':tile,'got':got,'store':store,'assertion':assertion,'predicate':pred,'failure':failure,'call':call,'nodes':nodes,'owner':owner}
        if mutate:mutate(tu,data_info)
        obj={'object_id':'original-data','guest_base':4096,'physical_base':65536,'extent':2,'dtype':0,
             'source_pin':STAGE['digest']({'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'caller':owner['mangledName'],
                                         'local_id':'data','declaration_sha256':STAGE['digest'](data)})}
        atlas=DISPATCH['prepare_atlas']([obj])
        kwargs={'caller':owner['mangledName'],'call_range':API['_span'](call),'source_path':self.source,'source_text':source,
                'declarations':self.declarations,'abi':ABI}
        binding=API['bind_call'](tu,**kwargs)
        stage=STAGE['Stager'](API,DISPATCH,tu,atlas=atlas,live_local_ids=set(),**{k:v for k,v in kwargs.items() if k!='call_range'})
        preparation={'normalized_full_tu_sha256':STAGE['digest'](tu),'original_source_sha256':hashlib.sha256(source.encode()).hexdigest(),'calls':[binding]}
        lower=STATEMENTS['Lowerer'](stage,preparation,assertion_header_pin=pin)
        return lower,data_info

    def test_07_complete_scoped_source_preserves_calls_writes_assertion_and_cleanup(self):
        lower,_=self.make();out=lower.lower()
        self.assertEqual(len(out['call_bindings']),1)
        self.assertEqual(len(out['assertions']),1)
        self.assertEqual(len(out['CPU_projections']),3)
        self.assertIn('dws_cpu_store_u32(owned_thread,',out['text'])
        self.assertIn('dws_cpu_load_u32(owned_thread,',out['text'])
        self.assertIn('"source-assert-L6"',out['text'])
        self.assertIn('source-object-lifetime-pending',out['text'])
        self.assertIn('dws_source_object_leave(0);\n  return src_return_',out['text'])
        self.assertNotIn('dxm_reset(',out['text']);self.assertNotIn('__CPROVER_assume',out['text'])
        self.assertFalse(out['public_admission']);self.assertTrue(out['receiver_state_and_harness_draw_binding_required'])
        with self.assertRaises(STATEMENTS['Refused']):lower.lower()

    def test_08_assertion_predicate_diagnostics_and_failure_effect_mutations_refuse(self):
        for index,value in ((1,'changed'),(2,'/wrong.cpp'),(4,'wrong function')):
            def mutate(tu,info,index=index,value=value):
                if index==4:info['failure']['inner'][4]['inner'][0]['value']=json.dumps(value)
                else:info['failure']['inner'][index]['value']=json.dumps(value)
            lower,_=self.make(mutate)
            with self.assertRaises(STATEMENTS['Refused']):lower.lower()
        for mutation in (
            lambda tu,i:i['failure']['inner'][3].update(value='99'),
            lambda tu,i:i['predicate']['range']['end']['spellingLoc'].update(offset=0),
            lambda tu,i:i['assertion']['inner'][0]['inner'][1]['inner'][0].update(value='1'),
            lambda tu,i:i['failure']['inner'][0]['inner'][0]['referencedDecl'].update(id='wrong'),
            lambda tu,i:i['nodes'].remove(i['assertion']),
            lambda tu,i:i['nodes'].insert(-1,copy.deepcopy(i['assertion'])),
        ):
            lower,_=self.make(mutation)
            with self.assertRaises(STATEMENTS['Refused']):lower.lower()

    def test_09_missing_call_unknown_effect_and_source_change_do_not_succeed(self):
        with self.assertRaises(API['Refused']):
            self.make(lambda tu,i:i['nodes'].remove(next(n for n in i['nodes'] if n.get('kind')=='DeclStmt' and n['inner'][0]['id']=='tile')))
        lower,_=self.make();lower.expected[(0,1)]={'unbound':'missing site'}
        with self.assertRaises(STATEMENTS['Refused']):lower.lower()
        for kind in ('CXXNewExpr','CXXDeleteExpr','AsmStmt','ForStmt'):
            lower,_=self.make(lambda tu,i,kind=kind:i['nodes'].insert(-1,{'kind':kind}))
            with self.assertRaises(STATEMENTS['Refused']):lower.lower()
        lower,_=self.make();self.source.write_text(self.source.read_text()+'// changed\n')
        with self.assertRaises((STATEMENTS['Refused'],STAGE['Refused'])):lower.lower()

    def test_10_copied_descriptor_cannot_outlive_its_exact_object_scope(self):
        lower,info=self.make()
        # Synthetic preparation state models an outer descriptor retaining an
        # inner object's identity. No runtime/native claim follows from it.
        lower.frames=[{'ids':{'outer-copy'},'arrays':[]}]
        lower.origins['outer-copy']={'inner-array'}
        copied=ref('outer-copy','unsigned int *')
        with self.assertRaisesRegex(STATEMENTS['Refused'],'outside its exact active source scope'):lower.check_origins(copied)
        lower.frames.append({'ids':{'inner-array'},'arrays':['inner-array']})
        lower.check_origins(copied)
        lower.frames.pop()
        with self.assertRaises(STATEMENTS['Refused']):lower.check_origins(copied)

    def test_11_pointer_assignment_is_refused_before_it_can_escape(self):
        def mutate(tu,i):
            descriptor=cast(ref('data','unsigned int[2]'),'unsigned int *','ArrayToPointerDecay')
            local={'kind':'VarDecl','id':'alias','name':'alias','type':{'qualType':'unsigned int *'},
                'loc':{'_file':str(self.source)},'range':{'begin':{'offset':0},'end':{'offset':0,'tokLen':1}},'inner':[descriptor]}
            i['nodes'].insert(1,{'kind':'DeclStmt','inner':[local]})
            i['nodes'].insert(-1,{'kind':'BinaryOperator','opcode':'=','type':{'qualType':'unsigned int *'},
                'inner':[ref('alias','unsigned int *'),copy.deepcopy(descriptor)]})
        lower,_=self.make(mutate)
        with self.assertRaisesRegex(STATEMENTS['Refused'],'pointer assignment'):lower.lower()

    def test_12_scalar_if_while_and_loop_exits_preserve_explicit_control(self):
        def mutate(tu,i):
            condition={'kind':'BinaryOperator','opcode':'<','type':{'qualType':'bool'},
                'inner':[cast(ref('got','unsigned int'),'unsigned int'),cast(lit(9),'unsigned int','IntegralCast')]}
            control={'kind':'WhileStmt','inner':[condition,{'kind':'CompoundStmt','inner':[{'kind':'IfStmt','hasElse':True,
                'inner':[copy.deepcopy(condition),{'kind':'CompoundStmt','inner':[{'kind':'BreakStmt'}]},
                         {'kind':'CompoundStmt','inner':[{'kind':'ContinueStmt'}]}]}]}]}
            i['nodes'].insert(-1,control)
        lower,_=self.make(mutate);text=lower.lower()['text']
        self.assertIn('while (',text);self.assertIn('if (',text);self.assertIn('} else {',text)
        self.assertIn('break;',text);self.assertIn('continue;',text)
        self.assertNotIn('dws_source_object_leave(0);\n      break',text)

    def test_13_assertion_lexical_inventory_ignores_comment_tokens_and_rejects_quoted_predicates(self):
        text='/* assert(fake) */\nassert(real == 7); // assert(fake)\n'
        sites=STATEMENTS['assertion_sites'](text,0,len(text))
        self.assertEqual([(x['predicate'],x['line']) for x in sites],[('real == 7',2)])
        for text in ('assert("effect");','assert(/*x*/real);','assert(real\\\n==7);'):
            with self.assertRaises(STATEMENTS['Refused']):STATEMENTS['assertion_sites'](text,0,len(text))

    def test_14_builtin_source_location_diagnostics_bind_original_buffers_without_offset_join(self):
        lower,_=self.make(builtin=True);self.assertEqual(len(lower.lower()['assertions']),1)
        for mutation in (
            lambda tu,i:i['failure']['inner'][2]['type'].update(qualType='char *'),
            lambda tu,i:i['failure']['inner'][3]['range']['begin']['expansionLoc'].update(offset=0),
            lambda tu,i:i['failure']['inner'][2]['range']['end']['spellingLoc'].update(tokLen=2),
            lambda tu,i:i['failure']['inner'][2].update(inner=[lit(0)]),
        ):
            lower,_=self.make(mutation,builtin=True)
            with self.assertRaises(STATEMENTS['Refused']):lower.lower()


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    print(json.dumps({'date':'2026-10-16 ET','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
        'skips':len(result.skipped),'actual_compiler_or_project_child':False},sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)
