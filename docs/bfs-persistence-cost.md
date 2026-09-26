# Catalog persistence cost

Created: 2026-09-25 (Eastern Time)

`workflow.persist` previously loaded the entire catalog to decide whether a
record existed, then the writer loaded it again under its lock, validation
loaded it a third time, and index rebuilding loaded it a fourth time. This
repeat parsing is metadata cost, not BFS runtime. It does not explain all of
the residual host cost observed in remote pilot stages.

The writer now chooses create or replace under its existing exclusive file
lock. Full schema and cross-record validation use that same fresh in-memory
store, including every unrelated record and parsing problem. No store survives
an independent write. Explicit create-only calls still reject an existing ID,
replacement retains the record's existing path, and writes still use a
temporary YAML file followed by replacement. Index rebuilding retains its
independent fresh load and existing fingerprint checks. If indexing fails, the
caller still receives the error identifying the already-durable record.

An isolated 159-record catalog on the local Apple Silicon host was used to
rewrite its unchanged `mbit10` machine record three times before and after the
change, with a real index rebuild on every call. The catalog and measurements
are under `/private/tmp/bfs-persist-cost-awghke3y`; `before-redundant-loads.json`
and `after-redundant-loads.json` contain the wall-clock samples, with separate
`.prof` files for an additional instrumented call in each condition.

| Condition | Three local wall-clock samples (seconds) | Median | Store loads per instrumented call |
| --- | --- | --- | --- |
| Before | 2.3971, 2.3790, 2.3873 | 2.3873 | 4 |
| After | 1.4772, 1.4237, 1.4266 | 1.4266 | 2 |

The median reduction was about 40%. This small local diagnostic is evidence of
less catalog parsing; it is not a remote throughput estimate, a BFS speedup,
or a statistical performance claim. Active remote jobs retained their original
checkouts throughout.

Nineteen focused tests passed, covering public add and invalid-reference
behavior together with concurrent upserts, fresh rejection of an unrelated
malformed record, no writes on validation failure, noncanonical replacement
paths, create-only duplicate refusal, current index contents, and durable YAML
after an index failure. The broader clean-checkout review remains separate.
