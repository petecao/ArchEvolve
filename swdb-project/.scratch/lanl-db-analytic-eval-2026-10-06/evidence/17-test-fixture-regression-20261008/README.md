# Bounded contract fixture regression

Created: 2026-10-08 ET

The agreement suite's source-snapshot setup exceeded its unchanged 600-second timeout after its fixture copied the complete 704-record, 1,023,048,889-byte catalog. Five test files now copy byte-exact real dependencies reachable from explicit fixture roots. Selected bodies still use the existing YAML reader, and public commands still validate every copied record and reference. Product source, canonical records, library, frozen R/C185F6, evaluation controls and scientific budgets are unchanged.

The helper indexes bounded top-level ID headers, refuses missing roots and duplicate IDs, preserves relative filenames and copies recursive record references, including semantic evidence and cycles. Regressions verify that unrelated large malformed bodies are not parsed and that original selected bytes are preserved. Root and independent source review found no remaining material issue.

Commands below ran from `swdb-project` with `.venv/bin/python -m pytest -q`:

| Arguments | Result |
|---|---|
| `tests/test_record_subset.py tests/test_extensa_agreement.py::test_public_report_keeps_fixture_forecasts_ineligible_and_d30_unsupported` | 3 passed, 40.92 s |
| `-x tests/test_extensa_agreement.py::test_public_freeze_is_immutable_for_the_same_prospective_campaign_population tests/test_extensa_pairing.py::test_real_adapters_persist_estimates_before_every_evaluator_entry` | 3 passed, 36.96 s |
| `tests/test_record_subset.py tests/test_extensa_agreement.py tests/test_extensa_pairing.py tests/test_extensa_boundary.py tests/test_extensa_targets.py -k 'not test_repository_records_revalidate_unchanged'` | 73 passed, 1 deselected, 550.66 s |
| `tests/test_campaign_budget_fixes.py tests/test_certification_feedback.py tests/test_campaign_candidate_records.py` | 38 passed, 124.83 s |
| `tests/test_record_subset.py` after US spelling correction | 2 passed, 0.06 s |

The sole exclusion was the unchanged canonical repository revalidation test. Root separately ran the public validation command successfully against all 704 canonical records this turn. Test counts overlap across commands and should not be summed.

The initial full-catalog run timed out during setup. A superseded repair run produced 13 passes and five setup errors from a dated Kronecker fixture-root typo; corrected smoke and final suites passed. Another superseded run was interrupted after two passes to repair the boundary fixture's remaining full-catalog copy. These outcomes are reported from the retained command outputs; this document is a regression summary, not a byte-exact original stream archive or scientific execution evidence.
