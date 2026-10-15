# Standards review — Probata resumed frontier

Date: 2026-10-15 ET.
Scope: `git diff d94d629b...b047527e`; commit list: `git log d94d629b..b047527e --oneline`.

No documented-standard violations found. Root/SWDB agent rules, all `.claude/rules/*.md`, glossary, tracker/triage conventions and ADRs 0006/0016 were inspected. GAPBS's `CONTRIBUTING.md` applies to its application code; this diff changes none. Open dependency-gated tickets and historical proof boundaries are explicitly retained. Unrelated `.claude/settings.json` was not inspected or changed.

**[P3] Possible Duplicated Code / Shotgun Surgery (judgement).** The source-recheck eligibility condition is repeated in `swdb/wp_adapter.py:279-281`, `swdb/proof_setup.py:374-376`, and `swdb/wp_pointer_bounds.py:233-235`. Each hunk adds the same `member_windows` case alongside `owner` and the same site-kind set: `{"call", "producer", "import", "standard_range_call"}`. Admitting one new certificate family therefore requires synchronized changes across three gates; a future omitted gate could lose the independently reparsed-source protection. Extract the shared pointer-bounds eligibility predicate into the owning module and call it from these gates, retaining their distinct plan/array-domain checks and the independent source reparse itself. No current semantic failure is asserted.

Result: 0 hard violations; 1 low-priority smell judgement. Read-only review; no solvers or tests run.
