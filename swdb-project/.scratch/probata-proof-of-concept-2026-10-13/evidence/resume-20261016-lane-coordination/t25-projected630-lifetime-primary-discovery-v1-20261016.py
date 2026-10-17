"""2026-10-16 ET. Passive primary WP lifetime implementation attribution."""
import hashlib,json,re,signal
from pathlib import Path
signal.alarm(20)
root=Path('/data1/yanruj/probata-verifiers/opam/framac-33/lib/frama-c-wp/core')
rows=[]
for f in sorted(root.rglob('*')):
 if f.suffix not in {'.ml','.mli'} or not f.is_file():continue
 lines=f.read_text().splitlines();hits=[]
 for i,line in enumerate(lines):
  if re.search(r'\b(?:[Pp]_?(?:fresh|freeable|allocable|dangling)|P(?:fresh|freeable|allocable|dangling))\b|\\(?:fresh|freeable|allocable|dangling)|[Ii]gnor.*(?:alloc|fresh|dangling)|(?:alloc|fresh|dangling).*[Ii]gnor',line):
   hits.append({'line':i+1,'line_sha256':hashlib.sha256(line.encode()).hexdigest(),'source_excerpt':line.strip()[:240],'nearby_symbols':sorted(set(re.findall(r'\b(?:unsupported|not_implemented|e_true|e_false|p_true|p_false|freeable|allocable|dangling|ignored|Warning|WarningSet|not_yet|fresh)\b','\n'.join(lines[max(0,i-3):i+5]))))})
 if hits:rows.append({'relative':str(f.relative_to(root)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'sites':hits})
print(json.dumps({'created':'2026-10-16 ET','primary_source_sites':rows,'compiler_or_native_or_proof_calls':0,'raw_C_AST_SMT_exported':False},sort_keys=True))
