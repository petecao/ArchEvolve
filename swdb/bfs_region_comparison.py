"""Package-backed diagnostic comparisons. Updated 2026-09-29.

Native thread CPU and simulated thread elapsed quantities remain separate from BFS wall time.

Baseline-not-invoked rule (2026-09-29, root decision for T17): a frozen simulated
diagnostic pair whose baseline region has an exactly zero raw-verified invocation
count and zero inclusive/exclusive time in every replay cell does not reject the
comparison. It is reported as ``state: baseline_not_invoked`` with the candidate's
invocations and durations, no ``duration_ratio``, and ``gain_claim: false``; the
primary BFS ROI decision is unaffected. Every other invalid count or duration is
still rejected, including a zero-invocation candidate region and a baseline that
is zero in only some cells. Native diagnostic pairs keep strict rejection.
"""
import hashlib
import math
import socket
import statistics
from pathlib import Path

from swdb import artifacts
from swdb.bfs_protocol import _fail, _get, _positive, _integer, _geomean, _timestamp, _check_verifier_identity


def _raw(reference, host, *, verify_hash=True):
    path = Path(reference["path"])
    if not path.exists():
        remote = host and host != socket.gethostname().split(".")[0] and str(path).startswith(("/data/", "/data1/"))
        _fail(remote, "diagnostic raw artifact is unavailable locally")
        return None  # Metadata retrieval never pretends to recheck remote raw bytes.
    _fail(path.is_file() and not path.is_symlink() and (not verify_hash or artifacts.file_hash(path) == reference["sha256"]),
          "diagnostic raw artifact changed")
    return path


def _associated_profile(store, primary, package_id, pair, role):
    from swdb import profile_package
    package = _get(store, package_id, "profile_package")
    profile_package.verify(package)
    kind = primary["evidence_kind"]
    _fail("package_version" in package and package.get("evaluation") == primary["id"]
          and package.get("completeness") == ("complete" if kind == "execution" else "fixture")
          and package.get("evidence", {}).get("classification") == kind,
          "selected diagnostic package is incomplete or has another primary/evidence classification")
    profile = _get(store, package.get("region_profile"), "region_profile")
    _fail(profile.get("request", {}).get("fixture") is not True or kind == "contract_fixture",
          "fixture profile cannot support real execution")
    candidate = _get(store, primary["candidate"], "candidate")
    evidence = package["evidence"]
    _fail(evidence.get("evaluation_sha256") == artifacts.digest(primary)
          and evidence.get("region_profile_sha256") == artifacts.digest(profile), "selected diagnostic package evidence changed")
    _fail(not profile_package._profile_check(profile, primary, candidate), "diagnostic profile has incompatible primary context")
    _fail(profile_package._query_evidence(store, package)["state"] != "invalid", "diagnostic package memory evidence is invalid")
    _fail(evidence.get("diagnostic_executions") == profile.get("executions")
          and evidence.get("discovery") == profile.get("discovery")
          and evidence.get('diagnostic_build', {}) == profile.get('build', {}), "package collector evidence differs from its profile")
    chosen = [row for row in profile.get("regions", []) if row.get("id") == pair[role]]
    assembled = [row for row in package.get("regions", []) if row.get("id") == pair[role]]
    _fail(len(chosen) == len(assembled) == 1, "selected diagnostic region is missing or ambiguous")
    row, retained = chosen[0], assembled[0]
    _fail(all(retained.get(key) == row.get(key) for key in
              ("id", "kind", "path", "insertion_range", "metrics", "scope", "attribution", "basis", "artifact_sha256",
               "source_artifact_sha256", "text", "source_sha256", "byte_range")),
          "package region differs from its collector observation")
    _fail(row.get("source_artifact_sha256") == candidate["artifact"]["sha256"]
          and hashlib.sha256(row.get("text", "").encode()).hexdigest() == row.get("source_sha256"), "diagnostic region source identity changed")
    return candidate, package, profile, row


def _sample(store, primary, package_id, pair, role):
    from swdb import profile_package
    from swdb.dx100_profile import _trial
    candidate, package, profile, row = _associated_profile(store, primary, package_id, pair, role)
    kind = primary["evidence_kind"]
    timing = primary.get("timing", [])
    _fail(len(timing) == 1, "regional package must identify one primary replay")
    cell = {key: timing[0][key] for key in ("source", "source_position", "repetition")}
    runs = [run for run in profile.get("executions", []) if run.get("kind") == "regions"]
    _fail(len(runs) == 1 and all(type(runs[0].get(key)) is int and runs[0][key] == value for key, value in cell.items()),
          "diagnostic region observations differ from the primary source/repetition cell")
    run = runs[0]
    diagnostic = _get(store, run.get("evaluation"), "evaluation")
    _fail(_trial(diagnostic, require_explicit=True) == _trial(primary, require_explicit=True) == cell,
          'diagnostic actual source/repetition trial differs from its retained profile cell')
    _fail(diagnostic.get("outcome", {}).get("state") == "complete" and diagnostic.get("correctness", {}).get("state") == "passed"
          and run.get("correctness") == diagnostic["correctness"] and diagnostic.get("evidence_kind") == kind
          and run.get("evidence_kind") == kind and diagnostic.get("candidate") == candidate["id"]
          and profile_package._context(diagnostic) == profile_package._context(primary), "diagnostic replay lacks compatible independent correctness")
    _fail(diagnostic.get("request", {}).get("fixture") is not True or kind == "contract_fixture", "fixture diagnostic cannot support real execution")
    build = _get(store, diagnostic.get("context", {}).get("candidate_build"), "evaluation")
    definition = build.get("context", {}).get("diagnostic", {})
    _fail(build.get("request", {}).get("fixture") is not True or kind == "contract_fixture",
          "fixture diagnostic compilation cannot support real execution")
    binary = diagnostic.get("build", {})
    _fail(build.get("outcome", {}).get("state") == "complete" and build["outcome"].get("stage") == "candidate_build"
          and build.get("candidate") == candidate["id"] and build.get("evidence_kind") == kind
          and build.get("context", {}).get("candidate_sha256") == candidate["artifact"]["sha256"]
          and build.get("build", {}).get("binary_sha256") == binary.get("binary_sha256")
          and row.get("artifact_sha256") == run.get("binary_sha256") == binary.get("binary_sha256"),
          "diagnostic region lacks its exact source/binary compilation receipt")
    _fail(all(binary.get(key) == primary["build"].get(key) for key in ("model_build", "simulator", "simulator_sha256")),
          "diagnostic replay uses another simulator/model build")
    collector = pair["collector"]
    discovery = definition.get("discovery", {})
    _fail(profile.get("discovery") == discovery and all(discovery.get(key) == collector[key]
              for key in ("backend", "collector", "library_sha256", "pass_sha256"))
          and definition.get("runtime", {}).get("sha256") == collector["runtime_sha256"],
          "diagnostic collector differs from its frozen identity")
    originals = [item for item in definition.get("regions", []) if item.get("id") == row["id"]]
    _fail(len(originals) == 1 and all(originals[0].get(key) == row.get(key) for key in
              ("text", "source_sha256", "byte_range", "source_artifact_sha256")), "selected region differs from compiler discovery")
    attribution = row.get("attribution", {})
    _fail(row.get("basis") == "simulated" and row.get("scope") ==
          "accumulated simulated elapsed per executing thread within " + primary["context"]["roi"]
          and attribution.get("clock") == "m5_rpns" and attribution.get("whole_lexical_region") is True
          and attribution.get("quantity") == definition.get("quantity")
          and attribution.get("inclusive") is True
          and attribution.get("exclusive") == "nested guarded intervals subtracted on the same thread",
          "diagnostic region timing scope or attribution differs")
    log = {"path": run["region_output"], "sha256": run["region_output_sha256"]}
    stages = [stage for stage in diagnostic.get("stages", []) if stage.get("stage") == "simulation"]
    _fail(len(stages) == 1 and log == {"path": stages[0].get("log"), "sha256": stages[0].get("log_sha256")}
          and run.get("output") == log["path"] and run.get("output_sha256") == log["sha256"],
          "diagnostic region report is not bound to its simulation output")
    _fail(_timestamp(stages[0].get("started")) >= _timestamp(primary["context"]["protocol_binding"]["frozen_at"]),
          "diagnostic region observation predates protocol freeze")
    checks = diagnostic["correctness"].get("checks", [])
    _check_verifier_identity(diagnostic, store)
    _fail(diagnostic.get("context", {}).get("verifier") == primary["context"].get("verifier"),
          "diagnostic correctness verifier differs from primary")
    _fail(len(checks) == 1 and checks[0].get("passed") is True
          and all(type(checks[0].get(key)) is int and checks[0][key] == value for key, value in cell.items())
          and checks[0].get("binary_sha256") == binary["binary_sha256"]
          and checks[0].get("graph_sha256") == primary["context"]["workload"]["canonical_sha256"]
          and checks[0].get("output_sha256") == log["sha256"], "diagnostic correctness is not bound to the reported graph/source/binary")
    host = diagnostic.get("context", {}).get("host")
    raw = _raw(log, host, verify_hash=False)
    for reference in (definition["runtime"], definition["instrumented_source"],
                      {"path": binary["binary"], "sha256": binary["binary_sha256"]}):
        _raw(reference, host)
    metrics = row["metrics"]
    # Only a baseline region may record zero invocations (baseline_not_invoked);
    # then both durations must be exactly zero. Candidates stay strictly >= 1.
    invocations = _integer(metrics.get("invocations"), "diagnostic invocation count", 0 if role == "baseline" else 1)
    not_invoked = invocations == 0
    if not_invoked:
        inclusive, exclusive = metrics.get("inclusive_simulated_seconds"), metrics.get("exclusive_simulated_seconds")
        _fail(type(inclusive) in (int, float) and type(exclusive) in (int, float) and inclusive == 0 and exclusive == 0,
              "diagnostic region with zero invocations must record zero inclusive and exclusive seconds")
    else:
        inclusive = _positive(metrics.get("inclusive_simulated_seconds"), "diagnostic inclusive seconds")
        exclusive = metrics.get("exclusive_simulated_seconds")
        _fail(type(exclusive) in (int, float) and math.isfinite(exclusive) and 0 <= exclusive <= inclusive,
              "diagnostic exclusive duration is invalid or exceeds inclusive duration")
    if raw:
        from swdb.dx100_diagnostic import counters
        observed, digest = counters(raw, len(definition["regions"]), return_sha256=True)
        _fail(digest == log["sha256"], "diagnostic raw report changed")
        values = observed[definition["regions"].index(originals[0])]
        _fail(values["invocations"] == invocations and values["inclusive_ns"] / 1e9 == inclusive
              and values["exclusive_ns"] / 1e9 == exclusive, "diagnostic region values differ from the raw report")
    duration = inclusive if pair["attribution"] == "inclusive" else exclusive
    if not_invoked:
        duration = None
    else:
        _positive(duration, "selected diagnostic duration")
        if pair["scope"] == "per_invocation": duration /= invocations
    return {**cell, "duration_s": duration, "invocations": invocations, "primary_evaluation": primary["id"],
            "primary_binary_sha256": primary["build"]["binary_sha256"], "diagnostic_evaluation": diagnostic["id"],
            "diagnostic_evaluation_sha256": artifacts.digest(diagnostic), "diagnostic_build": build["id"],
            "diagnostic_build_sha256": artifacts.digest(build), "diagnostic_binary_sha256": binary["binary_sha256"],
            "profile_package": package["id"], "package_sha256": package["identity_sha256"],
            "region_profile": profile["id"], "region_profile_sha256": artifacts.digest(profile), "raw_report": log,
            "source_sha256": row["source_sha256"], "source_artifact_sha256": candidate["artifact"]["sha256"],
            "quantity": definition["quantity"], "timing_scope": row["scope"], "attribution": attribution}


def _native_samples(store, primary, package_id, pair, role):
    from swdb import bfs_discovery, bfs_native, bfs_profiling, profile_package
    from swdb.cli import Failure

    candidate, package, profile, row = _associated_profile(store, primary, package_id, pair, role)
    context, build = profile['context'], profile.get('build', {})
    if 'native_runtime' in primary.get('build', {}):
        _fail(build.get('native_runtime') == primary['build']['native_runtime'],
              'native diagnostic runtime inputs differ from primary')
    _fail(primary['context'].get('basis') == 'measured' and not primary.get('component_evaluations')
          and primary['context'].get('roi') == bfs_native.ROI, 'native diagnostic requires a native complete-call primary')
    _fail(profile.get('outcome', {}).get('state') in {'partial', 'complete'}
          and context.get('primary_evaluation') == primary['id']
          and profile.get('request', {}).get('evaluation') == primary['id'], 'native profile association is incomplete')
    _fail(all(build.get(key) == primary['build'].get(key) for key in ('compiler', 'compiler_version', 'flags'))
          and all(context.get(key) == primary['context'].get(key)
                  for key in ('instrumentation', 'verifier', 'verifier_sha256', 'machine_sha256', 'host')),
          'native diagnostic source build or checker differs from primary')
    collector = pair['collector']
    _fail(all(profile.get('discovery', {}).get(key) == collector[key]
              for key in ('backend', 'library_sha256', 'pass_sha256', 'collector_sha256'))
          and build.get('runtime_sha256') == collector['runtime_sha256'], 'native collector differs from its frozen identity')
    repetitions = pair['diagnostic_repetitions']
    _fail(type(context.get('repetitions')) is int and context['repetitions'] == repetitions
          and type(profile['request'].get('repetitions', 1)) is int
          and profile['request'].get('repetitions', 1) == repetitions, 'native diagnostic repetition policy differs')
    _fail(row.get('basis') == 'measured' and row.get('scope') == 'accumulated within diagnostic complete-call ROI'
          and context.get('timing_basis') == 'diagnostic accumulated thread CPU seconds; primary ROI wall timing remains in evaluation'
          and context.get('overhead_treatment') == 'scope instrumentation overhead is included; no synthetic subtraction or gain claim',
          'native diagnostic CPU timing scope differs')

    def local(reference):
        path = _raw(reference, context.get('host'))
        _fail(path is not None, 'native region comparison requires locally available raw per-trial evidence')
        return path

    binary = profile.get('artifacts', {}).get('region_binary', {})
    _fail(profile.get('artifacts', {}).get('primary_binary_sha256') == primary['build']['binary_sha256']
          and row.get('artifact_sha256') == binary.get('sha256'), 'native diagnostic binary binding differs')
    local(binary)
    directory = Path(build['directory'])
    for filename, field in (('runtime.hpp', 'runtime_sha256'), ('regions_driver.cc', 'wrapper_sha256'),
                            ('instrumented_bfs.cc', 'instrumented_source_sha256')):
        local({'path': str(directory / filename), 'sha256': build[field]})
    root = artifacts.verify(candidate['artifact'])
    regions = profile['regions']
    _fail(0 < len(regions) <= 10000 and len({item['id'] for item in regions}) == len(regions),
          'native diagnostic region inventory is invalid')
    for original in regions:
        profile_package._region(original, root)
        extent = original.get('insertion_range')
        _fail(isinstance(extent, list) and len(extent) == 2 and all(type(value) is int for value in extent)
              and original['byte_range'][0] <= extent[0] <= extent[1] <= original['byte_range'][1],
              'native compiler instrumentation extent differs from source region')
    _fail(len({item['path'] for item in regions}) == 1, 'native diagnostic inventory spans multiple source files')
    instrumented = bfs_discovery.instrument(root / regions[0]['path'], regions)
    _fail(hashlib.sha256(instrumented).hexdigest() == build['instrumented_source_sha256'],
          'native source-to-counter instrumentation mapping differs')
    build_stages = [stage for stage in profile.get('stages', []) if stage.get('stage') == 'region_build']
    _fail(len(build_stages) == 1 and build_stages[0].get('state') == 'complete'
          and build_stages[0].get('returncode') == 0 and build_stages[0].get('command') == build.get('command'),
          'native diagnostic compilation receipt differs')
    command = build.get('command', [])
    _fail(command[:1 + len(build['flags'])] == [build['compiler'], *build['flags']]
          and command[:-3] == primary['build'].get('command', [])[:-3]
          and command[-3:] == [str(directory / 'regions_driver.cc'), '-o', binary['path']],
          'native diagnostic compilation command differs')
    graph_reference = {'path': primary['context']['workload']['canonical_path'],
                       'sha256': primary['context']['workload']['canonical_file_sha256']}
    graph, facts = bfs_native.read_canonical_graph(local(graph_reference))
    _fail(facts['canonical_sha256'] == context['workload']['canonical_sha256'], 'native diagnostic graph identity differs')
    sources = context['sources']
    expected = {(position, source, repetition) for position, source in enumerate(sources) for repetition in range(repetitions)}
    primary_cells = {(item['source_position'], item['source'], item['repetition']) for item in primary['timing']}
    _fail(expected <= primary_cells, 'native diagnostic cells are outside the primary grid')
    runs = [run for run in profile['executions'] if run.get('kind') == 'regions']
    stages = [stage for stage in profile['stages'] if stage.get('stage') == 'region_execution']
    _fail(len(runs) == len(stages) == len(expected), 'native diagnostic sample grid is incomplete or duplicated')
    samples, seen, outputs = [], set(), set()
    totals = {'inclusive_thread_cpu_seconds': 0.0, 'exclusive_thread_cpu_seconds': 0.0, 'invocations': 0}
    region_index = regions.index(row)
    for run in runs:
        cell = {key: _integer(run.get(key), 'native diagnostic ' + key, 0)
                for key in ('source_position', 'source', 'repetition')}
        key = (cell['source_position'], cell['source'], cell['repetition'])
        _fail(key in expected and key not in seen, 'native diagnostic source/repetition cell differs')
        seen.add(key)
        _fail(run.get('binary_sha256') == binary['sha256'], 'native diagnostic run binary differs')
        output = {'path': run['output'], 'sha256': run['output_sha256']}
        report = {'path': run['region_output'], 'sha256': run['region_output_sha256']}
        _fail(report['path'] == output['path'] + '.regions.json' and output['path'] not in outputs,
              'native diagnostic raw report is reused or disconnected from its parent output')
        outputs.add(output['path'])
        matching = [stage for stage in stages if stage.get('command') ==
                    [binary['path'], graph_reference['path'], str(cell['source']), output['path']]]
        _fail(len(matching) == 1 and matching[0].get('state') == 'complete' and matching[0].get('returncode') == 0
              and _timestamp(matching[0].get('started')) >= _timestamp(primary['context']['protocol_binding']['frozen_at']),
              'native diagnostic execution receipt is missing, failed, or predates freeze')
        try:
            checked = bfs_profiling._trial_output(local(output), graph, cell['source'], context['threads'])
            observed, digest = bfs_profiling._region_observations(local(report), regions)
        except bfs_native.StageFailure as exc:
            raise Failure('native diagnostic raw observation is invalid: ' + str(exc)) from None
        _fail(checked == {key: run.get(key) for key in checked} and digest == report['sha256'],
              'native diagnostic correctness or raw report identity differs')
        values = observed[region_index]
        for field in ('inclusive', 'exclusive'):
            totals[field + '_thread_cpu_seconds'] += values[field + '_ns'] / 1e9
        totals['invocations'] += values['invocations']
        invocations = _integer(values['invocations'], 'selected native diagnostic invocation count')
        seconds = _positive(values[pair['attribution'] + '_ns'] / 1e9, 'selected native diagnostic CPU duration')
        if pair['scope'] == 'per_invocation': seconds /= invocations
        samples.append({**cell, 'duration_s': seconds, 'invocations': invocations,
            'primary_evaluation': primary['id'], 'primary_binary_sha256': primary['build']['binary_sha256'],
            'profile_package': package['id'], 'package_sha256': package['identity_sha256'],
            'region_profile': profile['id'], 'region_profile_sha256': artifacts.digest(profile),
            'diagnostic_binary_sha256': binary['sha256'], 'diagnostic_build_sha256': artifacts.digest(build),
            'raw_report': report, 'parent_output': output, 'correctness': checked['correctness'],
            'source_sha256': row['source_sha256'], 'source_artifact_sha256': candidate['artifact']['sha256'],
            'quantity': 'diagnostic_thread_cpu_seconds', 'timing_scope': row['scope'],
            'attribution': pair['attribution'], 'checker': context['verifier'],
            'primary_checker_sha256': context['verifier_sha256'],
            'raw_recheck_checker_sha256': artifacts.file_hash(bfs_native.__file__)})
    _fail(all(row.get('metrics', {}).get(key) == value for key, value in totals.items()),
          'native accumulated region values differ from the raw trial reports')
    return samples


def compare(store, a, b, settings, packages):
    _fail(isinstance(packages, dict), "diagnostic comparison requires explicit region_packages")
    native = settings['mode'] == 'native'
    components = {}
    for role, evaluation in (("baseline", a), ("candidate", b)):
        components[role] = ([evaluation] if native else
            [_get(store, item["evaluation"], "evaluation") for item in evaluation.get("component_evaluations", [])])
        _fail(components[role], "diagnostic comparison requires actual primary evaluations")
    _fail(set(packages) == {item["id"] for rows in components.values() for item in rows}, "region_packages must cover exactly both primary execution grids")
    results = []
    for pair in settings.get("region_pairs", []):
        if pair.get("evidence") not in {'simulated_diagnostic_profile', 'native_diagnostic_profile.v1'}: continue
        samples = {role: _native_samples(store, rows[0], packages[rows[0]['id']], pair, role) if native else
                   [_sample(store, primary, packages[primary["id"]], pair, role) for primary in rows]
                   for role, rows in components.items()}
        diagnostic_ids = [(row['parent_output']['path'] if native else row["diagnostic_evaluation"])
                          for rows in samples.values() for row in rows]
        _fail(len(diagnostic_ids) == len(set(diagnostic_ids)), "diagnostic replay is reused across distinct comparison cells")
        cells = {role: {(row["source_position"], row["repetition"], row["source"]) for row in rows} for role, rows in samples.items()}
        _fail(cells["baseline"] == cells["candidate"] and all(len(cells[role]) == len(samples[role]) for role in cells),
              "diagnostic comparison has missing, duplicate, or different replay cells")
        positions = sorted({cell[0] for cell in cells["baseline"]})
        absent = [row["duration_s"] is None for row in samples["baseline"]]
        if any(absent):
            _fail(all(absent), "baseline diagnostic region is not invoked in only some replay cells")
            candidate = {position: statistics.median(row["duration_s"] for row in samples["candidate"]
                                                     if row["source_position"] == position) for position in positions}
            results.append({**pair, "state": "baseline_not_invoked", "duration_ratio": None,
                "baseline_invocations": 0,
                "candidate_invocations": [row["invocations"] for row in samples["candidate"]],
                "candidate_duration_s": {str(position): value for position, value in candidate.items()},
                "samples": samples, "primary_bfs_roi": False, "gain_claim": False,
                "note": ("The baseline never executes this region (raw-verified zero invocations and time); "
                         "no regional ratio exists. Candidate time is reported alone; the primary BFS result is separate.")})
            continue
        ratios = {position: statistics.median(row["duration_s"] for row in samples["baseline"] if row["source_position"] == position)
                  / statistics.median(row["duration_s"] for row in samples["candidate"] if row["source_position"] == position)
                  for position in positions}
        results.append({**pair, "duration_ratio": _positive(_geomean(ratios.values()), "region duration ratio"),
            "per_source_position_ratio": {str(position): value for position, value in ratios.items()},
            "samples": samples, "primary_bfs_roi": False, "gain_claim": False,
            "note": ("Diagnostic thread CPU ratio with scope instrumentation included; excludes descheduled time and cannot replace primary BFS wall timing."
                     if native else "Diagnostic per-thread elapsed ratio; includes waiting and overlap and cannot replace primary BFS timing.")})
    return results
