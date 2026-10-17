"""The checkout guard reports and never deletes (code review T6). Created 2026-10-05 ET.

The autouse guard in tests/conftest.py fails any test that creates, changes or deletes a file
under the checkout's records/ or library/. It used to delete the files a test created; a guard
must not delete files from the real checkout, so it now only fails and reports. The guard is run
here on a throwaway copy of the test package whose "checkout" is a temporary folder.
"""

import os
import shutil
import subprocess
import sys

from conftest import REPO, checkout_changes, checkout_report

PROBE = '''
from pathlib import Path


def test_writes_into_the_checkout_records():
    (Path(__file__).resolve().parents[1] / "records" / "probe.yaml").write_text("id: probe\\n")
'''


def test_the_report_names_each_change_relative_to_the_checkout():
    before = {str(REPO / "records/a.yaml"): (1, 1), str(REPO / "records/b.yaml"): (1, 1)}
    after = {str(REPO / "records/a.yaml"): (2, 2), str(REPO / "records/c.yaml"): (1, 1)}
    changes = checkout_changes(before, after)
    assert changes == {"created": [str(REPO / "records/c.yaml")], "changed": [str(REPO / "records/a.yaml")],
                       "deleted": [str(REPO / "records/b.yaml")]}
    report = checkout_report(changes)
    assert "left in place" in report and "records/c.yaml" in report and str(REPO) not in report
    assert checkout_report(checkout_changes(before, before)) is None


def test_a_test_that_writes_into_the_checkout_fails_and_its_file_is_kept(tmp_path):
    copy = tmp_path / "checkout"
    shutil.copytree(REPO / "tests" / "testkit", copy / "tests" / "testkit")
    shutil.copy(REPO / "tests" / "conftest.py", copy / "tests" / "conftest.py")
    (copy / "records").mkdir()
    (copy / "library").mkdir()
    (copy / "tests" / "test_probe.py").write_text(PROBE)
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(REPO), os.environ.get("PYTHONPATH", "")])}
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--rootdir", str(copy),
                             "--basetemp", str(tmp_path / "inner"), str(copy / "tests" / "test_probe.py")],
                            cwd=copy, capture_output=True, text=True, env=env, timeout=300)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "test wrote into the checkout's records/library" in result.stdout
    assert "records/probe.yaml" in result.stdout
    assert (copy / "records" / "probe.yaml").read_text() == "id: probe\n"         # reported, never deleted
