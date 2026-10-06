"""Ticket 80: new BC gem5 records take their labels from the kernel plug-in (spec review C16).

Created: 2026-10-05 ET. Old records (BFS and BC) keep the BFS labels they were written with.
"""

import json

import pytest
import yaml

from conftest import REPO
from swdb import bfs_protocol, dx100_coverage, kernels
from swdb import read_only_checks as checks
from swdb.store import Record, Store

VALUES = {"simTicks": "100", "finalTick": "200"}


def _trace(path, marker):
    path.write_text("50: system.maa: R[0] executeInstruction: my_idx_j: 16, tile size: 16\n"
                    "110: system.maa: I[0] Start [INSTR[opcode(INDIR_ST_VECTOR) datatype(INT32) baseAddr(0x4000)]]\n"
                    "120: system.maa: I[0] recvData: 2 entries received for addr(0x8000), grow(x0) from T[0]!\n"
                    "121: system.maa: I[0] recvData: new_data[2] = SPD[0][0] = 7/7/0.0!\n"
                    "122: system.maa: I[0] recvData: new_data[2] = SPD[0][1] = 9/9/0.0!\n"
                    f"{marker} address=4000 count=20 element_bytes=4\n")
    return path


def test_new_bc_coverage_takes_the_score_labels_and_old_records_keep_the_bfs_labels(tmp_path):
    log = _trace(tmp_path / "bc.log", kernels.BC.gem5_storage_marker)
    assert dx100_coverage.labels_version(kernels.BC) == dx100_coverage.LABELS_V2
    assert dx100_coverage.labels_version(kernels.BFS) is None            # BFS records are unchanged
    new = dx100_coverage.observe(log, VALUES, 16, plugin=kernels.BC, label_version=dx100_coverage.LABELS_V2)
    assert "competing_parent_updates" not in new and new["competing_score_updates"]["count"] == 1
    assert new["competing_score_updates"]["score_storage"]["virtual_address"] == 0x4000
    assert "returned score array" in new["competing_score_updates"]["definition"]
    assert new["address_space_contract"]["instruction_baseAddr"].endswith("returned score.data()")
    assert "parent" not in json.dumps(new)
    # a record without `coverage_labels` (every record before ticket 80) re-derives the labels it holds
    old = dx100_coverage.observe(log, VALUES, 16, plugin=kernels.BC)
    assert old["competing_parent_updates"]["parent_storage"]["virtual_address"] == 0x4000
    assert "returned parent array" in old["competing_parent_updates"]["definition"]
    bfs = dx100_coverage.observe(_trace(tmp_path / "bfs.log", kernels.BFS.gem5_storage_marker), VALUES, 16)
    assert bfs == old                              # BFS output is exactly the legacy shape
    with pytest.raises(Exception, match="unknown coverage label version"):
        dx100_coverage.labels(kernels.BC, "swdb.dx100.coverage-labels.v9")


def test_a_committed_bc_record_still_matches_the_legacy_labels():
    """The committed BC timed record has no `coverage_labels` and keeps the BFS labels it was written with."""
    record = yaml.safe_load((REPO / "records/evaluations/bc-gem5-20261003-a1.timed-r1.candidate.evaluation.yaml")
                            .read_text())
    assert "coverage_labels" not in record["context"]
    coverage = record["correctness"]["checks"][0]["coverage"]
    names = dx100_coverage.labels(kernels.BC, record["context"].get("coverage_labels"))
    assert names["case"] in coverage and names["storage"] in coverage[names["case"]]
    assert record["correctness"]["checks"][0]["parent_gather_race"]["outcome"] == "inconclusive"   # stands as written


def test_new_bc_records_carry_no_parent_gather_race(tmp_path, monkeypatch):
    store = Store(tmp_path / "empty")
    store.add(Record("workload.yaml", {"kind": "workload", "id": "bc-graph", "definition": {"sources": [0]}}))
    monkeypatch.setattr(bfs_protocol, "materialize_workload",
                        lambda store, wid: {"graph": {"adjacency": [[1, 2], [3, 4], [3], [4], [5], []]}})
    log = tmp_path / "run.stdout"
    log.write_text("Starting PBFS: 1 elements\nStarting PBFS: 2 elements\nStarting PBFS: 2 elements\n"
                   "Starting PBFS: 1 elements\n")
    new = checks.observe_output(log, store, "bc-graph", 0, kernels.BC, race=kernels.BC.race_companion)
    assert set(new) == {"frontier_sizes"} and new["frontier_sizes"]["state"] == "passed"
    legacy = checks.observe_output(log, store, "bc-graph", 0, kernels.BC)
    assert legacy["parent_gather_race"]["outcome"] == "inconclusive"            # what old records hold
    assert legacy["frontier_sizes"] == new["frontier_sizes"]
    assert kernels.BFS.race_companion is True
