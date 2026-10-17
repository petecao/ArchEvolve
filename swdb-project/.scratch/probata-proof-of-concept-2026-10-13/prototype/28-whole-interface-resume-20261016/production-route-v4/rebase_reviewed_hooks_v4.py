"""2026-10-16 ET. Inert V3 hook rebase over exact root-published 1c bases.

Only this owned proposal tree is written. Shared files and historical proposals
are read-only. This script performs no project import, process or compiler call.
"""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import runpy
import shutil

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
V3 = WHOLE / 'production-route-v3'
PROJECT = WHOLE.parents[3]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path, root):
    raw = path.read_bytes()
    return {'path': path.relative_to(root).as_posix(), 'bytes': len(raw), 'sha256': sha(raw)}


def main():
    manifest = json.loads((HERE / 'published-hook-bases-v4.json').read_bytes())
    assert manifest['source_commit'] == '1c45737f6cff9b43731d8da530be869a7e5d745e'
    controls = runpy.run_path(str(V3 / 'build_hooks_v1.py'))
    wanted = {Path(row['path']).name: row for row in manifest['files']}
    assert set(wanted) == set(controls['TRANSFORMS'])
    out = HERE / 'proposed/swdb'
    if not out.exists():
        shutil.copytree(V3 / 'proposed/swdb', out)
    deltas, inverses, patch = [], {}, []
    for name, transform in controls['TRANSFORMS'].items():
        raw = (HERE / 'base-source' / name).read_bytes()
        assert len(raw) == wanted[name]['bytes'] and sha(raw) == wanted[name]['sha256']
        assert (PROJECT / 'swdb' / name).read_bytes() == raw, 'shared source changed after published readback'
        controls['EDITS'].clear()
        after = transform(raw.decode())
        inverse = list(controls['EDITS'])
        restored = after
        for edit in reversed(inverse):
            assert restored.count(edit['new']) == edit['count']
            restored = restored.replace(edit['new'], edit['old'], edit['count'])
        assert restored.encode() == raw, 'source-route inverse must restore every root hunk'
        ast.parse(after)
        if name != 'proof_setup.py':
            assert after.encode() == (V3 / 'proposed/swdb' / name).read_bytes()
        (out / name).write_text(after)
        deltas.append({'path': 'swdb/' + name, 'base_sha256': sha(raw), 'proposed_sha256': sha(after.encode())})
        inverses[name] = inverse
        patch.extend(difflib.unified_diff(raw.decode().splitlines(True), after.splitlines(True),
            fromfile='a/swdb/' + name, tofile='b/swdb/' + name))
    (HERE / 'reviewed-hooks-rebased-v4.patch').write_text(''.join(patch))
    (HERE / 'reviewed-hooks-rebased-inverse-v4.json').write_text(json.dumps(inverses, sort_keys=True, indent=2) + '\n')
    root_runtime = [pin(PROJECT / 'swdb' / name, PROJECT) for name in
                    ('wp_adapter.py', 'wp_pointer_bounds.py', 'standard_vector_member_view.py')]
    receipt = {'date': '2026-10-16 ET', 'source_commit': manifest['source_commit'], 'files': deltas,
        'preserved_root_runtime_inputs': root_runtime, 'source_route_hooks_unchanged_from_reviewed_v3': True,
        'proof_setup_complete_inverse_restores_published_root_bytes': True,
        'new_registry_runtime_ingress_integration': 'pending separate explicit deltas',
        'shared_production_written': False, 'scientific_execution': False}
    (HERE / 'reviewed-hooks-rebase-receipt-v4.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps(pin(HERE / 'reviewed-hooks-rebase-receipt-v4.json', HERE), sort_keys=True))


if __name__ == '__main__':
    main()
