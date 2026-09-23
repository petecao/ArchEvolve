"""Shared test helpers: every test drives `swdb` as a separate process."""

import copy
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
DB_COMMANDS = {"build", "sql", "find", "implementations", "add", "profile"}


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


@pytest.fixture
def records(tmp_path):
    """An empty temporary records folder with helpers to write records into it."""

    class Records:
        path = tmp_path / "records"

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
            """Copy the repo's own records (all, or only these kind folders) into this folder."""
            source = REPO / "records"
            for folder in kinds or [p.name for p in source.iterdir() if p.is_dir()]:
                if (source / folder).exists():
                    shutil.copytree(source / folder, self.path / folder, dirs_exist_ok=True)
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
