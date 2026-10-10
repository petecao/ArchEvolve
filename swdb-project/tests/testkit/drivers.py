"""The ticket 58 driver under test. Created 2026-10-05 ET (code review T1/T3), from
tests/test_provider_login.py, which loaded the driver script inline."""

from conftest import REPO
from testkit.toolchain import load_script

CAMPAIGN = "extensa-gem5-bfs-20261004-s1"


def spec_enough_driver():
    """A fresh module of tools/spec_enough_driver.py (it is a script, not a package module)."""
    return load_script(REPO / "tools" / "spec_enough_driver.py", "spec_enough_driver_under_test")


def driver_args(module, tmp_path, provider_config=None, *, attempt="a3", stop_after_failures=2):
    return module.argparse.Namespace(campaign=CAMPAIGN, runs_root=tmp_path, attempt=attempt,
                                     provider_config=provider_config or tmp_path / "fixture.json",
                                     codex_command="codex", lane_seconds=module.LANE_SECONDS,
                                     stop_after_failures=stop_after_failures)


def campaign_root(tmp_path):
    return tmp_path / "extensa" / CAMPAIGN


def offline_inputs(module, monkeypatch):
    """Replace the snapshot reconstruction and the pinned documents with one small input file."""
    monkeypatch.setattr(module, "base_source", lambda scratch: {})
    monkeypatch.setattr(module, "arm_files", lambda arm, base: ({"spec/a.md": "spec"}, {}))
