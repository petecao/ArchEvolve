# Legality integration fixture seam correction — 2026-10-08 ET

SOURCE ONLY / UNAPPLIED / NOT RUN. Retain the R4 test stdout/stderr/exit and
completed original unit-test receipts unchanged; parent owns final diagnosis,
application and rerun. This corrects my fixture proposal's cross-module omission.

The four legality integration tests import _certify from test_certification_controls.
The applied fixture patch made that helper require keyword-only certification_store,
but my original module-local dependency scan omitted its imported callers.
Current collection positions135/136/144/145 and missing test certification.json
receipts are consistent with TypeError before any compiler/evaluator call;
parent will preserve the exact final R4 traceback when the run ends. Do not
attribute these four failures to R3 certification classification or candidate
rejection. The live unit-test metadata also shows both process1.5 integrations
and exact nativeA8 1.3/1.4 integrations certified with no leftover shm_open failure.

The prospective correction changes only four test function signatures and their
four _certify calls in test_certification_legality.py. Each now receives the same
per-test real original-record closure Store and explicitly passes the required
keyword argument. Pure legality tests, real transformation functions, expected
verdicts, version1.6 assertions, knobs/schedule controls, compiler/evaluator calls,
counts and every original assertion are unchanged. All assertion ASTs are exact;
removing just those eight fixture additions restores the whole original file
byte for byte. A source-wide tests import scan finds no other modules importing
the transformed certification test helpers. No production/library/schema/YAML,
source digest, procedure version or scientific control is changed.

Prospective patch:
/private/tmp/lanl17-certification-fixture-legality-callers-prospective-r1-20261008.diff
2996 bytes; SHA256 c4006577b25b91e0940d5098619e694372522a51674ff9b3b5adb9a126b6cfaf.
Static original/prospective hash, AST and inverse receipt:
/private/tmp/lanl17-certification-fixture-legality-callers-static-review-r1-20261008.json
1073 bytes; SHA256 0fa4ff5f3de2b18ff2517361af2f424a71102c250f8b252cf656f685e4f3be4d.

Parent next step after retaining the original completed R4 diagnostics: apply
only this test file's patch, review the eight edits, and run the four genuine
legality integrations in the authorized unsandboxed environment. Their compiler,
evaluator and positive/control paths must run; do not skip or mock them.
