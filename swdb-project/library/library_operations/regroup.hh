// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
// Ported 2026-10-03 from MaizeHPC/MemAcc af3d6d7f7a69a72facdc3b95b42e78c952f44a76
// Source: DataLayoutAPI/data_layout.hh (class RegroupExecutor declaration) and
//         DataLayoutAPI/data_layout_impl.hh (regroup, getRegroupedValue, writeRegroupedValue)
// SWDB changes (2026-10-03 ET): the base RegroupExecutor only (no tiled or
// regroup-and-consume variants); MemAcc's build timer is removed; the vector-of-vectors
// overload delegates to the pointer overload (same loop); standalone C++11
// with no hardware API.
#ifndef SWDB_LIBRARY_REGROUP_HH
#define SWDB_LIBRARY_REGROUP_HH

#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <vector>

template <typename ValueT>
class RegroupExecutor {
public:
    typedef int64_t int_t;

    RegroupExecutor() {}
    ~RegroupExecutor() { delete[] regrouped_array_; }
    RegroupExecutor(const RegroupExecutor&) = delete;
    RegroupExecutor& operator=(const RegroupExecutor&) = delete;
    RegroupExecutor(RegroupExecutor&& other) noexcept
        : regrouped_array_(other.regrouped_array_), num_arrays_(other.num_arrays_),
          shortest_array_size_(other.shortest_array_size_), occurences_(other.occurences_) {
        other.regrouped_array_ = nullptr;
    }
    RegroupExecutor& operator=(RegroupExecutor&& other) noexcept {
        if (this != &other) {
            delete[] regrouped_array_;
            regrouped_array_ = other.regrouped_array_;
            num_arrays_ = other.num_arrays_;
            shortest_array_size_ = other.shortest_array_size_;
            occurences_ = other.occurences_;
            other.regrouped_array_ = nullptr;
        }
        return *this;
    }

    /// Interleave the input arrays: regrouped[num_arrays * j + i] = input_arrays[i][j].
    void regroup(const std::vector<int_t>& periods, const std::vector<int_t>& array_sizes,
                 const std::vector<ValueT*>& input_arrays) {
        num_arrays_ = input_arrays.size();
        bool flag = false;
        if (regrouped_array_ == nullptr) {
            flag = true;
            shortest_array_size_ = std::numeric_limits<int_t>::max();
            for (int_t i = 0; i < num_arrays_; ++i) {
                if (array_sizes[i] < shortest_array_size_) {
                    shortest_array_size_ = array_sizes[i];
                }
            }
            regrouped_array_ = new ValueT[shortest_array_size_ * num_arrays_];
            occurences_ = 0;
        }
        bool all_refresh = true;
        for (int_t i = 0; i < num_arrays_; ++i) {
            if (!flag && !(periods[i] > 0 && occurences_ % periods[i] == 0)) {
                all_refresh = false;
                break;
            }
        }
        if (all_refresh) {
            #pragma omp parallel for
            for (int_t j = 0; j < shortest_array_size_; ++j) {
                for (int_t i = 0; i < num_arrays_; ++i) {
                    regrouped_array_[num_arrays_ * j + i] = input_arrays[i][j];
                }
            }
        } else {
            for (int_t i = 0; i < num_arrays_; ++i) {
                int_t period = periods[i];
                if ((period > 0 && occurences_ % period == 0) || flag) {
                    #pragma omp parallel for
                    for (int_t j = 0; j < shortest_array_size_; ++j) {
                        regrouped_array_[num_arrays_ * j + i] = input_arrays[i][j];
                    }
                }
            }
        }
        occurences_++;
    }

    void regroup(const std::vector<int_t>& periods, const std::vector<int_t>& array_sizes,
                 const std::vector<std::vector<ValueT> >& input_arrays) {
        std::vector<ValueT*> pointers;
        for (std::size_t i = 0; i < input_arrays.size(); ++i)
            pointers.push_back(const_cast<ValueT*>(input_arrays[i].data()));
        regroup(periods, array_sizes, pointers);
    }

    ValueT getRegroupedValue(int_t arr_index, int_t i) {
        if (regrouped_array_ == nullptr || arr_index >= num_arrays_ || i >= shortest_array_size_) {
            throw std::out_of_range("Regrouped array not initialized or index out of range");
        }
        return regrouped_array_[num_arrays_ * i + arr_index];
    }

    ValueT getRegroupedValueUnchecked(int_t arr_index, int_t i) const {
        return regrouped_array_[num_arrays_ * i + arr_index];
    }

    void writeRegroupedValue(int_t arr_index, int_t i, ValueT value) {
        if (regrouped_array_ == nullptr || arr_index >= num_arrays_ || i >= shortest_array_size_) {
            throw std::out_of_range("Regrouped array not initialized or index out of range");
        }
        regrouped_array_[num_arrays_ * i + arr_index] = value;
    }

private:
    ValueT* regrouped_array_ = nullptr;
    int_t num_arrays_ = 0;
    int_t shortest_array_size_ = 0;
    int_t occurences_ = 0;
};

#endif
