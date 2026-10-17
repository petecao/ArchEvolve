"""2026-10-16 ET. Lossless bounded gzip primitives; no runner or zlib import.

Caller must gate the supplied exact stdlib zlib module, physical artifacts,
compiler exit, source/runtime closure and actual time/RSS. Hashes are attribution.
"""
import hashlib
import re

CHUNK=65536
MAX_COMPRESSED=134217728
MAX_EXPANDED=536870912


class Refused(ValueError):
    pass


def need(value,message):
    if not value:raise Refused(message)


def limits(expanded,compressed):
    need(type(expanded) is int and 0<expanded<=MAX_EXPANDED and type(compressed) is int and 0<compressed<=MAX_COMPRESSED,
        'explicit expanded/retained bounds required')


class Capture:
    def __init__(self,zlib,sink,*,expanded_limit,compressed_limit,check):
        limits(expanded_limit,compressed_limit)
        self.zlib=zlib;self.sink=sink;self.expanded_limit=expanded_limit;self.compressed_limit=compressed_limit
        self.check=check;self.raw_hash=hashlib.sha256();self.compressed_hash=hashlib.sha256()
        self.raw_bytes=0;self.compressed_bytes=0;self.finished=False
        self.encoder=zlib.compressobj(level=1,method=8,wbits=31,memLevel=8,strategy=0)

    def emit(self,data):
        self.check()
        need(type(data) is bytes and len(data)<=1048576,'bounded compressor output required')
        need(self.compressed_bytes+len(data)<=self.compressed_limit,'retained gzip limit exceeded')
        need(self.sink.write(data)==len(data),'short gzip artifact write')
        self.compressed_hash.update(data);self.compressed_bytes+=len(data)

    def feed(self,data):
        self.check();need(not self.finished,'gzip capture already finished')
        need(type(data) is bytes and 0<len(data)<=CHUNK,'bounded nonempty original stdout chunk required')
        need(self.raw_bytes+len(data)<=self.expanded_limit,'expanded compiler stream limit exceeded')
        self.raw_hash.update(data);self.raw_bytes+=len(data)
        self.emit(self.encoder.compress(data))

    def finish(self):
        self.check();need(not self.finished and self.raw_bytes>0,'one nonempty complete compiler stream required')
        self.emit(self.encoder.flush(self.zlib.Z_FINISH));self.finished=True
        return {'schema':'lossless-original-tu-gzip-1','codec':'gzip-single-member','level':1,'wbits':31,
            'method':8,'memLevel':8,'strategy':0,'expanded_limit':self.expanded_limit,'compressed_limit':self.compressed_limit,
            'expanded_bytes':self.raw_bytes,'expanded_sha256':self.raw_hash.hexdigest(),
            'compressed_bytes':self.compressed_bytes,'compressed_sha256':self.compressed_hash.hexdigest(),
            'compiler_zero_exit_and_source_runtime_checks_separately_required':True}


def check_receipt(receipt,*,expanded_limit,compressed_limit):
    limits(expanded_limit,compressed_limit)
    expected={'schema','codec','level','wbits','method','memLevel','strategy','expanded_limit','compressed_limit',
        'expanded_bytes','expanded_sha256','compressed_bytes','compressed_sha256','compiler_zero_exit_and_source_runtime_checks_separately_required'}
    need(isinstance(receipt,dict) and set(receipt)==expected,'exact lossless stream receipt required')
    for key,value in {'schema':'lossless-original-tu-gzip-1','codec':'gzip-single-member','level':1,'wbits':31,
        'method':8,'memLevel':8,'strategy':0,'expanded_limit':expanded_limit,'compressed_limit':compressed_limit,
        'compiler_zero_exit_and_source_runtime_checks_separately_required':True}.items():
        need(type(receipt[key]) is type(value) and receipt[key]==value,'fixed gzip profile differs: '+key)
    for key,limit in (('expanded_bytes',expanded_limit),('compressed_bytes',compressed_limit)):
        need(type(receipt[key]) is int and 0<receipt[key]<=limit,'lossless byte count exceeds bound')
    for key in ('expanded_sha256','compressed_sha256'):
        need(isinstance(receipt[key],str) and re.fullmatch('[0-9a-f]{64}',receipt[key]),'lossless SHA256 required')


def decode(zlib,source,receipt,*,expanded_limit,compressed_limit,check):
    check_receipt(receipt,expanded_limit=expanded_limit,compressed_limit=compressed_limit)
    decoder=zlib.decompressobj(wbits=31);raw=bytearray();raw_hash=hashlib.sha256();compressed_hash=hashlib.sha256();compressed_bytes=0
    while True:
        check();chunk=source.read(CHUNK)
        need(type(chunk) is bytes and len(chunk)<=CHUNK,'bounded physical compressed input required')
        if not chunk:break
        need(not decoder.eof,'trailing bytes/additional gzip member refused')
        compressed_bytes+=len(chunk);need(compressed_bytes<=compressed_limit,'retained gzip decode limit exceeded')
        compressed_hash.update(chunk);pending=chunk
        while True:
            check();bound=min(CHUNK,expanded_limit-len(raw)+1);prior=len(pending)
            try:output=decoder.decompress(pending,bound)
            except zlib.error as error:raise Refused('invalid gzip header/body/checksum') from error
            need(len(raw)+len(output)<=expanded_limit,'bounded expanded decode limit exceeded')
            raw.extend(output);raw_hash.update(output);pending=decoder.unconsumed_tail
            need(not decoder.unused_data,'trailing bytes/additional gzip member refused')
            if decoder.eof:
                need(not pending,'unconsumed input after gzip EOF');break
            if pending:
                need(output or len(pending)<prior,'gzip decoder made no progress');continue
            if len(output)==bound:
                pending=b'';continue
            break
    check();need(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail,'truncated/incomplete gzip stream')
    need(compressed_bytes==receipt['compressed_bytes'] and compressed_hash.hexdigest()==receipt['compressed_sha256'],
        'physical gzip count/hash differs')
    need(len(raw)==receipt['expanded_bytes'] and raw_hash.hexdigest()==receipt['expanded_sha256'],'expanded compiler count/hash differs')
    return bytes(raw)
