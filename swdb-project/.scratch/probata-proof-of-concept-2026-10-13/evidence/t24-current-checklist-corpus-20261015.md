# Current runtime checklist and corpus refresh

Updated: 2026-10-15 ET. Scope: compiler/public controls and ACSL typechecking;
no actual WP run or repeat of the 115 passing atomic controls.

The guarded narrow profile passes 24 cases in 51.21 seconds: all seven original
unsupported groups refuse before launch with a construct and source location;
all nine original groups lower twice to identical C/anchors and compile as C11;
kept class fields/references/constructor/destructor names and template instances
match; the class formal half typechecks and its wrong-field control fails;
allocation, standard-model calls, summary calls and version-bump naming hashes
retain their expected forms. Peak RSS is 361,037,824 bytes, exit 0, no OOM/timeout.
All seven physical proof records and their reports are hash-checked.

Three diagnosed admission failures now have explicit ticket21 corpus entries:
closed local Ring subobjects, pure conditional-return window reads, and canonical
`i<=n` allocation overruns. Their existing real regression tests consume these
case inputs/expected values and retain all previous positive/negative assertions.
The 15 existing compiler/public controls pass in 6.16 seconds, peak RSS
264,273,920 bytes, exit 0 and no OOM/timeout. An initial YAML ternary quoting
collection error is retained under a separate raw directory; it changed no
production code and was corrected before the green replay.

The [compact metadata](t24-current-checklist-corpus-20261015.json) records commands,
JUnit case names, stdout/resource hashes, runtime identity, all seven refusal
records and exact source boundaries. The runtime matches frozen `0e7f2327` byte
for byte under `swdb/`; new corpus inputs and three test modules are test-only
changes after that freeze. Active remote producers, checkouts and evaluation
artifacts were unchanged. Generated-C proofs retain the direct naming pin;
early Unsupported refusals have no generated C names and retain the trusted
lowering identity containing the naming rules. Original-C model proofs have no
C++ name mapping. The version-bump hash check passes separately.

The fresh finite agreement limb and float actual pair are accepted separately.
Remaining current actual caller/model/summary and allocation/lifetime rows,
whole-job resources/cleanup and independent final audit remain open. Ticket24
stays claimed until that complete evidence is available.
