"""2026-10-16 ET. Compiler-free real metadata seams; no profile preparation.

The third-party JSON-schema engine is replaced by a small, fail-closed evaluator
of this exact retained schema. All Library.validate Python checks, formal _entry,
concurrency/roles/placement, ACSL scanning, obligation parsing and selected-unit
checks are exact extracted source. Only source-policy selection is an explicit
protocol stand-in. Frama-C/C lowering/typechecking is deliberately not executed.
"""
import ast
import builtins
import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import runpy
import sys
import tempfile
from types import SimpleNamespace
import unittest

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
BASE = HERE / 'base-source'
ROUTE = WHOLE / 'production-route-v3/proposed/swdb'


def check_basis():
    rows = json.loads((HERE / 'test-source-basis-v2.json').read_bytes())['files']
    for row in rows:
        path = WHOLE / row['path']
        assert not path.is_symlink() and path.resolve(strict=True) == path
        raw = path.read_bytes()
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']


def no_child(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec', 'socket.connect', 'socket.bind'}:
        raise AssertionError('child/network forbidden in source controls: ' + event)
    if event == 'import' and str(args[0]).split('.')[0] == 'swdb':
        raise AssertionError('project import forbidden')


sys.addaudithook(no_child)
check_basis()
OLD = SimpleNamespace(**runpy.run_path(str(WHOLE / 'public-profile-builder-v1/profile_builder_v1.py')))
NEW = SimpleNamespace(**runpy.run_path(str(HERE / 'profile_builder_v2.py')))
SCANNER = SimpleNamespace(**runpy.run_path(str(BASE / 'acsl_subset.py')))


def extract(path, names, namespace):
    tree = ast.parse(path.read_text())
    nodes = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names]
    assert {node.name for node in nodes} == set(names)
    exec(compile(ast.Module(nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def assignments(path, names, namespace):
    found = set()
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in names for target in node.targets):
            found.update(target.id for target in node.targets if isinstance(target, ast.Name))
            exec(compile(ast.Module([node], type_ignores=[]), str(path), 'exec'), namespace)
    assert found == set(names)


def import_protocol(selected):
    def imported(name, globals=None, locals=None, fromlist=(), level=0):
        key = (name, tuple(fromlist))
        if key in selected:
            return selected[key]
        raise AssertionError('unexpected import in extracted source: ' + repr(key))
    return dict(vars(builtins), __import__=imported)


@dataclass(frozen=True)
class Problem:
    path: str
    field: str
    reason: str


class RetainedSchema:
    """Test-only schema evaluator, not a replacement for production jsonschema.

    Refuses unknown validation keywords, so omitted schema constraints cannot be
    silently accepted. Annotation keywords do not constrain instances.
    """
    def __init__(self):
        self.schema = json.loads((BASE / 'library_entry.schema.json').read_bytes())

    def iter_errors(self, data):
        def check(value, rule, path=()):
            annotations = {'$schema', '$id', 'title', 'description', '$defs'}
            supported = {'$ref', 'type', 'required', 'properties', 'allOf', 'if', 'then',
                         'const', 'enum', 'minLength', 'minItems', 'items', 'additionalProperties', 'minimum'}
            assert not set(rule) - annotations - supported, 'unimplemented schema validation keyword'
            def error(validator, message):
                return SimpleNamespace(validator=validator, path=path, message=message)
            if '$ref' in rule:
                target = self.schema
                assert rule['$ref'].startswith('#/')
                for name in rule['$ref'][2:].split('/'):
                    target = target[name]
                yield from check(value, target, path)
            kinds = {'object': lambda x: type(x) is dict, 'array': lambda x: type(x) is list,
                     'string': lambda x: type(x) is str, 'integer': lambda x: type(x) is int,
                     'null': lambda x: x is None}
            if 'type' in rule:
                choices = rule['type'] if isinstance(rule['type'], list) else [rule['type']]
                assert all(name in kinds for name in choices)
                if not any(kinds[name](value) for name in choices):
                    yield error('type', 'wrong type for retained schema'); return
            if 'enum' in rule and value not in rule['enum']:
                yield error('enum', 'outside retained schema enum')
            if 'const' in rule and value != rule['const']:
                yield error('const', 'differs from retained schema constant')
            for key, kind in (('minLength', str), ('minItems', list)):
                if key in rule and type(value) is kind and len(value) < rule[key]:
                    yield error(key, 'shorter than retained schema minimum')
            if 'minimum' in rule and type(value) is int and value < rule['minimum']:
                yield error('minimum', 'below retained schema minimum')
            if type(value) is dict:
                for name in rule.get('required', []):
                    if name not in value:
                        yield error('required', 'missing ' + name)
                for name, child in rule.get('properties', {}).items():
                    if name in value:
                        yield from check(value[name], child, path + (name,))
                if rule.get('additionalProperties') is False and set(value) - set(rule.get('properties', {})):
                    yield error('additionalProperties', 'unknown retained schema field')
            if type(value) is list and 'items' in rule:
                for index, child in enumerate(value):
                    yield from check(child, rule['items'], path + (index,))
            for child in rule.get('allOf', []):
                yield from check(value, child, path)
            if 'if' in rule and not list(check(value, rule['if'], path)):
                yield from check(value, rule.get('then', {}), path)
        return list(check(data, self.schema))


class MetadataSeam:
    """Real normal-library metadata path over generated in-memory contracts."""
    def __init__(self, folder, contracts, *, policy_rows=None):
        self.policy = {'unit_contracts': NEW.contract_rows(contracts) if policy_rows is None else policy_rows}
        source = {'json': json, 'FUNCTION': NEW.FUNCTION, 'select_baseline': lambda *_: object(),
                  'Inputs': lambda _: None, 'source_policy': lambda *_: (None, None, self.policy)}
        extract(ROUTE / 'dx100_checked_source.py',
                {'Refused', 'need', 'checked_unit_format', 'sole_whole_frame', 'unit_contract'}, source)
        self.source = source
        module = SimpleNamespace(**source)
        frame = {'re': re, 'acsl_subset': SCANNER,
                 '__builtins__': import_protocol({('swdb', ('dx100_checked_source',)):
                                                  SimpleNamespace(dx100_checked_source=module)})}
        assignments(ROUTE / 'formal_frame.py',
                    {'FRAME_VERSION', 'FRAME_FIELDS', 'CLAUSE_FIELDS', 'ROLES', 'VERSION', 'RANGE'}, frame)
        extract(ROUTE / 'formal_frame.py', {'_entry', '_placement', '_concurrency', '_roles'}, frame)
        self.frame = frame
        operations = extract(BASE / 'library_operations.py', {'chain_form_problems'}, {})
        artifacts = SimpleNamespace(**extract(BASE / 'artifacts.py', {'digest', 'file_hash'},
                                              {'json': json, 'hashlib': hashlib, 'Path': Path}))
        self.pending = []
        def metadata_check(library):
            problems = []; self.pending = []
            for ident, value in library.entries.items():
                frame['_entry'](library, ident, value,
                    lambda field, reason: problems.append(Problem(str(library.files[ident]), field, reason)),
                    {'shared_action_kinds': ['cas']}, SCANNER.LogicLibrary({}), set(), self.pending)
            return SimpleNamespace(problems=problems)
        namespace = {'re': re, 'Path': Path, 'artifacts': artifacts, 'Problem': Problem,
                     'paths': SimpleNamespace(HOME=folder), 'entry_validator': RetainedSchema,
                     '__builtins__': import_protocol({
                         ('swdb.library_operations', ('chain_form_problems',)): SimpleNamespace(**operations),
                         ('swdb', ('formal_frame',)): SimpleNamespace(formal_frame=SimpleNamespace(check=metadata_check))})}
        assignments(BASE / 'library.py', {'KINDS', 'PREFIXES', 'TEST_MODES', 'DISCHARGE_MODES', 'ROLES'}, namespace)
        original = next(node for node in ast.parse((BASE / 'library.py').read_text()).body
                        if isinstance(node, ast.ClassDef) and node.name == 'Library')
        methods = {'get', 'content_sha256', 'resolve', '_pin', 'validate'}
        selected = [node for node in original.body if isinstance(node, ast.FunctionDef) and node.name in methods]
        assert {node.name for node in selected} == methods
        # Exact original method nodes, merely housed in a class with no I/O constructor.
        cls = ast.ClassDef(name='MetadataLibrary', bases=[], keywords=[], body=selected, decorator_list=[])
        exec(compile(ast.fix_missing_locations(ast.Module([cls], type_ignores=[])), str(BASE / 'library.py'), 'exec'), namespace)
        library = namespace['MetadataLibrary']()
        library.root, library.store, library.problems = folder, None, []
        library.entries = {value['id']: value for value in contracts.values()}
        library.files = {ident: folder / 'rewrite_contracts' / (ident + '.yaml') for ident in library.entries}
        self.library = library
        translator = {'dataclass': dataclass, 'acsl_subset': SCANNER}
        extract(ROUTE / 'cbmc_translator.py', {'Untranslatable', 'Clause', 'clauses', '_tokens'}, translator)
        self.translator = translator

    def problems(self):
        return self.library.validate()

    def format(self, value):
        return self.source['checked_unit_format'](self.library, value['id'], value)

    def obligations(self, value):
        rows = self.translator['clauses'](value['id'], value['clauses'])
        self.source['unit_contract'](self.library, SimpleNamespace(policy_json=json.dumps(self.policy)),
                                     value['id'], self.library.content_sha256(value['id']), rows)
        return rows


class FormatterControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / 'proof_units').mkdir()
        raw = (WHOLE / 'source_call_fixture_v2.cpp').read_bytes()
        self.assertEqual(NEW.sha(raw), NEW.SOURCE_SHA)
        (self.root / 'proof_units/source.cpp').write_bytes(raw)
        self.proof = {'root': 'library', 'path': 'proof_units/source.cpp', 'sha256': NEW.SOURCE_SHA}

    def seam(self, contracts=None, *, old=False, policy_rows=None):
        return MetadataSeam(self.root, contracts if contracts is not None else
                            (OLD if old else NEW).unit_contracts(self.proof), policy_rows=policy_rows)

    def test_v1_red_v2_green_real_format_and_whole_metadata(self):
        old = self.seam(old=True)
        self.assertTrue(all(old.format(value) for value in old.library.entries.values()))
        old_findings = old.problems()
        self.assertTrue(any(row.field == 'pattern_key' and 'one role per' in row.reason for row in old_findings))
        self.assertTrue(any(row.field == 'concurrency_frame' for row in old_findings))
        self.assertTrue(any(row.field == 'whole_source_unit_contract' for row in old_findings))
        new = self.seam()
        self.assertEqual(new.problems(), [])
        self.assertEqual(len(new.pending), 2)
        for value in new.library.entries.values():
            self.assertEqual(new.format(value), [])
            self.assertEqual(len(new.obligations(value)), 2)

    def test_both_real_obligation_expressions_and_distinct_names(self):
        seam = self.seam()
        for expected in (79, 80):
            value = seam.library.get(NEW.CONTRACT_IDS[expected])
            rows = seam.obligations(value)
            self.assertEqual([(row.kind, row.text) for row in rows],
                             [('assigns', r'\everything'), ('ensures', r'\result == ' + str(expected))])
            self.assertEqual([row.name for row in rows], [value['id'] + '#frame', value['id'] + '#result'])
            self.assertNotEqual(rows[0].name, rows[1].name)
        self.assertTrue(SCANNER.check_formal_half(r'assigns \everything;', [], SCANNER.LogicLibrary({})))

    def test_each_of_three_repairs_is_individually_necessary(self):
        for defect in ('combined', 'concurrency', 'pattern'):
            values = NEW.unit_contracts(self.proof)
            for value in values.values():
                if defect == 'combined':
                    value['clauses'] = [copy.deepcopy(value['clauses'][1])]
                    value['clauses'][0]['acsl']['text'] = NEW.FRAME + ' ' + value['clauses'][0]['acsl']['text']
                elif defect == 'concurrency':
                    del value['concurrency_frame']
                else:
                    value['pattern_key'][0]['roles'] = ['index', 'target']
            findings = self.seam(values).problems()
            self.assertTrue(findings, defect)
            expected_field = {'combined': 'whole_source_unit_contract', 'concurrency': 'concurrency_frame',
                              'pattern': 'pattern_key'}[defect]
            self.assertTrue(any(row.field == expected_field for row in findings), defect)

    def test_real_concurrency_and_role_refusals(self):
        seam = self.seam(); data = NEW.unit_contracts(self.proof)[80]
        errors = []
        seam.frame['_concurrency'](data, lambda *row: errors.append(row), {})
        seam.frame['_roles'](seam.library, data, lambda *row: errors.append(row))
        self.assertEqual(errors, [])
        for frame in (None, {}, 'none', [None], [{'array': 'a'}],
                      [{'array': 'a', 'shared_actions': [], 'history_reads': 'false'}]):
            errors = []
            seam.frame['_concurrency']({**data, 'concurrency_frame': frame}, lambda *row: errors.append(row), {})
            self.assertTrue(errors, repr(frame))
        for changes in ({'contract_role': 'invalid'}, {'required_enabling_contracts': []},
                        {'contract_role': 'offload_only', 'required_enabling_contracts': []}):
            errors = []
            seam.frame['_roles'](seam.library, {**data, **changes}, lambda *row: errors.append(row))
            self.assertTrue(errors, changes)

    def test_real_entry_refuses_extra_or_changed_properties(self):
        mutations = [lambda x: x['clauses'].append({'id': 'extra', 'role': 'precondition', 'statement': 'extra',
                      'acsl': {'text': 'requires 1;', 'uses': []}, 'proof_placement': {'once': 'self'}}),
                     lambda x: x['clauses'][0]['acsl'].update(text=r'assigns \nothing;'),
                     lambda x: x['clauses'][0]['acsl'].update(text=r'assigns \everything, x;'),
                     lambda x: x['clauses'][1]['acsl'].update(text=r'ensures \unknown;'),
                     lambda x: x['clauses'][1]['acsl'].update(uses=['unknown']),
                     lambda x: x.update(proof_unit={'function': NEW.FUNCTION, 'prototype': 'unsigned f();'})]
        for index, mutate in enumerate(mutations):
            contracts = NEW.unit_contracts(self.proof); mutate(contracts[80])
            seam = self.seam(contracts)
            self.assertTrue(seam.problems())
            if index < 5:
                self.assertTrue(seam.format(contracts[80]))
            # Parsed obligations intentionally omit logic-use/proof-unit metadata;
            # those last two mutations must be refused at the actual _entry gate.
            if index < 4:
                with self.assertRaises((seam.source['Refused'], seam.translator['Untranslatable'])):
                    seam.obligations(contracts[80])

    def test_real_metadata_required_fields_roles_controls_and_placement(self):
        cases = [lambda x: x.pop('strategies'), lambda x: x['clauses'][0].update(role='invalid'),
                 lambda x: x['clauses'][0].pop('proof_placement'),
                 lambda x: x['clauses'][0].update(proof_placement={'once': 'missing@1.0'}),
                 lambda x: x['clauses'][0].update(negative_control={}),
                 lambda x: x['negative_controls'].pop(),
                 lambda x: x.update(version='not-a-version'),
                 lambda x: x.update(proof_unit={'source': self.proof, 'function': 'invalid-name'})]
        for mutate in cases:
            contracts = NEW.unit_contracts(self.proof); mutate(contracts[80])
            self.assertTrue(self.seam(contracts).problems(), mutate)

    def test_real_source_pin_and_contract_hash_refusals(self):
        contracts = NEW.unit_contracts(self.proof); rows = NEW.contract_rows(contracts)
        changed = copy.deepcopy(contracts); changed[80]['clauses'][1]['statement'] += ' changed'
        seam = self.seam(changed, policy_rows=rows)
        self.assertTrue(seam.format(changed[80]))
        self.assertTrue(seam.problems())
        with self.assertRaises(seam.source['Refused']):
            seam.obligations(changed[80])
        (self.root / 'proof_units/source.cpp').write_text('changed')
        seam = self.seam(contracts)
        self.assertTrue(any(row.field == 'proof_unit.source' for row in seam.problems()))

    def test_real_schema_snapshot_covers_generated_shapes(self):
        schema = RetainedSchema()
        for value in NEW.unit_contracts(self.proof).values():
            self.assertEqual(schema.iter_errors(value), [])
        altered = NEW.unit_contracts(self.proof)[80]; altered['concurrency_frame'] = {}
        self.assertTrue(any(row.validator == 'type' and row.path == ('concurrency_frame',)
                            for row in schema.iter_errors(altered)))
        with self.assertRaisesRegex(AssertionError, 'unimplemented'):
            schema.schema['unimplementedConstraint'] = True
            schema.iter_errors(altered)

    def test_pair_hash_order_identity_and_no_derived_model_change(self):
        old, new = OLD.unit_contracts(self.proof), NEW.unit_contracts(self.proof)
        for expected in (79, 80):
            self.assertNotEqual(OLD.digest(old[expected]), NEW.digest(new[expected]))
            self.assertEqual(old[expected]['proof_unit'], new[expected]['proof_unit'])
            self.assertNotIn('semantics', NEW.canonical(new[expected]).decode())
        a, b = (copy.deepcopy(new[value]) for value in (79, 80))
        for value in (a, b):
            del value['id']; del value['clauses']
        self.assertEqual(a, b)
        rows = NEW.contract_rows(new)
        self.assertEqual(rows, [{'id': new[value]['id'], 'sha256': NEW.digest(new[value]), 'expected_result': value}
                                for value in (79, 80)])

    def test_entire_builder_text_inverse_only_formatter_changed(self):
        old = (WHOLE / 'public-profile-builder-v1/profile_builder_v1.py').read_text()
        new = (HERE / 'profile_builder_v2.py').read_text()
        def function(text):
            node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == 'unit_contracts')
            return ast.get_source_segment(text, node)
        before, after = function(old), function(new)
        self.assertNotEqual(before, after)
        self.assertEqual(new.replace(after, before, 1), old)
        inverse = json.loads((HERE / 'unit-contracts-inverse-v2.json').read_bytes())
        self.assertEqual(inverse['edits'], [{'old': before, 'new': after}])
        self.assertEqual((HERE / 'normal-producer-basis-v1.json').read_bytes(),
                         (WHOLE / 'public-profile-builder-v1/normal-producer-basis-v1.json').read_bytes())

    def test_frozen_predecessor_packets_and_memory_draft_unchanged(self):
        for directory, filename in [('public-profile-builder-v1', 'source-packet-v1.json'),
                                    ('public-profile-planner-v2', 'source-packet-v2.json')]:
            packet = json.loads((WHOLE / directory / filename).read_bytes())
            for row in packet['files']:
                path = WHOLE / directory / row.get('relative', row.get('path', ''))
                if not path.exists():
                    path = WHOLE / row.get('relative', row.get('path', ''))
                self.assertEqual(path.stat().st_size, row['bytes'])
                self.assertEqual(NEW.sha(path.read_bytes()), row['sha256'])
        self.assertEqual(NEW.sha((WHOLE / 'runtime-projection-v4/runtime_projection_v4.py').read_bytes()),
                         '56077c3476ba0f4af3b06089e937a0a5723318f7927ba81ea45c8556251cb7de')


if __name__ == '__main__':
    unittest.main(verbosity=2)
