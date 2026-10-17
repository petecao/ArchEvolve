"""2026-10-16 ET. Inert scoped source-to-checked-C preparation.

No project imports or tools. All compiler/source/model/receiver/draw admission
remains external. The closed scope rejects pointer escape, effectful API argument
expressions, class/heap/unknown calls and missing/altered assertion evidence.
"""
import ast
import hashlib
import json
from pathlib import Path
import re
import stat


class Refused(ValueError):
    pass


def need(ok,message):
    if not ok: raise Refused(message)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def walk(node):
    yield node
    for child in node.get('inner',[]):
        if isinstance(child,dict):yield from walk(child)


def children(node):
    value=node.get('inner',[])
    need(isinstance(value,list) and all(isinstance(item,dict) for item in value),'exact original children required')
    return value


def assertion_sites(source,start,end):
    """Closed lexical assertion inventory, excluding comments/string contents."""
    sites=[];at=start
    while at<end:
        if source.startswith('//',at):
            stop=source.find('\n',at+2);at=end if stop<0 else stop+1;continue
        if source.startswith('/*',at):
            stop=source.find('*/',at+2);need(stop>=0,'unterminated source comment');at=stop+2;continue
        if source[at] in "\"'":
            quote=source[at];at+=1
            while at<end:
                if source[at]=='\\':at+=2
                elif source[at]==quote:at+=1;break
                else:at+=1
            continue
        match=re.match(r'[A-Za-z_]\w*',source[at:])
        if not match:at+=1;continue
        token=match[0];begin=at;at+=len(token)
        if token!='assert':continue
        while at<end and source[at].isspace():at+=1
        need(at<end and source[at]=='(','unhandled source assert token')
        at+=1;predicate=at;depth=1
        while at<end and depth:
            need(source[at] not in "\"'\\" and not source.startswith(('/*','//'),at),
                 'assertion predicate requires closed ordinary scalar spelling')
            if source[at]=='(':depth+=1
            elif source[at]==')':depth-=1
            if depth:at+=1
        need(depth==0,'unterminated assertion predicate')
        stop=at
        while predicate<stop and source[predicate].isspace():predicate+=1
        while stop>predicate and source[stop-1].isspace():stop-=1
        need(predicate<stop,'empty source assertion')
        sites.append({'offset':begin,'predicate_range':[predicate,stop],'predicate':source[predicate:stop],
                      'line':source.count('\n',0,begin)+1})
        at+=1
    return sites


def _callee(node):
    inner=children(node)
    if node.get('kind')!='CallExpr' or not inner:return None,None
    leaf=inner[0]
    while leaf.get('kind') in {'ImplicitCastExpr','ParenExpr'} and len(children(leaf))==1:leaf=children(leaf)[0]
    reference=leaf.get('referencedDecl',{})
    return reference.get('name'),reference.get('id')


def _unary_wrappers(node,kinds):
    while node.get('kind') in kinds and len(children(node))==1:node=children(node)[0]
    return node


def _literal_string(node):
    while node.get('kind') in {'ImplicitCastExpr','ParenExpr','UnaryOperator'}:
        need(len(children(node))==1,'one original diagnostic wrapper operand required')
        if node['kind']=='ImplicitCastExpr':need(node.get('castKind') in {'NoOp','ArrayToPointerDecay'},'diagnostic conversion differs')
        if node['kind']=='UnaryOperator':need(node.get('opcode')=='__extension__','diagnostic has an unbound unary effect')
        node=children(node)[0]
    need(node.get('kind')=='StringLiteral' and not children(node) and isinstance(node.get('value'),str),'original assertion string diagnostic required')
    try:value=ast.literal_eval(node['value'])
    except (ValueError,SyntaxError) as error:raise Refused('malformed assertion string diagnostic') from error
    need(isinstance(value,str),'ordinary assertion string required')
    need(node.get('type',{}).get('qualType')=='const char['+str(len(value)+1)+']','assertion literal character extent differs')
    return value


def lifetime_helper():
    return '''/* Original automatic object scope, checked without reset/ownership grants. */
static void dws_source_object_leave(unsigned object) {
  struct dws_pointer p=dws_object_pointer(object);
  uint64_t bytes=dws_pointer_bytes(p),begin=dws_objects[object].physical;
  for(unsigned i=0;i<dxc_count;++i) {
    const struct dxc_command *c=&dxc_commands[i];
    DXM_CHECK(!(c->pending && c->access && begin<c->end && c->begin<begin+bytes),"source-object-lifetime-pending");
  }
}
'''


class Lowerer:
    def __init__(self,stager,unit_preparation,*,assertion_header_pin):
        self.stage=stager;self.api=stager.api;self.source=stager.source['source_text'];self.tu=stager.tu
        need(unit_preparation.get('normalized_full_tu_sha256')==digest(self.tu)
             and unit_preparation.get('original_source_sha256')==hashlib.sha256(self.source.encode()).hexdigest(),
             'actual unit/source preparation linkage required')
        self.expected={tuple(row['call_range']):row for row in unit_preparation['calls'] if row['caller_mangled']==stager.source['caller']}
        need(len(self.expected)==len([row for row in unit_preparation['calls'] if row['caller_mangled']==stager.source['caller']]),'distinct original source call sites required')
        self.calls=[];self.accesses=[];self.assertions=[];self.lines=[];self.frames=[];self.origins={};self.opaque={};self.serial=0
        self.indent=0;self.loops=[];self.emitted=False
        need(not any(node.get('kind')=='ParmVarDecl' for node in children(stager.owner)), 'first source scope has no original function parameters')
        need(not stager.locals and not stager.live,'statement consumer owns initially empty local scope')
        bodies=[node for node in children(stager.owner) if node.get('kind')=='CompoundStmt']
        need(len(bodies)==1,'one original function body required');self.body=bodies[0]
        self.body_range=self.api['_span'](self.body)
        self.sites=assertion_sites(self.source,*self.body_range)
        self._assertion_profile(assertion_header_pin)
        typ=stager.owner.get('type',{}).get('qualType','')
        match=re.fullmatch(r'(.+?)\s*\(\)',typ)
        need(match,'exact no-parameter source function type required')
        returns=match[1]
        if returns.startswith('std::') and returns[5:] in stager.abi['canonical_types']:
            returns=stager.abi['canonical_types'][returns[5:]]
        need(stager._ctype(returns) is not None,'exact ordinary scalar source return type required')
        self.returns=stager._ctype(returns)

    def _assertion_profile(self,pin):
        need(isinstance(pin,dict) and set(pin)=={'path','bytes','sha256'},'selected assertion header physical pin required')
        path=Path(pin['path']);before=path.lstat()
        need(stat.S_ISREG(before.st_mode) and path.resolve(strict=True)==path,'canonical physical assertion header required')
        raw=path.read_bytes()
        need(path.lstat()==before and len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'assertion header pin changed')
        text=raw.decode('ascii').replace('\\\n','')
        macro=re.compile(r'#\s*define\s+assert\(expr\)\s*\(static_cast\s*<bool>\s*\(expr\)\s*\?\s*void\s*\(0\)\s*:\s*__assert_fail\s*\(#expr,\s*(?P<file>__FILE__|__builtin_FILE\s*\(\s*\)),\s*(?P<line>__LINE__|__builtin_LINE\s*\(\s*\)),\s*__ASSERT_FUNCTION\)\)')
        matches=list(macro.finditer(text));need(len(matches)==1,'exact selected Linux C++ assertion macro profile required')
        builtin=matches[0]['file'].startswith('__builtin_')
        need(matches[0]['line'].startswith('__builtin_')==builtin,'mixed assertion file/line diagnostic profile refuses')
        self.builtin_source_location=builtin;self.assertion_header_bytes=raw
        definitions=[]
        def global_failures(node,scope=()):
            kind=node.get('kind')
            if kind=='FunctionDecl' and node.get('name')=='__assert_fail' and node.get('loc',{}).get('_file',node.get('loc',{}).get('file'))==str(path):
                need(not scope,'assertion failure declaration must have original global scope');definitions.append(node)
            if kind in {'NamespaceDecl','CXXRecordDecl','RecordDecl','FunctionDecl'}:scope=scope+(kind,)
            for child in children(node):global_failures(child,scope)
        global_failures(self.tu)
        need(len(definitions)==1 and definitions[0].get('id'),'one selected global assertion failure declaration required')
        need(not any(node.get('kind')=='CompoundStmt' for node in children(definitions[0])),'assertion failure must be the admitted external noreturn path')
        need(any(node.get('kind')=='NoReturnAttr' for node in children(definitions[0])),'original failure declaration must be noreturn')
        self.assertion_header=pin;self.failure_id=definitions[0]['id']

    def source_location_diagnostic(self,node,site,*,builtin,result_type):
        """Exact original-TU builtin diagnostic, never executable source code.

        SourceLocExpr shape follows the source-owned initialized observer. Here
        original header spelling and caller expansion coordinates replace frozen
        preprocessor-marker reasoning: no offsets are joined across buffers.
        """
        need(set(node)=={'id','kind','range','type','valueCategory'} and node.get('kind')=='SourceLocExpr'
             and isinstance(node.get('id'),str) and re.fullmatch('0x[0-9a-f]+',node['id'])
             and node.get('valueCategory')=='prvalue' and node.get('type')=={'qualType':result_type},
             'exact typed source-location diagnostic leaf required')
        need(set(node.get('range',{}))=={'begin','end'},'complete source-location diagnostic range required')
        points=[node['range'][key] for key in ('begin','end')]
        for point in points:
            spelling,expansion=point.get('spellingLoc',{}),point.get('expansionLoc',{})
            need(spelling.get('_file',spelling.get('file'))==self.assertion_header['path']
                 and expansion.get('_file',expansion.get('file'))==str(Path(self.stage.source['source_path']).resolve())
                 and expansion.get('offset')==site['offset'],'source-location builtin is not bound to the original header/caller expansion')
        begin,end=(point['spellingLoc'] for point in points)
        start,stop=begin.get('offset'),end.get('offset')
        need(type(start) is int and type(stop) is int and type(end.get('tokLen')) is int and end['tokLen']>0
             and 0<=start<=stop and stop+end['tokLen']<=len(self.assertion_header_bytes),'source-location original header span differs')
        text=self.assertion_header_bytes[start:stop+end['tokLen']].decode('ascii')
        need(re.sub(r'\s+','',text)==builtin+'()','source-location builtin spelling differs')

    def emit(self,text):self.lines.append('  '*self.indent+text)

    def active_arrays(self):return {ident for frame in self.frames for ident in frame['arrays']}

    def check_origins(self,node):
        for item in walk(node):
            if item.get('kind')!='DeclRefExpr':continue
            ident=item.get('referencedDecl',{}).get('id')
            if ident in self.opaque:raise Refused('noncacheable pointer is admitted only for explicit discarded address observation')
            if ident in self.origins:
                need(self.origins[ident]<=self.active_arrays(),'descriptor points to an automatic object outside its exact active source scope')

    def pure(self,node):
        self.check_origins(node)
        return self.stage.expression(node)

    def value(self,node,*,whole_call=False):
        self.check_origins(node)
        kind=node.get('kind');inner=children(node)
        if kind=='CallExpr':
            need(whole_call,'nested API calls require an independently checked sequencing route')
            key=tuple(self.api['_span'](node));need(key in self.expected,'unknown original source call refuses')
            result=self.stage.call(self.expected[key]);self.calls.append(result)
            for line in result['staging_statements']:self.emit(line)
            binding=result['binding'];name=binding['name']
            category='pointer-descriptor' if result['source_pointer_return'] else 'exact-scalar'
            return {'expression':result['model_expression'],'category':category,'origins':set(),
                    'dtype':binding['dtype'],'source_call':name}
        if kind=='ArraySubscriptExpr':
            result=self.stage.cpu_load(node);self.accesses.append(result)
            return {'expression':result['expression'],'category':'exact-scalar','origins':set()}
        if kind=='ImplicitCastExpr' and len(inner)==1 and node.get('castKind')=='LValueToRValue' and inner[0].get('kind')=='ArraySubscriptExpr':
            return self.value(inner[0])
        if kind in {'ImplicitCastExpr','ParenExpr'} and len(inner)==1 and any(item.get('kind') in {'CallExpr','ArraySubscriptExpr'} for item in walk(node)):
            need(kind=='ParenExpr' or node.get('castKind') in {'NoOp','LValueToRValue','IntegralCast','IntegralToFloating','FloatingCast'},'checked scalar wrapper around original operation required')
            value=self.value(inner[0],whole_call=whole_call)
            if kind=='ImplicitCastExpr' and value['category']=='exact-scalar':
                typ=self.stage._ctype(node.get('type',{}).get('desugaredQualType',node.get('type',{}).get('qualType','')))
                need(typ,'exact scalar operation conversion required');value=dict(value,expression='(('+typ+')('+value['expression']+'))')
            return value
        if kind=='BinaryOperator' and node.get('opcode') in {'+','-','*','/','%','==','!=','<','<=','>','>=','&&','||','&','|','^','<<','>>'} and len(inner)==2:
            actual_type=node.get('type',{}).get('desugaredQualType',node.get('type',{}).get('qualType',''))
            if actual_type.endswith('*'):
                value=self.pure(node);origins=set()
                for item in walk(node):
                    if item.get('kind')=='DeclRefExpr':origins.update(self.origins.get(item.get('referencedDecl',{}).get('id'),set()))
                return dict(value,origins=origins)
            reads=[item for item in walk(node) if item.get('kind')=='ArraySubscriptExpr']
            if len(reads)>1 and node['opcode'] not in {'&&','||'}:
                for access in reads:
                    refs=[item.get('referencedDecl',{}).get('id') for item in walk(children(access)[0]) if item.get('kind')=='DeclRefExpr']
                    need(refs and all(self.origins.get(ident) for ident in refs),'unsequenced multiple tile/stateful CPU reads require an independent source order route')
            # Keep original lazy/eager C expression structure. API calls are not
            # allowed below an operator, so no statement prelude can escape it.
            left,right=(self.value(item) for item in inner)
            need(left['category']==right['category']=='exact-scalar','pointer operations use the dedicated checked pure path')
            return {'expression':'(('+left['expression']+') '+node['opcode']+' ('+right['expression']+'))','category':'exact-scalar','origins':set()}
        value=self.pure(node)
        origins=set()
        for item in walk(node):
            if item.get('kind')=='DeclRefExpr':origins.update(self.origins.get(item.get('referencedDecl',{}).get('id'),set()))
        return dict(value,origins=origins)

    def _leave(self,frames):
        for frame in reversed(frames):
            for ident in reversed(frame['arrays']):self.emit('dws_source_object_leave('+str(self.stage.locals[ident]['object_index'])+');')

    def block(self,node):
        need(node.get('kind')=='CompoundStmt','source control body must have an explicit compound scope')
        frame={'ids':set(),'arrays':[]};self.frames.append(frame)
        for item in children(node):self.statement(item)
        self._leave([frame]);self.stage.live-=frame['ids'];self.frames.pop()

    def local(self,node):
        need(node.get('kind')=='VarDecl','only scalar/descriptor/array declarations are admitted')
        self.stage._owned(node)
        ident=node.get('id');inner=children(node)
        need(node.get('storageClass') not in {'static','extern'} and not node.get('tls')
             and not any(item.get('kind','').endswith('Attr') for item in inner),'automatic unattributed source local required')
        typ=node.get('type',{}).get('desugaredQualType',node.get('type',{}).get('qualType',''))
        need(len(inner)==1,'one explicit original initializer required')
        if re.fullmatch(r'volatile .+?\s*\*',typ):
            loc=node.get('loc',{})
            need(loc.get('_file',loc.get('file'))==str(Path(self.stage.source['source_path']).resolve()),'opaque local original physical file required')
            self.api['_span'](node)
            value=self.value(inner[0],whole_call=True)
            need(value.get('source_call')=='get_noncacheable_tile_pointer' and value['category']=='pointer-descriptor', 'noncacheable address only from the exact original getter')
            name='src_opaque_'+str(self.serial);self.serial+=1
            self.opaque[ident]={'name':name,'source_declaration_sha256':digest(node)}
            self.emit('struct dws_pointer '+name+' = '+value['expression']+';');self.frames[-1]['ids'].add(ident);return
        array=re.fullmatch(r'(.+?)\s*\[([1-9][0-9]*)\]',typ)
        ordinary=None
        if array:
            need(not self.loops,'automatic arrays inside loops require separate per-iteration provenance admission')
            expected=digest({'source_sha256':hashlib.sha256(self.source.encode()).hexdigest(),'caller':self.stage.source['caller'],
                             'local_id':ident,'declaration_sha256':digest(node)})
            found=[row['object_id'] for row in self.stage.atlas['objects'] if row['source_pin']==expected]
            need(len(found)==1,'one source-owned ordinary object projection required');ordinary=found[0]
        local=self.stage.register_local(ident,ordinary_object=ordinary);self.frames[-1]['ids'].add(ident)
        if array:
            self.frames[-1]['arrays'].append(ident);self.origins[ident]={ident}
            self.emit(local['c_type']+' '+local['name']+' = '+local['ordinary_descriptor_initializer']+';')
            initialization=self.stage.array_initializer(ident);self.accesses.append(initialization)
            for line in initialization['statements']:self.emit(line)
        else:
            value=self.value(inner[0],whole_call=True)
            need(value['category']==local['category'],'source initializer scalar/descriptor category differs')
            if value['category']=='pointer-descriptor':
                need(value['origins']<=self.active_arrays(),'pointer copy escapes its source object scope')
                self.origins[ident]=set(value['origins'])
            self.emit(local['c_type']+' '+local['name']+' = '+value['expression']+';')
        self.stage.live.add(ident)

    def assertion(self,node):
        # Fail closed on actual macro-shape differences. The declaration, header,
        # original condition span and every failure diagnostic are bound together.
        macro_begin=node.get('range',{}).get('begin',{}).get('expansionLoc',{})
        offset=macro_begin.get('offset')
        matches=[site for site in self.sites if site['offset']==offset]
        need(len(matches)==1 and offset not in {row['offset'] for row in self.assertions},'one original unconsumed assertion site required')
        site=matches[0];root=_unary_wrappers(node,{'ParenExpr','ExprWithCleanups'})
        need(root.get('kind')=='ConditionalOperator' and len(children(root))==3,'exact observed Linux assertion conditional required')
        condition,success,failure=children(root)
        need(condition.get('kind')=='CXXStaticCastExpr' and condition.get('castKind') in {'NoOp','IntegralToBoolean'}
             and len(children(condition))==1 and condition.get('type',{}).get('qualType')=='bool','original bool assertion conversion required')
        predicate=children(condition)[0]
        while predicate.get('kind')=='ParenExpr' and len(children(predicate))==1:
            points=[predicate.get('range',{}).get(k,{}) for k in ('begin','end')]
            if all('spellingLoc' in point for point in points) and all(point['spellingLoc'].get('_file',point['spellingLoc'].get('file'))==str(Path(self.stage.source['source_path']).resolve()) for point in points):break
            predicate=children(predicate)[0]
        points=[predicate.get('range',{}).get(k,{}) for k in ('begin','end')]
        spelling=[point.get('spellingLoc',point) for point in points]
        need(all(point.get('_file',point.get('file'))==str(Path(self.stage.source['source_path']).resolve()) for point in spelling),'assertion operand original physical source required')
        begin,end=spelling
        need([begin.get('offset'),end.get('offset',-1)+end.get('tokLen',0)]==site['predicate_range'],'assertion operand differs from original complete predicate span')
        need(success.get('kind')=='CXXFunctionalCastExpr' and success.get('castKind')=='ToVoid' and len(children(success))==1
             and children(success)[0].get('kind')=='IntegerLiteral' and children(success)[0].get('value')=='0','original assertion success arm must be void(0)')
        need(_callee(failure)==('__assert_fail',self.failure_id) and len(children(failure))==5,'exact original assertion failure path required')
        args=children(failure)[1:]
        need(_literal_string(args[0])==' '.join(site['predicate'].split()),'assertion stringized predicate differs')
        if self.builtin_source_location:
            self.source_location_diagnostic(args[1],site,builtin='__builtin_FILE',result_type='const char *')
            self.source_location_diagnostic(args[2],site,builtin='__builtin_LINE',result_type='unsigned int')
        else:
            need(_literal_string(args[1])==str(Path(self.stage.source['source_path']).resolve()),'assertion source-file diagnostic differs')
            line=args[2]
            while line.get('kind') in {'ImplicitCastExpr','ParenExpr'}:
                need(len(children(line))==1 and (line['kind']=='ParenExpr' or line.get('castKind') in {'NoOp','IntegralCast'}),'source line diagnostic conversion differs')
                line=children(line)[0]
            need(line.get('kind')=='IntegerLiteral' and line.get('value')==str(site['line']),'assertion original line diagnostic differs')
        function=args[3]
        while function.get('kind') in {'ImplicitCastExpr','ParenExpr','UnaryOperator'}:
            need(len(children(function))==1,'one assertion function diagnostic wrapper required')
            if function['kind']=='ImplicitCastExpr':need(function.get('castKind') in {'NoOp','ArrayToPointerDecay'},'assertion function conversion differs')
            if function['kind']=='UnaryOperator':need(function.get('opcode')=='__extension__','assertion function has an unbound effect')
            function=children(function)[0]
        need(function.get('kind')=='PredefinedExpr' and function.get('name')=='__PRETTY_FUNCTION__' and len(children(function))==1,'assertion original function diagnostic required')
        function_begin=self.api['_span'](self.stage.owner)[0]
        pretty=' '.join(self.source[function_begin:self.body_range[0]].split())
        need(_literal_string(children(function)[0])==pretty,'assertion function diagnostic differs')
        need(sum(item.get('kind')=='CallExpr' for item in walk(root))==1,'assertion has unbound calls/effects')
        value=self.pure(predicate)
        need(value['category']=='exact-scalar','ordinary original scalar assertion predicate required')
        self.emit('SWDB_CHECK(('+value['expression']+'),"source-assert-L'+str(site['line'])+'");')
        self.assertions.append(dict(site,observed_subtree_sha256=digest(node),failure_declaration_id=self.failure_id))

    def statement(self,node):
        kind=node.get('kind');inner=children(node)
        if node.get('range',{}).get('begin',{}).get('expansionLoc'):
            self.assertion(node);return
        if kind=='DeclStmt':
            for item in inner:self.local(item)
        elif kind=='CompoundStmt':
            self.emit('{');self.indent+=1;self.block(node);self.indent-=1;self.emit('}')
        elif kind=='CallExpr':
            value=self.value(node,whole_call=True);self.emit(value['expression']+';')
        elif kind=='BinaryOperator' and node.get('opcode')=='=' and len(inner)==2:
            if inner[0].get('kind')=='ArraySubscriptExpr':
                self.check_origins(node);out=self.stage.cpu_store(node,discarded_statement=True);self.accesses.append(out)
                for line in out['statements']:self.emit(line)
            else:
                left=self.pure(inner[0]);need(left['category']=='exact-scalar','pointer assignment/escaping copies are refused')
                right=self.value(inner[1]);need(right['category']=='exact-scalar','ordinary scalar assignment required')
                self.emit(left['expression']+' = '+right['expression']+';')
        elif kind in {'CStyleCastExpr','CXXStaticCastExpr'} and node.get('castKind')=='ToVoid' and len(inner)==1:
            leaf=_unary_wrappers(inner[0],{'ImplicitCastExpr','ParenExpr'})
            ident=leaf.get('referencedDecl',{}).get('id')
            need(leaf.get('kind')=='DeclRefExpr' and ident in self.opaque and ident in {item for frame in self.frames for item in frame['ids']},'only live noncacheable address discard admitted')
            self.emit('(void)'+self.opaque[ident]['name']+';')
        elif kind=='ReturnStmt':
            need(len(inner)==1,'ordinary scalar return expression required')
            value=self.value(inner[0]);need(value['category']=='exact-scalar','pointer escape through return is refused')
            name='src_return_'+str(self.serial);self.serial+=1;self.emit(self.returns+' '+name+' = '+value['expression']+';')
            self._leave(self.frames);self.emit('return '+name+';')
        elif kind=='IfStmt':
            need(not any(node.get(key) for key in ('hasInit','hasVar','isConstexpr','isConsteval')) and len(inner) in {2,3},'simple original if required')
            need(bool(node.get('hasElse'))==(len(inner)==3),'original if else-arm census differs')
            cond=self.pure(inner[0]);need(cond['category']=='exact-scalar','scalar if condition required')
            before=set(self.stage.live);self.emit('if ('+cond['expression']+') {');self.indent+=1;self.block(inner[1]);yes=set(self.stage.live)
            self.indent-=1
            if len(inner)==3:
                self.emit('} else {');self.indent+=1;self.stage.live=set(before);self.block(inner[2]);no=set(self.stage.live);self.indent-=1
            else:no=before
            self.stage.live=yes&no;self.emit('}')
        elif kind=='WhileStmt':
            need(not node.get('hasVar') and len(inner)==2,'simple original while required')
            cond=self.pure(inner[0]);need(cond['category']=='exact-scalar','scalar while condition required')
            before=set(self.stage.live);self.loops.append(len(self.frames));self.emit('while ('+cond['expression']+') {');self.indent+=1
            self.block(inner[1]);self.indent-=1;self.emit('}');self.loops.pop();self.stage.live=before
        elif kind in {'BreakStmt','ContinueStmt'}:
            need(not inner and self.loops,'source loop exit requires exact active loop')
            self._leave(self.frames[self.loops[-1]:]);self.emit('break;' if kind=='BreakStmt' else 'continue;')
        elif kind=='UnaryOperator' and node.get('opcode') in {'++','--'} and len(inner)==1:
            value=self.pure(inner[0]);need(value['category']=='exact-scalar','pointer mutation is refused')
            self.emit('('+value['expression']+')'+node['opcode']+';')
        elif kind=='NullStmt' and not inner:self.emit(';')
        else:raise Refused('source statement outside the closed consumer: '+str(kind))

    def lower(self):
        need(not self.emitted,'statement consumer is single use');self.emitted=True
        self.emit(self.returns+' dws_source_program(unsigned '+self.stage.thread+') {');self.indent+=1;self.block(self.body);self.indent-=1;self.emit('}')
        need(sorted(tuple(row['binding']['call_range']) for row in self.calls)==sorted(self.expected),'complete original API call-site inventory required')
        need(sorted(row['offset'] for row in self.assertions)==sorted(row['offset'] for row in self.sites),'every original assertion site must remain checked')
        need(digest(self.tu)==self.stage.tu_pin and Path(self.stage.source['source_path']).read_bytes()==self.source.encode(),'final original source/TU recheck required')
        text=lifetime_helper()+'\n'+'\n'.join(self.lines)+'\n'
        return {'schema':'whole-interface-source-statements-1','text':text,'generated_c_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'original_full_tu_sha256':digest(self.tu),'original_source_sha256':hashlib.sha256(self.source.encode()).hexdigest(),
            'call_bindings':self.calls,'CPU_projections':self.accesses,'assertions':self.assertions,'assertion_header_pin':self.assertion_header,
            'source_scope':'no-parameter scalar-return function, checked locals/arrays, blocks/if/while and closed statements',
            'pointer_escape_policy':'single initialized local copies, active exact origin scopes; assignments/returns/unknown calls refuse',
            'receiver_state_and_harness_draw_binding_required':True,'original_source_RTE_and_unwinding_checks_required':True,
            'actual_compiler_run_inferred':False,'production_integrated':False,'public_admission':False}
