"""Agreement of the summary forms through `swdb summary-agreement` (Probata proof of concept ticket 23).

Created: 2026-10-14 ET. Design: formal-verification map spec ("Verifier lineup and order": one summary source;
"DX100 proof semantics": the forms agree); map 12 item 8. Format: docs/reference/format-v0.4-stubs-check-mode.md.

Fixture scenarios from ticket 22's seed (tests/test_cbmc_adapter.py): callers of the add_one summary and map 07's
smoke pair. The C-stub form runs CBMC 6.11, the ACSL form Frama-C/WP 33.0 (both real; the cases skip without
them). Run inside the machine-wide verifier lock.
"""

import json
import shutil

import pytest
import yaml

from conftest import run_swdb
from test_cbmc_adapter import (QUIET, ADD_ONE, CALL_INC, CALL_KEEP, CALL_OUTSIDE, SMOKE, Seed, build_cbmc_seed, needs_cbmc)


def _wp_present():
    from swdb import framac
    return not framac.locate().missing


needs_wp = pytest.mark.skipif(not _wp_present(), reason="Frama-C/WP 33.0 is missing")
WITH_WP = {"SWDB_FRAMA_C": ""}                    # the real Frama-C (the seed's other commands switch it off)
CALLER = {"threads": 1, "n": 3}


@pytest.fixture(scope="module")
def agreement_seed(tmp_path_factory):
    path = tmp_path_factory.mktemp("agreement-seed")
    return path, build_cbmc_seed(path)


@pytest.fixture
def seed(agreement_seed, tmp_path):
    source, candidates = agreement_seed
    for name in ("records", "library"):
        shutil.copytree(source / name, tmp_path / name)
    seed = Seed(tmp_path, candidates)
    summary = seed.prove_summary(ADD_ONE, bounds={"threads": 1, "n": 3})
    assert seed.read(summary)["verdict"] == "proven"
    return seed


def scenarios(seed, only=None):
    safe = seed.candidates["safe"]
    found = [
        {"name": "relies-on-the-postcondition", "function": "swdb_fixture_call_inc", "contract": CALL_INC,
         "bounds": CALLER, "expect": "safe"},
        {"name": "relies-outside-assigns", "function": "swdb_fixture_call_outside", "contract": CALL_OUTSIDE,
         "bounds": CALLER, "expect": "safe"},
        {"name": "expects-inside-assigns-kept", "function": "swdb_fixture_call_keep", "contract": CALL_KEEP,
         "bounds": CALLER, "expect": "buggy"},
        {"name": "smoke-buggy", "function": "smoke_main", "contract": SMOKE, "bounds": {"threads": 1},
         "expect": "buggy", "defines": ["BUGGY"]}]
    found = [s for s in found if only is None or s["name"] in only]
    for scenario in found:
        scenario["candidate"] = safe
    path = seed.root / "scenarios.yaml"
    path.write_text(yaml.safe_dump(found, sort_keys=False))
    return path


def agreement(seed, env=None, ok=True, only=None):
    result = run_swdb("summary-agreement", "--records", seed.records, "--scenarios", scenarios(seed, only),
                      "--runs-dir", seed.runs, "--format", "json", env={**QUIET, **WITH_WP, **(env or {})},
                      timeout=3600)                  # WP jobs that cannot prove run to their solver timeouts
    assert (result.returncode == 0) is ok, result.stderr + result.stdout
    return json.loads(result.stdout) if ok else result


@needs_cbmc
@needs_wp
def test_the_c_stub_and_acsl_forms_agree_on_every_fixture_scenario(seed):
    report = agreement(seed)
    assert report["agree"] is True and report["forms"] == ["c_stub", "acsl"]
    verdicts = {s["name"]: (s["forms"]["c_stub"]["verdict"], s["forms"]["acsl"]["verdict"]) for s in report["scenarios"]}
    assert verdicts["relies-on-the-postcondition"] == ("proven", "proven")
    assert verdicts["expects-inside-assigns-kept"][0] == "refuted" and verdicts["expects-inside-assigns-kept"][1] != "proven"
    assert verdicts["smoke-buggy"][0] == "refuted" and verdicts["smoke-buggy"][1] != "proven"
    assert not list((seed.records / "proofs").glob("agreement*"))          # a check: no proof record written


@needs_cbmc
@needs_wp
def test_a_hand_weakened_c_stub_makes_the_agreement_check_fail_and_name_the_scenario(seed):
    fault = seed.root / "stub-fault.yaml"
    fault.write_text(yaml.safe_dump({"drop": [f"{ADD_ONE}#add_one_post.ensures1"]}))   # the postcondition dropped
    result = agreement(seed, env={"SWDB_CBMC_STUB_FAULT": str(fault)}, ok=False,
                       only={"relies-on-the-postcondition", "relies-outside-assigns"})
    assert "disagree" in result.stderr and "relies-on-the-postcondition" in result.stderr
