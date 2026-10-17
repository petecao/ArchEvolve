"""2026-10-16 ET. Scratch-only explicit semantic-reader dependent source copy."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
HERE=Path(__file__).resolve().parent
WHOLE=HERE.parent
OLD=WHOLE/'abi-memory-production-v1'
TYPED=WHOLE/'finite-trace-public-v4/proposed/swdb/dx100_checked_source.py'
READER=WHOLE/'abi-enum-repair-v1/proposed/compiler_unit_adapter_v4.py'
OUT=HERE/'proposed'
SHA='b5bd7293259f69ffe4e5d6094cb6bd46c2d5527ef95cd28d0aaa95d88529e6c6'
OLD_SHA='775ab2ecf6068153a6167473129dcd416dc2727c9afe0ef6e0846bab62d3085c'
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
assert pin(TYPED)['sha256']=='1fceabc02d69ea8774148ede5fdc69be2ea895ed00fac0a9cbc784b06d19f3d9'
assert pin(READER)['sha256']==SHA
inverses={}
def transform(relative,edits,basis=None):
    basis=basis or OLD/'proposed'/relative
    text=basis.read_text();record=[]
    for old,new in edits:
        assert old!=new and text.count(old)>0,old
        record.append({'old':old,'new':new,'count':text.count(old)})
        text=text.replace(old,new)
    ast.parse(text)
    target=OUT/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
    inverses[relative]={'basis':pin(basis),'replacements':record}
    return target
for path in (OLD/'proposed').rglob('*'):
    if path.is_file():
        target=OUT/path.relative_to(OLD/'proposed');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
reader_target=OUT/'swdb/_dx100_whole/compiler_unit_adapter_v4.py'
shutil.copyfile(READER,reader_target)
# A real separate module, not an overlay of compiler_unit_adapter_v3.
source=transform('swdb/dx100_checked_source.py',[
    ('from swdb._dx100_whole import compiler_unit_adapter_v3 as compiler',
     'from swdb._dx100_whole import compiler_unit_adapter_v3 as compiler\nfrom swdb._dx100_whole import compiler_unit_adapter_v4 as semantic_compiler'),
    ('modules = (compiler, codec, model, receiver,', 'modules = (compiler, semantic_compiler, codec, model, receiver,')],TYPED)
for name in ('normalized_compiler_adapter_v1.py','memory_normalized_compiler_adapter_v1.py'):
    relative='swdb/_dx100_whole/'+name
    # Explicit consumer naming reflects that this is a changed semantic reader.
    edits=[('compiler_unit_adapter_v3 as legacy','compiler_unit_adapter_v4 as consumer'),
        (OLD_SHA,SHA),('LEGACY_SHA','CONSUMER_SHA'),('legacy.__file__','consumer.__file__'),
        ('legacy.prepare_unit','consumer.prepare_unit')]
    if name.startswith('memory_'):
        edits += [('unchanged TU consumer','selected semantic TU consumer'),
                  ('unchanged generic compiler consumer required','selected semantic compiler consumer required'),
                  ('generic compiler consumer changed','semantic compiler consumer changed'),
                  ('unchanged legacy ABI reader must identify','selected semantic ABI reader must identify')]
    else:
        edits += [('unchanged TU consumer','selected semantic TU consumer'),
                  ('unchanged physical legacy compiler consumer required','selected physical semantic compiler consumer required'),
                  ('legacy compiler consumer changed during preparation','semantic compiler consumer changed during preparation'),
                  ('unchanged legacy ABI reader must identify','selected semantic ABI reader must identify'),
                  ('The\n    legacy function is not modified.','The semantic reader is a separately pinned module; its full-TU\n    consumer function is byte-identical to the original v3 function.')]
    transform(relative,edits)
first=OUT/'swdb/_dx100_whole/normalized_compiler_adapter_v1.py'
memory=OUT/'swdb/_dx100_whole/memory_normalized_compiler_adapter_v1.py'
for name,adapter,prefix in (('normalized_capture_ingress_v2.py',first,'normalized_compiler'),
    ('memory_normalized_capture_ingress_v1.py',memory,'memory_compiler')):
    basis=OLD/'proposed/swdb/_dx100_whole'/name
    text=basis.read_text()
    old_adapter=OLD/'proposed/swdb/_dx100_whole'/adapter.name
    edits=[(pin(old_adapter)['sha256'],pin(adapter)['sha256']),
        ('source.compiler', 'source.semantic_compiler'),
        (prefix+'.LEGACY_SHA',prefix+'.CONSUMER_SHA'),(prefix+'.legacy',prefix+'.consumer')]
    if prefix=='normalized_compiler':
        edits += [('same unchanged legacy compiler module','same selected semantic compiler module')]
    else:edits += [('one unchanged generic full-TU consumer required','one selected semantic full-TU consumer required')]
    transform('swdb/_dx100_whole/'+name,edits)
write(HERE/'exact-inverses-v1.json',{'date':'2026-10-16 ET','files':inverses,'new_reader':pin(READER),
    'generic_v3_source_file_retained_unchanged':True,'typed_V4_source_scope_retained':True,
    'old_source_complete_capture_function_unchanged':True,'actual_project_or_shared_files_edited':False})
print(json.dumps({'paths':len([p for p in OUT.rglob('*') if p.is_file()]),'source':pin(source),'first_adapter':pin(first),'memory_adapter':pin(memory)}))
