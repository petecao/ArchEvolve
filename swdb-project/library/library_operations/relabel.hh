// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
// Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
// Source: DataLayoutAPI/vertex_relabel.hh (RelabelRowOrder, RelabelPlan,
//         plan_vertex_relabel, VertexRelabelExecutor)
// SWDB changes (2026-10-03 ET): the base executor only; the parallel merge sort of
// build_degree_order is replaced by std::stable_sort with the same total order (a
// variant optimization, not semantics); standalone C++11 with no hardware API.
#ifndef SWDB_LIBRARY_RELABEL_HH
#define SWDB_LIBRARY_RELABEL_HH

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <numeric>
#include <vector>

enum class RelabelRowOrder {
    kSortedAscending,
    kPreserveInput,
};

struct RelabelPlan {
    bool bijection = false;
    std::size_t n = 0;
    std::size_t first_violation = 0;
    bool checked = true;
};

template <typename IndexT = int>
RelabelPlan plan_vertex_relabel(const IndexT* perm, std::size_t n) {
    RelabelPlan p;
    p.n = n;
    p.first_violation = n;
    if (perm == nullptr && n != 0) { p.checked = false; return p; }
    std::vector<bool> seen(n, false);
    for (std::size_t i = 0; i < n; ++i) {
        const long long v = static_cast<long long>(perm[i]);
        if (v < 0 || static_cast<std::size_t>(v) >= n || seen[static_cast<std::size_t>(v)]) {
            p.first_violation = i;
            return p;
        }
        seen[static_cast<std::size_t>(v)] = true;
    }
    p.bijection = true;
    return p;
}

template <typename IndexT = int>
class VertexRelabelExecutor {
public:
    struct DegreeBefore {
        const IndexT* offsets;
        bool operator()(IndexT a, IndexT b) const {
            const IndexT da = offsets[a + 1] - offsets[a];
            const IndexT db = offsets[b + 1] - offsets[b];
            return da != db ? da > db : a < b;
        }
    };

    bool build_degree_order(const IndexT* offsets, std::size_t n) {
        if (offsets == nullptr || n == 0) return adopt_permutation(nullptr, 0);
        std::vector<IndexT> order(n);
        std::iota(order.begin(), order.end(), IndexT(0));
        DegreeBefore before = {offsets};
        std::stable_sort(order.begin(), order.end(), before);
        std::vector<IndexT> perm(n);
        const std::int64_t sn = static_cast<std::int64_t>(n);
#if defined(_OPENMP)
#pragma omp parallel for schedule(static) if (sn >= kParallelMin)
#endif
        for (std::int64_t rank = 0; rank < sn; ++rank)
            perm[static_cast<std::size_t>(order[static_cast<std::size_t>(rank)])] = static_cast<IndexT>(rank);
        return adopt_permutation(perm.data(), n);
    }

    bool adopt_permutation(const IndexT* perm, std::size_t n) {
        plan_ = plan_vertex_relabel<IndexT>(perm, n);
        perm_.clear();
        inv_.clear();
        if (!plan_.bijection) return false;
        if (n == 0) return true;
        perm_.assign(perm, perm + n);
        inv_.resize(n);
        const std::int64_t sn = static_cast<std::int64_t>(n);
#if defined(_OPENMP)
#pragma omp parallel for schedule(static) if (sn >= kParallelMin)
#endif
        for (std::int64_t i = 0; i < sn; ++i)
            inv_[static_cast<std::size_t>(perm_[static_cast<std::size_t>(i)])] = static_cast<IndexT>(i);
        return true;
    }

    const RelabelPlan& plan() const { return plan_; }
    std::size_t size() const { return perm_.size(); }
    const IndexT* permutation() const { return perm_.empty() ? nullptr : perm_.data(); }
    const IndexT* inverse() const { return inv_.empty() ? nullptr : inv_.data(); }

    void relabel_csr(const IndexT* offsets, const IndexT* neighbors, IndexT* new_offsets, IndexT* new_neighbors,
                     RelabelRowOrder order = RelabelRowOrder::kSortedAscending) const {
        const std::size_t n = perm_.size();
        if (n == 0 || offsets == nullptr || neighbors == nullptr || new_offsets == nullptr ||
            new_neighbors == nullptr)
            return;
        const std::int64_t sn = static_cast<std::int64_t>(n);
        new_offsets[0] = 0;
#if defined(_OPENMP)
#pragma omp parallel for schedule(static) if (sn >= kParallelMin)
#endif
        for (std::int64_t v_new = 0; v_new < sn; ++v_new) {
            const std::size_t v_old = static_cast<std::size_t>(inv_[static_cast<std::size_t>(v_new)]);
            new_offsets[v_new + 1] = offsets[v_old + 1] - offsets[v_old];
        }
        for (std::size_t v_new = 0; v_new < n; ++v_new) new_offsets[v_new + 1] += new_offsets[v_new];
        const bool sort_rows = (order == RelabelRowOrder::kSortedAscending);
#if defined(_OPENMP)
#pragma omp parallel for schedule(dynamic, 256) if (sn >= kParallelMin)
#endif
        for (std::int64_t v_new = 0; v_new < sn; ++v_new) {
            const std::size_t v_old = static_cast<std::size_t>(inv_[static_cast<std::size_t>(v_new)]);
            IndexT* dst = new_neighbors + new_offsets[v_new];
            const IndexT lo = offsets[v_old], hi = offsets[v_old + 1];
            for (IndexT k = lo; k < hi; ++k) dst[k - lo] = perm_[static_cast<std::size_t>(neighbors[k])];
            if (sort_rows) std::sort(dst, dst + (hi - lo));
        }
    }

    template <typename ValueT>
    void permute_values(const ValueT* in, ValueT* out) const {
        if (in == nullptr || out == nullptr) return;
        const std::int64_t sn = static_cast<std::int64_t>(perm_.size());
#if defined(_OPENMP)
#pragma omp parallel for schedule(static) if (sn >= kParallelMin)
#endif
        for (std::int64_t v = 0; v < sn; ++v)
            out[static_cast<std::size_t>(perm_[static_cast<std::size_t>(v)])] = in[v];
    }

    template <typename ValueT>
    void unpermute_values(const ValueT* in, ValueT* out) const {
        if (in == nullptr || out == nullptr) return;
        const std::int64_t sn = static_cast<std::int64_t>(perm_.size());
#if defined(_OPENMP)
#pragma omp parallel for schedule(static) if (sn >= kParallelMin)
#endif
        for (std::int64_t v = 0; v < sn; ++v)
            out[v] = in[static_cast<std::size_t>(perm_[static_cast<std::size_t>(v)])];
    }

    bool inverse_round_trips() const {
        for (std::size_t i = 0; i < perm_.size(); ++i) {
            if (inv_[static_cast<std::size_t>(perm_[i])] != static_cast<IndexT>(i)) return false;
            if (perm_[static_cast<std::size_t>(inv_[i])] != static_cast<IndexT>(i)) return false;
        }
        return true;
    }

private:
    static const std::int64_t kParallelMin = 1 << 14;
    RelabelPlan plan_;
    std::vector<IndexT> perm_;
    std::vector<IndexT> inv_;
};

#endif
