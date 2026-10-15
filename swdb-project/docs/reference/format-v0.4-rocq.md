# Rocq method-part records

Created: 2026-10-15 ET (Probata ticket 42). Code: `swdb/rocq_adapter.py`.
The composition proof remains open until its approved theorem passes every gate below.

`swdb prove --adapter rocq --method-part composition_theorem --runs-dir /outside/repo/runs --method-version METHOD` checks `library/rocq/probata/` beside the records. `--development DIR`
selects a proposed copy; its full content must match the named method's `rocq_development` pin.
This is a method part, so candidate, contract, bounded-verifier and hint inputs are refused.

The runner refuses admitted steps and added axioms before invoking Rocq. The trusted statement
reconstruction guard checks the approved source definitions and theorem; the independent
`check/Checks.v` harness compares Rocq's elaborated statement with `check/statement.expected`.
Rocq 9.3.0 compiles fresh copies of `Vocabulary.v`, `Composition.v` and the harness in a fresh
scratch directory. No existing `.vo` file is copied. The theorem's own assumption listing must
say it is closed under the global context. Every compile uses the shared verifier lock,
8 GiB RSS watchdog and remaining job budget. The proof setup check records every generated
input hash immediately before launch. Original compile logs remain outside the repository.

A successful record has subject `{kind: method_part, id: rocq.probata.composition,
part: composition_theorem}`, verdict `proven` and `method_part_status: rocq_checked`.
The lifecycle `status` remains independent. `pins.rocq_development` is `{id: rocq.probata,
sha256: ...}`: a digest of the named development files and the trusted statement guard.
The method version pins the same digest, both theorem names and the exact Rocq version.
`settings` identifies the fresh run and memory cap; `evidence.reports` preserves each compile
log by path and hash. A record produced under a fixture method remains `contract_fixture`
evidence. A failed compiler invocation may write `not_proven`; a changed statement or an
unexpected assumption writes no checked record.

`method_part_status: written` represents a written fallback, when the ticket's time-box rule
permits it; this runner does not manufacture that fallback. A written record keeps the named
`written_proof` assumption. Under `level-rule.3`, a counting, proven `rocq_checked` method part
with the canonical subject ID, matching part name and development hash discharges that entry on read and adds the
checked record's trusted-tool assumptions. A changed development restores the written entry;
no existing candidate proof record is rewritten and no assumption entry caps its level.
