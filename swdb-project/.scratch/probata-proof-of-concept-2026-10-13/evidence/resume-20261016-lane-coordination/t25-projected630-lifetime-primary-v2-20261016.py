"""2026-10-16 ET. Passive exact primary unsupported-predicate branch metadata."""
import hashlib,json,signal
from pathlib import Path
signal.alarm(10)
p=Path('/data1/yanruj/probata-verifiers/opam/framac-33/lib/frama-c-wp/core/LogicSemantics.ml')
b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=='7612c77530d4fe9bb89ec0b28460685f801b10e9b32fc9bfa479548d1b6e9e03'
lines=b.decode().splitlines();selected=lines[881:895]
print(json.dumps({'created':'2026-10-16 ET','source':str(p),'sha256':hashlib.sha256(b).hexdigest(),'start_line':882,'primary_ML_excerpt':selected,'scope':'Pinned implementation source only; no raw C/AST/SMT/proof term or native execution.'},sort_keys=True))
