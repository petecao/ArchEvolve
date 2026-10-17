"""2026-10-16 ET. Freeze the owned inert passive metadata source; no execution."""
import ast
import base64
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def pin(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

expected=(HERE/'expected.json').read_bytes();yaml=(HERE/'record_yaml_subset.py').read_bytes()
source=(HERE/'observer_template.py').read_text()
for key,value in {'__EXPECTED_BASE64__':base64.b64encode(expected).decode(),
    '__EXPECTED_SHA__':hashlib.sha256(expected).hexdigest(),
    '__YAML_BASE64__':base64.b64encode(yaml).decode(),'__YAML_SHA__':hashlib.sha256(yaml).hexdigest()}.items():
    assert source.count(key)==1
    source=source.replace(key,value)
ast.parse(source)
with (HERE/'observer-v2.py').open('x') as stream:stream.write(source)
print(json.dumps(pin(HERE/'observer-v2.py'),sort_keys=True))
