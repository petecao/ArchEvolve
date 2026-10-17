"""2026-10-16 ET. No-child source/AST preparation; never compile or run C.

Loads only the new standard-library source preparer. Existing backend generators
are read as AST and their closed string expressions are interpreted as data;
their Python modules are not imported or executed.
"""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


DIRECTORY = Path(__file__).resolve().parent
PROJECT = Path(__file__).resolve().parents[4]
BACKEND = DIRECTORY.parent / '28-proof-semantics'


def no_children(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        raise RuntimeError('source preparation refuses ' + event)


sys.addaudithook(no_children)
sys.dont_write_bytecode = True
sys.pycache_prefix = str(DIRECTORY / '.nonexistent-private-bytecode-prefix')
if Path(sys.pycache_prefix).exists() or Path(sys.pycache_prefix).is_symlink():
    raise ValueError('nonexistent private source cache prefix required')


def pin(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def literal_render(path, arguments):
    """Evaluate only the pinned generators' literal string/Name/Add grammar."""
    tree = ast.parse(Path(path).read_text())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'render_header']
    if len(functions) != 1:
        raise ValueError('one render_header definition required')
    function = functions[0]
    if {argument.arg for argument in function.args.args} != set(arguments):
        raise ValueError('closed backend string renderer arguments differ')
    values = dict(arguments)
    def string(expression):
        if isinstance(expression, ast.Constant) and type(expression.value) is str:
            return expression.value
        if isinstance(expression, ast.Name) and expression.id in values:
            return values[expression.id]
        if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add):
            return string(expression.left) + string(expression.right)
        raise ValueError('backend expression is not a closed source string')
    for statement in function.body:
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
            values[statement.targets[0].id] = string(statement.value)
        elif isinstance(statement, ast.Return):
            return string(statement.value)
        else:
            raise ValueError('backend renderer has an executable/nonliteral statement')
    raise ValueError('backend renderer did not return a source string')


def main():
    spec = importlib.util.spec_from_file_location('new_source_preparer', DIRECTORY / 'interface_memory.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    dependencies = [pin(BACKEND / name) for name in ['deferred_state.py', 'command_state.py', 'region_state.py']]
    values = literal_render(BACKEND / 'deferred_state.py', {})
    command = literal_render(BACKEND / 'command_state.py', {'values_header': values})
    backend = literal_render(BACKEND / 'region_state.py', {'command_header': command})
    (DIRECTORY / 'backend_for_prepare.h').write_text(backend)
    binding = module.write_preparation(PROJECT, DIRECTORY)
    if [pin(row['path']) for row in dependencies] != dependencies:
        raise ValueError('backend source changed during preparation')
    files = ['interface_memory.py', 'test_source_preparation.py', 'native_prepare_cases.c',
             'prepare_artifacts.py', 'binding.json', 'interface_memory_prepare.h',
             'backend_for_prepare.h', 'pure-tests.log']
    manifest = {'date': '2026-10-16 ET', 'scope': 'source-only preparation; native harness is prospective and unexecuted',
                'backend_generator_pins': dependencies, 'artifacts': [pin(DIRECTORY / name) for name in files],
                'pinned_upstream_sources': binding['sources'], 'memory_call_preparers': 7,
                'pure_role_controls': 16, 'native_controls_planned': 53,
                'backend_assembly': 'closed AST string interpretation, no existing project Python import/execution',
                'native_execution': False, 'compiler_execution': False, 'runtime_admission': False,
                'public_support': False, 'whole_call_binding': False, 'current_0_2': False}
    (DIRECTORY / 'source-manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
    if Path(sys.pycache_prefix).exists() or Path(sys.pycache_prefix).is_symlink():
        raise ValueError('source cache prefix unexpectedly created')
    print(json.dumps({'source_only': True, 'call_preparers': 7, 'backend_generators_read': 3,
                      'native_controls_planned_not_executed': 53, 'manifest': pin(DIRECTORY / 'source-manifest.json')}, sort_keys=True))


if __name__ == '__main__':
    main()
