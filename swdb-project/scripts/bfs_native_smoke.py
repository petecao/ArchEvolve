#!/usr/bin/env python3
"""Run the public DX100-scalar native diagnostic workflow inside an owned lane.

Created: 2026-09-25 (Eastern Time). No profitability assessment or speedup claim.
"""

import argparse
import difflib
import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--runs-dir", type=Path, required=True)
    parser.add_argument("--records", type=Path, default=Path("records"))
    parser.add_argument("--lane", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    args.runs_dir = args.runs_dir.resolve()
    folder = args.runs_dir / (args.id + ".driver")
    folder.mkdir(parents=True, exist_ok=False)
    def call(command, *rest):
        argv = [sys.executable, "-m", "swdb", command, *map(str, rest),
                "--records", str(args.records), "--format", "json"]
        result = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=600)
        (folder / f"{command}.stdout.json").write_text(result.stdout)
        (folder / f"{command}.stderr.txt").write_text(result.stderr)
        if result.returncode:
            print(f"{command} failed; retained {folder}", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            raise SystemExit(result.returncode)
        return json.loads(result.stdout)
    source = call("source-snapshot", "dx100-bfs-scalar", "--id", args.id + ".source", "--runs-dir", args.runs_dir)
    package = call("fixture-package", source["id"], "--id", args.id + ".package")
    path = "benchmarks/gapbs/src/bfs.cc"
    original = (Path(source["artifact"]["path"]) / path).read_text()
    # The scalar CAS already stores u. Remove only its immediately repeated store.
    old = "if (compare_and_swap(parent[v], curr_val, u)) {\n                        parent[v] = u;"
    new = "if (compare_and_swap(parent[v], curr_val, u)) {"
    if original.count(old) != 1:
        raise SystemExit("pinned scalar source did not match the expected supporting edit")
    changed = original.replace(old, new)
    patch = "".join(difflib.unified_diff(original.splitlines(keepends=True), changed.splitlines(keepends=True),
                                       fromfile="a/"+path, tofile="b/"+path))
    proposal = {"message_version": "1.0", "id": args.id + ".proposal",
                "producer": {"name": "swdb-native-diagnostic-client", "role": "sw", "test_client": True},
                "profile_package": package["id"], "source_snapshot": source["id"],
                "implementation": "dx100-bfs-scalar", "source_sha256": source["artifact"]["sha256"],
                "regions": [r["id"] for r in source["regions"]],
                "intent": "Remove the redundant non-atomic parent store immediately after successful scalar CAS; preserve BFS semantics.",
                "constraints": {"editable_files": [path], "preserve_correctness": True, "preserve_roi": True},
                "payload": {"kind": "patch", "content": patch}, "required_operations": []}
    proposal_file = folder / "proposal.json"
    proposal_file.write_text(json.dumps(proposal, indent=2))
    submitted = call("submit", proposal_file, "--runs-dir", args.runs_dir)
    request = {"message_version": "1.0", "id": args.id + ".evaluation", "candidate": submitted["candidate"],
               "machine": "mbit10", "threads": 1, "sources": [0, 3, 8], "repetitions": 1,
               "roi": "bfs.complete_call.v1", "budget": {"build_seconds": 180, "run_seconds": 30, "total_seconds": 300},
               "comparison_baseline": "dx100-bfs-scalar",
               "workload": {"id": args.id + ".graph", "family": "diagnostic",
                            "generator": {"name": "explicit-small-correctness-case", "version": "1.0"},
                            "graph": {"num_vertices": 10, "directed": True,
                                      "edges": [[0,1],[0,2],[1,3],[2,3],[3,4],[4,5],[5,3],[6,7]]}}}
    request_file = folder / "evaluation.json"
    request_file.write_text(json.dumps(request, indent=2))
    evaluation = call("evaluate", request_file, "--runs-dir", args.runs_dir, "--lane", args.lane)
    chain = call("get", evaluation["id"], "--chain")
    if evaluation["correctness"]["state"] != "passed" or len(evaluation["timing"]) != 3 or evaluation["gain_claim"]:
        raise SystemExit("native diagnostic acceptance did not produce three checked timed results")
    print(json.dumps({"evaluation": evaluation["id"], "outcome": evaluation["outcome"],
                      "correctness": evaluation["correctness"]["state"], "trials": len(evaluation["timing"]),
                      "profiling": evaluation["profiling"], "gain_claim": False,
                      "records_retrieved": len(chain["records"]), "raw": str(folder)}, indent=2))


if __name__ == "__main__":
    main()
