"""Regression for an observed active CMake-tree monitor race. Updated: 2026-09-25."""

from pathlib import Path
import runpy
import subprocess

import pytest


@pytest.mark.parametrize("stderr,code,accepted", [
    ("", 0, True),
    ("du: cannot access '/build/CMakeScratch/check.tmp': No such file or directory\n", 1, True),
    ("du: cannot read directory '/build/private': Permission denied\n", 1, False),
])
def test_active_build_storage_monitor_preserves_vanished_file_warning(monkeypatch, stderr, code, accepted):
    namespace = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/dx100_build.py"))
    def completed(command, **kwargs):
        return subprocess.CompletedProcess(command, code, "204800\t/build\n", stderr)
    monkeypatch.setattr(subprocess, "run", completed)
    if accepted:
        size, warnings = namespace["disk_usage_kib"](Path("/build"))
        assert size == 204800
        assert warnings == stderr.splitlines()
    else:
        with pytest.raises(subprocess.CalledProcessError):
            namespace["disk_usage_kib"](Path("/build"))
