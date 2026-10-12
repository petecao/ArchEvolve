"""Contract link tables: `swdb_contract_definitions`, `swdb_contract_data_structures`,
`swdb_contract_kernels`, `swdb_contract_kernel_variants` (LANL-shaped-db ticket 06).
Created 2026-10-11 ET. See `swdb/lanl.py` for what a group module provides.

These are `swdb_` extension tables: they point at LANL rows and at the contract's
`swdb_library_entries` row, and no LANL table points back, so dropping them leaves the LANL core
intact. Each row names the record (and field) that states the link; nothing is inferred.

A link is made only from a record that ties a rewrite contract to code:

- a certification whose `candidate` names a `contract` and a source `snapshot`: the contract
  links to the snapshot's implementation (`kernel_variants`) and that implementation's kernel;
- a statement fact `legality:<contract>:<clause>` on an implementation's statement: the contract
  links, for that clause, to the statement's function (`definitions`, the row the implementation's
  `extensions.statements.function` produced), to the arrays of the access-pattern steps the
  statement names (`data_structures`), and to the implementation and its kernel.

A link says that a record ties the contract to the row, not that the contract holds there: a
certification links whatever its verdict, and a fact whatever its value (both stay readable
through `record_id` and `record_field`, and in `swdb_statement_facts`). A contract the library does not hold (kind `rewrite_contract`) gets no link: the link would have
no contract row to point to. The site finder's matches (recorded in campaign summaries) and a
proposal's offered library are not links: the first is inference, the second an offer.
"""

ORDER = 60

_LINK = """
CREATE TABLE swdb_contract_{table} (contract TEXT NOT NULL REFERENCES swdb_library_entries(id),
    {column} INTEGER NOT NULL REFERENCES {target}(id), clause TEXT,
    record_id TEXT NOT NULL REFERENCES swdb_records(id), record_field TEXT NOT NULL,
    PRIMARY KEY (contract, {column}, record_id, record_field));
"""
_TABLES = {"definitions": ("definition_id", "definitions"),
           "data_structures": ("data_structure_id", "data_structures"),
           "kernels": ("kernel_id", "kernels"),
           "kernel_variants": ("kernel_variant_id", "kernel_variants")}

SCHEMA = "".join(_LINK.format(table=table, column=column, target=target)
                 for table, (column, target) in _TABLES.items())

GUESSED = []


def fill(rows, store):
    links = _Links(rows.con)
    if not links.contracts:
        return
    for record in sorted(store.of_kind("certification"), key=lambda r: r.id):
        candidate = record.data.get("candidate") or {}
        snapshot = store.get(candidate.get("snapshot"), "source_snapshot") or {}
        links.variant(rows, candidate.get("contract"), snapshot.get("implementation"), None, record.id, "candidate")
    for record in sorted(store.of_kind("implementation"), key=lambda r: r.id):
        _statements(rows, links, record)


def _statements(rows, links, record):
    """The links an implementation's statement facts state, one set per `legality:` fact."""
    statements = (record.data.get("extensions") or {}).get("statements") or {}
    function = rows.con.execute("SELECT row_id FROM swdb_row_origins WHERE table_name = 'definitions' "
                                "AND record_id = ? AND record_field = 'extensions.statements.function'",
                                (record.id,)).fetchone()
    for i, annotation in enumerate(statements.get("annotations") or []):
        for j, fact in enumerate(annotation.get("annotation_facts") or []):
            contract, clause = links.legality(fact.get("field") if isinstance(fact, dict) else None)
            if contract is None:
                continue
            field = f"extensions.statements.annotations[{i}].annotation_facts[{j}]"
            if function is not None:
                links.add("definitions", contract, function[0], clause, record.id, field)
            for array in _step_arrays(record.data, annotation):
                structure = rows.con.execute("SELECT d.id FROM data_structures d JOIN kernel_variants v "
                                             "ON v.kernel_id = d.kernel_id WHERE v.slug = ? AND d.name = ?",
                                             (record.id, array)).fetchone()
                if structure is not None:
                    links.add("data_structures", contract, structure[0], clause, record.id, field)
            links.variant(rows, contract, record.id, clause, record.id, field)


def _step_arrays(impl, annotation):
    """The array names of the access-pattern steps a statement names (`step` is a 0-based
    position in the pattern's `steps`)."""
    patterns = {p.get("id"): p.get("steps") or [] for p in impl.get("access_patterns") or []}
    for ref in annotation.get("access_pattern_steps") or []:
        steps, step = patterns.get(ref.get("pattern"), []), ref.get("step")
        if isinstance(step, int) and 0 <= step < len(steps) and (steps[step].get("array") or {}).get("name"):
            yield steps[step]["array"]["name"]


class _Links:
    """Inserts link rows for the contracts the library holds."""

    def __init__(self, con):
        self.con = con
        self.contracts = {cid for (cid,) in con.execute(
            "SELECT id FROM swdb_library_entries WHERE kind = 'rewrite_contract'")}

    def legality(self, field):
        """(contract, clause) of a statement-fact field `legality:<contract>:<clause>` naming a
        contract the library holds, else (None, None). The contract is matched against the
        library's IDs, so neither part is split on a guess."""
        if not isinstance(field, str) or not field.startswith("legality:"):
            return None, None
        rest = field.removeprefix("legality:")
        named = [c for c in self.contracts if rest.startswith(c + ":") and len(rest) > len(c) + 1]
        if not named:
            return None, None
        contract = max(named, key=len)
        return contract, rest[len(contract) + 1:]

    def add(self, table, contract, target, clause, record_id, field):
        column = _TABLES[table][0]
        self.con.execute(f"INSERT OR IGNORE INTO swdb_contract_{table} (contract, {column}, clause, record_id, "
                         f"record_field) VALUES (?,?,?,?,?)", (contract, target, clause, record_id, field))

    def variant(self, rows, contract, implementation, clause, record_id, field):
        """Link `contract` to the variant of `implementation` and to that variant's kernel."""
        variant = rows.id_of("kernel_variants", implementation)
        if contract not in self.contracts or variant is None:
            return
        self.add("kernel_variants", contract, variant, clause, record_id, field)
        (kernel,) = self.con.execute("SELECT kernel_id FROM kernel_variants WHERE id = ?", (variant,)).fetchone()
        self.add("kernels", contract, kernel, clause, record_id, field)
