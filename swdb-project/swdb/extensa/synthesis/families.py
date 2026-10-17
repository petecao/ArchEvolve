# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/synthesis/families.py (Family, contract resolution,
#         canonical contract JSON and its sha256)
"""Synthesis families: one movement hook per BFS-relevant shape.

SWDB changes (2026-10-03 ET): the family table is fixed to decision D1's BFS-relevant
families (gather, pack, regroup, bin_drain, gather_stream); MemAcc derived it from its
transformation registry, which is not ported. A family's contract resolves from SWDB's
typed library: the library-operation entry whose `differential_test.family` names the
family (its normative fields only; tier and status are never part of a contract).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, FrozenSet, Optional

from swdb.extensa.synthesis.shape_classes import SHAPE_CLASSES


@dataclass(frozen=True)
class Family:
    name: str
    shape_class: str
    output_equivalence: str
    movement_only: bool
    requires: FrozenSet[str]

    @property
    def hook_signature(self) -> str:
        return SHAPE_CLASSES[self.shape_class].hook


FAMILIES: Dict[str, Family] = {
    "gather": Family("gather", "flat_movement", "bitwise_identical", True, frozenset()),
    "pack": Family("pack", "chained_pack", "bitwise_identical", True, frozenset()),
    "regroup": Family("regroup", "strided_interleave", "bitwise_identical", True, frozenset()),
    "bin_drain": Family("bin_drain", "bin_drain", "bitwise_identical", False, frozenset()),
    "gather_stream": Family("gather_stream", "gather_stream", "bitwise_identical", True, frozenset()),
    # SWDB addition (ticket 51): vertex relabeling has no MemAcc synthesis family.
    "relabel": Family("relabel", "relabel", "bitwise_identical", True, frozenset()),
}

#: Entry fields that are normative contract content (never derived evidence state).
_CONTRACT_FIELDS = ("id", "kind", "signature", "intent", "clauses", "provenance", "pattern_keys")


def resolve_contract(family: Family, library_root: Optional[Path] = None) -> dict:
    """The family's canonical contract bundle from the typed library."""
    from swdb.library import Library
    library = Library(library_root) if library_root else Library()
    entries = [e for e in library.entries.values()
               if e.get("kind") == "library_operation"
               and (e.get("differential_test") or {}).get("family") == family.name]
    entries.sort(key=lambda e: e["id"])
    shape = SHAPE_CLASSES[family.shape_class]
    return {
        "family": family.name,
        "entries": [{k: e[k] for k in _CONTRACT_FIELDS if k in e} for e in entries],
        "intent": entries[0]["intent"] if entries else f"{family.name} movement hook",
        "postconditions": {"output_equivalence": family.output_equivalence},
        "synthesis": {"family": family.name, "hook": shape.hook, "shape_class": shape.name,
                      "output_equivalence": family.output_equivalence,
                      "movement_only": family.movement_only, "requires": sorted(family.requires)},
    }


def canonical_contract_json(contract: dict) -> str:
    return json.dumps(contract, indent=2, sort_keys=True) + "\n"


def contract_sha256(contract: dict) -> str:
    return hashlib.sha256(canonical_contract_json(contract).encode()).hexdigest()
