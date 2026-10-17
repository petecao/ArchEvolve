# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/synthesis/synthesize.py (prompt rendering, contract-only
#         workspace, probe compile of the returned header)
"""Synthesis stage: a provider writes a backend header for one family's hook.

Kept from Extensa: the workspace holds the contract and the agent-visible spec only
(never certification cases, witnesses or prior generated backends); the returned header
must compile against the family's adapter probe before certification.

SWDB changes (2026-10-03 ET): the call goes through SWDB's provider launcher role
`synthesis` (guarded workspace, structured output `{entry, files, unresolved}`); one
call per attempt (charged by the campaign ledger, D7) instead of an internal retry loop;
MemAcc's write-guard hook and DataLayoutAPI worktree are replaced by the launcher's
guard and the explicit file mapping.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from swdb.extensa.synthesis.families import FAMILIES, canonical_contract_json, contract_sha256
from swdb.extensa.synthesis.shape_classes import SHAPE_CLASSES
from swdb.extensa.synthesis.spec import SynthesisSpec, agent_visible_view
from swdb.extensa.synthesis.targets.base import TargetHarness

PROMPT = """\
Synthesize a C++11 backend for the `{family}` family.

Contract: CONTRACT.json (sha256 {contract_sha256}); output equivalence {equivalence}.
Intent: {intent}
Target: TARGET.json. Goal: {goal}

Write one header `backends/{basename}` defining `struct SynthBackend` with exactly this
static member function template:
  {hook}
{hint}
The header may include only standard headers (<...>). No hardware API, no timing, no
I/O. Return it in `files` and describe it in `entry` (`name`, `summary`).
"""


@dataclass(frozen=True)
class SynthesisOutcome:
    ok: bool
    header_text: Optional[str]
    entry: dict
    reason: str
    infrastructure_error: bool = False


def render_prompt(spec: SynthesisSpec, contract: dict, basename: str) -> str:
    view = agent_visible_view(spec)
    sc = SHAPE_CLASSES[FAMILIES[spec.family].shape_class]
    return PROMPT.format(family=spec.family, contract_sha256=contract_sha256(contract),
                         equivalence=contract["postconditions"]["output_equivalence"],
                         intent=contract.get("intent", ""), goal=view["goal"], basename=basename,
                         hook=sc.hook, hint=sc.test_hint)


def run_synthesis(spec: SynthesisSpec, contract: dict, target: TargetHarness, session_dir: Path, *,
                  invoker: Callable[..., dict]) -> SynthesisOutcome:
    """One charged synthesis attempt: call, then the adapter probe compile."""
    if spec.family not in FAMILIES:
        return SynthesisOutcome(False, None, {}, f"unknown synthesis family {spec.family!r}")
    sc = SHAPE_CLASSES[FAMILIES[spec.family].shape_class]
    session_dir = Path(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)
    basename = f"synth_{spec.target.name}_{spec.family}.hh".replace("-", "_")
    files = {"CONTRACT.json": canonical_contract_json(contract),
             "TARGET.json": json.dumps(agent_visible_view(spec), indent=2) + "\n"}
    try:
        response = invoker(files=files, prompt=render_prompt(spec, contract, basename))
    except Exception as exc:                          # noqa: BLE001 - recorded as infrastructure
        return SynthesisOutcome(False, None, {}, f"synthesis call failed: {exc}", infrastructure_error=True)
    produced = {f.get("path"): f.get("content") for f in (response or {}).get("files", [])}
    text = produced.get(f"backends/{basename}")
    if not isinstance(text, str):
        return SynthesisOutcome(False, None, {}, f"no backends/{basename} was returned")
    header = session_dir / basename
    header.write_text(text)
    probe = session_dir / "probe.cpp"
    probe.write_text(sc.probe.format(header=header.resolve()))
    build = target.build([probe], session_dir / "probe", sanitize=False)
    if not build.ok:
        return SynthesisOutcome(False, text, dict(response.get("entry") or {}),
                                f"header failed the adapter probe compile: {build.log[-1500:]}")
    return SynthesisOutcome(True, text, dict(response.get("entry") or {}), "header compiles; probe links")
