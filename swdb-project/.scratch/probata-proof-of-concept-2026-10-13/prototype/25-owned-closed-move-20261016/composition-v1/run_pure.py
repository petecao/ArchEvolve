"""2026-10-16 ET. Public source-rule controls with a synthetic compiler boundary.

No claim of a retained actual Lowering replay: original C/AST remain remote.
The normal public tests use real c_lowering.lower; only this pure harness replaces
that external compiler boundary with the independently specified closed input.
"""
import ast
import copy
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import runpy
import signal
import sys
import traceback
import types

import pytest

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
BODY = '''  std_vector_int source;
  std_vector_int_ctor_count_value(&source, n, 7);
  int *saved = std_vector_int_data(&source);
  std_vector_int destination;
  std_vector_int_move_ctor(&destination, &source);
  int value = (n > 0) ? saved[0] : 0;
  {
    int swdb_return = value;
    std_vector_int_dtor(&destination);
    std_vector_int_dtor(&source);
    return swdb_return;
  }
  std_vector_int_dtor(&destination);
  std_vector_int_dtor(&source);'''


def main():
    stage = sys.argv[1]
    assert stage in {'red-v1', 'green-v1', 'red-v2', 'green-v2', 'red-v3', 'green-v3', 'green-v4', 'green-v5'}
    output = Path('/private/tmp/probata-t25-owned-move-composition-'+stage)
    output.mkdir(exist_ok=False)
    (output/'swdb').mkdir(); (output/'testkit').mkdir()
    names = ['__init__.py', 'std_models.py', 'c_lowering.py', 'heap_model_vcs.py',
             'vector_reallocation_model.py', 'vector_reallocation_vcs.py',
             'vector_reallocation_inventory.py', 'vector_reallocation_private_frame.py',
             'vector_owned_transfer.py', 'vector_owned_source_view.py', 'vector_owned_move_source.py',
             'heap_reallocation.mlw', 'vector_owned_state.mlw', 'vector_owned_effects.mlw',
             'vector_reallocation_closed_evidence.py']
    if not stage.startswith('red-v1'):
        names.append('vector_owned_move_composition.py')
    pins = []
    for name in names:
        data = (PROJECT/'swdb'/name).read_bytes()
        (output/'swdb'/name).write_bytes(data)
        pins.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    for name in ('__init__.py', 'vector_owned_move.py'):
        (output/'testkit'/name).write_bytes((PROJECT/'tests/testkit'/name).read_bytes())
    fixture = output/'fixtures/proof/lowering/vector_owned_transfer.cc'
    fixture.parent.mkdir(parents=True)
    fixture.write_bytes((PROJECT/'tests/fixtures/proof/lowering/vector_owned_transfer.cc').read_bytes())
    test = output/'test_owned_move_composition.py'
    test.write_bytes((PROJECT/'tests/test_vector_owned_move_composition.py').read_bytes())
    attempts = []
    def audit(event, args):
        if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec', 'os.fork', 'ctypes.dlopen'} or event.startswith('socket.'):
            attempts.append(event)
            raise RuntimeError('pure move source controls forbid '+event)
    sys.addaudithook(audit)
    sys.path.insert(0, str(output)); sys.dont_write_bytecode = True
    signal.alarm(60)
    lowerer = types.ModuleType('swdb.c_lowering')
    syntax = ast.parse((PROJECT/'swdb/c_lowering.py').read_bytes())
    registry = [n for n in syntax.body if isinstance(n, ast.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], ast.Name) and n.targets[0].id in {'INTEGER_TYPES', 'FLOAT_TYPES', 'INTERNAL_TYPES'}]
    for node in registry:
        setattr(lowerer, node.targets[0].id, ast.literal_eval(node.value))
    node = next(n for n in syntax.body if isinstance(n, ast.ClassDef) and n.name == 'Lowering')
    values = {'dataclass': dataclass, 'field': field, 'hashlib': hashlib, 'json': json, 'Path': Path}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual-Lowering-dataclass>', 'exec'), values)
    lowerer.Lowering = values['Lowering']
    lowerer.locate = lambda: types.SimpleNamespace(missing=False)
    def lower(source, function):
        from swdb import std_models
        pieces = [('SWDB_MODEL_FAIL', std_models.MACROS), ('std_vector_int_valid', std_models.vector_logic('std_vector_int', 'int'))]
        for member in ('ctor_count_value', 'dtor', 'data', 'move_ctor'):
            for name, text in std_models.vector_member('std_vector_int', 'int', member):
                if name not in {n for n, _ in pieces}:
                    pieces.append((name, text))
        sha = hashlib.sha256(Path(source).read_bytes()).hexdigest()
        headers = '#include <stdbool.h>\n#include <stddef.h>\n#include <stdint.h>\n#include <stdlib.h>\n'
        struct = 'typedef struct std_vector_int std_vector_int;\nstruct std_vector_int { int *data; size_t size; size_t capacity; };\n'
        prototype = 'int vector_owned_move_capture(int n)'
        prefix = f'/* C lowering of {function} from {Path(source).name} (sha256 {sha}) by swdb-c-lowering 9 (kept-names.3), clang 22.1.8. Generated: do not edit. */\n'+headers+struct+'/* swdb-anchor ghost.globals */\n'
        lines = BODY.splitlines()
        blocks = [lines[:2], lines[2:3], lines[3:5], lines[5:6], lines[6:12], lines[12:13], lines[13:14]]
        anchored = []
        for index, block in enumerate(blocks, 1):
            anchored += ['  /* swdb-anchor '+function+'.s'+str(index)+'.before */', *block,
                         '  /* swdb-anchor '+function+'.s'+str(index)+'.after */']
        text = prefix+'\n'.join(s for _, s in pieces)+'\n'+prototype+';\n/* swdb-anchor '+function+'.contract */\n'+prototype+' {\n  /* swdb-anchor '+function+'.entry */\n'+'\n'.join(anchored)+'\n}\n'
        anchors = []
        for line, value in enumerate(text.splitlines(), 1):
            if '/* swdb-anchor ' not in value:
                continue
            ident = value.split('/* swdb-anchor ', 1)[1].split(' */', 1)[0]
            anchors.append({'id': ident, 'kind': 'ghost_globals' if ident == 'ghost.globals' else
                            'contract' if ident.endswith('.contract') else ident.rsplit('.', 1)[1],
                            'function': None if ident == 'ghost.globals' else function, 'line': line})
        models = tuple(n for n, _ in pieces if n != 'SWDB_MODEL_FAIL' and not n.endswith('_valid'))
        provenance = {'verdict': 'passed', 'library': {'id': 'libc++-22.1.8'}, 'models': sorted(set((*models, 'std_vector_int'))), 'substitution_requests': [], 'pure_harness_only': True}
        return lowerer.Lowering(function=function, text=text, anchors=tuple(anchors), declaration=headers+struct+prototype+';\n', parameters=(('n', 'int', False),),
            source_sha256=sha, tool={'id': 'swdb-c-lowering', 'version': '9', 'naming_rules': 'kept-names.3', 'clang': '22.1.8'},
            models=models, std_models=('std_vector_int',), allocation=True, stdlib_provenance=provenance)
    lowerer.lower = lower
    sys.modules['swdb.c_lowering'] = lowerer
    tests = runpy.run_path(str(test)); outcomes = []
    for name, function in tests.items():
        if not name.startswith('test_'):
            continue
        directory = output/name; directory.mkdir()
        try:
            function(directory)
            outcomes.append({'name': name, 'passed': True})
        except (Exception, pytest.fail.Exception) as error:
            outcomes.append({'name': name, 'passed': False, 'error': type(error).__name__+': '+str(error), 'traceback': traceback.format_exc()})
    total = sum(p.lstat().st_size for p in output.rglob('*') if p.is_file() and not p.is_symlink())
    assert total < 16*1024**2
    result = {'date': '2026-10-16 ET', 'stage': stage, 'source_pins': pins, 'outcomes': outcomes,
              'passed': sum(r['passed'] for r in outcomes), 'failed': sum(not r['passed'] for r in outcomes),
              'child_native_network_attempts': attempts, 'raw_bytes': total,
              'compiler_boundary': 'Explicit synthetic closed source input; actual Lowering dataclass, model renderer and new public module. No real parser replay or native run claimed.',
              'scientific_acceptance': False}
    path = output/'result.json'; path.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    signal.alarm(0)
    print(json.dumps({'result': str(path), 'passed': result['passed'], 'failed': result['failed'], 'attempts': attempts}))
    return int(result['failed'] != 0 or bool(attempts))


if __name__ == '__main__':
    raise SystemExit(main())
