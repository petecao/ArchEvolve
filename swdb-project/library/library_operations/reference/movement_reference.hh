// Plain C++11 reference semantics for SWDB library operations (Extensa families).
// Created 2026-10-03 ET. Original SWDB code, written from the semantics stated in
// MemAcc af3d6d7f7a69 AgenticRefiner/transformations/{pack,regroup,binned,staging}
// contracts: the simplest sequential loops, no OpenMP, no hardware API.
#ifndef SWDB_MOVEMENT_REFERENCE_HH
#define SWDB_MOVEMENT_REFERENCE_HH
#include <cstddef>
#include <cstdint>

namespace swdb_ref {

// packed[i] = src[walk(chain, i) * coeff + offset], walking `depth` levels.
template <typename ValueT, typename IndexT>
void pack_gather(ValueT* packed, const ValueT* src, const IndexT* const* chain, std::size_t depth,
                 std::size_t n, std::int64_t coeff, std::int64_t offset, std::size_t n_src) {
  (void)n_src;
  for (std::size_t i = 0; i < n; ++i) {
    std::int64_t idx = (std::int64_t)i;
    for (std::size_t j = 0; j < depth; ++j) idx = (std::int64_t)chain[j][idx];
    packed[i] = src[idx * coeff + offset];
  }
}

// out[i] = src[idx[i]].
template <typename ValueT, typename IndexT>
void gather(ValueT* out, const ValueT* src, const IndexT* idx, std::size_t n, std::size_t n_src) {
  (void)n_src;
  for (std::size_t i = 0; i < n; ++i) out[i] = src[(std::size_t)idx[i]];
}

// out[num_arrays * i + a] = arrays[a][i] (array-of-structures interleave).
template <typename ValueT>
void interleave(ValueT* out, const ValueT* const* arrays, std::size_t num_arrays, std::size_t n) {
  for (std::size_t i = 0; i < n; ++i)
    for (std::size_t a = 0; a < num_arrays; ++a) out[num_arrays * i + a] = arrays[a][i];
}

// For k in [0, n) in order: target[dests[k]] += vals[k].
template <typename ValueT, typename IndexT>
void bin_drain(ValueT* target, const IndexT* dests, const ValueT* vals, std::size_t n) {
  for (std::size_t k = 0; k < n; ++k) target[(std::size_t)dests[k]] += vals[k];
}

// dst[r * dst_stride + j] = src[r * src_stride + idx[j]] for j < row_len; padding untouched.
template <typename ValueT, typename IndexT>
void gather_stream(ValueT* dst, const ValueT* src, const IndexT* idx, std::size_t rows,
                   std::size_t row_len, std::size_t dst_stride, std::size_t src_stride) {
  for (std::size_t r = 0; r < rows; ++r)
    for (std::size_t j = 0; j < row_len; ++j)
      dst[r * dst_stride + j] = src[r * src_stride + (std::size_t)idx[j]];
}

// new_values[new_id[v]] = old_values[v] (a relabeling permutation applied to data).
template <typename ValueT, typename IndexT>
void relabel_apply(ValueT* new_values, const ValueT* old_values, const IndexT* new_id, std::size_t n) {
  for (std::size_t v = 0; v < n; ++v) new_values[(std::size_t)new_id[v]] = old_values[v];
}

}  // namespace swdb_ref
#endif
