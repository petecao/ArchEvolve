# Finite mechanism scaffold

[finite_gather.py](finite_gather.py) illustrates two distinct association contracts: MAPLE-style reserved FIFO slots tolerate out-of-order response arrival while consumption remains in queue order; a DX100-inspired line/offset fixture groups requests and restores each logical ordinal, including duplicates.

These are integer-bit association examples. They do not model cycles, DRAM scheduling, translation, coherence, faults, real hardware capacities or accelerator speedups. Line issue order and ACK-retained credit policy in `DxLines` are explicitly chosen fixture policies. A correct synthetic contract is not a certified accelerator implementation.

The source-backed differences, editions and unknown implementation obligations are recorded in [the mechanism handoff](../../docs/mechanism-handoff-2026-10-06/README.md).
