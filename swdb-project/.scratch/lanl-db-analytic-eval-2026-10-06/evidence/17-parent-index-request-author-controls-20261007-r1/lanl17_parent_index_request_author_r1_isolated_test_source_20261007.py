#!/usr/bin/env python3
"""NOT RUN: five narrow synthetic route/Git diagnostic checks, parent review required.

AST-lifts only closed named helpers and CIDS assignment, then the exact route
statement window and refusal print/exit body. Never imports either source module,
executes its main, reads real catalogs/requests/receipts, runs Git/scientific
commands, or imports SWDB/Store/auditor/collector/index writer. All subprocess
calls in selected git helpers are mocked. Fixtures are new private sentinels only.
"""
import ast
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ORIGINAL = Path('/private/tmp/lanl17_author_parent_full_record_index_request_20261007.py')
R1 = Path('/private/tmp/lanl17_author_parent_full_record_index_request_r1_20261007.py')
PINS = {
    ORIGINAL: (38076, '7f2e2d01dc8fc375a2bfb36d3654444bab15d4abfb6a4a7be86532d9971f0e3f'),
    R1: (38266, 'a2e69aef10deb6186ac49401516ffba9a165b2f3cc94c8001646b6ac9a5b701d'),
}
HELPERS = {'Refused', 'require', 'remaining', 'sha', 'checked_path', 'git'}
SENTINEL = 'SYNTHETIC_PRIVATE_GIT_ERROR_VALUE_20261007'


def source_bytes(path):
    raw = path.read_bytes()
    size, expected = PINS[path]
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('isolated_test_exact_source_pin_differs')
    return raw


def lift(path):
    tree = ast.parse(source_bytes(path), filename=str(path))
    chosen = [copy.deepcopy(n) for n in tree.body if
        isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in HELPERS or
        isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'CIDS' for t in n.targets)]
    if len(chosen) != len(HELPERS) + 1:
        raise ValueError('closed_exact_helper_and_original_assign_lift_differs')
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    start = next(i for i, n in enumerate(main.body) if isinstance(n, ast.Assign) and
        len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'records')
    guards, statements = [], [copy.deepcopy(main.body[start])]
    for node in main.body[start + 1:]:
        if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and
                isinstance(node.value.func, ast.Name) and node.value.func.id == 'require' and
                isinstance(node.value.args[-1], ast.Constant) and node.value.args[-1].value in {
                    'exact_canonical_records_directory_string_required',
                    'exact_original28d_one_catalog_routing_required'}):
            break
        guards.append(node.value.args[-1].value)
        statements.append(copy.deepcopy(node))
    expected = ['exact_original28d_one_catalog_routing_required'] if path == ORIGINAL else [
        'exact_canonical_records_directory_string_required', 'exact_original28d_one_catalog_routing_required']
    if guards != expected:
        raise ValueError('closed_exact_route_statement_window_differs')
    route = ast.parse('def route(context, folders, campaign):\n    return records\n').body[0]
    route.body = statements + route.body
    chosen.append(route)
    boundary = next(n for n in tree.body if isinstance(n, ast.If) and
        ast.dump(n.test, include_attributes=False) == ast.dump(ast.parse("__name__ == '__main__'", mode='eval').body, include_attributes=False))
    handler = boundary.body[0].handlers[0]
    if len(handler.body) != 2:
        raise ValueError('closed_exact_refusal_print_exit_body_differs')
    refusal = ast.parse('def hashed_refusal(error):\n    pass\n').body[0]
    refusal.body = copy.deepcopy(handler.body)
    chosen.append(refusal)
    # The full module/main/imports/loader cannot enter this synthetic namespace.
    if any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in chosen):
        raise ValueError('source_module_import_lift_refused')
    namespace = {'__builtins__': __builtins__, 'os': os, 'Path': Path, 'stat': stat,
        'subprocess': subprocess, 'time': time, 'hashlib': hashlib, 'json': json, 'sys': sys}
    selected = ast.fix_missing_locations(ast.Module(body=chosen, type_ignores=[]))
    exec(compile(selected, '<closed-synthetic-helper-lift>', 'exec'), namespace)
    return namespace


class SyntheticRouteAndPrivacy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = {p: source_bytes(p) for p in PINS}
        cls.original, cls.r1 = lift(ORIGINAL), lift(R1)

    @classmethod
    def tearDownClass(cls):
        for p, raw in cls.before.items():
            if source_bytes(p) != raw:
                raise AssertionError('original_or_R1_source_changed_in_synthetic_checks')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lanl17-index-request-r1-synthetic-', dir='/private/tmp')
        self.root = Path(self.temp.name)
        self.folders = tuple(self.root / 'campaigns' / cid for cid in self.r1['CIDS'])
        for folder in self.folders:
            (folder / 'records').mkdir(parents=True)
        self.campaign = self.r1['CIDS'][0]
        self.records = self.folders[0] / 'records'
        self.canonical = {'records_directory': str(self.records)}
        self.noncanonical = {'records_directory': str(self.records.parent) + '//records'}
        self.assertNotEqual(self.noncanonical['records_directory'], str(self.records))

    def tearDown(self):
        self.temp.cleanup()  # Only this test's new synthetic empty directories.

    def test_original_route_accepts_writer_incompatible_spelling(self):
        # Historical RED premise: both observations/context could preserve this
        # raw spelling;7a independently requires observed == str(resolved records).
        result = self.original['route'](self.noncanonical, self.folders, self.campaign)
        self.assertEqual(result, self.records)
        self.assertNotEqual(self.noncanonical['records_directory'], str(result))

    def test_R1_refuses_noncanonical_and_preserves_exact_route(self):
        with self.assertRaisesRegex(self.r1['Refused'], 'exact_canonical_records_directory_string_required'):
            self.r1['route'](self.noncanonical, self.folders, self.campaign)
        self.assertEqual(self.r1['route'](self.canonical, self.folders, self.campaign), self.records)

    def failing_git(self, *args, **kwargs):
        # No subprocess is launched. Simulate check_output's inherited channel
        # versus PIPE from the actual lifted helper's exact keyword arguments.
        if kwargs.get('stderr') != subprocess.PIPE:
            print(SENTINEL, file=sys.stderr)
        raise subprocess.CalledProcessError(128, args[0], stderr=SENTINEL.encode())

    def test_original_git_failure_exposes_synthetic_stderr(self):
        output = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), patch('subprocess.check_output', side_effect=self.failing_git), contextlib.redirect_stderr(output):
            with self.assertRaises(subprocess.CalledProcessError):
                self.original['git'](self.root, time.monotonic() + 60, 'rev-parse', 'HEAD')
        self.assertIn(SENTINEL, output.getvalue())

    def test_R1_git_failure_is_captured_and_refusal_only_hashed(self):
        output = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), patch('subprocess.check_output', side_effect=self.failing_git) as child, contextlib.redirect_stderr(output):
            try:
                self.r1['git'](self.root, time.monotonic() + 60, 'rev-parse', 'HEAD')
            except subprocess.CalledProcessError as error:
                self.assertEqual(error.stderr, SENTINEL.encode())
                with self.assertRaises(SystemExit) as refused:
                    self.r1['hashed_refusal'](error)
                self.assertEqual(refused.exception.code, 3)
            else:
                self.fail('synthetic Git failure must raise')
        self.assertEqual(child.call_args.kwargs['stderr'], subprocess.PIPE)
        encoded = output.getvalue()
        self.assertNotIn(SENTINEL, encoded)
        refusal = json.loads(encoded)
        self.assertEqual(refusal['exception_class'], 'CalledProcessError')
        self.assertEqual(len(refusal['exception_message_sha256']), 64)
        self.assertFalse(refusal['original_parser_or_command_or_environment_text_transferred'])

    def test_successful_read_only_git_bytes_and_fixed_argv_are_preserved(self):
        expected = b'SYNTHETIC_PUBLIC_COMMIT_BYTES\n'
        calls = []
        for source in (self.original, self.r1):
            with patch.dict(os.environ, {}, clear=True), patch('subprocess.check_output', return_value=expected) as child:
                self.assertEqual(source['git'](self.root, time.monotonic() + 60, 'rev-parse', 'HEAD'), expected)
            calls.append(child.call_args)
        self.assertEqual(calls[0].args, calls[1].args)
        self.assertNotIn('stderr', calls[0].kwargs)
        self.assertEqual(calls[1].kwargs['stderr'], subprocess.PIPE)
        self.assertEqual(calls[0].kwargs['env'], calls[1].kwargs['env'])
        self.assertIn('protocol.allow=never', calls[1].args[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
