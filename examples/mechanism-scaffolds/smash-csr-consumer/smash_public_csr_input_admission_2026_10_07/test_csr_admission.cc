#include <cassert>
#include <climits>
#include <cstddef>
#include <iostream>

#include "csr_input_admission.h"

int main()
{
    int rows[] = {0, 2, 2, 3, 3};
    int columns[] = {0, 3, 2};
    float values[] = {1, 2, 3};
    smash_csr_input_view good = {4, rows, 5, columns, 3, values, 3, 3};
    assert(smash_admit_csr_structure(good) == SMASH_CSR_STRUCTURE_OK);
    auto bad = good;
    bad.row_words = 4;
    assert(smash_admit_csr_structure(bad) == SMASH_CSR_TRUNCATED_STORAGE);
    bad = good; bad.column_words = 2;
    assert(smash_admit_csr_structure(bad) == SMASH_CSR_TRUNCATED_STORAGE);
    bad = good; bad.value_words = 2;
    assert(smash_admit_csr_structure(bad) == SMASH_CSR_TRUNCATED_STORAGE);
    bad = good; bad.declared_nnz = (size_t)INT_MAX + 1;
    assert(smash_admit_csr_structure(bad) == SMASH_CSR_INVALID_SIZE);
    int shifted[] = {1, 2, 2, 3, 3};
    bad = good; bad.rows = shifted;
    assert(smash_admit_csr_structure(bad) == SMASH_CSR_INVALID_ROW_ORIGIN);
    int descending[] = {0, 2, 1, 3, 3};
    bad = good; bad.rows = descending;
    assert(smash_admit_csr_structure(bad) == SMASH_CSR_INVALID_ROW_ORDER);
    int negative[] = {0, -1, 2, 3, 3};
    bad = good; bad.rows = negative;
    assert(smash_admit_csr_structure(bad) == SMASH_CSR_INVALID_ROW_ORDER);
    int wrong_tail[] = {0, 2, 2, 3, 4};
    bad = good; bad.rows = wrong_tail;
    assert(smash_admit_csr_structure(bad) == SMASH_CSR_INVALID_ROW_ORDER);
    int short_tail[] = {0, 2, 2, 2, 2};
    bad = good; bad.rows = short_tail;
    assert(smash_admit_csr_structure(bad) == SMASH_CSR_NNZ_MISMATCH);
    int out_of_range[] = {0, 4, 2};
    bad = good; bad.columns = out_of_range;
    assert(smash_admit_csr_structure(bad) == SMASH_CSR_INVALID_COLUMN);
    int negative_col[] = {-1, 3, 2};
    bad = good; bad.columns = negative_col;
    assert(smash_admit_csr_structure(bad) == SMASH_CSR_INVALID_COLUMN);
    int duplicate[] = {0, 0, 2};
    bad = good; bad.columns = duplicate;
    assert(smash_admit_csr_structure(bad) ==
           SMASH_CSR_UNSUPPORTED_COLUMN_ORDER);
    int unordered[] = {3, 0, 2};
    bad = good; bad.columns = unordered;
    assert(smash_admit_csr_structure(bad) ==
           SMASH_CSR_UNSUPPORTED_COLUMN_ORDER);
    int empty[] = {0, 0, 0, 0, 0};
    smash_csr_input_view zero = {4, empty, 5, nullptr, 0, nullptr, 0, 0};
    assert(smash_admit_csr_structure(zero) == SMASH_CSR_STRUCTURE_OK);
    std::cout << "new CSR defined-prefix shape/order/nnz cases PASS\n";
}
