"""Shared test helpers: every test drives `swdb` as a separate process.

Updated 2026-10-05 ET (code review T1, T6): fixtures shared by several test modules live in
`tests/testkit/` modules registered below as plugins, so no test module imports another test
module or calls a fixture through `__wrapped__`; plain builders (`make_records`,
`testkit.proposals.build_proposal_setup`, ...) serve module-scoped seeds. The checkout guard
fails the test and reports; it never deletes files from the real checkout.
"""

import copy
import functools
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from swdb import host_identity

REPO = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
DB_COMMANDS = {"build", "sql", "find", "implementations", "add", "profile"}

pytest.register_assert_rewrite("testkit")
pytest_plugins = ["testkit.certification_records", "testkit.proposals", "testkit.bfs_native", "testkit.bfs_protocol", "testkit.extensa",
                  "testkit.extensa_targets", "testkit.bfs_native_scalable", "testkit.provider_workspace",
                  "testkit.toolchain", "testkit.native_pilot", "testkit.profile_packages", "testkit.analytic",
                  "testkit.vector_reallocation"]


#: 2026-10-13 ET: the suite runs as this fixture host on every machine, mbit10 included.
FIXTURE_HOST = "swdb-fixture-host"
REAL_GETHOSTNAME = socket.gethostname


@pytest.fixture(scope="session", autouse=True)
def fixture_host():
    """Run the whole suite as `FIXTURE_HOST`, never as the machine it happens to run on.

    On mbit10 the real host name switches on lab policy (socket lanes, `/data1/yanruj`
    build and source roots, NUMA preflight) that a test's fixture machine does not carry,
    and shared `/data1` source snapshots collide across tests and runs. `swdb` child
    processes get the fixture name through `host_identity.FIXTURE_HOST_ENV`; this process
    gets it through `socket.gethostname`, which a test may still patch to `mbit10` to
    opt into lab behavior. Session scope, so module-scoped seeds see it too. A test that
    needs the real host requests `real_host`."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv(host_identity.FIXTURE_HOST_ENV, FIXTURE_HOST)
        patch.setattr(host_identity, "_FIXTURE_HOST", None)    # in-process: socket.gethostname decides
        patch.setattr(socket, "gethostname", lambda: FIXTURE_HOST)
        yield FIXTURE_HOST


@pytest.fixture
def real_host(monkeypatch):
    """Opt out of the fixture host: this test and its `swdb` children see the real host."""
    monkeypatch.delenv(host_identity.FIXTURE_HOST_ENV, raising=False)
    monkeypatch.setattr(socket, "gethostname", REAL_GETHOSTNAME)
    return REAL_GETHOSTNAME().split(".")[0]


def run_swdb(*args, env=None, timeout=600):
    """Run `python -m swdb <args>` from the repo root and return the completed process."""
    full_env = dict(os.environ)
    full_env.update(env or {})
    return subprocess.run(
        [sys.executable, "-m", "swdb", *map(str, args)],
        cwd=REPO,
        capture_output=True,
        text=True,
        env=full_env,
        timeout=timeout,
    )


def read_yaml(path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_fixture(name):
    """Return a fresh copy of a fixture record as a dict."""
    with open(FIXTURES / name, encoding="utf-8") as fh:
        return copy.deepcopy(yaml.safe_load(fh))


@functools.lru_cache(maxsize=1)
def _catalog_index():
    """{record ID: path relative to the checkout's records/}, read once per test process."""
    from swdb.access import record_files
    from testkit.record_ids import record_id
    return {record_id(path): Path(rel) for path, rel in record_files(REPO / "records")}


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


@functools.lru_cache(maxsize=None)
def _catalog_refs(rid):
    """The catalog IDs that record `rid` mentions (parsed once per test process)."""
    from swdb.access import read_record
    where = _catalog_index()
    return frozenset(text for text in _strings(read_record(REPO / "records" / where[rid])) if text in where)


def make_records(tmp_path):
    """An empty records folder under `tmp_path` with helpers to write records into it.

    The `records` fixture's builder; module-scoped seeds call it directly (T1, 2026-10-05 ET)."""

    class Records:
        path = Path(tmp_path) / "records"

        def write(self, relpath, data):
            target = self.path / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            return target

        def write_text(self, relpath, text):
            target = self.path / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            return target

        def validate(self):
            return run_swdb("validate", "--records", self.path)

        def swdb(self, command, *args, env=None):
            """Run one swdb command against this folder (with its own database file)."""
            extra = ["--db", self.path.parent / "build" / "swdb.sqlite"] if command in DB_COMMANDS else []
            return run_swdb(command, "--records", self.path, *extra, *args, env=env)

        def read(self, relpath):
            return read_yaml(self.path / relpath)

        def copy_repo(self, *kinds):
            """Copy these kind folders of the repo's own records into this folder.

            2026-10-13 ET (suite closure): with no kinds this no longer copies the whole
            ~1.3 GB store (every swdb command then revalidated all of it and timed out at
            600 s); it copies the reference-closed minimal view `copy_closure()` instead.
            A test that needs more names its roots with `copy_closure(...)`; a test of the
            whole real store uses `copy_whole()` and is marked `whole_store`."""
            if not kinds:
                return self.copy_closure()
            source = REPO / "records"
            for folder in kinds:
                if (source / folder).exists():
                    shutil.copytree(source / folder, self.path / folder, dirs_exist_ok=True)
            return self

        def copy_whole(self):
            """Copy every record of the real store (~1.3 GB). Only for `whole_store` tests."""
            return self.copy_repo(*sorted(p.name for p in (REPO / "records").iterdir() if p.is_dir()))

        def copy_closure(self, *roots):
            """Copy only the repo records that `roots` reach through exact ID references.

            2026-10-09 ET: copying the whole ~1 GB catalog made every swdb command reparse
            and revalidate unrelated estimates for minutes. Small catalog kinds are kept
            whole, as in the native-acceptance `minimal_view`; other records are kept only
            when a kept record mentions their ID. Non-YAML record-root files are copied.
            The copied store is still fully validated by the command under test.
            2026-10-13 ET: the ID index and each record's references are read once per
            test process (`_catalog_refs`); the checkout's records are guarded read-only."""
            source = REPO / "records"
            where, refs = _catalog_index(), _catalog_refs
            assert all(root in where for root in roots), roots
            whole = {"applications", "kernels", "implementations", "operations", "intrinsics",
                     "hardware_targets", "machines", "workloads", "inputs", "strategies"}
            keep, queue = set(), [*roots, *(rid for rid, rel in where.items() if rel.parts[0] in whole)]
            while queue:
                rid = queue.pop()
                if rid in keep:
                    continue
                keep.add(rid)
                queue.extend(text for text in refs(rid) if text not in keep)
            for rid in keep:
                (self.path / where[rid]).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source / where[rid], self.path / where[rid])
            for path in source.rglob("*"):
                rel = path.relative_to(source)
                if path.is_file() and path.suffix not in {".yaml", ".yml"} and not any(p.startswith(".") for p in rel.parts):
                    (self.path / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(path, self.path / rel)
            return self

        def add_stub(self):
            """The stub kernel, implementation, tiny input, and a machine record for this host."""
            self.copy_repo("applications")
            self.write("kernels/stub-kernel.yaml", load_fixture("profile/stub-kernel.yaml"))
            self.write("implementations/stub-impl.yaml", load_fixture("profile/stub-impl.yaml"))
            code = self.path / "implementations" / "stub-impl" / "stub_bench.py"
            code.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(FIXTURES / "profile" / "stub_bench.py", code)
            self.write("inputs/tiny-sym.yaml", load_fixture("profile/tiny-input.yaml"))
            machine = read_yaml(REPO / "records" / "machines" / "mbit10.yaml")
            machine["id"] = "testhost"
            machine["hostname"] = socket.gethostname().split(".")[0]
            machine["lane_required"] = False   # the stub runs anywhere; lane tests set it back
            self.write("machines/testhost.yaml", machine)
            return self

    rec = Records()
    rec.path.mkdir()
    return rec


def record_view(folder, *roots):
    """A records folder under `folder` with the reference closure of `roots` (see `copy_closure`).

    2026-10-13 ET (suite closure): for in-process `Store(...)` readers of real evidence, which
    otherwise parse the whole ~1.3 GB checkout store (minutes) for a few records."""
    Path(folder).mkdir(parents=True, exist_ok=True)
    return make_records(folder).copy_closure(*roots).path


@pytest.fixture
def records(tmp_path):
    """An empty temporary records folder with helpers to write records into it."""
    return make_records(tmp_path)


# 2026-10-04 ET (final code review): the suite once left stray `records/*/fixture.*.yaml` files
# in the real checkout. Every test now fails if it creates, changes or deletes a file under the
# checkout's `records/` or `library/`. 2026-10-05 ET (code review T6): the guard only reports;
# it never deletes a file from the real checkout (a deletion there could hide or destroy work).
GUARDED = ("records", "library")


def _checkout_files():
    files = {}
    for name in GUARDED:
        for folder, _dirs, names in os.walk(REPO / name):
            for item in names:
                path = os.path.join(folder, item)
                try:
                    state = os.stat(path)
                except FileNotFoundError:
                    continue
                files[path] = (state.st_size, state.st_mtime_ns)
    return files


def checkout_changes(before, after):
    """{created, changed, deleted} paths between two `_checkout_files` snapshots (empty lists if none)."""
    return {"created": sorted(set(after) - set(before)),
            "changed": sorted(p for p in set(after) & set(before) if after[p] != before[p]),
            "deleted": sorted(set(before) - set(after))}


def checkout_report(changes):
    """The failure text for a test that touched the checkout; None when it did not."""
    if not any(changes.values()):
        return None
    shown = {kind: [os.path.relpath(p, REPO) for p in paths[:5]] for kind, paths in changes.items()}
    return ("test wrote into the checkout's records/library (left in place for inspection; remove "
            f"created files by hand): created={shown['created']} changed={shown['changed']} "
            f"deleted={shown['deleted']}")


@pytest.fixture(autouse=True)
def checkout_records_unchanged():
    before = _checkout_files()
    yield
    report = checkout_report(checkout_changes(before, _checkout_files()))
    if report:
        pytest.fail(report)
