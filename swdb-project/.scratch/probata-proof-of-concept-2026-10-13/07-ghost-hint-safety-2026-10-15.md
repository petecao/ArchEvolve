# Ticket 07: trusted ghost-state hint boundary

Created: 2026-10-15 ET. Safety-method bug fix before any further counted run.

The prototype hint check previously accepted ghost writes to `dxc_pending`, `dxc_dep`,
`dxc_reg`, and `dxc_tile_len`, and declarations shadowing trusted header names. Frama-C's
ordinary ghost noninterference check does not establish that hints preserve a model
implemented in ghost state. A hint may add proof witnesses; it may not rewrite that model.

The unconditional `fresh-scalars-pure-indexed-reads-v1` guard now runs in `hints.check`,
before parse, goal generation, or solver execution. `loop.py` and `edit_loop.py` record
the guard version in future metadata; the existing harness hashes pin its implementation.
The standalone only-run record also names the guard. There is no disabling flag.

The guard allows fresh scalar declarations and assignments to those hint-owned scalars.
It rejects trusted-name shadowing, array/member/pointer writes, pointer declarations,
macro expansion, direct and indirect calls, address-taking, and expressions containing
assignments or increments. Its reserved-name and macro base includes the original C unit
and every stand-in header (`bfs_unit.h`, `dxc_summaries.h`, `gapbs_models.h`), so header-only
model state is protected too. Rejected declarations do not acquire witness ownership.

The grammar follows production `swdb.proof_setup.check_semantics_hints` with two deliberate
prototype differences: no trusted-store-bound assignment exception, and pure indexed
reads on a scalar declaration/assignment RHS remain allowed. For example, run 13's
`ghost int td_old_i = dxc_reg[c.reg[4]];` and analogous old-j snapshot retain their meaning.
The prototype remains self-contained and does not acquire an unpinned production-module
dependency. Strategy vocabulary, prover limits, attachments, and smoke restrictions are
unchanged; a quoted word `ghost` in a strategy is not an executable ghost statement.

Name reservation is conservative: all base identifier tokens are reserved, including
header/comment identifiers. The old positive test's generic `g` witness was renamed
to a fresh name because `g` already appears in `bfs_unit.h`. This is an intentional
rejection change, not a relaxed check.

## Validation

At the existing public hint-check and loop-precheck seams, the controls first failed:
unsafe model-shadow hints reached the would-be verifier; model writes, aliases, and
calls were accepted. After the repair, all 54 prototype tests pass (the original 26
plus 28 safety/preservation controls). The precheck control confirms that rejection
happens before a verifier call or run directory is created. Coverage includes all three
trusted headers, direct/indexed calls, hidden ghost statements, duplicate witness names,
macro tokens, pure indexed snapshots, fresh scalar reassignment, and existing strategies.
Independent local review found that the initial mutation pattern missed `<<=` and `>>=`
inside RHS expressions. Four failing controls reproduced both array and scalar mutations;
the guard now rejects shift assignments explicitly while retaining `<=`/`>=` comparisons.

Command (from the repository root):

```sh
python -m pytest swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/test_hints.py swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/test_loop_tool.py swdb-project/.scratch/probata-proof-of-concept-2026-10-13/prototype/07-wp-hints/test_edit_loop.py -q
```

The selected interpreter was Python 3.12.6, pytest 9.0.3. The final run took 0.10 seconds.
No real verifier, external agent CLI, or expensive hint loop was run for this repair.

## Evidence boundary

Counted run 13's original artifacts remain unchanged. It finished FAIL, outside its budget,
with 19 open goals (2 unit and 17 hint). A read-only lexical recheck accepts all 44 hints
in its best set under the new guard; this does not discharge any proof obligation or
change the run's verdict. Any future counted run must record the new safety method and
perform its own required proof replay. The coordinator owns the ticket and run-13
metadata update.

A short read-only diagnosis of the outstanding goals is outside the repository at
`/private/tmp/probata-t07-guard-notes/remaining-goals.md`. The two unit goals are source
validity preconditions for the queue and parent gathers; the hint debts comprise 11
loop-invariant obligations, 3 assertions, 2 variant obligations, and one helper lemma.
No missing result was replaced by an assumption.

### Preprocessing boundary hardening, 2026-10-15 ET

The ghost-expression guard explicitly refuses `??` sequences, which have no legitimate
use in the admitted pure expression language and could be transformed by C trigraph
processing before line splicing. Controls cover `dx_count >>??/` followed by newline and
`= 31`, an unsupported `??` expression, and an ordinary comparison/ternary expression.
The exact shift/newline example was already refused by the plain-assignment check; the
new explicit rejection removes reliance on recognizing the later operator spelling.
This is lexical safety hardening, not evidence that a trigraph attack executed under the
installed compiler's default flags. No preprocessing or solver run was needed.
