# 17 — How do enabling rewrites chain with offloading rewrites?

Created: 2026-10-13 16:09 ET
**Type:** grilling
**Status:** ready-for-human
**Blocked by:** 15
**Map:** `../map.md`

## Question

How does Extensa Probata propose and prove **enabling rewrites** (glossary: rewrites that offload
nothing and only reshape code so that an offloading rewrite contract can match, as the DX100
authors did by hand), and how are they chained with the offloading rewrites built on top? Decide:

- who proposes an enabling rewrite (the rewriting role in Extensa mode, the site finder, a fixed
  catalog) and how it names the offloading contract it enables;
- what an enabling rewrite's contract states (strategy effect "restructure a loop", its unit
  relation), and whether ticket 15's race fix (plain reads of shared-action locations become
  relaxed atomic loads; redundant plain stores removed) is the first enabling rewrite;
- how proofs chain: when two unit relations compose, how a chain's level is set (its weakest
  link), and when the final candidate artifact is proven directly against the baseline
  implementation instead;
- how a chain is certified and recorded (lineage, content hashes per step).

The answer must handle any input code (map Notes), not only code an expert already reshaped.

## Comments

- 2026-10-13 16:09 ET: graduated from ticket 15 (Q10). Yan-Ru: the DX100 authors reshaped the
  baseline to fit the DX100 API before offloading (compare `TDStepMAA`,
  `apps/dx100/benchmarks/gapbs/src/bfs.cc:66-225`, with `TDStep`, `:227-256`); Probata may likewise
  rewrite the baseline into an equivalent, DX100-compatible form first. The name "equivalent
  baseline" was rejected: the baseline implementation is the code as found, which every proof
  compares against (11, Q30). Chaining is optional: the final candidate artifact can always be
  proven directly against the baseline; a chain only splits one hard relational proof into two
  easier ones. Codex's frontier-staging rewrite (`library/native/bfs-tdstep-frontier-staging.patch`)
  is a CPU-only restructuring already in the library.
