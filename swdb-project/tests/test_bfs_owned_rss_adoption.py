"""Subreaper adoption during an owned RSS sample. Date: 2026-09-29 ET.

Kept apart from test_bfs_owned_rss.py, whose case list is pinned by the frozen lease
supplement plan (tests/test_bfs_linux_fixture.py).
"""
import shutil

import pytest

from scripts.bfs_owned_rss import DescendantRSS
from tests.test_bfs_owned_rss import process


def test_child_adopted_by_owned_subreaper_after_parent_exit_stays_owned(tmp_path, monkeypatch):
    """2026-09-29: the routes a2 reparent race is benign under an owned subreaper."""
    process(tmp_path, 100, 1, 1000, children=[101])
    process(tmp_path, 101, 100, 1001, children=[102])
    process(tmp_path, 102, 101, 1002)
    sampler = DescendantRSS(100, tmp_path)
    original = sampler._stat

    def parent_exits_before_child_read(pid):
        if pid == 102 and (tmp_path / '101').exists():
            shutil.rmtree(tmp_path / '101')
            process(tmp_path, 102, 100, 1002)
        return original(pid)

    monkeypatch.setattr(sampler, '_stat', parent_exits_before_child_read)
    assert {row['pid'] for row in sampler.sample()['processes']} == {100, 101, 102}
    assert sampler.known[102] == 1002


def test_child_adopted_by_unowned_process_is_still_refused(tmp_path, monkeypatch):
    process(tmp_path, 100, 1, 1000, children=[101])
    process(tmp_path, 101, 100, 1001, children=[102])
    process(tmp_path, 102, 101, 1002)
    sampler = DescendantRSS(100, tmp_path)
    original = sampler._stat

    def adopted_by_init(pid):
        if pid == 102 and (tmp_path / '101').exists():
            shutil.rmtree(tmp_path / '101')
            process(tmp_path, 1, 0, 1)
            process(tmp_path, 102, 1, 1002)
        return original(pid)

    monkeypatch.setattr(sampler, '_stat', adopted_by_init)
    with pytest.raises(ValueError, match='discovering parent'):
        sampler.sample()
