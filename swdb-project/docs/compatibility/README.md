# Main-database crosswalk v0

Date: 2026-10-06 ET

[The crosswalk](lanl-crosswalk-v0.yaml) is a versioned compatibility draft from slides
8–9 of the ArchEvolve overview deck dated 2026-10-06. It is separate from research
records and does not import or export LANL data. [ADR 0014](../adr/0014-main-and-research-databases.md)
defines the main/research database boundary.

From `swdb-project/`, validate its format and the current research records together:

```sh
python -m swdb validate --crosswalk docs/compatibility/lanl-crosswalk-v0.yaml
```

The command accepts YAML or JSON, rejects duplicate keys, and reports failures with
the document path and field. Without `--crosswalk`, existing record validation and
query behavior stay the same. The standalone
[JSON Schema](../../schemas/compatibility/main_crosswalk.schema.json) uses Draft 2020-12;
it does not use the research-record envelope.

Read each row as a proposed semantic mapping:

- `table_label` and `field_label` preserve what the slide shows. A null field label
  maps a table as a whole.
- `table_identifier` and `field_identifier` record only tokens visible in the deck.
  All unseen SQL identifiers are null. A visible token is still unverified until
  LANL provides `database/schema.sql` and its ingest rules.
- `research` lists record kinds and dotted fields. A null research field means the
  whole record kind. A `proposed` mapping has at least one destination;
  `no_counterpart` has an empty list.
- Every mapping and extension concept has `status: unverified` and `source_slide: 8`
  or `9`. A source slide on an extension identifies the inventory against which
  absence was inferred; it does not prove absence from the main database.

The 25 mapping rows cover the ten table labels and visible field descriptions.
The slides do not expose the complete schema, foreign-key layout, ID lifetimes,
metric units or timing scopes. Those remain unknown. The 19 concepts in
`separable_extension` preserve research-only records and evidence-basis semantics
without requiring LANL to adopt them. Search chunks and embeddings stay in the main
database; SWDB has no matching record kinds.

The source PDF was inspected read-only at
`/Users/yanrujhou/Downloads/ArchEvolve-project-overview.pdf`. Its filename, date and
SHA-256 are retained in `source_deck`; the source deck is not copied into this repository.
Validation checks the draft format, not a live LANL schema or source-deck availability.
Import and round-trip work remains blocked on LANL access (tickets 21–23).
