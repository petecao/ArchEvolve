"""2026-10-16 ET. Public smoke-observation policy; report fixtures only."""
import pytest

from test_proof_report_closure import reports


def smoke_reports(tmp_path, observations, native_verdict="unknown", native_mutation=None):
    def inventory(data):
        data["goals"][1]["results"] = observations
    def native(rows):
        rows[1]["verdict"] = native_verdict
        if native_mutation:
            native_mutation(rows)
    return reports(tmp_path, inventory, native)


@pytest.mark.parametrize("observations", [
    [], ["untried"], ["failed"], ["valid"], ["unknown", "failed"],
    ["unknown", "untried"], ["unknown", "valid"], ["computing"],
    ["unexpected"], "unknown", None,
])
def test_vacuous_unhealthy_or_contradictory_smoke_observations_cannot_prove(tmp_path, observations):
    result = smoke_reports(tmp_path, observations)
    assert result["verdict"] == "not_proven"


@pytest.mark.parametrize("verdict", ["none", "untried", "failed", "valid", "timeout", "invalid", None])
def test_native_smoke_verdict_must_match_a_healthy_inventory_observation(tmp_path, verdict):
    result = smoke_reports(tmp_path, ["unknown"], verdict)
    assert result["verdict"] == "not_proven"


@pytest.mark.parametrize("mutation", [
    lambda rows: rows[1].update(property="unrelated-property"),
    lambda rows: rows[1].update(smoke=False),
    lambda rows: rows[1].update(passed=False),
])
def test_native_smoke_identity_and_flags_must_match(tmp_path, mutation):
    assert smoke_reports(tmp_path, ["unknown"], native_mutation=mutation)["verdict"] == "not_proven"


@pytest.mark.parametrize("verdict", ["unknown", "timeout", "stepout", "invalid"])
def test_nonempty_healthy_smoke_observation_is_retained_without_a_sat_claim(tmp_path, verdict):
    result = smoke_reports(tmp_path, [verdict], verdict)
    assert result["verdict"] == "proven"  # ordinary fixture proof; no consistency theorem


def test_healthy_inventory_smoke_can_be_read_when_native_omits_the_goal(tmp_path):
    result = smoke_reports(tmp_path, ["unknown"], native_mutation=lambda rows: rows.pop())
    assert result["verdict"] == "proven"  # independent complete inventory is mandatory


def test_healthy_smoke_results_do_not_override_a_failed_raw_pass_flag(tmp_path):
    result = reports(tmp_path, lambda d: d["goals"][1].update(results=["unknown"], passed=False),
                     lambda rows: rows[1].update(verdict="unknown", passed=False))
    assert result["verdict"] == "not_proven"


@pytest.mark.parametrize("flag", [1, "true", None])
def test_malformed_smoke_pass_flag_cannot_bypass_observation_check(tmp_path, flag):
    result = reports(tmp_path, lambda d: d["goals"][1].update(results=[], passed=flag),
                     lambda rows: rows[1].update(verdict="unknown", passed=flag))
    assert result["verdict"] == "not_proven"
