"""Candidate compilation and trusted driver contracts. Updated: 2026-09-25."""

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

from swdb import artifacts, workflow
from swdb.dx100_candidate import driver
from test_dx100 import case, reference


@pytest.mark.parametrize("override", [False, True])
def test_public_candidate_compile_preserves_source_binary_receipt_and_rejects_driver_override(case, records, override):
    request, invoke, folder = case
    records.copy_repo("applications")
    repository = Path(__file__).resolve().parents[1]
    kernel = yaml.safe_load((repository / "records/kernels/gapbs-bfs.yaml").read_text())
    kernel["baseline_implementation"] = "dx100-bfs-scalar"
    records.write("kernels/gapbs-bfs.yaml", kernel)
    records.write("implementations/dx100-bfs-scalar.yaml", yaml.safe_load(
        (repository / "records/implementations/dx100-bfs-scalar.yaml").read_text()))
    model_build = request("model-build")
    model_build["fixture_command"] = [sys.executable, "-c", "print('fixture model build')"]
    assert invoke("dx100-build", model_build)["outcome"]["state"] == "complete"
    root = folder / "candidate-source"
    source = root / "benchmarks/gapbs/src/bfs.cc"
    source.parent.mkdir(parents=True)
    verifier = "bool BFSVerifier() { return true; }"
    source.write_text("// Contract fixture source\n" + verifier + "\n" + ("#define m5_dump_stats(...) ((void)0)\n" if override else ""))
    artifact = artifacts.identify(root)
    protections = [{"path": "benchmarks/gapbs/src/bfs.cc", "kind": "verifier", "text": verifier}]
    snapshot = workflow.record("source_snapshot", "source", implementation="dx100-bfs-scalar", application="dx100-gapbs",
        revision="fixture", artifact=artifact, context={}, protections=protections, regions=[])
    candidate = workflow.record("candidate", "candidate", implementation="dx100-bfs-scalar", source_snapshot="source",
        artifact=artifact, context={}, protections=protections, state="unverified", artifact_role="source_baseline")
    records.write("source_snapshots/source.yaml", snapshot)
    records.write("candidates/candidate.yaml", candidate)
    model = Path(model_build["model_root"])
    assembly = model / "util/m5/build/x86/abi/x86/m5op.S"
    assembly.parent.mkdir(parents=True)
    assembly.write_text("// fixture assembly\n")
    compiler = folder / "fixture-compiler"
    compiler.write_text(f"#!{sys.executable}\n" + "import pathlib,sys\np=pathlib.Path(sys.argv[sys.argv.index('-o')+1]); p.write_text('#!/bin/sh\\nexit 0\\n'); p.chmod(0o755)\n")
    compiler.chmod(0o755)
    compile_request = request("candidate-build")
    compile_request.update(candidate="candidate", build_evaluation="model-build", function="DOBFS", accelerated=False,
        roi="bfs.complete_call.v1", fixture_compiler=reference(compiler),
        budget={"total_seconds": 60, "memory_gib": 1, "storage_gib": 1, "build_seconds": 10})
    result = invoke("dx100-compile", compile_request)
    assert result["outcome"]["state"] == ("failed" if override else "complete"), result["outcome"]
    if not override:
        assert result["build"]["binary_sha256"]
        assert result["context"]["candidate_sha256"] == artifact["sha256"]
        assert result["context"]["roi"] == "bfs.complete_call.v1"
        assert "m5_dump_stats" in result["context"]["suppressed_internal_events"]
        assert result["context"]["verifier_source"]["bounds_check"]


@pytest.mark.parametrize("parents,passes", [("0,0,1", True), ("0,9,1", False), ("0,0", False)])
def test_generated_driver_checks_bounds_before_verifier_and_fingerprints_returned_parents(tmp_path, parents, passes):
    compiler = shutil.which("clang++") or shutil.which("g++")
    if compiler is None:
        pytest.skip("C++ compiler unavailable for trusted driver contract")
    model = tmp_path / "model"
    header = model / "include/gem5/m5ops.h"
    header.parent.mkdir(parents=True)
    header.write_text("#pragma once\n" + "\n".join(f"inline void {name}(int,int) {{}}" for name in (
        "m5_checkpoint", "m5_work_begin", "m5_work_end", "m5_dump_stats", "m5_reset_stats")) + "\ninline void m5_exit(int) {}\n")
    source = tmp_path / "fixture.cc"
    source.write_text('''#include <vector>
using NodeID=int;
struct CLApp { CLApp(int,char**,const char*) {} bool ParseArgs(){return true;} int start_vertex(){return 0;} bool logging_en(){return false;} };
struct Graph { int num_nodes() const {return 3;} };
struct Builder { Builder(CLApp&){} Graph MakeGraph(){return Graph();} };
std::vector<int> DOBFS(const Graph&,int,bool) {return {PARENTS};}
bool BFSVerifier(const Graph&,int,const std::vector<int>& p) { std::puts("CHECKER_CALLED"); return p.size()==3 && p[0]==0 && p[1]==0 && p[2]==1; }
int main(int,char**) {return 0;}
'''.replace("PARENTS", parents))
    generated = tmp_path / "driver.cc"
    generated.write_text(driver(source, model, "DOBFS"))
    binary = tmp_path / "driver"
    result = subprocess.run([compiler, "-std=c++11", str(generated), "-o", str(binary)], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=5)
    assert run.returncode == (0 if passes else 4)
    assert ("CHECKER_CALLED" in run.stdout) is passes
    assert "SWDB_BFS_RESULT source=0 vertices=3" in run.stdout
    assert "parent_fnv1a64=" in run.stdout
    assert ("Verification: PASS" in run.stdout) is passes
