#!/usr/bin/env python3
"""NOT RUN: focused synthetic AST-lift regression SOURCE for a parent review.

No whole writer/main imports, actual requests/records, Store/validate/SWDB,
scientific calls, SSH, provider, auditor or collector execution. A future
separate authorization is required to execute this one small regression batch.
Only explicitly named original assignment/class/function/loader nodes are
lifted after verifying the exact writer bytes. Multiplication constants remain
original Assign ASTs; no ast.literal_eval or general expression evaluator.
"""
import ast
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import time
import unittest
from unittest import mock

import yaml

WRITER = Path('/private/tmp/lanl17_write_parent_full_record_index_20261007.py')
WRITER_SHA = '7a67d46f8ad7d453fe07bd458a21f663bd4dc7ec12e71de83ad8b5caaf28894b'
CONSTANTS = {'MAX_CATALOG_FILE', 'MAX_CATALOG_TOTAL', 'MAX_METADATA', 'MAX_RECORDS', 'STAMP_KEYS'}
SYMBOLS = {'Refused', 'require', 'sha', 'digest', 'exact', 'full_hash', 'token', 'RecordLoader',
           'no_duplicates', 'plain_record', 'index_record', 'remaining', 'checked_path', 'stamp',
           'returned_bytes', 'record_relative', 'scan_catalog', 'approved_inventory',
           'require_inventory_equal', 'build_index', 'recheck_catalog', 'recheck_originals', 'publish'}


def isolated_symbols():
    raw = WRITER.read_bytes()
    if hashlib.sha256(raw).hexdigest() != WRITER_SHA:
        raise AssertionError('Exact prospective writer source pin differs; do not run a substituted source')
    parsed = ast.parse(raw)
    selected, seen, loader_nodes = [], set(), 0
    for node in parsed.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in SYMBOLS:
            selected.append(node)
            seen.add(node.name)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in CONSTANTS:
                selected.append(node)
                seen.add(target.id)
            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and \
                    target.value.id == 'RecordLoader' and target.attr == 'yaml_implicit_resolvers':
                selected.append(node)
                loader_nodes += 1
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and \
                isinstance(node.value.func, ast.Attribute) and isinstance(node.value.func.value, ast.Name) and \
                node.value.func.value.id == 'RecordLoader' and node.value.func.attr == 'add_constructor':
            selected.append(node)
            loader_nodes += 1
    if seen != CONSTANTS | SYMBOLS or loader_nodes != 2:
        raise AssertionError('Closed original AST projection differs')
    namespace = {'hashlib': hashlib, 'json': json, 'math': math, 'os': os, 'Path': Path,
                 'PurePosixPath': PurePosixPath, 're': re,
                 'stat': stat, 'time': time, 'yaml': yaml}
    module = ast.Module(body=selected, type_ignores=[])
    exec(compile(module, str(WRITER) + ':isolated-original-nodes', 'exec'), namespace)
    return namespace


class ParentIndexSyntheticCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lifted = isolated_symbols()

    def setUp(self):
        # All changed bytes/inodes below are synthetic sentinels in a new folder.
        self.temp = tempfile.TemporaryDirectory(prefix='lanl17-index-synthetic-', dir='/private/tmp')
        self.folder = Path(self.temp.name)
        self.deadline = time.monotonic() + 30
        self.addCleanup(self.temp.cleanup)

    def fn(self, name):
        return self.lifted[name]

    def pin(self, path):
        raw = path.read_bytes()
        return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

    def inventory(self, records):
        rows = []
        for path in sorted(records.rglob('*.yaml')):
            rows.append({'path': path.relative_to(records).as_posix(), 'bytes': path.stat().st_size,
                         'sha256': self.pin(path)['sha256'], 'stat': self.fn('stamp')(path.stat())})
        limits = {'catalog_record_count': len(rows), 'catalog_total_bytes': sum(row['bytes'] for row in rows)}
        return self.fn('approved_inventory')(rows, limits)

    def test_exact_whole_record_digest_file_sha_and_original_string_date(self):
        raw = 'id: synthetic.record\nkind: input\nlabel: café\ndate: 2026-10-07\n'.encode()
        index = {}
        data = self.fn('index_record')(index, raw)
        expected = {'id': 'synthetic.record', 'kind': 'input', 'label': 'café', 'date': '2026-10-07'}
        independent = hashlib.sha256(json.dumps(expected, sort_keys=True, separators=(',', ':'),
            ensure_ascii=True, allow_nan=False).encode()).hexdigest()
        self.assertEqual(data, expected)
        self.assertEqual(index, {'synthetic.record': {'kind': 'input',
            'sha256': hashlib.sha256(raw).hexdigest(), 'record_sha256': independent}})
        alternate = {}
        self.fn('index_record')(alternate, raw + b'\n')
        self.assertNotEqual(index['synthetic.record']['sha256'], alternate['synthetic.record']['sha256'])
        self.assertEqual(index['synthetic.record']['record_sha256'], alternate['synthetic.record']['record_sha256'])

    def test_duplicate_record_ids_refuse_full_index(self):
        records = self.folder / 'records'
        records.mkdir()
        (records / 'a.yaml').write_bytes(b'id: synthetic.duplicate\nkind: input\n')
        (records / 'b.yaml').write_bytes(b'id: synthetic.duplicate\nkind: kernel\n')
        with self.assertRaisesRegex(self.lifted['Refused'], 'duplicate_record_id'):
            self.fn('build_index')(records, self.inventory(records), self.deadline)

    def test_top_and_nested_duplicate_yaml_keys_refuse(self):
        for raw in (b'id: synthetic.r\nid: synthetic.s\nkind: input\n',
                    b'id: synthetic.r\nkind: input\nnested: {x: 1, x: 2}\n'):
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(self.lifted['Refused'], 'duplicate_yaml_mapping_key'):
                    self.fn('index_record')({}, raw)

    def test_changed_returned_bytes_refuse_even_with_same_length(self):
        original = self.folder / 'synthetic-original.yaml'
        original.write_bytes(b'first')
        pin = self.pin(original)
        original.write_bytes(b'other')
        with self.assertRaisesRegex(self.lifted['Refused'], 'returned_original_bytes_differs'):
            self.fn('returned_bytes')(pin, 128, self.deadline)

    def test_path_inode_swap_during_open_read_refuses(self):
        original = self.folder / 'synthetic-original.yaml'
        replacement = self.folder / 'synthetic-replacement.yaml'
        original.write_bytes(b'unchanged content')
        replacement.write_bytes(b'unchanged content')
        pin = self.pin(original)
        open_original = Path.open
        switched = False
        class SwappingStream:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return self.stream.__exit__(*args)
            def fileno(self):
                return self.stream.fileno()
            def read(self, amount):
                nonlocal switched
                data = self.stream.read(amount)
                if not switched:
                    switched = True
                    os.replace(replacement, original)
                return data
        def patched_open(path, *args, **kwargs):
            stream = open_original(path, *args, **kwargs)
            return SwappingStream(stream) if path == original and args == ('rb',) else stream
        with mock.patch.object(Path, 'open', patched_open):
            with self.assertRaisesRegex(self.lifted['Refused'], 'original_inode_or_content_changed'):
                self.fn('returned_bytes')(pin, 128, self.deadline)
        self.assertTrue(switched)

    def test_added_or_deleted_inventory_body_refuses(self):
        records = self.folder / 'records'
        records.mkdir()
        original = records / 'a.yaml'
        original.write_bytes(b'id: synthetic.a\nkind: input\n')
        approved = self.inventory(records)
        added = records / 'b.yaml'
        added.write_bytes(b'id: synthetic.b\nkind: input\n')
        with self.assertRaisesRegex(self.lifted['Refused'], 'full_catalog_inventory_path_set_changed'):
            self.fn('recheck_catalog')(records, approved, self.deadline)
        added.unlink()
        original.unlink()
        with self.assertRaisesRegex(self.lifted['Refused'], 'full_catalog_inventory_path_set_changed'):
            self.fn('recheck_catalog')(records, approved, self.deadline)

    def test_final_original_source_change_refuses_before_publication(self):
        source = self.folder / 'synthetic-writer-source.py'
        source.write_bytes(b'original synthetic source\n')
        pin = self.pin(source)
        source.write_bytes(b'changed synthetic source!\n')
        destination = self.folder / 'new-metadata'
        calls = []
        def before():
            calls.append('before')
            self.fn('recheck_originals')([pin], self.deadline)
        def after():
            calls.append('after')
        with self.assertRaises(self.lifted['Refused']):
            self.fn('publish')(destination, b'{}\n', b'{}\n', before, after)
        self.assertFalse(destination.exists())
        self.assertEqual(calls, ['before'])

    def test_final_source_recheck_after_publication_precedes_success(self):
        source = self.folder / 'synthetic-writer-source.py'
        source.write_bytes(b'original synthetic source\n')
        pin = self.pin(source)
        destination = self.folder / 'new-metadata'
        calls = []
        def before():
            calls.append('before')
            self.fn('recheck_originals')([pin], self.deadline)
        def after():
            calls.append('after')
            source.write_bytes(b'changed synthetic source!\n')
            self.fn('recheck_originals')([pin], self.deadline)
        with self.assertRaises(self.lifted['Refused']):
            self.fn('publish')(destination, b'{}\n', b'{}\n', before, after)
        self.assertEqual(calls, ['before', 'after'])
        self.assertEqual((destination / 'record-index.json').read_bytes(), b'{}\n')
        # Preserved partial publication is not a success/admission receipt.


if __name__ == '__main__':
    unittest.main(verbosity=2)
