"""LANL table group: `hardware_profiles`, `run_configs`, `performance_runs`,
`performance_metrics`, and the `swdb_estimates` extension (LANL-shaped-db ticket 04, spec D4).
Created 2026-10-11 ET. See `swdb/lanl.py` for what a group module provides.

Only measurements on real machines reach LANL's performance tables:

- `hardware_profiles`: one row per machine record. Hardware targets (a modeled DX100) are not
  machines and are left out. `cores` counts physical cores (sockets x cores per socket);
  `memory_gb` is the record's `memory_bytes` in GiB (2**30 bytes), unrounded.
- `performance_runs`: one row per `timing[]` entry of a profile, that is one benchmark process
  at one thread count. `elapsed_seconds` is the entry's median time per trial; no record states
  a throughput, so `throughput_value` is NULL.
- `run_configs`: what such a run ran with. `parameters_json` holds the input (and its generator
  arguments), threads, trials, compiler, flags and OpenMP binding; `git_commit` is the
  application's source revision (`build.application_commit`). Runs with identical
  parameters, commit and variant share one row.
- `performance_metrics`: profile metrics with basis `measured` and a numeric value, each on the
  run with its thread count. Simulated (cachegrind), inferred and unknown metrics, histograms,
  and metrics that name no single run stay in `swdb_metrics` only.
- `swdb_estimates` (extension): one row per estimate record (spec D4). `kernel_variant_id` is
  the estimated implementation; for a candidate subject it is NULL and `base_kernel_variant_id`
  holds the implementation the candidate rewrites (review fix, 2026-10-11 ET). Estimates never
  reach the LANL tables.
"""

import json

ORDER = 40

SCHEMA = """
CREATE TABLE hardware_profiles (id INTEGER PRIMARY KEY, cpu_model TEXT, cores INTEGER, memory_gb REAL);
CREATE TABLE run_configs (id INTEGER PRIMARY KEY, label TEXT, parameters_json TEXT, git_commit TEXT,
    kernel_variant_id INTEGER REFERENCES kernel_variants(id));
CREATE TABLE performance_runs (id INTEGER PRIMARY KEY, elapsed_seconds REAL, throughput_value REAL,
    hardware_profile_id INTEGER REFERENCES hardware_profiles(id), run_config_id INTEGER REFERENCES run_configs(id),
    kernel_variant_id INTEGER REFERENCES kernel_variants(id));
CREATE TABLE performance_metrics (id INTEGER PRIMARY KEY, metric_name TEXT, metric_value REAL,
    performance_run_id INTEGER REFERENCES performance_runs(id));
CREATE TABLE swdb_estimates (id TEXT PRIMARY KEY REFERENCES swdb_records(id),
    kernel_variant_id INTEGER REFERENCES kernel_variants(id),
    base_kernel_variant_id INTEGER REFERENCES kernel_variants(id), subject_kind TEXT, subject_id TEXT, target TEXT,
    input TEXT, threads INTEGER, seconds REAL, ratio REAL, verdict TEXT, estimator_version TEXT);
"""

_LINK = "link column not on the slide, named by the slide's <table singular>_id pattern; "
GUESSED = [
    ("run_configs", "kernel_variant_id", _LINK + "the implementation the profile ran (kernel_variants.id)"),
    ("performance_runs", "hardware_profile_id", _LINK + "the machine the profile ran on (hardware_profiles.id)"),
    ("performance_runs", "run_config_id", _LINK + "what the run ran with (run_configs.id)"),
    ("performance_runs", "kernel_variant_id", _LINK + "the implementation the profile ran (kernel_variants.id)"),
    ("performance_metrics", "performance_run_id", _LINK + "the run at the metric's thread count (performance_runs.id)"),
]


def fill(rows, store):
    machines = _hardware_profiles(rows, store)
    _runs(rows, store, machines)
    _estimates(rows, store)


def _estimates(rows, store):
    """One `swdb_estimates` row per estimate record. `kernel_variant_id` is the estimated
    implementation, set only when the subject is one. A candidate subject is a rewrite, not the
    implementation it names: that implementation is its base (`base_kernel_variant_id`), so an
    estimate of a candidate never reads as an estimate of the baseline. Anything else is NULL."""
    for record in sorted(store.of_kind("estimate"), key=lambda r: r.id):
        estimate = record.data
        subject = estimate.get("subject") or {}
        implementation = subject.get("id") if subject.get("kind") == "implementation" else None
        base = None
        if subject.get("kind") == "candidate":
            base = (store.get(subject.get("id"), "candidate") or {}).get("implementation")
        rows.con.execute("INSERT INTO swdb_estimates VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (
            record.id, rows.id_of("kernel_variants", implementation), rows.id_of("kernel_variants", base),
            subject.get("kind"), subject.get("id"),
            estimate.get("target"), estimate.get("input"), estimate.get("threads"), estimate.get("seconds"),
            estimate.get("ratio"), estimate.get("verdict"), estimate.get("estimator_version")))


def _hardware_profiles(rows, store):
    """Insert one row per machine record; return {machine ID: hardware_profiles.id}."""
    ids = {}
    for record in sorted(store.of_kind("machine"), key=lambda r: r.id):
        machine = record.data
        cpu = machine.get("cpu") or {}
        sockets, per_socket = cpu.get("sockets"), cpu.get("cores_per_socket")
        memory = machine.get("memory_bytes")
        ids[record.id] = rows.add("hardware_profiles", {
            "cpu_model": cpu.get("model"),
            "cores": sockets * per_socket if sockets is not None and per_socket is not None else None,
            "memory_gb": memory / 2**30 if memory is not None else None}, record.id)
    return ids


def _runs(rows, store, machines):
    configs = {}   # (variant, parameters, commit) -> run_configs.id
    for record in sorted(store.of_kind("profile"), key=lambda r: r.id):
        profile = record.data
        build, environment = profile.get("build") or {}, profile.get("environment") or {}
        variant = rows.id_of("kernel_variants", profile.get("implementation"))
        commit = build.get("application_commit")
        arguments = ((store.get(profile.get("input"), "input") or {}).get("generator") or {}).get("arguments")
        runs = {}   # threads -> [performance_runs.id] of this profile
        for i, timing in enumerate(profile.get("timing") or []):
            field = f"timing[{i}]"
            parameters = json.dumps({
                "input": profile.get("input"), "input_arguments": arguments,
                "threads": timing.get("threads"), "trials": timing.get("trials"),
                "compiler": build.get("compiler"), "compiler_version": build.get("compiler_version"),
                "flags": build.get("flags"), "omp_places": environment.get("omp_places"),
                "omp_proc_bind": environment.get("omp_proc_bind"), "binding": environment.get("binding")},
                sort_keys=True)
            key = (variant, parameters, commit)
            if key in configs:
                rows.origin("run_configs", configs[key], record.id, field)
            else:
                configs[key] = rows.add("run_configs", {
                    "label": f"{profile.get('implementation')} on {profile.get('input')}, "
                             f"{timing.get('threads')} threads",
                    "parameters_json": parameters, "git_commit": commit, "kernel_variant_id": variant},
                    record.id, field)
            run = rows.add("performance_runs", {
                "elapsed_seconds": timing.get("median_s"), "throughput_value": None,
                "hardware_profile_id": machines.get(profile.get("machine")), "run_config_id": configs[key],
                "kernel_variant_id": variant}, record.id, field)
            runs.setdefault(timing.get("threads"), []).append(run)
        _metrics(rows, record, runs)


def _metrics(rows, record, runs):
    """Measured, numeric metrics of one profile, each on the run with its thread count.
    `runs`: {threads: [performance_runs.id]}; a metric whose thread count names no single run
    (none stated, or no or several timing entries) states no run and is left out."""
    for i, metric in enumerate(record.data.get("metrics") or []):
        value = metric.get("value")
        if metric.get("basis") != "measured" or not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        run = runs.get(metric.get("threads"), [])
        if len(run) == 1:
            rows.add("performance_metrics", {"metric_name": metric.get("name"), "metric_value": value,
                                             "performance_run_id": run[0]}, record.id, f"metrics[{i}]")
