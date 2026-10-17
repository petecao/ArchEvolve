# Ticket 03 verification: crosswalk v0

Date: 2026-10-06 ET
Status: passed; one existing data-dependent query case skipped.

The [crosswalk](../../docs/compatibility/lanl-crosswalk-v0.yaml) contains 25 mappings
for ten table labels and the visible field descriptions in slides 8–9, plus 19
separable extension concepts. All 44 entries are `unverified` and cite slide 8 or 9.
Every proposed research record kind and dotted field was checked against the current
record vocabulary and merged research schemas. Unseen main-database SQL identifiers
remain null. No main-database import, export or access is claimed.

Source inspection used the local overview PDF read-only, including rendered slides
8–9, and independently extracted the PPTX slide text. The pinned PDF SHA-256 is
`a71e905932a3ef501a801aac2efc63a44c176ec0b7b0d1a645f41ad3826e49c9`.
The source file is named `ArchEvolve-project-overview.pdf`, dated 2026-10-06.

## Public checks

Commands run from `swdb-project/` with
`/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3`:

```sh
python -m swdb validate --crosswalk docs/compatibility/lanl-crosswalk-v0.yaml
python -m pytest tests/test_crosswalk.py -q
python -m pytest tests/test_crosswalk.py tests/test_validate_rules.py \
  tests/test_validate_application.py tests/test_db.py tests/test_query_index.py \
  tests/test_view.py -q
```

- Record and crosswalk validation: `OK: 553 record(s) valid; crosswalk valid`.
- Final focused set: seven public CLI cases passed. Each behavior was introduced
  after observing its failing public-command case, then checked green.
- Validation/query regression: 139 passed, 1 skipped in 602.83 seconds. The skip is
  `test_no_profile_means_explicitly_unknown_counts_metrics_bottleneck`: a real
  `gapbs-pr-gs.kron-g22-k16.mbit10` profile exists in the repository, so the test
  cannot exercise its no-profile premise. The final focused set also passed
  after adding the counterpart-kind guard.
- The standalone schema passed `Draft202012Validator.check_schema`.
- Source audit confirmed all referenced research kinds and dotted fields exist.
- `git diff --check` passed.

These checks establish the draft format and unchanged research-query behavior.
They do not verify the unseen LANL schema, ID lifetime, field units, timing scopes,
or the inferred absence of the separable extension concepts.
