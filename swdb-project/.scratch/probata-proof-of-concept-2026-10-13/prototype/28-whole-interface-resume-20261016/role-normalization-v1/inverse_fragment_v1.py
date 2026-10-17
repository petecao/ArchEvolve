def inverse_identity(normalized,manifest,receipt):
    """Verify the inverse token identity; never reconstruct original whitespace."""
    need(type(normalized) is bytes and len(normalized)<=134217728 and type(manifest) is bytes and len(manifest)<=33554432,
        'bounded normalized bytes and complete inverse manifest required')
    need(hashlib.sha256(normalized).hexdigest()==receipt['normalized_sha256'] and len(normalized)==receipt['normalized_bytes'],
        'normalized physical identity differs')
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
    at=0;original_end=0;digest=hashlib.sha256();count=0
    for row in rows:
        begin,end=row['normalized_key_span'];replacement=row['normalized_token'].encode();original=row['original_token'].encode()
        need(at<=begin<end<=len(normalized) and normalized[begin:end]==replacement and row['original_key_span'][0]>=original_end,
            'inverse spans overlap, reorder or replace an unexpected token')
        value=normalized[at:begin]+original;digest.update(value);count+=len(value);at=end;original_end=row['original_key_span'][1]
    digest.update(normalized[at:]);count+=len(normalized)-at
    need((count,digest.hexdigest())==(receipt['original_minified_token_bytes'],receipt['original_minified_token_sha256']),
        'inverse does not reproduce the complete original token stream')
    return {'original_minified_token_bytes':count,'original_minified_token_sha256':digest.hexdigest(),'inverse_rows':len(rows),
        'original_raw_whitespace_reconstructed':False,'original_normalized_identity_claimed':False,'source_or_ABI_admission':False}
