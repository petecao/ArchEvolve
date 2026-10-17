# Stall contract consequences

Created: 2026-10-15 ET.

These frozen C inputs establish two narrow consequences used by the original
qualified stall fixture. The matching commands, per-goal outcomes, process
results and report hashes are in
[`t27-stall-model-consequences-20261015.json`](../../../evidence/t27-stall-model-consequences-20261015.json).

- `alu_memory_domain.c` calls the old ALU contract, which has no new preservation
  clause. Its universal memory-domain consequence passed 8 ordinary goals and
  2 smoke checks. It is derived from the existing trusted contract.
- `store_initializedness.c` retains the actual store read/write loop, replaces
  its operand-check macro with a checked assertion, and adds a universal
  initializedness invariant. It passed 56 ordinary goals and 6 smoke checks,
  including the real old-value read's initializedness and memory checks.
- `store_effect_closure.json` independently inventories the actual generated
  model's seven-function reachable closure. The omitted dispatch and final
  bookkeeping write only fixed model storage or scalar locals. The loop
  contains the closure's sole host-memory write; there is no allocation, free,
  opaque call or indirect helper write.

Both proofs use Frama-C 33, the real model, `-wp-no-filter-init`, RTE
initializedness checks, fresh sessions, cache none and smoke checks. Raw
reports remain at the absolute paths recorded in the evidence file.

This is an initializedness and logical-preservation check. It does not prove
the entire model's undefined-behavior or hazard contract, or replace ticket 29's
independent three-form agreement. Entry-window qualifications remain explicit
conditional input contracts. No source fixture or caller precondition changes.

The checked consequence inputs use **DX_NT=8, DX_TS=2**. Their production
postconditions are conditional on that exact geometry; other geometries retain
the prior contracts. The 909 qualified stall replay discharged initializedness
but remained unproved at its store memory-domain precondition.

`memory_clear_eight.c` proves the production finite conjunction equivalent to
the frozen original forall for arbitrary state and all integer arguments.
`memory_clear_fallback40.c` checks the quantified fallback at NT40/TS1.
`memory_clear_missing_row7.c` is a separate fault control: omitting index 7 leaves
the equivalence unproved. These are pure logic lemmas with no input premises
or C paths; they add no lemma to production. Commands and hashes are in
[`t27-stall-memory-quantifier-20261015.json`](../../../evidence/t27-stall-memory-quantifier-20261015.json).
