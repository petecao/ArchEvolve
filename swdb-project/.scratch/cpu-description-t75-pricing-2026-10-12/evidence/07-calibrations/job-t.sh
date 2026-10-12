#!/bin/bash
# The two native-LLVM OpenMP tests that hit the 180 s budget on the Mac (ticket 05), run on mbit10.
# The tests pass no --toolchain-flag, and on mbit10 clang 22 picks GCC 14 (no libstdc++ headers),
# so attempt 1 failed with "'cstddef' file not found". Attempt 2 runs them against a wrapper bin
# directory: symlinks to every LLVM 22 tool, with clang++/clang wrapped to add the same
# --gcc-install-dir flag that every real calibration run passes.
source "$(dirname "$0")/common.sh" "$1" job-t
envsnap job-t-start
W=$RAW/llvm22-gcc13-bin
rm -rf "$W" && mkdir -p "$W"
for f in "$LLVM"/bin/*; do ln -s "$f" "$W/$(basename "$f")"; done
for c in clang++ clang; do
  rm "$W/$c"; printf '#!/bin/sh\nexec %s/bin/%s --gcc-install-dir=/usr/lib/gcc/x86_64-linux-gnu/13 "$@"\n' "$LLVM" "$c" > "$W/$c"; chmod +x "$W/$c"
done
rm -rf "$RAW/pytest-bt"; mkdir -p "$RAW/pytest-bt"
step openmp-native-tests-2 2400 env SWDB_LLVM_BIN="$W" /data1/yanruj/venvs/swdb-test/bin/python -m pytest -p no:cacheprovider \
  --basetemp="$RAW/pytest-bt" -o tmp_path_retention_policy=failed -rfE -v \
  "tests/test_cpu_openmp_calibration.py::test_count_only_matrix_proves_exact_selected_event_scope_without_elapsed" \
  "tests/test_cpu_openmp_calibration.py::test_portable_probe_retains_every_legal_event_and_is_imported_only_as_fixture"
rc=$?; envsnap job-t-end; exit $rc
