// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
// Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
// Source: DataLayoutAPI/update_binning.hh (BinPlan, CpuBinDrainBackend,
//         UpdateBinningExecutor base Fast path with execute and scatter_add)
// SWDB changes (2026-10-03 ET): base variant only (no deterministic, team or advisor
// code: DirectionAdvisor and memacc_cache_config.hh are not ported); `inline constexpr`
// becomes a C++11 constant; scatter_add's lambdas become named functors with the same
// semantics; standalone C++11 with no hardware API.
#ifndef SWDB_LIBRARY_BINNING_HH
#define SWDB_LIBRARY_BINNING_HH

#include <cstddef>
#include <cstdint>
#include <vector>
#if defined(_OPENMP)
#include <omp.h>
#endif

enum class DrainMode { Fast, Deterministic };

static const std::size_t kDefaultBinByteBudget = 512 * 1024;

template <typename IndexT = int>
class BinPlan {
public:
    void build(std::size_t num_dest, std::size_t bytes_per_update, std::size_t bin_byte_budget = 0) {
        num_dest_ = num_dest;
        if (bin_byte_budget == 0) bin_byte_budget = kDefaultBinByteBudget;
        if (bytes_per_update == 0) bytes_per_update = 1;
        dest_per_bin_ = bin_byte_budget / bytes_per_update;
        if (dest_per_bin_ == 0) dest_per_bin_ = 1;
        num_bins_ = num_dest == 0 ? 0 : (num_dest + dest_per_bin_ - 1) / dest_per_bin_;
    }
    std::size_t num_bins() const { return num_bins_; }
    std::size_t num_dest() const { return num_dest_; }
    IndexT bin_begin(std::size_t b) const { return static_cast<IndexT>(b * dest_per_bin_); }
    IndexT bin_end(std::size_t b) const {
        std::size_t e = (b + 1) * dest_per_bin_;
        return static_cast<IndexT>(e < num_dest_ ? e : num_dest_);
    }
    std::size_t bin_of(IndexT dest) const { return static_cast<std::size_t>(dest) / dest_per_bin_; }

private:
    std::size_t num_dest_ = 0;
    std::size_t num_bins_ = 0;
    std::size_t dest_per_bin_ = 1;
};

struct CpuBinDrainBackend {
    static const char* name() { return "cpu_bin_drain"; }
    template <typename ValueT, typename IndexT, typename UpdateOp>
    static void apply(ValueT* target, const IndexT* dests, const ValueT* vals, std::size_t n, UpdateOp op) {
        for (std::size_t k = 0; k < n; ++k) op(target[dests[k]], vals[k]);
    }
};

template <typename ValueT, typename IndexT = int, DrainMode Mode = DrainMode::Fast,
          typename Backend = CpuBinDrainBackend>
class UpdateBinningExecutor {
public:
    void initialize(const BinPlan<IndexT>& plan) {
        plan_ = plan;
#if defined(_OPENMP)
        n_threads_ = static_cast<std::size_t>(omp_get_max_threads());
#else
        n_threads_ = 1;
#endif
        dest_bufs_.assign(n_threads_ * plan_.num_bins(), std::vector<IndexT>());
        val_bufs_.assign(n_threads_ * plan_.num_bins(), std::vector<ValueT>());
    }

    template <typename ProduceFn, typename UpdateOp>
    void execute(std::size_t n_iters, ProduceFn produce, ValueT* target, UpdateOp op) {
        const std::size_t B = plan_.num_bins();
        if (B == 0 || n_iters == 0) return;
        const std::size_t T = n_threads_;
        for (std::size_t q = 0; q < dest_bufs_.size(); ++q) dest_bufs_[q].clear();
        for (std::size_t q = 0; q < val_bufs_.size(); ++q) val_bufs_[q].clear();
#if defined(_OPENMP)
#pragma omp parallel num_threads((int)T)
#endif
        {
#if defined(_OPENMP)
            const std::size_t t = (std::size_t)omp_get_thread_num();
#else
            const std::size_t t = 0;
#endif
            const std::size_t lo = n_iters * t / T;
            const std::size_t hi = n_iters * (t + 1) / T;
            std::vector<IndexT>* dbuf = &dest_bufs_[t * B];
            std::vector<ValueT>* vbuf = &val_bufs_[t * B];
            IndexT dest;
            ValueT val;
            for (std::size_t i = lo; i < hi; ++i) {
                produce(i, dest, val);
                const std::size_t b = plan_.bin_of(dest);
                dbuf[b].push_back(dest);
                vbuf[b].push_back(val);
            }
        }
#if defined(_OPENMP)
#pragma omp parallel for schedule(dynamic, 1)
#endif
        for (long long b = 0; b < (long long)B; ++b) {
            for (std::size_t t = 0; t < T; ++t) {
                const std::vector<IndexT>& d = dest_bufs_[t * B + (std::size_t)b];
                const std::vector<ValueT>& v = val_bufs_[t * B + (std::size_t)b];
                if (!d.empty())
                    Backend::template apply<ValueT, IndexT>(target, d.data(), v.data(), d.size(), op);
            }
        }
    }

    struct AddOp {
        void operator()(ValueT& t, ValueT v) const { t += v; }
    };
    struct ScatterProducer {
        const IndexT* dest_idx;
        const ValueT* values;
        void operator()(std::size_t i, IndexT& dest, ValueT& val) const {
            dest = dest_idx[i];
            val = values[i];
        }
    };

    void scatter_add(std::size_t n_iters, const IndexT* dest_idx, const ValueT* values, ValueT* target) {
        ScatterProducer produce = {dest_idx, values};
        execute(n_iters, produce, target, AddOp());
    }

    static const char* backend_name() { return Backend::name(); }

private:
    BinPlan<IndexT> plan_;
    std::size_t n_threads_ = 1;
    std::vector<std::vector<IndexT> > dest_bufs_;
    std::vector<std::vector<ValueT> > val_bufs_;
};

#endif
