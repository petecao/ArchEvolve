"""Shared test helpers: every test drives `swdb` as a separate process."""

import copy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def run_swdb(*args):
    """Run `python -m swdb <args>` from the repo root and return the completed process."""
    return subprocess.run(
        [sys.executable, "-m", "swdb", *map(str, args)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )


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

    rec = Records()
    rec.path.mkdir()
    return rec
