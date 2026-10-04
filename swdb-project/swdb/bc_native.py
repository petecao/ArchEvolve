"""BC native result check: BCVerifier reproduced by the evaluator. Created: 2026-10-03 ET (ticket 40).

This module is the BC plug-in's native verifier; its file hash is the retained
``verifier_sha256`` of native BC evaluations (as ``swdb/bfs_native.py`` is for
BFS), so it holds only the check and nothing that later tickets edit.

BCVerifier recomputes serial Brandes scores from the same source in the
source's own float types, normalizes by the largest score and requires every
vertex within float epsilon. The reproduction rounds every operation to the C++
type the source uses (``ScoreT`` float; ``CountT`` float in the DX100 source,
double in upstream GAPBS) and assumes no floating-point contraction (FMA) in the
evaluated build; x86-64 builds without an FMA ``-march`` satisfy that. Rounding
an exact double quotient, product or sum of two floats to float equals the float
operation, so single-precision steps are reproduced exactly.

BCVerifier accepts any scores when the largest reference score is zero (every
normalized value is NaN and NaN comparisons are false). Such a source makes the
check vacuous, so sources without an outgoing edge are refused, which is the
rule GAPBS's SourcePicker applies to the sources it picks.
"""

import math
import struct

FLT_EPSILON = 2.0 ** -23
_FLOAT = struct.Struct("<f")


def f32(value):
    """Round a Python float to the nearest IEEE single, as a C++ float store does."""
    try:
        return _FLOAT.unpack(_FLOAT.pack(value))[0]
    except OverflowError:
        return math.copysign(math.inf, value)


def reference_scores(adjacency, source, count_type="float"):
    """BCVerifier's normalized reference scores for one source (num_iters = 1)."""
    if count_type not in {"float", "double"}:
        raise ValueError("count_type must be float or double")
    n = len(adjacency)
    single = count_type == "float"
    depth = [-1] * n
    depth[source] = 0
    counts = [0.0] * n
    counts[source] = 1.0
    order = [source]
    position = 0
    while position < len(order):
        u = order[position]
        position += 1
        below = depth[u] + 1
        for v in adjacency[u]:
            if depth[v] == -1:
                depth[v] = below
                order.append(v)
            if depth[v] == below:
                counts[v] = f32(counts[v] + counts[u]) if single else counts[v] + counts[u]
    levels = {}
    for vertex in range(n):
        if depth[vertex] != -1:
            levels.setdefault(depth[vertex], []).append(vertex)
    deltas = [0.0] * n
    scores = [0.0] * n
    for level in sorted(levels, reverse=True):
        for u in levels[level]:
            below = depth[u] + 1
            delta = deltas[u]
            for v in adjacency[u]:
                if depth[v] == below:
                    ratio = counts[u] / counts[v]
                    factor = f32(1.0 + deltas[v])
                    if single:
                        delta = f32(delta + f32(f32(ratio) * factor))
                    else:
                        delta = f32(delta + ratio * factor)
            deltas[u] = delta
            scores[u] = f32(scores[u] + delta)
    biggest = max(scores) if scores else 0.0
    if biggest == 0.0:
        return [math.nan] * n, depth
    return [f32(score / biggest) for score in scores], depth


def verify_scores(adjacency, source, scores, count_type="float"):
    """BCVerifier's criterion on evaluator-owned adjacency, closed against NaN.

    BCVerifier tests ``abs(tested - reference) > epsilon``, which is false for a
    NaN tested score, so it accepts NaN at any vertex. The evaluator is stricter
    (ticket 40 assumption): a score passes only when ``abs(...) <= epsilon``, so
    NaN or infinite scores fail. A non-finite reference score (for example float
    path counts overflowing) would make the check vacuous and is refused.
    """
    n = len(adjacency)
    if isinstance(source, bool) or not isinstance(source, int) or not 0 <= source < n:
        return {"passed": False, "reason": "source outside graph"}
    if not adjacency[source]:
        return {"passed": False, "reason": "BC source has no outgoing edge; BCVerifier would accept any scores"}
    if not isinstance(scores, list) or len(scores) != n:
        return {"passed": False, "reason": "score vector length differs from vertex count"}
    tested = []
    for v, value in enumerate(scores):
        if value is None:
            tested.append(math.nan)
        elif isinstance(value, bool) or not isinstance(value, (int, float)):
            return {"passed": False, "reason": f"score[{v}] is not a number or null"}
        else:
            tested.append(f32(float(value)))
    reference, depth = reference_scores(adjacency, source, count_type)
    if not all(math.isfinite(value) for value in reference):
        return {"passed": False, "reason": "BCVerifier reference has a non-finite score; the check would be vacuous"}
    worst, mismatches, first = 0.0, 0, None
    for v in range(n):
        difference = abs(f32(tested[v] - reference[v]))
        if not difference <= FLT_EPSILON:  # NaN fails, unlike BCVerifier's '>' test
            mismatches += 1
            first = v if first is None else first
        elif difference > worst:
            worst = difference
    if mismatches:
        return {"passed": False, "reason": f"{mismatches} score(s) differ from BCVerifier's reference by more than "
                                           f"float epsilon or are not finite; first vertex {first}"}
    return {"passed": True, "reason": None, "reachable_vertices": sum(d >= 0 for d in depth),
            "maximum_absolute_difference": worst}
