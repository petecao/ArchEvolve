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
