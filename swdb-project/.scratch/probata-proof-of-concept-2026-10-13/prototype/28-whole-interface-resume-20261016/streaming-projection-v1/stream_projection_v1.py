"""2026-10-16 ET. Bounded one-stream AST projection prototype, never a runner.

Explicit producer/parser/normalizer TCB. A certificate cannot reconstruct elided
bytes from hashes. New projection root and reader boundary; never an old raw TU.
No project imports, compiler, subprocess, remote or scientific execution.
"""
import hashlib
import json
import math
import re

STAGE_BYTES=134217728
TOTAL_BYTES=268435456
RESERVE_BYTES=1048576
REFERENCE_FIELDS={'referencedDecl','decl','ownedTagDecl'}
RESERVED_FIELDS={'_file','_line','__projection_node__','__projection_scaffold__'}
SELECTOR_FIELDS={'id','kind','name','mangledName','loc','range','type'}
TYPE_DECL_KINDS={'TypedefDecl','TypeAliasDecl','EnumDecl'}
SCOPE_KINDS={'NamespaceDecl','CXXRecordDecl','RecordDecl','FunctionDecl','FunctionTemplateDecl'}
CALLER_KINDS={'FunctionDecl','CompoundStmt','DeclStmt','VarDecl','CallExpr','DeclRefExpr','ImplicitCastExpr',
 'ParenExpr','CXXStaticCastExpr','CStyleCastExpr','CXXFunctionalCastExpr','UnaryOperator','BinaryOperator',
 'ArraySubscriptExpr','IntegerLiteral','FloatingLiteral','CXXBoolLiteralExpr','CharacterLiteral','ReturnStmt',
 'IfStmt','WhileStmt','BreakStmt','ContinueStmt','NullStmt','InitListExpr','ImplicitValueInitExpr','SourceLocExpr',
 'PredefinedExpr','StringLiteral','ConditionalOperator','ExprWithCleanups','CXXDefaultArgExpr','ConstantExpr','TemplateArgument'}


class Refused(ValueError):
    pass


def need(ok,message):
    if not ok:raise Refused(message)


def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()


def digest(value):return hashlib.sha256(encode(value)).hexdigest()


class Reader:
    def __init__(self,stream,limit):
        self.stream=stream;self.limit=limit;self.buffer=b'';self.at=0;self.position=0
        self.bytes_received=0;self.hash=hashlib.sha256();self.eof=False;self.frames=[]
        self.outside_hash=hashlib.sha256();self.leading=None
        self.charge=None

    def available(self):
        if self.at==len(self.buffer) and not self.eof:
            chunk=self.stream.read(65536)
            need(type(chunk) is bytes and len(chunk)<=65536,'bounded binary original compiler stream required')
            if not chunk:self.eof=True;self.buffer=b'';self.at=0
            else:
                self.bytes_received+=len(chunk)
                need(self.bytes_received<=self.limit,'explicit complete-stream byte allowance exceeded')
                self.hash.update(chunk);self.buffer=chunk;self.at=0
        return self.buffer[self.at:]

    def peek(self):
        part=self.available();return part[0] if part else None

    def take(self,count=1):
        part=self.available();need(0<count<=len(part),'truncated original JSON stream')
        out=part[:count];self.at+=count;self.position+=count
        for frame in self.frames:frame['hash'].update(out)
        if self.frames:self.frames[-1]['gap_hash'].update(out)
        else:self.outside_hash.update(out)
        return out

    def whitespace(self):
        while True:
            part=self.available()
            if not part:return
            match=re.search(rb'[^ \t\r\n]',part)
            count=match.start() if match else len(part)
            if count:self.take(count)
            if match:return

    def literal(self,expected):
        for byte in expected:need(self.take()==bytes([byte]),'malformed JSON token')

    def begin(self):
        self.whitespace();start=self.position
        if self.frames:self.finish_gap(self.frames[-1])
        else:self.leading={'start':0,'end':start,'bytes':start,'sha256':self.outside_hash.hexdigest()}
        self.frames.append({'start':start,'hash':hashlib.sha256(),'gap_start':start,
            'gap_hash':hashlib.sha256(),'partition':[],'partition_charge':0})
        return start

    def finish_gap(self,frame):
        if self.position>frame['gap_start']:
            row={'role':'gap','start':frame['gap_start'],'end':self.position,
                'bytes':self.position-frame['gap_start'],'sha256':frame['gap_hash'].hexdigest()}
            frame['partition'].append(row);count=len(encode(row))+1;frame['partition_charge']+=count
            if self.charge:self.charge(count)

    def end(self,start):
        frame=self.frames[-1];self.finish_gap(frame);self.frames.pop()
        span={'start':start,'end':self.position,'bytes':self.position-start,'sha256':frame['hash'].hexdigest()}
        if self.frames:
            parent=self.frames[-1];row={'role':'child',**span};parent['partition'].append(row)
            count=len(encode(row))+1;parent['partition_charge']+=count
            if self.charge:self.charge(count)
            parent['gap_start']=self.position;parent['gap_hash']=hashlib.sha256()
        else:self.outside_hash=hashlib.sha256()
        return span,frame['partition'],frame['partition_charge']


class Projector:
    def __init__(self,stream,policy):
        need(set(policy)=={'schema','max_stream_bytes','max_depth','max_token_bytes','max_metadata_bytes','max_nodes','max_ids',
            'max_census_rows','max_work_bytes','max_retained_pair_bytes','caller_mangled','caller_source_path','selected_names','api_names','source_and_compiler_receipt_sha256'},'exact projection policy fields required')
        need(policy['schema']=='original-tu-stream-policy-1','new explicit streaming policy required')
        for key in ('max_stream_bytes','max_depth','max_token_bytes','max_metadata_bytes','max_nodes','max_ids','max_census_rows','max_work_bytes','max_retained_pair_bytes'):
            need(type(policy[key]) is int and policy[key]>0,'explicit finite positive parser/stream limits required')
        need(policy['max_depth']<=256 and policy['max_token_bytes']<=1048576 and policy['max_metadata_bytes']<=1048576
             and policy['max_nodes']<=1000000 and policy['max_ids']<=200000 and policy['max_census_rows']<=100000
             and policy['max_work_bytes']<=TOTAL_BYTES-RESERVE_BYTES and policy['max_retained_pair_bytes']<=TOTAL_BYTES-RESERVE_BYTES,
             'prototype fixed parser-memory ceiling exceeded')
        need(isinstance(policy['caller_mangled'],str) and policy['caller_mangled'] and isinstance(policy['caller_source_path'],str)
            and policy['caller_source_path'].startswith('/') and '..' not in policy['caller_source_path'].split('/'),
            'exact absolute original caller policy required')
        for key in ('selected_names','api_names'):
            need(isinstance(policy[key],list) and len(policy[key])<=1000 and all(isinstance(name,str) and name for name in policy[key])
                and len(policy[key])==len(set(policy[key])),'closed bounded unique source name sets required')
        need(len(encode(policy))<=1048576,'bounded prospective stream policy required')
        need(set(policy['api_names'])<=set(policy['selected_names']),'every API candidate name must be retained')
        need(re.fullmatch('[0-9a-f]{64}',policy['source_and_compiler_receipt_sha256']),'actual future source/compiler receipt attribution required')
        self.policy=policy;self.reader=Reader(stream,policy['max_stream_bytes']);self.nodes=0;self.ids={};self.id_occurrences=[]
        self.named_declarations=[];self.census_rows=0;self.callers=[]
        self.location={'file':None,'line':None}
        self.event_hash=hashlib.sha256();self.events=0
        self.live_bytes=0;self.peak_accounted_bytes=0
        self.reader.charge=self.charge

    def charge(self,count):
        self.live_bytes+=count;self.peak_accounted_bytes=max(self.peak_accounted_bytes,self.live_bytes)
        need(0<=self.live_bytes<=self.policy['max_work_bytes'],'bounded live serialized working set exceeded')

    def event(self,value):
        self.events+=1;self.event_hash.update(encode(value)+b'\n')

    def string(self):
        r=self.reader;need(r.take()==b'"','JSON string required');raw=bytearray(b'"')
        while True:
            part=r.available();need(part,'truncated JSON string')
            match=re.search(rb'["\\\x00-\x1f]',part)
            count=match.start() if match else len(part)
            if count:raw.extend(r.take(count))
            need(len(raw)<=self.policy['max_token_bytes'],'bounded JSON token required')
            if not match:continue
            byte=r.take();raw.extend(byte)
            if byte==b'"':break
            need(byte==b'\\','raw control byte in JSON string')
            raw.extend(r.take())
        try:value=json.loads(raw)
        except (ValueError,UnicodeError) as error:raise Refused('malformed UTF8/escape in compiler JSON string') from error
        need(type(value) is str,'ordinary JSON string required');return value

    def scalar(self):
        r=self.reader;r.whitespace();byte=r.peek()
        if byte==34:return self.string()
        for prefix,value in ((b'true',True),(b'false',False),(b'null',None)):
            if byte==prefix[0]:r.literal(prefix);return value
        raw=bytearray()
        while r.peek() is not None and r.peek() in b'-+0123456789.eE':
            raw.extend(r.take());need(len(raw)<=128,'bounded JSON numeric token required')
        need(re.fullmatch(rb'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?',raw),'malformed JSON scalar')
        try:value=json.loads(raw)
        except ValueError as error:raise Refused('invalid JSON number') from error
        need(not isinstance(value,float) or math.isfinite(value),'nonfinite JSON number refused');return value

    def regular(self,depth,reference=False):
        need(depth<=self.policy['max_depth'],'bounded JSON depth required')
        r=self.reader;r.whitespace();start=r.position;byte=r.peek()
        if byte==123:
            r.take();value={};r.whitespace()
            if r.peek()!=125:
                while True:
                    key=self.string();need(key not in value,'duplicate JSON key')
                    need(key not in RESERVED_FIELDS,'reserved normalized/projection key in raw compiler stream')
                    r.whitespace();need(r.take()==b':','JSON object colon required')
                    value[key]=self.regular(depth+1,key in REFERENCE_FIELDS);r.whitespace()
                    marker=r.take()
                    if marker==b'}':break
                    need(marker==b',','JSON object delimiter required');r.whitespace()
            else:r.take()
            if 'kind' in value:
                need(reference and isinstance(value.get('id'),str) and not set(value)&{'inner','array_filler'},
                    'unknown owned AST object outside reviewed child edges')
            if 'offset' in value:
                if 'file' in value:self.location['file']=value['file']
                if 'line' in value:self.location['line']=value['line']
                value['_file']=self.location['file'];value['_line']=self.location['line']
                if 'line' not in value and self.location['line'] is not None:value['line']=self.location['line']
        elif byte==91:
            r.take();value=[];r.whitespace()
            if r.peek()!=93:
                while True:
                    value.append(self.regular(depth+1));r.whitespace();marker=r.take()
                    if marker==b']':break
                    need(marker==b',','JSON array delimiter required');r.whitespace()
            else:r.take()
        else:value=self.scalar()
        need(r.position-start<=self.policy['max_metadata_bytes'],'bounded non-owned compiler metadata required')
        return value

    def ast_array(self,depth,force,scope):
        r=self.reader;r.whitespace();need(r.take()==b'[','owned AST child array required');r.whitespace();items=[]
        if r.peek()!=93:
            while True:
                items.append(self.node(depth+1,force,scope));r.whitespace();marker=r.take()
                if marker==b']':break
                need(marker==b',','AST child delimiter required');r.whitespace()
                need(len(items)<=self.policy['max_nodes'],'bounded immediate AST children required')
        else:r.take()
        return items

    def node(self,depth,force=False,scope=()):
        need(depth<=self.policy['max_depth'],'bounded AST depth required')
        self.nodes+=1;need(self.nodes<=self.policy['max_nodes'],'bounded complete AST node count required')
        r=self.reader;start=r.begin();need(r.take()==b'{','AST object required');r.whitespace()
        fields={};owned={};ordered=[];owned_seen=False;fields_charge=0
        if r.peek()!=125:
            while True:
                key=self.string();need(key not in fields and key not in owned,'duplicate AST JSON key')
                need(key not in RESERVED_FIELDS,'reserved normalized/projection compiler key')
                need(not owned_seen or key not in SELECTOR_FIELDS,'late AST selector field after children refuses')
                r.whitespace();need(r.take()==b':','AST field colon required')
                if key in {'inner','array_filler'}:
                    need(isinstance(fields.get('kind'),str),'compiler node kind must precede owned children')
                    owned_seen=True
                    selected=force or self.selected(fields)
                    nested=scope+((fields.get('kind'),fields.get('name',''),fields.get('id','')),) if fields.get('kind') in SCOPE_KINDS else scope
                    owned[key]=self.ast_array(depth+1,selected,nested);ordered.append(key)
                else:
                    fields[key]=self.regular(depth+1,key in REFERENCE_FIELDS)
                    count=len(encode(key))+len(encode(fields[key]))+2;fields_charge+=count;self.charge(count)
                r.whitespace();marker=r.take()
                if marker==b'}':break
                need(marker==b',','AST object delimiter required');r.whitespace()
        else:r.take()
        span,partition,partition_charge=r.end(start)
        need(isinstance(fields.get('kind'),str),'every owned node has an actual kind')
        selected=force or self.selected(fields)
        child_results=[item for key in ordered for item in owned[key]]
        full=all(item['full'] for item in child_results)
        need(not selected or full,'selected node must retain complete control/effects')
        # Merkle content ignores whitespace and preserves every field/owned edge.
        fingerprint=digest({'fields':fields,'owned':{key:[item['fingerprint'] for item in owned[key]] for key in ordered}})
        ident=fields.get('id')
        if ident is not None:
            need(isinstance(ident,str) and ident,'actual AST node ID required')
            prior=self.ids.get(ident)
            if prior is not None:
                need(fields['kind'].endswith('Type') and prior['kind']==fields['kind'] and prior['fingerprint']==fingerprint,
                     'duplicate/conflicting structural declaration/node ID')
            else:
                need(len(self.ids)<self.policy['max_ids'],'bounded full-TU ID ledger required')
                self.ids[ident]={'kind':fields['kind'],'fingerprint':fingerprint}
            row=[ident,fields['kind'],fingerprint,span['start'],span['end']]
            self.id_occurrences.append(row);self.charge(len(encode(row))+1)
            need(len(self.id_occurrences)<=self.policy['max_nodes'],'bounded ID occurrence census required')
        if fields['kind'].endswith('Decl') and 'name' in fields:
            row={'id':ident,'kind':fields['kind'],'name':fields['name'],
                'mangledName':fields.get('mangledName'),'scope':scope,'location':fields.get('loc'),
                'retained_by_name_or_caller':self.selected(fields),'span':[span['start'],span['end']]}
            self.named_declarations.append(row);self.charge(len(encode(row))+1)
            need(len(self.named_declarations)<=self.policy['max_census_rows'],'bounded complete named-declaration census required')
        kept=selected or any(item['kept'] for item in child_results)
        counts={'nodes':1+sum(item['counts']['nodes'] for item in child_results),
                'selected_roots':int(self.selected(fields))+sum(item['counts']['selected_roots'] for item in child_results)}
        if kept:
            value=dict(fields)
            for key in ordered:value[key]=[item['value'] for item in owned[key]]
            if not selected:value['__projection_scaffold__']=True
            value['__projection_node__']={'raw_span':span,'partition':partition,'selected_full':selected}
            extra=len(encode(value['__projection_node__']))+128
            local_bytes=fields_charge+partition_charge+extra;self.charge(extra)
            work_bytes=local_bytes+sum(item['work_bytes'] for item in child_results)
        else:
            value={'kind':'ElidedOriginalASTSubtreeV1','original_kind':fields['kind'],'raw_span':span,
                   'content_merkle_sha256':fingerprint,'counts':counts,'relevance':'all descendants scanned; zero matching selection roots'}
            need(counts['selected_roots']==0,'cannot elide any selected descendant')
            work_bytes=len(encode(value));self.charge(work_bytes-sum(item['work_bytes'] for item in child_results)-fields_charge-partition_charge)
        self.census_rows+=1;need(self.census_rows<=self.policy['max_nodes'],'bounded traversal census required')
        self.event({'span':span,'fields_sha256':digest(fields),'content_merkle_sha256':fingerprint,'kept':kept,'selected':selected,'counts':counts})
        result={'value':value,'kept':kept,'full':selected or not owned,'fingerprint':fingerprint,'span':span,'counts':counts,'work_bytes':work_bytes}
        if fields['kind']=='FunctionDecl' and fields.get('mangledName')==self.policy['caller_mangled']:
            if any(item.get('kind')=='CompoundStmt' for item in value.get('inner',[]) if isinstance(item,dict)):
                self.callers.append(value)
        return result

    def selected(self,fields):
        return (fields.get('kind')=='FunctionDecl' and fields.get('mangledName')==self.policy['caller_mangled']) or (
            fields.get('kind','').endswith('Decl') and fields.get('name') in self.policy['selected_names']) or (
            fields.get('kind') in TYPE_DECL_KINDS and isinstance(fields.get('name'),str) and bool(fields['name']))

    def caller_checks(self,caller):
        loc=caller.get('loc',{})
        need(loc.get('_file',loc.get('file'))==self.policy['caller_source_path'],'selected caller original physical file differs')
        definitions={node['id'] for node in walk(caller) if isinstance(node.get('id'),str)}
        retained_ids={node['id'] for node in walk(self.projected) if isinstance(node.get('id'),str)}
        references=set();issues=[]
        for node in walk(caller):
            if node.get('kind') not in CALLER_KINDS:issues.append('unmodeled caller node '+str(node.get('kind')))
            if node.get('kind')=='UnaryOperator' and node.get('opcode') not in {'+','-','!','~','*','&'}:
                issues.append('unmodeled caller unary operator '+str(node.get('opcode')))
            typ=node.get('type',{})
            if isinstance(typ,dict) and any(isinstance(value,str) and re.search(r'\bvolatile\b',value) for value in typ.values()):
                issues.append('unmodeled caller volatile type')
            for key in ('typeAliasDeclId','referencedMemberDecl'):
                value=node.get(key)
                if isinstance(value,str):references.add(value)
            typ=node.get('type',{})
            if isinstance(typ,dict) and isinstance(typ.get('typeAliasDeclId'),str):references.add(typ['typeAliasDeclId'])
            reference=node.get('referencedDecl',{})
            if isinstance(reference,dict) and isinstance(reference.get('id'),str):references.add(reference['id'])
            if node.get('kind')=='CallExpr':
                inner=node.get('inner',[]);leaf=inner[0] if inner else {}
                while leaf.get('kind') in {'ImplicitCastExpr','ParenExpr'} and len(leaf.get('inner',[]))==1:leaf=leaf['inner'][0]
                ref=leaf.get('referencedDecl',{});name=ref.get('name')
                if leaf.get('kind')!='DeclRefExpr' or name not in set(self.policy['api_names'])|{'__assert_fail','__assert_rtn'}:
                    issues.append('unmodeled caller call '+str(name))
                elif name in self.policy['api_names']:
                    points=[node.get('range',{}).get(key,{}) for key in ('begin','end')]
                    if any('offset' not in point or 'spellingLoc' in point or 'expansionLoc' in point for point in points):
                        issues.append('selected API call has macro/non-direct coordinates')
        need(references<=retained_ids,'retained caller references an omitted declaration/type/enum/global ID')
        need(not issues,'; '.join(issues[:8]))
        return {'definition_ids':len(definitions),'required_reference_ids':sorted(references),'unmodeled_effects':[]}

    def run(self):
        root=self.node(0);r=self.reader;r.whitespace();need(r.peek() is None,'one complete TU only; trailing/concatenated JSON refuses')
        need(root['value'].get('kind')=='TranslationUnitDecl','one original complete TranslationUnitDecl stream required')
        need(len(self.callers)==1,'one complete original caller body required')
        self.projected=root['value'];caller=self.callers[0]
        checks=self.caller_checks(caller)
        need(root['counts']['nodes']==self.nodes,'complete owned-node traversal count differs')
        # The distinct root prevents accidental old raw-TU consumer acceptance.
        self.projected['original_kind']=self.projected.pop('kind')
        self.projected['kind']='ProjectedOriginalTranslationUnitV1'
        certificate={'schema':'original-tu-stream-projection-certificate-1','policy_sha256':digest(self.policy),
            'complete_stream_sha256':r.hash.hexdigest(),'complete_stream_bytes':r.bytes_received,
            'root_raw_span':root['span'],'complete_stream_parsed':True,'owned_nodes_visited':self.nodes,
            'complete_stream_partition':[{'role':'leading',**r.leading},{'role':'root',**root['span']},
                {'role':'trailing','start':root['span']['end'],'end':r.position,'bytes':r.position-root['span']['end'],
                 'sha256':r.outside_hash.hexdigest()}],
            'event_count':self.events,'ordered_traversal_merkle_sha256':self.event_hash.hexdigest(),
            'complete_node_id_occurrences':self.id_occurrences,'complete_named_declaration_census':self.named_declarations,
            'caller_checks':checks,'projection_sha256':digest(self.projected),
            'source_and_compiler_receipt_sha256':self.policy['source_and_compiler_receipt_sha256'],
            'discarded_bytes_independently_reconstructable':False,'streaming_classifier_and_location_normalizer_TCB':True,
            'old_raw_TU_consumer_compatible':False,'new_projection_consumer_admission_required':True,
            'actual_compiler_execution_inferred_from_digest':False,'source_call_or_public_admission':False}
        certificate['serialized_work_accounting']={'peak_charged_bytes':self.peak_accounted_bytes,
            'limit':self.policy['max_work_bytes'],'Python_allocator_and_actual_RSS_not_certified':True}
        certificate['allocated_retained_pair_bytes']=self.policy['max_retained_pair_bytes']
        projection_bytes,certificate_bytes=encode(self.projected),encode(certificate)
        need(len(projection_bytes)<=STAGE_BYTES and len(certificate_bytes)<=STAGE_BYTES
             and len(projection_bytes)+len(certificate_bytes)<=self.policy['max_retained_pair_bytes'],'unchanged retained per-file/allocated-total budget exceeded')
        return {'projection':self.projected,'certificate':certificate,'retained_bytes':len(projection_bytes)+len(certificate_bytes)}


def walk(node):
    if not isinstance(node,dict):return
    if node.get('kind')=='ElidedOriginalASTSubtreeV1':return
    yield node
    for field in ('inner','array_filler'):
        for child in node.get(field,[]):yield from walk(child)


def project_stream(stream,policy):return Projector(stream,policy).run()


def strict_artifact(raw):
    need(type(raw) is bytes and len(raw)<=STAGE_BYTES,'bounded retained artifact bytes required')
    def pairs(values):
        result={}
        for key,value in values:
            need(key not in result,'duplicate retained JSON key');result[key]=value
        return result
    try:
        return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:need(False,'nonfinite retained JSON'))
    except (ValueError,UnicodeError,RecursionError) as error:
        raise Refused('malformed retained projection/certificate') from error


def _verify_projection(projection_raw,certificate_raw,policy):
    """New passive reader: structural consistency, never elided-byte reconstruction.

    The independently reviewed future producer and source/compiler receipt are
    required premises. This function never calls an existing raw-TU consumer.
    """
    checker=Projector(None,policy)
    projected=strict_artifact(projection_raw);certificate=strict_artifact(certificate_raw)
    need(isinstance(projected,dict) and projected.get('kind')=='ProjectedOriginalTranslationUnitV1'
        and projected.get('original_kind')=='TranslationUnitDecl','distinct projected-TU root required')
    need(isinstance(certificate,dict) and certificate.get('schema')=='original-tu-stream-projection-certificate-1','projection certificate required')
    need(certificate.get('policy_sha256')==digest(policy) and certificate.get('projection_sha256')==digest(projected),
        'projection/policy certificate binding differs')
    need(certificate.get('source_and_compiler_receipt_sha256')==policy['source_and_compiler_receipt_sha256'],
        'source/compiler observation receipt differs')
    for key,value in {'complete_stream_parsed':True,'discarded_bytes_independently_reconstructable':False,
        'streaming_classifier_and_location_normalizer_TCB':True,'old_raw_TU_consumer_compatible':False,
        'new_projection_consumer_admission_required':True,'actual_compiler_execution_inferred_from_digest':False,
        'source_call_or_public_admission':False}.items():
        need(type(certificate.get(key)) is bool and certificate[key] is value,'explicit projection/TCB boundary differs')
    def span(value):
        need(isinstance(value,dict) and set(value)=={'start','end','bytes','sha256'},'exact raw span required')
        need(all(type(value[k]) is int for k in ('start','end','bytes')) and 0<=value['start']<=value['end']
            and value['bytes']==value['end']-value['start'],'raw span bounds differ')
        need(isinstance(value['sha256'],str) and re.fullmatch('[0-9a-f]{64}',value['sha256']),'raw span hash required')
        return value
    stream_bytes=certificate.get('complete_stream_bytes')
    need(type(stream_bytes) is int and 0<stream_bytes<=policy['max_stream_bytes'],'complete input byte allowance differs')
    need(isinstance(certificate.get('complete_stream_sha256'),str) and re.fullmatch('[0-9a-f]{64}',certificate['complete_stream_sha256']),
        'complete input hash required')
    whole_parts=certificate.get('complete_stream_partition')
    need(isinstance(whole_parts,list) and [part.get('role') for part in whole_parts]==['leading','root','trailing'],
        'one leading/root/trailing complete-stream partition required')
    cursor=0
    for part in whole_parts:
        value=span({key:value for key,value in part.items() if key!='role'})
        need(value['start']==cursor,'complete stream partition gap/overlap');cursor=value['end']
    need(cursor==stream_bytes and span(certificate['root_raw_span'])==span({key:value for key,value in whole_parts[1].items() if key!='role'}),
        'complete stream/root bounds differ')
    retained=[];elided=[];all_nodes=0;selected_roots=0;fingerprints={}
    def visit(node,forced=False,depth=0):
        nonlocal all_nodes,selected_roots
        need(depth<=policy['max_depth'] and isinstance(node,dict),'bounded projected AST node required')
        if node.get('kind')=='ElidedOriginalASTSubtreeV1':
            need(not forced,'selected full subtree contains an elision')
            need(set(node)=={'kind','original_kind','raw_span','content_merkle_sha256','counts','relevance'},'exact elided subtree shape required')
            value=span(node['raw_span']);counts=node['counts']
            need(isinstance(counts,dict) and set(counts)=={'nodes','selected_roots'} and type(counts['nodes']) is int
                and counts['nodes']>0 and type(counts['selected_roots']) is int and counts['selected_roots']==0,
                'elided subtree relevance/node census differs')
            need(node['relevance']=='all descendants scanned; zero matching selection roots'
                and isinstance(node['content_merkle_sha256'],str) and re.fullmatch('[0-9a-f]{64}',node['content_merkle_sha256']),
                'elision classification/fingerprint differs')
            elided.append(value);all_nodes+=counts['nodes'];return value
        annotation=node.get('__projection_node__')
        need(isinstance(annotation,dict) and set(annotation)=={'raw_span','partition','selected_full'},'retained node provenance required')
        value=span(annotation['raw_span']);selected=checker.selected(node)
        need(type(annotation['selected_full']) is bool and annotation['selected_full']==(forced or selected),'retained selection propagation differs')
        if not annotation['selected_full']:need(node.get('__projection_scaffold__') is True,'unselected ancestor context must be explicit')
        else:need('__projection_scaffold__' not in node,'complete selected node marked as scaffold')
        retained.append(node);all_nodes+=1;selected_roots+=int(selected)
        children=[]
        for key in ('inner','array_filler'):
            need(key not in node or isinstance(node[key],list),'projected owned child array required')
            for child in node.get(key,[]):children.append(visit(child,annotation['selected_full'],depth+2))
        parts=annotation['partition'];need(isinstance(parts,list) and parts,'complete node byte partition required')
        cursor=value['start'];observed=[]
        for part in parts:
            need(isinstance(part,dict) and part.get('role') in {'gap','child'},'raw partition role required')
            interval=span({key:value for key,value in part.items() if key!='role'})
            need(interval['start']==cursor and interval['end']>cursor,'node partition gap/overlap');cursor=interval['end']
            if part['role']=='child':observed.append(interval)
        need(cursor==value['end'] and observed==children,'node byte partition/owned edges differ')
        fields={key:value for key,value in node.items() if key not in {'inner','array_filler','__projection_node__','__projection_scaffold__'}}
        if fields.get('kind')=='ProjectedOriginalTranslationUnitV1':fields['kind']=fields.pop('original_kind')
        owned={}
        for key in ('inner','array_filler'):
            if key in node:
                owned[key]=[child['content_merkle_sha256'] if child.get('kind')=='ElidedOriginalASTSubtreeV1'
                    else fingerprints[(child['__projection_node__']['raw_span']['start'],child['__projection_node__']['raw_span']['end'])]
                    for child in node[key]]
        fingerprints[(value['start'],value['end'])]=digest({'fields':fields,'owned':owned})
        return value
    root=visit(projected)
    need(root==certificate['root_raw_span'],'projected root/raw observation differs')
    need(all_nodes==certificate.get('owned_nodes_visited')==certificate.get('event_count') and all_nodes<=policy['max_nodes'],
        'complete traversal/elision node census differs')
    named=certificate.get('complete_named_declaration_census');ids=certificate.get('complete_node_id_occurrences')
    need(isinstance(named,list) and len(named)<=policy['max_census_rows'] and isinstance(ids,list) and len(ids)<=policy['max_nodes'],
        'bounded complete declaration/ID census required')
    retained_spans={(node['__projection_node__']['raw_span']['start'],node['__projection_node__']['raw_span']['end']):node for node in retained}
    need(len(retained_spans)==len(retained),'duplicate retained node spans')
    selected_census=0;named_spans=set()
    for row in named:
        need(isinstance(row,dict) and set(row)=={'id','kind','name','mangledName','scope','location','retained_by_name_or_caller','span'},
            'complete named declaration census row differs')
        selected=checker.selected(row)
        need(type(row['retained_by_name_or_caller']) is bool and row['retained_by_name_or_caller']==selected,'named declaration relevance differs')
        bounds=row['span'];need(isinstance(bounds,list) and len(bounds)==2 and all(type(n) is int for n in bounds)
            and root['start']<=bounds[0]<bounds[1]<=root['end'],'named declaration span differs')
        need(tuple(bounds) not in named_spans,'duplicate named declaration census span');named_spans.add(tuple(bounds))
        if selected:
            selected_census+=1
            actual=retained_spans.get(tuple(bounds));need(actual is not None,'selected competing declaration omitted')
            need(all(actual.get(key)==row.get(key) for key in ('id','kind','name','mangledName')),'selected declaration identity differs')
        need(not any(part['start']<=bounds[0] and bounds[1]<=part['end'] for part in elided) or not selected,
            'selected name hidden within elided subtree')
    need(selected_census==selected_roots,'complete selected declaration count differs')
    ledger={};occurrences={}
    for row in ids:
        need(isinstance(row,list) and len(row)==5 and isinstance(row[0],str) and isinstance(row[1],str)
            and isinstance(row[2],str) and re.fullmatch('[0-9a-f]{64}',row[2]) and type(row[3]) is int and type(row[4]) is int
            and root['start']<=row[3]<row[4]<=root['end'],'complete ID occurrence row differs')
        ident,kind,fingerprint,start,end=row
        need((start,end) not in occurrences,'duplicate structural ID occurrence span');occurrences[(start,end)]=(ident,kind,fingerprint)
        if ident in ledger:need(kind.endswith('Type') and ledger[ident]==(kind,fingerprint),'conflicting duplicate ID ledger')
        ledger[ident]=(kind,fingerprint)
    need(len(ledger)<=policy['max_ids'],'ID ledger cap differs')
    for node in retained:
        if 'id' in node:
            bounds=node['__projection_node__']['raw_span'];site=(bounds['start'],bounds['end'])
            need(occurrences.get(site)==(node['id'],node.get('original_kind',node['kind']),fingerprints[site]),
                'retained definition/complete ID ledger differs')
        if node.get('kind','').endswith('Decl') and 'name' in node:
            bounds=node['__projection_node__']['raw_span'];need((bounds['start'],bounds['end']) in named_spans,
                'retained named declaration missing from complete census')
    callers=[node for node in retained if node.get('kind')=='FunctionDecl' and node.get('mangledName')==policy['caller_mangled']
             and any(child.get('kind')=='CompoundStmt' for child in node.get('inner',[]))]
    need(len(callers)==1,'one retained complete caller body required')
    checker.projected=projected
    need(checker.caller_checks(callers[0])==certificate.get('caller_checks'),'complete caller reference/effect closure differs')
    work=certificate.get('serialized_work_accounting')
    need(isinstance(work,dict) and set(work)=={'peak_charged_bytes','limit','Python_allocator_and_actual_RSS_not_certified'}
        and type(work['peak_charged_bytes']) is int and 0<work['peak_charged_bytes']<=policy['max_work_bytes']
        and work['limit']==policy['max_work_bytes'] and work['Python_allocator_and_actual_RSS_not_certified'] is True,
        'explicit bounded work-accounting/allocator TCB differs')
    need(certificate.get('allocated_retained_pair_bytes')==policy['max_retained_pair_bytes']
        and len(projection_raw)+len(certificate_raw)<=policy['max_retained_pair_bytes'],'unchanged retained allocated total allowance exceeded')
    return {'structurally_consistent':True,'complete_owned_nodes':all_nodes,'selected_declarations':selected_roots,
        'retained_nodes':len(retained),'elided_roots':len(elided),'producer_and_source_compiler_observations_remain_TCB':True,
        'old_raw_TU_consumer_compatible':False,'actual_source_or_public_admission':False}


def verify_projection(projection_raw,certificate_raw,policy):
    try:return _verify_projection(projection_raw,certificate_raw,policy)
    except Refused:raise
    except (TypeError,KeyError,IndexError,AttributeError,RecursionError,OverflowError) as error:
        raise Refused('malformed projected AST/certificate structure') from error
