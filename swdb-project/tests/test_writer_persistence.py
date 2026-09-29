"""Fresh, fully validated writes with no cross-request cache. Updated: 2026-09-25."""
import copy
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from swdb import db, workflow, writer, yamlio
from swdb.cli import Failure
from swdb.validate import validate_records


def machine(records, rid='write-test'):
    records.copy_repo('machines')
    data = records.read('machines/mbit10.yaml')
    data['id'] = rid
    return data


def test_persist_creates_then_replaces_original_path_and_refreshes_index(records, tmp_path):
    data = machine(records)
    path = records.write('machines/noncanonical-name.yaml', data)
    data['hostname'] = 'Updated writer fixture'
    index = tmp_path / 'index.sqlite'
    workflow.persist(records.path, data, index)
    assert yamlio.load(path)['hostname'] == data['hostname']
    assert not (records.path / 'machines/write-test.yaml').exists()
    assert not db.is_stale(records.path, index)
    assert json.loads(db.sql(index, "SELECT json FROM records WHERE id='write-test'")[0]['json'])['hostname'] == data['hostname']
    fresh = copy.deepcopy(data)
    fresh['id'] = 'another-write'
    workflow.persist(records.path, fresh, index)
    assert (records.path / 'machines/another-write.yaml').is_file()
    assert json.loads(db.sql(index, "SELECT json FROM records WHERE id='another-write'")[0]['json'])['hostname'] == fresh['hostname']


def test_each_upsert_revalidates_unrelated_current_records_and_writes_nothing_on_failure(records):
    data = machine(records)
    writer.commit(records.path, upsert=[data])
    path = records.path / 'machines/write-test.yaml'
    before = path.read_bytes()
    records.write_text('machines/unrelated.yaml', 'kind: [unclosed\n')
    data['hostname'] = 'Must not appear'
    with pytest.raises(Failure, match='validation failed; nothing written'):
        writer.commit(records.path, upsert=[data])
    assert path.read_bytes() == before
    assert validate_records(records.path).problems


def test_create_only_keeps_duplicate_refusal_and_original_bytes(records, tmp_path):
    data = machine(records)
    workflow.persist(records.path, data, tmp_path / 'index.sqlite', create=True)
    path = records.path / 'machines/write-test.yaml'
    before = path.read_bytes()
    data['hostname'] = 'Rejected duplicate'
    with pytest.raises(Failure, match='already used'):
        workflow.persist(records.path, data, tmp_path / 'index.sqlite', create=True)
    assert path.read_bytes() == before


def test_index_failure_still_reports_the_durable_record(records, tmp_path, monkeypatch):
    data = machine(records)
    def fail(*_args):
        raise OSError('fixture unavailable index')
    monkeypatch.setattr(db, 'build', fail)
    with pytest.raises(Failure, match='persisted, but query indexing failed'):
        workflow.persist(records.path, data, tmp_path / 'index.sqlite')
    assert yamlio.load(records.path / 'machines/write-test.yaml')['id'] == data['id']


def test_concurrent_upserts_select_creation_inside_the_writer_lock(records):
    data = machine(records)
    ready = Barrier(2)
    def write(label):
        current = copy.deepcopy(data)
        current['hostname'] = label
        ready.wait(timeout=5)
        return writer.commit(records.path, upsert=[current])
    with ThreadPoolExecutor(max_workers=2) as pool:
        calls = [pool.submit(write, label) for label in ('first', 'second')]
        assert [call.result(timeout=20) for call in calls] == [['machines/write-test.yaml']] * 2
    result = validate_records(records.path)
    assert not result.problems
    assert result.store.get(data['id'])['hostname'] in {'first', 'second'}
    assert len([r for r in result.store.records if r.id == data['id']]) == 1
