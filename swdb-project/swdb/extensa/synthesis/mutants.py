# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/synthesis/mutants.py (variant pool, gate-time rng
#         selection, write_mutant)
"""Injected-bad mutant backends: the mutation gate's ground truth.

A generated test suite is accepted only if it kills a mutant. The variant is chosen
at gate time with an rng the test author never sees. SWDB change (2026-10-03 ET):
mutant headers are self-contained (no DataLayoutAPI include).
"""
from __future__ import annotations

import random
import secrets
from pathlib import Path
from typing import Dict, List, Optional

from swdb.extensa.synthesis.families import FAMILIES
from swdb.extensa.synthesis.shape_classes import SHAPE_CLASSES

_HEADER = """\
#pragma once
#include <cstddef>
#include <cstdint>
#include <vector>
// MUTANT ({family}/{variant}) -- used ONLY by the mutation gate. Never shipped.
struct SynthBackend {{
  static const char* name() {{ return "mutant_{family}_{variant}"; }}
{body}
}};
"""


def variants_for(family: str) -> List[str]:
    fam = FAMILIES[family]
    return sorted(SHAPE_CLASSES[fam.shape_class].mutant_bodies)


def _body(family: str, variant: str) -> str:
    bodies = SHAPE_CLASSES[FAMILIES[family].shape_class].mutant_bodies
    if variant not in bodies:
        raise ValueError(f"unknown mutant variant {variant!r} for family {family!r}")
    return bodies[variant]


MUTANTS: Dict[str, List[str]] = {f: variants_for(f) for f in FAMILIES}


def mutant_text(family: str, variant: str) -> str:
    return _HEADER.format(family=family, variant=variant, body=_body(family, variant))


def write_mutant(family: str, dest: Path, *, variant: Optional[str] = None,
                 rng: Optional[random.Random] = None) -> Path:
    if variant is None:
        rng = rng or random.Random(secrets.randbits(32))
        variant = rng.choice(variants_for(family))
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(mutant_text(family, variant))
    return dest
