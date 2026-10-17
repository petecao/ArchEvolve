# An access pattern is a chain of steps

Date: 2026-09-22

Each access pattern is a chain of steps (one array per step, and the address shape used
to reach it) that ends at the array it reads or updates, with one update kind for the
whole pattern. The model follows Prodigy's Data Indirection Graph (Talati et al., HPCA
2021: single-valued and ranged indirection) plus Pointer Chase from Ayers et al. (ASPLOS
2020). A flat list of labels would need a name for every multi-level and multi-way
combination, and each step's array fields (base, element count, element size) are what
a programmable prefetcher is configured with. No published taxonomy defines update
kinds, so that axis is our own.
