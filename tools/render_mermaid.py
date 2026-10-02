#!/usr/bin/env python3
"""Convert provisional hardware-request YAML to Mermaid and a review report.

This is a diagram converter, not a hardware selector or correctness evaluator.
Unknown feature/capability fields are retained in the report's YAML snapshot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import textwrap
from pathlib import Path
from typing import Any

import yaml


class RequestError(ValueError):
    """A malformed or unsupported diagram input."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loading that refuses silently overwritten mapping keys."""


def _unique_mapping(loader: UniqueKeyLoader, node: Any, deep: bool = False) -> dict:
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise RequestError("YAML mapping keys must be strings; quote ambiguous keys.")
        if key in result:
            raise RequestError(f"Duplicate YAML key {key!r} on line {key_node.start_mark.line + 1}.")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def mapping(value: Any, where: str) -> dict:
    if not isinstance(value, dict):
        raise RequestError(f"{where}: expected a mapping.")
    return value


def sequence(value: Any, where: str) -> list:
    if not isinstance(value, list):
        raise RequestError(f"{where}: expected a list.")
    return value


def identifier(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RequestError(f"{where}: expected a non-empty string.")
    return value


def load_request(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    try:
        data = yaml.load(raw.decode("utf-8"), Loader=UniqueKeyLoader)
        # A JSON-compatible representation avoids YAML-specific objects or cycles.
        json.dumps(data, allow_nan=False)
    except (yaml.YAMLError, UnicodeError, TypeError, ValueError) as exc:
        raise RequestError(f"Cannot read {path.name}: {exc}") from exc
    return mapping(data, "request"), hashlib.sha256(raw).hexdigest()


def validate_request(request: dict, *, allow_template: bool = False) -> None:
    """Check graph integrity only; leave evolving feature schemas flexible."""
    mapping(request, "request")
    if request.get("contract_version") != "draft-0.2":
        raise RequestError("Expected contract_version: draft-0.2; legacy SPARTA schemas are not supported.")
    kind = request.get("record_kind")
    if not isinstance(kind, str) or kind not in {"agent_proposal", "human_proposal", "illustrative", "template"}:
        raise RequestError("record_kind must be agent_proposal, human_proposal, illustrative, or template.")
    if kind == "template" and not allow_template:
        raise RequestError("Unfilled template: supply a real/synthetic request, or use --allow-template for a labeled preview.")
    identifier(request.get("kernel_id"), "kernel_id")
    candidate_ids = set()
    for ci, candidate in enumerate(sequence(request.get("candidates"), "candidates")):
        where = f"candidates[{ci}]"
        mapping(candidate, where)
        cid = identifier(candidate.get("id"), f"{where}.id")
        if cid in candidate_ids:
            raise RequestError(f"Duplicate candidate ID {cid!r}.")
        candidate_ids.add(cid)
        hardware = mapping(candidate.get("hardware"), f"{where}.hardware")
        blocks = sequence(hardware.get("blocks"), f"{where}.hardware.blocks")
        if not blocks:
            raise RequestError(f"Candidate {cid!r} has no hardware blocks to render.")
        block_ids = set()
        ports = {}
        for bi, block in enumerate(blocks):
            bw = f"{where}.hardware.blocks[{bi}]"
            mapping(block, bw)
            bid = identifier(block.get("id"), f"{bw}.id")
            if bid in block_ids:
                raise RequestError(f"Candidate {cid!r}: duplicate block ID {bid!r}.")
            block_ids.add(bid)
            block_port_ids = set()
            for direction in ("inputs", "outputs"):
                for pi, port in enumerate(sequence(block.get(direction, []), f"{bw}.{direction}")):
                    pw = f"{bw}.{direction}[{pi}]"
                    mapping(port, pw)
                    pid = identifier(port.get("id"), f"{pw}.id")
                    if pid in block_port_ids:
                        raise RequestError(f"Block {bid!r}: duplicate port ID {pid!r} (including across directions).")
                    block_port_ids.add(pid)
                    role = port.get("endpoint_role", "unknown")
                    if not isinstance(role, str) or role not in {"host-facing", "memory-facing", "internal", "unknown"}:
                        raise RequestError(f"{pw}.endpoint_role: unsupported role {role!r}.")
                    width = port.get("element_bytes")
                    if width is not None and (type(width) is not int or width <= 0):
                        raise RequestError(f"{pw}.element_bytes must be a positive integer or null.")
                    ports[(bid, pid)] = direction
            parameter_names = set()
            for parameter in sequence(block.get("parameters", []), f"{bw}.parameters"):
                mapping(parameter, f"{bw}.parameters item")
                name = identifier(parameter.get("name"), f"{bw}.parameters.name")
                if name in parameter_names:
                    raise RequestError(f"Block {bid!r}: duplicate parameter {name!r}.")
                parameter_names.add(name)
                state, value = parameter.get("state"), parameter.get("value")
                if not isinstance(state, str) or state not in {"open", "fixed"}:
                    raise RequestError(f"Parameter {name!r}: state must be open or fixed.")
                if state == "open" and value is not None:
                    raise RequestError(f"Parameter {name!r}: an open parameter must have a null/omitted value.")
                if state == "fixed" and value is None:
                    raise RequestError(f"Parameter {name!r}: a fixed parameter needs a value.")
        edges = set()
        for edge in sequence(hardware.get("connections", []), f"{where}.hardware.connections"):
            mapping(edge, "connection")
            source = tuple(identifier(edge.get(k), f"connection.{k}") for k in ("from_block", "from_port"))
            target = tuple(identifier(edge.get(k), f"connection.{k}") for k in ("to_block", "to_port"))
            if source not in ports or target not in ports:
                raise RequestError(f"Candidate {cid!r}: connection has an unknown block/port: {source!r} -> {target!r}.")
            if ports[source] != "outputs" or ports[target] != "inputs":
                raise RequestError(f"Candidate {cid!r}: connections must run from an output port to an input port.")
            if (source, target) in edges:
                raise RequestError(f"Candidate {cid!r}: duplicate connection {source!r} -> {target!r}.")
            edges.add((source, target))


def display(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, (dict, list, bool)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def label(*parts: Any) -> str:
    """Escape user text as Mermaid decimal entities; only we insert line breaks."""
    lines = []
    dangerous = set('"<>#&`|\\[]{}')
    for part in parts:
        for line in display(part).splitlines() or [""]:
            for wrapped in textwrap.wrap(line, width=48, break_long_words=True) or [""]:
                lines.append("".join(f"#{ord(ch)};" if ch in dangerous or ord(ch) < 32 else ch for ch in wrapped))
    return "<br/>".join(lines)


def fenced(text: str, language: str) -> str:
    fence = "`" * max(3, 1 + max((len(m.group()) for m in re.finditer(r"`+", text)), default=0))
    return f"{fence}{language}\n{text.rstrip()}\n{fence}"


def render_candidate(request: dict, candidate: dict) -> str:
    """Render already-validated data; no model calls and no inferred signal edges."""
    kind = request["record_kind"].upper()
    title = f"{kind} | {request['kernel_id']} | {candidate['id']} | {display(candidate.get('status'))}"
    config = {"theme": "neutral", "layout": "elk", "flowchart": {"htmlLabels": True, "wrappingWidth": 320, "nodeSpacing": 24, "rankSpacing": 60, "padding": 12}}
    lines = ["---", "title: " + json.dumps(title, ensure_ascii=False), "config: " + json.dumps(config), "---", "flowchart LR"]
    ports = {}
    for bi, block in enumerate(candidate["hardware"]["blocks"]):
        group = f"b{bi}"
        # Mermaid can overlap a multiline subgraph title with its children.
        # Keep the heading on one line and put component details in the annotation.
        header = label(block["id"]).replace("<br/>", " ")
        lines += [f'  subgraph {group}["{header}"]', "    direction TB"]
        details = ["Component: " + display(block.get("component_ref")), "Function: " + display(block.get("function"))]
        contract = block.get("operation_contract")
        if contract:
            realization = contract.get("realization", {})
            details.append("Realization: " + display(realization.get("kind")))
            if block.get("requested_payload_types"):
                details.append("Requested payload: " + ", ".join(block["requested_payload_types"]))
            if block.get("requested_index_width_bits"):
                details.append("Requested index bits: " + ", ".join(str(w) for w in block["requested_index_width_bits"]))
            if block.get("missing_capability_evidence"):
                details.append("Evidence missing: " + ", ".join(block["missing_capability_evidence"]))
        if block.get("reference_parameters"):
            details.append("Reference settings in YAML; none selected")
        if block.get("unknown_parameters"):
            details.append("Parameter domains unresolved: " + ", ".join(p["id"] for p in block["unknown_parameters"]))
        for parameter in block.get("parameters", []):
            value = "OPEN" if parameter["state"] == "open" else display(parameter["value"])
            details.append(f"{parameter['name']}: {value} [{display(parameter.get('unit'))}]")
        lines.append(f'    {group}_info["{label(*details)}"]:::annotation')
        for direction, short in (("inputs", "in"), ("outputs", "out")):
            for pi, port in enumerate(block.get(direction, [])):
                node = f"{group}_{short}{pi}"
                ports[(block["id"], port["id"])] = node
                role = port.get("endpoint_role", "unknown")
                style = {"host-facing": "hostPort", "memory-facing": "memoryPort", "internal": "internalPort", "unknown": "unknownPort"}[role]
                body = label(f"{short.upper()}: {port['id']}", port.get("payload"),
                             f"{display(port.get('type'))}; {display(port.get('element_bytes'))} B/element", role)
                lines.append(f'    {node}["{body}"]:::{style}')
        lines.append("  end")
    if candidate.get("mechanism_context"):
        # Descriptions are evidence annotations, not fabricated blocks or edges.
        from textwrap import shorten
        context = candidate["mechanism_context"]
        details = ["Internal mechanism annotations (no wiring implied)"]
        details += [m["kind"] + ": " + shorten(m["description"], width=110, placeholder=" ...")
                    for m in context["annotations"] if m["status"] == "described"]
        if any(m["status"] == "described" for m in context["annotations"]):
            details.append("Full mechanism descriptions in YAML")
        if context["missing_kinds"]:
            details.append("Internal detail unrecorded: " + ", ".join(context["missing_kinds"]))
        lines.append(f'  mechanism_info["{label(*details)}"]:::annotation')
    for edge in candidate["hardware"].get("connections", []):
        source = ports[(edge["from_block"], edge["from_port"])]
        target = ports[(edge["to_block"], edge["to_port"])]
        edge_label = f'|"{label(edge["label"])}"|' if edge.get("label") else ""
        lines.append(f"  {source} -->{edge_label} {target}")
    lines += [
        "  classDef annotation fill:#f8fafc,stroke:#94a3b8,color:#334155,stroke-dasharray:3 3",
        "  classDef hostPort fill:#dbeafe,stroke:#2563eb,color:#172554",
        "  classDef memoryPort fill:#dcfce7,stroke:#16a34a,color:#14532d",
        "  classDef internalPort fill:#f1f5f9,stroke:#64748b,color:#0f172a",
        "  classDef unknownPort fill:#fef3c7,stroke:#d97706,color:#78350f",
    ]
    return "\n".join(lines) + "\n"


def build_artifacts(request: dict, source_name: str, source_sha256: str,
                    *, candidate_id: str | None = None, allow_template: bool = False) -> dict[str, str]:
    validate_request(request, allow_template=allow_template)
    selected = request["candidates"]
    if candidate_id is not None:
        selected = [c for c in selected if c["id"] == candidate_id]
        if not selected:
            raise RequestError(f"Candidate {candidate_id!r} was not found.")
    metadata = {key: request.get(key) for key in (
        "contract_version", "record_kind", "kernel_id", "input_ref", "input_revision", "catalog_ref", "catalog_revision")}
    metadata.update(source_file=source_name, source_sha256=source_sha256)
    artifacts = {"request.snapshot.yaml": yaml.safe_dump(request, sort_keys=False, allow_unicode=True)}
    report = ["# Hardware candidate diagrams", "",
              "Generated deterministically from the request YAML. This is a structural view, not a hardware correctness or performance verdict.", ""]
    if request["record_kind"] in {"illustrative", "template"}:
        report += [f"**{request['record_kind'].upper()}: not an evaluated hardware design.**", ""]
    report += [fenced(yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True), "yaml"), ""]
    if request.get("workload_summary") is not None:
        report += ["## Workload context", "", fenced(yaml.safe_dump(request["workload_summary"], sort_keys=False, allow_unicode=True), "yaml"), ""]
    if request.get("interpretation_notes") is not None:
        report += ["## Interpretation notes", "", fenced(yaml.safe_dump(request["interpretation_notes"], allow_unicode=True), "yaml"), ""]
    report += [
               "Blue ports face the host; green ports face memory; gray ports are internal; amber ports have an unknown role. Dashed boxes are explanatory annotations, not additional hardware components. Only connections explicitly present in the YAML are drawn. Unconnected ports remain visible.", "",
               "Open values remain OPEN. Read the candidate details for constraints, behavior, and unresolved conditions.", ""]
    if request.get("representation") == "source_scoped_operation_interface_views":
        report += ["**Operation-interface view:** boxes represent catalog operation contracts, including documented sequences. They are not physical components or a proof that the displayed operations compose. Reference settings are recorded separately from chosen values; unknown ABI details remain unknown.", ""]
    manifest = {"source": metadata, "diagrams": []}
    for index, candidate in enumerate(selected, start=1):
        filename = f"candidate-{index:02d}.mmd"
        diagram = render_candidate(request, candidate)
        artifacts[filename] = diagram
        manifest["diagrams"].append({"candidate_id": candidate["id"], "file": filename})
        report += [f"## Candidate {index}", "", f"[Mermaid source]({filename})", "", fenced(diagram, "mermaid"), "",
                   "### Full candidate details", "", fenced(yaml.safe_dump(candidate, sort_keys=False, allow_unicode=True), "yaml"), ""]
    if not selected:
        report += ["No candidates were supplied. No hardware blocks have been invented.", ""]
    report += ["## Clarification requests", "", fenced(yaml.safe_dump(request.get("clarification_requests", []), allow_unicode=True), "yaml"), ""]
    artifacts["README.md"] = "\n".join(report)
    artifacts["manifest.json"] = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    return artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="draft-0.2 hardware-request YAML")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--candidate", help="Render one candidate by its exact ID")
    parser.add_argument("--allow-template", action="store_true", help="Render a clearly labeled unfilled template preview")
    parser.add_argument("--overwrite", action="store_true", help="Replace generated files with matching names")
    args = parser.parse_args(argv)
    try:
        request, digest = load_request(args.input)
        artifacts = build_artifacts(request, args.input.name, digest,
                                    candidate_id=args.candidate, allow_template=args.allow_template)
        targets = [args.output_dir / name for name in artifacts]
        if any(path.resolve() == args.input.resolve() for path in targets):
            raise RequestError("The output directory would overwrite the source request; choose a separate directory.")
        conflicts = [path.name for path in targets if path.exists()]
        if conflicts and not args.overwrite:
            raise RequestError("Generated files already exist: " + ", ".join(conflicts) + ". Use --overwrite or a new directory.")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in artifacts.items():
            (args.output_dir / filename).write_text(content, encoding="utf-8")
        count = len(json.loads(artifacts["manifest.json"])["diagrams"])
        print(f"Wrote {count} Mermaid diagram(s) and review report to {args.output_dir}")
        return 0
    except (RequestError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
