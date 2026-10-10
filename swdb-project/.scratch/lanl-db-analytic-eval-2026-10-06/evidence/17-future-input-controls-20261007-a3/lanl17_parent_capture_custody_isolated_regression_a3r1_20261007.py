#!/usr/bin/env python3
"""SOURCE-ONLY prepared 12-case custody regression; NOT RUN.

After separate parent review, reads only the exact producer SOURCE, AST-lifts
listed custody helpers and guard expressions, and uses owned temporary synthetic
files. Never imports/runs the producer module/main, SWDB, Store, auditor,
collector, control, native/provider, Git or SSH. No original study data read.
"""
import ast
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
import yaml

PRODUCER = Path('/private/tmp/lanl17_parent_capture_projection_producer_a3_20261007.py')
PRODUCER_SHA256 = '32bead204337aa66d0a732b6f143216946abafc5d2eb752577b0d90f7190b7b6'
LIFTED_NAMES = ('Refused', 'require', 'need', 'sha', 'hex64', 'regular',
                'hash_file', 'returned_bytes', 'manifest_output_roots')
GUARD_MESSAGES = {
    'output': 'Output cannot enter original source/M2 raw/four campaign roots or overwrite originals',
    'publication': 'Own producer source changed before publication',
    'success': 'Own producer source changed before success',
}


def source_lift():
    raw = PRODUCER.read_bytes()
    if len(raw) != 46165 or hashlib.sha256(raw).hexdigest() != PRODUCER_SHA256:
        raise RuntimeError('isolated regression producer source pin mismatch')
    tree = ast.parse(raw)
    named = {node.name: node for node in tree.body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    constant_nodes = {}
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id in ('HELPER', 'F6', 'MAX_BYTES')):
            # Lift only these three reviewed source assignments verbatim.
            # MAX_BYTES is the reviewed integer multiplication, not a literal
            # accepted by ast.literal_eval; no general expression evaluator.
            constant_nodes[node.targets[0].id] = copy.deepcopy(node)
    namespace = {'Path': Path, 'os': os, 'stat': stat, 'hashlib': hashlib,
                 're': re, 'json': json, 'sys': sys, 'yaml': yaml}
    if set(constant_nodes) != {'HELPER', 'F6', 'MAX_BYTES'}:
        raise RuntimeError('isolated regression reviewed constant inventory differs')
    selected = list(constant_nodes.values()) + [copy.deepcopy(named[name]) for name in LIFTED_NAMES]
    main_ast = named['main']
    for role, message in GUARD_MESSAGES.items():
        matches = [node for node in main_ast.body
                   if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                   and isinstance(node.value.func, ast.Name)
                   and node.value.func.id == 'require'
                   and len(node.value.args) == 2
                   and isinstance(node.value.args[1], ast.Constant)
                   and node.value.args[1].value == message]
        if len(matches) != 1:
            raise RuntimeError('isolated regression exact source guard missing')
        arguments = ('output, forbidden_output_roots, inputs'
                     if role == 'output' else 'spec')
        wrapper = ast.parse('def guard_' + role + '(' + arguments + '):\n pass').body[0]
        wrapper.body = [copy.deepcopy(matches[0])]
        selected.append(wrapper)
    original_if = next(node for node in tree.body if isinstance(node, ast.If)
                       and ast.unparse(node.test) == "__name__ == '__main__'")
    handler = original_if.body[0].handlers[0]
    wrapper = ast.parse('def safe_diagnostic(error):\n try:\n  raise error\n except ValueError as exc:\n  pass').body[0]
    # The original except type/body is lifted verbatim. The source main and
    # original try body are excluded; only a synthetic supplied error is raised.
    wrapper.body[0].handlers = [copy.deepcopy(handler)]
    selected.append(wrapper)
    module = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    exec(compile(module, '<exact-custody-AST-lift>', 'exec'), namespace)
    return namespace


def mapped_path_type(sandbox):
    """Logical /data prefix maps exclusively onto this synthetic temp tree.

    No actual /data, campaign or source directory is opened/stat'ed. Only the
    original helper's Path dependency is supplied by this transparent fixture;
    the lifted helper/guard AST is unchanged.
    """
    logical_prefix = PurePosixPath('/data/yanruj/isolated-custody-fixture')

    class MappedPath:
        def __init__(self, value):
            self.logical = value.logical if isinstance(value, MappedPath) else PurePosixPath(str(value))

        def physical(self):
            if self.logical.is_relative_to(logical_prefix):
                return sandbox / self.logical.relative_to(logical_prefix)
            # Ancestors of the logical prefix have synthetic nonsymlink status.
            if logical_prefix.is_relative_to(self.logical):
                return sandbox
            raise AssertionError('fixture attempted outside its logical sandbox')

        def __str__(self): return str(self.logical)
        def __truediv__(self, value): return MappedPath(self.logical / value)
        @property
        def parts(self): return self.logical.parts
        @property
        def parents(self): return tuple(MappedPath(p) for p in self.logical.parents)
        def is_absolute(self): return self.logical.is_absolute()
        def is_symlink(self): return self.physical().is_symlink()
        def is_dir(self): return self.physical().is_dir()
        def exists(self): return self.physical().exists()
        def stat(self): return self.physical().stat()
        def is_relative_to(self, other):
            return self.logical.is_relative_to(other.logical if isinstance(other, MappedPath)
                                               else PurePosixPath(str(other)))
        def __eq__(self, other):
            return self.logical == (other.logical if isinstance(other, MappedPath)
                                    else PurePosixPath(str(other)))
    return MappedPath


class CustodyOnlyRegression(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lanl17-custody-synthetic-',
                                                dir=str(Path(tempfile.gettempdir()).resolve(strict=True)))
        self.addCleanup(self.temp.cleanup)
        self.sandbox = Path(self.temp.name)
        self.ns = source_lift()
        self.Refused = self.ns['Refused']
        self.raw_bytes = b'synthetic exact original\n'
        self.file = self.sandbox / 'original.txt'
        self.file.write_bytes(self.raw_bytes)
        self.expected = hashlib.sha256(self.raw_bytes).hexdigest()

    def manifest_fixture(self):
        for name in ('raw', 'source', 'captures'):
            (self.sandbox / name).mkdir(exist_ok=True)
        MappedPath = mapped_path_type(self.sandbox)
        self.ns['Path'] = MappedPath
        source = '/data/yanruj/isolated-custody-fixture/source'
        ctx = {'source_commit': 'f' * 40, 'manifest_identity_sha256': '1' * 64,
               'source_path': source,
               'policy': {'id': 'synthetic.policy', 'identity_sha256': '2' * 64,
                          'frozen_at': '2026-10-07T00:00:00+00:00'}}
        m2 = {'format': 'swdb.lanl17-parent-population.v1',
              'identity_sha256': ctx['manifest_identity_sha256'],
              'source_commit': ctx['source_commit'], 'source': source,
              'helper_sha256': self.ns['HELPER'], 'estimator_sha256': self.ns['F6'],
              'source_clean': True, 'policy': copy.deepcopy(ctx['policy']),
              'raw': '/data/yanruj/isolated-custody-fixture/raw'}
        ns = self.ns

        class CompactFixture:
            # The preexisting seal loader is deliberately not tested/replayed.
            # This fixture supplies its validated-output interface only.
            def __init__(self):
                self.values = {'manifest_M2': m2}
                self.pins = {'manifest_M2': {'path': '/data/yanruj/isolated-custody-fixture/custody/original-manifest.json',
                                           'writer_source': {'sha256': ns['HELPER']},
                                           'canonical_ensure_ascii': True}}

            def compact(self, name, expected_format):
                ns['require'](name in self.values, 'synthetic exact M2 missing')
                value = self.values[name]
                ns['require'](value['format'] == expected_format, 'synthetic M2 format differs')
                return value
        return CompactFixture(), ctx, MappedPath

    def test_01_exact_returned_read(self):
        self.assertEqual(self.ns['returned_bytes'](self.file, len(self.raw_bytes), self.expected),
                         self.raw_bytes)

    def test_02_same_size_different_returned_hash_refuses(self):
        self.file.write_bytes(b'X' * len(self.raw_bytes))
        with self.assertRaisesRegex(self.Refused, 'returned original bytes differ'):
            self.ns['returned_bytes'](self.file, len(self.raw_bytes), self.expected)

    def test_03_inode_replacement_with_identical_bytes_refuses(self):
        replacement = self.sandbox / 'replacement.txt'
        replacement.write_bytes(self.raw_bytes)
        self.assertNotEqual(self.file.stat().st_ino, replacement.stat().st_ino)
        calls = 0

        def replacing_fstat(fd):
            nonlocal calls
            result = os.fstat(fd)
            calls += 1
            if calls == 2:
                os.replace(replacement, self.file)
            return result
        self.ns['os'] = SimpleNamespace(getuid=os.getuid, fstat=replacing_fstat)
        with self.assertRaisesRegex(self.Refused, 'changed/replaced while returning bytes'):
            self.ns['returned_bytes'](self.file, len(self.raw_bytes), self.expected)
        self.assertEqual(calls, 2)
        self.assertEqual(self.file.read_bytes(), self.raw_bytes)

    def test_04_exact_M2_roots_exclude_source_raw_and_four_campaigns(self):
        inputs, ctx, MappedPath = self.manifest_fixture()
        roots = self.ns['manifest_output_roots'](inputs, ctx)
        expected = [ctx['source_path'], inputs.values['manifest_M2']['raw']]
        expected += [expected[1] + '/campaign-runs/extensa/extensa-gem5-bfs-20261006-p' + str(i)
                     for i in range(1, 5)]
        self.assertEqual([str(root) for root in roots], expected)
        for root in roots:
            with self.subTest(root=str(root)), self.assertRaises(self.Refused):
                self.ns['guard_output'](root / 'capture.json', roots, inputs)

    def test_05_output_outside_exact_roots_is_admitted(self):
        inputs, ctx, MappedPath = self.manifest_fixture()
        roots = self.ns['manifest_output_roots'](inputs, ctx)
        self.ns['guard_output'](MappedPath('/data/yanruj/isolated-custody-fixture/captures/new.json'),
                                roots, inputs)

    def test_06_missing_M2_refuses(self):
        inputs, ctx, _ = self.manifest_fixture()
        inputs.values.clear()
        with self.assertRaises(self.Refused): self.ns['manifest_output_roots'](inputs, ctx)

    def test_07_wrong_M2_helper_writer_or_body_refuses(self):
        for field in ('writer', 'body'):
            inputs, ctx, _ = self.manifest_fixture()
            if field == 'writer': inputs.pins['manifest_M2']['writer_source']['sha256'] = '0' * 64
            else: inputs.values['manifest_M2']['helper_sha256'] = '0' * 64
            with self.subTest(field=field), self.assertRaises(self.Refused):
                self.ns['manifest_output_roots'](inputs, ctx)

    def test_08_wrong_M2_source_refuses(self):
        inputs, ctx, _ = self.manifest_fixture()
        inputs.values['manifest_M2']['source_commit'] = 'e' * 40
        with self.assertRaises(self.Refused): self.ns['manifest_output_roots'](inputs, ctx)

    def test_09_wrong_M2_policy_refuses(self):
        inputs, ctx, _ = self.manifest_fixture()
        inputs.values['manifest_M2']['policy']['identity_sha256'] = '3' * 64
        with self.assertRaises(self.Refused): self.ns['manifest_output_roots'](inputs, ctx)

    def test_10_own_source_mutation_refuses_both_publication_and_success(self):
        self.ns['__file__'] = str(self.file)
        spec = {'producer_sha256': self.expected}
        for role in ('publication', 'success'):
            self.ns['guard_' + role](spec)
        self.file.write_bytes(b'changed synthetic source\n')
        for role in ('publication', 'success'):
            with self.subTest(role=role), self.assertRaises(self.Refused):
                self.ns['guard_' + role](spec)

    def check_diagnostic(self, error, forbidden):
        output = io.StringIO()
        with contextlib.redirect_stderr(output), self.assertRaises(SystemExit) as stopped:
            self.ns['safe_diagnostic'](error)
        self.assertEqual(stopped.exception.code, 2)
        raw = output.getvalue()
        self.assertLess(len(raw), 512)
        self.assertEqual(raw.count('\n'), 1)
        self.assertNotIn(forbidden, raw)
        document = json.loads(raw)
        self.assertEqual(set(document), {'format', 'state', 'exception_class',
                                        'exception_message_sha256', 'raw_exception_or_parser_context_transferred'})
        self.assertEqual(document['state'], 'refused')
        self.assertEqual(document['exception_class'], type(error).__name__)
        self.assertEqual(document['exception_message_sha256'],
                         hashlib.sha256(str(error).encode('utf-8', errors='replace')).hexdigest())
        self.assertIs(document['raw_exception_or_parser_context_transferred'], False)

    def test_11_yaml_parser_context_is_only_hashed(self):
        secret = 'synthetic_private_parser_context'
        try: yaml.safe_load('key: [' + secret + '\n')
        except yaml.YAMLError as error:
            self.assertIn(secret, str(error))
            self.check_diagnostic(error, secret)
        else: self.fail('synthetic malformed YAML unexpectedly parsed')

    def test_12_existing_failure_message_is_only_hashed(self):
        secret = 'synthetic_private_failure_value'
        self.check_diagnostic(ValueError(secret), secret)


if __name__ == '__main__':
    unittest.main(verbosity=2)
