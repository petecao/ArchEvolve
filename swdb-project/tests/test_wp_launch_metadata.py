"""Public WP invocation metadata, including source-gate refusal; 2026-10-15 ET."""
import pytest

from test_closed_owner_data import SOURCE
from test_closed_owner_members import _record
from test_vector_ownership_wp import _ownership_seed
from test_wp_adapter import fake, needs_wp


@needs_wp
@pytest.mark.parametrize("shadow", [False, True], ids=["launched", "prelaunch_refusal"])
def test_wp_launch_metadata_matches_the_public_execution_boundary(tmp_path, shadow):
    seed = _ownership_seed(tmp_path, source=SOURCE, cases=[("data_safe", 7)])
    if shadow:
        (tmp_path / "library/proof_units/vector").write_text(
            "#include_next <vector>\n#include <cstdlib>\n"
            "void *operator new(std::size_t n) {return std::malloc(n);}\n")
    record = _record(seed, "--summary", "contract.fixture_vector_owner_data_safe",
        env=fake("unknown", SWDB_VERIFIER_LOCK=str(tmp_path / "standin.lock")))
    settings = record["settings"]
    reports = {row["name"] for row in record["evidence"]["reports"]}
    if shadow:
        assert record["failure_class"] == "unsupported_construct", record
        assert settings["verifier_launched"] is False
        assert settings["flags"] == [] and "wp_log" not in reports
    else:
        assert record["failure_class"] == "unknown", record
        assert settings["flags"] and "wp_log" in reports
        assert settings["verifier_launched"] is True
