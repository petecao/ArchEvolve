"""`swdb capture-machine`: parse a saved read-only capture into a machine record.
Created 2026-09-22."""

import yaml

from conftest import FIXTURES, run_swdb

CAPTURE = FIXTURES / "machine" / "mbit10-capture.txt"


def test_capture_from_file_prints_a_valid_machine_record(records):
    result = run_swdb("capture-machine", "--id", "mbit10-copy", "--from-file", CAPTURE)
    assert result.returncode == 0, result.stderr
    data = yaml.safe_load(result.stdout)
    assert data["id"] == "mbit10-copy" and data["hostname"] == "mbit10"
    assert data["cpu"]["logical_cpus"] == 64 and data["cpu"]["threads_per_core"] == 2
    assert [c["size_bytes"] for c in data["caches"]] == [49152, 32768, 1310720, 25165824]
    assert [n["node"] for n in data["numa_nodes"]] == [0, 1]
    assert data["numa_nodes"][1]["cpus"].startswith("1,3,5")
    assert data["os"]["kernel"].startswith("6.8.0")
    assert data["counters"]["perf_event_paranoid"] == 4
    assert data["counters"]["hardware_counters_available"]["value"] is False
    assert "not in the vtune group" in data["counters"]["hardware_counters_available"]["note"]
    assert data["capture"]["date"].endswith("Z")
    assert data["lane_required"] is True     # two NUMA nodes: profiles only inside a socket lane
    records.write_text("machines/m.yaml", result.stdout)
    assert records.validate().returncode == 0


def test_capture_missing_a_section_fails(tmp_path):
    broken = tmp_path / "broken.txt"
    broken.write_text(CAPTURE.read_text().replace("### lscpu-caches", "### something-else"))
    result = run_swdb("capture-machine", "--id", "x", "--from-file", broken)
    assert result.returncode == 1
    assert "lscpu-caches" in result.stderr
