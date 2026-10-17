# 06 — Which papers are closest to ours?

Created: 2026-10-09
**Type:** research
**Status:** resolved
**Blocked by:** None — can start immediately
**Map:** `../map.md`

## Question

Which 2023–2026 papers are closest to "LLM-produced performance rewrites, formally verified
against reusable rewrite contracts, with LLM proof hints when the verifier stalls"?

Cover: LLM code optimization with verification (LLM-Vectorizer, LLM vectorization with
verification, LLM superoptimization with equivalence checking, LLM-guided compiler optimization
checked by Alive2, verified transpilation), agentic HPC optimization with correctness checks,
and the related work of the Extensa paper (`/Users/yanrujhou/CLionProjects/MemAcc/paper/LACT_Submission/`).

Output: a positioning table (what each verifies, against what, how it scales, what it cannot do)
and the gap our paper fills, or evidence that the gap is already filled.

## Answer

Answered 2026-10-09 14:20 ET. Full findings, tables and sources:
[`../research/06-closest-prior-work.md`](../research/06-closest-prior-work.md).

- **The gap is real but narrow.** No paper found formally verifies LLM-written C/C++ performance
  rewrites against reusable rewrite contracts proven once. None formally verifies an LLM-written
  accelerator offload. Each piece has precedent, so claim the combination and the subject (DX100
  offload), never "first".
- **Closest three:**
  - Trivet (arXiv 2026): an LLM writes Lean proofs when Alive2 times out or is bounded. Integer
    IR only, no memory.
  - LLMLift (NeurIPS 2024): LLM-written invariants checked by SMT. Per program, side-effect-free
    code lifted into a DSL.
  - ProofWright (arXiv 2025/26): the LLM annotates LLM-written CUDA kernels for VerCors/Rocq and
    also writes the specification. Full equivalence for 14% of kernels.
- **Verify-the-LLM-output at IR level is taken** (LLM-Vectorizer, CoV, LLM-VeriOpt). All use
  Alive2 and stay within bounds. None uses LLM proof hints or a reusable spec.
- **Accelerator work with LLMs is tests only** (Autocomp, KernelCraft, QiMeng-Xpiler). This is the
  least crowded part of the claim.
- **Two decisions from 01 to refine:**
  - Trivet already uses a "no `sorry`/`admit`, statement unchanged" gate. Cite it; our guard is
    its C/C++ counterpart.
  - LPG could not prove generalized rules for all bitwidths and fell back to checking each width.
    So ticket 10 should apply the two proven levels to contracts as well, not only to candidates.
