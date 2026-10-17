// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
// Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
// Source: DataLayoutAPI/gather_staging.hh (CpuGatherStagingBackend, GatherStagingExecutor,
//         BackendGatherStagingExecutor)
// SWDB changes (2026-10-03 ET): the base executor only; `inline constexpr` constants
// become C++11 constants; standalone C++11 with no accelerator API (the x86 streaming
// store path stays behind its __AVX__ guard, as in the source).
// NEGATIVE CONTROL index_shift: element j reads index j - 1 (2026-10-03 ET).
#ifndef SWDB_LIBRARY_GATHER_STAGING_HH
#define SWDB_LIBRARY_GATHER_STAGING_HH

#include <cstddef>
#include <cstdint>
#include <cstdlib>

#if defined(__x86_64__) || defined(__i386__)
#define SWDB_GATHER_STAGING_X86 1
#include <immintrin.h>
#endif

static const std::size_t kGatherStagingAlignment = 64;
static const std::size_t kGatherStagingLanes = 4;

struct CpuGatherStagingBackend {
    static const char* name() { return "cpu_gather_staging"; }

    template <typename ValueT, typename IndexT>
    static void gather_stream(ValueT* dst, const ValueT* src, const IndexT* idx, std::size_t rows,
                              std::size_t row_len, std::size_t dst_stride, std::size_t src_stride) {
        if (rows == 0 || row_len == 0) return;
        ValueT* staging = static_cast<ValueT*>(alloc_staging(row_len * sizeof(ValueT)));
        for (std::size_t r = 0; r < rows; ++r)
            stream_row(dst + r * dst_stride, src + r * src_stride, idx, row_len, staging);
        free_staging(staging);
        fence();
    }

    template <typename ValueT, typename IndexT>
    static void stream_row(ValueT* dst_row, const ValueT* src_row, const IndexT* idx, std::size_t row_len,
                           ValueT* staging) {
        if (staging == nullptr) {
            for (std::size_t j = 0; j < row_len; ++j) dst_row[j] = src_row[static_cast<std::size_t>(idx[j])];
            return;
        }
        for (std::size_t j = 0; j < row_len; ++j) staging[j] = src_row[static_cast<std::size_t>(idx[j == 0 ? 0 : j - 1])];
        drain(dst_row, staging, row_len);
    }

    static void drain(double* dst, const double* staging, std::size_t n) {
#if defined(SWDB_GATHER_STAGING_X86) && defined(__AVX__)
        std::size_t i = 0;
        while (i < n && (reinterpret_cast<std::uintptr_t>(dst + i) & (kGatherStagingLanes * sizeof(double) - 1)) != 0u) {
            dst[i] = staging[i];
            ++i;
        }
        for (; i + kGatherStagingLanes <= n; i += kGatherStagingLanes)
            _mm256_stream_pd(dst + i, _mm256_loadu_pd(staging + i));
        for (; i < n; ++i) dst[i] = staging[i];
#else
        for (std::size_t i = 0; i < n; ++i) dst[i] = staging[i];
#endif
    }

    template <typename ValueT>
    static void drain(ValueT* dst, const ValueT* staging, std::size_t n) {
        for (std::size_t i = 0; i < n; ++i) dst[i] = staging[i];
    }

    static void fence() {
#if defined(SWDB_GATHER_STAGING_X86)
        _mm_sfence();
#endif
    }

    static void* alloc_staging(std::size_t bytes) {
        if (bytes == 0) return nullptr;
        const std::size_t padded = ((bytes + kGatherStagingAlignment - 1) / kGatherStagingAlignment)
                                   * kGatherStagingAlignment;
        void* p = nullptr;
        if (posix_memalign(&p, kGatherStagingAlignment, padded) != 0) return nullptr;
        return p;
    }

    static void free_staging(void* p) { std::free(p); }
};

template <typename ValueT, typename IndexT = int>
class GatherStagingExecutor {
public:
    GatherStagingExecutor() {}
    ~GatherStagingExecutor() { release(); }
    GatherStagingExecutor(const GatherStagingExecutor&) = delete;
    GatherStagingExecutor& operator=(const GatherStagingExecutor&) = delete;
    GatherStagingExecutor(GatherStagingExecutor&& other) noexcept
        : staging_(other.staging_), row_len_(other.row_len_) {
        other.staging_ = nullptr;
        other.row_len_ = 0;
    }
    GatherStagingExecutor& operator=(GatherStagingExecutor&& other) noexcept {
        if (this != &other) {
            release();
            staging_ = other.staging_;
            row_len_ = other.row_len_;
            other.staging_ = nullptr;
            other.row_len_ = 0;
        }
        return *this;
    }

    void build(std::size_t row_len) {
        if (staging_ != nullptr && row_len_ == row_len) return;
        release();
        row_len_ = row_len;
        if (row_len == 0) return;
        staging_ = static_cast<ValueT*>(CpuGatherStagingBackend::alloc_staging(row_len * sizeof(ValueT)));
    }

    std::size_t row_length() const { return row_len_; }

    void gather_stream_row(ValueT* dst_row, const ValueT* src_row, const IndexT* idx) {
        if (row_len_ == 0) return;
        CpuGatherStagingBackend::stream_row(dst_row, src_row, idx, row_len_, staging_);
    }

    static void flush() { CpuGatherStagingBackend::fence(); }
    static const char* backend_name() { return CpuGatherStagingBackend::name(); }

private:
    void release() {
        flush();
        if (staging_ != nullptr) {
            CpuGatherStagingBackend::free_staging(staging_);
            staging_ = nullptr;
        }
        row_len_ = 0;
    }

    ValueT* staging_ = nullptr;
    std::size_t row_len_ = 0;
};

template <typename IndexT = int, typename Backend = CpuGatherStagingBackend>
class BackendGatherStagingExecutor {
public:
    template <typename ValueT>
    static void gather_stream(ValueT* dst, const ValueT* src, const IndexT* idx, std::size_t rows,
                              std::size_t row_len, std::size_t dst_stride, std::size_t src_stride) {
        Backend::template gather_stream<ValueT, IndexT>(dst, src, idx, rows, row_len, dst_stride, src_stride);
    }
    static const char* backend_name() { return Backend::name(); }
};

#endif
