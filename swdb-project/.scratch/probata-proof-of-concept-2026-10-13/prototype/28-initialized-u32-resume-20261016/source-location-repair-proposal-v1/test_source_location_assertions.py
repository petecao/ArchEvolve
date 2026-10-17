"""2026-10-16 ET. Compiler-free source-location assertion seam regressions.

Execute AST-extracted real checker functions only. No project module import,
compiler, native program, verifier, SSH, or child process is permitted here.
Synthetic diagnostic reconstruction does not reproduce the retained full AST.
"""
import ast
import copy
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = {'_children', '_walk', '_slice', '_clean', '_strip_expr', '_expression',
         '_callee', '_string', '_assert_function_diagnostic', '_assertion'}
EVENTS = []


def audit(event, args):
    if (event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn',
                          'os.fork', 'pty.spawn', 'ctypes.dlopen'))
            or event in {'os.system', 'os.startfile'}):
        EVENTS.append(event)
        raise RuntimeError('child/native execution forbidden: ' + event)


sys.addaudithook(audit)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_checker(path, candidate=False):
    tree = ast.parse(path.read_text(), filename=str(path))
    wanted = NAMES | ({'_assert_source_location_diagnostics'} if candidate else set())
    nodes = [node for node in tree.body
             if (isinstance(node, ast.FunctionDef) and node.name in wanted)
             or (isinstance(node, ast.ClassDef) and node.name == 'Refused')]
    assert {node.name for node in nodes} == wanted | {'Refused'}
    module = ast.Module(body=nodes, type_ignores=[])
    assert not any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(module))
    namespace = {'json': json, 're': re, 'Path': Path, '__name__': 'inert_assertion_slice'}
    exec(compile(module, str(path), 'exec'), namespace)
    return namespace, tree


def walk(node):
    yield node
    for child in node.get('inner', []):
        yield from walk(child)


def abort(row):
    result = [node for node in walk(row['ast']) if node.get('kind') == 'CallExpr']
    assert len(result) == 1
    return result[0]


def literal_path(row):
    result = copy.deepcopy(row)
    call = abort(result)
    file = '/synthetic/original/MAA_gem5.hpp'
    call['inner'][2] = {
        'kind': 'ImplicitCastExpr', 'castKind': 'ArrayToPointerDecay',
        'type': {'qualType': 'const char *'}, 'valueCategory': 'prvalue',
        'inner': [{'kind': 'StringLiteral', 'value': json.dumps(file),
                   'type': {'qualType': 'const char[' + str(len(file) + 1) + ']'},
                   'valueCategory': 'lvalue'}]}
    call['inner'][3] = {
        'kind': 'ImplicitCastExpr', 'castKind': 'IntegralCast',
        'type': {'qualType': 'unsigned int'}, 'valueCategory': 'prvalue',
        'inner': [{'kind': 'IntegerLiteral', 'value': '121' if row['expected'] == 'width' else '125',
                   'type': {'qualType': 'int'}, 'valueCategory': 'prvalue'}]}
    return result


class SourceLocationRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata = json.loads((HERE / 'proposal-base.json').read_text())
        assert sha(HERE / 'base-source.py') == cls.metadata['base_sha256'] == 'c023a4a6298fab7a34f4213f888b6c0fb4fe5c405e5a53741942e3e2accb81cb'
        assert sha(HERE / 'proposed-source.py') == cls.metadata['proposal_sha256']
        cls.old, cls.old_tree = load_checker(HERE / 'base-source.py')
        cls.new, cls.new_tree = load_checker(HERE / 'proposed-source.py', True)
        cls.fixture = json.loads((HERE / 'synthetic-source-location-fixture.json').read_text())
        cls.rows = cls.fixture['cases']
        assert [(row['expected'], row['variable']) for row in cls.rows] == [('width', 'num_regs_needed'), ('bound', 'REG_count')]

    def refuse(self, row, tokens=True):
        with self.assertRaises(self.new['Refused']):
            self.new['_assertion'](row['ast'], row['expected'], row['variable'], row['tokens'] if tokens else None)

    def test_old_red_new_green_exact_real_function_seam(self):
        for row in self.rows:
            with self.subTest(expected=row['expected']):
                with self.assertRaisesRegex(self.old['Refused'], 'unchecked AST effect'):
                    self.old['_assertion'](row['ast'], row['expected'], row['variable'])
                self.assertIsNone(self.new['_assertion'](row['ast'], row['expected'], row['variable'], row['tokens']))
                qualified = self.new['_assert_source_location_diagnostics'](abort(row), row['tokens'], row['expected'])
                self.assertEqual(len(qualified), 2)
                self.assertIs(qualified[0], abort(row)['inner'][2])
                self.assertIs(qualified[1], abort(row)['inner'][3])

    def test_fixture_is_reproducible_and_explicitly_synthetic(self):
        namespace = {'__name__': 'inert_fixture_builder', '__file__': str(HERE / 'build_source_location_fixture.py')}
        exec(compile((HERE / 'build_source_location_fixture.py').read_text(), str(HERE / 'build_source_location_fixture.py'), 'exec'), namespace)
        self.assertEqual(namespace['build'](), self.fixture)
        self.assertIn('SYNTHETIC', self.fixture['scope'])
        self.assertIn('not the retained initialized AST', self.fixture['scope'])
        self.assertEqual(self.fixture['capture']['sha256'], '00ad79efcccbef558a41b163e09ffa6969488ff0d1a9853bbb72d0bca5dae6fa')
        retained = json.loads((HERE / 'retained-diagnostic-metadata.json').read_text())
        self.assertEqual(retained['retained_width_assertion_sha256'], '160c6b76a6a241cd730ceaa5c25b93ec27fbfe7ef7403df38cc106b122ad4a09')
        shape = retained['observed_source_location_shape']
        for row in self.rows:
            call = abort(row)
            self.assertEqual(self.new['_callee'](call), shape['callee'])
            for role in ('file', 'line'):
                leaf = call['inner'][shape[role + '_child_index']]
                self.assertEqual(leaf['type']['qualType'], shape[role + '_type'])
                self.assertEqual(leaf['valueCategory'], shape['value_category'])
                self.assertEqual('inner' in leaf, shape['inner_present'])
                self.assertEqual(self.new['_slice'](leaf, row['tokens'])[2], shape[role + '_tokens'])
            marker = '# ' + str(shape[row['expected'] + '_line']) + ' '
            self.assertTrue(row['tokens'].startswith(marker))
            self.assertIn('/' + shape['original_file_basename'] + '"', row['tokens'])

    def test_literal_path_success_and_failures_unchanged(self):
        for source in self.rows:
            row = literal_path(source)
            for checker in (self.old, self.new):
                self.assertIsNone(checker['_assertion'](row['ast'], row['expected'], row['variable']))
            # The candidate still ignores tokens on the literal-only legacy path.
            self.assertIsNone(self.new['_assertion'](row['ast'], row['expected'], row['variable'], 'invalid source'))
            for label in ('file', 'line', 'message', 'function'):
                changed = copy.deepcopy(row); call = abort(changed)
                if label == 'file':
                    item = call['inner'][2]['inner'][0]; item['value'] = json.dumps('/synthetic/wrong.hpp')
                    item['type'] = {'qualType': 'const char[21]'}
                elif label == 'line': call['inner'][3]['inner'][0]['value'] = '124'
                elif label == 'message': call['inner'][1]['inner'][0]['value'] = '"changed"'
                else: call['inner'][4]['inner'][0]['inner'][0]['inner'][0]['value'] = '"other"'
                outcomes = []
                for checker in (self.old, self.new):
                    with self.assertRaises(checker['Refused']) as caught:
                        checker['_assertion'](changed['ast'], changed['expected'], changed['variable'])
                    outcomes.append(str(caught.exception))
                self.assertEqual(*outcomes, msg=label)

    def test_closed_leaf_shape_and_types(self):
        for source in self.rows:
            for label in ('value', 'empty_inner', 'effectful_inner', 'missing_id', 'bad_id',
                          'extra_type', 'file_type', 'line_type', 'category', 'range_key'):
                with self.subTest(expected=source['expected'], mutation=label):
                    row = copy.deepcopy(source); call = abort(row); file, line = call['inner'][2:4]
                    if label == 'value': file['value'] = '42'
                    elif label == 'empty_inner': file['inner'] = []
                    elif label == 'effectful_inner': file['inner'] = [{'kind': 'UnaryOperator', 'opcode': '++', 'inner': []}]
                    elif label == 'missing_id': del file['id']
                    elif label == 'bad_id': file['id'] = 'not-a-Clang-id'
                    elif label == 'extra_type': file['type']['desugaredQualType'] = 'const char *'
                    elif label == 'file_type': file['type']['qualType'] = 'char *'
                    elif label == 'line_type': line['type']['qualType'] = 'int'
                    elif label == 'category': file['valueCategory'] = 'lvalue'
                    else: file['range']['unexpected'] = True
                    self.refuse(row)

    def test_pair_position_wrapping_and_lexical_order(self):
        for source in self.rows:
            for label in ('swapped_args', 'file_cast', 'line_cast', 'one_literal', 'both_hidden', 'overlap', 'reordered_ranges', 'outside_call'):
                with self.subTest(expected=source['expected'], mutation=label):
                    row = copy.deepcopy(source); call = abort(row); file, line = call['inner'][2:4]
                    if label == 'swapped_args': call['inner'][2:4] = [line, file]
                    elif label in {'file_cast', 'line_cast'}:
                        position = 2 if label == 'file_cast' else 3
                        call['inner'][position] = {'kind': 'ImplicitCastExpr', 'castKind': 'NoOp', 'type': dict(call['inner'][position]['type']), 'inner': [call['inner'][position]]}
                    elif label == 'one_literal': call['inner'][2] = abort(literal_path(source))['inner'][2]
                    elif label == 'both_hidden':
                        for position in (2, 3):
                            call['inner'][position] = {'kind': 'ParenExpr', 'inner': [call['inner'][position]]}
                    elif label in {'overlap', 'reordered_ranges'}:
                        old_file_range, old_line_range = copy.deepcopy(file['range']), copy.deepcopy(line['range'])
                        # Swap the actual spelling AND bind each node to its own
                        # exact builtin, preserving all checks except order.
                        start = old_file_range['begin']['offset']; stop = old_line_range['end']['offset'] + 1
                        text = '__builtin_LINE (), __builtin_FILE ()'
                        self.assertEqual(len(text), stop - start)
                        row['tokens'] = row['tokens'][:start] + text + row['tokens'][stop:]
                        file['range'], line['range'] = old_line_range, old_file_range
                        if label == 'overlap': line['range'] = copy.deepcopy(file['range'])
                    else: call['range']['begin']['offset'] = file['range']['end']['offset'] + 1
                    self.refuse(row)

    def test_source_ranges_must_be_direct_and_available(self):
        for source in self.rows:
            for label in ('spelling', 'expansion', 'negative', 'bool', 'zero_toklen', 'out_of_bounds', 'missing_range', 'call_indirect'):
                with self.subTest(expected=source['expected'], mutation=label):
                    row = copy.deepcopy(source); call = abort(row); item = call['inner'][2]
                    point = item['range']['begin']
                    if label == 'spelling': point['spellingLoc'] = dict(point)
                    elif label == 'expansion': point['expansionLoc'] = dict(point)
                    elif label == 'negative': point['offset'] = -1
                    elif label == 'bool': point['offset'] = True
                    elif label == 'zero_toklen': point['tokLen'] = 0
                    elif label == 'out_of_bounds': item['range']['end']['offset'] = len(row['tokens']) + 1
                    elif label == 'missing_range': del item['range']
                    else: call['range']['begin']['expansionLoc'] = dict(call['range']['begin'])
                    self.refuse(row)

    def test_source_marker_and_builtin_text_binding(self):
        for source in self.rows:
            for label in ('wrong_file', 'wrong_line', 'no_marker', 'wrong_flag', 'file_builtin', 'line_builtin', 'effectful_builtin', 'missing_tokens'):
                with self.subTest(expected=source['expected'], mutation=label):
                    row = copy.deepcopy(source)
                    if label == 'wrong_file': row['tokens'] = row['tokens'].replace('MAA_gem5.hpp', 'MAA_evil.hpp')
                    elif label == 'wrong_line': row['tokens'] = row['tokens'].replace('# 121 ', '# 122 ').replace('# 125 ', '# 126 ')
                    elif label == 'no_marker': row['tokens'] = row['tokens'].replace('# ', '//', 1)
                    elif label == 'wrong_flag': row['tokens'] = row['tokens'].replace('" 1\n', '" 5\n', 1)
                    elif label == 'file_builtin': row['tokens'] = row['tokens'].replace('__builtin_FILE', '__builtin_FUNC')
                    elif label == 'line_builtin': row['tokens'] = row['tokens'].replace('__builtin_LINE', '__builtin_FILE')
                    elif label == 'effectful_builtin': row['tokens'] = row['tokens'].replace('__builtin_FILE ()', '__builtin_FILE(x)')
                    self.refuse(row, tokens=label != 'missing_tokens')

    def test_value_bearing_source_location_never_globally_allowed(self):
        for source in self.rows:
            for location in ('predicate', 'success', 'message', 'function'):
                with self.subTest(expected=source['expected'], location=location):
                    row = copy.deepcopy(source); call = abort(row); replacement = copy.deepcopy(call['inner'][3])
                    conditional = next(node for node in walk(row['ast']) if node.get('kind') == 'ConditionalOperator')
                    if location == 'predicate': conditional['inner'][0] = replacement
                    elif location == 'success': conditional['inner'][1] = replacement
                    elif location == 'message': call['inner'][1] = replacement
                    else: call['inner'][4] = replacement
                    self.refuse(row)

    def test_predicate_effects_signature_and_diagnostic_still_closed(self):
        for source in self.rows:
            for label in ('unary_effect', 'new_call', 'wrong_predicate', 'abort_signature', 'function_diagnostic', 'abort_arity', 'unbound_variable'):
                with self.subTest(expected=source['expected'], mutation=label):
                    row = copy.deepcopy(source); call = abort(row)
                    if label == 'unary_effect': call['inner'][4]['inner'][0]['opcode'] = '++'
                    elif label == 'new_call': call['inner'][1]['inner'].append({'kind': 'CallExpr', 'inner': []})
                    elif label == 'wrong_predicate': next(node for node in walk(row['ast']) if node.get('kind') == 'BinaryOperator')['opcode'] = '+'
                    elif label == 'abort_signature': call['inner'][0]['inner'][0]['referencedDecl']['type']['qualType'] = 'void ()'
                    elif label == 'function_diagnostic': call['inner'][4]['inner'][0]['inner'][0]['inner'][0]['value'] = '"wrong function"'
                    elif label == 'abort_arity': call['inner'].append(copy.deepcopy(call['inner'][3]))
                    else: next(node for node in walk(row['ast']) if node.get('kind') == 'DeclRefExpr' and node.get('referencedDecl', {}).get('kind') == 'VarDecl')['referencedDecl']['name'] = 'foreign'
                    self.refuse(row)

    def test_only_assertion_seam_and_token_forwarding_change(self):
        old = {node.name: node for node in self.old_tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        new = {node.name: node for node in self.new_tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        self.assertEqual(set(new) - set(old), {'_assert_source_location_diagnostics'})
        changed = {name for name in old if ast.dump(old[name]) != ast.dump(new[name])}
        self.assertEqual(changed, {'_assertion', '_bodies'})
        original = copy.deepcopy(old['_bodies']); revised = copy.deepcopy(new['_bodies'])
        calls = [node for node in ast.walk(revised) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '_assertion']
        self.assertEqual(len(calls), 1); self.assertEqual(len(calls[0].args), 4)
        self.assertEqual(ast.dump(calls[0].args.pop()), ast.dump(ast.Name(id='tokens', ctx=ast.Load())))
        self.assertEqual(ast.dump(original), ast.dump(revised))
        def outside_functions(tree):
            return ast.dump(ast.Module(body=[node for node in tree.body if not isinstance(node, (ast.FunctionDef, ast.ClassDef))], type_ignores=[]))
        self.assertEqual(outside_functions(self.old_tree), outside_functions(self.new_tree))

    def test_no_child_or_native_execution(self):
        self.assertEqual(EVENTS, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
