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
