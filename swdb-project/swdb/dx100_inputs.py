"""Stable serialized-input aliases for the pinned loader. Updated: 2026-09-25."""
import errno
import os
from pathlib import Path
import uuid

from swdb import artifacts
from swdb.bfs_native import StageFailure
from swdb.cli import Failure


def verify(reference):
    path = Path(reference['path'])
    if path.is_symlink() or not path.is_file() or artifacts.file_hash(path) != reference['sha256']:
        raise Failure('serialized loader alias is missing, unsafe, or differs from its recorded hash')
    return path


def resolve(session, runs, original, application, registered):
    source = Path(original['path'])
    if source.suffix == '.sg':
        return source, None
    expected = {'gapbs': 'gapbs_sg64le', 'dx100-gapbs': 'gapbs_sg32le'}
    if (not registered or application not in expected
            or registered['representation']['format'] != expected[application]):
        raise Failure('non-.sg inputs require a registered serialized SG representation for the selected application')
    directory = Path(runs).resolve() / 'dx100-loader-inputs'
    directory.mkdir(exist_ok=True)
    if directory.is_symlink():
        raise Failure('serialized loader alias directory cannot be a symlink')
    alias = directory / (application + '-' + original['sha256'] + '.sg')
    reference = {'path': str(alias), 'sha256': original['sha256']}
    provenance = {'method': 'existing_alias', 'storage_charge_bytes': 0}
    session.remaining()
    if not alias.exists() and not alias.is_symlink():
        try:
            os.link(source, alias)
            provenance['method'] = 'hardlink'
        except FileExistsError:
            pass
        except OSError as exc:
            if exc.errno != errno.EXDEV:
                raise
            pending = directory / (alias.name + '.pending-' + uuid.uuid4().hex)
            used = sum(path.stat().st_size for path in session.folder.rglob('*') if path.is_file())
            available = session.data['context']['budget']['storage_gib'] * 1024**3 - used
            if source.stat().st_size > available:
                raise StageFailure('budget_exhausted', 'serialized loader alias copy exceeds raw storage budget')
            copied = 0
            try:
                with source.open('rb') as reader, pending.open('xb') as writer:
                    while True:
                        session.remaining()
                        chunk = reader.read(1024 * 1024)
                        if not chunk:
                            break
                        copied += len(chunk)
                        if copied > available:
                            raise StageFailure('budget_exhausted', 'serialized loader alias copy exceeds raw storage budget')
                        writer.write(chunk)
                verify({'path': str(pending), 'sha256': original['sha256']})
                session.remaining()
                try:
                    os.link(pending, alias)  # Publish without replacing any existing alias.
                    provenance.update(method='bounded_copy', storage_charge_bytes=copied)
                except FileExistsError:
                    pass
            finally:
                pending.unlink(missing_ok=True)
    details = {'format': 'swdb.dx100.loader-input.v1', 'application': application,
        'serialization': expected[application], 'original': dict(original), 'alias': reference,
        'provenance': provenance}
    # Preserve the attempted alias and any allocation in a failed stage too.
    session.data['context']['loader_input'] = details
    verify(reference)
    if provenance['method'] == 'existing_alias':
        provenance['method'] = 'existing_verified_alias'
    session.remaining()
    return alias, details
