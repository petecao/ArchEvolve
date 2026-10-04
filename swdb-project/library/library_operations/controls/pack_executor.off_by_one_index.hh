// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
// Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
// Source: DataLayoutAPI/data_layout.hh (class PackExecutor declaration) and
//         DataLayoutAPI/data_layout_impl.hh (initialize_packed_array, load_to_pack,
//         get_packed_value, packed_ref, write_packed_value)
// SWDB changes (2026-10-03 ET): only the base PackExecutor path (one-level and chained
// load_to_pack) and its dependencies; range, tiled, partial, multi and index-map
// variants are not ported; MemAcc's build timer is removed (SWDB's evaluator supplies
// every number); standalone C++11 with no hardware API; adds a packed_size() accessor.
// NEGATIVE CONTROL off_by_one_index: slot i walks the chain from slot i + 1 (2026-10-03 ET).
#ifndef SWDB_LIBRARY_PACK_HH
#define SWDB_LIBRARY_PACK_HH

#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <vector>

// one per instance of packing
template <typename ValueT, typename IndexT = int>
class PackExecutor {
public:
    typedef int64_t int_t;

    PackExecutor() {}
    ~PackExecutor() {
        delete[] packed_array_;
        delete[] pack_indices_;
    }
    PackExecutor(const PackExecutor&) = delete;
    PackExecutor& operator=(const PackExecutor&) = delete;
    PackExecutor(PackExecutor&& other) noexcept
        : packed_array_(other.packed_array_), pack_indices_(other.pack_indices_),
          packed_size_(other.packed_size_), packed_capacity_(other.packed_capacity_) {
        other.packed_array_ = nullptr;
        other.pack_indices_ = nullptr;
        other.packed_size_ = 0;
        other.packed_capacity_ = 0;
    }
    PackExecutor& operator=(PackExecutor&& other) noexcept {
        if (this != &other) {
            delete[] packed_array_;
            delete[] pack_indices_;
            packed_array_ = other.packed_array_;
            pack_indices_ = other.pack_indices_;
            packed_size_ = other.packed_size_;
            packed_capacity_ = other.packed_capacity_;
            other.packed_array_ = nullptr;
            other.pack_indices_ = nullptr;
            other.packed_size_ = 0;
            other.packed_capacity_ = 0;
        }
        return *this;
    }

    /// Initialize the packed array with the given size.
    void initialize_packed_array(size_t packed_size) {
        packed_size_ = packed_size;
        if (packed_size_ > packed_capacity_) {
            delete[] packed_array_;
            delete[] pack_indices_;
            packed_array_ = new ValueT[packed_size_];
            pack_indices_ = new IndexT[packed_size_];
            packed_capacity_ = packed_size_;
        }
    }

    /// For each packed slot i: idx = i; for each level j: idx = indices[j][idx];
    /// packed[i] = source[idx * coeff + offset].
    void load_to_pack(const ValueT* source, const std::vector<IndexT*>& indices, int64_t coeff = 1,
                      int64_t offset = 0) {
        const size_t num_indices = indices.size();
        if (pack_indices_) {
            #pragma omp parallel for
            for (size_t i = 0; i < packed_size_; ++i) {
                IndexT idx = (i + 1 < packed_size_) ? (IndexT)(i + 1) : (IndexT)i;
                for (size_t j = 0; j < num_indices; ++j) {
                    idx = (indices[j])[idx];
                }
                idx = idx * coeff + offset;
                pack_indices_[i] = idx;
                packed_array_[i] = source[idx];
            }
        } else {
            #pragma omp parallel for
            for (size_t i = 0; i < packed_size_; ++i) {
                IndexT idx = (i + 1 < packed_size_) ? (IndexT)(i + 1) : (IndexT)i;
                for (size_t j = 0; j < num_indices; ++j) {
                    idx = (indices[j])[idx];
                }
                idx = idx * coeff + offset;
                packed_array_[i] = source[idx];
            }
        }
    }

    void load_to_pack(const std::vector<ValueT>& source, const std::vector<IndexT*>& indices,
                      int64_t coeff = 1, int64_t offset = 0) {
        load_to_pack(source.data(), indices, coeff, offset);
    }

    ValueT get_packed_value(size_t i) {
        if (i >= packed_size_) {
            throw std::out_of_range("Index out of range in get_packed_value");
        }
        return packed_array_[i];
    }

    ValueT& packed_ref(size_t i) {
        if (i >= packed_size_) {
            throw std::out_of_range("Index out of range in packed_ref");
        }
        return packed_array_[i];
    }

    const ValueT& packed_ref(size_t i) const {
        if (i >= packed_size_) {
            throw std::out_of_range("Index out of range in packed_ref");
        }
        return packed_array_[i];
    }

    void write_packed_value(size_t i, ValueT value) {
        if (i >= packed_size_) {
            throw std::out_of_range("Index out of range in write_packed_value");
        }
        packed_array_[i] = value;
    }

    size_t packed_size() const { return packed_size_; }

private:
    ValueT* packed_array_ = nullptr;
    IndexT* pack_indices_ = nullptr;
    size_t packed_size_ = 0;
    size_t packed_capacity_ = 0;
};

#endif
