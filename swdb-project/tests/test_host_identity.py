"""The fixture-host seam keeps the suite host-independent without weakening real-host guards.

Created 2026-10-13 ET. The suite runs as `conftest.FIXTURE_HOST` everywhere (mbit10
included); these tests start `swdb` children that pretend to be mbit10 through
`socket.gethostname`, with and without `SWDB_FIXTURE_HOST`, to show the override is
the only thing that lifts the mbit10 policy and that it can never name a real host.
"""

import json
import os
import subprocess
import sys

import pytest
import yaml

from conftest import FIXTURE_HOST, REPO
from swdb import host_identity

EXTENSA = ("--mode", "extensa", "--campaign", "extensa-gem5-bfs-20261004-f1")


def as_host(hostname, code, *, fixture=None):
    """Run `code` in a child whose real host name is `hostname`; `fixture` sets the override."""
    env = {key: value for key, value in os.environ.items() if key != host_identity.FIXTURE_HOST_ENV}
    if fixture is not None:
        env[host_identity.FIXTURE_HOST_ENV] = fixture
    prelude = f"import socket; socket.gethostname = lambda: {hostname!r}\n"
    return subprocess.run([sys.executable, "-c", prelude + code], cwd=REPO, env=env,
                          capture_output=True, text=True, timeout=120)


NAMES = "from swdb import host_identity as h; print(h.short_name(), h.full_name())"


def test_without_the_override_the_real_host_name_is_used():
    result = as_host("mbit10.eecs.umich.edu", NAMES)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["mbit10", "mbit10.eecs.umich.edu"]


def test_the_override_names_only_a_fixture_host():
    result = as_host("mbit10.eecs.umich.edu", NAMES, fixture=FIXTURE_HOST)
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == [FIXTURE_HOST, FIXTURE_HOST]


@pytest.mark.parametrize("claimed", ["mbit10", "mbit9", "fixture-mac.local", "swdb-fixture.mbit10"])
def test_the_override_cannot_claim_a_real_host(claimed):
    result = as_host("laptop.local", NAMES, fixture=claimed)
    assert result.returncode != 0
    assert "is not a fixture host name" in result.stderr


def test_the_test_process_itself_is_the_fixture_host():
    import socket
    assert socket.gethostname() == FIXTURE_HOST
    assert host_identity.short_name() == FIXTURE_HOST
    assert os.environ[host_identity.FIXTURE_HOST_ENV] == FIXTURE_HOST


def test_real_host_fixture_restores_the_real_name(real_host):
    import socket
    assert socket.gethostname().split(".")[0] == real_host
    assert host_identity.FIXTURE_HOST_ENV not in os.environ


@pytest.mark.parametrize("fixture", [None, FIXTURE_HOST])
def test_mbit10_lane_guard_still_fires_unless_the_seam_is_overridden(records, tmp_path, fixture):
    """A lane-free machine on mbit10 is refused; only the fixture override lifts the guard."""
    records.copy_repo("operations", "hardware_targets", "machines")
    machine = records.read("machines/mbit10.yaml")
    machine.update(id="lanefree", hostname=fixture or "mbit10", lane_required=False)
    records.write("machines/lanefree.yaml", machine)
    model = tmp_path / "model"
    model.mkdir()
    request = {"message_version": "1.0", "id": "lane-guard", "fixture": True, "machine": "lanefree",
               "hardware_target": "dx100-e4fc4af-4c", "model_root": str(model),
               "fixture_command": [sys.executable, "-c", "pass"],
               "budget": {"total_seconds": 20, "memory_gib": 1, "storage_gib": 1, "jobs": 1}}
    path = tmp_path / "request.yaml"
    path.write_text(yaml.safe_dump(request))
    argv = ["swdb", "dx100-build", "--records", str(records.path), str(path), "--runs-dir", str(tmp_path / "runs"), "--lane", "0",
            "--format", "json", *EXTENSA]
    result = as_host("mbit10.eecs.umich.edu", f"import runpy, sys; sys.argv = {argv!r}; "
                     "runpy.run_module('swdb', run_name='__main__')", fixture=fixture)
    assert result.stdout, result.stderr
    reason = json.loads(result.stdout)["outcome"]["reason"] or ""
    if fixture is None:
        assert result.returncode == 1
        assert reason == "mbit10 cannot disable socket lane policy"
    else:
        assert "socket lane" not in reason, reason
