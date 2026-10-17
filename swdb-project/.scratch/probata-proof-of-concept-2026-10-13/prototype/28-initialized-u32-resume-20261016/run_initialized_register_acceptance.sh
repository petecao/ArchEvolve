#!/usr/bin/env bash
# 2026-10-16 ET. INERT until root source/runtime/solver/lane admission.
# Usage: bash run_initialized_register_acceptance.sh <full SHA> <positive|negative|pair>
# Root wraps the entire tree with one-worker 8GiB/1200s watchdog/socket lane.
set -euo pipefail
PROBATA_INITIALIZED_COMMIT="${1:?full frozen source SHA}"
PROBATA_INITIALIZED_PROFILE="${2:?positive, negative or pair}"
[ "$#" -eq 2 ] || exit 2
case "$PROBATA_INITIALIZED_COMMIT" in *[!0-9a-f]*|'') exit 2 ;; esac
[ "${#PROBATA_INITIALIZED_COMMIT}" -eq 40 ] || exit 2
[ "$(git rev-parse HEAD)" = "$PROBATA_INITIALIZED_COMMIT" ] || exit 2
[ -z "$(git status --porcelain --untracked-files=all)" ] || exit 2
: "${PROBATA_OUTPUT:?fresh external retained output directory}"
: "${PROBATA_PYTHON:?root physical/runtime-pinned pytest interpreter}"
: "${SWDB_DX100_SELECTOR_ACTUAL_LINEUP:?explicit root-pinned actual Frama33/solver version JSON}"
: "${SWDB_VERIFIER_RUN_TOKEN:?root shared counted-verifier admission}"
PROBATA_INITIALIZED_ROOT="$(git rev-parse --show-toplevel)"
PROBATA_INITIALIZED_ROOT="$(cd "$PROBATA_INITIALIZED_ROOT" && pwd -P)"
PROBATA_OUTPUT="$("$PROBATA_PYTHON" -I -B -c '
from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve(); requested=Path(sys.argv[2]); output=requested.resolve()
if not requested.is_absolute() or requested.is_symlink() or output.exists() or output.is_relative_to(root) or root.is_relative_to(output):
    raise SystemExit("fresh source-disjoint resolved output required")
print(output)
' "$PROBATA_INITIALIZED_ROOT" "$PROBATA_OUTPUT")"
case "$PROBATA_INITIALIZED_PROFILE" in
  positive) PROBATA_INITIALIZED_TESTS=('tests/test_dx100_initialized_register_actual.py::test_actual_initialized_u32_original_partial_pair[correct-initialized-result]') ;;
  negative) PROBATA_INITIALIZED_TESTS=('tests/test_dx100_initialized_register_actual.py::test_actual_initialized_u32_original_partial_pair[wrong-crossregister-result]') ;;
  pair) PROBATA_INITIALIZED_TESTS=('tests/test_dx100_initialized_register_actual.py::test_actual_initialized_u32_original_partial_pair[correct-initialized-result]' 'tests/test_dx100_initialized_register_actual.py::test_actual_initialized_u32_original_partial_pair[wrong-crossregister-result]') ;;
  *) exit 2 ;;
esac
mkdir -p "$PROBATA_OUTPUT/tmp" "$PROBATA_OUTPUT/cache"
export TMPDIR="$PROBATA_OUTPUT/tmp" XDG_CACHE_HOME="$PROBATA_OUTPUT/cache"
export PYTHONPYCACHEPREFIX="$PROBATA_OUTPUT/source-cache" PYTHONDONTWRITEBYTECODE=1
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 SWDB_DX100_INITIALIZED_REGISTER_ACTUAL=1
export SWDB_VERIFIER_RSS_CAP_BYTES=8589934592
export SWDB_VERIFIER_LOCK="$PROBATA_OUTPUT/verifier.lock"
cd "$PROBATA_INITIALIZED_ROOT/swdb-project"
git rev-parse HEAD > "$PROBATA_OUTPUT/source-commit.txt"
printf '%s\n' "$PROBATA_INITIALIZED_PROFILE" > "$PROBATA_OUTPUT/profile.txt"
printf '%s\n' "${PROBATA_INITIALIZED_TESTS[@]}" > "$PROBATA_OUTPUT/selected-tests.txt"
"$PROBATA_PYTHON" -B - "$PROBATA_OUTPUT" <<'PY'
import hashlib,json,platform,subprocess,sys
from pathlib import Path
out=Path(sys.argv[1]);root=Path.cwd()
sys.path.insert(0,str(root/'tests'))
from testkit.dx100_selector import read_actual_lineup
actual_lineup=read_actual_lineup()
from swdb import c_lowering,proof_setup,stdlib_provenance
files=subprocess.check_output(['git','ls-files','-z','--','swdb','tests','pyproject.toml',
    'vocab','schemas','library/proof_semantics','library/dx100','apps/dx100/benchmarks/API'],text=True).split('\0')
pins=[{'path':p,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest(),'bytes':(root/p).stat().st_size}for p in files if p]
(out/'source-manifest.json').write_text(json.dumps(pins,indent=2)+'\n')
(out/'runtime-provenance.json').write_text(json.dumps({'compiler':stdlib_provenance.runtime_identity(c_lowering.locate()),
    'lowering':c_lowering.identity(),'checks':proof_setup.identity(),'platform':platform.platform(),
    'actual_initialized_lineup':actual_lineup,'python':sys.version,'python_executable':sys.executable},indent=2)+'\n')
PY
set +e
"$PROBATA_PYTHON" -B -m pytest "${PROBATA_INITIALIZED_TESTS[@]}" -q --tb=short --maxfail=1 -p no:cacheprovider \
    --basetemp "$PROBATA_OUTPUT/pytest" --junitxml "$PROBATA_OUTPUT/junit.xml" > "$PROBATA_OUTPUT/pytest.log" 2>&1
PROBATA_INITIALIZED_EXIT=$?
printf '%s\n' "$PROBATA_INITIALIZED_EXIT" > "$PROBATA_OUTPUT/exit-code.txt"
"$PROBATA_PYTHON" -I -B - "$PROBATA_OUTPUT" "$PROBATA_INITIALIZED_PROFILE" <<'PY'
import json,sys
import xml.etree.ElementTree as ET
from pathlib import Path
out=Path(sys.argv[1]);profile=sys.argv[2]
expected={'positive':{'correct-initialized-result'},'negative':{'wrong-crossregister-result'},'pair':{'correct-initialized-result','wrong-crossregister-result'}}[profile]
result={'accepted':False,'scope':'pytest workflow census only; independent complete cold audit still required'}
try:
 root=ET.parse(out/'junit.xml').getroot();suites=list(root.iter('testsuite'));cases=list(root.iter('testcase'))
 assert root.tag=='testsuites'and len(list(root.iter('testsuites')))==len(suites)==1
 assert suites[0].get('tests')==str(len(expected))and len(cases)==len(expected)
 assert all(suites[0].get(k)=='0'for k in ('errors','failures','skipped'))
 assert not any(next(root.iter(k),None)is not None for k in ('error','failure','skipped'))
 wanted={'test_actual_initialized_u32_original_partial_pair['+name+']'for name in expected}
 assert {c.get('name')for c in cases}==wanted
 assert all(c in list(suites[0])and c.get('classname')=='tests.test_dx100_initialized_register_actual'for c in cases)
 assert not (out/'source-cache').exists()and not (out/'source-cache').is_symlink()
 result.update(accepted=True,cases=len(cases))
except (OSError,ValueError,ET.ParseError,AssertionError)as error:result['error']=str(error)or type(error).__name__
(out/'junit-census.json').write_text(json.dumps(result,indent=2)+'\n')
raise SystemExit(0 if result['accepted']else 1)
PY
PROBATA_INITIALIZED_CENSUS_EXIT=$?
set -e
[ "$PROBATA_INITIALIZED_EXIT" -eq 0 ] && [ "$PROBATA_INITIALIZED_CENSUS_EXIT" -eq 0 ]
