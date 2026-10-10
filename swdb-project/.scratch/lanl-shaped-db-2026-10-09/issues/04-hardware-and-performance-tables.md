# 04 — Hardware and performance tables, measured results only

Created: 2026-10-09
**Type:** slice
**Status:** ready-for-agent
**Blocked by:** 02
**Spec:** `../spec.md`

**What to build:** the build fills `hardware_profiles` (`cpu_model`, `cores`, `memory_gb`) from
machine records (real machines only; hardware targets excluded), `run_configs` (`label`,
`parameters_json`, `git_commit`) from what measured profiles ran with, `performance_runs`
(`elapsed_seconds`, `throughput_value`) from profiles with measured timing, and
`performance_metrics` (`metric_name`, `metric_value`) from profile metrics with basis `measured`.
Guessed link columns (`performance_runs.hardware_profile_id`, `.run_config_id`,
`.kernel_variant_id`; `performance_metrics.performance_run_id`; `run_configs.kernel_variant_id`)
are added and listed in `swdb_guessed_columns`. A new `swdb_estimates` table links each estimate
record to its kernel variant. Can run in parallel with 03 and 05.

About 3 h.

- [ ] The four tables have exactly the slide's columns plus `id` and the listed guessed columns
- [ ] With a fixture estimate and a fixture measured profile, only the measured one reaches `performance_runs`
- [ ] Simulated metrics (cachegrind) and estimated metrics never appear in `performance_metrics`
- [ ] A hardware target (for example DX100) never appears in `hardware_profiles`
- [ ] Each estimate appears in `swdb_estimates` linked to its kernel variant
- [ ] Origins, foreign-key and separability checks stay clean
