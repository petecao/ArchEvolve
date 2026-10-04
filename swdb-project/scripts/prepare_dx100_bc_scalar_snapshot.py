#!/usr/bin/env python3
"""Materialize and register the DX100 scalar-only BC rewrite source (2026-10-03 ET).

Ticket 40. Mirrors prepare_dx100_scalar_snapshot.py (BFS): the full DX100 source
stays byte-for-byte unchanged; the derivation removes the authors' accelerated
BC code (PBFSMAA, BrandesMaa, their per-core tile/register arrays and the MAA
main selection) so from-scratch rewrite workspaces cannot read that answer key
(ADR 0006). Outputs belong outside Git; --check is a native correctness smoke
on mbit10 inside an owned socket lane.
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

BC = "benchmarks/gapbs/src/bc.cc"
PIN = "9732327b347c5da72526923f44b4250afcd7816c3b0ca1d0c8a43cd1d77f36ea"
ID = "bc-dx100-scalar-only-20261003-a1.source"
IMPLEMENTATION = "dx100-bc-scalar"
# Exact pinned ranges (1-based, inclusive): tile/register arrays, PBFSMAA and
# its trailing blank line, BrandesMaa and its trailing blank line.
REMOVED = [[66, 67], [130, 331], [426, 643]]
VERIFIER_LINES = [654, 720]
SELECTION = """#ifdef MAA
        return BrandesMaa(g, sp, cli.num_iters(), cli.logging_en());
#else
        return Brandes(g, sp, cli.num_iters(), cli.logging_en());
#endif"""


def scalar_source(original):
    # These exact ranges are tied to the pinned source, not a C++ heuristic.
    if hashlib.sha256(original.encode()).hexdigest() != PIN:
        raise Failure("DX100 bc.cc differs from the pinned e4fc4af source")
    lines = original.splitlines(keepends=True)
    removed = set()
    for first, last in REMOVED:
        removed |= set(range(first, last + 1))
    if not (lines[129].startswith("void PBFSMAA(") and lines[425].startswith("pvector<ScoreT> BrandesMaa(")
            and lines[65].startswith("int tiles0[NUM_CORES]") and lines[66].startswith("int regs0[NUM_CORES]")):
        raise Failure("pinned DX100 BC removal anchors differ")
    result = "".join(line for number, line in enumerate(lines, 1) if number not in removed)
    if result.count(SELECTION) != 1:
        raise Failure("pinned DX100 BC main selection differs")
    result = result.replace(SELECTION, "        return Brandes(g, sp, cli.num_iters(), cli.logging_en());")
    if re.search(r"\b(?:PBFSMAA|BrandesMaa|tiles[0-9]|regs[0-9]|maa_[a-z_]+|get_new_tile|get_new_reg)\b", result):
        raise Failure("scalar-only BC source retains accelerator implementation material")
    return result


def materialize(folder, records):
    full = ROOT / "apps/dx100"
    before = artifacts.identify(full)
    original = (full / BC).read_text()
    source = folder / "source"
    source.mkdir(parents=True, exist_ok=False)
    # Keep the BC translation unit and build headers only. Other benchmark
    # translation units and API examples contain additional answer keys.
    keep = ["LICENSE", "benchmarks/gapbs/LICENSE"]
    keep += [p.relative_to(full).as_posix() for p in (full / "benchmarks/gapbs/src").glob("*.h")]
    keep += [p.relative_to(full).as_posix() for p in (full / "benchmarks/API").glob("*.hpp")]
    keep += [p.relative_to(full).as_posix() for p in (full / "include").rglob("*.h")]
    for relative in sorted(keep):
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(full / relative, target)
    (source / BC).write_text(scalar_source(original))
    (source / "PROVENANCE.md").write_text(
        "# DX100 scalar-only BC rewrite source\n\nDate: 2026-10-03 ET\n\n"
        "Derived from DX100 e4fc4afdf894f295442cef3604667a469fab8e62. "
        "The accelerator BC functions (PBFSMAA, BrandesMaa), their tile/register arrays, and the MAA "
        "main selection were removed under ADR 0006 to keep the authors' accelerator answer key out of "
        "from-scratch rewrite workspaces. Only the BC translation unit, required build headers "
        "and licenses remain. The scalar PBFS forward pass, Brandes, BCVerifier, and FUNC API setup are "
        "preserved. API headers are operation definitions, not an accelerated BC implementation. "
        "The full source remains available for author-code reuse strategies.\n")
    store = Store(records)
    context = copy.deepcopy(store.source_context(store.get(IMPLEMENTATION, "implementation")))
    text = (source / BC).read_text()
    file_hash = artifacts.file_hash(source / BC)
    context["code"] = [{"root": "application", "path": BC, "sha256": file_hash}]
    # The scalar-only tree needs no NUM_CORES: the arrays that used it are removed.
    context["build"]["flags"] = "-std=c++11 -O3 -Wall -fopenmp -pthread -DFUNC"
    # Relocate the unchanged evaluator range after removal of the answer key.
    first, last = VERIFIER_LINES
    verifier_text = "".join(original.splitlines(keepends=True)[first - 1:last])
    if not verifier_text.startswith("// Still uses Brandes") or text.count(verifier_text) != 1:
        raise Failure("scalar derivation changed the BC correctness check")
    start = text[:text.index(verifier_text)].count("\n") + 1
    context["evaluator"]["verifier"]["code"] = {
        "root": "application", "path": BC, "sha256": file_hash,
        "lines": [start, start + len(verifier_text.splitlines()) - 1]}
    context["source_derivation"] = {
        "date": "2026-10-03", "decision": "docs/adr/0006-rewrite-providers-work-in-a-guarded-workspace.md",
        "upstream_bc_sha256": PIN,
        "removed_functions": ["PBFSMAA", "BrandesMaa"],
        "removed_pinned_line_ranges": REMOVED,
        "removed_main_selection": "MAA branch calling BrandesMaa",
        "excluded_material": "Other benchmark translation units, API examples/scripts, and old manifests.",
        "purpose": "From-scratch proposals cannot read the authors' accelerator BC answer key.",
        "full_source_artifact_sha256": before["sha256"],
        "script": "scripts/prepare_dx100_bc_scalar_snapshot.py"}
    context["verification"] = {"status": "unchecked", "evidence": [],
        "scope": "Derived scalar source; native correctness smoke is recorded separately, no performance claim."}
    region = {"id": f"{BC}:1-{len(text.splitlines())}:{file_hash[:16]}", "path": BC,
              "lines": [1, len(text.splitlines())], "source_sha256": file_hash,
              "text": text, "association": "declared_source_region"}
    data = workflow.record("source_snapshot", ID, implementation=IMPLEMENTATION,
        application="dx100-gapbs", revision=context["source"]["commit"],
        artifact=artifacts.identify(source), context=context, regions=[region],
        protections=artifacts.protections(source, context))
    data["provenance"][0]["description"] = (
        "Scalar-only derivative registered by prepare_dx100_bc_scalar_snapshot.py on 2026-10-03; "
        "removed author accelerator BC code under ADR 0006; full source retained unchanged.")
    if artifacts.identify(full) != before:
        raise Failure("full source changed during scalar-only materialization")
    return data


def check(data, folder, records, lane):
    if socket.gethostname().split(".")[0] != "mbit10":
        raise Failure("native scalar BC snapshot correctness smoke must run on mbit10")
    machine = Store(records).get("mbit10", "machine")
    verified = _verified_lane(machine, lane)
    source = Path(data["artifact"]["path"])
    binary = folder / "bc.scalar"
    flags = shlex.split(data["context"]["build"]["flags"])
    command = ["g++", *flags, "-I" + str(source / "benchmarks/API"),
               "-I" + str(source / "benchmarks/gapbs/src"), str(source / BC), "-o", str(binary)]
    build = subprocess.run(command, capture_output=True, text=True, timeout=180)
    (folder / "build.stdout").write_text(build.stdout)
    (folder / "build.stderr").write_text(build.stderr)
    if build.returncode:
        raise Failure("scalar BC snapshot build failed; raw logs retained")
    trials = []
    environment = {**os.environ, "OMP_NUM_THREADS": "4", "OMP_DYNAMIC": "FALSE"}
    for graph in ("-g", "-u"):
        argv = [str(binary), graph, "10", "-k", "4", "-i", "1", "-n", "1", "-v"]
        run = subprocess.run(argv, capture_output=True, text=True, timeout=120, env=environment)
        name = "kronecker" if graph == "-g" else "uniform-random"
        (folder / (name + ".stdout")).write_text(run.stdout)
        (folder / (name + ".stderr")).write_text(run.stderr)
        passed = run.returncode == 0 and bool(re.search(r"Verification:\s+PASS", run.stdout))
        trials.append({"family": name, "argv": argv, "returncode": run.returncode, "passed": passed})
    receipt = {"created": "2026-10-03", "classification": "native_correctness_smoke",
               "snapshot": data["id"], "source_sha256": data["artifact"]["sha256"],
               "bc_sha256": artifacts.file_hash(source / BC), "binary_sha256": artifacts.file_hash(binary),
               "build_argv": command, "lane": verified, "host": "mbit10", "threads": 4,
               "trials": trials, "gain_claim": False}
    (folder / "correctness.json").write_text(json.dumps(receipt, indent=2) + "\n")
    if not all(row["passed"] for row in trials):
        raise Failure("scalar BC snapshot correctness smoke failed; receipt retained")
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
    receipt = check(data, folder, args.records, args.lane) if args.check else None
    if receipt:
        receipt_path = folder / "correctness.json"
        data["context"]["verification"] = {
            "status": "passed", "evidence": [{"path": str(receipt_path),
                "sha256": artifacts.file_hash(receipt_path), "classification": receipt["classification"]}],
            "scope": "Native FUNC smoke only: one random source, scale-10 Kronecker and uniform-random graphs, four threads; no performance or accelerator claim."}
    request = folder / "source-record.yaml"
    request.write_text(yamlio.dumps(data))
    if args.register:
        subprocess.run([sys.executable, "-B", "-m", "swdb", "add", str(request),
                        "--records", str(args.records)], cwd=ROOT, check=True)
    print(json.dumps({"snapshot": data["id"], "artifact": data["artifact"]["path"],
                      "sha256": data["artifact"]["sha256"], "files": len(data["artifact"]["files"]),
                      "registered": args.register, "correctness": receipt,
                      "record_file": str(request)}, indent=2))


if __name__ == "__main__":
    main()
