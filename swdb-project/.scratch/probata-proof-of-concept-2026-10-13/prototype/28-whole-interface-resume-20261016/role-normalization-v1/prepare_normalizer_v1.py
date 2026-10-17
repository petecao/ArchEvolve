"""Author inert normalization primitives from frozen census, never actual AST I/O."""
import ast
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;ORIGIN=WHOLE/'compiler-duplicate-census-v3/complete_duplicate_census_v3.py'
raw=ORIGIN.read_bytes();assert hashlib.sha256(raw).hexdigest()=='7517108384e877d6e67322a3b291662b95fa305a3bc5bab169414b6f06b0f54b'
source=raw.decode();tree=ast.parse(source)
roles=next(ast.get_source_segment(source,n) for n in tree.body if getattr(n,'name',None)=='role')
body=next(ast.get_source_segment(source,n) for n in tree.body if getattr(n,'name',None)=='census');edits=[]
def edit(before,after):
    global body
    assert body.count(before)==1,(before,body.count(before));body=body.replace(before,after,1);edits.append({'before':before,'after':after})
edit('def census(source,base,check):','def normalize(source,sink,manifest_sink,base,check):')
edit('    class Census(base[\'Minifier\']):','''    output_bytes=0;manifest_bytes=0;manifest_hash=hashlib.sha256();renames=0
    def write_output(value):
        nonlocal output_bytes
        need(output_bytes+len(value)<=134217728,'normalized retained file cap exceeded')
        for begin in range(0,len(value),65536):
            part=value[begin:begin+65536];check();need(sink.write(part)==len(part),'short normalized write');output_bytes+=len(part)
    def write_manifest(row):
        nonlocal manifest_bytes,renames
        value=json.dumps(row,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()+b'\\n'
        need(len(value)<=4096 and manifest_bytes+len(value)<=33554432,'bounded complete inverse manifest required')
        check();need(manifest_sink.write(value)==len(value),'short inverse manifest write')
        manifest_bytes+=len(value);manifest_hash.update(value);renames+=1
    class Census(base['Minifier']):''')
edit('            self.last_token=value\n','            write_output(value)\n            self.last_token=value\n')
edit('            self.last_token=token;self.stack[-1]', '            write_output(token if replacement is None else replacement)\n            self.last_token=token;self.stack[-1]')
edit('                        key=self.string(key=True);token=self.key_token;self.key_capture=False;key_end=position(r)',
     "                        key=self.string(key=True);token=self.key_token;self.key_capture=False;key_end=position(r)\n                        need(key!='swdbClangDesugaredType','original key collides with reserved role transport namespace')")
edit('                        self.emit_key(token,replacement);count=', '                        normalized_key_start=self.normalized_bytes\n                        self.emit_key(token,replacement);normalized_key_end=self.normalized_bytes;count=')
edit("'key_span':[key_start,key_end],'ordinal':ordinal", "'key_span':[key_start,key_end],'normalized_key_span':[normalized_key_start,normalized_key_end],'ordinal':ordinal")
edit("                    if qualified:self.qualified_replacements+=1", """                    if qualified:
                        self.qualified_replacements+=1
                        item=next(row for row in entries if row['key']=='type' and row['ordinal']==2)
                        write_manifest({'schema':'llvm22-type-role-rename-1','role':reason,
                            'node_id':fields['id']['scalar']['text'],'original_key_span':item['key_span'],
                            'normalized_key_span':item['normalized_key_span'],'original_token':'"type"',
                            'normalized_token':'"swdbClangDesugaredType"'})""")
edit('    return Census().complete()', '''    result=Census().complete()
    need(result['prospective_role_normalization_eligible'] is True,'unknown role/order/shape/collision prevents transport publication')
    need(renames==result['duplicate_events']==result['prospective_role_renames'],'complete inverse rename census differs')
    need(output_bytes==result['prospective_normalized_token_bytes'],'written normalized extent differs')
    result.pop('normalized_AST_retained_or_admitted')
    result.update(schema='llvm22-original-tu-role-transport-1',normalized_AST_written=True,normalized_AST_admitted=False,
        normalized_bytes=output_bytes,normalized_sha256=result['prospective_normalized_token_sha256'],
        inverse_manifest_bytes=manifest_bytes,inverse_manifest_sha256=manifest_hash.hexdigest(),inverse_manifest_rows=renames,
        original_TU_source_ABI_or_public_admission=False)
    return result''')
restored=body
for row in reversed(edits):assert restored.count(row['after'])==1;restored=restored.replace(row['after'],row['before'],1)
assert restored==next(ast.get_source_segment(source,n) for n in tree.body if getattr(n,'name',None)=='census')
prefix='''"""2026-10-16 ET. INERT prospective paired-Type lossless transport primitives.

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
'''
suffix=(HERE/'inverse_fragment_v1.py').read_text()
(HERE/'role_normalizer_v1.py').write_text(prefix+'\n'+roles+'\n\n'+body+'\n\n'+suffix)
(HERE/'exact-census-origin-v1.json').write_text(json.dumps({'origin':{'path':str(ORIGIN),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()},
    'copied_role_AST_exact':True,'census_function_text_inverse':True,'edits':edits,'actual_executed':False},sort_keys=True,indent=2)+'\n')
print('Authored normalizer source only; no normalization executed.')
