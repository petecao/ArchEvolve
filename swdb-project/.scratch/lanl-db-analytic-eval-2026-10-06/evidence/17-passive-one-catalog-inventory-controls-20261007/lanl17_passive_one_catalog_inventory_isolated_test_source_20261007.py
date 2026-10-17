#!/usr/bin/env python3
"""NOT RUN: four isolated synthetic passive-observation tests, parent review required.

Only exact closed named helper/class, constant Assign and two loader-policy AST
nodes are lifted after checking reviewed reader76 bytes. No full reader/module
import, main/source inspection, actual catalog/M2/request/control execution,
Store/SWDB/public validation/auditor/collector/writer/campaign/native/provider,
Git or SSH runs. All fixtures belong to fresh private temporary directories.
Original7a8 and authorR1five test batches are not repeated.
"""
import ast
import copy
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

SOURCE = Path('/private/tmp/lanl17_read_passive_one_catalog_inventory_20261007.py')
SOURCE_BYTES = 29653
SOURCE_SHA256 = '76b86959ceca7a162a34b7a2d1e633ee9523d0b9cc7f629e9fbeeb4e101aa176'
CONSTANTS = {'MAX_CATALOG_FILE', 'MAX_CATALOG_TOTAL', 'MAX_RECORDS', 'STAMP_KEYS', 'FORBIDDEN_NAMES'}
HELPERS = {'Refused', 'require', 'sha', 'digest', 'exact', 'full_hash', 'RecordLoader',
           'no_duplicates', 'plain_record', 'remaining', 'checked_path', 'stamp', 'returned_bytes',
           'record_relative', 'scan_catalog', 'require_inventory_equal', 'privacy_path',
           'observe_inventory_row', 'observe_one_inventory', 'observe_present_summary'}


def pinned_source_bytes():
    raw = SOURCE.read_bytes()
    if len(raw) != SOURCE_BYTES or hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise AssertionError('isolated_passive_test_reviewed_source_pin_differs')
    return raw


def isolated_symbols():
    parsed = ast.parse(pinned_source_bytes(), filename=str(SOURCE))
    selected, seen, loader_nodes = [], set(), []
    for node in parsed.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in HELPERS:
            selected.append(copy.deepcopy(node))
            seen.add(node.name)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in CONSTANTS:
                selected.append(copy.deepcopy(node))
                seen.add(target.id)
            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and \
                    target.value.id == 'RecordLoader' and target.attr == 'yaml_implicit_resolvers':
                selected.append(copy.deepcopy(node))
                loader_nodes.append('timestamp_resolvers')
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and \
                isinstance(node.value.func, ast.Attribute) and isinstance(node.value.func.value, ast.Name) and \
                node.value.func.value.id == 'RecordLoader' and node.value.func.attr == 'add_constructor':
            selected.append(copy.deepcopy(node))
            loader_nodes.append('duplicate_keys')
    if seen != HELPERS | CONSTANTS or loader_nodes != ['timestamp_resolvers', 'duplicate_keys']:
        raise AssertionError('closed_exact_passive_helper_constant_loader_projection_differs')
    if len(selected) != len(HELPERS) + len(CONSTANTS) + 2 or any(
            isinstance(node, (ast.Import, ast.ImportFrom)) for node in selected):
        raise AssertionError('closed_AST_only_no_source_module_import_required')
    namespace = {'hashlib': hashlib, 'json': json, 'math': math, 'os': os,
                 'Path': Path, 'PurePosixPath': PurePosixPath, 're': re, 'stat': stat,
                 'time': time, 'yaml': yaml}
    # Executes only these pinned, explicit original nodes if parent later approves
    # this synthetic test; never evaluates source main or an arbitrary expression.
    module = ast.fix_missing_locations(ast.Module(body=selected, type_ignores=[]))
    exec(compile(module, '<reviewed-passive-synthetic-closed-AST>', 'exec'), namespace)
    return namespace


class PassiveObservationSyntheticCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_source = pinned_source_bytes()
        cls.lifted = isolated_symbols()

    @classmethod
    def tearDownClass(cls):
        if pinned_source_bytes() != cls.original_source:
            raise AssertionError('reviewed_reader_source_changed_during_synthetic_checks')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lanl17-passive-synthetic-', dir='/private/tmp')
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)  # Only this test's fresh synthetic files.
        self.deadline = time.monotonic() + 30

    def fn(self, name):
        return self.lifted[name]

    def independent_stamp(self, path):
        status = path.stat()
        return {'dev': status.st_dev, 'ino': status.st_ino, 'mode': status.st_mode,
                'uid': status.st_uid, 'size': status.st_size,
                'mtime_ns': status.st_mtime_ns, 'ctime_ns': status.st_ctime_ns}

    def test_sorted_exact_inventory_hashes_opaque_bodies_without_YAML_parse(self):
        # Invalid UTF8/NUL bodies could never be parsed as ordinary record YAML.
        paths = {'z.yaml': b'\xff\x00opaque synthetic z',
                 'nested/a.yml': b'\x00\x00opaque synthetic a'}
        for rel, raw in paths.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        (self.root / 'ignored.bin').write_bytes(b'outside public suffix set')
        (self.root / '.ignored.yaml').write_bytes(b'hidden public-looking sentinel')
        expected = {rel: {'path': rel, 'bytes': len(paths[rel]),
                         'sha256': hashlib.sha256(paths[rel]).hexdigest(),
                         'stat': self.independent_stamp(self.root / rel)}
                    for rel in sorted(paths)}
        with mock.patch.object(yaml, 'load', side_effect=AssertionError('ordinary_body_YAML_parse_forbidden')) as loader:
            actual, total = self.fn('observe_one_inventory')(self.root, self.deadline)
        loader.assert_not_called()
        self.assertEqual(list(actual), ['nested/a.yml', 'z.yaml'])
        self.assertEqual(actual, expected)
        self.assertEqual(total, sum(len(raw) for raw in paths.values()))
        self.assertEqual(set(next(iter(actual.values()))['stat']), set(self.lifted['STAMP_KEYS']))

    def test_same_size_same_bytes_inode_replacement_refuses_before_hash(self):
        path, replacement = self.root / 'one.yaml', self.root / 'replacement.yaml'
        sentinel = b'identical synthetic opaque body'
        path.write_bytes(sentinel)
        replacement.write_bytes(sentinel)
        expected = self.independent_stamp(path)
        self.assertEqual(path.stat().st_size, replacement.stat().st_size)
        self.assertNotEqual(path.stat().st_ino, replacement.stat().st_ino)
        os.replace(replacement, path)
        with mock.patch.object(hashlib, 'sha256', side_effect=AssertionError('changed_inode_must_refuse_before_hash')) as hasher:
            with self.assertRaisesRegex(self.lifted['Refused'], 'observed_catalog_fd_inode_stat_UID_differs'):
                self.fn('observe_inventory_row')(self.root, 'one.yaml', expected, self.deadline)
        hasher.assert_not_called()

    def test_unique_one_catalog_2GiB_overflow_refuses_before_body_hashing(self):
        self.assertEqual(self.lifted['MAX_CATALOG_FILE'], 128 * 1024 * 1024)
        self.assertEqual(self.lifted['MAX_CATALOG_TOTAL'], 2 * 1024 * 1024 * 1024)
        # Seventeen declared128MiB files exceed2GiB. These are metadata only;
        # no large sentinel allocation, original file read or cap override occurs.
        one = dict(self.independent_stamp(self.root), size=self.lifted['MAX_CATALOG_FILE'])
        scanned = {f'synthetic-{i:02d}.yaml': dict(one) for i in range(17)}
        with mock.patch.dict(self.lifted, {'scan_catalog': mock.Mock(return_value=scanned),
                                         'observe_inventory_row': mock.Mock(side_effect=AssertionError('overflow_must_precede_body_hash'))}):
            with self.assertRaisesRegex(self.lifted['Refused'], 'unchanged_2GiB_unique_one_catalog_bound_exceeded'):
                self.fn('observe_one_inventory')(self.root, self.deadline)
            self.lifted['observe_inventory_row'].assert_not_called()
            self.lifted['scan_catalog'].assert_called_once_with(self.root, self.deadline)

    def test_explicit_present_summary_exact_policy_and_wrong_CID_source_refusal(self):
        campaign, revision = 'synthetic.extensa.p1', '1' * 40
        rel = 'summaries/explicit-original.yaml'
        path = self.root / rel
        path.parent.mkdir()
        raw = ('id: synthetic.extensa.p1.summary\n'
               'kind: campaign_summary\n'
               'campaign: synthetic.extensa.p1\n'
               'mode: extensa\n'
               'swdb_commit: "' + revision + '"\n'
               'date: 2026-10-07\n'
               'label: café\n').encode('utf8')
        path.write_bytes(raw)
        inventory, _ = self.fn('observe_one_inventory')(self.root, self.deadline)
        expected_record = {'id': campaign + '.summary', 'kind': 'campaign_summary',
                           'campaign': campaign, 'mode': 'extensa', 'swdb_commit': revision,
                           'date': '2026-10-07', 'label': 'café'}
        expected_digest = hashlib.sha256(json.dumps(expected_record, sort_keys=True,
            separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
        binding, original_pin = self.fn('observe_present_summary')(
            self.root, rel, inventory, campaign, revision, self.deadline)
        self.assertEqual(binding, {'state': 'present', 'path': rel,
            'id': campaign + '.summary', 'record_sha256': expected_digest})
        self.assertEqual(original_pin, {'path': str(path), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest(), 'id': campaign + '.summary',
            'kind': 'campaign_summary', 'record_sha256': expected_digest})
        for wrong_campaign, wrong_revision in (('synthetic.extensa.p2', revision), (campaign, '2' * 40)):
            with self.subTest(wrong_CID=wrong_campaign != campaign, wrong_source=wrong_revision != revision):
                with self.assertRaisesRegex(self.lifted['Refused'], 'explicit_original_present_summary_identity_source_differs'):
                    self.fn('observe_present_summary')(
                        self.root, rel, inventory, wrong_campaign, wrong_revision, self.deadline)
        self.assertEqual(path.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main(verbosity=2)
