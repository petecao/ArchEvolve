"""2026-10-16 ET. Deterministic source-only passive primitive preparation.

No project import, child, compiler, solver or actual evidence audit.
"""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACE = HERE.parent
INIT = TRACE.parent / '28-initialized-u32-resume-20261016'
PROJECT = TRACE.parents[3]
BASE_SHA = '11b4e94d269f153d91ecd016dceee6deb65beb6cd6ee7a554ec9df78f37a65d3'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def build():
    base = (INIT / 'initialized_cold_audit_v2.py').read_bytes()
    assert sha(base) == BASE_SHA
    text = base.decode(); tree = ast.parse(text)
    names = {'strict_json', 'safe_yaml', 'digest', 'absolute', 'relative', 'stable_stat',
             'Physical', 'raw_snapshot', 'source_membership', 'pure_runtime_helpers', 'runtime_closure', 'admit_reader'}
    chosen = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    assert {node.name for node in chosen} == names and len(chosen) == len(names)
    parts = [ast.get_source_segment(text, node) for node in chosen]
    head = '''"""2026-10-16 ET. Exact reviewed initialized cold primitive copies.
No main, project import, child discovery or actual evidence audit.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import types
H = lambda value: hashlib.sha256(value).hexdigest()
KERNEL_META = {'path': '/data1/yanruj/probata-verifiers/opam/framac-33/lib/frama-c/META', 'bytes': 2318,
    'sha256': '1d41605b5220bc71779ffac319ff9b06950245f5eab9f61894e865ddd9658002'}

'''
    (HERE / 'reviewed_cold_primitives_v1.py').write_text(head + '\n\n\n'.join(parts) + '\n')
    public = (TRACE / 'test_public_actual.py').read_text()
    function = next(node for node in ast.parse(public).body if isinstance(node, ast.FunctionDef) and
                    node.name == 'test_actual_public_abstract_memory_trace')
    # The producer seam (prove/CLI result/YAML capture) is separately checked
    # against persisted workflow and physical records. Preserve all assertion
    # ASTs after those inputs are captured; never call prove or project code.
    assert ast.get_source_segment(public, function.body[6]).startswith("assert record['pins']")
    suffix = function.body[6:]
    assert all(not (isinstance(node, ast.Name) and node.id in {'prove', 'pytest', 'tmp_path', 'result', 'records', 'marker'})
               for statement in suffix for node in ast.walk(statement))
    copied = ast.FunctionDef(name='audit_public_assertions_v1',
        args=ast.arguments(posonlyargs=[], args=[ast.arg(arg=name) for name in ('record', 'entry', 'row', 'semantics')],
                           kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=suffix, decorator_list=[], returns=None, type_comment=None)
    generated = ast.unparse(ast.fix_missing_locations(ast.Module(body=[copied], type_ignores=[]))) + '\n'
    restored = ast.parse(generated).body[0]
    assert [ast.dump(node, include_attributes=False) for node in restored.body] == [
        ast.dump(node, include_attributes=False) for node in suffix]
    (HERE / 'public_assertions_v1.py').write_text('"""2026-10-16 ET. Exact public assertion AST suffix; passive inputs only."""\n' + generated)
    provenance = {'date': '2026-10-16 ET', 'source_commit': '04af74c121a733589fbe1a2087ad602deaef598b',
        'base_sha256': BASE_SHA, 'copies': {node.name: sha(part.encode()) for node, part in zip(chosen, parts)},
        'public_source_sha256': sha(public.encode()), 'public_assertion_statements': len(suffix),
        'public_assertion_ast_sha256': sha(json.dumps([ast.dump(node, include_attributes=False) for node in suffix],
            separators=(',', ':')).encode()),
        'boundary': 'exact reviewed primitive nodes and complete public post-capture assertion suffix; no producer seam invocation or actual audit'}
    (HERE / 'trace-cold-primitive-provenance-v1.json').write_text(json.dumps(provenance, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    build()
