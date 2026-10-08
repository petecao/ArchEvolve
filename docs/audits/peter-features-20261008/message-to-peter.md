Hey Peter, I audited v1.2 against the hybrid sketch. For the next handoff, could you add:

- Runtime/cycle share tied to the existing statement or IR regions, with the ROI/denominator and any unattributed remainder.
- Per-level frontier size, edges visited and a degree summary, tied to the same input/root/trial.
- Exact build/run identity and raw profiling references.

We can reuse Yanru's statement mapping. I also found a few helper issues around symbol/threshold filtering, locality labels and the old schema target—details are in the [audit](https://github.com/petecao/ArchEvolve/blob/main/docs/audits/peter-features-20261008/README.md). Unknown values are fine; no accelerator measurements needed from your side.
