"""2026-10-16 ET. Strict token-preserving full JSON identity projection.

No AST nodes are omitted and no JSON value/key/order/token spelling changes.
Complete gzip provenance and downstream full-TU semantic checks remain required.
No compiler, subprocess, network or project imports.
"""
import hashlib
import json
import re

CHUNK=65536
MAX_RETAINED=134217728
MAX_RAW=2147483648


class Refused(ValueError):pass


def need(ok,message):
    if not ok:raise Refused(message)


class Reader:
    def __init__(self,source,limit,check):
        self.source=source;self.limit=limit;self.check=check;self.buffer=b'';self.at=0;self.count=0;self.hash=hashlib.sha256();self.eof=False
    def fill(self):
        if self.at==len(self.buffer) and not self.eof:
            self.check();chunk=self.source.read(CHUNK)
            need(type(chunk) is bytes and len(chunk)<=CHUNK,'bounded original binary JSON read required')
            self.count+=len(chunk);need(self.count<=self.limit,'complete raw JSON allowance exceeded')
            self.hash.update(chunk);self.buffer=chunk;self.at=0;self.eof=not chunk
    def available(self):
        self.fill();return self.buffer[self.at:]
    def peek(self):
        self.fill();return self.buffer[self.at] if self.at<len(self.buffer) else None
    def take(self,count=1):
        self.fill();need(0<count<=len(self.buffer)-self.at,'truncated original JSON stream')
        start=self.at;self.at+=count;return self.buffer[start:self.at]
    def whitespace(self):
        while True:
            value=self.available()
            if not value:return
            match=re.search(rb'[^ \t\r\n]',value);count=match.start() if match else len(value)
            if count:self.take(count)
            if match:return


class Minifier:
    def __init__(self,source,sink,*,raw_limit,retained_limit,check):
        need(type(raw_limit) is int and 0<raw_limit<=MAX_RAW and type(retained_limit) is int
            and 0<retained_limit<=MAX_RETAINED,'explicit raw/retained identity-projection limits required')
        self.reader=Reader(source,raw_limit,check);self.sink=sink;self.check=check;self.raw_limit=raw_limit
        self.retained_limit=retained_limit;self.output=bytearray();self.output_bytes=0;self.output_hash=hashlib.sha256()
        self.tokens=0;self.max_depth=0;self.key_bytes=0;self.peak_key_bytes=0;self.objects=0;self.arrays=0;self.keys=0
    def emit(self,value):
        need(type(value) is bytes and self.output_bytes+len(value)<=self.retained_limit,'complete minified TU exceeds retained file cap')
        self.output_bytes+=len(value);self.output_hash.update(value)
        # Never combine a maximum string token with the existing buffer into a
        # write larger than the final metadata reserve. Every write <=64 KiB.
        at=0
        while at<len(value):
            amount=min(CHUNK-len(self.output),len(value)-at)
            self.output.extend(value[at:at+amount]);at+=amount
            if len(self.output)==CHUNK:self.flush()
    def flush(self):
        self.check()
        if self.output:
            need(self.sink.write(self.output)==len(self.output),'short minified artifact write');self.output.clear()
    def string(self,*,key=False):
        r=self.reader;need(r.take()==b'"','JSON string required');token=bytearray(b'"')
        while True:
            available=r.available();need(available,'truncated JSON string')
            match=re.search(rb'["\\\x00-\x1f]',available);count=match.start() if match else len(available)
            if count:token.extend(r.take(count))
            need(len(token)<= (4096 if key else 1048576),'bounded compiler JSON key/string required')
            if not match:continue
            marker=r.take();token.extend(marker)
            if marker==b'"':break
            need(marker==b'\\','raw JSON string control byte refused');token.extend(r.take())
        need(len(token)<= (4096 if key else 1048576),'bounded complete compiler JSON string required')
        try:decoded=json.loads(token.decode('utf-8'))
        except (ValueError,UnicodeError) as error:raise Refused('invalid compiler JSON UTF8/escape') from error
        need(type(decoded) is str,'ordinary JSON string required');self.emit(bytes(token));return decoded
    def scalar(self):
        r=self.reader;byte=r.peek()
        if byte==34:self.string();return
        for token in (b'true',b'false',b'null'):
            if byte==token[0]:
                for part in token:need(r.take()==bytes([part]),'malformed JSON literal')
                self.emit(token);return
        token=bytearray()
        while r.peek() is not None and r.peek() in b'-+0123456789.eE':
            token.extend(r.take());need(len(token)<=128,'bounded JSON number required')
        need(re.fullmatch(rb'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?',token),'malformed JSON scalar')
        # Preserve the numeric lexeme; the unchanged full-TU decoder retains its
        # finite-number policy rather than reformatting a value here.
        self.emit(bytes(token))
    def value(self,depth=0):
        need(depth<=256,'bounded complete compiler JSON depth required');self.max_depth=max(self.max_depth,depth)
        self.tokens+=1;need(self.tokens<=20000000,'bounded complete JSON token count required')
        if self.tokens%4096==0:self.check()
        r=self.reader;r.whitespace();byte=r.peek()
        if byte==123:
            self.objects+=1;self.emit(r.take());r.whitespace();seen=set();charged=0
            if r.peek()!=125:
                while True:
                    key=self.string(key=True);need(key not in seen,'duplicate compiler JSON key')
                    seen.add(key);count=len(key.encode('utf-8','surrogatepass'))+64;charged+=count;self.key_bytes+=count;self.keys+=1
                    self.peak_key_bytes=max(self.peak_key_bytes,self.key_bytes)
                    need(len(seen)<=1024 and self.key_bytes<=16777216,'bounded live JSON key census required')
                    r.whitespace();need(r.take()==b':','JSON object colon required');self.emit(b':');self.value(depth+1);r.whitespace()
                    marker=r.take();need(marker in (b',',b'}'),'JSON object delimiter required');self.emit(marker)
                    if marker==b'}':break
                    r.whitespace()
            else:self.emit(r.take())
            self.key_bytes-=charged
        elif byte==91:
            self.arrays+=1;self.emit(r.take());r.whitespace()
            if r.peek()!=93:
                while True:
                    self.value(depth+1);r.whitespace();marker=r.take();need(marker in (b',',b']'),'JSON array delimiter required');self.emit(marker)
                    if marker==b']':break
            else:self.emit(r.take())
        else:self.scalar()
    def run(self):
        self.value();self.reader.whitespace();need(self.reader.peek() is None,'one complete original JSON stream only')
        need(self.key_bytes==0,'complete JSON key-stack closure required');self.flush()
        return {'schema':'full-tu-token-preserving-identity-1','raw_bytes':self.reader.count,'raw_sha256':self.reader.hash.hexdigest(),
            'minified_bytes':self.output_bytes,'minified_sha256':self.output_hash.hexdigest(),'raw_limit':self.raw_limit,
            'retained_limit':self.retained_limit,'objects':self.objects,'arrays':self.arrays,'values':self.tokens,'keys':self.keys,
            'max_depth':self.max_depth,'peak_live_key_charge':self.peak_key_bytes,'complete_JSON_syntax_and_duplicate_key_check':True,
            'outside_string_whitespace_only_removed':True,'all_token_spellings_and_key_order_preserved':True,
            'AST_nodes_elided':False,'independent_filtered_parse_join':False,'downstream_complete_TU_consumer_required':True,
            'compiler_success_or_source_admission_inferred':False}


def minify(source,sink,*,raw_limit,retained_limit,check):
    return Minifier(source,sink,raw_limit=raw_limit,retained_limit=retained_limit,check=check).run()
