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
