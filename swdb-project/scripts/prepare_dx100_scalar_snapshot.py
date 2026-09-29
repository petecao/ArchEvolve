#!/usr/bin/env python3
"""Materialize and register the DX100 scalar-only rewrite source (2026-09-29 ET).

The full DX100 source remains byte-for-byte unchanged. Outputs belong outside Git;
--check is a native correctness smoke on mbit10 inside an owned socket lane.
"""

import argparse
import copy
import hashlib
import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from swdb import artifacts, workflow, yamlio
from swdb.cli import Failure
from swdb.profile import _verified_lane
from swdb.store import Store

BFS = "benchmarks/gapbs/src/bfs.cc"
PIN = "6835fc42dfadcb60c1c3fae543f736903977f135fd7c55cd495c0e481b572465"
ID = "bfs-dx100-scalar-only-20260929-a1.source"


def scalar_source(original):
    # These exact ranges are tied to the pinned source, not a C++ heuristic.
    if hashlib.sha256(original.encode()).hexdigest() != PIN:
        raise Failure("DX100 bfs.cc differs from the pinned e4fc4af source")
    lines = original.splitlines(keepends=True)
    removed = set(range(63, 226)) | set(range(366, 444))
    result = "".join(line for number, line in enumerate(lines, 1) if number not in removed)
    selection = """#ifdef MAA
        return DOBFSMAA(g, sp.PickNext(), cli.logging_en());
#else
        return DOBFS(g, sp.PickNext(), cli.logging_en());
#endif"""
    if result.count(selection) != 1:
        raise Failure("pinned DX100 main selection differs")
    result = result.replace(selection, "        return DOBFS(g, sp.PickNext(), cli.logging_en());")
    if re.search(r"\b(?:TDStepMAA|DOBFSMAA|tiles[0-9ij]|regs[0-9]|last_[ij]_regs)\b", result):
        raise Failure("scalar-only source retains accelerator implementation material")
    return result


def materialize(folder, records):
    full = ROOT / "apps/dx100"
    before = artifacts.identify(full)
    original = (full / BFS).read_text()
    source = folder / "source"
    source.mkdir(parents=True, exist_ok=False)
    # Keep the BFS translation unit and build headers only. Other benchmark
    # translation units and API examples contain additional answer keys.
    keep = ["LICENSE", "benchmarks/gapbs/LICENSE"]
    keep += [p.relative_to(full).as_posix() for p in (full / "benchmarks/gapbs/src").glob("*.h")]
    keep += [p.relative_to(full).as_posix() for p in (full / "benchmarks/API").glob("*.hpp")]
    keep += [p.relative_to(full).as_posix() for p in (full / "include").rglob("*.h")]
    for relative in sorted(keep):
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(full / relative, target)
    (source / BFS).write_text(scalar_source(original))
    (source / "PROVENANCE.md").write_text(
        "# DX100 scalar-only rewrite source\n\nDate: 2026-09-29 ET\n\n"
        "Derived from DX100 e4fc4afdf894f295442cef3604667a469fab8e62. "
        "The accelerator BFS functions, their tile/register arrays, and the MAA main selection "
        "were removed under ADR 0006 to keep the authors' accelerator answer key out of "
        "from-scratch rewrite workspaces. Only the BFS translation unit, required build headers "
        "and licenses remain. The scalar TDStep, DOBFS, BFSVerifier, and FUNC API setup are "
        "preserved. API headers are operation definitions, not an accelerated BFS implementation. "
        "The full source snapshot remains available for author-code reuse strategies.\n")
    store = Store(records)
    context = copy.deepcopy(store.source_context(store.get("dx100-bfs-scalar", "implementation")))
    text = (source / BFS).read_text()
    file_hash = artifacts.file_hash(source / BFS)
    context["code"] = [{"root": "application", "path": BFS, "sha256": file_hash}]
    # Relocate the unchanged evaluator range after removal of the answer key.
    verifier_text = "".join(original.splitlines(keepends=True)[457:509])
    if text.count(verifier_text) != 1:
        raise Failure("scalar derivation changed the BFS correctness check")
    start = text[:text.index(verifier_text)].count("\n") + 1
    context["evaluator"]["verifier"]["code"] = {
        "root": "application", "path": BFS, "sha256": file_hash,
        "lines": [start, start + len(verifier_text.splitlines()) - 1]}
    context["source_derivation"] = {
        "date": "2026-09-29", "decision": "docs/adr/0006-rewrite-providers-work-in-a-guarded-workspace.md",
        "upstream_bfs_sha256": PIN,
        "removed_functions": ["TDStepMAA", "DOBFSMAA"],
        "removed_pinned_line_ranges": [[63, 225], [366, 443]],
        "removed_main_selection": "MAA branch calling DOBFSMAA",
        "excluded_material": "Other benchmark translation units, API examples/scripts, and old manifests.",
        "purpose": "From-scratch proposals cannot read the authors' accelerator BFS answer key.",
        "full_snapshot": "bfs-dx100-compile-20260925-a1.source",
        "full_source_artifact_sha256": before["sha256"]}
    context["verification"] = {"status": "unchecked", "evidence": [],
        "scope": "Derived scalar source; native correctness smoke is recorded separately, no performance claim."}
    region = {"id": f"{BFS}:1-{len(text.splitlines())}:{file_hash[:16]}", "path": BFS,
              "lines": [1, len(text.splitlines())], "source_sha256": file_hash,
              "text": text, "association": "declared_source_region"}
    data = workflow.record("source_snapshot", ID, implementation="dx100-bfs-scalar",
        application="dx100-gapbs", revision=context["source"]["commit"],
        artifact=artifacts.identify(source), context=context, regions=[region],
        protections=artifacts.protections(source, context))
    data["provenance"][0]["description"] = (
        "Scalar-only derivative registered by prepare_dx100_scalar_snapshot.py on 2026-09-29; "
        "removed author accelerator BFS code under ADR 0006; full snapshot retained unchanged.")
    if artifacts.identify(full) != before:
        raise Failure("full source changed during scalar-only materialization")
    return data


def check(data, folder, records, lane):
    if socket.gethostname().split(".")[0] != "mbit10":
        raise Failure("native scalar snapshot correctness smoke must run on mbit10")
    machine = Store(records).get("mbit10", "machine")
    verified = _verified_lane(machine, lane)
    source = Path(data["artifact"]["path"])
    binary = folder / "bfs.scalar"
    flags = shlex.split(data["context"]["build"]["flags"])
    command = ["g++", *flags, "-I" + str(source / "benchmarks/API"),
               "-I" + str(source / "benchmarks/gapbs/src"), str(source / BFS), "-o", str(binary)]
    build = subprocess.run(command, capture_output=True, text=True, timeout=180)
    (folder / "build.stdout").write_text(build.stdout)
    (folder / "build.stderr").write_text(build.stderr)
    if build.returncode:
        raise Failure("scalar snapshot build failed; raw logs retained")
    trials = []
    environment = {**os.environ, "OMP_NUM_THREADS": "4", "OMP_DYNAMIC": "FALSE"}
    for graph in ("-g", "-u"):
        argv = [str(binary), graph, "10", "-k", "4", "-r", "0", "-n", "1", "-v"]
        run = subprocess.run(argv, capture_output=True, text=True, timeout=60, env=environment)
        name = "kronecker" if graph == "-g" else "uniform-random"
        (folder / (name + ".stdout")).write_text(run.stdout)
        (folder / (name + ".stderr")).write_text(run.stderr)
        passed = run.returncode == 0 and bool(re.search(r"Verification:\s+PASS", run.stdout))
        trials.append({"family": name, "argv": argv, "returncode": run.returncode, "passed": passed})
    receipt = {"created": "2026-09-29", "classification": "native_correctness_smoke",
               "snapshot": data["id"], "source_sha256": data["artifact"]["sha256"],
               "bfs_sha256": artifacts.file_hash(source / BFS), "binary_sha256": artifacts.file_hash(binary),
               "build_argv": command, "lane": verified, "host": "mbit10", "threads": 4,
               "trials": trials, "gain_claim": False}
    (folder / "correctness.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if not all(row["passed"] for row in trials):
        raise Failure("scalar snapshot BFS correctness smoke failed; receipt retained")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", required=True, type=Path)
    parser.add_argument("--records", type=Path, default=ROOT / "records")
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--lane")
    args = parser.parse_args()
    folder = artifacts.external_directory(args.runs_dir) / ID
    data = materialize(folder, args.records)
    request = folder / "source-record.yaml"
    request.write_text(yamlio.dumps(data))
    receipt = check(data, folder, args.records, args.lane) if args.check else None
    if args.register:
        subprocess.run([sys.executable, "-B", "-m", "swdb", "add", str(request),
                        "--records", str(args.records)], cwd=ROOT, check=True)
    print(json.dumps({"snapshot": data["id"], "artifact": data["artifact"]["path"],
                      "sha256": data["artifact"]["sha256"], "files": len(data["artifact"]["files"]),
                      "registered": args.register, "correctness": receipt,
                      "record_file": str(request)}, indent=2))


if __name__ == "__main__":
    main()
