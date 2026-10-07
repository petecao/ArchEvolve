"""Blind campaign pairing through public fixture campaigns; all fixture numbers are synthetic."""
import json

from conftest import run_swdb
from testkit.extensa import campaign_file, campaign_store, fixture_file, provider, records_of, run


def test_fixture_freezes_each_artifact_input_before_pilot_and_comparison(campaign_team):
    summary = run(campaign_team, campaign_file(campaign_team), fixture_file(campaign_team),
                  provider(campaign_team, {}))
    pairing = summary["paired_estimates"]
    records = records_of(campaign_store(campaign_team), "paired_estimates")
    assert records and pairing["records"] and pairing["outcome_accesses"]
    by_id = {r["id"]: r for r in records}
    assert all(r["mode"] == "extensa" and r["campaign"] == summary["campaign"] for r in records)
    assert any("pilot" in e["stage"] for e in pairing["outcome_accesses"])
    assert any("comparison" in e["stage"] for e in pairing["outcome_accesses"])
    for event in pairing["outcome_accesses"]:
        for rid in event["paired_estimates"]:
            assert by_id[rid]["estimated_at"] < event["outcome_access_started_at"]
            assert not by_id[rid]["eligible_for_agreement"]
    result = run_swdb("validate", "--records", campaign_store(campaign_team))
    assert result.returncode == 0, result.stderr
