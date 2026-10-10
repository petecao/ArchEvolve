# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/differential_oracle.py (unchanged logic)
"""WS-0 differential-equivalence oracle — principled tolerance model.

This module is the soundness keystone of the contract-gated self-extension
program: it derives the acceptance tolerance for an equivalence check **from
numerical-analysis first principles**, NOT from any agent-chosen literal. A
postcondition repair (WS-A) or a synthesized backend (WS-C) may only relax the
guarantee to a tolerance this code computes; an agent that wants its candidate
to pass cannot widen the goalposts, because the bound is a function of the
operation (term count, dtype, conditioning), not of the candidate.

Forward-error model (Higham, *Accuracy and Stability of Numerical Algorithms*):
a reordered floating-point reduction of ``n`` terms differs from another
ordering by at most ``~ cond * gamma_n``, where ``gamma_n = n*u / (1 - n*u)`` and
``u`` is the unit roundoff. We apply a small safety factor and report a relative
tolerance. ``bitwise_identical`` maps to exact (tolerance 0).

The full oracle (input generation that exercises a contract's preconditions,
reference-vs-candidate execution, GPU race-checking) builds on this tolerance.
"""
from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import Optional, Sequence

# IEEE-754 unit roundoff u = 2^-(mantissa_bits + 1).
UNIT_ROUNDOFF = {
    "float64": 2.0 ** -53,   # 53-bit significand (52 stored + implicit)
    "float32": 2.0 ** -24,   # 24-bit significand
    "float16": 2.0 ** -11,
}

# Tags whose guarantee is exact equality (no FP reassociation permitted).
_EXACT_TAGS = {"bitwise_identical", "writeback_to_original"}
# Tags whose guarantee permits reassociation / reordering within an FP bound.
_FP_TAGS = {"stat_equivalent_fp_assoc", "order_dependent_observation_only"}

# TICKET 14. `equivalent_modulo_declared_tiebreak` is in NEITHER set, and that is
# the point rather than an omission. Its outputs are not bit-equal (an exact tag
# would be a false promise) and they are not within any FP bound either -- a
# first-wins rewrite of a last-wins loop writes a DIFFERENT ELEMENT, and an argmax
# index moves by an arbitrary amount when a near-tie flips. No numeric tolerance
# accepts that, so `derive_tolerance` raises "unknown output_equivalence tag" for
# it, which is the correct behaviour: a differential oracle cannot check this
# family, and the caller must find out by being refused rather than by being
# handed a bound that admits everything. If a tie-break family is ever
# synthesized, it needs an oracle that compares against the DECLARED rule, not a
# widened epsilon.

_DEFAULT_SAFETY = 4.0


@dataclass(frozen=True)
class ToleranceSpec:
    """A derived acceptance tolerance. ``rel`` is relative, ``atol`` absolute."""
    mode: str        # "exact" | "fp_reassoc"
    rel: float
    atol: float = 0.0
    # Provenance: how the bound was derived (for the verdict record / audit).
    derivation: str = ""


def _gamma_n(n_terms: int, u: float) -> float:
    """Classic gamma_n = n*u/(1 - n*u), clamped finite-positive when n*u -> 1.

    When n*u >= 1 the first-order bound is meaningless (>100% worst-case error);
    we clamp the denominator to a tiny positive value so the result stays finite
    and positive (callers treat such a regime as "reassociation not trustworthy"
    rather than crashing on inf/NaN).
    """
    n = max(int(n_terms), 1)
    nu = n * u
    denom = 1.0 - nu
    if denom <= 1e-16:
        denom = 1e-16
    return nu / denom


def derive_tolerance(
    output_equivalence: str,
    *,
    n_terms: int,
    dtype: str = "float64",
    condition_number: float = 1.0,
    safety: float = _DEFAULT_SAFETY,
) -> ToleranceSpec:
    """Derive the equivalence tolerance for a postcondition tag (non-LLM).

    Args:
        output_equivalence: the contract's ``postconditions.output_equivalence`` tag.
        n_terms: number of accumulation steps in the reduction being reordered
                 (the dominant driver of the reassociation error bound).
        dtype: "float64" | "float32" | "float16".
        condition_number: empirical conditioning of the reduction (>= 1).
        safety: multiplicative safety factor on the first-order bound.

    Raises:
        ValueError: on an unknown tag or unknown dtype.
    """
    if output_equivalence in _EXACT_TAGS:
        return ToleranceSpec(mode="exact", rel=0.0, atol=0.0,
                             derivation=f"{output_equivalence} -> exact")
    if output_equivalence not in _FP_TAGS:
        raise ValueError(f"unknown output_equivalence tag: {output_equivalence!r}")
    if dtype not in UNIT_ROUNDOFF:
        raise ValueError(f"unknown dtype: {dtype!r}")
    u = UNIT_ROUNDOFF[dtype]
    # Use the conditioning as given (>=1 typical); the bound scales linearly with it.
    cond = float(condition_number)
    gamma = _gamma_n(n_terms, u)
    rel = safety * cond * gamma
    return ToleranceSpec(
        mode="fp_reassoc", rel=rel, atol=0.0,
        derivation=(f"safety({safety}) * cond({cond}) * gamma_n("
                    f"n={n_terms}, u={dtype}={u:.3e}) = {rel:.3e}"),
    )


@dataclass(frozen=True)
class Verdict:
    """Result of comparing a candidate output against the reference."""
    equivalent: bool
    max_abs_err: float
    max_rel_err: float
    first_divergence: Optional[int]   # index of the first failing element (a counterexample)
    reason: str = ""


def compare_outputs(reference: Sequence[float], candidate: Sequence[float],
                    spec: ToleranceSpec, *,
                    n_terms_per_element: Optional[Sequence[int]] = None,
                    dtype: str = "float64",
                    condition_number: float = 1.0,
                    safety: float = _DEFAULT_SAFETY) -> Verdict:
    """Compare candidate vs reference under a derived ToleranceSpec.

    Defense in depth: a length mismatch or any non-finite candidate value
    (NaN/inf) is ALWAYS a failure (NaN negative-control), regardless of mode.
    ``exact`` requires bit-equality; ``fp_reassoc`` requires
    ``|a-b| <= atol + rel*|a|`` elementwise. Returns the worst observed errors
    and the first failing index (a reproducible counterexample).

    P5d (per-element bounds): when ``n_terms_per_element`` is given (and
    ``spec.mode == "fp_reassoc"``), element i's relative bound is derived from
    ITS OWN reduction width -- ``safety * condition_number *
    gamma_n(n_terms_per_element[i], u)`` -- instead of the scalar ``spec.rel``.
    A tolerance derived from the case's longest row and applied uniformly
    would be soundly WIDE on short rows, which is exactly where a
    dropped-term mutant's damage is smallest relative to the bound; the
    per-element form keeps every element's bound tight. Misuse is a loud
    ValueError (config error in the HARNESS), never a candidate verdict:
    wrong length, or supplied alongside an exact-mode spec.
    """
    ref = list(reference)
    cand = list(candidate)
    rel_per: Optional[list] = None
    if n_terms_per_element is not None:
        if spec.mode == "exact":
            raise ValueError("n_terms_per_element with an exact-mode spec is a config error")
        if dtype not in UNIT_ROUNDOFF:
            raise ValueError(f"unknown dtype: {dtype!r}")
        nt = list(n_terms_per_element)
        if len(nt) != len(ref):
            raise ValueError(f"n_terms_per_element length {len(nt)} != reference length {len(ref)}")
        u = UNIT_ROUNDOFF[dtype]
        cond = float(condition_number)
        rel_per = [safety * cond * _gamma_n(n, u) for n in nt]
    if len(ref) != len(cand):
        return Verdict(False, math.inf, math.inf, min(len(ref), len(cand)),
                       f"length mismatch: ref={len(ref)} cand={len(cand)}")
    max_abs = 0.0
    max_rel = 0.0
    first: Optional[int] = None
    for i, (a, b) in enumerate(zip(ref, cand)):
        if not math.isfinite(b):
            return Verdict(False, math.inf, math.inf, i,
                           f"non-finite candidate at {i}: {b!r}")
        ae = abs(a - b)
        re_ = ae / abs(a) if a != 0.0 else (0.0 if ae == 0.0 else math.inf)
        max_abs = max(max_abs, ae)
        max_rel = max(max_rel, re_)
        # exact == the bitwise_identical guarantee: compare the IEEE-754 bit
        # patterns, not Python float equality (-0.0 == 0.0 would otherwise pass).
        rel_i = rel_per[i] if rel_per is not None else spec.rel
        ok = (struct.pack("<d", a) == struct.pack("<d", b)) if spec.mode == "exact" \
            else (ae <= spec.atol + rel_i * abs(a))
        if not ok and first is None:
            first = i
    return Verdict(first is None, max_abs, max_rel, first,
                   "" if first is None else f"diverges at index {first}")


@dataclass(frozen=True)
class OracleResult:
    """Aggregate verdict of running reference vs candidate over many inputs."""
    accepted: bool
    n_inputs: int
    n_failures: int
    first_counterexample: Optional[dict] = None


def run_oracle(reference, candidate, inputs, *, output_equivalence: str,
               n_terms: int, dtype: str = "float64",
               condition_number: float = 1.0) -> OracleResult:
    """Differential-equivalence check: run ``reference`` and ``candidate`` on each
    input, compare under the derived (non-LLM) tolerance, and ACCEPT only if no
    input diverges. This is the oracle entry point WS-A (repair) and WS-C
    (backend synthesis) call to certify a candidate; an injected-bad candidate
    must never be accepted (false-accept = 0).

    ``reference``/``candidate`` are callables: input -> output sequence.
    """
    spec = derive_tolerance(output_equivalence, n_terms=n_terms, dtype=dtype,
                            condition_number=condition_number)
    inputs = list(inputs)
    n_fail = 0
    first: Optional[dict] = None
    for idx, x in enumerate(inputs):
        v = compare_outputs(list(reference(x)), list(candidate(x)), spec)
        if not v.equivalent:
            n_fail += 1
            if first is None:
                first = {"input_index": idx, "reason": v.reason,
                         "first_divergence": v.first_divergence,
                         "max_rel_err": v.max_rel_err}
    return OracleResult(accepted=(n_fail == 0), n_inputs=len(list(inputs)),
                        n_failures=n_fail, first_counterexample=first)
