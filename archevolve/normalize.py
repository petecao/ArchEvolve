"""Adapt the received v1.1 TDStep reports without upgrading their evidence."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re

from tools.render_mermaid import RequestError, load_request, mapping, sequence


def number(value):
    return value if type(value) in (int, float) else None


def normalize(data: dict, digest: str, source_name: str, reference: dict,
              large_jump_threshold: float = 16, methods: dict | None = None) -> dict:
    if str(data.get("schema_version")) != "1.1":
        raise RequestError("The initial feature adapter supports schema_version 1.1.")
    kernel = mapping(data.get("kernel"), "kernel")
    if kernel.get("function") != "TDStep":
        raise RequestError("The initial adapter supports TDStep; other functions need an adapter.")
    if not isinstance(kernel.get("name"), str) or not kernel["name"].strip():
        raise RequestError("kernel.name must identify the workload case.")
    issues = []

    def issue(code, message, fields, affects):
        issues.append({"id": code, "severity": "needs_clarification", "message": message,
                       "fields": fields, "affects": affects})

    revision = kernel.get("source_revision", kernel.get("revision"))
    binding = "unverified"
    if revision is None:
        issue("source-unbound", "No exact profiled source revision/hash is supplied. Do not attach this report to the local DX100 revision automatically.",
              ["kernel.source_file", "kernel.source_revision"], ["source_binding", "interface_details"])
    elif revision != reference.get("revision"):
        binding = "different_revision"
        issue("source-differs", "The reported source revision differs from the recorded DX100 reference.",
              ["kernel.source_revision"], ["source_binding", "interface_details"])
    else:
        binding = "revision_reported_matching" # Still not a reproduced measurement.

    issue("raw-profile-missing", "Received values are reported; raw profiling logs, build flags, dataset identity and per-run scope have not been bound/verified by this prototype.",
          ["hardware_performance_profile", "indirect_access_distances"], ["performance_claims"])
    raw_streams = sequence(data.get("memory_streams", []), "memory_streams")
    distances = sequence(data.get("indirect_access_distances", []), "indirect_access_distances")
    structures = sequence(data.get("data_structures", []), "data_structures")

    def indexed(rows, field, where):
        result = {}
        for row in rows:
            mapping(row, where)
            name = row.get(field)
            if not isinstance(name, str) or not name.strip():
                raise RequestError(f"{where}.{field} must be a non-empty string.")
            if name in result:
                raise RequestError(f"Duplicate {where} entry {name!r}.")
            result[name] = row
        return result

    stream_by_name = indexed(raw_streams, "name", "memory_streams")
    distance_by_name = indexed(distances, "array_name", "indirect_access_distances")
    structure_by_name = indexed(structures, "name", "data_structures")
    operations = mapping(data.get("operations", {}), "operations")
    working_set = mapping(data.get("working_set", {}), "working_set")
    scale_examples = mapping(working_set.get("scale_examples", {}), "working_set.scale_examples")
    rmw = mapping(operations.get("rmw_operation", {}), "rmw_operation")
    subtype = str(rmw.get("subtype", "unknown"))
    cas = bool(re.search(r"cas|compare.and.swap", subtype, re.I)) or "CAS(" in str(rmw.get("primitive", ""))
    phases = deepcopy(rmw.get("execution_frequency", {}))
    if cas and phases:
        issue("phase-specific-cas", "Retain conditional CAS for the kernel. A reported zero-execution second phase does not remove the discovery-phase update.",
              ["operations.rmw_operation.execution_frequency"], ["phase_specialization", "correctness"])

    accesses, hypotheses, excluded = [], [], []
    for index, name in enumerate(dict.fromkeys([*stream_by_name, *distance_by_name])):
        stream, distance, structure = stream_by_name.get(name, {}), distance_by_name.get(name, {}), structure_by_name.get(name, {})
        stats = mapping(distance.get("statistics", {}), f"{name}.statistics")
        width_values = [r.get("element_size_bytes") for r in (structure, distance) if r.get("element_size_bytes") is not None]
        if any(type(w) is not int or w <= 0 for w in width_values):
            raise RequestError(f"{name}: element_size_bytes must be a positive integer.")
        width = width_values[0] if width_values else None
        if len(set(width_values)) > 1:
            issue(f"width-internal-{index}", f"Conflicting reported widths for {name}.", [f"data_structures.{name}", f"indirect_access_distances.{name}"], ["configuration"])
            usable_width = None
        else:
            usable_width = width
        ref_width = reference.get("element_bytes", {}).get(name)
        if width is not None and ref_width is not None and width != ref_width:
            issue(f"width-reference-{index}", f"{name} is reported as {width} bytes; the recorded DX100 reference uses {ref_width}. This may be a different fork/build; neither value is silently substituted.",
                  [f"data_structures.{name}.element_size_bytes", f"indirect_access_distances.{name}.element_size_bytes"], ["source_binding", "port_widths", "configuration"])
            usable_width = None
        mean_index = number(stats.get("mean_index_distance"))
        mean_bytes = number(stats.get("mean_byte_stride"))
        if mean_index is not None and mean_index < 0:
            raise RequestError(f"{name}: absolute mean index distance cannot be negative.")
        if mean_bytes is not None and mean_bytes < 0:
            raise RequestError(f"{name}: absolute mean byte stride cannot be negative.")
        if mean_index is not None and mean_bytes is not None and width is not None:
            expected = mean_index * width
            if abs(expected - mean_bytes) > max(0.001, abs(expected) * 0.001):
                issue(f"stride-arithmetic-{index}", f"{name}: mean byte stride does not agree with reported element width times mean index distance.", [f"indirect_access_distances.{name}.statistics"], ["stride_interpretation"])
        if "spatial_locality_distribution" in stats:
            excluded.append({"field": f"indirect_access_distances.{name}.statistics.spatial_locality_distribution", "reported_value": deepcopy(stats["spatial_locality_distribution"]),
                             "reason": "A distance threshold does not establish same cache-line/page membership or cache-hit rate. Excluded from selection rules."})
        if distance.get("hardware_implication"):
            hypotheses.append({"field": f"indirect_access_distances.{name}.hardware_implication", "text": distance["hardware_implication"], "use": "hypothesis_not_constraint"})
        kind = str(stream.get("type", "unknown"))
        op = "read_modify_write" if (name == "parent" and cas) or "rmw" in kind.lower() else "read" if "read" in kind.lower() else "unknown"
        accesses.append({
            "id": f"access-{index + 1:02d}", "array": name,
            "statement_ids": [], "source_location": None,
            "reported_stream_kind": kind, "indexed_addressing": name in distance_by_name or "indirect" in kind.lower(),
            "reported_index_expression": distance.get("index_stream"), "operation": op,
            "rmw_subtype": "conditional_compare_and_swap" if name == "parent" and cas else None,
            "reported_element_type": structure.get("element_type", distance.get("element_type")),
            "reported_element_bytes": width, "reference_element_bytes": ref_width,
            "diagram_element_bytes": usable_width,
            "width_status": "unresolved_conflict" if width is not None and usable_width is None else "reported" if width else "unknown",
            "reported_mean_index_distance": mean_index, "reported_mean_byte_stride": mean_bytes,
            "reported_stream_stride_bytes": stream.get("stride_bytes"),
            "reuse_distance": None, "reuse_frequency": None, "tile_working_set_bytes": None,
            "evidence_refs": [f"input:{digest}", f"field:memory_streams.{name}"] + ([f"field:indirect_access_distances.{name}"] if distance else []),
        })
    if not accesses:
        raise RequestError("No supported access records found in the feature report.")
    if excluded:
        issue("locality-not-hit-rate", "Locality percentages and associated cache-hit conclusions are retained as unverified claims, not measured cache-hit rates.",
              [x["field"] for x in excluded], ["performance_claims", "hardware_priority"])
    if working_set:
        issue("footprint-not-working-set", "Reported array footprints are not a tile/phase-scoped active working set. MB versus MiB also needs confirmation; no storage size is selected from these values.",
              ["working_set"], ["storage_sizing"])
    if len(scale_examples) > 1:
        issue("multiple-scales", "This report includes several graph scales without binding each statistic to a run. Do not transfer values between scales.", ["working_set.scale_examples", "indirect_access_distances"], ["measurement_scope"])
    issue("statement-locations-missing", "Array-level features are usable for exploratory retrieval; exact statement IDs and profiled-source locations are still absent.",
          ["memory_streams", "kernel.source_file"], ["intrinsic_placement"])
    means = [a["reported_mean_index_distance"] for a in accesses if a["reported_mean_index_distance"] is not None]
    signals = {
        "always": True,
        "has_indirect_access": any(a["indexed_addressing"] for a in accesses),
        "has_regular_stream": any("streaming" in a["reported_stream_kind"] for a in accesses),
        "has_read_stream": any(a["operation"] == "read" for a in accesses),
        "has_conditional_cas": cas,
        "reported_large_jumps": any(v >= large_jump_threshold for v in means) if means else None,
        "reported_near_unit_indices": all(v <= 1.1 for v in means) if means else None,
    }
    result = {
        "normalizer_version": "offline-0.1", "case_id": kernel["name"],
        "input_ref": source_name, "input_sha256": digest,
        "kernel": deepcopy(kernel), "source_binding": {"status": binding, "reported_revision": revision, "reference_revision": reference.get("revision")},
        "evidence_status": "reported_not_reproduced", "accesses": accesses,
        "rmw": {"kind": "conditional_compare_and_swap" if cas else "unknown", "reported_details": deepcopy(rmw), "must_preserve": True, "phase_execution": phases},
        "reported_topology": deepcopy(data.get("topology_characteristics")),
        "reported_footprints_and_reuse": deepcopy(data.get("working_set")),
        "reported_counters": deepcopy(data.get("hardware_performance_profile")),
        "hardware_hypotheses": hypotheses, "excluded_from_selection": excluded,
        "issues": issues, "signals": signals,
        "heuristic_policy": {"large_jump_threshold_elements": large_jump_threshold, "near_unit_upper_bound_elements": 1.1, "meaning": "Exploration ordering only; not a bottleneck classifier or speedup estimate."},
    }
    if methods is not None:
        from archevolve.measurement_methods import apply_methodology
        result = apply_methodology(result, data, methods)
    return result


def load_normalized(path: Path, reference: dict, large_jump_threshold=16, methods=None):
    data, digest = load_request(path)
    return normalize(data, digest, str(path), reference, large_jump_threshold, methods)
