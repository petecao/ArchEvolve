"""Versioned hardware evidence and conditional retrieval, without performance ranking.

This module validates the representation, not the hardware. Paper/code claims are
kept distinct from runtime validation; retrieval never discharges a mapping's
ownership, aliasing, synchronization, or numeric requirements.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

from tools.render_mermaid import RequestError, identifier, load_request, mapping, sequence

FORMAT = "hardware-catalog-v0.1"
DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "catalog/hardware-v0.1.yaml"
OPERATIONS = {"read", "write", "read_modify_write", "reduce"}
PATTERNS = {"sequential", "constant_stride", "indirect", "ranged_indirect", "chained_indirect", "pointer_chase"}
SUPPORT = {"paper_specified", "code_observed", "unsupported", "unknown"}
ROLES = {"execute", "assist"}
PAYLOAD_TYPES = {"uint32", "int32", "float32", "uint64", "int64", "float64"}
OLD_VALUE = {"returned", "not_returned", "unknown", "not_applicable"}
ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]*\Z")


def require(condition, message):
    if not condition:
        raise RequestError(message)


def text(value, where):
    return identifier(value, where)


def record_id(value, where):
    text(value, where)
    require(bool(ID.fullmatch(value)), f"{where}: invalid stable identifier.")
    return value


def vocabulary(value, allowed, where):
    require(isinstance(value, str) and value in allowed, f"{where}: expected one of {sorted(allowed)}.")
    return value


def strings(value, where, *, nonempty=False):
    sequence(value, where)
    require(not nonempty or bool(value), f"{where}: must not be empty.")
    for i, item in enumerate(value):
        text(item, f"{where}[{i}]")
    return value


def references(value, allowed, where, *, nonempty=False):
    strings(value, where, nonempty=nonempty)
    require(len(value) == len(set(value)), f"{where}: duplicate references.")
    require(set(value) <= set(allowed), f"{where}: unknown reference(s): {sorted(set(value) - set(allowed))}.")
    return value


def indexed(rows, where):
    sequence(rows, where)
    out = {}
    for row in rows:
        mapping(row, where)
        key = record_id(row.get("id"), f"{where}.id")
        require(key not in out, f"{where}: duplicate ID {key!r}.")
        out[key] = row
    return out


def validate_catalog(catalog):
    """Fail on structural/provenance contradictions, not unproven hardware facts."""
    mapping(catalog, "catalog")
    require(catalog.get("format") == FORMAT, "Unsupported hardware catalog format.")
    record_id(catalog.get("catalog_id"), "catalog_id")
    text(catalog.get("revision"), "revision")
    require(catalog.get("status") == "research_reviewed_prototype", "Catalog must retain research_reviewed_prototype status.")
    sources = mapping(catalog.get("sources"), "sources")
    require(bool(sources), "At least one primary source is required.")
    for key, source in sources.items():
        record_id(key, "source ID")
        mapping(source, f"sources.{key}")
        for field in ("title", "edition", "url", "locator_basis"):
            text(source.get(field), f"sources.{key}.{field}")
        url = urlparse(source["url"])
        require(url.scheme in {"https", "http"} and bool(url.netloc) and not url.username,
                f"sources.{key}.url: use a public primary-source URL.")
        if source.get("sha256") is not None:
            require(isinstance(source["sha256"], str) and bool(re.fullmatch(r"[a-f0-9]{64}", source["sha256"])),
                    f"sources.{key}.sha256: expected lowercase SHA-256.")
    claims = mapping(catalog.get("claims"), "claims")
    require(bool(claims), "At least one located claim is required.")
    for key, claim in claims.items():
        record_id(key, "claim ID")
        mapping(claim, f"claims.{key}")
        references(claim.get("source_refs"), sources, f"claims.{key}.source_refs", nonempty=True)
        text(claim.get("locator"), f"claims.{key}.locator")
        text(claim.get("statement"), f"claims.{key}.statement")
        vocabulary(claim.get("evidence_kind"), {"paper_specification", "code_inspection", "research_inference"}, f"claims.{key}.evidence_kind")
        strings(claim.get("limitations"), f"claims.{key}.limitations")
    families = indexed(catalog.get("mechanism_families"), "mechanism_families")
    require(bool(families), "Mechanism family index is required.")
    for key, family in families.items():
        text(family.get("description"), f"mechanism_families.{key}.description")
        require("operations" not in family, "Families cannot supply inherited operation capabilities; use concrete designs.")
    questions = indexed(catalog.get("decision_questions"), "decision_questions")
    for key, question in questions.items():
        text(question.get("question"), f"decision_questions.{key}.question")
        text(question.get("why_it_matters"), f"decision_questions.{key}.why_it_matters")
        references(question.get("claim_refs"), claims, f"decision_questions.{key}.claim_refs")
    designs = indexed(catalog.get("designs"), "designs")
    require(bool(designs), "At least one concrete design/version is required.")
    if "project_selections" in catalog:
        selected = mapping(catalog["project_selections"], "project_selections")
        if "second_indirect_fetcher" in selected:
            entry = mapping(selected["second_indirect_fetcher"], "project_selections.second_indirect_fetcher")
            require(entry.get("design_id") in designs, "Selected second fetcher must reference a catalog design.")
            text(entry.get("selection_provenance"), "second fetcher.selection_provenance")
    for key, design in designs.items():
        where = f"designs.{key}"
        for field in ("name", "revision", "summary"):
            text(design.get(field), f"{where}.{field}")
        vocabulary(design.get("record_kind"), {"design_version", "configuration", "mapping"}, f"{where}.record_kind")
        references(design.get("mechanism_refs"), families, f"{where}.mechanism_refs", nonempty=True)
        references(design.get("source_refs"), sources, f"{where}.source_refs", nonempty=True)
        strings(design.get("limitations"), f"{where}.limitations")
        if "hardware_structure" in design:
            structure = mapping(design["hardware_structure"], f"{where}.hardware_structure")
            require(structure.get("view_kind") == "paper_logical_paths_not_port_netlist", "Hardware structure must retain its paper logical-path scope.")
            blocks = indexed(structure.get("blocks"), f"{where}.hardware_structure.blocks")
            for bid, block in blocks.items():
                text(block.get("description"), f"hardware_structure.{bid}.description")
                references(block.get("claim_refs"), claims, f"hardware_structure.{bid}.claim_refs", nonempty=True)
            for connection in sequence(structure.get("connections"), "hardware_structure.connections"):
                mapping(connection, "hardware_structure.connection")
                require(connection.get("from_block") in blocks and connection.get("to_block") in blocks, "Hardware structure connection has unknown endpoint.")
                text(connection.get("label"), "hardware_structure.connection.label")
                references(connection.get("claim_refs"), claims, "hardware_structure.connection.claim_refs", nonempty=True)
        # Optional meeting follow-up: explicit annotations, never capabilities
        # inherited from a family or a promise of measured performance.
        for mid, mechanism in indexed(design.get("internal_mechanisms", []), f"{where}.internal_mechanisms").items():
            mw = f"{where}.internal_mechanisms.{mid}"
            vocabulary(mechanism.get("kind"), {"buffering", "coalescing", "reordering", "issue_policy", "dependency_tracking", "completion", "other"}, f"{mw}.kind")
            state = vocabulary(mechanism.get("status"), {"described", "unknown"}, f"{mw}.status")
            refs = references(mechanism.get("claim_refs"), claims, f"{mw}.claim_refs", nonempty=state == "described")
            if state == "described":
                text(mechanism.get("description"), f"{mw}.description")
                require(any(claims[c]["evidence_kind"] in {"paper_specification", "code_inspection"} for c in refs),
                        f"{mw}: a described mechanism needs located paper/code evidence, not inference alone.")
            else:
                require(mechanism.get("description") is None and not refs, f"{mw}: unknown mechanisms must have null description and empty claims.")
        for hid, hypothesis in indexed(design.get("performance_hypotheses", []), f"{where}.performance_hypotheses").items():
            hw = f"{where}.performance_hypotheses.{hid}"
            text(hypothesis.get("description"), f"{hw}.description")
            strings(hypothesis.get("workload_conditions"), f"{hw}.workload_conditions", nonempty=True)
            strings(hypothesis.get("limiting_factors"), f"{hw}.limiting_factors", nonempty=True)
            references(hypothesis.get("claim_refs"), claims, f"{hw}.claim_refs", nonempty=True)
        interface = mapping(design.get("interface"), f"{where}.interface")
        for field in ("software_supplies", "invocation", "outputs"):
            text(interface.get(field), f"{where}.interface.{field}")
        references(interface.get("claim_refs"), claims, f"{where}.interface.claim_refs", nonempty=True)
        ops = indexed(design.get("operations"), f"{where}.operations")
        require(bool(ops), f"{where}: operation records required.")
        for op_id, op in ops.items():
            ow = f"{where}.operations.{op_id}"
            vocabulary(op.get("operation"), OPERATIONS, f"{ow}.operation")
            record_id(op.get("subtype"), f"{ow}.subtype")
            vocabulary(op.get("execution_role"), ROLES, f"{ow}.execution_role")
            vocabulary(op.get("support"), SUPPORT, f"{ow}.support")
            references(op.get("address_patterns"), PATTERNS, f"{ow}.address_patterns")
            refs = references(op.get("claim_refs"), claims, f"{ow}.claim_refs",
                              nonempty=op["support"] != "unknown")
            if op["support"] in {"paper_specified", "code_observed"}:
                expected = "paper_specification" if op["support"] == "paper_specified" else "code_inspection"
                require(any(claims[c]["evidence_kind"] == expected for c in refs), f"{ow}: support must have {expected} evidence.")
            for field, required in (("result", ("form", "validity")),
                                    ("ordering", ("scope", "description")),
                                    ("completion", ("event", "visibility"))):
                detail = mapping(op.get(field), f"{ow}.{field}")
                for name in required:
                    text(detail.get(name), f"{ow}.{field}.{name}")
                references(detail.get("claim_refs"), claims, f"{ow}.{field}.claim_refs")
            vocabulary(op["result"].get("old_value"), OLD_VALUE, f"{ow}.result.old_value")
            require(not (op["execution_role"] == "assist" and op["result"]["old_value"] == "returned"),
                    f"{ow}: assistance cannot claim to return the required operation's old value.")
            if "realization" in op:
                realization = mapping(op["realization"], f"{ow}.realization")
                vocabulary(realization.get("kind"), {"native_primitive", "documented_sequence", "mapping_role"}, f"{ow}.realization.kind")
                text(realization.get("description"), f"{ow}.realization.description")
                references(realization.get("claim_refs"), claims, f"{ow}.realization.claim_refs", nonempty=True)
            if "type_constraints" in op:
                types = mapping(op["type_constraints"], f"{ow}.type_constraints")
                references(types.get("payload_types"), PAYLOAD_TYPES, f"{ow}.type_constraints.payload_types")
                widths = sequence(types.get("index_width_bits"), f"{ow}.type_constraints.index_width_bits")
                require(all(type(w) is int and w > 0 for w in widths) and len(widths) == len(set(widths)),
                        f"{ow}.type_constraints.index_width_bits: expected unique positive integer widths.")
                text(types.get("notes"), f"{ow}.type_constraints.notes")
                references(types.get("claim_refs"), claims, f"{ow}.type_constraints.claim_refs", nonempty=bool(widths or types["payload_types"]))
            text(op.get("datatype_notes"), f"{ow}.datatype_notes")
            strings(op.get("limitations"), f"{ow}.limitations")
        for req_id, req in indexed(design.get("requirements"), f"{where}.requirements").items():
            for field in ("description", "scope"):
                text(req.get(field), f"{where}.requirements.{req_id}.{field}")
            vocabulary(req.get("verification"), {"required", "unknown"}, f"{where}.requirements.{req_id}.verification")
            references(req.get("claim_refs"), claims, f"{where}.requirements.{req_id}.claim_refs")
        for pid, parameter in indexed(design.get("parameters"), f"{where}.parameters").items():
            pw = f"{where}.parameters.{pid}"
            text(parameter.get("unit"), f"{pw}.unit")
            text(parameter.get("notes"), f"{pw}.notes")
            state = vocabulary(parameter.get("state"), {"open", "fixed_reference", "unknown"}, f"{pw}.state")
            require("value" in parameter and "domain" in parameter, f"{pw}: value and domain must be explicit, possibly null.")
            require(state == "fixed_reference" or parameter["value"] is None, f"{pw}: open/unknown parameters cannot silently fix values.")
            require(state != "fixed_reference" or parameter["value"] is not None, f"{pw}: reference value required.")
            references(parameter.get("claim_refs"), claims, f"{pw}.claim_refs",
                       nonempty=state == "fixed_reference" or parameter["domain"] is not None)
    return {"valid": True, "format": FORMAT, "designs": len(designs), "claims": len(claims),
            "scope": "Structure and evidence-reference checks only; no hardware correctness, composition legality or performance certification."}


def load_catalog(path=DEFAULT_CATALOG):
    catalog, digest = load_request(Path(path))
    validate_catalog(catalog)
    return catalog, digest


def inspect_design(catalog, design_id):
    validate_catalog(catalog)
    for design in catalog["designs"]:
        if design["id"] == design_id:
            return deepcopy(design)
    raise RequestError(f"Unknown design ID {design_id!r}.")


def query_catalog(catalog, *, operation, subtype=None, address_pattern=None,
                  require_old_value=False, execution_role=None, design_id=None,
                  payload_type=None, index_width_bits=None):
    """Retrieve operation-level evidence; no timing heuristics or requirements assumed."""
    validate_catalog(catalog)
    vocabulary(operation, OPERATIONS, "query.operation")
    if subtype is not None:
        record_id(subtype, "query.subtype")
    if address_pattern is not None:
        vocabulary(address_pattern, PATTERNS, "query.address_pattern")
    if execution_role is not None:
        vocabulary(execution_role, ROLES, "query.execution_role")
    require(type(require_old_value) is bool, "query.require_old_value must be boolean.")
    if payload_type is not None:
        vocabulary(payload_type, PAYLOAD_TYPES, "query.payload_type")
    if index_width_bits is not None:
        require(type(index_width_bits) is int and index_width_bits > 0, "query.index_width_bits must be a positive integer.")
    if design_id is not None:
        inspect_design(catalog, design_id)
    matches, excluded = [], []
    for design in sorted(catalog["designs"], key=lambda d: d["id"]):
        if design_id is not None and design["id"] != design_id:
            continue
        for op in sorted(design["operations"], key=lambda op: op["id"]):
            if op["operation"] != operation:
                continue
            if execution_role is not None and op["execution_role"] != execution_role:
                continue
            # A read prefetch can assist a gather, but cannot satisfy its returned value.
            read_assist = (operation == "read" and subtype in {"gather", "stream_load"}
                           and op["execution_role"] == "assist" and op["subtype"] == "prefetch")
            if subtype is not None and op["subtype"] != subtype and not read_assist:
                continue
            entry = {"design_id": design["id"], "design_revision": design["revision"],
                     "record_kind": design["record_kind"],
                     "operation_id": op["id"], "operation": deepcopy(op),
                     "requirement_status": "not_discharged_by_retrieval",
                     "requirements": deepcopy(design["requirements"]),
                     "design_limitations": deepcopy(design["limitations"])}
            if op["support"] == "unsupported":
                entry.update(status="excluded", reason="Explicitly unsupported in this examined configuration/path.")
                excluded.append(entry)
                continue
            if address_pattern is not None and op["address_patterns"] and address_pattern not in op["address_patterns"]:
                entry.update(status="not_covered", reason="Requested address pattern is not in this record; absence is not a universal hardware impossibility claim.")
                excluded.append(entry)
                continue
            missing = []
            if op["support"] == "unknown":
                missing.append("operation_support")
            if address_pattern is not None and not op["address_patterns"]:
                missing.append("address_pattern_support")
            type_mismatch = []
            for field, wanted in (("payload_types", payload_type), ("index_width_bits", index_width_bits)):
                if wanted is None:
                    continue
                known = op.get("type_constraints", {}).get(field, [])
                if not known:
                    missing.append(field)
                elif wanted not in known:
                    type_mismatch.append(field)
            if type_mismatch:
                entry.update(status="not_covered", reason="Requested type/width is outside the examined domain: " + ", ".join(type_mismatch))
                excluded.append(entry)
                continue
            if require_old_value:
                old = op["result"]["old_value"]
                if old in {"not_returned", "not_applicable"}:
                    entry.update(status="excluded", reason="This operation does not return the required old value.")
                    excluded.append(entry)
                    continue
                if old == "unknown":
                    missing.append("old_value_return")
            entry["missing_capability_evidence"] = missing
            entry["status"] = ("needs_evidence" if missing else "mapping_reference" if design["record_kind"] == "mapping"
                               else "assistance_only" if op["execution_role"] == "assist" else "conditional_executor")
            matches.append(entry)
    return {"catalog_id": catalog["catalog_id"], "revision": catalog["revision"],
            "query": {"operation": operation, "subtype": subtype, "address_pattern": address_pattern,
                      "require_old_value": require_old_value, "execution_role": execution_role, "design_id": design_id,
                      "payload_type": payload_type, "index_width_bits": index_width_bits},
            "matches": matches, "excluded": excluded,
            "ordering": "Stable design/operation IDs, not performance rank.",
            "scope": "Evidence lookup only. Requirements, aliasing, concurrency, types and completion must be established for a particular workload mapping."}



def navigation_tree(catalog):
    """Derive a non-exclusive navigation tree from recorded operations only.

    A design appears on multiple paths when it has multiple capabilities. Leaves
    retain support and requirements; reaching a leaf is not a compatibility proof.
    """
    validate_catalog(catalog)
    branches = {}
    for design in sorted(catalog["designs"], key=lambda d: d["id"]):
        for op in sorted(design["operations"], key=lambda o: o["id"]):
            role = "mapping_reference" if design["record_kind"] == "mapping" else op["execution_role"]
            for pattern in op["address_patterns"] or ["unknown"]:
                leaves = branches.setdefault(op["operation"], {}).setdefault(role, {}).setdefault(pattern, [])
                leaves.append({"design_id": design["id"], "revision": design["revision"],
                               "operation_id": op["id"], "subtype": op["subtype"],
                               "support": op["support"], "claim_refs": deepcopy(op["claim_refs"]),
                               "requirement_ids": [r["id"] for r in design["requirements"]],
                               "realization": deepcopy(op.get("realization"))})
    return {"kind": "derived_navigation_tree", "catalog_id": catalog["catalog_id"],
            "revision": catalog["revision"], "levels": ["operation", "execution_role_or_mapping_reference", "address_pattern"],
            "branches": branches, "decision_questions": deepcopy(catalog["decision_questions"]),
            "interpretation": "Non-exclusive classification of source-scoped operation records. Unsupported and unknown leaves remain explicit. This tree does not select winners, discharge requirements or enumerate legal component compositions."}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    sub.add_parser("list")
    sub.add_parser("questions")
    sub.add_parser("tree")
    sub.add_parser("inspect").add_argument("id")
    query = sub.add_parser("query")
    query.add_argument("--operation", choices=sorted(OPERATIONS), required=True)
    query.add_argument("--subtype")
    query.add_argument("--pattern", choices=sorted(PATTERNS))
    query.add_argument("--require-old-value", action="store_true")
    query.add_argument("--role", choices=sorted(ROLES))
    query.add_argument("--design")
    query.add_argument("--payload-type", choices=sorted(PAYLOAD_TYPES))
    query.add_argument("--index-width", type=int)
    args = parser.parse_args(argv)
    try:
        catalog, digest = load_catalog(args.catalog)
        if args.command == "validate":
            result = {**validate_catalog(catalog), "sha256": digest}
        elif args.command == "list":
            result = [{k: d[k] for k in ("id", "name", "revision", "record_kind", "summary")} for d in catalog["designs"]]
        elif args.command == "questions":
            result = catalog["decision_questions"]
        elif args.command == "tree":
            result = navigation_tree(catalog)
        elif args.command == "inspect":
            result = inspect_design(catalog, args.id)
        else:
            result = query_catalog(catalog, operation=args.operation, subtype=args.subtype,
                                   address_pattern=args.pattern, require_old_value=args.require_old_value,
                                   execution_role=args.role, design_id=args.design,
                                   payload_type=args.payload_type, index_width_bits=args.index_width)
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except (RequestError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
