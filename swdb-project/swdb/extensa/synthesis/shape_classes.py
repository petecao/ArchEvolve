# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
# Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
# Source: AgenticRefiner/refiner/synthesis/shape_classes.py (only the pack
#         [chained_pack], regroup [strided_interleave], gather [flat_movement],
#         gather_stream and bin_drain case generators, IO, envelopes, mutants, probes
#         and hints; decision D1).
"""Shape classes: one driver-template set, case generator, mutant family, probe and
hint per BFS-relevant movement shape.

SWDB changes (2026-10-03 ET): templates live in `library/library_operations/drivers/`
and call SWDB's plain C++ reference header (`swdb_ref::`), not MemAcc's DataLayoutAPI;
run symbols are `swdb_ref_<family>` / `swdb_cand_<family>`; perf sizes and the
extensive-size machinery are not ported (SWDB's evaluator times nothing here); the
pack generator also sweeps chain depth 1 and 2 (the base `load_to_pack` path); the
delegating headers forward to `swdb_ref::`. Patterns, generators and mutant bodies
are otherwise unchanged.
"""
from __future__ import annotations

import random
import struct
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Callable, List, Mapping, Optional, Tuple


def _mp(d: dict) -> Mapping:
    return MappingProxyType(dict(d))


_INDEX_PATTERNS = ("random", "all_zero", "all_max", "reverse", "dup_max", "strided")


def _pattern_indices(rng: random.Random, length: int, hi: int, pattern: str) -> List[int]:
    if pattern == "random":
        return [rng.randrange(hi) for _ in range(length)]
    if pattern == "all_zero":
        return [0] * length
    if pattern == "all_max":
        return [hi - 1] * length
    if pattern == "reverse":
        return [hi - 1 - (i % hi) for i in range(length)]
    if pattern == "dup_max":
        mid = hi // 2
        return [mid] * length
    if pattern == "strided":
        stride = max(1, hi // max(1, length))
        return [(i * stride) % hi for i in range(length)]
    raise ValueError(f"unknown index pattern: {pattern!r}")


def _write_i32(path: Path, xs: List[int]) -> None:
    path.write_bytes(struct.pack(f"<{len(xs)}i", *xs))


def _write_f64(path: Path, xs: List[float]) -> None:
    path.write_bytes(struct.pack(f"<{len(xs)}d", *xs))


def _read_doubles(path: Path, n: int) -> list:
    return list(struct.unpack(f"<{n}d", path.read_bytes()))


def _read_f64_pair(case_dir: Path, count: int) -> Tuple[list, list]:
    return (_read_doubles(case_dir / "ref.bin", count), _read_doubles(case_dir / "cand.bin", count))


# --- gather (flat_movement) -------------------------------------------------------

def generate_gather_case(rng: random.Random, sizes: dict, case_idx: int = 0, n_cases: int = 1) -> dict:
    n, n_src = sizes["n"], sizes["n_src"]
    pattern = _INDEX_PATTERNS[case_idx % len(_INDEX_PATTERNS)]
    src = [rng.uniform(-1e3, 1e3) for _ in range(n_src)]
    idx = _pattern_indices(rng, n, n_src, pattern)
    if pattern == "random":
        idx[0] = 0
        idx[-1] = n_src - 1
        if n >= 4:
            idx[1] = idx[2] = n_src // 2
    return {"src": src, "idx": idx}


def _write_gather_case(case_dir: Path, case: dict) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    _write_f64(case_dir / "src.bin", case["src"])
    _write_i32(case_dir / "idx.bin", case["idx"])


def _flat_envelope_sample(case: dict, sizes: dict) -> dict:
    idx = case["idx"]
    return {"idx_min": min(idx), "idx_max": max(idx), "has_duplicates": len(set(idx)) < len(idx)}


def _flat_merge_envelope(samples: List[dict]) -> dict:
    if not samples:
        return {}
    return {"idx_min": min(s["idx_min"] for s in samples), "idx_max": max(s["idx_max"] for s in samples),
            "duplicates_seen": any(s["has_duplicates"] for s in samples)}


# --- pack (chained_pack) ----------------------------------------------------------

def generate_pack_case(rng: random.Random, sizes: dict, case_idx: int = 0, n_cases: int = 1) -> dict:
    """SWDB: depth alternates 2, 1 by case index (both base `load_to_pack` forms)."""
    n, n_src = sizes["n"], sizes["n_src"]
    depth = 2 if case_idx % 2 == 0 else 1
    coeff = rng.choice([1, 2])
    offset = rng.choice([0, 3])
    max_final = (n_src - 1 - offset) // coeff
    assert max_final >= 0
    src = [rng.uniform(-1e3, 1e3) for _ in range(n_src)]
    pattern = _INDEX_PATTERNS[(case_idx // 2) % len(_INDEX_PATTERNS)]
    if depth == 2:
        chain0 = _pattern_indices(rng, n, n_src, pattern)
        chain1 = _pattern_indices(rng, n_src, max_final + 1, pattern)
        if pattern == "random":
            chain0[0] = 0
            chain0[-1] = n_src - 1
    else:
        chain0 = _pattern_indices(rng, n, max_final + 1, pattern)
        chain1 = [0]
        if pattern == "random":
            chain0[0] = 0
            chain0[-1] = max_final
    return {"src": src, "chain0": chain0, "chain1": chain1, "coeff": coeff, "offset": offset, "depth": depth}


def _write_pack_case(case_dir: Path, case: dict) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    _write_f64(case_dir / "src.bin", case["src"])
    _write_i32(case_dir / "chain0.bin", case["chain0"])
    _write_i32(case_dir / "chain1.bin", case["chain1"])


def _chained_envelope_sample(case: dict, sizes: dict) -> dict:
    chain0, chain1 = case["chain0"], case["chain1"]
    return {"chain0_min": min(chain0), "chain0_max": max(chain0), "chain1_min": min(chain1),
            "chain1_max": max(chain1), "depth": case["depth"],
            "has_duplicates": len(set(chain0)) < len(chain0) or len(set(chain1)) < len(chain1)}


def _chained_merge_envelope(samples: List[dict]) -> dict:
    if not samples:
        return {}
    return {"chain0_min": min(s["chain0_min"] for s in samples), "chain0_max": max(s["chain0_max"] for s in samples),
            "chain1_min": min(s["chain1_min"] for s in samples), "chain1_max": max(s["chain1_max"] for s in samples),
            "depths": sorted({s["depth"] for s in samples}),
            "duplicates_seen": any(s["has_duplicates"] for s in samples)}


# --- regroup (strided_interleave) ------------------------------------------------

_REGROUP_PATTERNS = ("random", "zeros", "alternating_sign")


def generate_regroup_case(rng: random.Random, sizes: dict, case_idx: int = 0, n_cases: int = 1) -> dict:
    n, k = sizes["n"], sizes["k"]
    pattern = _REGROUP_PATTERNS[case_idx % len(_REGROUP_PATTERNS)]
    if pattern == "random":
        arrays = [[rng.uniform(-1e3, 1e3) for _ in range(n)] for _ in range(k)]
    elif pattern == "zeros":
        arrays = [[0.0 for _ in range(n)] for _ in range(k)]
    else:
        arrays = [[rng.uniform(1.0, 1e3) * (1 if i % 2 == 0 else -1) for i in range(n)] for _ in range(k)]
    return {"arrays": arrays}


def _write_regroup_case(case_dir: Path, case: dict) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    for a, arr in enumerate(case["arrays"]):
        _write_f64(case_dir / f"arr{a}.bin", arr)


def _strided_envelope_sample(case: dict, sizes: dict) -> dict:
    flat = [v for arr in case["arrays"] for v in arr]
    return {"value_min": min(flat), "value_max": max(flat), "has_zero": any(v == 0.0 for v in flat)}


def _strided_merge_envelope(samples: List[dict]) -> dict:
    if not samples:
        return {}
    return {"value_min": min(s["value_min"] for s in samples), "value_max": max(s["value_max"] for s in samples),
            "zero_seen": any(s["has_zero"] for s in samples)}


# --- bin_drain --------------------------------------------------------------------

_BIN_DRAIN_PATTERNS = ("random", "single_target", "uniform", "empty_heavy")


def generate_bin_drain_case(rng: random.Random, sz: dict, case_idx: int = 0, n_cases: int = 1) -> dict:
    n, n_target = sz["n"], sz["n_target"]
    pattern = _BIN_DRAIN_PATTERNS[case_idx % len(_BIN_DRAIN_PATTERNS)]
    if pattern == "random":
        dests = [rng.randrange(n_target) for _ in range(n)]
        if n >= 2:
            dests[0] = 0
            dests[-1] = n_target - 1
    elif pattern == "single_target":
        t = rng.randrange(n_target)
        dests = [t] * n
    elif pattern == "uniform":
        dests = [i % n_target for i in range(n)]
    else:
        live = max(1, n_target // 8)
        dests = [rng.randrange(live) for _ in range(n)]
    vals = [rng.uniform(0.25, 4.0) for _ in range(n)]
    return {"dests": dests, "vals": vals}


def _write_bin_drain_case(case_dir: Path, case: dict) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    _write_i32(case_dir / "dests.bin", case["dests"])
    _write_f64(case_dir / "vals.bin", case["vals"])


def _bin_drain_envelope_sample(case: dict, sz: dict) -> dict:
    counts = [0] * sz["n_target"]
    for d in case["dests"]:
        counts[d] += 1
    live = [w for w in counts if w > 0]
    return {"collision_min": min(live) if live else 0, "collision_max": max(counts) if counts else 0,
            "empty_targets_seen": any(w == 0 for w in counts)}


def _bin_drain_merge_envelope(samples: List[dict]) -> dict:
    if not samples:
        return {}
    return {"collision_min": min(s["collision_min"] for s in samples),
            "collision_max": max(s["collision_max"] for s in samples),
            "empty_targets_seen": any(s["empty_targets_seen"] for s in samples)}


# --- gather_stream ----------------------------------------------------------------

_GATHER_STREAM_LANES = 4


def generate_gather_stream_case(rng: random.Random, sz: dict, case_idx: int = 0, n_cases: int = 1) -> dict:
    rows, row_len, src_stride = sz["rows"], sz["row_len"], sz["src_stride"]
    pattern = _INDEX_PATTERNS[case_idx % len(_INDEX_PATTERNS)]
    idx = _pattern_indices(rng, row_len, src_stride, pattern)
    if pattern == "random" and row_len >= 4:
        idx[0] = 0
        idx[-1] = src_stride - 1
        idx[1] = idx[2]
    src = [float(r + 1) + rng.uniform(-0.25, 0.25) for r in range(rows) for _ in range(src_stride)]
    return {"src": src, "idx": idx}


def _gather_stream_envelope_sample(case: dict, sz: dict) -> dict:
    idx = case["idx"]
    return {"distinct_indices": len(set(idx)), "duplicates_seen": len(set(idx)) < len(idx),
            "row_len_mod_vector": sz["row_len"] % _GATHER_STREAM_LANES,
            "padding_per_row": sz["dst_stride"] - sz["row_len"]}


def _gather_stream_merge_envelope(samples: List[dict]) -> dict:
    if not samples:
        return {}
    return {"distinct_indices_min": min(s["distinct_indices"] for s in samples),
            "duplicates_seen": any(s["duplicates_seen"] for s in samples),
            "row_len_mod_vector": sorted({s["row_len_mod_vector"] for s in samples}),
            "padding_per_row": sorted({s["padding_per_row"] for s in samples})}


# --- relabel (SWDB addition 2026-10-03 ET, ticket 51; not ported) -----------------
# MemAcc has no synthesis shape for VertexRelabelExecutor. This shape follows the
# ported conventions (pattern sweep by case index, canary, bitwise compare) for
# `permute_values`: out[perm[v]] = in[v] for a bijection perm.

_RELABEL_PATTERNS = ("random", "identity", "reverse", "rotate")


def generate_relabel_case(rng: random.Random, sz: dict, case_idx: int = 0, n_cases: int = 1) -> dict:
    n = sz["n"]
    pattern = _RELABEL_PATTERNS[case_idx % len(_RELABEL_PATTERNS)]
    if pattern == "random":
        perm = list(range(n))
        rng.shuffle(perm)
    elif pattern == "identity":
        perm = list(range(n))
    elif pattern == "reverse":
        perm = [n - 1 - v for v in range(n)]
    else:
        shift = 1 + rng.randrange(max(1, n - 1))
        perm = [(v + shift) % n for v in range(n)]
    values = [rng.uniform(-1e3, 1e3) for _ in range(n)]
    return {"perm": perm, "values": values}


def _write_relabel_case(case_dir: Path, case: dict) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    _write_i32(case_dir / "perm.bin", case["perm"])
    _write_f64(case_dir / "values.bin", case["values"])


def _relabel_envelope_sample(case: dict, sz: dict) -> dict:
    perm = case["perm"]
    return {"fixed_points": sum(1 for v, p in enumerate(perm) if v == p)}


def _relabel_merge_envelope(samples: List[dict]) -> dict:
    if not samples:
        return {}
    return {"fixed_points_min": min(s["fixed_points"] for s in samples),
            "fixed_points_max": max(s["fixed_points"] for s in samples)}


_RELABEL_MUTANTS = {
    "inverse_direction": """\
  template <typename ValueT, typename IndexT>
  static void relabel_apply(ValueT* out, const ValueT* in, const IndexT* perm, std::size_t n) {
    for (std::size_t v = 0; v < n; ++v) out[v] = in[(std::size_t)perm[v]];
  }""",
    "skip_last_vertex": """\
  template <typename ValueT, typename IndexT>
  static void relabel_apply(ValueT* out, const ValueT* in, const IndexT* perm, std::size_t n) {
    for (std::size_t v = 0; v + 1 < n; ++v) out[(std::size_t)perm[v]] = in[v];
  }""",
}

_RELABEL_SIG = ("  template <typename ValueT, typename IndexT>\n  static void relabel_apply(ValueT* out, const ValueT* in,"
                " const IndexT* perm, std::size_t n)")


# --- registry ---------------------------------------------------------------------

@dataclass(frozen=True)
class ShapeClass:
    name: str
    family: str
    ref_template: str
    cand_template: str
    run_template: str
    run_symbols: Tuple[str, str]
    hook: str
    mutant_bodies: Mapping[str, str]
    probe: str
    test_hint: str
    default_sizes: Mapping[str, int]
    gen_case: Callable[..., dict]
    write_case: Callable[[Path, dict], None]
    argv: Callable[[dict, dict, Path], list]
    read_outputs: Callable[[Path, dict], Tuple[list, list]]
    expected_cand_bytes: Callable[[dict], int]
    patterns: Tuple[str, ...]
    envelope_sample: Callable[[dict, dict], dict]
    merge_envelope: Callable[[list], dict]
    delegating_header: str = ""
    n_terms_per_output: Optional[Callable] = None
    read_sections: Optional[Callable] = None


def _delegating(name: str, signature: str, call: str) -> str:
    return ("#pragma once\n#include \"movement_reference.hh\"\nstruct SynthBackend {\n"
            f"  static const char* name() {{ return \"delegating_{name}\"; }}\n{signature} {{\n    {call}\n  }}\n}};\n")


_FLAT_MUTANTS = {
    "off_by_one": """\
  template <typename ValueT, typename IndexT>
  static void gather(ValueT* out, const ValueT* source, const IndexT* idx,
                     std::size_t n, std::size_t n_source) {
    for (std::size_t i = 0; i < n; ++i)
      out[i] = source[((std::size_t)idx[i] + 1) % n_source];
  }""",
    "reversed_iteration": """\
  template <typename ValueT, typename IndexT>
  static void gather(ValueT* out, const ValueT* source, const IndexT* idx,
                     std::size_t n, std::size_t n_source) {
    (void)n_source;
    for (std::size_t i = 0; i < n; ++i)
      out[i] = source[idx[n - 1 - i]];
  }""",
    "zero_first": """\
  template <typename ValueT, typename IndexT>
  static void gather(ValueT* out, const ValueT* source, const IndexT* idx,
                     std::size_t n, std::size_t n_source) {
    (void)n_source;
    for (std::size_t i = 0; i < n; ++i) out[i] = source[idx[i]];
    if (n) out[0] = ValueT(0);
  }""",
}

_CHAINED_MUTANTS = {
    "final_index_off_by_one": """\
  template <typename ValueT, typename IndexT>
  static void pack_gather(ValueT* packed, const ValueT* src,
                          const IndexT* const* chain, std::size_t depth,
                          std::size_t n, std::int64_t coeff,
                          std::int64_t offset, std::size_t n_src) {
    for (std::size_t i = 0; i < n; ++i) {
      std::size_t idx = i;
      for (std::size_t j = 0; j < depth; ++j) idx = (std::size_t)chain[j][idx];
      packed[i] = src[((std::size_t)((std::int64_t)idx * coeff + offset) + 1) % n_src];
    }
  }""",
    "skip_last_chain_level": """\
  template <typename ValueT, typename IndexT>
  static void pack_gather(ValueT* packed, const ValueT* src,
                          const IndexT* const* chain, std::size_t depth,
                          std::size_t n, std::int64_t coeff,
                          std::int64_t offset, std::size_t n_src) {
    for (std::size_t i = 0; i < n; ++i) {
      std::size_t idx = i;
      std::size_t d = depth ? depth - 1 : 0;   // drops the last indirection
      for (std::size_t j = 0; j < d; ++j) idx = (std::size_t)chain[j][idx];
      packed[i] = src[((std::size_t)((std::int64_t)idx * coeff + offset)) % n_src];
    }
  }""",
}

_STRIDED_MUTANTS = {
    "transposed_layout": """\
  template <typename ValueT>
  static void interleave(ValueT* out, const ValueT* const* arrays,
                         std::size_t num_arrays, std::size_t n) {
    for (std::size_t i = 0; i < n; ++i)
      for (std::size_t a = 0; a < num_arrays; ++a)
        out[a * n + i] = arrays[a][i];
  }""",
    "arrays_reversed": """\
  template <typename ValueT>
  static void interleave(ValueT* out, const ValueT* const* arrays,
                         std::size_t num_arrays, std::size_t n) {
    for (std::size_t i = 0; i < n; ++i)
      for (std::size_t a = 0; a < num_arrays; ++a)
        out[num_arrays * i + a] = arrays[num_arrays - 1 - a][i];
  }""",
}

_BIN_DRAIN_MUTANTS = {
    "assign_not_accumulate": """\
  template <typename ValueT, typename IndexT>
  static void apply(ValueT* target, const IndexT* dests, const ValueT* vals,
                    std::size_t n) {
    for (std::size_t k = 0; k < n; ++k) target[(std::size_t)dests[k]] = vals[k];
  }""",
    "off_by_one_dest": """\
  template <typename ValueT, typename IndexT>
  static void apply(ValueT* target, const IndexT* dests, const ValueT* vals,
                    std::size_t n) {
    for (std::size_t k = 0; k < n; ++k) {
      std::size_t d = (std::size_t)dests[k];
      target[d > 0 ? d - 1 : d] += vals[k];
    }
  }""",
    "dropped_last_record": """\
  template <typename ValueT, typename IndexT>
  static void apply(ValueT* target, const IndexT* dests, const ValueT* vals,
                    std::size_t n) {
    std::size_t m = n > 0 ? n - 1 : 0;
    for (std::size_t k = 0; k < m; ++k) target[(std::size_t)dests[k]] += vals[k];
  }""",
    "subtract_not_add": """\
  template <typename ValueT, typename IndexT>
  static void apply(ValueT* target, const IndexT* dests, const ValueT* vals,
                    std::size_t n) {
    for (std::size_t k = 0; k < n; ++k) target[(std::size_t)dests[k]] -= vals[k];
  }""",
}

_GATHER_STREAM_MUTANTS = {
    "gather_index_shift": """\
  template <typename ValueT, typename IndexT>
  static void gather_stream(ValueT* dst, const ValueT* src, const IndexT* idx,
                            std::size_t rows, std::size_t row_len,
                            std::size_t dst_stride, std::size_t src_stride) {
    for (std::size_t r = 0; r < rows; ++r)
      for (std::size_t j = 0; j < row_len; ++j)
        dst[r * dst_stride + j] =
            src[r * src_stride + (((std::size_t)idx[j] + 1) % src_stride)];
  }""",
    "partial_stream": """\
  template <typename ValueT, typename IndexT>
  static void gather_stream(ValueT* dst, const ValueT* src, const IndexT* idx,
                            std::size_t rows, std::size_t row_len,
                            std::size_t dst_stride, std::size_t src_stride) {
    const std::size_t whole = (row_len / 4) * 4;
    for (std::size_t r = 0; r < rows; ++r)
      for (std::size_t j = 0; j < whole; ++j)
        dst[r * dst_stride + j] = src[r * src_stride + (std::size_t)idx[j]];
  }""",
    "padding_overrun": """\
  template <typename ValueT, typename IndexT>
  static void gather_stream(ValueT* dst, const ValueT* src, const IndexT* idx,
                            std::size_t rows, std::size_t row_len,
                            std::size_t dst_stride, std::size_t src_stride) {
    for (std::size_t r = 0; r < rows; ++r)
      for (std::size_t j = 0; j < dst_stride; ++j)
        dst[r * dst_stride + j] = src[r * src_stride + (std::size_t)idx[j % row_len]];
  }""",
    "stale_staging": """\
  template <typename ValueT, typename IndexT>
  static void gather_stream(ValueT* dst, const ValueT* src, const IndexT* idx,
                            std::size_t rows, std::size_t row_len,
                            std::size_t dst_stride, std::size_t src_stride) {
    (void)src_stride;
    for (std::size_t r = 0; r < rows; ++r)
      for (std::size_t j = 0; j < row_len; ++j)
        dst[r * dst_stride + j] = src[(std::size_t)idx[j]];
  }""",
}

_PACK_SIG = ("  template <typename ValueT, typename IndexT>\n  static void pack_gather(ValueT* packed, const ValueT* src,"
             " const IndexT* const* chain, std::size_t depth, std::size_t n, std::int64_t coeff,"
             " std::int64_t offset, std::size_t n_src)")
_GATHER_SIG = ("  template <typename ValueT, typename IndexT>\n  static void gather(ValueT* out, const ValueT* source,"
               " const IndexT* idx, std::size_t n, std::size_t n_source)")
_REGROUP_SIG = ("  template <typename ValueT>\n  static void interleave(ValueT* out, const ValueT* const* arrays,"
                " std::size_t num_arrays, std::size_t n)")
_BIN_SIG = ("  template <typename ValueT, typename IndexT>\n  static void apply(ValueT* target, const IndexT* dests,"
            " const ValueT* vals, std::size_t n)")
_STREAM_SIG = ("  template <typename ValueT, typename IndexT>\n  static void gather_stream(ValueT* dst, const ValueT* src,"
               " const IndexT* idx, std::size_t rows, std::size_t row_len, std::size_t dst_stride,"
               " std::size_t src_stride)")

SHAPE_CLASSES: Mapping[str, ShapeClass] = _mp({
    "flat_movement": ShapeClass(
        name="flat_movement", family="gather", ref_template="gather_ref.cpp.tmpl",
        cand_template="gather_cand.cpp.tmpl", run_template="gather_run.cpp.tmpl",
        run_symbols=("swdb_ref_gather", "swdb_cand_gather"), hook=_GATHER_SIG.strip(),
        mutant_bodies=_mp(_FLAT_MUTANTS),
        probe=("#include \"{header}\"\nint main() {{\n  double s[4] = {{1, 2, 3, 4}}; int i[2] = {{3, 0}}; double o[2];\n"
               "  SynthBackend::gather<double, int>(o, s, i, 2, 4);\n  return o[0] == 4.0 && o[1] == 1.0 ? 0 : 1;\n}}\n"),
        test_hint=("Concrete call: SynthBackend::gather<double, int>(out.data(), src.data(), idx.data(), n, n_source);\n"
                   "Expected: expected[i] = src[idx[i]] for i in [0,n); every idx in [0,n_source)."),
        default_sizes=_mp({"n": 257, "n_src": 1031}), gen_case=generate_gather_case,
        write_case=_write_gather_case, argv=lambda s, c, d: [str(s["n"]), str(s["n_src"]), str(d)],
        read_outputs=lambda d, s: _read_f64_pair(d, s["n"]), expected_cand_bytes=lambda s: s["n"] * 8,
        patterns=_INDEX_PATTERNS, envelope_sample=_flat_envelope_sample, merge_envelope=_flat_merge_envelope,
        delegating_header=_delegating("gather", _GATHER_SIG,
                                      "swdb_ref::gather<ValueT, IndexT>(out, source, idx, n, n_source);")),
    "chained_pack": ShapeClass(
        name="chained_pack", family="pack", ref_template="pack_ref.cpp.tmpl",
        cand_template="pack_cand.cpp.tmpl", run_template="pack_run.cpp.tmpl",
        run_symbols=("swdb_ref_pack", "swdb_cand_pack"), hook=_PACK_SIG.strip(),
        mutant_bodies=_mp(_CHAINED_MUTANTS),
        probe=("#include \"{header}\"\nint main() {{\n  double src[4] = {{1, 2, 3, 4}};\n"
               "  int c0[2] = {{1, 0}}; int c1[4] = {{2, 3, 0, 1}};\n  const int* chain[2] = {{c0, c1}};\n"
               "  double p[2];\n  SynthBackend::pack_gather<double, int>(p, src, chain, 2, 2, 1, 0, 4);\n"
               "  return p[0] == 4.0 && p[1] == 3.0 ? 0 : 1;\n}}\n"),
        test_hint=("Concrete call (depth-2 chain): const int* chain[2] = {chain0.data(), chain1.data()};\n"
                   "SynthBackend::pack_gather<double, int>(packed.data(), src.data(), chain, 2, n, coeff, offset, n_src);\n"
                   "Expected: idx=i; idx=chain0[idx]; idx=chain1[idx]; packed[i] = src[idx*coeff + offset]."),
        default_sizes=_mp({"n": 257, "n_src": 1031}), gen_case=generate_pack_case,
        write_case=_write_pack_case,
        argv=lambda s, c, d: [str(s["n"]), str(s["n_src"]), str(c["depth"]), str(c["coeff"]), str(c["offset"]), str(d)],
        read_outputs=lambda d, s: _read_f64_pair(d, s["n"]), expected_cand_bytes=lambda s: s["n"] * 8,
        patterns=_INDEX_PATTERNS, envelope_sample=_chained_envelope_sample, merge_envelope=_chained_merge_envelope,
        delegating_header=_delegating("pack_gather", _PACK_SIG,
                                      "swdb_ref::pack_gather<ValueT, IndexT>(packed, src, chain, depth, n, coeff, offset, n_src);")),
    "strided_interleave": ShapeClass(
        name="strided_interleave", family="regroup", ref_template="regroup_ref.cpp.tmpl",
        cand_template="regroup_cand.cpp.tmpl", run_template="regroup_run.cpp.tmpl",
        run_symbols=("swdb_ref_regroup", "swdb_cand_regroup"), hook=_REGROUP_SIG.strip(),
        mutant_bodies=_mp(_STRIDED_MUTANTS),
        probe=("#include \"{header}\"\nint main() {{\n  double a[2] = {{1, 2}}, b[2] = {{3, 4}};\n"
               "  const double* arrays[2] = {{a, b}};\n  double o[4];\n"
               "  SynthBackend::interleave<double>(o, arrays, 2, 2);\n"
               "  return o[0] == 1.0 && o[1] == 3.0 && o[2] == 2.0 && o[3] == 4.0 ? 0 : 1;\n}}\n"),
        test_hint=("Concrete call: SynthBackend::interleave<double>(out.data(), arrays, num_arrays, n);\n"
                   "Expected: out[num_arrays*i + a] = arrays[a][i]."),
        default_sizes=_mp({"n": 509, "k": 3}), gen_case=generate_regroup_case, write_case=_write_regroup_case,
        argv=lambda s, c, d: [str(s["n"]), str(s["k"]), str(d)],
        read_outputs=lambda d, s: _read_f64_pair(d, s["k"] * s["n"]),
        expected_cand_bytes=lambda s: s["k"] * s["n"] * 8, patterns=_REGROUP_PATTERNS,
        envelope_sample=_strided_envelope_sample, merge_envelope=_strided_merge_envelope,
        delegating_header=_delegating("interleave", _REGROUP_SIG,
                                      "swdb_ref::interleave<ValueT>(out, arrays, num_arrays, n);")),
    "bin_drain": ShapeClass(
        name="bin_drain", family="bin_drain", ref_template="bin_drain_ref.cpp.tmpl",
        cand_template="bin_drain_cand.cpp.tmpl", run_template="bin_drain_run.cpp.tmpl",
        run_symbols=("swdb_ref_bin_drain", "swdb_cand_bin_drain"), hook=_BIN_SIG.strip(),
        mutant_bodies=_mp(_BIN_DRAIN_MUTANTS),
        probe=("#include \"{header}\"\nint main() {{\n  double target[3] = {{10.0, 20.0, 30.0}};\n"
               "  int dests[4] = {{0, 2, 0, 1}};\n  double vals[4] = {{1.0, 2.0, 3.0, 4.0}};\n"
               "  SynthBackend::apply<double, int>(target, dests, vals, 4);\n"
               "  return (target[0] == 14.0 && target[1] == 24.0 && target[2] == 32.0) ? 0 : 1;\n}}\n"),
        test_hint=("Concrete call: SynthBackend::apply<double, int>(target.data(), dests.data(), vals.data(), n);\n"
                   "Expected: for k in [0, n) IN ORDER, target[dests[k]] += vals[k]; target is caller-seeded."),
        default_sizes=_mp({"n": 1021, "n_target": 127}), gen_case=generate_bin_drain_case,
        write_case=_write_bin_drain_case, argv=lambda s, c, d: [str(s["n"]), str(s["n_target"]), str(d)],
        read_outputs=lambda d, s: _read_f64_pair(d, s["n_target"]),
        expected_cand_bytes=lambda s: s["n_target"] * 8, patterns=_BIN_DRAIN_PATTERNS,
        envelope_sample=_bin_drain_envelope_sample, merge_envelope=_bin_drain_merge_envelope,
        delegating_header=_delegating("bin_drain", _BIN_SIG,
                                      "swdb_ref::bin_drain<ValueT, IndexT>(target, dests, vals, n);")),
    "gather_stream": ShapeClass(
        name="gather_stream", family="gather_stream", ref_template="gather_stream_ref.cpp.tmpl",
        cand_template="gather_stream_cand.cpp.tmpl", run_template="gather_stream_run.cpp.tmpl",
        run_symbols=("swdb_ref_gather_stream", "swdb_cand_gather_stream"), hook=_STREAM_SIG.strip(),
        mutant_bodies=_mp(_GATHER_STREAM_MUTANTS),
        probe=("#include \"{header}\"\nint main() {{\n  double src[6] = {{1, 2, 3, 4, 5, 6}};\n  int idx[2] = {{2, 0}};\n"
               "  double dst[6] = {{0, 0, 0, 0, 0, 0}};\n"
               "  SynthBackend::gather_stream<double, int>(dst, src, idx, 2, 2, 3, 3);\n"
               "  return dst[0] == 3.0 && dst[1] == 1.0 && dst[2] == 0.0 && dst[3] == 6.0 && dst[4] == 4.0 && dst[5] == 0.0 ? 0 : 1;\n}}\n"),
        test_hint=("Concrete call: SynthBackend::gather_stream<double, int>(dst.data(), src.data(), idx.data(), rows, row_len, dst_stride, src_stride);\n"
                   "Expected: dst[r*dst_stride + j] = src[r*src_stride + idx[j]] for j < row_len; padding untouched."),
        default_sizes=_mp({"rows": 16, "row_len": 61, "dst_stride": 63, "src_stride": 128}),
        gen_case=generate_gather_stream_case, write_case=_write_gather_case,
        argv=lambda s, c, d: [str(s["rows"]), str(s["row_len"]), str(s["dst_stride"]), str(s["src_stride"]), str(d)],
        read_outputs=lambda d, s: _read_f64_pair(d, s["rows"] * s["dst_stride"]),
        expected_cand_bytes=lambda s: s["rows"] * s["dst_stride"] * 8, patterns=_INDEX_PATTERNS,
        envelope_sample=_gather_stream_envelope_sample, merge_envelope=_gather_stream_merge_envelope,
        delegating_header=_delegating("gather_stream", _STREAM_SIG,
                                      "swdb_ref::gather_stream<ValueT, IndexT>(dst, src, idx, rows, row_len, dst_stride, src_stride);")),
    # SWDB addition (ticket 51), see the relabel section above.
    "relabel": ShapeClass(
        name="relabel", family="relabel", ref_template="relabel_ref.cpp.tmpl",
        cand_template="relabel_cand.cpp.tmpl", run_template="relabel_run.cpp.tmpl",
        run_symbols=("swdb_ref_relabel", "swdb_cand_relabel"), hook=_RELABEL_SIG.strip(),
        mutant_bodies=_mp(_RELABEL_MUTANTS),
        probe=("#include \"{header}\"\nint main() {{\n  double in[3] = {{1, 2, 3}}; int perm[3] = {{2, 0, 1}};\n"
               "  double out[3];\n  SynthBackend::relabel_apply<double, int>(out, in, perm, 3);\n"
               "  return out[2] == 1.0 && out[0] == 2.0 && out[1] == 3.0 ? 0 : 1;\n}}\n"),
        test_hint=("Concrete call: SynthBackend::relabel_apply<double, int>(out.data(), in.data(), perm.data(), n);\n"
                   "Expected: out[perm[v]] = in[v] for every v; perm is a bijection on [0, n)."),
        default_sizes=_mp({"n": 1031}), gen_case=generate_relabel_case, write_case=_write_relabel_case,
        argv=lambda s, c, d: [str(s["n"]), str(d)],
        read_outputs=lambda d, s: _read_f64_pair(d, s["n"]), expected_cand_bytes=lambda s: s["n"] * 8,
        patterns=_RELABEL_PATTERNS, envelope_sample=_relabel_envelope_sample,
        merge_envelope=_relabel_merge_envelope,
        delegating_header=_delegating("relabel", _RELABEL_SIG,
                                      "swdb_ref::relabel_apply<ValueT, IndexT>(out, in, perm, n);")),
})
