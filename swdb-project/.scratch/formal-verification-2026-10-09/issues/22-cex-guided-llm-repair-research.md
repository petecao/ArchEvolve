# 22 — Which LLM repair loops driven by model-checker counterexamples exist, and how close are they to ours?

Created: 2026-10-13 17:02 ET
**Type:** research
**Status:** resolved
**Blocked by:** None — can start immediately
**Map:** `../map.md`

## Question

13 named ESBMC-AI (Tihanyi et al., 2023; citation not checked) as prior work for
**counterexample-guided repair** (glossary). Find and check:

- LLM repair loops for C or C++ driven by bounded-model-checker counterexamples (ESBMC-AI and its
  successors, 2023-2026): what they repair (memory safety, overflow, data races), what the LLM
  sees, and how a repair is validated.
- Whether any of them repairs data races or accelerator hazards, or repairs against a functional or
  relational specification instead of a safety property.
- How ours differs: the counterexample comes from the bounded verifier on a proof unit checked
  against a rewrite contract; the repaired candidate artifact must certify and be proven again;
  proof hints never change code (13).

Output: `../research/22-cex-guided-llm-repair.md`, every citation checked (map Notes). Feeds
positioning (06) and ticket 23's baselines.

## Comments

- 2026-10-13 17:02 ET: graduated from the map's "Evaluation plan" fog (13's "check the ESBMC-AI
  citation" item).

## Answer

2026-10-13 17:32 ET. Resolved by a research subagent; findings in
[`../research/22-cex-guided-llm-repair.md`](../research/22-cex-guided-llm-repair.md) (15 works,
each opened at its source). Spot-checked in the main session: the ESBMC-AI DOI in Crossref and the
T-LLM Compiler arXiv page match.

1. **ESBMC-AI citation fixed:** cite Tihanyi, Charalambous, Jain, Ferrag, Cordeiro, AST 2025,
   pp. 136-147, DOI 10.1109/AST66626.2025.00020 (preprint arXiv:2305.14752). It repairs C safety
   violations; a repair counts when ESBMC passes again at `--unwind 1` with a 10 s timeout; behavior
   checked by hand only.
2. **Closest new work:** T-LLM Compiler (arXiv:2608.14953, August 2026): LLM performance rewrites of
   C loops, bounded CBMC equivalence with the original (`--unwind 20`), verifier feedback to the LLM,
   plus an LLM judge. Its CBMC filter accepted 33.8% of wrong rewrites. Not in research 06.
3. **Relational repair loops exist** (T-LLM, VERT, LPO), each against a per-program reference;
   none against a reusable contract proven once.
4. **Races:** LLM repair from a formal counterexample exists for Java (ConFixAgent, JPF) and Go
   (DR.FIX, ThreadSanitizer), not for C/C++. Without an LLM: LLOR (OpenMP) and GPURepair (CUDA).
   **Accelerator hazards:** none found.
5. **Does the counterexample help?** Mixed evidence: ESBMC-AI says yes; its 2024 follow-up and
   FLOURINE found no gain or a loss.
6. **The term "counterexample-guided repair" is already used** (Orvalho et al., AAAI 2025; AuthFix,
   ASE 2025). Cite them where the glossary term first appears in the paper.

**Inputs passed on:**
- **Ticket 23:** five baselines that mirror published loops (safety-only repair; per-pair bounded
  equivalence; no counterexample or ask again; race repair without an LLM; ThreadSanitizer-driven
  repair) and the metrics this literature reports (repair rate after 1 and k rounds, false
  acceptance found by an independent check, patch size, copies of the reference).
- **Tickets 23 and 25:** a repair may simply revert to the baseline implementation (Orvalho et al.
  saw models copy the reference). Decide whether that counts and measure how often it happens.
- **Positioning (06):** add T-LLM Compiler to the closest-work table when the spec is written.
