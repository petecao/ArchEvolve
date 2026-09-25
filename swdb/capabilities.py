"""Source-backed accelerator contracts and fail-closed proposal checks.

Updated: 2026-09-25. A supported declaration is not an executable build receipt.
"""

import json


def query(args):
    from swdb.cli import Failure, _require_valid

    store = _require_valid(args.records)
    target = store.get(args.target, "hardware_target")
    if target is None:
        raise Failure(f"unknown hardware target {args.target!r}")
    operations = [record.data for record in store.of_kind("operation")
                  if record.id in target["operations"]]
    return {"message_version": "1.0", "producer": "swdb", "target": target,
            "operations": sorted(operations, key=lambda item: item["id"]),
            "evidence_limit": "Source/model support is separate from executable readiness and measured behavior."}


def check_requirements(request, store):
    """Return a durable failure reason, or None for supported exact requirements.

    A wrapper is a named sequence of requirements, never a new capability. The
    evaluator must independently validate a build receipt before real execution.
    """
    requirements = request.get("required_operations", [])
    if not isinstance(requirements, list):
        return "required_operations must be a list"
    if not requirements:
        return None
    target_id = request.get("hardware_target")
    if not isinstance(target_id, str):
        return "required accelerator operations require an exact hardware_target"
    target = store.get(target_id, "hardware_target")
    if target is None:
        return f"unknown hardware target {target_id!r}"
    executable = request.get("require_executable_backend", False)
    if not isinstance(executable, bool):
        return "require_executable_backend must be boolean"
    if executable and (target["backend"]["readiness"] not in {"built", "verified"}
                       or not target["backend"]["build_evidence"]):
        return f"target {target_id!r} has no identified executable backend build"
    queue = [(item, 0) for item in requirements]
    count = 0
    while queue:
        item, depth = queue.pop(0)
        count += 1
        if count > 128 or depth > 8:
            return "operation requirement expansion exceeds the 128-entry/eight-level bound"
        if not isinstance(item, dict):
            return "operation requirements must be mappings with exact interface/model identity"
        if "wrapper" in item:
            if (set(item) != {"wrapper", "requires"} or not isinstance(item["wrapper"], str)
                    or not item["wrapper"].strip() or not isinstance(item["requires"], list)
                    or not item["requires"]):
                return "a wrapper requires a nonempty named sequence of underlying operation requirements"
            queue.extend((child, depth + 1) for child in item["requires"])
            continue
        required = {"operation", "interface", "interface_version", "model_revision"}
        if not required <= item.keys() or item.keys() - (required | {"semantics"}):
            return "operation requires operation, interface, interface_version, model_revision and optional semantics only"
        if any(not isinstance(item[key], str) or not item[key].strip() for key in required):
            return "operation and interface/model identities must be nonempty strings"
        name = item["operation"]
        op = store.get(name, "operation")
        if op is None or name not in target["operations"]:
            return f"operation {name!r} is unsupported by target {target_id!r}"
        expected = (target["interface"]["id"], target["interface"]["version"], target["model"]["revision"])
        actual = (item["interface"], item["interface_version"], item["model_revision"])
        contract = (op["interface"]["id"], op["interface"]["version"], op["model"]["revision"])
        if actual != expected or contract != expected or op["model"]["id"] != target["model"]["id"]:
            return f"operation {name!r} has a conflicting interface/version/model requirement"
        if op["support"] != "source_supported" or op["backend"] != target["backend"]["id"]:
            return f"operation {name!r} has unresolved implementing backend support"
        if not op["declaration_evidence"] or not op["implementation_evidence"]:
            return f"operation {name!r} lacks source/model evidence"
        semantics = item.get("semantics", {})
        if not isinstance(semantics, dict):
            return "required semantics must be a mapping"
        for key, value in semantics.items():
            fact = op["semantics"].get(key)
            if not fact or fact["state"] != "supported":
                return f"operation {name!r} required semantic property {key!r} is unsupported or unknown"
            # JSON comparison distinguishes true from 1; Python equality does not.
            try:
                same = json.dumps(value, sort_keys=True, allow_nan=False) == json.dumps(fact["value"], sort_keys=True, allow_nan=False)
            except (TypeError, ValueError):
                same = False
            if not same:
                return f"operation {name!r} conflicts with required semantic property {key!r}"
    return None
