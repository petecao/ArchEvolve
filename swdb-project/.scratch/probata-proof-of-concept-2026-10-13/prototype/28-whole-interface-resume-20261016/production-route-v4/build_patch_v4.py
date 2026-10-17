"""Materialize the proposed patch and exact bases; never apply it or call Git."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
PROJECT = WHOLE.parents[3]
OUT = HERE / 'proposed/swdb'
V3 = WHOLE / 'production-route-v3/proposed/swdb'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


published = json.loads((HERE / 'published-hook-bases-v4.json').read_bytes())
assert published['source_commit'] == '1c45737f6cff9b43731d8da530be869a7e5d745e'
base = HERE / 'base-source'
for path in base.glob('*.py'):
    assert (PROJECT / 'swdb' / path.name).read_bytes() == path.read_bytes(), path.name
patch = []; paths = []; unchanged = []; deltas = []; definitions = {}
for path in sorted(OUT.rglob('*')):
    if not path.is_file(): continue
    relative = path.relative_to(OUT).as_posix(); raw = path.read_bytes()
    old_path = base / relative
    if old_path.exists():
        old = old_path.read_bytes(); old_name = 'a/swdb-project/swdb/' + relative
    else:
        assert not (PROJECT / 'swdb' / relative).exists(), 'new path appeared in shared production: ' + relative
        old = b''; old_name = '/dev/null'
    target = 'b/swdb-project/swdb/' + relative
    patch.extend(difflib.unified_diff(old.decode().splitlines(keepends=True), raw.decode().splitlines(keepends=True),
        fromfile=old_name, tofile=target))
    paths.append({'path': 'swdb-project/swdb/' + relative, 'base': None if not old_path.exists() else pin(old_path),
                  'proposal': pin(path), 'current_shared_matches_published_base': old_path.exists()})
    previous = V3 / relative
    if previous.exists():
        prior = previous.read_bytes()
        row = {'relative': relative, 'predecessor': pin(previous), 'proposal': pin(path)}
        (unchanged if raw == prior else deltas).append(row)
        if path.suffix == '.py' and raw != prior:
            def nodes(value):
                text = value.decode()
                return {node.name: ast.get_source_segment(text, node) for node in ast.parse(text).body
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
            before, after = nodes(prior), nodes(raw)
            definitions[relative] = {'unchanged': sorted(name for name in before.keys() & after.keys() if before[name] == after[name]),
                'changed': {name: {'old': sha(before[name].encode()), 'new': sha(after[name].encode())}
                            for name in before.keys() & after.keys() if before[name] != after[name]},
                'new': sorted(after.keys() - before.keys()), 'removed': sorted(before.keys() - after.keys())}
(HERE / 'production-route-v4.patch').write_text(''.join(patch))
(HERE / 'production-paths-and-bases-v4.json').write_text(json.dumps({'source_commit': published['source_commit'],
    'shared_production_written': False, 'paths': paths, 'root_final_fresh_overlap_check_required': True}, sort_keys=True, indent=2) + '\n')
(HERE / 'predecessor-scope-v4.json').write_text(json.dumps({'predecessor': 'frozen production-route-v3', 'byte_unchanged': unchanged,
    'changed': deltas, 'new': [row for row in paths if not (V3 / Path(row['path']).relative_to('swdb-project/swdb')).exists()],
    'definition_scope': definitions, 'legacy_complete_capture_preserved': True,
    'root_WP_and_member_view_additions_preserved': True}, sort_keys=True, indent=2) + '\n')
print(json.dumps({'patch': pin(HERE / 'production-route-v4.patch'), 'proposed_paths': len(paths),
    'unchanged_V3_files': len(unchanged), 'changed_V3_files': len(deltas), 'shared_production_written': False}))
