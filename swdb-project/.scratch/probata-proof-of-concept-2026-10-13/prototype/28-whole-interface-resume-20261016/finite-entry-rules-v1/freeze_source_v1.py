"""2026-10-16 Eastern. Pure metadata source packet author."""
import ast
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def pin(path):
    raw=path.read_bytes();return dict(path=str(path.resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def main():
    tree=ast.parse((HERE/'entry_rules_v1.py').read_bytes())
    sources=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCE_PINS' for t in n.targets)))
    for row in sources.values():assert pin(Path(row['path']))==row
    own=sorted(p for p in HERE.rglob('*') if p.is_file() and p.name!='source-packet-v1.json')
    assert not list(HERE.rglob('__pycache__'))
    for path in own:
        if path.suffix=='.py':ast.parse(path.read_bytes())
    finite=HERE.parent/'finite-trace-public-v2'
    basis=[Path(row['path']) for row in sources.values()]+[finite/'source-packet-v2.json',finite/'test_finite_public.py',finite/'proposed/swdb/proof_semantics.py',HERE.parents[4]/'swdb/level_rule.py',HERE.parents[4]/'swdb/handoff_level.py']
    value=dict(schema='finite-entry-rule-superset-source-packet-1',date='2026-10-16 Eastern',owned_files=[pin(p) for p in own],basis_files=[pin(p) for p in dict.fromkeys(basis)],
        fixed_finite_owner='ticket28 synthetic fixture harness',appended_generic_rule_count=7,pure_control_count=5,
        preserves_existing_source_trust_owned_context_rules_and_Eric_owner=True,canonical_append_inverse=True,
        applicability_conflict_explicit=True,typed_route_applicability_successor_required=True,
        bind_contexts_or_create_Library_or_execute_science=False,metadata_alone_grants_authority=False)
    (HERE/'source-packet-v1.json').write_bytes(json.dumps(value,sort_keys=True,separators=(',',':')).encode()+b'\n')
    print(json.dumps(dict(packet=pin(HERE/'source-packet-v1.json'),module=pin(HERE/'entry_rules_v1.py')),sort_keys=True))
if __name__=='__main__':main()
