# Builder contract formatter V2

2026-10-16 ET.

This inert successor fixes three metadata errors in the first 79/80 pair. It
changes only `unit_contracts` in the frozen V1 builder:

- Emit separate `frame` and `result` clause rows with distinct obligation names.
- State `concurrency_frame: []` for the original no-parameter unit interface.
- Use one `target` role for the existing single `stream` address shape.

All source, model, receiver, allocation, draw, transport, method and output-writing
functions remain byte-exact V1. The whole-module inverse proves that boundary.
Contract content hashes and dependent future source-policy hashes change; neither
expected result enters derivation or model state. Contracts still precede the
source policy and semantics entry, with no semantics back-reference or hash cycle.

The pure controls demonstrate V1 refusal and V2 acceptance through extracted real
`Library.validate` Python checks, formal-frame `_entry`, placement, concurrency,
roles, the ACSL scanner, `checked_unit_format`, the translator's clause parser, and
`unit_contract`. Both real result expressions remain separate from the frame.
Mutations exercise each repaired field, required fields, clause roles, controls,
placement, source pins, selected contract hashes, extra requires, narrower/mixed
frames and unknown builtins. The original source buffer is used only as a pinned
metadata fixture; no compilation or source admission occurs.

The source-policy selector is a disclosed protocol stand-in populated with the
generated contract IDs and actual content hashes. The external JSON-schema engine
is replaced only in these stdlib controls by a fail-closed evaluator of the exact
pinned repository schema. The evaluator rejects any unknown validation keyword.
It is not production `jsonschema` validation. The real formal-frame compiler
typecheck stage is not run. These are metadata seam controls, not a public proof,
profile derivation, actual runtime preparation, or scientific acceptance.

V1, planner V2, the runtime V4 draft, and all shared production files remain
unchanged. V1's preparer still pins its original builder; this packet does not
silently redirect it. A coherent later route/profile must explicitly bind V2 and
the reviewed complete-capture ingress before actual preparation. Current failed
or partial captures remain refused.
