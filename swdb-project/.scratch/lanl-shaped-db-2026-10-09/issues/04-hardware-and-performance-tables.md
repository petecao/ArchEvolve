# 04 — Hardware and performance tables, measured results only

Created: 2026-10-09
**Type:** slice
**Status:** resolved
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

## Answer

Resolved 2026-10-11 21:40 ET on `lanl-shaped-db` (commit 8093fe52, merge 51ce1ac7).
Built in `swdb/lanl_performance.py`. `hardware_profiles`: one row per machine record (never a
hardware target); `cores` = sockets × cores_per_socket (physical), `memory_gb` = bytes / 2^30.
`performance_runs`: one row per profile `timing[]` entry, `elapsed_seconds` = median per-trial
time, `throughput_value` NULL (no record states one). `run_configs`: distinct (variant,
parameters, commit), `git_commit` = `build.application_commit` or NULL. `performance_metrics`:
numeric `measured` metrics tied to exactly one run's thread count; simulated, estimated,
histogram and run-less metrics stay in `swdb_metrics`. `swdb_estimates`: one row per estimate,
linked to the stated implementation (for a candidate subject, the implementation the candidate
names), else NULL. Five guessed link columns listed. Evaluation timings are not included (spec
names profiles only; possible follow-up). Tests: `tests/test_lanl_performance.py` (22 pass).
