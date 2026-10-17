"""2026-10-16 ET. Actual helper CLI -> real CBMC bounds seam, no project/child.

The complete helper and caller functions execute with tiny inert library/YAML/
identity doubles. Their real public run_swdb call feeds exact production
_bounds_argument, _sizes and full _build. Real Interface/Plan definitions are
extracted unchanged; only translation/harness generation is a stand-in.
This tests launch bounds only, never native/proof/model acceptance.
"""
import ast
import builtins
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest


def deny(event, arguments):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn')) or event in {'os.system', 'os.fork', 'os.forkpty', 'ctypes.dlopen'}:
        raise RuntimeError('pure fixture-bound seam refuses ' + event)


sys.addaudithook(deny)
HERE = Path(__file__).resolve().parent
TRACE = HERE.parent
BASE = json.loads((HERE / 'proposal-base.json').read_text())
SPEC = importlib.util.spec_from_file_location('frozen_production_bounds_leafs', HERE / 'production_bounds_leafs.py')
leaf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(leaf)


class AdapterError(ValueError):
    pass


leaf.AdapterError = AdapterError
leaf.logic_of = lambda library: NS(block=lambda: '')
leaf.stub_fault = lambda: ()
PROTOTYPES = json.loads((HERE / 'query-prototypes.json').read_text())
ENVIRONMENT = {'SWDB_CBMC': '/inert/pinned/cbmc', 'SWDB_VERIFIER_LOCK': '/inert/lock'}


def source_namespace(path, names=None, **context):
    tree = ast.parse(path.read_text())
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.Assign)) and
             (names is None or isinstance(node, ast.FunctionDef) and node.name in names or
              isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in names for target in node.targets))]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), context)
    return context


class Seam:
    def __init__(self, root, *, helper='proposed-dx100_trust.py', caller='proposed-trace_cases.py', validate=True):
        self.root = root; self.calls = []; self.harness_calls = []; self.validate = validate
        repository, fixtures = root / 'repository', root / 'fixtures'
        for folder in ('proof_semantics', 'dx100'):
            (repository / 'library' / folder).mkdir(parents=True)
        (repository / 'library/proof_semantics/dx100_bfs_0_1.yaml').write_text(json.dumps({'calls': [], 'rules': []}))
        (fixtures / 'proof/methods').mkdir(parents=True)
        (fixtures / 'proof/methods/contract-fixture-1.yaml').write_text(json.dumps({'id': 'method.inert',
            'c_lowering': {}, 'checks': {}, 'lineup': [{'tool': name, 'version': 'inert', 'flags': []}
            for name in ('cbmc', 'frama-c-wp', 'z3', 'cvc5', 'alt-ergo')]}))
        adapter_source = Path(__file__).resolve().parents[5] / 'swdb/cbmc_adapter.py'
        # The literal method flags are inert here, but retain the actual source value.
        adapter_tree = ast.parse(adapter_source.read_text())
        frozen = next(ast.literal_eval(node.value) for node in adapter_tree.body if isinstance(node, ast.Assign) and
                      any(isinstance(target, ast.Name) and target.id == 'FROZEN' for target in node.targets))
        lowering = NS(identity=lambda: {'c_lowering': {'id': 'inert-lowering', 'sha256': '1' * 64}},
                      naming_rules=lambda: {'id': 'inert-names', 'sha256': '2' * 64})
        swdb = NS(c_lowering=lowering, cbmc_adapter=NS(FROZEN=frozen),
                  cbmc_translator=NS(identity=lambda: {'id': 'inert-translator', 'sha256': '3' * 64}),
                  proof_setup=NS(identity=lambda: {}))
        self.semantic_transform = lambda data, library: None
        def imports(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'swdb': return swdb
            if name == 'testkit.dx100_trust': return NS(run_semantics_fixture=self.helper)
            if name == 'trace_fixture': return NS(transform=self.semantic_transform)
            return builtins.__import__(name, globals, locals, fromlist, level)
        control_builtins = dict(vars(builtins), __import__=imports)
        # JSON is an inert serialization double; no installed YAML parser is imported.
        yaml = NS(safe_load=json.loads, safe_dump=lambda value, **kwargs: json.dumps(value))
        helper_context = source_namespace(HERE / helper, names={'TRUST', 'run_semantics_fixture'},
            hashlib=hashlib, json=json, shutil=shutil, sys=sys, yaml=yaml, REPO=repository, FIXTURES=fixtures,
            make_records=lambda temporary: NS(path=temporary / 'records'), run_swdb=self.public_run_swdb,
            __builtins__=control_builtins)
        self.helper = helper_context['run_semantics_fixture']
        self.caller = source_namespace(HERE / caller, QUERY_PROTOTYPES=PROTOTYPES, __builtins__=control_builtins)

    def harness(self, unit, clauses, **keywords):
        self.harness_calls.append({'unit': unit, 'clauses': clauses, **keywords})
        return 'INERT bound-seam harness', leaf.Plan(capacity=keywords['cap'])

    def public_run_swdb(self, *arguments, env=None, timeout=None):
        # This is the real helper's public run_swdb boundary: arguments are not
        # reconstructed by the test. Validate with exact production functions.
        assert arguments[0] == 'prove' and timeout == 1200
        assert env == ENVIRONMENT
        text = arguments[arguments.index('--bounds') + 1]
        call = {'arguments': list(map(str, arguments)), 'bounds_text': text}
        self.calls.append(call)
        if not self.validate: return NS(returncode=0, stdout='{}', stderr='')
        bounds = leaf._bounds_argument(text)
        sizes = leaf._sizes(bounds)
        fixture = Path(arguments[arguments.index('--records') + 1]).parent
        contract = json.loads((fixture / 'library/rewrite_contracts/trust.yaml').read_text())
        source = (fixture / 'library/proof_units/trust.cc').read_text()
        assert 'int trust_fixture(void)' in source, 'this bound seam controls a scalar zero-argument unit'
        assert 'array_domains' not in contract['proof_unit'] and contract['concurrency_frame'] == []
        unit = leaf.Interface('trust_fixture', 'int', ())
        code = NS(interface=lambda name: unit, model=None, functions=('trust_fixture',))
        adapter = NS(contract=contract['id'], library=NS(), defines=(), _knobs=lambda *args: ([], []))
        leaf.tr = NS(clauses=lambda name, chosen: chosen, harness=self.harness)
        context = {'settings': {}, 'pins': {}}
        result = leaf._build(adapter, NS(unit=NS(function='trust_fixture'), bounds=bounds), contract, code,
                             sizes, True, context)
        call.update(sizes=result['sizes'], unwind=result['unwind'], plan_type=type(result['plan']).__name__,
                    source_sha256=hashlib.sha256(source.encode()).hexdigest())
        return NS(returncode=0, stdout='{}', stderr='')

    def prove(self, row, index=0):
        directory = self.root / ('case-' + str(index)); directory.mkdir()
        return self.caller['prove'](directory, row, actual_environment=ENVIRONMENT)


class BoundsSeamControls(unittest.TestCase):
    def test_old_call_reproduces_all25_input_size_refusals_before_harness(self):
        with tempfile.TemporaryDirectory() as directory:
            seam = Seam(Path(directory).resolve(), helper='base-dx100_trust.py', caller='base-trace_cases.py')
            self.assertEqual(len(seam.caller['CASES']), 25)
            for index, row in enumerate(seam.caller['CASES']):
                with self.subTest(case=row['name']):
                    with self.assertRaisesRegex(AdapterError, 'bound input_size is not an integer parameter of trust_fixture'):
                        seam.prove(row, index)
            self.assertEqual(len(seam.calls), 25)
            self.assertEqual(seam.harness_calls, [])
            self.assertTrue(all(call['bounds_text'] == '{"threads": 1, "input_size": 1}' for call in seam.calls))

    def test_fixed_call_all25_pass_unchanged_real_bound_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            seam = Seam(Path(directory).resolve())
            for index, row in enumerate(seam.caller['CASES']):
                seam.prove(row, index)
                generated = seam.caller['source'](row)
                self.assertEqual((TRACE / 'cases' / (row['name'] + '.cc')).read_text(), generated)
            self.assertEqual(len(seam.calls), 25)
            self.assertEqual(len(seam.harness_calls), 25)
            self.assertTrue(all(call['bounds_text'] == '{"threads": 1}' and call['sizes'] == {} and call['unwind'] == 1
                                and call['plan_type'] == 'Plan' for call in seam.calls))
            self.assertTrue(all(call['unit'].parameters == () and call['cap'] == 0 for call in seam.harness_calls))

    def test_proposed_helper_old_caller_still_refuses_unknown_dimension(self):
        with tempfile.TemporaryDirectory() as directory:
            seam = Seam(Path(directory).resolve(), caller='base-trace_cases.py')
            with self.assertRaisesRegex(AdapterError, 'not an integer parameter'):
                seam.prove(seam.caller['CASES'][0])
            self.assertEqual(seam.harness_calls, [])

    def test_optional_default_byte_identity_and_explicit_empty_not_coerced(self):
        with tempfile.TemporaryDirectory() as directory:
            seam = Seam(Path(directory).resolve(), validate=False)
            for index, supplied in enumerate((None, {}, {'threads': 1, 'input_size': 1})):
                target = seam.root / ('default-' + str(index)); target.mkdir()
                keywords = {} if supplied is None else {'bounds': supplied}
                seam.helper(target, 'cbmc', tool_environment=ENVIRONMENT, **keywords)
            self.assertEqual([call['bounds_text'] for call in seam.calls],
                             ['{"threads": 1, "input_size": 1}', '{}', '{"threads": 1, "input_size": 1}'])
            with self.assertRaises(ValueError): leaf._bounds_argument(seam.calls[1]['bounds_text'])
            for invalid in ({'threads': 2}, {'threads': 1, 'n': -1}, {'threads': 1, 'n': True}):
                with self.assertRaises(AdapterError): leaf._sizes(invalid)

    def test_exact_frozen_leafs_shared_bases_and_model_boundary(self):
        project = Path(__file__).resolve().parents[5]
        for relative, metadata in BASE['production_leaf_origins'].items():
            path = project.parent / relative
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), metadata['sha256'])
        for relative, metadata in BASE['base_files'].items():
            path = HERE / ('base-' + Path(relative).name)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), metadata['sha256'])
            proposed = HERE / ('proposed-' + Path(relative).name)
            self.assertEqual(hashlib.sha256(proposed.read_bytes()).hexdigest(), metadata['proposed_sha256'])
        for name, digest in BASE['trace_model_files'].items():
            self.assertEqual(hashlib.sha256((TRACE / name).read_bytes()).hexdigest(), digest)
        old = source_namespace(HERE / 'base-trace_cases.py', QUERY_PROTOTYPES=PROTOTYPES)
        new = source_namespace(HERE / 'proposed-trace_cases.py', QUERY_PROTOTYPES=PROTOTYPES)
        self.assertEqual(old['CASES'], new['CASES'])
        self.assertTrue(all(old['source'](row) == new['source'](row) for row in old['CASES']))


if __name__ == '__main__': unittest.main(verbosity=2)
