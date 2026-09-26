"""Execution-bound DX100 statistics and selected-region collection.

Updated: 2026-09-25. Source discovery is reused; no static access stream is invented.
"""

import configparser
import copy
from decimal import Decimal, InvalidOperation
import math
from pathlib import Path
import re
import time

from swdb import artifacts, workflow
from swdb.bfs_protocol import _request
from swdb.cli import Failure, _require_valid
from swdb.dx100 import _file
from swdb.bfs_native import StageFailure


def diagnostic_regions(store, request, evaluation, candidate, root):
    from swdb.dx100_diagnostic import counters
    from swdb.profile_package import _context, _region
    diagnostic = store.get(request.get('diagnostic_evaluation'), 'evaluation')
    if (not diagnostic or diagnostic.get('candidate') != candidate['id']
            or diagnostic.get('outcome', {}).get('state') != 'complete'
            or diagnostic.get('evidence_kind') != evaluation['evidence_kind']
            or artifacts.digest(_context(diagnostic)) != artifacts.digest(_context(evaluation))):
        raise Failure('diagnostic execution differs from the exact primary source/workload/configuration/ROI')
    build = store.get(diagnostic['context'].get('candidate_build'), 'evaluation')
    if (not build or not build.get('context', {}).get('diagnostic')
            or build.get('outcome', {}).get('state') != 'complete'
            or build['outcome'].get('stage') != 'candidate_build'
            or build.get('candidate') != candidate['id']
            or build.get('evidence_kind') != diagnostic['evidence_kind']):
        raise Failure('diagnostic execution has no instrumented compilation receipt')
    definition = build['context']['diagnostic']
    if definition.get('discovery', {}).get('backend') != 'libclang-cindex':
        raise Failure('diagnostic compilation does not identify the shared compiler discovery')
    if (build['context'].get('candidate_sha256') != candidate['artifact']['sha256']
            or build['build']['binary_sha256'] != diagnostic['build']['binary_sha256']):
        raise Failure('diagnostic compilation source/binary identity differs')
    binary = _file({'path': build['build']['binary'], 'sha256': build['build']['binary_sha256']}, 'diagnostic binary')
    for key in ('instrumented_source', 'runtime'):
        _file(definition[key], 'diagnostic ' + key)
    stage = next((item for item in diagnostic['stages'] if item['stage'] == 'simulation'), None)
    if not stage or not stage.get('log_sha256'):
        raise Failure('diagnostic simulation log identity is unavailable')
    log = _file({'path': stage['log'], 'sha256': stage['log_sha256']}, 'diagnostic log')
    observed = counters(log, len(definition['regions']))
    regions = []
    for original, values in zip(definition['regions'], observed):
        row = _region(original, root)
        row.update(metrics={'inclusive_simulated_seconds': values['inclusive_ns'] / 1e9,
                            'exclusive_simulated_seconds': values['exclusive_ns'] / 1e9,
                            'invocations': values['invocations']},
            basis='simulated', scope='accumulated simulated elapsed per executing thread within diagnostic complete-call ROI',
            artifact_sha256=diagnostic['build']['binary_sha256'], source_artifact_sha256=candidate['artifact']['sha256'],
            attribution={'inclusive': True, 'exclusive': 'nested guarded intervals subtracted on the same thread',
                         'whole_lexical_region': True, 'clock': 'm5_rpns',
                         'quantity': definition['quantity'], 'limitations': definition['difference']})
        regions.append(row)
    source = diagnostic['context']['source']
    trial = evaluation['context'].get('protocol_trial', {'source_position': 0, 'repetition': 0})
    run = {'kind': 'regions', 'evaluation': diagnostic['id'], 'source': source, **trial,
        'binary_sha256': diagnostic['build']['binary_sha256'], 'output': str(log), 'output_sha256': stage['log_sha256'],
        'region_output': str(log), 'region_output_sha256': stage['log_sha256'],
        'evidence_kind': diagnostic['evidence_kind'], 'correctness': copy.deepcopy(diagnostic['correctness']),
        'differences_from_primary': [definition['difference']], 'host_cost_is_performance': False}
    return regions, definition['discovery'], run, {'path': str(binary), 'sha256': run['binary_sha256'], 'difference': definition['difference']}


def statistics(path, deadline):
    """Read complete raw intervals; require an explicit caller-selected interval."""
    intervals, current = [], None
    if path.stat().st_size > 64 * 1024 * 1024:
        raise Failure("statistics file exceeds the 64 MiB collector bound")
    with path.open() as stream:
        for number, line in enumerate(stream, 1):
            if number % 1000 == 0 and time.monotonic() > deadline:
                raise StageFailure("budget_exhausted", "statistics collection time budget exhausted")
            if "Begin Simulation Statistics" in line:
                if current is not None:
                    raise Failure("nested or truncated statistics interval")
                current = {"start_line": number, "values": {}}
            elif "End Simulation Statistics" in line:
                if current is None:
                    raise Failure("statistics end without a begin")
                current["end_line"] = number
                intervals.append(current)
                current = None
            elif current is not None:
                fields = line.split()
                if not fields or fields[0].startswith("#"):
                    continue
                if len(fields) < 2 or fields[0] in current["values"]:
                    raise Failure("malformed or duplicate statistic")
                current["values"][fields[0]] = fields[1]
    if current is not None or not intervals:
        raise Failure("no complete readable statistics interval")
    return intervals


def duration(interval):
    try:
        raw_ticks = interval["values"]["simTicks"]
        raw_frequency = interval["values"]["simFreq"]
        if not all(re.fullmatch(r"[0-9]{1,24}", raw) for raw in (raw_ticks, raw_frequency)):
            raise Failure("ROI ticks and tick frequency must use bounded decimal integers")
        ticks, frequency = Decimal(raw_ticks), Decimal(raw_frequency)
    except (KeyError, InvalidOperation):
        raise Failure("ROI requires numeric simTicks and simFreq") from None
    if any(not value.is_finite() or value <= 0 or value != value.to_integral_value() for value in (ticks, frequency)):
        raise Failure("ROI ticks and tick frequency must be finite positive integers")
    return {"sim_ticks": int(ticks), "tick_frequency_hz": int(frequency),
            "duration_s": float(ticks / frequency), "unit": "seconds",
            "conversion": "simTicks / simFreq; no fixed clock-period divisor"}


def clocks(path, frequency):
    if path.stat().st_size > 8 * 1024 * 1024:
        raise Failure("configuration file exceeds the 8 MiB collector bound")
    config = configparser.ConfigParser(interpolation=None)
    config.read(path)
    found = {}
    for name in config.sections():
        if config.get(name, "type", fallback="") == "SrcClockDomain":
            periods = config.get(name, "clock", fallback="").split()
            if not periods or any(not re.fullmatch(r"[0-9]{1,24}", value) or int(value) <= 0 for value in periods):
                raise Failure("actual clock domain has no positive tick period")
            found[name] = {"period_ticks": [int(value) for value in periods],
                           "frequency_hz": [frequency / int(value) for value in periods]}
    if not found:
        raise Failure("actual configuration has no resolved source clock domain")
    return found


def memory(interval, evidence, execution):
    rows = []
    for name, raw in interval["values"].items():
        definition = None
        if re.fullmatch(r"system\..*(?:cache|l2|l3).*\.(?:overallAccesses|overallHits|overallMisses)::total", name):
            definition = "Modeled cache access, hit, or miss count at the named cache; totals retain its request semantics."
        elif re.fullmatch(r"system\.maa\.port_(?:cache|mem)_(?:RD|WR)_packets", name):
            definition = "DX100 MAA packet count on the named cache-side or memory-side read/write port; not element accesses."
        if definition:
            if not re.fullmatch(r"[0-9]{1,24}", raw):
                raise Failure(f"dynamic counter {name} must use a bounded decimal integer")
            try:
                value = Decimal(raw)
            except InvalidOperation:
                raise Failure(f"malformed dynamic counter {name}") from None
            if not value.is_finite() or value < 0 or value != value.to_integral_value():
                raise Failure(f"dynamic counter {name} is not a nonnegative integer")
            rows.append({"metric": name, "available": True, "value": int(value), "unit": "count",
                "definition": definition, "basis": "simulated", "scope": "entire sealed BFS ROI; no loop attribution",
                "collector": "dx100-gem5-statistics.v1", "execution": execution,
                "artifact_sha256": evidence["sha256"], "raw_artifact": evidence,
                "interval": {"start_line": interval["start_line"], "end_line": interval["end_line"]}})
    return rows


def steps(path, deadline):
    observed = {"td": [], "td_maa": []}
    active = False
    starts = ends = 0
    with path.open(errors="replace") as stream:
        for number, line in enumerate(stream, 1):
            if number % 10000 == 0 and time.monotonic() > deadline:
                raise StageFailure("budget_exhausted", "region log collection time budget exhausted")
            if line.startswith("ROI started:"):
                starts += 1; active = True
            elif line.strip() == "ROI End!!!":
                ends += 1; active = False
            elif active:
                match = re.fullmatch(r"\s*(td|td_maa)\s+(\d+\.\d+)\s*", line)
                if match:
                    seconds = float(match[2])
                    if not math.isfinite(seconds):
                        raise Failure("region duration is not finite")
                    observed[match[1]].append({"line": number, "seconds": seconds})
    if starts != 1 or ends != 1:
        raise Failure("region attribution requires exactly one complete logged ROI")
    return observed


def collect(args):
    store = _require_valid(args.records)
    request = _request(args)
    if store.get(request["id"]):
        raise Failure("profile ID already exists; retain it and use a new ID")
    data = workflow.record("region_profile", request["id"], request=request,
        outcome={"state": "submitted", "stage": "collection", "reason": None},
        stages=[], regions=[], dynamic_memory=[], executions=[], raw_artifacts=[], reasons=[], gain_claim=False)
    workflow.persist(args.records, data, getattr(args, "db", None))
    try:
        base_fields = {"message_version", "id", "evaluation", "budget"}
        if (set(request) not in (base_fields | {'discovery_profile'}, base_fields | {'diagnostic_evaluation'})):
            raise Failure("DX100 profile requires evaluation, exactly one discovery_profile or diagnostic_evaluation, and explicit budget")
        budget = request["budget"]
        if not isinstance(budget, dict) or set(budget) != {"total_seconds"} or type(budget["total_seconds"]) is not int or not 1 <= budget["total_seconds"] <= 600:
            raise Failure("collector budget.total_seconds must be an integer from 1 to 600")
        deadline = time.monotonic() + budget["total_seconds"]
        evaluation = store.get(request["evaluation"], "evaluation")
        if not evaluation or evaluation.get("context", {}).get("backend") != "dx100-gem5-se":
            raise Failure("evaluation does not identify DX100 execution")
        context = evaluation["context"]
        candidate = store.get(evaluation.get("candidate"), "candidate")
        discovery = store.get(request.get("discovery_profile"), "region_profile")
        if not candidate or (not request.get('diagnostic_evaluation') and (not discovery or discovery.get("candidate") != candidate["id"])):
            raise Failure("collection requires compiler discovery for this exact candidate")
        if discovery and discovery.get("discovery", {}).get("backend") != "libclang-cindex":
            raise Failure("source regions must come from the shared compiler discovery engine")
        root = artifacts.verify(candidate["artifact"])
        if context.get("candidate_sha256") != candidate["artifact"]["sha256"]:
            raise Failure("timed execution and candidate source differ")
        from swdb.profile_package import _region
        data.update(evaluation=evaluation["id"], candidate=candidate["id"], source_snapshot=candidate["source_snapshot"],
                    implementation=candidate["implementation"], machine=evaluation["machine"], context=copy.deepcopy(context),
                    discovery=copy.deepcopy(discovery["discovery"]) if discovery else {})
        data["context"]["primary_binary_sha256"] = evaluation["build"]["binary_sha256"]
        stats_reference = context["statistics"]
        stats = _file(stats_reference, "recorded statistics")
        config = _file(context["actual_configuration"], "actual simulator configuration")
        intervals = statistics(stats, deadline)
        # The primary guest dump precedes simulator shutdown's optional dump.
        # A sealed verification run contains exactly the guest interval.
        if "sealed_roi" in context and len(intervals) != 1:
            raise Failure("sealed ROI contains multiple statistics intervals")
        selected = intervals[0]
        roi = duration(selected)
        roi.update(interval_index=0, interval_count=len(intervals), start_line=selected["start_line"],
                   end_line=selected["end_line"], clocks=clocks(config, roi["tick_frequency_hz"]),
                   statistics=stats_reference, configuration=context["actual_configuration"])
        data["context"]["roi_observation"] = roi
        data["dynamic_memory"] = memory(selected, stats_reference, evaluation["id"])
        stage = next((stage for stage in evaluation["stages"] if stage["stage"] == "simulation"), None)
        if not stage or not stage.get("log_sha256"):
            raise Failure("simulation log identity is unavailable")
        log_reference = {"path": stage["log"], "sha256": stage["log_sha256"]}
        log = _file(log_reference, "simulation log")
        observations = steps(log, deadline) if discovery else {}
        for original in discovery["regions"] if discovery else []:
            row = _region(original, root)
            row["metrics"] = {}
            row.update(basis="simulated", artifact_sha256=log_reference["sha256"],
                       scope="unobserved in this primary execution")
            labels = [label for label in observations if f'PrintStep("{label}"' in row["text"]]
            # Associate existing timer statements with their smallest discovered
            # enclosing loop. Never copy native timings or invent exclusivity.
            if row["kind"] == "loop" and labels and "t.Start()" in row["text"] and "t.Stop()" in row["text"]:
                events = [item for label in labels for item in observations[label]]
                row["metrics"] = {"inclusive_simulated_seconds": sum(item["seconds"] for item in events),
                                  "invocations": len(events)}
                row.update(scope="accumulated Start-to-Stop statements inside this traversal loop; inclusive of called work",
                    attribution={"inclusive": True, "exclusive": "unavailable", "whole_lexical_region": False,
                        "print_resolution_s": 0.00001, "timer": "guest std::chrono high_resolution_clock",
                        "observed_log_lines": [item["line"] for item in events],
                        "limitations": "Includes queue advancement and any logging between timer endpoints; zero printed durations are quantized, not exact zero."})
            data["regions"].append(row)
        data["reasons"] = ["Primary logging does not measure every discovered function/loop or establish exclusive region attribution; diagnostic profiling remains required."]
        if not data["dynamic_memory"]:
            data["reasons"].append("No supported actual dynamic memory counter appears in the selected interval.")
        data["executions"] = [{"evaluation": evaluation["id"], "binary_sha256": evaluation["build"]["binary_sha256"],
            "evidence_kind": evaluation["evidence_kind"], "correctness": copy.deepcopy(evaluation["correctness"]),
            "roi": context["roi"], "statistics": stats_reference, "output": log_reference,
            "differences_from_primary": [], "host_cost_is_performance": False}]
        if request.get('diagnostic_evaluation'):
            regions, discovered, run, binary = diagnostic_regions(store, request, evaluation, candidate, root)
            data.update(regions=regions, discovery=discovered, reasons=[])
            data['executions'].append(run)
            data['artifacts'] = {'primary_binary_sha256': evaluation['build']['binary_sha256'],
                'region_binary': binary, 'memory_binary': {'path': evaluation['build']['binary'],
                    'sha256': evaluation['build']['binary_sha256'], 'difference': 'actual primary modeled memory counters'}}
            trial = context.get('protocol_trial', {'source_position': 0, 'repetition': 0})
            data['executions'][0].update(kind='memory', source=context['source'], **trial,
                output=str(log), output_sha256=log_reference['sha256'], raw_artifact=str(stats), raw_sha256=stats_reference['sha256'])
            for row in data['dynamic_memory']:
                row.update(artifact_sha256=evaluation['build']['binary_sha256'], source_artifact_sha256=candidate['artifact']['sha256'],
                    execution={'source': context['source'], **trial},
                    raw_artifact=str(stats), raw_sha256=stats_reference['sha256'])
            if not data['dynamic_memory']:
                data['reasons'].append('No supported actual dynamic memory counter appears in the primary interval.')
            if discovered.get('unresolved'):
                data['reasons'].append('Compiler discovery retains unresolved source scopes.')
            if not all(any(row['kind'] == kind and row['metrics']['invocations'] > 0 for row in regions) for kind in ('function', 'loop')):
                data['reasons'].append('No invoked function and loop pair has complete diagnostic timing.')
        data["raw_artifacts"] = [{"kind": "statistics", **stats_reference}, {"kind": "log", **log_reference},
                                 {"kind": "configuration", **context["actual_configuration"]}]
        trial = context.get('protocol_trial', {'source_position': 0, 'repetition': 0})
        timing = {"source": context["source"], **trial,
            "duration_s": roi["duration_s"], "roi": context["roi"], "basis": "simulated", "quantity": "simulated_roi_seconds",
            "binary_sha256": evaluation["build"]["binary_sha256"], "output": str(log), "output_sha256": log_reference["sha256"],
            "statistics_sha256": stats_reference["sha256"],
            "verified": evaluation["correctness"]["state"] == "passed", "evidence_kind": evaluation["evidence_kind"]}
        if time.monotonic() > deadline:
            raise StageFailure("budget_exhausted", "profile collection time budget exhausted")
        if evaluation["timing"] and evaluation["timing"] != [timing]:
            raise Failure("existing primary timing differs from this interval; preserve it and investigate")
        evaluation["timing"] = [timing]
        evaluation["profiling"] = {"state": "incomplete" if data['reasons'] else 'complete', "region_profile": data["id"], "reasons": data["reasons"]}
        workflow.persist(args.records, evaluation, getattr(args, "db", None))
        data["outcome"] = {"state": "partial" if data['reasons'] else 'complete', "stage": "collection",
            "reason": data['reasons'][0] if data['reasons'] else 'Exact source scopes and modeled memory collected; diagnostic durations are separate from primary timing.'}
    except (Failure, StageFailure, OSError, ValueError, KeyError, TypeError, configparser.Error) as exc:
        if isinstance(exc, Failure) and "persisted, but query indexing failed" in str(exc):
            raise
        data["outcome"] = {"state": exc.state if isinstance(exc, StageFailure) else "failed", "stage": "collection", "reason": str(exc)}
        data["reasons"].append(str(exc))
    return workflow.persist(args.records, data, getattr(args, "db", None))
