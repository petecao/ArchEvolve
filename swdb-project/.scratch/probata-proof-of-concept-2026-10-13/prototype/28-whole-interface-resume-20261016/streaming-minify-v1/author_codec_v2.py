"""Inert text-only successor assembly; no runner invocation."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
old=(HERE.parent/'lossless-capture-v1/lossless_gzip_v1.py').read_text()
head=old[:old.index('\ndef decode(')].replace('MAX_EXPANDED=536870912','MAX_EXPANDED=2147483648')
body='''
class DecodeReader:
    """Bounded raw chunks, no accumulated raw DOM; verifies true physical EOF."""
    def __init__(self,zlib,source,receipt,*,expanded_limit,compressed_limit,check):
        check_receipt(receipt,expanded_limit=expanded_limit,compressed_limit=compressed_limit)
        self.zlib=zlib;self.source=source;self.receipt=receipt;self.expanded_limit=expanded_limit
        self.compressed_limit=compressed_limit;self.check=check;self.decoder=zlib.decompressobj(wbits=31)
        self.raw_hash=hashlib.sha256();self.compressed_hash=hashlib.sha256();self.raw_bytes=0;self.compressed_bytes=0
        self.pending=b'';self.need_input=True;self.verified=False

    def input(self):
        self.check();chunk=self.source.read(CHUNK)
        need(type(chunk) is bytes and len(chunk)<=CHUNK,'bounded physical compressed input required')
        self.compressed_bytes+=len(chunk);need(self.compressed_bytes<=self.compressed_limit,'retained gzip decode limit exceeded')
        self.compressed_hash.update(chunk);return chunk

    def finish(self):
        need(self.decoder.eof and not self.decoder.unused_data and not self.decoder.unconsumed_tail,'truncated/incomplete gzip stream')
        need(not self.input(),'trailing bytes/additional gzip member refused')
        need(self.compressed_bytes==self.receipt['compressed_bytes'] and self.compressed_hash.hexdigest()==self.receipt['compressed_sha256'],
            'physical gzip count/hash differs')
        need(self.raw_bytes==self.receipt['expanded_bytes'] and self.raw_hash.hexdigest()==self.receipt['expanded_sha256'],
            'expanded compiler count/hash differs')
        self.verified=True

    def read(self,count):
        need(type(count) is int and 0<count<=CHUNK,'bounded expanded read required')
        if self.verified:return b''
        while True:
            self.check()
            if self.need_input:
                self.pending=self.input();need(self.pending,'truncated/incomplete gzip stream')
            bound=min(count,self.expanded_limit-self.raw_bytes+1);prior=len(self.pending)
            try:output=self.decoder.decompress(self.pending,bound)
            except self.zlib.error as error:raise Refused('invalid gzip header/body/checksum') from error
            self.pending=self.decoder.unconsumed_tail
            need(not self.decoder.unused_data,'trailing bytes/additional gzip member refused')
            need(self.raw_bytes+len(output)<=self.expanded_limit,'bounded expanded decode limit exceeded')
            self.raw_bytes+=len(output);self.raw_hash.update(output)
            self.need_input=not self.pending and len(output)<bound
            if self.decoder.eof:
                self.finish();return output
            need(output or len(self.pending)<prior or self.need_input,'gzip decoder made no progress')
            if output:return output
'''
(HERE/'lossless_gzip_v2.py').write_text(head+body)
