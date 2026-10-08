# PHI bulk scatter-update mechanisms

PHI (MICRO 2019) buffers partial commutative updates in cache lines initialized
to the reduction identity. Cache ALUs combine repeated updates without first
fetching the original destination. LLC banks choose in-place application or
streaming into index/value bins based on update density. Replay disables
batching so bins can drain. These mechanisms target synchronization and memory
traffic, rather than returning a value to the issuing instruction.

Revision 0.1.12 adds two explicit bulk-reduction subtypes, six located claims
and six mechanism annotations. The table-supported double-add example is
scoped to float64. Integer signedness and a universal index ABI remain unknown.
Ordinary gather queries, previous records and the MAPLE selection are unchanged.
PHI is an older implementation reference, not a new recent-paper admission.

Its software contract requires a declared relaxed-atomic bulk phase, no
intervening destination reads and no mixed conventional atomics on that region.
All bins must be replayed and private partials flushed with `phi_sync` before
reads. The examined batching implementation also requires contiguous physical
destination storage, bank-local bins and disabling batching before paging out.
Returned old values, CAS success and source-order floating-point equivalence
are not supplied. Numeric legality must be established under the workload's
unchanged oracle, including identity, rounding, NaN and signed-zero behavior.

The portable [phase model](../../examples/mechanism-scaffolds/phi/phase_contract.py)
checks these adoption and phase boundaries. It performs no arithmetic, executes
no memory operations and models no timing. Its caller-provided completion
events are not hardware flush or coherence certificates.

```sh
python3 -m unittest discover -s examples/mechanism-scaffolds/phi -p 'test_*.py'
```

The [primary binding](primary-binding.json) identifies the cached 14-page
author edition by hash and DOI; no corpus PDF is copied. Catalog claim locators
refer to physical PDF pages 5–9, sections 3.1–3.3, Figures 6–9, Listing 2 and
Table 3. The [implementation contract](implementation-contract.json) records
the remaining source, allocator, reduction and completion obligations.
