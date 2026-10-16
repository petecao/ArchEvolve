"""Pair-only ticket25 profile entry; created 2026-10-15 ET.

The coordinator supplies the socket/verifier admission, one-worker 8 GiB RSS
watchdog and wall timeout. This entry is not an admission or a resource guard.
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
    parser.add_argument("--mode", choices=("controls", "actual-wp"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=7200,
                        help="prospective wall budget; external watchdog must enforce this total")
    args = parser.parse_args()
    if not 1 <= args.seconds <= 21600:
        parser.error("seconds must be in 1..21600")
    project = Path(__file__).resolve().parents[1]
    checkout = project.parent
    output = args.output.resolve()
    if output == checkout or checkout in output.parents:
        parser.error("output must be outside the source checkout")
    output.mkdir(parents=True, exist_ok=False)
    names = ("scripts/probata_pair_profile.py", "tests/test_pair_workflow.py",
             "tests/fixtures/proof/lowering/pair_only.cc", "swdb/bounded_std_initialization.py",
             "swdb/bounded_initialization.py", "swdb/std_models.py", "swdb/c_lowering.py", "swdb/wp_adapter.py",
             "swdb/proof_setup.py", "library/methods/probata-draft-1.yaml",
             "tests/fixtures/proof/methods/contract-fixture-1.yaml")
    pins = {name: hashlib.sha256((project / name).read_bytes()).hexdigest() for name in names}
    selection = "tests/test_pair_workflow.py"
    if args.mode == "actual-wp":
        selection += "::test_actual_four_pair_bodies_then_unchanged_caller_pin_current_proof_dependencies"
    command = [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", selection,
               "--basetemp=" + str(output / "pytest"), "--junitxml=" + str(output / "junit.xml")]
    manifest = {"created": datetime.now(timezone.utc).isoformat(), "mode": args.mode,
                "source_sha256": pins, "command": command, "prospective_wall_seconds": args.seconds,
                "required_external_rss_cap_bytes": 8589934592,
                "actual_expected_records": 6 if args.mode == "actual-wp" else 0,
                "scope": "four original int/int pair bodies, safe caller and wrong-field negative; contract_fixture"}
    (output / "profile.json").write_text(json.dumps(manifest, indent=2) + "\n")
    started = time.monotonic()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
           "SWDB_VERIFIER_RSS_CAP_BYTES": "8589934592",
           "SWDB_PAIR_ACTUAL": "1" if args.mode == "actual-wp" else "0",
           "SWDB_PAIR_DEADLINE_MONOTONIC": str(started + args.seconds)}
    if args.mode == "controls":
        env.update(SWDB_FRAMA_C="none", SWDB_CBMC="none")
    with (output / "pytest.log").open("w") as log:
        done = subprocess.run(command, cwd=project, env=env, stdout=log, stderr=subprocess.STDOUT)
    after = {name: hashlib.sha256((project / name).read_bytes()).hexdigest() for name in names}
    elapsed = time.monotonic() - started
    result = {"pytest_exit_code": done.returncode, "source_unchanged": after == pins,
              "elapsed_seconds": elapsed, "within_prospective_wall_budget": elapsed <= args.seconds,
              "actual_proof_claim": "requires retained records and independent cold audit"}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    if elapsed > args.seconds:
        return 124
    return done.returncode if after == pins else 2


if __name__ == "__main__":
    raise SystemExit(main())
