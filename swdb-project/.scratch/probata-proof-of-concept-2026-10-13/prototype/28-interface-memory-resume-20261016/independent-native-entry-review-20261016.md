# Native memory53 controller review — 2026-10-16 ET

**PASS_SOURCE_REVIEW** for the inert controller and command. Ticket28 parent
reviewed the child-authored source independently; no compiler/native job ran.

1. Controller/command/policy/plan pins match. All 14 source, three additional
   ASan/UBSan and 7,605 augmented public-runtime pins currently match. The exact
   C harness and both generated headers are mandatory inputs.
2. Entry requires the exact selected Python/LLVM22, guard token/tag/cap4GiB,
   fresh private cache and external output. Its closed child environment preserves
   guard ownership, enables ASan/UBSan failure exits and avoids a symbolizer child.
   Token values pass only to children and are redacted from retained receipts.
3. C11 and C++17 each preprocess the original source with the selected flags,
   retain dependency output, pin dependencies after preprocessing, compile frozen
   bytes, then require exit0/exact53-control JSON/empty stderr. Used inputs,
   frozen source, binaries and all declared physical source/runtime pins are
   checked across capture, compilation and execution.
4. Header bytes before their first post-preprocessing capture, concurrent
   change-and-restoration and compiler/loader correctness remain explicit TCB.
   Native outcomes check private preparation only; they do not prove original
   MMIO implementation, memory effects/history, public source-body or hardware.
5. Root must freshly admit the complete 180-second/4GiB one-worker tree guard,
   shared slot,50GiB+256MiBcapacity and independent settlement. Stage128MiB/final
   256MiB limits are postchecks, not a disk quota. Retain the first failure; no
   automatic retry or formal acceptance follows from the command.

Only standard-library source/AST/hash metadata work occurred in this review.
The companion JSON pins the final controller and all policy boundaries.
