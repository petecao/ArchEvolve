#!/usr/bin/env bash
# 2026-10-16 ET. INERT until coordinator admission; partial-normal-return stream gate only.
# No total-correctness, source-refinement, hardware-progress or whole28 acceptance.
# Usage: run_stream_acceptance.sh <full clean frozen SHA> <positive|negative|pair|missing>
# The coordinator must wrap this entire process tree in its 8 GiB/1,200 s watchdog.
set -euo pipefail
PROBATA_STREAM_COMMIT="${1:?full frozen source SHA}"
PROBATA_STREAM_PROFILE="${2:?positive, negative, pair or missing}"
[ "$#" -eq 2 ] || exit 2
case "$PROBATA_STREAM_COMMIT" in *[!0-9a-f]*|'') exit 2 ;; esac
[ "${#PROBATA_STREAM_COMMIT}" -eq 40 ] || exit 2
[ "$(git rev-parse HEAD)" = "$PROBATA_STREAM_COMMIT" ] || exit 2
[ -z "$(git status --porcelain)" ] || exit 2
: "${PROBATA_OUTPUT:?external retained output directory}"
: "${PROBATA_PYTHON:?pinned pytest interpreter}"
PROBATA_STREAM_ROOT="$(git rev-parse --show-toplevel)"
case "$PROBATA_OUTPUT" in /*) ;; *) exit 2 ;; esac
case "$PROBATA_OUTPUT/" in "$PROBATA_STREAM_ROOT/"*) exit 2 ;; esac
case "$PROBATA_STREAM_PROFILE" in
  positive) PROBATA_STREAM_TESTS=('tests/test_dx100_stream_actual.py::test_actual_wp_source_partial_stream_gate[correct-size]') ;;
  negative) PROBATA_STREAM_TESTS=('tests/test_dx100_stream_actual.py::test_actual_wp_source_partial_stream_gate[wrong-size]') ;;
  pair) PROBATA_STREAM_TESTS=('tests/test_dx100_stream_actual.py::test_actual_wp_source_partial_stream_gate[correct-size]' 'tests/test_dx100_stream_actual.py::test_actual_wp_source_partial_stream_gate[wrong-size]') ;;
  missing) PROBATA_STREAM_TESTS=('tests/test_dx100_stream_actual.py::test_actual_missing_isolated_stream_certificate_refuses_before_wp') ;;
  *) exit 2 ;;
esac
[ ! -e "$PROBATA_OUTPUT/pytest" ] || exit 2
mkdir -p "$PROBATA_OUTPUT/tmp" "$PROBATA_OUTPUT/cache"
export TMPDIR="$PROBATA_OUTPUT/tmp" XDG_CACHE_HOME="$PROBATA_OUTPUT/cache"
export SWDB_DX100_STREAM_ACTUAL=1 PYTHONDONTWRITEBYTECODE=1
export SWDB_VERIFIER_RSS_CAP_BYTES=8589934592
export SWDB_VERIFIER_LOCK="$PROBATA_OUTPUT/verifier.lock"
cd "$PROBATA_STREAM_ROOT/swdb-project"
git rev-parse HEAD > "$PROBATA_OUTPUT/source-commit.txt"
printf '%s\n' "$PROBATA_STREAM_PROFILE" > "$PROBATA_OUTPUT/profile.txt"
printf '%s\n' "${PROBATA_STREAM_TESTS[@]}" > "$PROBATA_OUTPUT/selected-tests.txt"
"$PROBATA_PYTHON" - "$PROBATA_OUTPUT" <<'PY'
import hashlib,json,platform,subprocess,sys
from pathlib import Path
out=Path(sys.argv[1]);root=Path.cwd()
# Explicit actual pins must validate before compiler/runtime provenance work.
sys.path.insert(0,str(root/'tests'))
from testkit.dx100_selector import read_actual_lineup
actual_lineup=read_actual_lineup()
from swdb import c_lowering,proof_setup,stdlib_provenance
files=subprocess.check_output(['git','ls-files','-z','--','swdb',
    'tests/test_dx100_stream_actual.py','tests/test_dx100_stream_source.py','tests/testkit/dx100_stream.py','tests/testkit/dx100_stream_outcomes.py','tests/testkit/dx100_selector.py','tests/testkit/dx100_trust.py',
    'tests/fixtures/proof/dx100/gem5-e4fc4af','tests/fixtures/proof/dx100/gem5-e4fc4af-stream',
    'vocab/proof_subject_kinds.yaml','vocab/proof_failure_classes.yaml','schemas/proof.schema.json',
    'library/proof_semantics','apps/dx100/benchmarks/API'],text=True).split('\0')
pins=[{'path':p,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest(),
       'bytes':(root/p).stat().st_size} for p in files if p]
(out/'source-manifest.json').write_text(json.dumps(pins,indent=2)+'\n')
(out/'runtime-provenance.json').write_text(json.dumps({'compiler':stdlib_provenance.runtime_identity(c_lowering.locate()),
    'lowering':c_lowering.identity(),'checks':proof_setup.identity(),'platform':platform.platform(),
    'actual_stream_lineup':actual_lineup,
    'python':sys.version,'python_executable':sys.executable},indent=2)+'\n')
PY
set +e
"$PROBATA_PYTHON" -m pytest "${PROBATA_STREAM_TESTS[@]}" -q --tb=short --maxfail=1 -p no:cacheprovider \
    --basetemp "$PROBATA_OUTPUT/pytest" --junitxml "$PROBATA_OUTPUT/junit.xml" \
    --report-log "$PROBATA_OUTPUT/report.jsonl" > "$PROBATA_OUTPUT/pytest.log" 2>&1
PROBATA_STREAM_EXIT=$?
printf '%s\n' "$PROBATA_STREAM_EXIT" > "$PROBATA_OUTPUT/exit-code.txt"
exit "$PROBATA_STREAM_EXIT"
