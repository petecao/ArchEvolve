"""2026-10-16 ET. Pure entry controls with every child/native tool prohibited."""
import ast
import builtins
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest


def deny(event, _args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        raise RuntimeError('checked contract controls refuse ' + event)


sys.addaudithook(deny)
HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
PROJECT = WHOLE.parents[3]
M = types.ModuleType('inert_checked_contracts')
original_import = builtins.__import__
def imports(name, *args, **kwargs):
    if name == 'swdb':
        return types.SimpleNamespace(paths=types.SimpleNamespace(HOME=PROJECT))
    return original_import(name, *args, **kwargs)
M.__dict__['__builtins__'] = dict(vars(builtins), __import__=imports)
exec(compile(ast.parse((HERE / 'dx100_whole_checked_v2.py').read_bytes()),
    str(HERE / 'dx100_whole_checked_v2.py'), 'exec'), M.__dict__)


class Library:
    def __init__(self, root):
        self.root = root

    def resolve(self, pin):
        return (self.root if pin['root'] == 'library' else PROJECT) / pin['path']

    def _pin(self, pin):
        if hashlib.sha256(self.resolve(pin).read_bytes()).hexdigest() != pin['sha256']:
            raise ValueError('physical pin changed')


class Controls(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix='inert-checked-contracts-', dir=HERE)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.library = Library(self.root)
        self.design = json.loads((WHOLE / 'new-0.2-contract-design-v1.json').read_bytes())
        design_pin = self.put('design.json', (WHOLE / 'new-0.2-contract-design-v1.json').read_bytes())
        components = [self.put(name, (WHOLE / name).read_bytes()) for name in M.COMPONENTS]
        source_pin = self.put('source-policy.json', M.canonical({'kind': M.SOURCE_KIND,
            'test_scope': 'synthetic policy shape only; not actual source admission'}))
        sources, actual = [], []
        for name in M.HEADERS:
            path = PROJECT / 'apps/dx100/benchmarks/API' / name
            raw = path.read_bytes()
            sources.append({'root': 'project', 'path': str(path.relative_to(PROJECT)),
                'sha256': hashlib.sha256(raw).hexdigest()})
            actual.extend(M.declarations(raw, name))
        self.entry = {'kind': 'proof_semantics', 'formal_frame': 1, 'version': '0.2', 'sequence': 2,
            'target': 'dx100-mmio', 'contract_form': M.KIND,
            'hardware_interface': self.design['prospective_entry']['hardware_interface'],
            'checked_body': {'design': design_pin, 'components': components,
                'source_policy': source_pin, 'choice_budget': 128},
            'calls': copy.deepcopy(self.design['calls']),
            'declaration_inventory': {'sources': sources, 'declarations': actual},
            'rules': [{'id': key, 'statement': value, 'assumed': {'owner': 'Eric' if key in M.TRUST else 'Synthetic fixture owner'},
                'record_assumption': True} for key, value in {**M.TRUST, **M.OWNED}.items()]}

    def put(self, name, raw):
        path = self.root / name
        path.write_bytes(raw)
        return {'root': 'library', 'path': name, 'sha256': hashlib.sha256(raw).hexdigest()}

    def refused(self, entry):
        with self.assertRaises((M.Refused, ValueError, TypeError, KeyError, AttributeError)):
            M.policy(self.library, entry)
        errors = []
        self.assertEqual(M.check(self.library, entry, lambda *row: errors.append(row)), [])
        self.assertTrue(errors)

    def test_complete_entry_is_structurally_checked_without_source_admission(self):
        result = M.policy(self.library, self.entry)
        self.assertEqual(len(result['contract_names']), 26)
        self.assertFalse(result['source_admission_granted'])
        self.assertFalse(result['WP_summary_supported'])
        self.assertEqual(sum(len(row['source_declarations']) for row in self.entry['calls']), 27)
        self.assertEqual(sum(len(row['typed_arity_instances']) for row in self.entry['calls']), 132)
        errors = []
        self.assertEqual(M.check(self.library, self.entry, lambda *row: errors.append(row)), [])
        self.assertEqual(errors, [])

    def test_each_of_26_deleted_contracts_refuses(self):
        for index in range(26):
            changed = copy.deepcopy(self.entry)
            del changed['calls'][index]
            with self.subTest(index=index):
                self.refused(changed)

    def test_each_type_arity_value_or_source_rule_mutation_refuses(self):
        for mutate in (
            lambda row: row['contract'].update(normal_return_state_value_relation='arbitrary value'),
            lambda row: row['contract']['asserted_domain_checks'].clear(),
            lambda row: row['contract']['owned_rules'].pop('mmio'),
            lambda row: row['source_declarations'].pop(),
            lambda row: row['typed_arity_instances'].pop(),
            lambda row: row['typed_arity_instances'][0].update(dtype=False),
            lambda row: row.update(supported=False)):
            changed = copy.deepcopy(self.entry)
            mutate(changed['calls'][0])
            self.refused(changed)

    def test_source_inventory_comes_from_both_headers_not_kernel_names(self):
        for mutate in (lambda inv: inv['sources'].pop(), lambda inv: inv['declarations'].pop(),
            lambda inv: inv['declarations'][0].update(line=999),
            lambda inv: inv['sources'][0].update(sha256='0' * 64),
            lambda inv: inv['sources'].append(inv['sources'][0])):
            changed = copy.deepcopy(self.entry)
            mutate(changed['declaration_inventory'])
            self.refused(changed)
        self.assertEqual(len(self.entry['declaration_inventory']['declarations']), 27)

    def test_old_form_and_every_version_or_interface_rebind_refuses(self):
        old = dict(self.entry, version='0.1', sequence=1)
        old.pop('contract_form')
        self.assertFalse(M.checked(old))
        self.refused(old)
        for key, value in (('version', '0.1'), ('sequence', True), ('formal_frame', True),
            ('target', 'other'), ('contract_form', 'unknown')):
            changed = copy.deepcopy(self.entry)
            changed[key] = value
            self.refused(changed)
        changed = copy.deepcopy(self.entry)
        changed['hardware_interface']['gem5_commit'] = '0' * 40
        self.refused(changed)

    def test_every_recorded_trust_entry_and_named_owner_is_mandatory(self):
        for index in range(7):
            for field, value in (('statement', 'assumed empty'), ('record_assumption', False),
                ('assumed', {'owner': ''})):
                changed = copy.deepcopy(self.entry)
                changed['rules'][index][field] = value
                self.refused(changed)
            changed = copy.deepcopy(self.entry)
            del changed['rules'][index]
            self.refused(changed)
        for index in range(5):
            changed = copy.deepcopy(self.entry)
            changed['rules'][index]['assumed']['owner'] = 'different'
            self.refused(changed)

    def test_additional_rules_need_exact_commit_citations_or_explicit_owner(self):
        good = {'id': 'test-source-citation', 'statement': 'Synthetic cited rule.',
            'cites': {'gem5_commit': M.COMMIT, 'path': 'src/mem/MAA/MAA.cc', 'lines': '563-580'}}
        self.entry['rules'].append(good)
        M.policy(self.library, self.entry)
        for change in ({'gem5_commit': '0' * 40}, {'lines': 'source'}, {'path': ''}):
            saved = copy.deepcopy(good['cites'])
            good['cites'].update(change)
            self.refused(self.entry)
            good['cites'] = saved

    def test_checked_model_has_no_acsl_query_or_wp_fallback(self):
        for key, value in (('wp', {}), ('queries', [{'query': 'unbound'}])):
            changed = copy.deepcopy(self.entry)
            changed[key] = value
            self.refused(changed)
        self.entry['queries'] = []
        self.assertFalse(M.policy(self.library, self.entry)['WP_summary_supported'])

    def test_physical_body_design_and_source_policy_mutations_refuse(self):
        for name in ('design.json', 'whole_value_backend_v1.h', 'source-policy.json'):
            path = self.root / name
            original = path.read_bytes()
            path.write_bytes(original + b' ')
            self.refused(self.entry)
            path.write_bytes(original)
        changed = copy.deepcopy(self.entry)
        changed['checked_body']['components'].pop()
        self.refused(changed)
        changed = copy.deepcopy(self.entry)
        changed['checked_body']['source_policy'] = self.put('arbitrary-policy.json', b'{"kind":"unknown"}')
        self.refused(changed)

    def test_portable_inputs_refuse_symlink_traversal_duplicates_and_nonfinite_json(self):
        target = self.root / 'source-policy.json'
        alias = self.root / 'alias.json'
        alias.symlink_to(target)
        changed = copy.deepcopy(self.entry)
        changed['checked_body']['source_policy']['path'] = alias.name
        self.refused(changed)
        for bad in ('../source-policy.json', str(target)):
            changed = copy.deepcopy(self.entry)
            changed['checked_body']['source_policy']['path'] = bad
            self.refused(changed)
        for raw in (b'{"kind":"one","kind":"two"}', b'{"kind":NaN}'):
            changed = copy.deepcopy(self.entry)
            changed['checked_body']['source_policy'] = self.put('bad-policy.json', raw)
            self.refused(changed)


    def real_resolution_library(self):
        # Execute only the real resolver method AST, with no production import
        # or catalog seed. This retains its canonicalizing behavior exactly.
        tree = ast.parse((PROJECT / 'swdb/library.py').read_bytes())
        library = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Library')
        resolver = next(node for node in library.body if isinstance(node, ast.FunctionDef) and node.name == 'resolve')
        namespace = {'Path': Path, 'paths': types.SimpleNamespace(HOME=PROJECT)}
        exec(compile(ast.Module(body=[resolver], type_ignores=[]), 'real-library-resolver-only', 'exec'), namespace)
        selected = types.SimpleNamespace(root=self.root)
        selected.resolve = types.MethodType(namespace['resolve'], selected)
        selected._pin = lambda _: (_ for _ in ()).throw(AssertionError('unbounded _pin must not run'))
        return selected

    def test_real_resolver_regular_inputs_pass_and_all_physical_aliases_refuse(self):
        self.library = self.real_resolution_library()
        M.policy(self.library, self.entry)
        for directory in (False, True):
            if directory:
                (self.root / 'linked-directory').symlink_to(self.root, target_is_directory=True)
                relative = 'linked-directory/source-policy.json'
            else:
                (self.root / 'linked-file.json').symlink_to(self.root / 'source-policy.json')
                relative = 'linked-file.json'
            row = dict(self.entry['checked_body']['source_policy'], path=relative)
            self.assertEqual(self.library.resolve(row), self.root / 'source-policy.json')
            with self.assertRaises(M.Refused):
                M.pinned(self.library, row)

    def test_root_alias_and_noncanonical_portable_spelling_refuse(self):
        selected = self.real_resolution_library()
        alias = self.root / 'alias-root'
        alias.symlink_to(self.root, target_is_directory=True)
        selected.root = alias
        with self.assertRaisesRegex(M.Refused, 'canonical physical reference root'):
            M.pinned(selected, self.entry['checked_body']['source_policy'])
        for relative in ('.', './source-policy.json', 'nested/../source-policy.json', 'source-policy.json/'):
            with self.subTest(relative=relative), self.assertRaises(M.Refused):
                M.pinned(self.library, dict(self.entry['checked_body']['source_policy'], path=relative))

    def test_size_gate_precedes_real_resolution_and_hash_or_read(self):
        path = self.root / 'large.bin'
        with path.open('wb') as handle:
            handle.truncate(4 * 1024 * 1024 + 1)
        selected = self.real_resolution_library()
        selected.resolve = lambda _: (_ for _ in ()).throw(AssertionError('resolve called before size gate'))
        with self.assertRaisesRegex(M.Refused, 'bounded canonical regular'):
            M.pinned(selected, {'root': 'library', 'path': path.name, 'sha256': '0' * 64})


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({'date': '2026-10-16 ET', 'tests': result.testsRun, 'failures': len(result.failures),
        'errors': len(result.errors), 'skips': len(result.skipped), 'child_native_or_project_execution': False}, sort_keys=True))
    raise SystemExit(not result.wasSuccessful())
