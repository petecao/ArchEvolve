"""2026-10-16 ET. Compiler-free initialized-register routing regressions.

Run as a standalone unittest module, bypassing compiler-aware pytest fixtures.
Exact AST projections exercise public function bodies with real source bytes;
they do not establish full-package import, CLI, compiler, parser, or proof
acceptance. Compiler discovery/runtime in identity tests are named stand-ins.
"""
import ast
import hashlib
import json
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


class PureProjection:
    """Load unchanged named definitions without tool-discovering module imports."""

    def __enter__(self):
        self.saved = {key: value for key, value in sys.modules.items()
                      if key == 'swdb' or key.startswith('swdb.')}
        for key in self.saved:
            del sys.modules[key]
        self.package = types.ModuleType('swdb')
        self.package.__path__ = []
        sys.modules['swdb'] = self.package
        return self

    def __exit__(self, *_):
        for key in list(sys.modules):
            if key == 'swdb' or key.startswith('swdb.'):
                del sys.modules[key]
        sys.modules.update(self.saved)

    def load(self, name, names, *, folder=None):
        path = (folder or PROJECT / 'swdb') / (name + '.py')
        tree = ast.parse(path.read_bytes(), filename=str(path))
        selected = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
                selected.append(node)
            elif isinstance(node, (ast.Assign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(isinstance(target, ast.Name) and target.id in names for target in targets):
                    selected.append(node)
        module = sys.modules.get('swdb.' + name) or types.ModuleType('swdb.' + name)
        module.__file__ = str(path)
        module.__dict__.update(Path=Path, hashlib=hashlib, json=json, re=re)
        sys.modules[module.__name__] = module
        setattr(self.package, name, module)
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), module.__dict__)
        for name in names:
            if name not in module.__dict__:
                raise AssertionError('missing exact projected definition: ' + name)
        return module

    def layouts(self):
        for name, predicate, constant in [
            ('dx100_source_selector', 'pure_layout', 'PURE_LAYOUT'),
            ('dx100_size_source', 'size_layout', 'LAYOUT'),
            ('dx100_stream_source', 'stream_layout', 'LAYOUT'),
            ('dx100_allocation_source', 'allocation_layout', 'LAYOUT'),
            ('dx100_register_source', 'register_layout', 'LAYOUT'),
            ('dx100_initialized_register_source', 'initialized_register_layout', 'LAYOUT'),
        ]:
            self.load(name, [predicate, constant])


class InitializedRouting(unittest.TestCase):
    def test_public_render_and_state_draws_preserve_only_the_ordinary_namespace(self):
        with PureProjection() as pure:
            pure.layouts()
            pure.load('proof', ['AdapterError'])
            pure.load('dx100_interface', ['contract_rows'])
            api = pure.load('proof_semantics', ['acsl_source', '_model_state', '_bounded_state',
                                               'state_draws', '_constants', 'check_defines'])
            state = ('int SPD_count;\nint REG_count;\nsigned char region_count;\n'
                     'static unsigned int __swdb_dx_reg_words[32];\n')
            data = {'model': {'layout': 'dx100-initialized-u32-register-partial-v1'}}
            texts = {'model.state': state, 'model.logic': '', 'ghost.acsl': ''}
            self.assertEqual(api.acsl_source(data, texts, rows=[]), '#include <stdint.h>\n' + state + '\n')
            library = types.SimpleNamespace(get=lambda _: data)
            self.assertEqual(api.state_draws(library, 'semantics.control'), [])
            data = {'constants': {'DX_NT': 2, 'DX_TS': 2}}
            self.assertEqual(api.state_draws(library, 'semantics.control'), [
                'dx_tile_data[0][0]', 'dx_tile_data[0][1]', 'dx_tile_data[1][0]', 'dx_tile_data[1][1]'])

    def test_public_lowering_options_bind_init_and_typed_calls_to_the_distinct_source_policy(self):
        with PureProjection() as pure:
            pure.layouts()
            size = pure.load('dx100_size_source', ['SOURCE_PINS', 'KIND'])
            for module in ['dx100_source_selector', 'dx100_stream_source', 'dx100_allocation_source', 'dx100_register_source']:
                pure.load(module, ['KIND'])
            original = pure.load('dx100_register_model', ['ENTRY'])
            # Exact initialized model declarations depend on two old-model names.
            model = pure.load('dx100_initialized_register_model', ['PROTOTYPES'])
            tree = ast.parse((PROJECT / 'swdb/dx100_initialized_register_model.py').read_bytes())
            entry = next(node for node in tree.body if isinstance(node, ast.Assign)
                         and any(isinstance(target, ast.Name) and target.id == 'ENTRY' for target in node.targets))
            model.__dict__['REGISTER_ENTRY'] = original.ENTRY
            exec(compile(ast.Module(body=[entry], type_ignores=[]), 'initialized-entry', 'exec'), model.__dict__)
            source = pure.load('dx100_initialized_register_source', ['KIND', 'Refused', '_same', '_hash', 'policy'])
            pure.load('dx100_initialized_register_source', ['_logical_reference'])
            source.__dict__.update(ENTRY=model.ENTRY, PROTOTYPES=model.PROTOTYPES, SOURCE_PINS=size.SOURCE_PINS)
            paths = types.ModuleType('swdb.paths'); paths.HOME = PROJECT
            sys.modules[paths.__name__] = paths; pure.package.paths = paths
            pins = []
            for name, digest in size.SOURCE_PINS.items():
                path = PROJECT / ('apps/dx100/benchmarks/API/' + name if name in {'MAA.hpp', 'MAA_gem5.hpp'}
                                  else 'tests/fixtures/proof/dx100/gem5-e4fc4af/' + name)
                pins.append({'root':'project','path':str(path.relative_to(PROJECT)),'sha256':digest})

            library_file=PROJECT/'swdb/library.py';library_tree=ast.parse(library_file.read_bytes())
            original_library=next(n for n in library_tree.body if isinstance(n,ast.ClassDef)and n.name=='Library')
            methods=[n for n in original_library.body if isinstance(n,ast.FunctionDef)and n.name in {'resolve','_pin'}]
            shell=ast.ClassDef(name='Library',bases=[],keywords=[],body=methods,decorator_list=[],type_params=[])
            context={'Path':Path,'paths':paths,'re':re,'artifacts':types.SimpleNamespace(file_hash=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest())}
            exec(compile(ast.fix_missing_locations(ast.Module(body=[shell],type_ignores=[])),str(library_file),'exec'),context)

            def definition(call):
                return {'kind': 'dx100-initialized-u32-register-v1', 'call': call, 'entry': model.ENTRY, 'sources': pins}

            data = {'kind': 'proof_semantics', 'target': 'initialized-control',
                    'model': {'layout': 'dx100-initialized-u32-register-partial-v1'},
                    'calls': [{'call': 'init_MAA', 'supported': True, 'definition': definition('init_MAA')},
                              *[{'call': call, 'supported': True, 'instances': [
                                  {'arguments': ['unsigned int'], 'arity': 1, 'definition': definition(call)}]}
                                for call in ['get_new_reg', 'get_reg']]]}
            library = context['Library'](); library.root = PROJECT/'library'; library.entries = {'semantics.control': data}
            api = pure.load('proof_semantics', ['TILE_POINTER', 'current', 'covered_names', 'lowering_options'])
            options = api.lowering_options(library)['semantics']
            self.assertEqual(set(options['source_definitions']), {'init_MAA'})
            for policy in [options['source_definitions']['init_MAA'],
                           *[options['template_instances'][call][0]['definition'] for call in ['get_new_reg', 'get_reg']]]:
                self.assertEqual(policy['kind'], 'dx100-initialized-u32-register-v1')
                self.assertEqual(len(policy['sources']), 7)

    def test_public_identity_recipes_change_with_either_initialized_policy_input(self):
        with tempfile.TemporaryDirectory(prefix='initialized-identity-') as folder, PureProjection() as pure:
            stage = Path(folder)
            total = 0
            for path in (PROJECT / 'swdb').iterdir():
                if path.is_file() and not path.is_symlink():
                    body = path.read_bytes(); total += len(body)
                    self.assertLess(total, 32 * 1024**2)
                    (stage / path.name).write_bytes(body)
            paths = types.ModuleType('swdb.paths'); paths.VOCAB = PROJECT / 'vocab'
            sys.modules[paths.__name__] = paths; pure.package.paths = paths
            setup = pure.load('proof_setup', ['CHECK_SOURCES', 'SETUP_VERSION', 'READING_VERSION', '_sha', '_digest', 'identity'], folder=stage)
            lower = pure.load('c_lowering', ['TOOL_ID', 'TOOL_VERSION', 'NAMING_RULES', 'RULES', 'RULES_SHA256', 'naming_rules', 'identity'], folder=stage)
            lower.locate = lambda: types.SimpleNamespace(missing='SYNTHETIC: discovery disabled')
            lower.stdlib_provenance = types.SimpleNamespace(runtime_identity=lambda _: {'synthetic_missing_compiler': True})
            lower.terminal_release = types.SimpleNamespace(__file__=str(stage / 'terminal_release.py'))
            lower.cpu_effects = types.SimpleNamespace(__file__=str(stage / 'cpu_effects.py'))
            lower.bounded_initialization = pure.load('bounded_initialization', ['identity'], folder=stage)
            lower.wp_pointer_bounds = pure.load('wp_pointer_bounds', ['identity'], folder=stage)
            before = setup.identity(), lower.identity()
            for name in ['dx100_initialized_register_source.py', 'dx100_initialized_register_model.py']:
                with self.subTest(changed_input=name):
                    path = stage / name; original = path.read_bytes()
                    path.write_bytes(original + b'\n# Synthetic identity mutation, 2026-10-16 ET.\n')
                    try:
                        self.assertNotEqual(setup.identity(), before[0])
                        self.assertNotEqual(lower.identity(), before[1])
                    finally:
                        path.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
