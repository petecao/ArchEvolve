#!/usr/bin/env python3
"""Recheck a3 and retain the two T17 v2 comparisons (2026-09-29 ET).

Run on mbit10, where the sealed raw observations, binaries and source artifacts live.
The protocol was already frozen on 2026-09-28; this operation never changes it.
"""

import argparse
import json
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swdb import artifacts, bfs_protocol
from swdb.cli import Failure
from swdb.profile import _verified_lane
from swdb.store import Store

PROTOCOL = "bfs-t17-controlled-simulator-20260928.952dead4468b86d7"
CLOSURE = ROOT / ".scratch/bfs-rewrite-evaluation-2026-09-25/observations/t17-t20-routes-a3-closure-20260929.json"
CLAIM = (
    "Strategy existing-dx100-top-down-offload reuses the DX100 authors' TDStepMAA path "
    "with the wait_ready(tile5) correctness fix. These are simulated joint hardware/software "
    "comparisons against scalar TDStep, restricted to source vertex 0, one repetition per "
    "graph family under declared deterministic replay; they do not establish a new "
    "accelerator algorithm discovered by a rewrite provider or general-source coverage.")


def require(condition, reason):
    if not condition:
        raise Failure(reason)


def record(store, identifier, kind):
    value = store.get(identifier, kind)
    require(value is not None, f"missing {kind} {identifier}; sync actual a3 metadata first")
    return value


def companion(store, closure, frozen):
    observation = closure["ac10_companions"]["t17"]
    require(observation.get("passed") is True and observation.get("correctness") == "passed"
            and observation.get("parent_storage_attributed") is True
            and observation.get("competing_parent_updates", {}).get("state") == "observed"
            and observation["competing_parent_updates"].get("count", 0) > 0,
            "a3 closure lacks the T17 competing-parent companion acceptance")
    # The closure names the run stem; the public dx100-execute record appends
    # .execute. Its exact retained digest, rather than the spelling, is binding.
    actual_id = observation["id"] if store.get(observation["id"], "evaluation") else observation["id"] + ".execute"
    actual = record(store, actual_id, "evaluation")
    require(artifacts.digest(actual) == observation["record_sha256"], "T17 companion record differs from a3 closure")
    require(actual["outcome"]["state"] == "complete" and actual["correctness"]["state"] == "passed"
            and actual["candidate"] == frozen["settings"]["route"]["candidate"]
            and actual["build"]["binary_sha256"] == observation["timed_binary_sha256"],
            "T17 companion is not the completed exact timed candidate")
    binary = Path(actual["build"]["binary"])
    require(artifacts.file_hash(binary) == observation["timed_binary_sha256"], "T17 companion/timed binary changed")
    checks = actual["correctness"].get("checks", [])
    require(len(checks) == 1 and checks[0].get("passed") is True and checks[0].get("source") == 0,
            "T17 companion lacks its source-0 structural check")
    coverage = checks[0].get("coverage", {})
    require(coverage.get("competing_parent_updates", {}).get("state") == "observed"
            and coverage["competing_parent_updates"].get("count") == observation["competing_parent_updates"]["count"]
            and coverage["competing_parent_updates"].get("parent_storage"),
            "T17 companion competing-parent observation differs from retained closure")
    # Public comparisons will independently reread primary and diagnostic raw
    # observations. Recheck the companion with the same v2 parser before claims.
    bfs_protocol._check_verifier_identity(actual, store)
    from swdb.dx100_witness import validate_completed_witness
    validate_completed_witness(actual, verify_artifacts=True)
    return {"evaluation": actual["id"], "sha256": artifacts.digest(actual),
            "binary_sha256": observation["timed_binary_sha256"],
            "competing_parent_updates": observation["competing_parent_updates"]["count"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, default=ROOT / "records")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--lane", required=True)
    args = parser.parse_args()
    require(socket.gethostname().split(".")[0] == "mbit10", "T17 raw recheck must run on mbit10")
    store = Store(args.records)
    lane = _verified_lane(record(store, "mbit10", "machine"), args.lane)
    output = artifacts.external_directory(args.output_dir)
    frozen = record(store, PROTOCOL, "protocol")
    require(frozen.get("state") == "frozen" and bfs_protocol.verify_immutable(frozen) == frozen["identity_sha256"],
            "T17 v2 is not the existing immutable freeze")
    require(frozen["version"] == 2 and frozen["settings"]["sampling"]["repetitions"] == 1
            and frozen["settings"]["sampling"]["determinism"]["basis"] == "deterministic_simulator_replay.v1",
            "T17 v2 sampling differs")
    closure = json.loads(CLOSURE.read_text())
    candidate = record(store, frozen["settings"]["route"]["candidate"], "candidate")
    source = artifacts.verify(candidate["artifact"])
    code = (source / "benchmarks/gapbs/src/bfs.cc").read_text()
    scalar = code[code.index("pvector<NodeID> DOBFS("):code.index("pvector<NodeID> DOBFSMAA(")]
    require("TDStepMAA(g, VertexOffsetsOut, parent, queue, num_nodes, num_edges);" in scalar
            and "wait_ready(tile5);" in code, "T17 source does not retain the documented author-path reuse and fix")
    ac10 = companion(store, closure, frozen)
    results = []
    for family in ("uniform18", "kronecker18"):
        group = closure["groups"]["t17." + family]
        require(group["driver_state"] == "complete", "T17 a3 family driver is incomplete")
        selected = {}
        packages = {}
        for role in ("baseline", "candidate"):
            prefix = f"bfs-t17-routes-20260928-a3.{role}.{family}"
            selected[role] = record(store, prefix + ".aggregate", "evaluation")
            closure_row = [r for r in group["series"] if r["id"] == prefix]
            require(len(closure_row) == 1 and closure_row[0]["state"] == "complete"
                    and len(closure_row[0]["complete_pairs"]) == 1
                    and closure_row[0]["complete_pairs"][0][:2] == [0, 0], "T17 a3 grid differs from source-0/repetition-0 closure")
            timing = selected[role].get("timing", [])
            require(len(timing) == 1 and timing[0]["source"] == 0
                    and timing[0]["duration_s"] == closure_row[0]["complete_pairs"][0][2],
                    "T17 aggregate sample differs from a3 closure")
            for binding in selected[role]["component_evaluations"]:
                primary = record(store, binding["evaluation"], "evaluation")
                matches = [r.data for r in store.of_kind("profile_package") if r.data.get("evaluation") == primary["id"]
                           and r.data.get("completeness") == "complete"]
                require(len(matches) == 1, "T17 primary lacks exactly one sealed complete diagnostic package")
                packages[primary["id"]] = matches[0]["id"]
        request = {"message_version": "1.0", "id": f"bfs-t17-handoff-20260929-a1.{family}",
            "protocol": PROTOCOL, "comparison_baseline": "dx100-bfs-scalar",
            "baseline_evaluation": selected["baseline"]["id"],
            "candidate_evaluation": selected["candidate"]["id"], "region_packages": packages,
            "claim_scope": CLAIM, "companion_acceptance": ac10}
        request_path = output / (family + ".request.json")
        request_path.write_text(json.dumps(request, indent=2) + "\n")
        existing = store.get(request["id"], "comparison_result")
        if existing:
            require(existing["request"] == request, "existing comparison has a different immutable request")
            result = existing
        else:
            process = subprocess.run([sys.executable, "-B", "-m", "swdb", "compare-evaluations", str(request_path),
                                      "--records", str(args.records), "--format", "json"],
                                     cwd=ROOT, capture_output=True, text=True, timeout=7200)
            (output / (family + ".stdout.json")).write_text(process.stdout)
            (output / (family + ".stderr.txt")).write_text(process.stderr)
            require(process.returncode == 0, "compare-evaluations failed; raw command logs retained")
            result = json.loads(process.stdout)
        results.append({"family": family, "comparison": result["id"], "decision": result["decision"],
                        "gain_claim": result["gain_claim"], "metrics": result["metrics"]})
    summary = {"created": "2026-09-29", "protocol": PROTOCOL, "protocol_sha256": frozen["identity_sha256"],
               "already_frozen_at": frozen["frozen_at"], "lane": lane, "claim_scope": CLAIM,
               "companion": ac10, "comparisons": results}
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    require(all(r["decision"]["state"] != "rejected" for r in results), "T17 comparison rejected; retained outcomes require review")


if __name__ == "__main__":
    main()
