# HTA reproduction inputs and source identity

The original experiment used execution-driven modified ZSim and special x86-64
NOP encodings for lookup, update, swap and delete. This is described in section
7 (Methodology), physical PDF page 8, before the section 7.1 workload heading.
Ordinary native execution or stock ZSim does not supply those HTA semantics.
Section 4.2's functional-unit RTL synthesis is a distinct reproduction path.

The bounded source search checked the exact author publication entries, accepted
manuscript/program identities, both publication titles, DOI and RTL/ZSim queries.
It did not bind an authenticated original repository/archive. This is not a global
claim that code does not exist. [Author entry bindings](author-primary-binding.json)
record final URLs, digests and publication links; no author was contacted.

[The source request](source-request.json) identifies two explicit modes:

- `zsim_execution_driven`: modified model, NOP decoder, register/branch wrappers,
  table/overflow/lock protocol, pinned build inputs and defined-input correctness
  harness.
- `rtl_component_only`: actual functional-unit RTL, testbench, synthesis recipe
  and build manifest. Synthesis alone cannot establish core/software integration.

Exact NOP bytes, CRC seed/word order, register packing/result flag polarity,
atomic retirement and faults are still unbound. An original source owner must
supply repository/archive identity and role paths. A future reconstruction without
that lineage must be labeled a **new implementation**, not an original artifact
reproduction. Paper claims and the mutex-backed consumer witnesses remain separate.

The portable inspector binds bounded source-file hashes only. Even a valid package
returns false author-origin, build-flags and ISA/atomic-semantic certificates. It
never starts compilation, execution or synthesis.

```sh
python3 docs/hta-catalog-admission/reproduction/source_request.py request
python3 docs/hta-catalog-admission/reproduction/source_request.py inspect SOURCE_PACKAGE.json
python3 -m unittest discover -s docs/hta-catalog-admission/reproduction -p 'test_*.py'
```

No catalog capability, existing test result, native ISA or current simulator is
changed by these source-role notes.
