"""Remote PYTHONPATH must not replace our driver helpers; 2026-09-25 ET."""
import os
from pathlib import Path
import subprocess
import sys


def test_smoke_help_ignores_other_repositories_scripts_package(tmp_path):
    foreign = tmp_path / "foreign"
    package = foreign / "scripts"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("raise RuntimeError('foreign scripts imported')\n")
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(foreign)}
    for name in ("dx100_smoke.py", "dx100_candidate_smoke.py", "bfs_simulator_series.py"):
        result = subprocess.run([sys.executable, str(root / "scripts" / name), "--help"],
                                cwd=tmp_path, env=env, text=True, capture_output=True, timeout=20)
        assert result.returncode == 0, result.stderr
        assert "usage:" in result.stdout
