# Native memory53 V2 controller review — 2026-10-16 ET

**PASS_SOURCE_REVIEW_V2.** Root must freshly bind the actual guard command and
resources before dispatch. The companion JSON pins the final controller/policies.

The earlier V1 review accepted a false preflight assumption: exact c6 exports
only SWDB_VERIFIER_RUN_TOKEN, not a watchdog tag or RSS-cap environment variable.
Root caught this before execution. V1 remains unexecuted; its guard-admission
claim is superseded, with no scientific result changed.

1. Exact B, c6 and staged_search bytes match. C6 line509 creates the inherited
   token; its marker scan at331 uses that token. B serializes only. V2 requires
   the actual token, accepts optional real inherited tag/cap context and creates
   neither. Root may supply its explicit4GiB RSS policy marker; enforcement comes
   from exact c6 `--timeout180 --cap-gb4`, fresh root admission and actual summary.
2. All14source,3sanitizer,3guard and7605runtime pins match. Source, sanitizer,
   frozen preprocessing/dependency timing, binary/result, cache and output checks
   retain V1's reviewed behavior. Each C11/C++17 binary must report53 controls.
3. The guard discovers owned ancestry, retainedPID/birth and sampled token matches
   and performs finite cleanup sweeps. That evidence is not kernel containment.
   Root owns current slot/resource/argv admission and independent settlement.

Review performed only standard-library source/AST/hash checks. No compiler,
project import, native program, verifier, entry main or SSH was executed.
