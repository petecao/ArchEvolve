# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/synthesis/certify.py (two-binary build, post-hoc seed,
#         sanitizer precondition, capture-before-expose and destroy-before-launch case
#         loop, output validation, header/include scans)
"""Two-binary differential certification of a movement backend.

Anti-cheat by construction, kept from Extensa: inputs are generated here with a seed
chosen at certify time (post-hoc, after the candidate exists); goldens are computed by
running the reference binary, never stored; a sanitized build is a hard precondition
(an ASan/UBSan abort rejects before any compare); the reference and candidate are two
separate executables (no shared link step); the reference's output is captured into
this process and its directory destroyed before the candidate is launched; a missing
or wrong-sized candidate output is a verdict, never a harness crash.

SWDB changes (2026-10-03 ET):

* The reference is SWDB's plain C++ reference header, not MemAcc's DataLayoutAPI.
* Templates come from the typed library (`library/library_operations/drivers/`);
  an entry may pin its own candidate adapter template (e.g. an executor class).
* Every rejection carries a named `check` (differential_mismatch, frame_violation,
  sanitizer, ...), so `swdb certify` can require a control to fail its expected check.
* `sanitize=False` with an OpenMP target gives the profile's multi-thread cell.
* This module is called by `swdb certify`; it writes no records itself.
"""
from __future__ import annotations

import random
import re
import secrets
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

from swdb.extensa.synthesis.differential_oracle import compare_outputs, derive_tolerance
from swdb.extensa.synthesis.families import FAMILIES
from swdb.extensa.synthesis.shape_classes import SHAPE_CLASSES
from swdb.extensa.synthesis.targets.base import TargetHarness

#: Named checks a certification run can fail.
CHECKS = ("differential_mismatch", "frame_violation", "sanitizer", "runtime_abort", "no_output",
          "malformed_output", "forbidden_token", "include_policy", "build_failed", "zero_case")


@dataclass(frozen=True)
class CertificateResult:
    accepted: bool
    reason: str
    seed: int
    n_cases: int
    sanitize_clean: bool
    coverage: dict = field(default_factory=dict)
    zero_case: bool = False
    check: Optional[str] = None
    infrastructure_error: bool = False

    def to_dict(self) -> dict:
        return {"accepted": self.accepted, "reason": self.reason, "seed": self.seed, "n_cases": self.n_cases,
                "sanitize_clean": self.sanitize_clean, "coverage": self.coverage, "zero_case": self.zero_case,
                "check": self.check, "infrastructure_error": self.infrastructure_error}


def family_and_shape(family_name: str):
    fam = FAMILIES[family_name]
    return fam, SHAPE_CLASSES[fam.shape_class]


def render_two_binaries(workdir: Path, family_name: str, backend_header: Path, *, drivers_dir: Path,
                        reference_header: Path, cand_template: Optional[Path] = None) -> Tuple[list, list]:
    """Two self-contained source sets: (ref_srcs, cand_srcs). No candidate object code
    is ever an input to the reference binary's link step, and vice versa."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    _fam, sc = family_and_shape(family_name)
    ref_symbol, cand_symbol = sc.run_symbols
    cleanroom_header = workdir / "synth_candidate.hh"
    shutil.copy(Path(backend_header), cleanroom_header)
    run_tmpl = (Path(drivers_dir) / sc.run_template).read_text()
    ref_src = workdir / f"{family_name}_ref.cpp"
    ref_src.write_text((Path(drivers_dir) / sc.ref_template).read_text()
                       .replace("{{REFERENCE_HEADER}}", str(Path(reference_header).resolve())))
    ref_run = workdir / f"{family_name}_refmain.cpp"
    ref_run.write_text(run_tmpl.replace("{{RUN_SYMBOL}}", ref_symbol).replace("{{OUT_FILE}}", "ref.bin")
                       .replace("{{NS_LABEL}}", "REF"))
    cand_src = workdir / f"{family_name}_cand.cpp"
    template = Path(cand_template) if cand_template else Path(drivers_dir) / sc.cand_template
    cand_src.write_text(template.read_text().replace("{{BACKEND_HEADER}}", str(cleanroom_header.resolve())))
    cand_run = workdir / f"{family_name}_candmain.cpp"
    cand_run.write_text(run_tmpl.replace("{{RUN_SYMBOL}}", cand_symbol).replace("{{OUT_FILE}}", "cand.bin")
                        .replace("{{NS_LABEL}}", "CAND"))
    return [ref_src, ref_run], [cand_src, cand_run]


_FORBIDDEN_TOKENS = re.compile(
    r"(?:#|%:)\s*(?:define|undef)\s+(SynthBackend|swdb_ref|swdb_lib|SWDB_MOVEMENT_REFERENCE_HH)\b")
_COMMENT_OR_LITERAL = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*.*?\*/|//[^\n]*', re.S)


def _normalize_for_scan(text: str) -> str:
    spliced = re.sub(r"\\[ \t]*\r?\n", "", text)
    return _COMMENT_OR_LITERAL.sub(lambda m: m.group(0) if m.group(0)[0] in "\"'" else " ", spliced)


def scan_candidate_header(text: str) -> Optional[str]:
    """Defense in depth: a candidate may not #define/#undef a harness identifier."""
    m = _FORBIDDEN_TOKENS.search(_normalize_for_scan(text))
    if m:
        return f"forbidden preprocessor token in candidate header: {m.group(0).strip()!r}"
    return None


_INCLUDE_DIRECTIVE = re.compile(r'(?:#|%:)\s*include\b[ \t]*(.*)')
_ANGLE_INCLUDE_TARGET = re.compile(r'^<[^<>/\r\n]+>$')
_INCLUDE_NEXT_DIRECTIVE = re.compile(r'(?:#|%:)\s*include_next\b')
_RAW_ANGLE_INCLUDE = re.compile(r'(?:#|%:)\s*include\b[ \t]*<([^<>\r\n]*)>')


def scan_candidate_includes(text: str, *, allowed_quote: Tuple[str, ...] = ()) -> Optional[str]:
    """Include policy: slash-free angle (system) headers only, plus explicitly allowed
    quote includes; `#include_next` and path-shaped targets are refused."""
    if _INCLUDE_NEXT_DIRECTIVE.search(_normalize_for_scan(text)):
        return "forbidden #include_next in candidate header"
    for raw in _RAW_ANGLE_INCLUDE.findall(text):
        if "/" in raw or "\\" in raw:
            return f"forbidden path-shaped angle include in candidate header: <{raw}>"
    for target in _INCLUDE_DIRECTIVE.findall(_normalize_for_scan(text)):
        target = target.strip()
        if _ANGLE_INCLUDE_TARGET.fullmatch(target):
            continue
        if target.startswith('"') and target.strip('"') in allowed_quote:
            continue
        return f"forbidden include in candidate header: {target!r}"
    return None


def classify_abort(output: str) -> str:
    if "SWDB_PRESERVATION_FAIL:frame_violation" in output:
        return "frame_violation"
    if "AddressSanitizer" in output or "UndefinedBehaviorSanitizer" in output or "runtime error:" in output:
        return "sanitizer"
    return "runtime_abort"


def _compare_case(sc, fam, compare_dir: Path, sz: dict) -> Optional[str]:
    spec = derive_tolerance(fam.output_equivalence, n_terms=1)
    if spec.mode != "exact":
        raise ValueError("only bitwise families are ported; refusing an underived tolerance")
    ref, cand = sc.read_outputs(compare_dir, sz)
    v = compare_outputs(ref, cand, spec)
    return None if v.equivalent else v.reason


def resolve_sizes(sc, sizes: Optional[dict]) -> dict:
    sz = dict(sc.default_sizes)
    if sizes:
        unknown = sorted(set(sizes) - set(sz))
        if unknown:
            raise ValueError(f"sizes keys {unknown} are not sizes of shape class {sc.name!r} (accepted: {sorted(sz)})")
        sz.update(sizes)
    return sz


def certify_backend(family_name: str, backend_header: Path, target: TargetHarness, workdir: Path, *,
                    drivers_dir: Path, reference_header: Path, seed: Optional[int] = None, n_cases: int = 6,
                    sizes: Optional[dict] = None, cand_template: Optional[Path] = None, sanitize: bool = True,
                    allowed_quote: Tuple[str, ...] = ()) -> CertificateResult:
    fam, sc = family_and_shape(family_name)
    seed = secrets.randbits(32) if seed is None else seed
    if n_cases <= 0:
        return CertificateResult(False, f"no cases run: n_cases={n_cases}; a certification that examined "
                                 "nothing is not a certification", seed, 0, False,
                                 coverage={"n_cases": 0, "patterns_exercised": [], "envelope": {}},
                                 zero_case=True, check="zero_case")
    rng = random.Random(seed)
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    sz = resolve_sizes(sc, sizes)
    header_text = Path(backend_header).read_text(errors="ignore")
    forbidden = scan_candidate_header(header_text)
    if forbidden:
        return CertificateResult(False, forbidden, seed, 0, False, check="forbidden_token")
    bad_include = scan_candidate_includes(header_text, allowed_quote=allowed_quote)
    if bad_include:
        return CertificateResult(False, bad_include, seed, 0, False, check="include_policy")
    ref_srcs, cand_srcs = render_two_binaries(workdir, family_name, backend_header, drivers_dir=drivers_dir,
                                              reference_header=reference_header, cand_template=cand_template)
    ref_build = target.build_ref(ref_srcs, workdir / f"{family_name}_ref_bin", sanitize=sanitize)
    if not ref_build.ok:
        return CertificateResult(False, f"reference build failed: {ref_build.log[-1500:]}", seed, 0, False,
                                 check="build_failed", infrastructure_error=True)
    cand_build = target.build(cand_srcs, workdir / f"{family_name}_cand_bin", sanitize=sanitize)
    if not cand_build.ok:
        return CertificateResult(False, f"candidate build failed: {cand_build.log[-1500:]}", seed, 0, False,
                                 check="build_failed")
    envelope_samples: List[dict] = []
    for c in range(n_cases):
        case_dir = workdir / f"case_{c}"
        case = sc.gen_case(rng, sz, case_idx=c, n_cases=n_cases)
        envelope_samples.append(sc.envelope_sample(case, sz))
        ref_dir, cand_dir = case_dir / "ref", case_dir / "cand"
        sc.write_case(ref_dir, case)
        sc.write_case(cand_dir, case)
        ref_code, ref_out = target.run(ref_build.binary, sc.argv(sz, case, ref_dir))
        if ref_code != 0:
            return CertificateResult(False, f"reference abort on case {c} (exit {ref_code}): {ref_out[-1500:]}",
                                     seed, c, False, check="runtime_abort", infrastructure_error=True)
        ref_bin = ref_dir / "ref.bin"
        expected_bytes = sc.expected_cand_bytes(sz)
        if not ref_bin.exists() or ref_bin.stat().st_size != expected_bytes:
            return CertificateResult(False, f"reference produced malformed output on case {c}", seed, c, False,
                                     check="malformed_output", infrastructure_error=True)
        captured_ref_bytes = ref_bin.read_bytes()          # capture before expose
        shutil.rmtree(ref_dir)                              # destroy before launch
        cand_code, cand_out = target.sanitized_run(cand_build.binary, sc.argv(sz, case, cand_dir))
        if cand_code != 0:
            check = classify_abort(cand_out)
            return CertificateResult(False, f"{check} in candidate on case {c} (exit {cand_code}): {cand_out[-1500:]}",
                                     seed, c, check != "sanitizer", check=check)
        cand_bin = cand_dir / "cand.bin"
        if not cand_bin.exists():
            return CertificateResult(False, f"candidate produced no output on case {c}", seed, c, True,
                                     check="no_output")
        if cand_bin.stat().st_size != expected_bytes:
            return CertificateResult(False, f"candidate produced malformed output on case {c}", seed, c, True,
                                     check="malformed_output")
        compare_dir = case_dir / "compare"
        compare_dir.mkdir(parents=True, exist_ok=True)
        (compare_dir / "ref.bin").write_bytes(captured_ref_bytes)
        shutil.copy(cand_bin, compare_dir / "cand.bin")
        reason = _compare_case(sc, fam, compare_dir, sz)
        if reason is not None:
            return CertificateResult(False, f"divergence on case {c}: {reason} (seed={seed})", seed, c + 1, True,
                                     check="differential_mismatch")
    coverage = {"n_cases": n_cases,
                "patterns_exercised": sorted({sc.patterns[c % len(sc.patterns)] for c in range(n_cases)}),
                "envelope": sc.merge_envelope(envelope_samples)}
    return CertificateResult(True, f"{n_cases} cases bitwise-equivalent" + (", sanitizer clean" if sanitize else ""),
                             seed, n_cases, sanitize, coverage=coverage)
