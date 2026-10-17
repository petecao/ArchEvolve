"""Store parse cache contracts. Created 2026-09-27 ET.

The cache only avoids re-parsing unchanged files inside one process; it must
never serve stale or shared data.
"""
import os

from swdb import store as store_module
from swdb.store import Store


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_unchanged_file_is_served_from_cache_as_fresh_objects(tmp_path, monkeypatch):
    write(tmp_path/'machines/m.yaml', 'kind: machine\nid: m\ncreated: 2026-09-27\nitems: [1, 2]\n')
    first = Store(tmp_path).get('m')
    calls = []
    original = store_module.yamlio.load
    monkeypatch.setattr(store_module.yamlio, 'load', lambda path: calls.append(path) or original(path))
    second = Store(tmp_path).get('m')
    assert calls == [] and second == first and second['created'] == '2026-09-27'
    second['items'].append(3)
    assert Store(tmp_path).get('m')['items'] == [1, 2]


def test_rewritten_file_is_reparsed(tmp_path):
    path = tmp_path/'machines/m.yaml'
    write(path, 'kind: machine\nid: m\nvalue: 1\n')
    assert Store(tmp_path).get('m')['value'] == 1
    replacement = tmp_path/'machines/.m.tmp'
    replacement.write_text('kind: machine\nid: m\nvalue: 2\n')
    os.replace(replacement, path)
    assert Store(tmp_path).get('m')['value'] == 2
    stat = path.stat()
    path.write_text('kind: machine\nid: m\nvalue: 3\n')  # same inode and size, new times
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns+1_000_000))
    assert Store(tmp_path).get('m')['value'] == 3


def test_non_json_round_trip_record_is_not_cached(tmp_path, monkeypatch):
    write(tmp_path/'machines/m.yaml', 'kind: machine\nid: m\n1: integer key\n')
    assert Store(tmp_path).get('m')[1] == 'integer key'
    calls = []
    original = store_module.yamlio.load
    monkeypatch.setattr(store_module.yamlio, 'load', lambda path: calls.append(path) or original(path))
    assert Store(tmp_path).get('m')[1] == 'integer key' and len(calls) == 1


def test_invalid_yaml_is_still_reported(tmp_path):
    write(tmp_path/'machines/m.yaml', 'kind: [unclosed\n')
    assert Store(tmp_path).problems
