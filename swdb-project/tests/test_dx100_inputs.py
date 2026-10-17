"""Serialized alias copy bounds and cleanup. Updated: 2026-09-25."""
import errno
import os

import pytest

from swdb import artifacts
from swdb.bfs_native import StageFailure
from swdb.dx100_inputs import resolve


@pytest.mark.parametrize('mode', ['copy', 'storage', 'time'])
def test_cross_filesystem_alias_copy_is_bounded_and_never_leaves_partial_input(tmp_path, monkeypatch, mode):
    source = tmp_path / 'source.sg32'
    source.write_bytes(b'identified serialized fixture')
    if mode == 'storage':
        with source.open('ab') as stream:
            stream.truncate(1024**3 + 1)
    class Session:
        folder = tmp_path / 'execution'
        data = {'context': {'budget': {'storage_gib': 1}}}
        calls = 0
        def remaining(self):
            self.calls += 1
            if mode == 'time' and self.calls == 2:
                raise StageFailure('budget_exhausted', 'fixture time budget exhausted')
            return 60
    session = Session()
    session.folder.mkdir()
    original_link = os.link
    def link(first, second):
        if first == source:
            raise OSError(errno.EXDEV, 'fixture cross-filesystem link')
        return original_link(first, second)
    monkeypatch.setattr(os, 'link', link)
    reference = {'path': str(source), 'sha256': artifacts.file_hash(source) if mode != 'storage' else '0' * 64}
    registered = {'representation': {'format': 'gapbs_sg32le'}}
    if mode == 'copy':
        alias, details = resolve(session, tmp_path, reference, 'dx100-gapbs', registered)
        assert alias.read_bytes() == source.read_bytes()
        assert details['provenance'] == {'method': 'bounded_copy', 'storage_charge_bytes': source.stat().st_size}
        assert alias.stat().st_ino != source.stat().st_ino
    else:
        with pytest.raises(StageFailure, match='budget'):
            resolve(session, tmp_path, reference, 'dx100-gapbs', registered)
        assert not list((tmp_path / 'dx100-loader-inputs').iterdir())
