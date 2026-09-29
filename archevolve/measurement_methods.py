"""Interpret explicit, hash-bound methodology without changing source reports."""

from copy import deepcopy
import math

from tools.render_mermaid import RequestError


def percentage(value):
    """Only percent-labeled strings have an unambiguous scale in these reports."""
    if not isinstance(value, str) or not value.strip().endswith("%"):
        return None
    try:
        result = float(value.strip()[:-1]) / 100
    except ValueError:
        return None
    return result if math.isfinite(result) and 0 <= result <= 1 else None


def apply_methodology(case, data, methods):
    result = deepcopy(case)
    if methods.get("methodology_version") != "1" or methods.get("record_kind") != "reported_methodology":
        raise RequestError("Unsupported measurement methodology record.")
    if case["input_sha256"] not in methods.get("applies_to_input_sha256", []):
        result["methodology"] = {"status":"not_applied_input_hash_mismatch", "record_sha256":methods.get("record_sha256")}
        result["issues"].append({"id":"method-input-mismatch", "severity":"needs_clarification",
                                "message":"The supplied methodology does not name this exact input hash and was not applied.",
                                "fields":["methodology"], "affects":["measurement_interpretation"]})
        return result
    result["methodology"] = {"status":"reported_method_bound_to_input", "record_sha256":methods.get("record_sha256"),
                             "source_ref":methods.get("source_ref"), "source_sha256":methods.get("source_sha256"),
                             "verification":"instrumentation_not_reproduced"}
    locality = methods.get("locality", {})
    if locality.get("interpretation") != "absolute_index_distance_threshold" or locality.get("comparison") != "less_than_or_equal":
        raise RequestError("This adapter supports only the explicitly described <= index-distance method.")
    by_array = {item["array_name"]:item for item in data.get("indirect_access_distances", [])}
    scope_notes = []
    for access in result["accesses"]:
        name = access["array"]
        method = locality.get("arrays", {}).get(name)
        if method is None:
            continue
        width = method.get("element_bytes")
        if type(width) is not int or width <= 0 or width != access["reported_element_bytes"]:
            raise RequestError(f"Methodology width for {name} disagrees with the received report.")
        values = by_array.get(name, {}).get("statistics", {}).get("spatial_locality_distribution", {})
        measurements = []
        for limit, field in ((64,"within_same_64B_cacheline"), (4096,"within_same_4KB_page")):
            threshold = method.get("threshold_elements", {}).get(str(limit))
            if type(threshold) is not int or threshold * width != limit:
                raise RequestError(f"Methodology threshold for {name}/{limit} is inconsistent.")
            if field not in values:
                continue
            measurements.append({"metric":"fraction_of_adjacent_pairs_with_absolute_byte_distance_at_most_threshold",
                                 "threshold_bytes":limit, "comparison":"<=", "fraction":percentage(values[field]),
                                 "reported_value":values[field], "original_label":field, "status":"reported_relabelled_by_method",
                                 "scope":method["pair_scope"], "measures_cache_hits":False, "measures_same_block_membership":False})
        access["adjacent_pair_proximity"] = measurements
        access["reported_mean_distance_scope"] = method["pair_scope"]
        access["distance_sequence"] = method["sequence"]
        access["cross_segment_pairs_included"] = method["cross_segment_pairs_included"]
        access["runtime_thread_interleaving_observed"] = method["runtime_thread_interleaving_observed"]
        scope_notes.append(f"{name}: {method['pair_scope']}")
    for issue in result["issues"]:
        if issue["id"] == "locality-not-hit-rate":
            issue["severity"] = "interpretation_resolved"
            issue["message"] = "Peter's instrumentation measures adjacent-index proximity, not same cache-line/page membership or cache-hit rates. Values are relabeled descriptively and remain outside selection rules."
        elif issue["id"] == "footprint-not-working-set":
            issue["severity"] = "interpretation_resolved"
            issue["message"] = "Peter confirmed capacity-based array footprints. Exact bytes and decimal/binary conversions are derived separately; active tile/phase working sets remain unknown and do not fix storage parameters."
    result["issues"].append({"id":"pair-sequence-scope", "severity":"interpretation_resolved",
                            "message":"The snippets enumerate adjacent positions within frontiers/rows, excluding segment transitions and thread interleaving; they do not establish a global hardware-access trace. " + "; ".join(scope_notes),
                            "fields":["indirect_access_distances"], "affects":["stride_scope", "reuse_interpretation"]})
    capacities = methods.get("footprints", {})
    if capacities.get("interpretation") != "logical_array_capacity":
        raise RequestError("Unsupported footprint methodology.")
    widths = capacities.get("element_bytes", {})
    if any(type(widths.get(key)) is not int or widths[key] <= 0 for key in ("parent", "VertexOffsets", "g.out_neighbors_", "queue.shared")):
        raise RequestError("Capacity calculations need positive integer element widths.")
    working = data.get("working_set", {})
    scopes = dict(working.get("scale_examples", {}))
    scopes.update({key:value for key,value in working.items() if isinstance(value,dict) and "num_nodes" in value and "num_directed_edges" in value})
    derived, unit_conflicts = [], []
    for name, scope in scopes.items():
        nodes, edges = scope.get("num_nodes"), scope.get("num_directed_edges")
        if type(nodes) is not int or type(edges) is not int or nodes < 0 or edges < 0:
            raise RequestError(f"Footprint scope {name} needs nonnegative integer graph dimensions.")
        arrays = {}
        for array, count, prefix in (("parent", nodes, "parent"), ("VertexOffsets", nodes + 1, "offsets"), ("g.out_neighbors_", edges, "neighbors"), ("queue.shared", nodes, "queue")):
            size = count * widths[array]
            checks = []
            for suffix, decimal, binary in (("kb",1000,1024), ("mb",1000000,1048576)):
                field = f"{prefix}_footprint_{suffix}"
                value = scope.get(field)
                if type(value) not in (float,int):
                    continue
                tolerance = max(0.011, abs(value) * 0.0001)
                binary_match = abs(value-size/binary) <= tolerance
                decimal_match = abs(value-size/decimal) <= tolerance
                interpretation = "ambiguous" if binary_match and decimal_match else "binary" if binary_match else "decimal" if decimal_match else "neither_within_tolerance"
                checks.append({"field":field, "reported_value":value, "matches_conversion":interpretation})
                if capacities.get("reported_unit_claim") == "binary" and not binary_match:
                    unit_conflicts.append(f"{name}.{field}={value} matches {interpretation} conversion; explanation claims binary.")
            arrays[array] = {"element_count":count, "reported_element_bytes":widths[array], "capacity_bytes":size,
                             "KiB":size/1024, "MiB":size/1048576, "kB":size/1000, "MB":size/1000000,
                             "reported_unit_checks":checks}
        derived.append({"scope":name, "status":"derived_from_reported_dimensions_and_widths_not_measured_residency",
                        "arrays":arrays, "listed_array_capacity_bytes":sum(item["capacity_bytes"] for item in arrays.values()),
                        "excludes":"allocator overhead, padding, per-thread queue buffers, and other program state", "active_working_set_bytes":None})
    result["derived_array_capacities"] = derived
    if unit_conflicts:
        result["issues"].append({"id":"footprint-unit-inconsistency", "severity":"needs_clarification",
                                "message":"Some reported footprints do not use the claimed binary conversion. Original numbers are preserved; exact byte-derived values are separate.",
                                "details":unit_conflicts, "fields":["working_set"], "affects":["footprint_units"]})
    return result
