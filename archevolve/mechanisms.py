"""Optional catalog mechanism annotations; no scheduling inferred from a gather."""

from copy import deepcopy

from tools.render_mermaid import label

KINDS = ("buffering", "coalescing", "reordering", "issue_policy", "dependency_tracking", "completion")


def mechanism_context(design):
    """Copy curated annotations and add explicitly unknown checklist items."""
    annotations = deepcopy(design.get("internal_mechanisms", []))
    present = {m["kind"] for m in annotations}
    for kind in KINDS:
        if kind not in present:
            annotations.append({"id": "unrecorded-" + kind, "kind": kind, "status": "unknown",
                                "description": None, "claim_refs": []})
    return {"annotations": annotations,
            "missing_kinds": [kind for kind in KINDS if not any(
                m["kind"] == kind and m["status"] == "described" for m in annotations)],
            "performance_hypotheses": deepcopy(design.get("performance_hypotheses", [])),
            "hardware_structure": deepcopy(design.get("hardware_structure")),
            "scope": "Curated descriptions and explicit unknowns; no cycle model or inferred physical topology."}


def render_mechanisms(candidate):
    """Annotations without edges: a description does not establish wiring."""
    lines = ["flowchart TB", '  title["Internal mechanism evidence — annotations, not physical wiring"]:::notice']
    for index, m in enumerate(candidate["mechanism_context"]["annotations"]):
        description = m["description"] if m["status"] == "described" else "UNKNOWN — Eric's mechanism annotation needed"
        lines.append(f'  m{index}["{label(m["kind"], m["status"], description, "Claims: " + ", ".join(m["claim_refs"]))}"]:::annotation')
    lines += ["  classDef notice fill:#dbeafe,stroke:#2563eb,color:#172554",
              "  classDef annotation fill:#f8fafc,stroke:#94a3b8,color:#334155,stroke-dasharray:3 3"]
    return "\n".join(lines) + "\n"


def render_structure(candidate):
    """Only explicitly supplied source-backed logical paths; no port ABI inferred."""
    structure = candidate["mechanism_context"].get("hardware_structure")
    if not structure:
        return None
    nodes = {b["id"]: f"n{i}" for i, b in enumerate(structure["blocks"])}
    lines = ["---", 'config: {"theme": "neutral", "layout": "elk", "flowchart": {"htmlLabels": true, "wrappingWidth": 220, "nodeSpacing": 24, "rankSpacing": 45}}', "---",
             "flowchart TB", '  scope["Paper logical paths — not a port netlist or a proved BFS mapping"]:::notice']
    for block in structure["blocks"]:
        lines.append(f'  {nodes[block["id"]]}["{label(block["id"], block["description"])}"]')
    for edge in structure["connections"]:
        lines.append(f'  {nodes[edge["from_block"]]} -->|"{label(edge["label"])}"| {nodes[edge["to_block"]]}')
    lines.append("  classDef notice fill:#fef3c7,stroke:#d97706,color:#78350f")
    return "\n".join(lines) + "\n"
