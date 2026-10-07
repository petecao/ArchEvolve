# ExTensor ordered-fiber operand delivery

ExTensor (MICRO 2019) intersects ordered sparse-tensor coordinate streams to
skip unmatched work and deliver only matching operand pairs. Scanners supply
coordinates and EOS; matching coordinate-position tuples preserve both operand
owners and parent/tile paths. Its optimized CAM/SkipTo mechanism skips larger
unmatched ranges while synchronizing hint frontiers. LLB and PE staging filter
work at different granularities; a partial-output buffer merges results by
output coordinate.

Catalog revision 0.1.13 adds the explicit
`extensor_ordered_fiber_operand_pair` read subtype, six located primary claims
and eight mechanism annotations. It supplies no generic gather, atomic old
value or scalar reduction operation. Evaluated double-precision operands are
scoped float64 evidence; coordinate width, transport encoding, DMA/control and
host-visible completion remain unknown. ExTensor is an older MICRO 2019
reference, not a new recent-paper admission.

The [portable merge helper](../../examples/mechanism-scaffolds/extensor/fiber_contract.py)
requires canonical strictly increasing unique fibers, preserves owner/parent/
position/generation and opaque operand bits, and retains matching inputs under
output backpressure. EOS flushes unmatched remainder; completion also requires
output drain. Canonical uniqueness is an admission restriction, not a claim
that hardware canonicalizes duplicates. The helper does not implement CAM
SkipTo, scalar arithmetic, memory requests, cycle timing or the paper's RTL.

```sh
python3 -m unittest discover -s examples/mechanism-scaffolds/extensor -p 'test_*.py'
```

A future implementation must bind actual tensor layout/positions, finite
storage and tiling, synchronized SkipTo state if enabled, outstanding read
completion, partial-output writeback and host memory visibility. Reordered
partial reductions require separate numerical legality under the original
workload oracle; this read contract grants no source-order FP equivalence.

The [primary binding](primary-binding.json) identifies the cached 15-page
proceedings edition by hash and DOI without duplicating the PDF. Catalog
locators cover sections 4–7 and evaluated configuration/type evidence in
sections 8.1–8.2, physical PDF pages 4–10.
