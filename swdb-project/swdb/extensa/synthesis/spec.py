# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/synthesis/spec.py (TargetSpec, SynthesisSpec, loader,
#         agent_visible_view)
"""Synthesis spec: the goal and target a synthesis call works toward.

Discipline kept from Extensa: only family, target and goal may reach a provider
prompt (`agent_visible_view`). SWDB changes (2026-10-03 ET): the only harness is
`cpu_like` (non-CPU targets are not ported); the witness block and MEMACC_ROOT flag
expansion are dropped; the spec is a plain mapping (a campaign file section or YAML).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Tuple

from swdb.extensa.synthesis.families import FAMILIES


class SpecError(ValueError):
    pass


@dataclass(frozen=True)
class TargetSpec:
    name: str
    isa: str
    cc: str
    flags: Tuple[str, ...]
    capabilities: Dict[str, object] = field(default_factory=dict)
    harness: str = "cpu_like"
    constraints: Dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SynthesisSpec:
    family: str
    target: TargetSpec
    goal: str


TARGET_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def load_doc(d: object) -> SynthesisSpec:
    if not isinstance(d, dict):
        raise SpecError("spec must be a mapping")
    fam = d.get("family")
    if fam not in FAMILIES:
        raise SpecError(f"unknown family: {fam!r} (known: {sorted(FAMILIES)})")
    t = d.get("target")
    if not isinstance(t, dict):
        raise SpecError("missing/invalid 'target' block")
    name = str(t.get("name", "")).strip()
    if not TARGET_NAME_RE.fullmatch(name):
        raise SpecError("target.name must be a lowercase slug using letters, digits, and hyphens")
    harness = str(t.get("harness") or "cpu_like")
    if harness != "cpu_like":
        raise SpecError("only the cpu_like harness is ported (non-CPU targets are out of scope)")
    tc = t.get("toolchain") or {}
    target = TargetSpec(name=name, isa=str(t.get("isa", "")), cc=str(tc.get("cc", "c++")),
                        flags=tuple(str(x) for x in (tc.get("flags") or [])),
                        capabilities=dict(t.get("capabilities") or {}), harness=harness,
                        constraints=dict(t.get("constraints") or {}))
    goal = str(d.get("goal", "")).strip()
    if not goal:
        raise SpecError("missing 'goal'")
    return SynthesisSpec(family=fam, target=target, goal=goal)


def load_spec(path: Path) -> SynthesisSpec:
    from swdb import yamlio
    return load_doc(yamlio.load(Path(path)))


def agent_visible_view(spec: SynthesisSpec) -> dict:
    """The ONLY spec content permitted near a provider prompt."""
    return {"family": spec.family,
            "target": {"name": spec.target.name, "harness": spec.target.harness, "isa": spec.target.isa,
                       "cc": spec.target.cc, "flags": list(spec.target.flags),
                       "capabilities": dict(spec.target.capabilities),
                       "constraints": dict(spec.target.constraints)},
            "goal": spec.goal}
