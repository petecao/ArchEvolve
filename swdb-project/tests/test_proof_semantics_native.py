"""Native public model-query ABI controls; created 2026-10-15 ET.

Compile the complete exported model_for result as C and C++, and call its declared footprint query.
AddressSanitizer's invalid-pointer-pair checker catches cross-object pointer subtraction even without a
memory dereference. The flat uintptr_t address ABI is explicit in the native model; CBMC retains object IDs.
"""
import json
import os
import subprocess

import pytest

from swdb import cbmc_translator as tr, c_lowering, proof_semantics
from swdb.library import Library
from conftest import REPO


QUERY_DRIVER = r'''
static int swdb_query_checks(void) {
  int a[4] = {11, 22, 33, 44}, b[4] = {0};
  swdb_dx_init();
  dx_tile_writer[0] = 0; dx_kind[0] = DX_GATHER;
  dx_base[0] = a; dx_index[0] = 1; dx_tile_size[1] = 2;
  dx_tile_data[1][0] = 0; dx_tile_data[1][1] = 2;
  if (swdb_dx_in_footprint(0, b)) return 1;
  if (!swdb_dx_in_footprint(0, a) || !swdb_dx_in_footprint(0, a + 2)) return 2;
  if (swdb_dx_in_footprint(0, a + 1) || swdb_dx_in_footprint(0, a + 4)) return 3;
  dx_base[0] = a + 1;
  if (swdb_dx_in_footprint(0, a) || !swdb_dx_in_footprint(0, a + 1) ||
      !swdb_dx_in_footprint(0, a + 3)) return 4;
  dx_kind[0] = DX_STREAM_LOAD; dx_base[0] = a;
  dx_lo[0] = 1; dx_hi[0] = 4; dx_stride[0] = 2;
  if (swdb_dx_in_footprint(0, b) || swdb_dx_in_footprint(0, a) ||
      !swdb_dx_in_footprint(0, a + 1) || !swdb_dx_in_footprint(0, a + 3)) return 5;
  if (dx_tile_of(a) != -1 || dx_tile_of(&dx_tile_data[0][0]) != 0 ||
      dx_tile_of(&dx_tile_data[DX_NT-1][DX_TS-1]) != DX_NT-1 ||
      dx_tile_of(&dx_tile_data[DX_NT-1][DX_TS]) != -1) return 6;
  swdb_dx_init();
  maa_const(-1, 0); maa_const(0, 1); maa_const(1, 2);
  maa_stream_load(a + 1, 0, 1, 2, 0, -1);
  if (dx_tile_size[0] != 1 || dx_tile_data[0][0] != 11 || !swdb_dx_in_footprint(0, a)) return 7;
  if (swdb_dx_in_footprint(0, a + 1) || swdb_dx_in_footprint(0, b)) return 8;
  if (swdb_dx_in_footprint(0, (const int *)((uintptr_t)a + 1)) ||
      swdb_dx_in_footprint(0, (const int *)(uintptr_t)0) ||
      swdb_dx_in_footprint(0, (const int *)(UINTPTR_MAX - (UINTPTR_MAX % sizeof(int))))) return 9;
  dx_kind[0] = DX_GATHER; dx_index[0] = 1; dx_tile_size[1] = 1; dx_tile_data[1][0] = 0;
  if (swdb_dx_in_footprint(0, a) || !swdb_dx_in_footprint(0, a + 1)) return 10;
#if defined(SWDB_CBMC)
  if (dx_tile_of(dx_tile_data[0] + DX_TS) != -1) return 11;
#endif
  return 0;
}
'''

@pytest.mark.parametrize("language,standard", [("c", "gnu11"), ("c++", "gnu++17")])
def test_native_footprint_query_accepts_related_offsets_and_rejects_other_objects(tmp_path, language, standard):
    compiler = c_lowering.locate()
    if compiler.missing:
        pytest.skip(compiler.missing)
    model = proof_semantics.model_for(Library(REPO / "library"), "semantics.dx100_bfs_0_1")
    source = tmp_path / "query.c"
    source.write_text(tr.prelude() + model.c_text + QUERY_DRIVER + "\nint main(void) { return swdb_query_checks(); }\n")
    executable = tmp_path / "query"
    built = subprocess.run([*compiler.command, "-x", language, f"-std={standard}", "-O1", "-g",
                            "-fsanitize=address,pointer-subtract,undefined", "-fno-omit-frame-pointer",
                            str(source), "-o", str(executable)], capture_output=True, text=True, timeout=60)
    assert built.returncode == 0, built.stderr
    ran = subprocess.run([str(executable)], capture_output=True, text=True, timeout=60,
                         env={**os.environ, "ASAN_OPTIONS": "detect_invalid_pointer_pairs=2:detect_leaks=0",
                              "UBSAN_OPTIONS": "halt_on_error=1"})
    assert ran.returncode == 0, ran.stdout + ran.stderr



def test_cbmc_footprint_query_preserves_signed_stream_offsets_and_distinct_tile_rows(tmp_path):
    from swdb import cbmc_adapter, rss_watchdog, verifier_lock
    command, _version, missing = cbmc_adapter.locate()
    if missing:
        pytest.skip(missing)
    model = proof_semantics.model_for(Library(REPO / "library"), "semantics.dx100_bfs_0_1")
    source, log = tmp_path / "query.c", tmp_path / "cbmc.json"
    source.write_text(tr.prelude() + model.c_text + QUERY_DRIVER + r'''
int main(void) {
  __CPROVER_assert(swdb_query_checks() == 0, "exported query checks");
  return 0;
}
''')
    with verifier_lock.hold("t27 signed-stream and row-object model control"):
        result = rss_watchdog.run([*command, str(source), "-DSWDB_CBMC", "--bounds-check", "--pointer-check",
            "--pointer-overflow-check", "--signed-overflow-check", "--div-by-zero-check",
            "--unwinding-assertions", "--unwind", str(model.unwind), "--json-ui"],
            log=log, cap_bytes=8 * 2**30, timeout=600, cwd=tmp_path)
    assert result.exit_code == 0 and not result.timed_out and not result.out_of_memory, log.read_text()
    messages = json.loads(log.read_text())
    properties = next(m["result"] for m in messages if "result" in m)
    assert any(p.get("description") == "exported query checks" and p["status"] == "SUCCESS" for p in properties)
