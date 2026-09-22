# Fail Fast

Copied 2026-09-22 from the owner's MemAcc rules.

Maximize learning per unit cost: surface failure as early and cheaply as possible.

1. **Cheapest falsifying test first.** Before any expensive step (long run, big
   build, large refactor, campaign), find the cheapest check that could kill the
   idea — and run that first.
2. **Pilot end to end before scaling up.** A minimal version must traverse the
   full pipeline, and its outputs must be opened and checked.
3. **Validate the instrument before trusting the measurement.** New/changed
   checks, metrics, or scripts need a passing positive control and a failing
   negative control.
4. **Stage: pilot → one full case → full scale.** Stop and root-cause at the
   first unexplained failure.
5. **Fail loud and early.** Don't swallow, defer, or batch errors; a wrong result
   found late costs far more than a crash found now.
