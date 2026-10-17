# DX100 v1 design-source binding

Updated: 2026-10-06 20:59 ET. This evidence companion binds the unchanged counted target descriptions to design claims; it changes no target parameter, backend, observation policy or record bytes.

The descriptor's numeric configuration facts come from pinned source revision `e4fc4af`, retained with exact file hashes in the fresh hardware-target record. Closed-row and row-hit latency are explicitly inferred conditional DDR4 service scenarios, not observed hardware latency. Unknown host, queue, parallelism, staging and setup rates remain null.

| Design source | Descriptor meaning and boundary |
| --- | --- |
| [DX100 v2, Table 2 and §§3.1–3.4](https://arxiv.org/pdf/2505.23073v2#page=4), catalog `dxp-read` | Strided loads, indexed gathers and half-open range expansion motivate the read descriptors. Ranged/chained accesses compose instructions; random-base pointer chasing remains outside this scope. |
| [DX100 v2, §3.3](https://arxiv.org/pdf/2505.23073v2#page=5) | Row grouping and read coalescing motivate logical counts. The declared allocation-relative windows/placement are inferred analytic premises; they do not observe DRAM mapping, scheduling or physical row hits. |
| [DX100 v2, §§3.5–3.6 and 4.1](https://arxiv.org/pdf/2505.23073v2#page=6), catalog `dxp-interface` | Encoded MMIO issue, tile/register allocation and ready-bit waiting motivate separate setup/staging/queue mechanisms. Functional execution does not establish MMIO CPU costs or asynchronous overlap. |
| [DX100 v2, §3.6](https://arxiv.org/pdf/2505.23073v2#page=6), catalog `dxp-translation` | Application-lifetime translation is a design premise; arbitrary aliasing, remapping and revocation are unproved. Native source allocation/page facts do not certify hardware translation or residency. |

Actual aliases and producers bind immutable shipped source hashes and selected FUNC semantics through `source_view`; paper names alone cannot authorize a source function. CPU updates/CAS and scalar fallback remain host work. The canonical read-only candidate does not assume paper update instructions implement CPU CAS. Required host-memory and cross-domain composition gaps stay explicit.

The [binding receipt](09-design-source-binding.json) records the read-only catalog hash, edition/claim locators and exact target hashes. Paper performance plots, simulation output and historical outcomes supply no calibration value. Original targets/counts stay immutable; a backend or structural model change needs its own target version and fresh observations.
