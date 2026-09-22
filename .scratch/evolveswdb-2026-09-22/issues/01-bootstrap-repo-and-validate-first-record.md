# 01 — Bootstrap the repo and validate the first record

Created: 2026-09-22
**Type:** slice
**Status:** resolved
**Blocked by:** None — can start immediately
**Spec:** `../spec.md`

**What to build:** The owner clones EvolveSWDB, runs `swdb validate`, and sees a valid
gapbs application record accepted and a broken one rejected, with the file, the field,
and the reason. The repo carries the SW Database documents and a copy of the HW
Ensemble drafts.

- [x] Local clone of the private GitHub repo `ruchou/EvolveSWDB` at `~/CLionProjects/EvolveSWDB`; the first commit is pushed to `main`.
- [x] The glossary, ADRs 0001–0003, the spec, these tickets, and format proposal v0.1 are copied in from MemAcc; the originals stay where they are.
- [x] Josh's HW Ensemble drafts are copied byte-identical (checksums match) into a folder labeled as his.
- [x] The envelope schema, the application schema, and the vocabularies for record kinds and provenance kinds exist; the schemas use only features jsonschema 4.10 supports.
- [x] A gapbs application record exists (upstream URL, pinned commit, license, language, parallel model, build command).
- [x] `swdb validate` exits 0 on the valid record; it exits non-zero on a fixture missing a required field and on a fixture with an unknown key outside `extensions`. Each error names the file, the field, and the reason on stderr.
- [x] The test harness runs `swdb` as a separate process against a temporary records folder; the tests pass on the Mac.
- [x] The only dependencies are Python 3.12, PyYAML, and jsonschema.

## Comments

## Answer

Resolved 2026-09-22.

- Repo `ruchou/EvolveSWDB` cloned at `~/CLionProjects/EvolveSWDB`, first commit on `main`.
- Copied in: glossary, ADRs 0001–0003, spec, tickets, map, format proposal v0.1 (as
  `docs/format-proposal-v0.1.md`). Josh's four drafts copied byte-identical into
  `archevolve/hw_ensemble/`; `shasum -a 256 -c SHA256SUMS` reports OK for all four.
- `swdb validate` checks the envelope and application schemas and five vocabularies
  (record kinds, provenance kinds, source origins, parallel models, domains). The gapbs
  record pins upstream commit `2972aeb2703165bafd921222f4ed7196f542d3a8` (BSD-3-Clause,
  `make`, `-std=c++11 -O3 -Wall -fopenmp`).
- Evidence: `python3 -m pytest` → 24 passed, both with jsonschema 4.26 / PyYAML 6.0.3
  and in a venv pinned to mbit10's jsonschema 4.10.3 / PyYAML 6.0.1.

Decisions taken while building (all reversible):

- Kernels will point to their application; the application record does not list kernels.
- Kind schemas are merged with the envelope in code instead of cross-file `$ref`,
  because `$ref` resolution differs between jsonschema 4.10 and current releases.
- Bare YAML dates stay text, and a repeated key in one mapping is an error.
- Schemas refer to vocabularies by name (`x-vocab`); `x-reason` gives a rule's message.
