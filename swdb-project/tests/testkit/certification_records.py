"""Real certification record closure; unrelated bulk estimates are not fixture inputs.

The normal library validator, source materializer, compilers, evaluators and
negative controls run unchanged. Full-catalog state/history tests opt out.
Created: 2026-10-08 ET.
"""

import shutil
from pathlib import Path

import pytest

from swdb import certification, kernels
from swdb.library import Library
from swdb.store import Store
from testkit.record_subset import copy_record_subset

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def certification_record_template(tmp_path_factory):
    records = tmp_path_factory.mktemp("certification-record-template") / "records"
    roots = {certification.DEFAULT_SNAPSHOT, kernels.BC.certification_snapshot}
    # certify validates every normative entry, not just the selected contract.
    # Use the current original record references; absent roots fail closed.
    catalog = Library(ROOT / "library")
    for entry_id in ("contract.bfs_read_offload", "contract.bfs_tdstep_frontier_staging",
                     "contract.bc_read_offload"):
        if catalog.get(entry_id) is None:
            raise ValueError(f"missing certification fixture contract: {entry_id}")
    for entry in catalog.entries.values():
        if entry.get("intrinsic_record"):
            roots.add(entry["intrinsic_record"])
        roots.update(entry.get("hardware_operations", []))
        roots.update(entry.get("strategies", []))
    copy_record_subset(ROOT / "records", records, sorted(roots))
    return records


@pytest.fixture
def certification_store(certification_record_template, tmp_path_factory):
    # A fresh Store and directory isolate any in-memory or writer mutations.
    # Keep them outside a test's tmp_path so no-build assertions stay meaningful.
    records = tmp_path_factory.mktemp("certification-records") / "records"
    shutil.copytree(certification_record_template, records)
    return Store(records)
