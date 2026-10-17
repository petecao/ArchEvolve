#!/usr/bin/env bash
# 2026-10-16 ET. INERT until coordinator admission; original-partial u32 scalar-register gate only.
# No actual proof acceptance, source-refinement, hardware-progress or whole28 acceptance.
# Usage: run_register_acceptance.sh <full clean frozen SHA> <positive|negative|pair>
# The coordinator must wrap this entire process tree in its 8 GiB/1,200 s watchdog.
set -euo pipefail
PROBATA_REGISTER_COMMIT="${1:?full frozen source SHA}"
PROBATA_REGISTER_PROFILE="${2:?positive, negative or pair}"
[ "$#" -eq 2 ] || exit 2
case "$PROBATA_REGISTER_COMMIT" in *[!0-9a-f]*|'') exit 2 ;; esac
[ "${#PROBATA_REGISTER_COMMIT}" -eq 40 ] || exit 2
[ "$(git rev-parse HEAD)" = "$PROBATA_REGISTER_COMMIT" ] || exit 2
[ -z "$(git status --porcelain)" ] || exit 2
: "${PROBATA_OUTPUT:?external retained output directory}"
: "${PROBATA_PYTHON:?pinned pytest interpreter}"
PROBATA_REGISTER_ROOT="$(git rev-parse --show-toplevel)"
case "$PROBATA_OUTPUT" in /*) ;; *) exit 2 ;; esac
PROBATA_REGISTER_ROOT="$(cd "$PROBATA_REGISTER_ROOT" && pwd -P)" || exit 2
PROBATA_OUTPUT="$("$PROBATA_PYTHON" -c '
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
output=Path(sys.argv[2]).resolve()
if output.is_relative_to(root) or root.is_relative_to(output):
    raise SystemExit("register output and source must be disjoint resolved paths")
print(output)
' "$PROBATA_REGISTER_ROOT" "$PROBATA_OUTPUT")" || exit 2
case "$PROBATA_REGISTER_PROFILE" in
  positive) PROBATA_REGISTER_TESTS=('tests/test_dx100_register_actual.py::test_actual_wp_original_partial_register_source_pair[correct-register-result]') ;;
  negative) PROBATA_REGISTER_TESTS=('tests/test_dx100_register_actual.py::test_actual_wp_original_partial_register_source_pair[wrong-crossregister-result]') ;;
  pair) PROBATA_REGISTER_TESTS=('tests/test_dx100_register_actual.py::test_actual_wp_original_partial_register_source_pair[correct-register-result]' 'tests/test_dx100_register_actual.py::test_actual_wp_original_partial_register_source_pair[wrong-crossregister-result]') ;;
  *) exit 2 ;;
esac
[ ! -e "$PROBATA_OUTPUT/pytest" ] || exit 2
mkdir -p "$PROBATA_OUTPUT/tmp" "$PROBATA_OUTPUT/cache"
export TMPDIR="$PROBATA_OUTPUT/tmp" XDG_CACHE_HOME="$PROBATA_OUTPUT/cache"
export SWDB_DX100_REGISTER_ACTUAL=1 PYTHONDONTWRITEBYTECODE=1
export SWDB_VERIFIER_RSS_CAP_BYTES=8589934592
export SWDB_VERIFIER_LOCK="$PROBATA_OUTPUT/verifier.lock"
cd "$PROBATA_REGISTER_ROOT/swdb-project"
git rev-parse HEAD > "$PROBATA_OUTPUT/source-commit.txt"
printf '%s\n' "$PROBATA_REGISTER_PROFILE" > "$PROBATA_OUTPUT/profile.txt"
printf '%s\n' "${PROBATA_REGISTER_TESTS[@]}" > "$PROBATA_OUTPUT/selected-tests.txt"
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
    'tests/test_dx100_register_actual.py','tests/test_dx100_register_source.py','tests/testkit/dx100_register.py','tests/testkit/dx100_stream_outcomes.py','tests/testkit/dx100_selector.py','tests/testkit/dx100_trust.py',
    'vocab/proof_subject_kinds.yaml','vocab/proof_failure_classes.yaml','schemas/proof.schema.json',
    'library/proof_semantics','apps/dx100/benchmarks/API'],text=True).split('\0')
pins=[{'path':p,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest(),
       'bytes':(root/p).stat().st_size} for p in files if p]
(out/'source-manifest.json').write_text(json.dumps(pins,indent=2)+'\n')
(out/'runtime-provenance.json').write_text(json.dumps({'compiler':stdlib_provenance.runtime_identity(c_lowering.locate()),
    'lowering':c_lowering.identity(),'checks':proof_setup.identity(),'platform':platform.platform(),
    'actual_register_lineup':actual_lineup,
    'python':sys.version,'python_executable':sys.executable},indent=2)+'\n')
PY
set +e
"$PROBATA_PYTHON" -m pytest "${PROBATA_REGISTER_TESTS[@]}" -q --tb=short --maxfail=1 -p no:cacheprovider \
    --basetemp "$PROBATA_OUTPUT/pytest" --junitxml "$PROBATA_OUTPUT/junit.xml" \
    --report-log "$PROBATA_OUTPUT/report.jsonl" > "$PROBATA_OUTPUT/pytest.log" 2>&1
PROBATA_REGISTER_EXIT=$?
printf '%s\n' "$PROBATA_REGISTER_EXIT" > "$PROBATA_OUTPUT/exit-code.txt"
exit "$PROBATA_REGISTER_EXIT"
