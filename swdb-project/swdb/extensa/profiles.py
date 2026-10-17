# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/a5_certification_profiles.py (data model and
#         validation only; closed field sets, identifier and sha256 checks).
"""Certification profiles: the matrix and control set a library entry must pass.

A profile is library YAML read by `swdb certify ENTRY --profile PROFILE`. It names the
matrix (builds, thread count, case count, family sizes and parameters) and the negative
controls with the named check each must fail. There is no profile runner and no
second certifier: `swdb certify` executes the matrix.

SWDB changes (2026-10-03 ET): MemAcc's A5 catalog, native-archive binding and per-
benchmark obligation lookup are not ported. Obligation categories become control
categories; a profile must cover every category it requires, and its control set must
equal the entry's declared negative controls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from swdb import artifacts, yamlio

PROFILE_FORMAT = "swdb.certification-profile.v1"
_PROFILE_FIELDS = {"format", "id", "entry", "date", "matrix", "controls", "required_categories"}
_MATRIX_FIELDS = {"builds", "threads", "n_cases", "sizes", "parameters"}
_CONTROL_FIELDS = {"id", "category", "expected_check"}
BUILDS = ("sanitized", "openmp")
#: Named checks a library-operation control may be rejected by.
NAMED_CHECKS = ("differential_mismatch", "frame_violation", "sanitizer", "contract_probe")
CATEGORIES = ("index_bounds", "dropped_operand", "aliasing", "double_claim", "overlapping_pointer",
              "ordering", "capacity")
_ID = re.compile(r"[a-z0-9][a-z0-9._-]*")
_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


class ProfileError(ValueError):
    """A profile that cannot certify anything (malformed or not matching its entry)."""


@dataclass(frozen=True)
class ProfileControl:
    control_id: str
    category: str
    expected_check: str


@dataclass(frozen=True)
class CertificationProfile:
    path: Path
    sha256: str
    profile_id: str
    entry: str
    date: str
    builds: tuple
    threads: int
    n_cases: int
    sizes: Mapping[str, int]
    parameters: Mapping[str, Any]
    controls: tuple
    required_categories: tuple

    def to_record(self) -> dict:
        return {"id": self.profile_id, "path": str(self.path), "sha256": self.sha256,
                "matrix": {"builds": list(self.builds), "threads": self.threads, "n_cases": self.n_cases,
                           "sizes": dict(self.sizes), "parameters": dict(self.parameters)},
                "controls": [{"id": c.control_id, "category": c.category, "expected_check": c.expected_check}
                             for c in self.controls],
                "required_categories": list(self.required_categories)}


def _closed(value: Any, fields: set, where: str, optional: set = frozenset()) -> Mapping:
    if not isinstance(value, Mapping):
        raise ProfileError(f"{where} must be a mapping")
    missing = fields - optional - set(value)
    unknown = set(value) - fields
    if missing or unknown:
        raise ProfileError(f"{where} has missing {sorted(missing)} or unknown {sorted(unknown)} fields")
    return value


def _identifier(value: Any, where: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ProfileError(f"{where} must be an identifier")
    return value


def _positive(value: Any, where: str) -> int:
    if type(value) is not int or value < 1:
        raise ProfileError(f"{where} must be a positive integer")
    return value


def load_profile(path: Path) -> CertificationProfile:
    path = Path(path)
    try:
        data = yamlio.load(path)
    except (OSError, ValueError) as exc:
        raise ProfileError(f"cannot read profile {path}: {exc}") from None
    data = _closed(data, _PROFILE_FIELDS, "profile")
    if data["format"] != PROFILE_FORMAT:
        raise ProfileError(f"profile format must be {PROFILE_FORMAT}")
    if not isinstance(data["date"], str) or not _DATE.fullmatch(data["date"]):
        raise ProfileError("profile date must be YYYY-MM-DD")
    matrix = _closed(data["matrix"], _MATRIX_FIELDS, "profile.matrix", optional={"parameters"})
    builds = matrix["builds"]
    if not isinstance(builds, list) or not builds or any(b not in BUILDS for b in builds) \
            or len(set(builds)) != len(builds):
        raise ProfileError(f"profile.matrix.builds must be distinct values from {list(BUILDS)}")
    if "sanitized" not in builds:
        raise ProfileError("the sanitized build is a certification precondition (ported rule)")
    sizes = matrix["sizes"]
    if not isinstance(sizes, Mapping) or not sizes or any(_positive(v, f"sizes.{k}") is None for k, v in sizes.items()):
        raise ProfileError("profile.matrix.sizes must map size keys to positive integers")
    parameters = matrix.get("parameters", {}) or {}
    if not isinstance(parameters, Mapping):
        raise ProfileError("profile.matrix.parameters must be a mapping")
    controls = []
    if not isinstance(data["controls"], list) or not data["controls"]:
        raise ProfileError("profile.controls must be a nonempty list")
    for i, row in enumerate(data["controls"]):
        row = _closed(row, _CONTROL_FIELDS, f"profile.controls[{i}]")
        if row["category"] not in CATEGORIES:
            raise ProfileError(f"profile.controls[{i}].category must be one of {list(CATEGORIES)}")
        if row["expected_check"] not in NAMED_CHECKS:
            raise ProfileError(f"profile.controls[{i}].expected_check must be a named check {list(NAMED_CHECKS)}")
        controls.append(ProfileControl(_identifier(row["id"], f"controls[{i}].id"), row["category"],
                                       row["expected_check"]))
    if len({c.control_id for c in controls}) != len(controls):
        raise ProfileError("profile control IDs repeat")
    required = data["required_categories"]
    if not isinstance(required, list) or not required or any(c not in CATEGORIES for c in required):
        raise ProfileError("profile.required_categories must list known categories")
    uncovered = sorted(set(required) - {c.category for c in controls})
    if uncovered:
        raise ProfileError("profile is missing a control for required categories: " + ", ".join(uncovered))
    return CertificationProfile(path, artifacts.file_hash(path), _identifier(data["id"], "profile.id"),
                                _identifier(data["entry"], "profile.entry"), data["date"], tuple(builds),
                                _positive(matrix["threads"], "threads"), _positive(matrix["n_cases"], "n_cases"),
                                dict(sizes), dict(parameters), tuple(controls), tuple(required))


def entry_controls(entry: Mapping) -> dict:
    """{control id: expected check} declared by the entry's clauses (test-discharged)."""
    found = {}
    for clause in entry.get("clauses", []) or []:
        control = clause.get("negative_control") or {}
        if control.get("id") and control.get("id") != "none":
            found[control["id"]] = control.get("check")
    return found


def check_against_entry(profile: CertificationProfile, entry: Mapping) -> None:
    """Refuse a profile that does not name exactly the entry's controls."""
    if profile.entry != entry.get("id"):
        raise ProfileError(f"profile {profile.profile_id} is for {profile.entry}, not {entry.get('id')}")
    declared = entry_controls(entry)
    named = {c.control_id: c.expected_check for c in profile.controls}
    missing = sorted(set(declared) - set(named))
    if missing:
        raise ProfileError("profile is missing entry controls: " + ", ".join(missing))
    extra = sorted(set(named) - set(declared))
    if extra:
        raise ProfileError("profile names controls the entry does not declare: " + ", ".join(extra))
    differ = sorted(cid for cid in declared if declared[cid] != named[cid])
    if differ:
        raise ProfileError("profile and entry disagree on the expected check of: " + ", ".join(differ))
