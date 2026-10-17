"""Source-only assembly of complete ordered-pair census; never actual reader."""
import ast
from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'compiler-duplicate-diagnostic-v1/duplicate_metadata_v1.py'
source=OLD.read_text();tree=ast.parse(source);old=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='locate');before=ast.get_source_segment(source,old)
body=(HERE/'census_parser_fragment_v1.py').read_text();module=ast.parse(body);functions='\n\n'.join(ast.get_source_segment(body,n) for n in module.body if isinstance(n,ast.FunctionDef))
assert source.count(before)==1;source=source.replace(before,functions,1)
source=source.replace('INERT first-duplicate metadata diagnostic, never JSON admission.','INERT complete ordered-pair duplicate census, never JSON admission.')
source=source.replace('report=locate(decoded,base,check)\n        while decoded.read(65536):check()','report=census(decoded,base,check)')
source=source.replace("need(decoded.verified,'entire original raw/gzip identity must verify')", "need(decoded.verified,'entire original raw/gzip identity must verify')\n        need((report['raw_bytes'],report['raw_sha256'])==(receipt['expanded_bytes'],receipt['expanded_sha256']) and report['duplicate_events']>0,'complete raw census attribution/refusal differs')")
source=source.replace("'schema':'first-strict-duplicate-metadata-1'","'schema':'complete-duplicate-role-census-1'").replace("'first_duplicate':report","'census':report")
source=source.replace("'<reviewed-duplicate-metadata-stdin>'","'<reviewed-complete-duplicate-census-stdin>'")
(HERE/'complete_duplicate_census_v1.py').write_text(source)
print('authored only')
