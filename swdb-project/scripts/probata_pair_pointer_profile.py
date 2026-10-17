"""2026-10-16 ET. Mixed pair control/eight-record actual profile.

Prospective entry only. Root must admit exact source/runtime, one worker and
the external 8 GiB whole-process-tree time/RSS guard before executing it.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("controls", "actual"), required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seconds", required=True, type=int)
    args = parser.parse_args()
    if not 60 <= args.seconds <= 21600:
        parser.error("seconds must be in 60..21600")
    project = Path(__file__).resolve().parents[1]
    checkout = project.parent
    out = args.output.resolve()
    if out == checkout or out.is_relative_to(checkout):
        parser.error("output must be outside the full source checkout")
    out.mkdir(parents=True, exist_ok=False)
    names = ("scripts/probata_pair_pointer_profile.py", "tests/test_pair_pointer_workflow.py",
             "tests/fixtures/proof/lowering/pair_pointer.cc", "tests/test_pair_workflow.py", "tests/testkit/pair_workflow.py",
             "tests/testkit/dx100_selector.py", "swdb/std_models.py", "swdb/c_lowering.py",
             "swdb/bounded_std_initialization.py", "swdb/bounded_initialization.py",
             "swdb/cbmc_adapter.py", "swdb/cbmc_translator.py", "swdb/wp_adapter.py",
             "swdb/proof_setup.py", "library/methods/probata-draft-1.yaml",
             "tests/fixtures/proof/methods/contract-fixture-1.yaml")
    def pins():
        return {name: hashlib.sha256((project/name).read_bytes()).hexdigest() for name in names}
    before = pins()
    selected = "tests/test_pair_pointer_workflow.py"
    if args.mode == "actual":
        selected += "::test_actual_mixed_pair_bodies_callers_and_bounded_cpp_replay"
    command = [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", selected,
               "--basetemp="+str(out/"pytest"), "--junitxml="+str(out/"junit.xml")]
    (out/"profile.json").write_text(json.dumps({"created": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode, "command": command, "source_pins": before, "whole_seconds": args.seconds,
        "external_rss_cap_bytes": 8589934592, "workers": 1,
        "expected_actual_records": 8 if args.mode == "actual" else 0,
        "scope": "Original mixed int/pointer pair models; local pointer identity, no dereference or pointer escape; contract_fixture only"}, indent=2)+"\n")
    started = time.monotonic()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
           "SWDB_VERIFIER_RSS_CAP_BYTES": "8589934592",
           "SWDB_MIXED_PAIR_ACTUAL": "1" if args.mode == "actual" else "0",
           "SWDB_PAIR_DEADLINE_MONOTONIC": str(started+args.seconds)}
    if args.mode == "controls":
        env.update(SWDB_FRAMA_C="none", SWDB_CBMC="none")
    with (out/"pytest.log").open("x") as log:
        done = subprocess.run(command, cwd=project, env=env, stdout=log, stderr=subprocess.STDOUT)
    elapsed = time.monotonic()-started
    unchanged = pins() == before
    (out/"result.json").write_text(json.dumps({"pytest_exit_code": done.returncode,
        "elapsed_seconds": elapsed, "within_budget": elapsed <= args.seconds,
        "source_unchanged": unchanged, "acceptance": "requires exact actual artifacts and independent cold audit"}, indent=2)+"\n")
    return done.returncode if unchanged and elapsed <= args.seconds else 124


if __name__ == "__main__":
    raise SystemExit(main())
