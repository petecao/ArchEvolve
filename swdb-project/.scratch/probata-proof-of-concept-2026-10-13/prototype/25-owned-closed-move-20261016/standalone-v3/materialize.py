"""2026-10-16 ET. Read-only Git/physical-source metadata; no tool execution.

Materialization is useful only after the shared root checkpoint is published.
The resulting inert packet still needs independent review and once-admission.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import pprint
import subprocess


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-commit', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    commit = args.source_commit
    if len(commit) != 40 or any(c not in '0123456789abcdef' for c in commit):
        raise ValueError('exact reviewed published Git SHA required')
    output = Path(args.output)
    if not str(output).startswith('/private/tmp/') or output.exists() or output.is_symlink():
        raise ValueError('fresh exact external output required')
    def git(*parts):
        return subprocess.check_output(['git', '--no-optional-locks', '--no-replace-objects',
            '-c', 'core.fsmonitor=false', '-c', 'core.preloadIndex=false', '-c', 'index.threads=1',
            '-C', str(PROJECT), *parts], timeout=30)
    if git('rev-parse', 'HEAD').decode().strip() != commit:
        raise ValueError('current root checkpoint differs; do not select an old source')
    roots = ['swdb-project/'+name for name in ('swdb', 'schemas', 'vocab')]
    explicit = ['tests/testkit/standard_library.py', 'tests/conftest.py',
        'tests/fixtures/proof/lowering/vector_owned_transfer.cc',
        'tests/fixtures/proof/methods/contract-fixture-1.yaml', 'library/methods/probata-draft-1.yaml']
    names = git('ls-tree', '--full-tree', '-r', '-z', '--name-only', commit, '--',
                *roots, *['swdb-project/'+name for name in explicit]).decode().split('\0')
    rows = []
    for name in sorted(n for n in names if n):
        relative = name.removeprefix('swdb-project/')
        path = PROJECT/relative
        raw = git('show', commit+':'+name)
        if path.is_symlink() or not path.is_file() or path.read_bytes() != raw:
            raise ValueError('selected physical source differs: '+relative)
        rows.append({'relative': relative, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    if not rows or not set(explicit) <= {row['relative'] for row in rows}:
        raise ValueError('complete source/helper/method selection is missing')
    template = (HERE/'entry-template.py').read_text()
    replacements = [("COMMIT = '__ROOT_PUBLISHED_SOURCE_COMMIT__'", 'COMMIT = '+repr(commit)),
        ('SOURCE_PINS = ()  # materializer fills the complete selected physical consumers',
         'SOURCE_PINS = '+pprint.pformat(tuple(rows), width=110, sort_dicts=True)),
        ("OUTPUT = '__FRESH_ABSOLUTE_MAC_OUTPUT__'", 'OUTPUT = '+repr(str(output)))]
    text = template
    for before, after in replacements:
        if text.count(before) != 1:
            raise ValueError('template assignment is not unique')
        text = text.replace(before, after, 1)
    ast.parse(text)
    reverse = text
    for before, after in reversed(replacements): reverse = reverse.replace(after, before, 1)
    if reverse != template:
        raise ValueError('complete materialization inverse differs')
    entry = HERE/('entry-'+commit[:8]+'.py')
    with entry.open('x') as handle: handle.write(text)
    receipt = {'date': '2026-10-16 ET', 'classification': 'INERT_COMPLETE_ORIGINAL_C_MAC_DIAGNOSTIC',
        'source_commit': commit, 'entry': pin(entry), 'template': pin(HERE/'entry-template.py'),
        'controls': pin(HERE/'test_controls.py'), 'README': pin(HERE/'README.md'),
        'source_pins': rows, 'source_roots': roots, 'explicit_helpers_and_methods': explicit,
        'full_template_inverse_exact': True, 'output': str(output),
        'guard_policy': {'workers': 1, 'RSS_cap_bytes': 8*1024**3, 'entry_seconds': 600,
            'required_outer_seconds': 720, 'native_seconds': 420, 'each_solver_seconds': 30,
            'aggregate_profile_bytes': 128*1024**2, 'existing_shared_verifier_lock': True},
        'actual_execution': False, 'independent_review_and_root_once_admission_required': True,
        'source_or_caller_admission': False,
        'runtime_boundary': 'normal method/runtime/compiler use-time observations plus explicit loader/OS/interposition TCB; no universal closure or continuous immutability claim'}
    path = HERE/('source-packet-'+commit[:8]+'.json')
    with path.open('x') as handle: handle.write(json.dumps(receipt, sort_keys=True, indent=2)+'\n')
    print(json.dumps({'packet': pin(path), 'source_consumer_count': len(rows)}, sort_keys=True))


if __name__ == '__main__':
    main()
