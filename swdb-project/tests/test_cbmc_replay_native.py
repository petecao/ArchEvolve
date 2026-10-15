"""Native counterexample input preservation across sanitizer aborts; 2026-10-15 ET."""
import os
import subprocess

import pytest

from conftest import FIXTURES
from swdb import cbmc_translator as tr, c_lowering


def test_replay_preserves_typed_inputs_when_original_vector_use_after_free_aborts(tmp_path):
    compiler = c_lowering.locate()
    if compiler.missing:
        pytest.skip(compiler.missing)
    interface = tr.Interface("swdb_fixture_vec_stale_data", "int",
                             (("a", "const int *", True), ("n", "int", False)))
    harness, _plan = tr.harness(interface, [], sizes={"n": 1}, cap=1)
    source = tmp_path / "replay.cc"
    source.write_text(tr.prelude() +
                      (FIXTURES / "proof/cbmc/vector_units.cc").read_text() +
                      '\nstatic_assert(sizeof(int) == 4, "captured oracle uses 32-bit int");\n' + harness)
    executable = tmp_path / "replay"
    built = subprocess.run([*compiler.command, "-x", "c++", "-std=gnu++17", "-O0", "-g",
                            "-DSWDB_NATIVE", "-DSWDB_REPLAY", "-fsanitize=address,undefined",
                            "-fno-omit-frame-pointer", str(source), "-o", str(executable)],
                           capture_output=True, text=True, timeout=60)
    assert built.returncode == 0, built.stderr
    # The actual CBMC oracle is cast by the emitted harness, not decoded by Python:
    # -4294967295 becomes int n=1. ASan then aborts before main's normal final flush.
    ran = subprocess.run([str(executable)], input="-4294967295 -1\n", capture_output=True,
                         text=True, timeout=60, env={**os.environ,
                         "ASAN_OPTIONS": "detect_leaks=0:abort_on_error=0",
                         "UBSAN_OPTIONS": "halt_on_error=1"})
    assert ran.returncode != 0 and "heap-use-after-free" in ran.stderr, ran.stdout + ran.stderr
    assert " input n=1" in ran.stdout, ran.stdout
    assert " input a[0]=-1" in ran.stdout, ran.stdout
    assert "end=done" not in ran.stdout
