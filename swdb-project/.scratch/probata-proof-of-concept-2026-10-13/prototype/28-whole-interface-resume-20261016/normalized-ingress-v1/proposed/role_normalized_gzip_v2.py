"""2026-10-16 ET. INERT paired-Type normalized-gzip transport primitives.

Synthetic controls only. No main, project imports, compiler, filesystem or actual
TU input selection. Separate physical-source/root admission is mandatory. A
failed traversal may leave partial sinks; no receipt or admission is returned.
"""
import hashlib
import json
ORIGIN_CENSUS_SHA='7517108384e877d6e67322a3b291662b95fa305a3bc5bab169414b6f06b0f54b'
MINIFIER_SHA='b866e14fe3ca210de178aab71f5c8a662e15f818a5ca485095487b005ae51897'
class Refused(ValueError):pass
def need(ok,message):
    if not ok:raise Refused(message)
def position(reader):return reader.count-(len(reader.buffer)-reader.at)
class NullSink:
    def write(self,value):need(len(value)<=65536,'reviewed write bound differs');return len(value)

def role(pairs):
    keys=[row['key'] for row in pairs];duplicates={key for key in keys if keys.count(key)>1}
    if not duplicates:return False,'no duplicate'
    if duplicates!={'type'} or keys.count('type')!=2:return False,'duplicate key/ordinal outside exact documented type roles'
    if keys[:3]!=['id','kind','type']:return False,'generic Type prefix/order differs'
    def short(row):return row.get('scalar',{}).get('text') if row.get('scalar',{}).get('complete') else None
    kind=short(pairs[1]['value'])
    if kind not in ('UsingType','TypedefType'):return False,'undocumented duplicate node kind'
    if not all(row['literal_key'] for row in pairs):return False,'compiler constant-key spelling differs'
    second=keys.index('type',3)
    if second<4 or keys[second-1]!='decl' or keys[second+1:] not in ([],['inner']):return False,'specialized Type decl/type/child order differs'
    allowed=['containsErrors','isDependent','isInstantiationDependent','isVariablyModified','containsUnexpandedPack','isImported']
    flags=keys[3:second-1]
    if flags!=[key for key in allowed if key in flags] or any(pairs[i]['value'].get('lexeme')!='true' for i in range(3,second-1)):
        return False,'generic Type flag order/value differs'
    if 'inner' in keys and pairs[-1]['value']['kind']!='array':return False,'Type children are not an array'
    ident=short(pairs[0]['value'])
    import re
    if not isinstance(ident,str) or not re.fullmatch(r'0x[0-9a-f]+',ident):return False,'Type same-TU id shape differs'
    original=pairs[2]['value'];target=pairs[second]['value'];decl=pairs[second-1]['value']
    def type_fields(value,original=False):
        if value['kind']!='object' or not value.get('keys_complete'):return False
        actual=value['keys']
        if original and actual!=['qualType']:return False
        if not original and (len(actual)!=len(set(actual)) or 'qualType' not in actual or not set(actual)<={'qualType','desugaredQualType','typeAliasDeclId'}):return False
        fields=value['fields']
        for key in actual:
            item=fields.get(key,{})
            if item.get('kind')!='string' or item['scalar']['length']==0:return False
            if key=='typeAliasDeclId' and (not item['scalar']['complete'] or not re.fullmatch(r'0x[0-9a-f]+',item['scalar']['text'])):return False
        return True
    if not type_fields(original,True) or not type_fields(target):return False,'original/desugared QualType field shape differs'
    wanted='UsingShadowDecl' if kind=='UsingType' else None
    if decl['kind']!='object' or not decl.get('keys_complete') or set(decl['keys'])!={'id','kind','name'} or len(decl['keys'])!=3:return False,'specialized Type bare declaration shape differs'
    fields=decl['fields'];dk=short(fields['kind']);di=short(fields['id'])
    if (dk!=wanted if wanted else dk not in ('TypedefDecl','TypeAliasDecl')) or not isinstance(di,str) or not re.fullmatch(r'0x[0-9a-f]+',di) or fields['name']['kind']!='string':return False,'specialized Type declaration role differs'
    return True,kind+'.type.original-and-desugared'

def normalize(source,sink,manifest_sink,base,check):
    """Complete grammar + ordered-pair census, never last-wins or AST acceptance."""
    output_bytes=0;manifest_bytes=0;manifest_hash=hashlib.sha256();renames=0
    def write_output(value):
        nonlocal output_bytes
        need(output_bytes+len(value)<=201326592,'normalized expanded token stream cap exceeded')
        for begin in range(0,len(value),65536):
            part=value[begin:begin+65536];check();need(sink.write(part)==len(part),'short normalized write');output_bytes+=len(part)
    def write_manifest(row):
        nonlocal manifest_bytes,renames
        value=json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()+b'\n'
        need(len(value)<=4096 and manifest_bytes+len(value)<=33554432,'bounded complete inverse manifest required')
        check();need(manifest_sink.write(value)==len(value),'short inverse manifest write')
        manifest_bytes+=len(value);manifest_hash.update(value);renames+=1
    class Census(base['Minifier']):
        def __init__(self):
            super().__init__(source,NullSink(),raw_limit=2147483648,retained_limit=134217728,check=check)
            self.stack=[];self.key_capture=False;self.key_token=None;self.last_token=None;self.last_string=None
            self.normalized_hash=hashlib.sha256();self.normalized_bytes=0;self.live_summary_charge=0;self.peak_summary_charge=0
            self.event_hash=hashlib.sha256();self.events=0;self.unknown=0;self.groups={};self.samples=[];self.candidate_replacements=0;self.qualified_replacements=0
        def emit(self,value):
            if self.key_capture:self.key_token=value;return
            write_output(value)
            self.last_token=value
            if self.stack:
                self.stack[-1]['hash'].update(b'T'+len(value).to_bytes(8,'big')+value);self.stack[-1]['bytes']+=len(value)
            self.normalized_hash.update(value);self.normalized_bytes+=len(value)
            need(self.normalized_bytes<=2147483648+2097152,'hash-only normalized token allowance exceeded')
            self.output_bytes+=len(value);need(self.output_bytes<=2147483648,'hash-only original token allowance exceeded');self.output_hash.update(value)
        def emit_key(self,token,replacement=None):
            # Keep original global token/structural digest, separately hash the
            # proposed role key. Nothing is written as a normalized AST.
            write_output(token if replacement is None else replacement)
            self.last_token=token;self.stack[-1]['hash'].update(b'T'+len(token).to_bytes(8,'big')+token);self.stack[-1]['bytes']+=len(token)
            self.normalized_hash.update(token if replacement is None else replacement);self.normalized_bytes+=len(token if replacement is None else replacement)
            need(self.normalized_bytes<=2147483648+2097152,'hash-only normalized token allowance exceeded')
            self.output_bytes+=len(token);need(self.output_bytes<=2147483648,'hash-only original token allowance exceeded');self.output_hash.update(token)
        def string(self,*,key=False):
            value=super().string(key=key);self.last_string=value;return value
        def child(self,depth,field):
            item=self.value(depth,field);self.stack[-1]['hash'].update(b'V'+bytes.fromhex(item['ordered_merkle_sha256']));self.stack[-1]['bytes']+=item['token_bytes'];return item
        def value(self,depth=0,field='$'):
            r=self.reader;r.whitespace();start=position(r);byte=r.peek();category={123:'object',91:'array',34:'string',116:'true',102:'false',110:'null'}.get(byte,'number')
            need(depth<=256,'complete census depth bound');self.tokens+=1;need(self.tokens<=20000000,'complete census token count bound');self.max_depth=max(self.max_depth,depth)
            frame={'hash':hashlib.sha256(b'N'+category.encode()),'bytes':0};self.stack.append(frame);entries=[];keys=[];fields={};charged=0;summary_charged=0
            if byte==123:
                self.objects+=1;self.emit(r.take());r.whitespace();seen={}
                if r.peek()!=125:
                    while True:
                        key_start=position(r);self.key_capture=True
                        key=self.string(key=True);token=self.key_token;self.key_capture=False;key_end=position(r)
                        need(key!='swdbClangDesugaredType','original key collides with reserved role transport namespace')
                        ordinal=seen.get(key,0)+1;seen[key]=ordinal
                        prefix_kind=fields.get('kind',{}).get('scalar',{}).get('text')
                        replacement=b'"swdbClangDesugaredType"' if key=='type' and ordinal==2 and prefix_kind in ('UsingType','TypedefType') else None
                        if replacement:self.candidate_replacements+=1
                        normalized_key_start=self.normalized_bytes
                        self.emit_key(token,replacement);normalized_key_end=self.normalized_bytes;count=len(key.encode('utf-8','surrogatepass'))+64;charged+=count;self.key_bytes+=count;self.keys+=1
                        self.peak_key_bytes=max(self.peak_key_bytes,self.key_bytes);need(len(entries)<1024 and self.key_bytes<=16777216,'complete census live key bound')
                        r.whitespace();need(r.take()==b':','census object colon required');self.emit(b':');value=self.child(depth+1,key)
                        entry={'key':key,'literal_key':token==json.dumps(key,ensure_ascii=False,separators=(',',':')).encode('utf-8','surrogatepass'),
                            'key_span':[key_start,key_end],'normalized_key_span':[normalized_key_start,normalized_key_end],'ordinal':ordinal,'value':value,'replacement_candidate':replacement is not None}
                        entries.append(entry);keys.append(key)
                        charge=len(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True))+96;summary_charged+=charge;self.live_summary_charge+=charge
                        self.peak_summary_charge=max(self.peak_summary_charge,self.live_summary_charge);need(self.live_summary_charge<=16777216,'complete census live summary bound')
                        if key in ('id','kind','name','qualType','desugaredQualType','typeAliasDeclId') and value['kind'] not in ('object','array'):
                            if ordinal==1:fields[key]=value
                            else:fields.pop(key,None)
                        r.whitespace();marker=r.take();need(marker in (b',',b'}'),'census object delimiter required');self.emit(marker)
                        if marker==b'}':break
                        r.whitespace()
                else:self.emit(r.take())
                duplicate_keys={key for key,count in seen.items() if count>1}
                if duplicate_keys:
                    qualified,reason=role(entries);node_kind=fields.get('kind',{}).get('scalar',{}).get('text','<missing-or-ambiguous>')
                    if qualified:
                        self.qualified_replacements+=1
                        item=next(row for row in entries if row['key']=='type' and row['ordinal']==2)
                        write_manifest({'schema':'llvm22-type-role-rename-1','role':reason,
                            'node_id':fields['id']['scalar']['text'],'original_key_span':item['key_span'],
                            'normalized_key_span':item['normalized_key_span'],'original_token':'"type"',
                            'normalized_token':'"swdbClangDesugaredType"'})
                    for item in entries:
                        if item['ordinal']<=1:continue
                        first=next(e for e in entries if e['key']==item['key']);self.events+=1;need(self.events<=100000,'complete duplicate census count bound')
                        if not qualified:self.unknown+=1
                        kind_value=fields.get('kind',{});kind_identity={'value_kind':kind_value.get('kind','missing-or-ambiguous'),
                            'ordered_merkle_sha256':kind_value.get('ordered_merkle_sha256'),
                            'decoded_string_sha256':kind_value.get('scalar',{}).get('sha256')}
                        event={'node_kind':node_kind,'node_kind_identity':kind_identity,'node_id':fields.get('id',{}).get('scalar',{}).get('text'),
                            'object_start':start,'key':item['key'][:256],'key_sha256':hashlib.sha256(item['key'].encode('utf-8','surrogatepass')).hexdigest(),
                            'ordinal':item['ordinal'],'first_key_span':first['key_span'],'key_span':item['key_span'],
                            'first_value':first['value'],'next_value':item['value'],'role_qualified':qualified,'reason':reason,
                            'values_structurally_identical':first['value']['ordered_merkle_sha256']==item['value']['ordered_merkle_sha256']}
                        encoded=json.dumps(event,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode();self.event_hash.update(len(encoded).to_bytes(8,'big')+encoded)
                        group=json.dumps({'node_kind_identity':kind_identity,'key_sha256':event['key_sha256'],'ordinal':item['ordinal'],'reason':reason},sort_keys=True,separators=(',',':'));self.groups[group]=self.groups.get(group,0)+1;need(len(self.groups)<=256,'bounded distinct duplicate role census')
                        if len(self.samples)<8:
                            sample=event
                            if len(encoded)>2048:
                                sample={key:event[key] for key in ('object_start','ordinal','first_key_span','key_span','role_qualified','reason','values_structurally_identical')}
                                sample.update(node_kind_sha256=hashlib.sha256(str(node_kind).encode('utf-8','surrogatepass')).hexdigest(),
                                    key_sha256=event['key_sha256'],first_value_merkle_sha256=first['value']['ordered_merkle_sha256'],
                                    next_value_merkle_sha256=item['value']['ordered_merkle_sha256'],large_sample_metadata_omitted=True)
                            self.samples.append(sample)
                self.key_bytes-=charged;self.live_summary_charge-=summary_charged
            elif byte==91:
                self.arrays+=1;self.emit(r.take());r.whitespace();index=0
                if r.peek()!=93:
                    while True:
                        self.child(depth+1,field+'['+str(index)+']');index+=1;r.whitespace();marker=r.take();need(marker in (b',',b']'),'census array delimiter required');self.emit(marker)
                        if marker==b']':break
                else:self.emit(r.take())
            else:super().scalar()
            self.stack.pop();result={'kind':category,'raw_span':[start,position(r)],'token_bytes':frame['bytes'],'ordered_merkle_sha256':frame['hash'].hexdigest()}
            if category=='string':
                value=self.last_string;result['scalar']={'text':value[:128],'complete':len(value)<=128,'length':len(value),'sha256':hashlib.sha256(value.encode('utf-8','surrogatepass')).hexdigest()}
            elif category not in ('object','array'):result['lexeme']=self.last_token.decode('ascii')
            if category=='object':result.update(keys=[key[:128] for key in keys[:24]],keys_complete=len(keys)<=24 and all(len(key)<=128 for key in keys),fields=fields)
            return result
        def complete(self):
            root=self.value();self.reader.whitespace();need(self.reader.peek() is None,'single complete original JSON root required')
            need(not self.stack and self.key_bytes==self.live_summary_charge==0,'complete census stack/summary closure required');self.flush()
            need(root['kind']=='object' and root['fields'].get('kind',{}).get('scalar',{}).get('text')=='TranslationUnitDecl','complete original TranslationUnitDecl required')
            need(root['token_bytes']==self.output_bytes,'complete ordered tree and original token byte counts differ')
            eligible=self.unknown==0 and self.candidate_replacements==self.qualified_replacements==self.events and self.normalized_bytes<=201326592
            group_rows=[{'signature':json.loads(key),'count':value} for key,value in sorted(self.groups.items())]
            group_raw=json.dumps(group_rows,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
            displayed=[]
            for row in group_rows[:16]:
                encoded=json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
                displayed.append(row if len(encoded)<=1024 else {'count':row['count'],'signature_sha256':hashlib.sha256(encoded).hexdigest(),'large_signature_omitted':True})
            return {'schema':'complete-original-tu-ordered-pair-census-1','raw_bytes':self.reader.count,'raw_sha256':self.reader.hash.hexdigest(),
                'original_minified_token_bytes':self.output_bytes,'original_minified_token_sha256':self.output_hash.hexdigest(),
                'ordered_graph_merkle_sha256':root['ordered_merkle_sha256'],'duplicate_events':self.events,'duplicate_event_census_sha256':self.event_hash.hexdigest(),
                'duplicate_groups':displayed,'duplicate_group_count':len(group_rows),'duplicate_group_limit':16,
                'complete_duplicate_group_census_sha256':hashlib.sha256(group_raw).hexdigest(),
                'unknown_or_mismatched_duplicate_events':self.unknown,'samples':self.samples,'sample_limit':8,
                'objects':self.objects,'arrays':self.arrays,'values':self.tokens,'keys':self.keys,'max_depth':self.max_depth,
                'peak_live_key_charge':self.peak_key_bytes,'peak_live_summary_charge':self.peak_summary_charge,
                'complete_original_JSON_token_grammar_checked':True,'ordered_duplicate_pairs_overwritten_or_dropped':False,
                'prospective_normalized_key':'swdbClangDesugaredType','prospective_normalized_token_bytes':self.normalized_bytes,
                'prospective_normalized_token_sha256':self.normalized_hash.hexdigest(),'role_normalization_and_expanded_cap_eligible':eligible,
                'expanded_role_transport_refused':not eligible,
                'plain_normalized_file_cap_fit':self.normalized_bytes<=134217728,
                'prospective_role_renames':self.qualified_replacements,'normalized_AST_retained_or_admitted':False,
                'normalization_is_original_token_identity':False,'actual_source_ABI_or_public_admission':False}
    result=Census().complete()
    need(result['role_normalization_and_expanded_cap_eligible'] is True,'unknown role/order/shape/collision prevents transport publication')
    need(renames==result['duplicate_events']==result['prospective_role_renames'],'complete inverse rename census differs')
    need(output_bytes==result['prospective_normalized_token_bytes'],'written normalized extent differs')
    result.pop('normalized_AST_retained_or_admitted')
    result.update(schema='llvm22-original-tu-role-expanded-2',normalized_expanded_stream_written=True,normalized_uncompressed_file_written=False,normalized_AST_admitted=False,
        normalized_bytes=output_bytes,normalized_sha256=result['prospective_normalized_token_sha256'],
        inverse_manifest_bytes=manifest_bytes,inverse_manifest_sha256=manifest_hash.hexdigest(),inverse_manifest_rows=renames,
        original_TU_source_ABI_or_public_admission=False)
    return result

EXPANDED_LIMIT=201326592
COMPRESSED_LIMIT=134217728
CODEC_SHA='aae4a423216fcdca6b16f9eba370ec4c83615ed61ae79dd4b3d09e3bed1702ef'

def compress_normalize(source,compressed_sink,manifest_sink,base,codec,zlib,check):
    """Only gzip bytes are retained; normalized expanded bytes stay streaming."""
    capture=codec['Capture'](zlib,compressed_sink,expanded_limit=EXPANDED_LIMIT,compressed_limit=COMPRESSED_LIMIT,check=check)
    class BufferedExpanded:
        def __init__(self):self.buffer=bytearray();self.bytes=0
        def write(self,value):
            need(type(value) is bytes and len(value)<=65536,'bounded normalized expanded chunk required')
            need(self.bytes+len(value)<=EXPANDED_LIMIT,'normalized expanded stream cap exceeded')
            self.bytes+=len(value);at=0
            while at<len(value):
                amount=min(65536-len(self.buffer),len(value)-at);self.buffer.extend(value[at:at+amount]);at+=amount
                if len(self.buffer)==65536:self.flush()
            return len(value)
        def flush(self):
            if self.buffer:capture.feed(bytes(self.buffer));self.buffer.clear()
    buffered=BufferedExpanded();normalization=normalize(source,buffered,manifest_sink,base,check)
    buffered.flush();gzip=capture.finish()
    need((gzip['expanded_bytes'],gzip['expanded_sha256'])==(normalization['normalized_bytes'],normalization['normalized_sha256']),
        'compressed normalized expanded identity differs from complete normalization')
    return {'schema':'llvm22-original-tu-paired-type-gzip-2','kind':'complete-original-tu-paired-type-lossless-gzip',
        'normalization':normalization,'normalized_gzip_codec':gzip,'normalized_expanded_limit_bytes':EXPANDED_LIMIT,
        'physical_gzip_limit_bytes':COMPRESSED_LIMIT,'normalized_uncompressed_file_written':False,
        'original_TU_source_ABI_or_public_admission':False}


def inverse_stream_identity(source,manifest,receipt,check):
    """Hash the inverse while draining bounded decoded bytes; no expanded DOM."""
    need(type(manifest) is bytes and len(manifest)<=33554432,'bounded complete inverse manifest required')
    need(hashlib.sha256(manifest).hexdigest()==receipt['inverse_manifest_sha256'] and len(manifest)==receipt['inverse_manifest_bytes'],
        'inverse manifest physical identity differs')
    def pairs(items):
        out={}
        for key,value in items:need(key not in out,'inverse manifest duplicate key');out[key]=value
        return out
    rows=[]
    for line in manifest.splitlines(keepends=True):
        need(len(line)<=4096 and line.endswith(b'\n') and len(rows)<100000,'bounded canonical inverse manifest row required')
        row=json.loads(line,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(Refused('nonfinite manifest')))
        need(type(row) is dict and set(row)=={'schema','role','node_id','original_key_span','normalized_key_span','original_token','normalized_token'}
            and row['schema']=='llvm22-type-role-rename-1' and row['role'] in ('UsingType.type.original-and-desugared','TypedefType.type.original-and-desugared')
            and row['original_token']=='"type"' and row['normalized_token']=='"swdbClangDesugaredType"','exact inverse role row required')
        need(type(row['node_id']) is str and row['node_id'].startswith('0x') and 2<len(row['node_id'])<=128
            and all(c in '0123456789abcdef' for c in row['node_id'][2:]),'exact same-TU node ID spelling required')
        need(line==json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()+b'\n',
            'canonical complete inverse row bytes required')
        for key in ('original_key_span','normalized_key_span'):
            need(type(row[key]) is list and len(row[key])==2 and all(type(n) is int and n>=0 for n in row[key]) and row[key][0]<row[key][1],
                'exact nonempty inverse key span required')
        need(row['original_key_span'][1]-row['original_key_span'][0]==len(row['original_token']), 'original literal key span differs')
        rows.append(row)
    need(len(rows)==receipt['inverse_manifest_rows']==receipt['duplicate_events']==receipt['prospective_role_renames'],
        'complete inverse role count differs')
    rows.sort(key=lambda row:row['normalized_key_span'])
    normal_hash=hashlib.sha256();normal_bytes=0;original_hash=hashlib.sha256();original_bytes=0;original_end=0
    def read(count):
        nonlocal normal_bytes
        check();need(type(count) is int and 0<count<=65536,'bounded inverse decoded read required')
        value=source.read(count);need(type(value) is bytes and len(value)<=count,'bounded inverse decoded result required')
        normal_bytes+=len(value);need(normal_bytes<=EXPANDED_LIMIT,'normalized expanded inverse cap exceeded');normal_hash.update(value);return value
    def ordinary_until(end):
        nonlocal original_bytes
        need(normal_bytes<=end<=receipt['normalized_bytes'],'inverse offset exceeds normalized extent')
        while normal_bytes<end:
            value=read(min(65536,end-normal_bytes));need(value,'truncated normalized inverse stream')
            original_hash.update(value);original_bytes+=len(value)
    for row in rows:
        begin,end=row['normalized_key_span'];replacement=row['normalized_token'].encode();original=row['original_token'].encode()
        need(normal_bytes<=begin<end<=receipt['normalized_bytes'] and end-begin==len(replacement)
            and row['original_key_span'][0]>=original_end,'inverse spans overlap, reorder or exceed normalized extent')
        ordinary_until(begin);token=bytearray()
        while normal_bytes<end:
            value=read(end-normal_bytes);need(value,'truncated renamed key');token.extend(value)
        need(bytes(token)==replacement,'unexpected normalized rename token')
        original_hash.update(original);original_bytes+=len(original);original_end=row['original_key_span'][1]
    ordinary_until(receipt['normalized_bytes']);need(not read(65536),'trailing normalized inverse bytes')
    need((normal_bytes,normal_hash.hexdigest())==(receipt['normalized_bytes'],receipt['normalized_sha256']),
        'complete normalized expanded identity differs')
    need((original_bytes,original_hash.hexdigest())==(receipt['original_minified_token_bytes'],receipt['original_minified_token_sha256']),
        'streaming inverse does not reproduce complete original token identity')
    return {'schema':'paired-type-streaming-inverse-2','normalized_expanded_bytes':normal_bytes,'normalized_expanded_sha256':normal_hash.hexdigest(),
        'original_minified_token_bytes':original_bytes,'original_minified_token_sha256':original_hash.hexdigest(),'inverse_rows':len(rows),
        'expanded_file_or_DOM_created':False,'source_ABI_or_public_admission':False}


def verify_inverse_gzip(zlib,compressed_source,manifest,transport,codec,check):
    need(type(transport) is dict and set(transport)=={'schema','kind','normalization','normalized_gzip_codec','normalized_expanded_limit_bytes',
        'physical_gzip_limit_bytes','normalized_uncompressed_file_written','original_TU_source_ABI_or_public_admission'}
        and transport['schema']=='llvm22-original-tu-paired-type-gzip-2' and transport['kind']=='complete-original-tu-paired-type-lossless-gzip'
        and transport['normalized_expanded_limit_bytes']==EXPANDED_LIMIT and transport['physical_gzip_limit_bytes']==COMPRESSED_LIMIT
        and transport['normalized_uncompressed_file_written'] is False and transport['original_TU_source_ABI_or_public_admission'] is False,
        'exact prospective normalized-gzip transport required')
    receipt=transport['normalization'];gzip=transport['normalized_gzip_codec']
    need(receipt['role_normalization_and_expanded_cap_eligible'] is True and receipt['expanded_role_transport_refused'] is False
        and receipt['normalized_AST_admitted'] is False and receipt['normalized_uncompressed_file_written'] is False,
        'complete role-qualified expanded stream required')
    need((gzip['expanded_bytes'],gzip['expanded_sha256'])==(receipt['normalized_bytes'],receipt['normalized_sha256']),
        'normalized codec and role-transform expanded identities differ')
    decoded=codec['DecodeReader'](zlib,compressed_source,gzip,expanded_limit=EXPANDED_LIMIT,compressed_limit=COMPRESSED_LIMIT,check=check)
    inverse=inverse_stream_identity(decoded,manifest,receipt,check)
    need(decoded.verified,'complete normalized gzip identity/EOF required')
    return {'schema':'paired-type-gzip-inverse-2','inverse':inverse,'complete_normalized_gzip_identity_verified':True,
        'original_wire_identity_is_normalized_identity':False,'source_ABI_or_public_admission':False}
