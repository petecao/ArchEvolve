"""Bind original standard-library provenance to every launch; created 2026-10-15 ET.

Generated C models have their separate model-text proof boundary. These plans bind
the original C++ translation unit before any checked ownership/helper projection.
"""
import copy
import hashlib
import json
from pathlib import Path

from swdb import stdlib_provenance


class Refused(ValueError):
    pass


def needed(lowering):
    return stdlib_provenance.needed((*lowering.models, *lowering.std_models), lowering.allocation)


def bind(context, lowering, source, *, includes=(), defines=(), side="unit"):
    """Retain the original certificate or return its explicit prelaunch refusal."""
    if not needed(lowering):
        return None
    certificate = copy.deepcopy(lowering.stdlib_provenance)
    if not certificate:
        certificate = {"verdict": "refused", "reason": "standard substitution has no original-TU certificate"}
    reports = context.setdefault("settings", {}).setdefault("stdlib_provenance", {})
    reports[side] = certificate
    if side == "unit":
        # The ordinary single-subject public record keeps its diagnostic at the top.
        reports.update(verdict=certificate["verdict"], reason=certificate.get("reason", ""))
    if certificate.get("verdict") != "passed":
        return certificate.get("reason", "original standard declaration provenance refused")
    if certificate.get("models") != sorted(set((*lowering.models, *lowering.std_models))):
        reason = "standard substitution certificate does not cover the lowered model/type set"
        reports[side] = {"verdict": "refused", "reason": reason, "source_certificate": certificate}
        if side == "unit":
            reports.update(verdict="refused", reason=reason)
        return reason
    if certificate.get("substitution_requests") != list(lowering.stdlib_substitutions):
        reason = "standard substitution certificate does not cover the printer's exact call requests"
        reports[side] = {"verdict": "refused", "reason": reason, "source_certificate": certificate}
        if side == "unit":
            reports.update(verdict="refused", reason=reason)
        return reason
    options = {"includes": tuple(map(str, includes)), "defines": tuple(defines),
               "models": tuple(certificate["models"]),
               "substitutions": copy.deepcopy(lowering.stdlib_substitutions)}
    context.setdefault("stdlib_sources", {})[side] = {
        "source": Path(source), "lowering": lowering, "certificate": certificate, "options": options}
    folder = context.get("wp_dir") or context.get("out")
    if folder is not None:
        path = Path(folder) / f"stdlib_provenance_{side}.json"
        text = json.dumps(certificate, sort_keys=True, indent=2) + "\n"
        path.write_text(text)
        context["stdlib_sources"][side].update(certificate_path=path, certificate_text=text)
        context.setdefault("reports", []).append((f"stdlib_provenance_{side}", path))
    return None


def recheck(context, lowering=None):
    """Reparse the original source/headers in the exact planned compiler context."""
    from swdb import c_lowering
    lowering = lowering or context.get("lowering")
    sides = ({"candidate": lowering, "baseline": context["baseline_lowering"]}
             if context.get("baseline_lowering") is not None else {"unit": lowering})
    plans = context.get("stdlib_sources") or {}
    for side, subject in sides.items():
        if subject is not None and needed(subject) and side not in plans:
            raise Refused(f"{side} standard substitution has no original source plan")
    checked = {}
    for side, plan in plans.items():
        certificate = plan["certificate"]
        if plan.get("certificate_path"):
            try:
                retained = plan["certificate_path"].read_text()
            except OSError as exc:
                raise Refused(f"retained original standard provenance artifact is unavailable: {exc}") from None
            if retained != plan["certificate_text"]:
                raise Refused("retained original standard provenance artifact changed after planning")
        if plan["lowering"].stdlib_provenance != certificate:
            raise Refused("original standard provenance certificate changed after planning")
        if tuple(plan["lowering"].stdlib_substitutions) != tuple(plan["options"]["substitutions"]):
            raise Refused("original standard substitution requests changed after planning")
        recorded = context.get("settings", {}).get("stdlib_provenance", {}).get(side)
        if recorded != certificate:
            raise Refused("recorded original standard provenance changed after planning")
        reason = stdlib_provenance.check(certificate, c_lowering.locate(), plan["source"], **plan["options"])
        if reason:
            raise Refused(reason)
        checked[side] = hashlib.sha256(json.dumps(certificate, sort_keys=True).encode()).hexdigest()
    return checked
