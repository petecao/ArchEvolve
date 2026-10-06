# ArchEvolve mode estimates speed; it never runs or cites gem5

Date: 2026-10-06 ET
Status: proposed (direction decided by Yan-Ru on 2026-10-06 after Scott's feedback; the spec's agent
defaults D8–D15 confirmed by Yan-Ru the same day)

Narrows [ADR 0008](0008-target-bound-correctness.md) for ArchEvolve mode. Clarifies
[ADR 0009](0009-two-modes-same-evaluator.md): both modes still share the evaluator; only the stage
that supplies speed differs.

ArchEvolve's evaluator is analytic: the team has no simulator, and Scott asked that SWDB estimate
performance with compiler analysis, LLM agents or a hybrid instead of running gem5. So in ArchEvolve
mode, correctness still executes and speed is estimated. For a hardware target that cannot run the
code, such as DX100, the speed number comes from the estimator, and correctness is
functional-target correctness: the kernel's correctness check and certification on the strict layer
of the functional model. ArchEvolve mode runs no gem5 job and cites no gem5 number, including for
calibrating or validating the estimator. Native timing on a real CPU stays allowed, because it is
not a simulation, and it is the estimator's CPU validation.

Extensa mode, Yan-Ru's research, keeps gem5 and the functional model. Estimates enter it first as
paired estimates beside gem5, and screening comes only after their agreement with gem5 is measured.
An estimator tuned with Extensa's gem5 data is a research variant and never enters a team protocol.

The estimator is general, not a DX100 model: it composes mechanism models (one hardware behavior
each, such as reordering requests within a window) according to each target's description, and
holds no kernel-specific or target-specific code. Accelerator memory behavior is estimated by
counting over the real address stream (for example, distinct DRAM rows per reorder window), not by
simulating time.

## Considered Options

- **Keep gem5 in ArchEvolve mode:** rejected by Scott; the team evaluator has no simulator.
- **Compiler trace plus a DRAM simulator (Aladdin-style):** its memory side is still a simulator.
- **A hand-written model per target:** fast to start, but every new accelerator would need new code,
  and ArchEvolve explores many targets.
- **LLM prediction alone:** weak as a numeric predictor (64% roofline classification from source,
  Bolet et al., HPDC AI4Sys 2025); LLMs fill only parameters the analytic model lacks.

## Consequences

- ArchEvolve-mode results for DX100 are estimates, labeled with basis estimated, and DX100 code
  there is never called correct on its hardware target.
- Estimator error is known for CPU targets (against native timing) but only loosely for DX100
  (against the DX100 paper's reported numbers) until Extensa's paired estimates are studied.
