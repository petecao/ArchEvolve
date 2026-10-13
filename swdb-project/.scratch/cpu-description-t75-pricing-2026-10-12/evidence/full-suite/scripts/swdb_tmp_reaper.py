"""Run-local pytest plugin (cpud full suite 2026-10-13 ET; not part of the repo).
After each test: record which /data1/yanruj/EvolveSWDB_sources namespaces came from its tmp_path,
then delete the tmp_path so the basetemp cannot grow with retained per-test copies."""
import hashlib, os, shutil
from pathlib import Path
import pytest

SRC = Path('/data1/yanruj/EvolveSWDB_sources')
LOG = os.environ.get('SWDB_REAPER_LOG')


def _record(root, depth=4):
    if not LOG or not root.is_dir():
        return
    hits = []
    base = len(root.parts)
    for d, dirs, _ in os.walk(root):
        if len(Path(d).parts) - base >= depth:
            dirs[:] = []
        ns = hashlib.sha256(str(Path(d).resolve()).encode()).hexdigest()[:16]
        if (SRC / ns).exists():
            hits.append(f'{ns}\t{d}\n')
    if hits:
        with open(f"{LOG}.{os.environ.get('PYTEST_XDIST_WORKER', 'main')}", 'a') as f:
            f.writelines(hits)


_PATHS = {}


@pytest.hookimpl(wrapper=True)
def pytest_fixture_setup(fixturedef, request):
    # Track tmp_path at creation: item.funcargs misses it when a later fixture's setup errors.
    result = yield
    if fixturedef.argname == 'tmp_path' and isinstance(result, Path):
        _PATHS[request.node.nodeid] = result
    return result


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_teardown(item, nextitem):
    yield
    p = _PATHS.pop(item.nodeid, None) or getattr(item, 'funcargs', {}).get('tmp_path')
    if isinstance(p, Path):
        try:
            _record(p)
        finally:
            # Empty the folder but keep it: pytest numbers the next same-prefix tmp_path after the
            # existing ones, so a deleted folder would let the next test reuse the same path (and the
            # same /data1/yanruj/EvolveSWDB_sources namespace, which then collides).
            for child in list(p.iterdir()) if p.is_dir() else []:
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child, ignore_errors=True)
                else:
                    child.unlink(missing_ok=True)


def pytest_sessionfinish(session, exitstatus):
    factory = getattr(session.config, '_tmp_path_factory', None)
    bt = getattr(factory, '_basetemp', None) if factory else None
    if bt is not None:
        _record(Path(bt), depth=5)
