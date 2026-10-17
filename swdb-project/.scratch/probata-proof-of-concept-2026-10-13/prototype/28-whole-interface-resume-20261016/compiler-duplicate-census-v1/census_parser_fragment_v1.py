"""Inert strict-token grammar; ordered duplicate pairs stay observational data."""
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


def census(source,base,check):
    """Complete grammar + ordered-pair census, never last-wins or AST acceptance."""
    class Census(base['Minifier']):
        def __init__(self):
            super().__init__(source,NullSink(),raw_limit=2147483648,retained_limit=134217728,check=check)
            self.stack=[];self.key_capture=False;self.key_token=None;self.last_token=None;self.last_string=None
            self.normalized_hash=hashlib.sha256();self.normalized_bytes=0;self.live_summary_charge=0;self.peak_summary_charge=0
            self.event_hash=hashlib.sha256();self.events=0;self.unknown=0;self.groups={};self.samples=[];self.candidate_replacements=0;self.qualified_replacements=0
        def emit(self,value):
            if self.key_capture:self.key_token=value;return
            self.last_token=value
            if self.stack:
                self.stack[-1]['hash'].update(b'T'+len(value).to_bytes(8,'big')+value);self.stack[-1]['bytes']+=len(value)
            self.normalized_hash.update(value);self.normalized_bytes+=len(value)
            need(self.normalized_bytes<=2147483648+2097152,'hash-only normalized token allowance exceeded')
            self.output_bytes+=len(value);need(self.output_bytes<=2147483648,'hash-only original token allowance exceeded');self.output_hash.update(value)
        def emit_key(self,token,replacement=None):
            # Keep original global token/structural digest, separately hash the
            # proposed role key. Nothing is written as a normalized AST.
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
                        ordinal=seen.get(key,0)+1;seen[key]=ordinal
                        prefix_kind=fields.get('kind',{}).get('scalar',{}).get('text')
                        replacement=b'"swdbClangDesugaredType"' if key=='type' and ordinal==2 and prefix_kind in ('UsingType','TypedefType') else None
                        if replacement:self.candidate_replacements+=1
                        self.emit_key(token,replacement);count=len(key.encode('utf-8','surrogatepass'))+64;charged+=count;self.key_bytes+=count;self.keys+=1
                        self.peak_key_bytes=max(self.peak_key_bytes,self.key_bytes);need(len(entries)<1024 and self.key_bytes<=16777216,'complete census live key bound')
                        r.whitespace();need(r.take()==b':','census object colon required');self.emit(b':');value=self.child(depth+1,key)
                        entry={'key':key,'literal_key':token==json.dumps(key,ensure_ascii=False,separators=(',',':')).encode('utf-8','surrogatepass'),
                            'key_span':[key_start,key_end],'ordinal':ordinal,'value':value,'replacement_candidate':replacement is not None}
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
                    if qualified:self.qualified_replacements+=1
                    for item in entries:
                        if item['ordinal']<=1:continue
                        first=next(e for e in entries if e['key']==item['key']);self.events+=1;need(self.events<=100000,'complete duplicate census count bound')
                        if not qualified:self.unknown+=1
                        event={'node_kind':node_kind,'node_id':fields.get('id',{}).get('scalar',{}).get('text'),
                            'object_start':start,'key':item['key'][:256],'key_sha256':hashlib.sha256(item['key'].encode('utf-8','surrogatepass')).hexdigest(),
                            'ordinal':item['ordinal'],'first_key_span':first['key_span'],'key_span':item['key_span'],
                            'first_value':first['value'],'next_value':item['value'],'role_qualified':qualified,'reason':reason,
                            'values_structurally_identical':first['value']['ordered_merkle_sha256']==item['value']['ordered_merkle_sha256']}
                        encoded=json.dumps(event,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode();self.event_hash.update(len(encoded).to_bytes(8,'big')+encoded)
                        group=json.dumps([node_kind,item['key'][:256],item['ordinal'],reason],separators=(',',':'));self.groups[group]=self.groups.get(group,0)+1;need(len(self.groups)<=256,'bounded distinct duplicate role census')
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
            eligible=self.unknown==0 and self.candidate_replacements==self.qualified_replacements==self.events and self.normalized_bytes<=134217728
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
                'prospective_normalized_token_sha256':self.normalized_hash.hexdigest(),'prospective_role_normalization_eligible':eligible,
                'prospective_normalization_refused':not eligible,
                'prospective_normalized_file_cap_fit':self.normalized_bytes<=134217728,
                'prospective_role_renames':self.qualified_replacements,'normalized_AST_retained_or_admitted':False,
                'normalization_is_original_token_identity':False,'actual_source_ABI_or_public_admission':False}
    return Census().complete()
