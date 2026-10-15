"""Public rehashed-renderer controls for private pipeline projection; 2026-10-15 ET."""
import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml

from conftest import REPO
from swdb import std_models
from test_vector_pipeline_wp import CONTRACT, pipeline_seed
from test_wp_adapter import fake, method_version, needs_wp


def _fault_record(tmp_path, old, new):
    seed = pipeline_seed(tmp_path)
    runtime = tmp_path / "changed-runtime"
    shutil.copytree(REPO / "swdb", runtime / "swdb", ignore=shutil.ignore_patterns("__pycache__"))
    path = runtime / "swdb" / "vector_pipeline.py"
    original = path.read_text()
    assert original.count(old) == 1
    path.write_text(original.replace(old, new))
    env = {**os.environ, **fake("unknown"), "SWDB_HOME": str(REPO), "PYTHONPATH": str(runtime),
           "SWDB_VERIFIER_LOCK": str(tmp_path / "scripted.lock")}
    refreshed = subprocess.run([sys.executable, "-c",
        "import json; from swdb import c_lowering,proof_setup; "
        "print(json.dumps([c_lowering.identity(),proof_setup.identity()]))"],
        cwd=runtime, env=env, capture_output=True, text=True, check=True)
    lowering, checks = json.loads(refreshed.stdout)
    method = method_version(lowering)
    method["checks"].update(checks)
    method["models"]["std_vector"] = std_models.identity()
    method["models"]["std_pair"] = std_models.identity()
    (seed.root / "library" / "methods" / "wp-tracer-fixture.yaml").write_text(
        yaml.safe_dump(method, sort_keys=False))
    result = subprocess.run([sys.executable, "-m", "swdb", "prove", "--records", str(seed.records),
        "--summary", CONTRACT, "--adapter", "wp", "--runs-dir", str(seed.runs), "--format", "json"],
        cwd=runtime, env=env, capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stderr + result.stdout
    return yaml.safe_load((seed.records / json.loads(result.stdout)["path"]).read_text())


@needs_wp
@pytest.mark.parametrize("old,new", [
    ('"  struct swdb_pipeline_pair best={0,0};",',
     '"  static struct swdb_pipeline_pair best={0,0};",'),
    ('"  struct swdb_pipeline_pair best={0,0};",',
     '"  static _Thread_local struct swdb_pipeline_pair best={0,0};",'),
    ('"int "+lowering.function+"(const int *a,int n) {",',
     '"static int "+lowering.function+"(const int *a,int n) {",'),
    ('"int "+lowering.function+"(const int *a,int n) {",',
     '"int __attribute__((const)) "+lowering.function+"(const int *a,int n) {",'),
    ('"int "+lowering.function+"(const int *a,int n) {",',
     '"int "+lowering.function+"(const int *a,int n __attribute__((unused))) {",'),
    ('globals_anchor, contract,', 'globals_anchor, "int extra_state;", contract,'),
    ('"    int x=a[swdb_pipeline_range];",', '"    short x=a[swdb_pipeline_range];",'),
], ids=["persistent_pair", "thread_pair", "function_storage", "function_attribute",
        "parameter_attribute", "extra_global", "narrowed_value"])
def test_a_rehashed_pipeline_renderer_cannot_change_declarations_or_storage(tmp_path, old, new):
    record = _fault_record(tmp_path, old, new)
    assert record["failure_class"] == "unsupported_construct", record
    assert not any(row["name"] == "wp_log" for row in record["evidence"]["reports"])
